# app/llm_setup.py
from langchain_community.llms import Ollama
from langchain_community.embeddings import OllamaEmbeddings
import os

class LLMFactory:
    def __init__(self):
        # Set up Ollama - make sure you have Ollama running locally
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    
    def get_llm(self, model="llama3.1:8b", temperature=0.1):
        """Get LLM instance"""
        try:
            return Ollama(
                base_url=self.ollama_base_url,
                model=model,
                temperature=temperature
            )
        except Exception as e:
            print(f"Warning: Could not create LLM: {e}")
            # Return a dummy LLM for testing
            class DummyLLM:
                def invoke(self, prompt):
                    return "LLM is not available. Please install Ollama or use a different LLM."
            return DummyLLM()
    
    def get_embeddings(self, model="nomic-embed-text"):
        """Get embeddings instance"""
        try:
            return OllamaEmbeddings(
                base_url=self.ollama_base_url,
                model=model
            )
        except Exception:
            # Return dummy embeddings
            class DummyEmbeddings:
                def embed_documents(self, texts):
                    return [[0.1] * 384 for _ in texts]
                def embed_query(self, text):
                    return [0.1] * 384
            return DummyEmbeddings()