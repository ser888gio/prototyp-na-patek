import os

from agent.tools_and_schemas import SearchQueryList, Reflection
from dotenv import load_dotenv
from langchain_core.messages import AIMessage
from langgraph.types import Send
from langgraph.graph import StateGraph
from langgraph.graph import START, END
from langchain_core.runnables import RunnableConfig
from google.genai import Client

from agent.state import (
    OverallState,
    QueryGenerationState,
    ReflectionState,
    WebSearchState,
)
from agent.configuration import Configuration
from agent.prompts import (
    get_current_date,
    query_writer_instructions,
    web_searcher_instructions,
    reflection_instructions,
    answer_instructions,
)
from langchain_google_genai import ChatGoogleGenerativeAI
from agent.utils import (
    get_citations,
    get_research_topic,
    insert_citation_markers,
    resolve_urls,
)

# Import RAG components
import asyncio
from langchain_pinecone import PineconeVectorStore
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from pinecone import Pinecone, ServerlessSpec

load_dotenv()

if os.getenv("GEMINI_API_KEY") is None:
    raise ValueError("GEMINI_API_KEY is not set")

# Used for Google Search API
genai_client = Client(api_key=os.getenv("GEMINI_API_KEY"))

# Global RAG components
vector_store = None
retriever = None

async def initialize_rag_system():
    """Initialize the RAG system with vector store and retriever"""
    global vector_store, retriever
    
    try:
        print(f"========== INITIALIZING RAG SYSTEM (GRAPH) ==========")
        print(f"Creating Pinecone client...")
        
        # Initialize Pinecone
        def _create_pinecone_client():
            pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
            index_name = "langchain-test-index"
            
            if not pc.has_index(index_name):
                print(f"Index '{index_name}' not found, creating...")
                pc.create_index(
                    name=index_name,
                    dimension=384,
                    metric="cosine",
                    spec=ServerlessSpec(cloud="aws", region="us-east-1"),
                )
                print(f"✅ Created new index: {index_name}")
            else:
                print(f"✅ Found existing index: {index_name}")
            
            return pc.Index(index_name)
        
        index = await asyncio.to_thread(_create_pinecone_client)
        print(f"✅ Pinecone index ready")
        
        # Initialize embeddings
        print(f"Loading HuggingFace embeddings model: sentence-transformers/all-MiniLM-L12-v2")
        embeddings_model = await asyncio.to_thread(
            HuggingFaceEmbeddings, 
            model_name='sentence-transformers/all-MiniLM-L12-v2'
        )
        print(f"✅ Embeddings model loaded")
        
        # Create vector store
        vector_store = PineconeVectorStore(
            index=index, 
            embedding=embeddings_model
        )
        print(f"✅ Vector store created: {type(vector_store).__name__}")
        
        # Create retriever
        retriever = vector_store.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={"k": 3, "score_threshold": 0.4},
        )
        print(f"✅ Retriever created with config:")
        print(f"   - search_type: similarity_score_threshold")
        print(f"   - k (max results): 3")
        print(f"   - score_threshold: 0.4")
        print(f"========== RAG SYSTEM INITIALIZATION COMPLETE (GRAPH) ==========\n")
        
        return True
    except Exception as e:
        print(f"❌ Failed to initialize RAG system: {e}")
        import traceback
        traceback.print_exc()
        return False

# Nodes
def generate_query(state: OverallState, config: RunnableConfig) -> QueryGenerationState:
    """LangGraph node that generates search queries based on the User's question.

    Uses Gemini 2.0 Flash to create an optimized search queries for web research based on
    the User's question.

    Args:
        state: Current graph state containing the User's question
        config: Configuration for the runnable, including LLM provider settings

    Returns:
        Dictionary with state update, including search_query key containing the generated queries
    """
    configurable = Configuration.from_runnable_config(config)

    # check for custom initial search query count
    if state.get("initial_search_query_count") is None:
        state["initial_search_query_count"] = configurable.number_of_initial_queries

    # init Gemini 2.0 Flash
    llm = ChatGoogleGenerativeAI(
        model=configurable.query_generator_model,
        temperature=1.0,
        max_retries=2,
        api_key=os.getenv("GEMINI_API_KEY"),
    )
    structured_llm = llm.with_structured_output(SearchQueryList)

    # Format the prompt
    current_date = get_current_date()
    formatted_prompt = query_writer_instructions.format(
        current_date=current_date,
        research_topic=get_research_topic(state["messages"]),
        number_queries=state["initial_search_query_count"],
    )
    
    # Generate the search queries with error handling
    try:
        result = structured_llm.invoke(formatted_prompt)
        if result is None:
            # Fallback: create a basic search query from the research topic
            research_topic = get_research_topic(state["messages"])
            return {"search_query": [research_topic]}
        
        # Ensure result.query is not None and is a list
        if not hasattr(result, 'query') or result.query is None:
            research_topic = get_research_topic(state["messages"])
            return {"search_query": [research_topic]}
            
        return {"search_query": result.query}
    except Exception as e:
        # Fallback: create a basic search query from the research topic
        research_topic = get_research_topic(state["messages"])
        print(f"Error in generate_query: {e}. Using fallback query.")
        return {"search_query": [research_topic]}

