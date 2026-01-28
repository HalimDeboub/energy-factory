# app/llm_setup.py
from langchain_ollama import OllamaLLM, OllamaEmbeddings

class LLMFactory:
    def __init__(self):
        self.base_url = "http://localhost:11434"
        
    def get_llm(self, model="llama3.1:8b", temperature=0.1):
        """Get Ollama LLM instance"""
        return OllamaLLM(
            model=model,
            base_url=self.base_url,
            temperature=temperature,
            num_predict=2048
        )
    
    def get_embeddings(self, model="nomic-embed-text"):
        """Get embeddings for RAG"""
        return OllamaEmbeddings(
            model=model,
            base_url=self.base_url
        )