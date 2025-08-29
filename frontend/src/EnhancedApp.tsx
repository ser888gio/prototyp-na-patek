import { useStream } from "@langchain/langgraph-sdk/react";
import type { Message } from "@langchain/langgraph-sdk";
import { useState, useEffect, useRef, useCallback } from "react";
import { ProcessedEvent } from "@/components/ActivityTimeline";
import { WelcomeScreen } from "@/components/WelcomeScreen";
import { ChatMessagesView } from "@/components/ChatMessagesView";
import { ConversationList } from "@/components/ConversationList";
import { Button } from "@/components/ui/button";
import { useChatHistory } from "@/hooks/useChatHistory";
import { PanelLeft, PanelLeftClose } from "lucide-react";

export default function App() {
  console.log("🏠 EnhancedApp: Component loaded/rendered");

  const [processedEventsTimeline, setProcessedEventsTimeline] = useState<
    ProcessedEvent[]
  >([]);
  const [historicalActivities, setHistoricalActivities] = useState<
    Record<string, ProcessedEvent[]>
  >({});
  const [showSidebar, setShowSidebar] = useState(true);
  const [userId] = useState("default-user"); // In real app, get from auth
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const hasFinalizeEventOccurredRef = useRef(false);
  const [error, setError] = useState<string | null>(null);

  // Chat history management
  const chatHistory = useChatHistory(userId);

  // Debug logging
  useEffect(() => {
    console.log("🎨 EnhancedApp: Sidebar state changed", {
      showSidebar,
      userId,
      currentConversationId: chatHistory.currentConversation?.id,
    });
  }, [showSidebar, userId, chatHistory.currentConversation?.id]);

  const thread = useStream<{
    messages: Message[];
    initial_search_query_count: number;
    max_research_loops: number;
    reasoning_model: string;
    conversation_id?: string;
    user_id?: string;
  }>({
    apiUrl: import.meta.env.DEV
      ? "http://localhost:2024"
      : "http://localhost:8123",
    assistantId: "agent",
    messagesKey: "messages",
    onUpdateEvent: (event: any) => {
      let processedEvent: ProcessedEvent | null = null;
      if (event.generate_query) {
        processedEvent = {
          title: "Generating Search Queries",
          data: event.generate_query?.search_query?.join(", ") || "",
        };
      } else if (event.web_research) {
        const sources = event.web_research.sources_gathered || [];
        const numSources = sources.length;
        const uniqueLabels = [
          ...new Set(sources.map((s: any) => s.label).filter(Boolean)),
        ];
        const exampleLabels = uniqueLabels.slice(0, 3).join(", ");
        processedEvent = {
          title: "Web Research",
          data: `Gathered ${numSources} sources. Related to: ${
            exampleLabels || "N/A"
          }.`,
        };
      } else if (event.reflection) {
        processedEvent = {
          title: "Reflection",
          data: `Knowledge gap identified: ${
            event.reflection?.knowledge_gap || "N/A"
          }`,
        };
      } else if (event.finalize_answer) {
        hasFinalizeEventOccurredRef.current = true;
        processedEvent = {
          title: "Finalizing Answer",
          data: "Research complete, generating final response",
        };
      } else if (event.rag_search) {
        const resultCount = event.rag_search?.rag_results?.length || 0;
        processedEvent = {
          title: "RAG Search",
          data: `Found ${resultCount} relevant documents from knowledge base`,
        };
      }

      if (processedEvent) {
        setProcessedEventsTimeline((prevEvents) => [
          ...prevEvents,
          processedEvent!,
        ]);
      }
    },
    onError: (error: any) => {
      setError(error.message);
    },
  });

  // Debug logging for save function
  useEffect(() => {
    console.log("[DEBUG] EnhancedApp: chatHistory state:", {
      currentConversation: chatHistory.currentConversation,
      saveConversation: !!chatHistory.saveConversation,
      messagesLength: thread.messages.length,
    });
  }, [
    chatHistory.currentConversation,
    chatHistory.saveConversation,
    thread.messages.length,
  ]);

  // Save messages to history when they're added
  useEffect(() => {
    console.log(
      `[DEBUG] EnhancedApp: useEffect triggered - messages.length=${thread.messages.length}, currentConversation=${chatHistory.currentConversation?.id}`
    );
    console.log(`[DEBUG] EnhancedApp: chatHistory state:`, {
      currentConversation: chatHistory.currentConversation,
    });

    console.log(`[DEBUG] EnhancedApp: thread.messages:`, thread.messages);

    if (chatHistory.currentConversation && thread.messages.length > 0) {
      const lastMessage = thread.messages[thread.messages.length - 1];
      console.log(`[DEBUG] EnhancedApp: Last message:`, lastMessage);

      // Only save new messages (avoid duplicates)
      if (lastMessage && lastMessage.id) {
        console.log(
          `[DEBUG] EnhancedApp: Saving message ${lastMessage.id} to conversation ${chatHistory.currentConversation.id}`
        );

        // EMERGENCY: Let's try saving the message and catch any errors
        chatHistory
          .saveMessage(chatHistory.currentConversation.id, lastMessage)
          .catch((error) => {
            console.error(
              `[DEBUG] EnhancedApp: CRITICAL ERROR saving message:`,
              error
            );
          });

        // Auto-generate title from first human message
        if (
          chatHistory.currentConversation.title === "New Conversation" &&
          lastMessage.type === "human" &&
          typeof lastMessage.content === "string"
        ) {
          console.log(
            `[DEBUG] EnhancedApp: Auto-generating title for conversation from message: ${lastMessage.content.substring(
              0,
              50
            )}...`
          );
          chatHistory.autoGenerateTitle(
            chatHistory.currentConversation.id,
            lastMessage.content
          );
        }
      } else {
        console.log(
          `[DEBUG] EnhancedApp: Last message has no ID, skipping save. Message:`,
          lastMessage
        );
      }
    } else {
      console.log(
        `[DEBUG] EnhancedApp: Not saving - currentConversation exists: ${!!chatHistory.currentConversation}, messages.length: ${
          thread.messages.length
        }`
      );

      // EMERGENCY: If no current conversation but we have messages, try to create one
      if (!chatHistory.currentConversation && thread.messages.length > 0) {
        console.log(
          `[DEBUG] EnhancedApp: EMERGENCY - Creating conversation because messages exist but no conversation`
        );
        chatHistory
          .createConversation()
          .then((conv) => {
            console.log(
              `[DEBUG] EnhancedApp: Emergency conversation created:`,
              conv
            );
          })
          .catch((error) => {
            console.error(
              `[DEBUG] EnhancedApp: Emergency conversation creation failed:`,
              error
            );
          });
      }
    }
  }, [thread.messages, chatHistory]);

  useEffect(() => {
    if (scrollAreaRef.current) {
      const scrollViewport = scrollAreaRef.current.querySelector(
        "[data-radix-scroll-area-viewport]"
      );
      if (scrollViewport) {
        scrollViewport.scrollTop = scrollViewport.scrollHeight;
      }
    }
  }, [thread.messages]);

  useEffect(() => {
    if (
      hasFinalizeEventOccurredRef.current &&
      !thread.isLoading &&
      thread.messages.length > 0
    ) {
      const lastMessage = thread.messages[thread.messages.length - 1];
      if (lastMessage && lastMessage.type === "ai" && lastMessage.id) {
        setHistoricalActivities((prev) => ({
          ...prev,
          [lastMessage.id!]: [...processedEventsTimeline],
        }));
      }
      setProcessedEventsTimeline([]);
      hasFinalizeEventOccurredRef.current = false;
    }
  }, [thread.isLoading, thread.messages, processedEventsTimeline]);

  const handleSubmit = useCallback(
    (submittedInputValue: string, effort: string) => {
      let initial_search_query_count = 3;
      let max_research_loops = 1;

      switch (effort) {
        case "low":
          initial_search_query_count = 2;
          max_research_loops = 1;
          break;
        case "medium":
          initial_search_query_count = 3;
          max_research_loops = 2;
          break;
        case "high":
          initial_search_query_count = 5;
          max_research_loops = 10;
          break;
      }

      const newMessages: Message[] = [
        ...(thread.messages || []),
        {
          type: "human",
          content: submittedInputValue,
          id: Date.now().toString(),
        },
      ];

      thread.submit({
        messages: newMessages,
        initial_search_query_count: initial_search_query_count,
        max_research_loops: max_research_loops,
        conversation_id: chatHistory.currentConversation?.id,
        user_id: userId,
      });
    },
    [thread, chatHistory.currentConversation, userId]
  );

  const handleCancel = useCallback(() => {
    thread.stop();
    window.location.reload();
  }, [thread]);

  const handleSelectConversation = useCallback(
    async (conversationId: string) => {
      try {
        const messages = await chatHistory.loadConversation(conversationId);
        // Reset the thread with the loaded messages
        thread.submit({
          messages: messages,
          initial_search_query_count: 3,
          max_research_loops: 1,
          conversation_id: conversationId,
          user_id: userId,
        });
        setProcessedEventsTimeline([]);
        setHistoricalActivities({});
      } catch (err) {
        console.error("Failed to load conversation:", err);
        setError("Failed to load conversation");
      }
    },
    [chatHistory, thread, userId]
  );

  const handleCreateConversation = useCallback(async () => {
    try {
      await chatHistory.createConversation();
      // Reset the UI for new conversation
      thread.submit({
        messages: [],
        initial_search_query_count: 3,
        max_research_loops: 1,
        conversation_id: chatHistory.currentConversation?.id,
        user_id: userId,
      });
      setProcessedEventsTimeline([]);
      setHistoricalActivities({});
    } catch (err) {
      console.error("Failed to create conversation:", err);
      setError("Failed to create conversation");
    }
  }, [chatHistory, thread, userId]);

  return (
    <div className="flex h-screen bg-background text-foreground font-sans antialiased">
      {/* Logo in upper left corner */}
      <div className="absolute top-4 left-4 z-50">
        <img
          src="scanservice-logo.png"
          alt="ScanService Logo"
          className="h-8 w-auto"
        />
      </div>

      {/* Sidebar toggle button */}
      <div className="absolute top-4 right-4 z-50">
        <Button
          variant="outline"
          size="sm"
          onClick={() => setShowSidebar(!showSidebar)}
          className="flex items-center gap-2"
        >
          {showSidebar ? (
            <>
              <PanelLeftClose className="h-4 w-4" />
              Hide History
            </>
          ) : (
            <>
              <PanelLeft className="h-4 w-4" />
              Show History
            </>
          )}
        </Button>
      </div>

      {/* Sidebar */}
      {showSidebar && (
        <div className="w-80 border-r border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
          <ConversationList
            currentConversationId={chatHistory.currentConversation?.id}
            onSelectConversation={handleSelectConversation}
            onCreateConversation={handleCreateConversation}
            userId={userId}
          />
        </div>
      )}

      <main
        className={`flex-1 h-full ${
          showSidebar ? "max-w-4xl" : "max-w-6xl"
        } mx-auto`}
      >
        {thread.messages.length === 0 ? (
          <WelcomeScreen
            handleSubmit={handleSubmit}
            isLoading={thread.isLoading}
            onCancel={handleCancel}
          />
        ) : error ? (
          <div className="flex flex-col items-center justify-center h-full">
            <div className="flex flex-col items-center justify-center gap-4">
              <h1 className="text-2xl text-red-400 font-bold">Error</h1>
              <p className="text-red-400">{JSON.stringify(error)}</p>

              <Button
                variant="destructive"
                onClick={() => {
                  setError(null);
                  window.location.reload();
                }}
              >
                Retry
              </Button>
            </div>
          </div>
        ) : (
          <ChatMessagesView
            messages={thread.messages}
            isLoading={thread.isLoading}
            scrollAreaRef={scrollAreaRef}
            onSubmit={handleSubmit}
            onCancel={handleCancel}
            liveActivityEvents={processedEventsTimeline}
            historicalActivities={historicalActivities}
            onSaveConversation={chatHistory.saveConversation}
            currentConversationId={chatHistory.currentConversation?.id}
          />
        )}
      </main>

      {/* Chat history loading/error states */}
      {chatHistory.isLoading && (
        <div className="absolute bottom-4 right-4 bg-muted p-2 rounded-lg">
          Loading chat history...
        </div>
      )}

      {chatHistory.error && (
        <div className="absolute bottom-4 right-4 bg-destructive text-destructive-foreground p-2 rounded-lg">
          {chatHistory.error}
        </div>
      )}
    </div>
  );
}