async def rag_search(state: OverallState, config: RunnableConfig) -> OverallState:
    """LangGraph node that performs RAG search using the vector database.
    
    This node searches the vector database for relevant documents and adds them
    to the research results.
    
    Args:
        state: Current graph state containing the user's question
        config: Configuration for the runnable
        
    Returns:
        Dictionary with state update, including rag_results and sources_gathered
    """
    global vector_store, retriever
    
    try:
        # Initialize RAG system if not already done
        if vector_store is None or retriever is None:
            rag_initialized = await initialize_rag_system()
            if not rag_initialized:
                return {
                    "rag_results": ["RAG system not available"],
                    "sources_gathered": state.get("sources_gathered", [])
                }
        
        # Get the research topic from messages
        research_topic = get_research_topic(state["messages"])
        print(f"========== RAG SEARCH IN GRAPH ==========")
        print(f"Research topic extracted: '{research_topic}'")
        
        # Perform RAG search
        print(f"Invoking retriever with topic: '{research_topic}'")
        relevant_docs = await retriever.ainvoke(research_topic)
        
        print(f"========== VECTOR STORE EXTRACTION (GRAPH) ==========")
        print(f"Query/Topic: '{research_topic}'")
        print(f"Found {len(relevant_docs)} documents from vector store")
        print(f"Retriever config: search_type=similarity_score_threshold, k=3, score_threshold=0.4")
        
        # Format RAG results
        rag_results = []
        rag_sources = []
        
        for i, doc in enumerate(relevant_docs):
            print(f"\n--- RAG Document {i+1} (Graph Node) ---")
            print(f"Content length: {len(doc.page_content)} characters")
            print(f"Metadata: {doc.metadata}")
            score = getattr(doc, 'score', None)
            if score is not None:
                print(f"Similarity score: {score}")
            print(f"Content preview (first 300 chars): {doc.page_content[:300]}...")
            if len(doc.page_content) > 300:
                print(f"Content preview (last 100 chars): ...{doc.page_content[-100:]}")
            
            # Create a formatted result
            result_text = f"Document {i+1} (from vector database):\n{doc.page_content}"
            rag_results.append(result_text)
            
            # Add to sources (format similar to web sources)
            rag_sources.append({
                "label": f"rag_doc_{i}",
                "short_url": f"rag://doc_{i}",
                "value": f"Vector Database Document {i+1}",
                "type": "rag"
            })
            
            print(f"Added to rag_results: First 200 chars of formatted result: {result_text[:200]}...")
            print(f"Added to sources: {rag_sources[-1]}")
        
        print(f"========== END RAG EXTRACTION (GRAPH) ==========\n")
        
        # Combine with existing sources
        existing_sources = state.get("sources_gathered", [])
        updated_sources = existing_sources + rag_sources

        context_text = rag_results
        
        return {
            "rag_results": rag_results,
            "sources_gathered": updated_sources,
            "context_text": context_text
        }
        
    except Exception as e:
        print(f"Error in rag_search: {e}")
        return {
            "rag_results": [f"Error searching vector database: {str(e)}"],
            "sources_gathered": state.get("sources_gathered", [])
        }

def continue_to_web_research(state: QueryGenerationState):
    """LangGraph node that sends the search queries to the web research node.

    This is used to spawn n number of web research nodes, one for each search query.
    """
    return [
        Send("web_research", {"search_query": search_query, "id": int(idx)})
        for idx, search_query in enumerate(state["search_query"])
    ]

