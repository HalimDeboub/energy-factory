from langchain_core.chat_history import BaseChatMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory 

class EnergyMemory:
    """Manages the memory of the energy agent, storing and retrieving past interactions."""
    
    def __init__(self):
        self.store = {}
        
        
    def get_session_history(self, session_id: str) -> BaseChatMessageHistory:
        """Retrieve the message history for a given session."""
        if session_id not in self.store:
            self.store[session_id] = ChatMessageHistory()
        return self.store[session_id]
        
    def with_memory(self, chain):
        """wrap any chain to include message history from the current session."""
        return RunnableWithMessageHistory (
            chain,
            self.get_session_history,
            input_message_key="query",  # Assuming the input key for the chain is "query"
            output_message_key="history",  # Assuming the chain's output key is "response"
        )
        
       
