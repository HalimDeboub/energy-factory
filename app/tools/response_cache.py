# app/tools/response_cache.py
#
# ═══════════════════════════════════════════════════════════════════════════
# WHY CACHING MATTERS IN A RAG SYSTEM
# ═══════════════════════════════════════════════════════════════════════════
#
# In a standard RAG pipeline every user query triggers at minimum:
#   1. A retrieval step  (DB queries + context building)
#   2. An LLM inference  (the slow part — ~20s on CPU)
#
# This is fine when the answer COULD be different every time.
# But in this energy system the underlying data only changes every 15 minutes
# (eco2mix publishes a new record every 15 min).
#
# That means:
#   • "What is consumption now?" asked at 14:01 and at 14:10
#     will produce IDENTICAL context → IDENTICAL answer.
#   • Running the full LLM pipeline twice is pure waste.
#
# Solution: cache the LLM answer keyed on (query + layers used + data version).
# If the same question is asked before the data changes → return instantly.
#
# ═══════════════════════════════════════════════════════════════════════════
# CACHE KEY DESIGN
# ═══════════════════════════════════════════════════════════════════════════
#
# Key = hash of (normalized_query  +  sorted_layers)
#
#   normalized_query:
#     • lowercased
#     • punctuation removed
#     • whitespace collapsed
#     This makes "What is consumption NOW?" and "what is consumption now"
#     hit the same cache entry.
#
#   sorted_layers:
#     The time layers selected by TimeIntentParser (e.g. ["realtime"]).
#     We sort them so ["today", "realtime"] == ["realtime", "today"].
#
# ═══════════════════════════════════════════════════════════════════════════
# CACHE INVALIDATION STRATEGY
# ═══════════════════════════════════════════════════════════════════════════
#
# A cache entry is considered STALE (and discarded) when EITHER:
#   1. The latest DB record timestamp has changed
#      (new eco2mix data arrived → answers may differ)
#   2. The entry is older than `ttl_minutes` (hard safety cap, default 15 min)
#
# Using the data timestamp as the primary invalidation signal is smarter than
# a pure TTL because:
#   • If the scheduler is delayed the cache stays valid longer (correct).
#   • As soon as new data arrives the cache is cleared (also correct).
#
# ═══════════════════════════════════════════════════════════════════════════

import hashlib
import re
from datetime import datetime
from typing import Dict, List, Optional


# ── Data class for a single cache entry ────────────────────────────────────

class CacheEntry:
    """
    Stores one cached LLM answer together with its validity metadata.

    Attributes:
        answer         : The LLM-generated answer string.
        layers         : The time layers that were used to build the context.
        data_timestamp : The `date_heure` of the latest DB record at cache time.
                         Used to detect when fresh data has arrived.
        cached_at      : Wall-clock time this entry was stored.
    """

    def __init__(self, answer: str, layers: List[str], data_timestamp: str) -> None:
        self.answer = answer
        self.layers = layers
        self.data_timestamp = data_timestamp
        self.cached_at = datetime.now()

    def is_valid(self, current_data_timestamp: str, ttl_minutes: int) -> bool:
        """
        Return True if this entry can still be served.

        Two independent expiry conditions:
          1. Hard TTL — entry is too old regardless of data.
          2. Data version — a newer DB record has been inserted.
        """
        # Condition 1: hard TTL check
        age_minutes = (datetime.now() - self.cached_at).total_seconds() / 60
        if age_minutes > ttl_minutes:
            return False

        # Condition 2: data freshness check
        # If the DB now has a newer record, this answer is potentially outdated.
        if current_data_timestamp and current_data_timestamp != self.data_timestamp:
            return False

        return True


# ── Main cache class ────────────────────────────────────────────────────────

