# app/database/redis_client.py
import redis
from langchain.memory import RedisChatMessageHistory

class AgentMemory:
    def __init__(self):
        self.redis_client = redis.Redis(
            host='localhost',
            port=6379,
            decode_responses=True
        )
    
    def save_conversation(self, session_id: str, messages: list):
        """Save conversation to Redis"""
        history = RedisChatMessageHistory(
            session_id=session_id,
            url="redis://localhost:6379"
        )
        for message in messages:
            history.add_message(message)
    
    def get_conversation(self, session_id: str):
        """Retrieve conversation from Redis"""
        history = RedisChatMessageHistory(
            session_id=session_id,
            url="redis://localhost:6379"
        )
        return history.messages