def web_research(state: WebSearchState, config: RunnableConfig) -> OverallState:
    """LangGraph node that performs web research using the native Google Search API tool.

    Executes a web search using the native Google Search API tool in combination with Gemini 2.0 Flash.

    Args:
        state: Current graph state containing the search query and research loop count
        config: Configuration for the runnable, including search API settings

    Returns:
        Dictionary with state update, including sources_gathered, research_loop_count, and web_research_results
    """
    # Configure
    configurable = Configuration.from_runnable_config(config)
    formatted_prompt = web_searcher_instructions.format(
        current_date=get_current_date(),
        research_topic=state["search_query"],
    )

    try:
        # Uses the google genai client as the langchain client doesn't return grounding metadata
        response = genai_client.models.generate_content(
            model=configurable.query_generator_model,
            contents=formatted_prompt,
            config={
                "tools": [{"google_search": {}}],
                "temperature": 0,
            },
        )
        
        # Check if response and required attributes exist
        if (response is None or 
            not hasattr(response, 'candidates') or 
            not response.candidates or 
            not hasattr(response.candidates[0], 'grounding_metadata') or
            response.candidates[0].grounding_metadata is None):
            
            # Fallback: return minimal valid state
            return {
                "sources_gathered": [],
                "search_query": [state["search_query"]],
                "web_research_result": [f"No search results found for: {state['search_query']}"],
            }
        
        # Check if grounding_chunks exists
        grounding_metadata = response.candidates[0].grounding_metadata
        grounding_chunks = getattr(grounding_metadata, 'grounding_chunks', None)
        
        if grounding_chunks is None:
            # Fallback: return minimal valid state with response text
            response_text = getattr(response, 'text', f"Search completed for: {state['search_query']}")
            return {
                "sources_gathered": [],
                "search_query": [state["search_query"]],
                "web_research_result": [response_text],
            }
        
        # resolve the urls to short urls for saving tokens and time
        resolved_urls = resolve_urls(grounding_chunks, state["id"])
        
        # Gets the citations and adds them to the generated text
        citations = get_citations(response, resolved_urls)
        modified_text = insert_citation_markers(response.text, citations)
        
        # Ensure citations is iterable and has the expected structure
        sources_gathered = []
        if citations and isinstance(citations, list):
            for citation in citations:
                if citation and isinstance(citation, dict) and "segments" in citation:
                    segments = citation["segments"]
                    if segments and isinstance(segments, list):
                        sources_gathered.extend(segments)

        return {
            "sources_gathered": sources_gathered,
            "search_query": [state["search_query"]],
            "web_research_result": [modified_text],
        }
        
    except Exception as e:
        # Fallback: return minimal valid state
        print(f"Error in web_research: {e}. Using fallback response.")
        return {
            "sources_gathered": [],
            "search_query": [state["search_query"]],
            "web_research_result": [f"Search error for: {state['search_query']}. {str(e)}"],
        }

def reflection(state: OverallState, config: RunnableConfig) -> ReflectionState:
    """LangGraph node that identifies knowledge gaps and generates potential follow-up queries.

    Analyzes the current summary to identify areas for further research and generates
    potential follow-up queries. Uses structured output to extract
    the follow-up query in JSON format.

    Args:
        state: Current graph state containing the running summary and research topic
        config: Configuration for the runnable, including LLM provider settings

    Returns:
        Dictionary with state update, including search_query key containing the generated follow-up query
    """
    configurable = Configuration.from_runnable_config(config)
    # Increment the research loop count and get the reasoning model
    state["research_loop_count"] = state.get("research_loop_count", 0) + 1
    reasoning_model = state.get("reasoning_model", configurable.reflection_model)

    # Format the prompt
    current_date = get_current_date()
    
    # Get RAG results for context
    rag_results = state.get("rag_results", [])
    rag_context = "\n\n---\n\n".join(rag_results) if rag_results else "No knowledge base results available."
    
    formatted_prompt = reflection_instructions.format(
        current_date=current_date,
        research_topic=get_research_topic(state["messages"]),
        summaries="\n\n---\n\n".join(state["web_research_result"]),
        rag_results=rag_context,
    )
    # init Reasoning Model
    llm = ChatGoogleGenerativeAI(
        model=reasoning_model,
        temperature=1.0,
        max_retries=2,
        api_key=os.getenv("GEMINI_API_KEY"),
    )
    
    # Generate reflection with error handling
    try:
        result = llm.with_structured_output(Reflection).invoke(formatted_prompt)
        
        if result is None:
            # Fallback: assume research is sufficient and stop
            return {
                "is_sufficient": True,
                "knowledge_gap": "",
                "follow_up_queries": [],
                "research_loop_count": state["research_loop_count"],
                "number_of_ran_queries": len(state["search_query"]),
            }
        
        # Ensure all required attributes exist
        is_sufficient = getattr(result, 'is_sufficient', True)
        knowledge_gap = getattr(result, 'knowledge_gap', "")
        follow_up_queries = getattr(result, 'follow_up_queries', [])
        
        # Ensure follow_up_queries is a list
        if follow_up_queries is None:
            follow_up_queries = []
        elif not isinstance(follow_up_queries, list):
            follow_up_queries = []

        return {
            "is_sufficient": is_sufficient,
            "knowledge_gap": knowledge_gap,
            "follow_up_queries": follow_up_queries,
            "research_loop_count": state["research_loop_count"],
            "number_of_ran_queries": len(state["search_query"]),
        }
    except Exception as e:
        # Fallback: assume research is sufficient and stop
        print(f"Error in reflection: {e}. Assuming research is sufficient.")
        return {
            "is_sufficient": True,
            "knowledge_gap": "",
            "follow_up_queries": [],
            "research_loop_count": state["research_loop_count"],
            "number_of_ran_queries": len(state["search_query"]),
        }