class ResponseCache:
    """
    In-memory LRU-free cache for LLM answers.

    Usage pattern inside the RAG pipeline:
    ┌─────────────────────────────────────────────┐
    │ cache.get(query, layers, data_ts)            │
    │   ├─ HIT  → return answer immediately ⚡    │
    │   └─ MISS → run LLM pipeline                │
    │              cache.set(...)                  │
    │              return answer                   │
    └─────────────────────────────────────────────┘
    """

    def __init__(self, ttl_minutes: int = 15) -> None:
        """
        Args:
            ttl_minutes: Maximum age of a cache entry.
                         Should match the data refresh interval (default 15 min).
        """
        self.ttl_minutes = ttl_minutes

        # The store is a plain dict: cache_key (str) → CacheEntry
        # In production you would replace this with Redis, but an in-memory
        # dict is perfectly adequate here since we have one process.
        self._store: Dict[str, CacheEntry] = {}

        # Stats counters — useful for understanding cache effectiveness
        self._hits = 0
        self._misses = 0

    # ── Key construction ────────────────────────────────────────────────────

    @staticmethod
    def _normalize_query(query: str) -> str:
        """
        Convert a raw user query into a canonical form for key comparison.

        Examples:
          "What is consumption NOW?"  →  "what is consumption now"
          "  Tell me   about wind "   →  "tell me about wind"
          "كيف راه الاستهلاك اليوم؟"  →  "كيف راه الاستهلاك اليوم"

        We keep Arabic/French characters (\u0600-\u06FF covers Arabic Unicode).
        """
        text = query.lower().strip()
        # Remove punctuation but preserve letters (Latin + Arabic + accented)
        text = re.sub(r"[^\w\s\u0600-\u06FF]", " ", text)
        # Collapse all whitespace runs into a single space
        text = re.sub(r"\s+", " ", text).strip()
        return text

    @staticmethod
    def _make_key(normalized_query: str, layers: List[str]) -> str:
        """
        Build a short, unique cache key.

        We MD5-hash the concatenation of query + sorted layers.
        MD5 is not used here for security — just for compact, fixed-length keys.

        Example:
          query = "what is consumption now"
          layers = ["realtime"]
          raw    = "what is consumption now|realtime"
          key    = md5("what is consumption now|realtime") → "a3f9..."
        """
        layers_str = ",".join(sorted(layers))          # sort so order doesn't matter
        raw = f"{normalized_query}|{layers_str}"
        return hashlib.md5(raw.encode("utf-8")).hexdigest()

    # ── Public API ──────────────────────────────────────────────────────────

    def get(
        self,
        query: str,
        layers: List[str],
        current_data_timestamp: str,
    ) -> Optional[str]:
        """
        Look up a cached answer.

        Args:
            query                 : Raw user query.
            layers                : Time layers selected by the intent parser.
            current_data_timestamp: `date_heure` of the latest DB record RIGHT NOW.
                                    Used to detect stale entries.

        Returns:
            The cached answer string if valid, or None (cache miss).
        """
        key = self._make_key(self._normalize_query(query), layers)
        entry = self._store.get(key)

        if entry is None:
            # Key not in store at all
            self._misses += 1
            print(f"❌ [Cache MISS] key={key[:8]}… (not found)")
            return None

        if not entry.is_valid(current_data_timestamp, self.ttl_minutes):
            # Entry exists but is stale — remove it proactively
            del self._store[key]
            self._misses += 1
            print(f"❌ [Cache MISS] key={key[:8]}… (stale/expired)")
            return None

        # Cache hit!
        self._hits += 1
        age = (datetime.now() - entry.cached_at).total_seconds()
        print(f"⚡ [Cache HIT]  key={key[:8]}… (age={age:.0f}s, layers={layers})")
        return entry.answer

    def set(
        self,
        query: str,
        layers: List[str],
        answer: str,
        data_timestamp: str,
    ) -> None:
        """
        Store an LLM answer in the cache.

        Args:
            query          : Raw user query.
            layers         : Time layers that were used to build the context.
            answer         : The LLM-generated answer to cache.
            data_timestamp : `date_heure` of the latest DB record at answer time.
        """
        key = self._make_key(self._normalize_query(query), layers)
        self._store[key] = CacheEntry(answer, layers, data_timestamp)
        print(f"💾 [Cache SET]  key={key[:8]}… (layers={layers}, data_ts={data_timestamp})")

    def clear(self) -> None:
        """Manually flush the entire cache (useful for testing)."""
        count = len(self._store)
        self._store.clear()
        print(f"🗑️  [Cache] Cleared {count} entries.")

    # ── Stats / observability ───────────────────────────────────────────────

    @property
    def stats(self) -> Dict:
        """
        Return cache performance statistics.

        Hit rate tells you how effective the cache is:
          • 0%   → every query is unique / data changes too fast
          • 80%+ → users ask similar questions repeatedly — great savings
        """
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0.0
        return {
            "entries":  len(self._store),
            "hits":     self._hits,
            "misses":   self._misses,
            "hit_rate": f"{hit_rate:.1f}%",
            "ttl_min":  self.ttl_minutes,
        }
