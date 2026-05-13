# app/core/base.py
#
# ═══════════════════════════════════════════════════════════════════════════
# THE PROVIDER INTERFACE — Standardizing Energy Sources
# ═══════════════════════════════════════════════════════════════════════════
#
# To make this project a "tool" for any data source, we must decouple the RAG
# pipeline from the specific data logic (RTE).
#
# We define two types of Providers:
#   1. DataProvider      → For "Numbers" (APIs, DBs, IoT).
#   2. KnowledgeProvider → For "Words" (PDFs, Documentation, Reports).
#
# ═══════════════════════════════════════════════════════════════════════════

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional


class BaseDataProvider(ABC):
    """
    Abstract Interface for any Structured Energy Data source.
    (e.g., RTE France, SolarEdge API, Home Assistant DB)
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Friendly name of the source (e.g. 'RTE France')"""
        pass

    @property
    @abstractmethod
    def supported_topics(self) -> List[str]:
        """List of metrics this source provides (e.g. ['nuclear', 'wind'])"""
        pass

    @abstractmethod
    def fetch_context(self, layers: List[str], topics: List[str]) -> str:
        """
        Retrieve structured data and format it as text for the LLM.
        
        Args:
            layers: Time periods needed (realtime, today, etc.)
            topics: Specific metrics to focus on.
        """
        pass

    @abstractmethod
    def get_latest_timestamp(self) -> str:
        """Returns the timestamp of the newest record (for cache invalidation)."""
        pass

    @abstractmethod
    def test_connection(self) -> Dict[str, Any]:
        """
        Tests if the source is reachable.
        Returns: {"status": "ok" | "error", "message": str, "latency_ms": int}
        """
        pass



class BaseKnowledgeProvider(ABC):
    """
    Abstract Interface for any Unstructured Knowledge source.
    (e.g., Vector DB of Energy Reports, PDFs, Web Search)
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Friendly name (e.g. 'Policy Documents')"""
        pass

    @abstractmethod
    def query_knowledge(self, query: str, top_k: int = 3) -> str:
        """
        Perform a semantic search and return relevant text excerpts.
        """
        pass