def evaluate_research(
    state: ReflectionState,
    config: RunnableConfig,
) -> OverallState:
    """LangGraph routing function that determines the next step in the research flow.

    Controls the research loop by deciding whether to continue gathering information
    or to finalize the summary based on the configured maximum number of research loops.

    Args:
        state: Current graph state containing the research loop count
        config: Configuration for the runnable, including max_research_loops setting

    Returns:
        String literal indicating the next node to visit ("web_research" or "finalize_summary")
    """
    configurable = Configuration.from_runnable_config(config)
    max_research_loops = (
        state.get("max_research_loops")
        if state.get("max_research_loops") is not None
        else configurable.max_research_loops
    )
    if state["is_sufficient"] or state["research_loop_count"] >= max_research_loops:
        return "finalize_answer"
    else:
        return [
            Send(
                "web_research",
                {
                    "search_query": follow_up_query,
                    "id": state["number_of_ran_queries"] + int(idx),
                },
            )
            for idx, follow_up_query in enumerate(state["follow_up_queries"])
        ]

def finalize_answer(state: OverallState, config: RunnableConfig):
    """LangGraph node that finalizes the research summary.

    Prepares the final output by combining web research and RAG results,
    deduplicating and formatting sources, then creating a well-structured
    research report with proper citations.

    Args:
        state: Current graph state containing the running summary, web research results, and RAG results

    Returns:
        Dictionary with state update, including running_summary key containing the formatted final summary with sources
    """
    configurable = Configuration.from_runnable_config(config)
    reasoning_model = state.get("reasoning_model") or configurable.answer_model

    # Combine web research and RAG results
    web_summaries = state.get("web_research_result", [])
    rag_summaries = state.get("rag_results", [])
    
    # Create a comprehensive summary from both sources
    all_summaries = []
    
    if web_summaries:
        all_summaries.append("=== Web Research Results ===")
        all_summaries.extend(web_summaries)
    
    if rag_summaries:
        all_summaries.append("\n=== Knowledge Base Results ===")
        all_summaries.extend(rag_summaries)
    
    combined_summaries = "\n---\n\n".join(all_summaries)

    # Format the prompt
    current_date = get_current_date()
    formatted_prompt = answer_instructions.format(
        current_date=current_date,
        research_topic=get_research_topic(state["messages"]),
        summaries=combined_summaries,
    )

    # init Reasoning Model, default to Gemini 2.0
    llm = ChatGoogleGenerativeAI(
        model=reasoning_model,
        temperature=0,
        max_retries=2,
        api_key=os.getenv("GEMINI_API_KEY"),
    )
    result = llm.invoke(formatted_prompt)

    # Replace the short urls with the original urls and add all used urls to the sources_gathered
    unique_sources = []
    for source in state["sources_gathered"]:
        if source["short_url"] in result.content:
            result.content = result.content.replace(
                source["short_url"], source["value"]
            )
            unique_sources.append(source)

    return {
        "messages": [AIMessage(content=result.content)],
        "sources_gathered": unique_sources,
    }

# Create our Agent Graph
builder = StateGraph(OverallState, config_schema=Configuration)

# Define the nodes we will cycle between
builder.add_node("generate_query", generate_query)
builder.add_node("rag_search", rag_search)
builder.add_node("web_research", web_research)
builder.add_node("reflection", reflection)
builder.add_node("finalize_answer", finalize_answer)

# Set the entrypoint as `generate_query`
# This means that this node is the first one called
builder.add_edge(START, "generate_query")
# First perform RAG search
builder.add_edge("generate_query", "rag_search")
# Add conditional edge to continue with search queries in a parallel branch
builder.add_conditional_edges(
    "rag_search", continue_to_web_research, ["web_research"]
)
# Reflect on the web research
builder.add_edge("web_research", "reflection")
# Evaluate the research
builder.add_conditional_edges(
    "reflection", evaluate_research, ["web_research", "finalize_answer"]
)
# Finalize the answer
builder.add_edge("finalize_answer", END)

graph = builder.compile(name="pro-search-agent")


