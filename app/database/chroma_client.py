import chromadb
from chromadb.config import Settings
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_core.tools import tool


import os

class EnergyRAGSystem:
    def __init__(self, embedding_model="nomic-embed-text"):
        self.client = chromadb.HttpClient(
            host="localhost",
            port=8000,
            settings=Settings(allow_reset=True)
        )
        
        # Initialize LLM factory for embeddings
        from app.llm_setup import LLMFactory
        llm_factory = LLMFactory()
        self.embeddings = llm_factory.get_embeddings(embedding_model)
        
    def ingest_documents(self, docs_path: str):
        """Ingest energy documents into vector store"""
        documents = []
        
        # Load all PDFs in directory
        for file in os.listdir(docs_path):
            if file.endswith('.pdf'):
                loader = PyPDFLoader(os.path.join(docs_path, file))
                documents.extend(loader.load())
            elif file.endswith('.txt'):
                loader = TextLoader(os.path.join(docs_path, file))
                documents.extend(loader.load())
        
        # Split documents
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        splits = text_splitter.split_documents(documents)
        
        # Create vector store
        vector_store = Chroma.from_documents(
            documents=splits,
            embedding=self.embeddings,
            client=self.client,
            collection_name="energy_documents"
        )
        
        return f"Ingested {len(splits)} chunks from {len(documents)} documents"
    
    def query_documents(self, query: str, k: int = 3):
        """Query the RAG system"""
        vector_store = Chroma(
            client=self.client,
            collection_name="energy_documents",
            embedding_function=self.embeddings
        )
        
        results = vector_store.similarity_search(query, k=k)
        return "\n\n".join([doc.page_content for doc in results])
    
    @tool
    def search_energy_policies(self, query: str):
        """Search energy policy documents for relevant information"""
        return self.query_documents(query)