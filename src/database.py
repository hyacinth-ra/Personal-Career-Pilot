import os
from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader, TextLoader, UnstructuredMarkdownLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

def load_all_docs(data_path):
    loaders = {
        ".pdf": PyPDFLoader,
        ".txt": TextLoader,
        ".md": UnstructuredMarkdownLoader,
    }
    documents = []
    for extension, loader_class in loaders.items():
        # Create a loader for each specific file type
        loader = DirectoryLoader(
            data_path, 
            glob=f"**/*{extension}", 
            loader_cls=loader_class,
            use_multithreading=True 
        )
        loaded_docs = loader.load()
        documents.extend(loaded_docs)
    return documents

def initialize_vector_store(DATA_PATH = "./knowledge_base", PERSIST_PATH = "./chroma_db"):  
    all_docs = load_all_docs(DATA_PATH)
    if not all_docs:
        return None
    
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_documents(all_docs)
    
    print(f"--- Syncing {len(chunks)} chunks to ChromaDB ---")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=PERSIST_PATH
    )
    print("--- Success! Vector store initialized and saved. ---")
    return vector_store

def get_retriever(PERSIST_PATH = "./chroma_db"):
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    vector_store = Chroma(
        persist_directory=PERSIST_PATH, 
        embedding_function=embeddings
    )
    
    return vector_store.as_retriever(search_kwargs={"k": 3})

if __name__ == "__main__":
    # 1. Initialize (Run this once to build the DB)
    # initialize_vector_store() 
    
    # 2. Query
    get_retriever("What is my experience with Python?")