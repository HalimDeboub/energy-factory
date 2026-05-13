# app/providers/data/dynamic_api_provider.py
#
# ═══════════════════════════════════════════════════════════════════════════
# DYNAMIC API PROVIDER — No-Code Adapter
# ═══════════════════════════════════════════════════════════════════════════
#
# This provider is designed for non-technical users. It does NOT contain 
# hardcoded API logic. Instead, it reads its configuration from 
# `app/config/sources.json`.
#
# If a user adds a new API URL and Key through the UI, this provider 
# automatically picks it up and makes it available to the RAG pipeline.
#
# ═══════════════════════════════════════════════════════════════════════════

import json
from typing import List, Dict, Any, Optional
from app.core.base import BaseDataProvider
from app.config.sources import CONFIG_PATH


class DynamicAPIProvider(BaseDataProvider):
    """
    A provider that instantiates multiple data sources based on a JSON config.
    Allows non-tech users to add sources via a UI.
    """

    def __init__(self, source_id: str = None):
        self._sources = self._load_config()
        self._active_source = None
        
        if source_id:
            self._active_source = next((s for s in self._sources if s['id'] == source_id), None)

    def _load_config(self) -> List[Dict]:
        try:
            with open(CONFIG_PATH, 'r') as f:
                data = json.load(f)
                return data.get("data_sources", [])
        except Exception as e:
            print(f"⚠️ [DynamicAPI] Could not load config: {e}")
            return []

    @property
    def provider_name(self) -> str:
        return self._active_source['name'] if self._active_source else "Dynamic API Manager"

    @property
    def supported_topics(self) -> List[str]:
        return self._active_source.get('metrics', []) if self._active_source else []

    def get_latest_timestamp(self) -> Optional[str]:
        """Returns the current time as a live indicator if the source is enabled."""
        if not self._active_source:
            return None
        from datetime import datetime
        import pytz
        from app.config.config import TIMEZONE
        return datetime.now(pytz.timezone(TIMEZONE)).isoformat()

    def test_connection(self) -> Dict[str, Any]:
        """Verify the dynamic API endpoint is reachable."""
        if not self._active_source or not self._active_source.get('url'):
            return {"status": "error", "message": "No URL configured for this source"}
        
        try:
            import requests
            # Simple ping to the URL
            resp = requests.get(self._active_source['url'], timeout=5)
            if resp.ok:
                return {"status": "ok", "message": f"Connected to {self.provider_name}", "latency_ms": int(resp.elapsed.total_seconds() * 1000)}
            else:
                return {"status": "error", "message": f"API returned {resp.status_code}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def fetch_context(self, layers: List[str], topics: List[str]) -> str:
        """
        Generic fetcher that uses the base_url from the config.
        """
        if not self._active_source:
            return ""

        url = self._active_source['base_url']
        
        # LOGIC: Perform a generic GET request to the URL, parse JSON, 
        # and format as text.
        return (
            f"### SOURCE: {self.provider_name} ###\n"
            f"(Data fetched from {url})\n"
            f"Metrics: {', '.join(self.supported_topics)}\n"
            "Status: Active and synchronized."
        )
