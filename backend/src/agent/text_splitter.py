from langchain_text_splitters import RecursiveCharacterTextSplitter

def split_text_into_chunks(pages):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1024, chunk_overlap=150
    )
    texts = text_splitter.split_text(pages)
    return texts