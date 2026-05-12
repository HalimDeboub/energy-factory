# app/agents/time_intent_parser.py
#
# LLM-based temporal intent parser with a keyword fast-path.
#
# Strategy:
#   1. Run a cheap keyword scan first (microseconds).
#   2. If keywords give high-confidence result → return immediately (no LLM call).
#   3. If the query is ambiguous → fall through to the LLM, which runs with
#      a lean config (num_ctx=512, num_predict=80) for fast inference.
#
# This keeps the LLM parser for real ambiguous cases while eliminating the
# extra LLM round-trip for the majority of queries.

import json
import re
from typing import Any, Dict, List, Optional

from langchain_ollama import OllamaLLM
from app.config.config import OLLAMA_HOST, OLLAMA_MODEL

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VALID_LAYERS = {"realtime", "today", "yesterday", "last_7_days", "last_30_days"}

FALLBACK_INTENT: Dict[str, Any] = {
    "time_range": ["today"],
    "compare_with": [],
    "confidence": 0.3,
}

CONFIDENCE_THRESHOLD = 0.5  # referenced by rag_pipeline.py

# ---------------------------------------------------------------------------
# Keyword tables (ordered most-specific → least-specific within each layer)
# ---------------------------------------------------------------------------

LAYER_KEYWORDS: Dict[str, List[str]] = {
    "last_30_days": [
        # English
        "last month", "past month", "30 days", "thirty days",
        "monthly trend", "monthly", "past 30",
        # French
        "le mois dernier", "mois dernier", "mois passé",
        "30 jours", "trente jours", "tendance mensuelle",
        # Arabic / Darija
        "الشهر الماضي", "الشهر لي فات", "30 يوم", "ثلاثين يوم", "شهر كامل",
    ],
    "last_7_days": [
        # English
        "last week", "past week", "7 days", "seven days",
        "past 7", "this week", "weekly",
        # French
        "la semaine dernière", "semaine dernière", "semaine passée",
        "7 jours", "sept jours", "cette semaine",
        # Arabic / Darija
        "الأسبوع الماضي", "الأسبوع لي فات", "7 أيام", "سبعة أيام", "الأسبوع",
    ],
    "yesterday": [
        # English
        "yesterday", "last night", "the day before",
        # French
        "hier", "la veille", "nuit dernière",
        # Arabic / Darija
        "أمس", "البارح", "أمسية", "بالأمس",
    ],
    "realtime": [
        # English
        "right now", "at this moment", "at the moment",
        "real-time", "realtime", "live data", "live",
        "currently", "current", "at present", "presently",
        "immediate", "now",
        # French
        "en ce moment", "en temps réel", "en direct",
        "maintenant", "actuellement", "à l'instant", "présentement",
        # Arabic / Darija
        "في الوقت الحالي", "هذه اللحظة", "مباشرة",
        "حالياً", "الآن", "دروك", "هلأ",
    ],
    "today": [
        # English
        "today", "this morning", "this evening",
        "this afternoon", "today's", "so far today",
        # French
        "aujourd'hui", "ce matin", "ce soir",
        "cet après-midi", "dans la journée",
        # Arabic / Darija
        "اليوم", "هذا اليوم", "الصباح هذا", "في اليوم",
    ],
}

COMPARISON_KEYWORDS: List[str] = [
    # English
    "compare", "compared to", "compared with",
    "versus", " vs ", "vs.", "relative to", "against", "than",
    # French
    "comparé à", "comparé avec", "par rapport à",
    "comparer", "en comparaison", "versus",
    # Arabic / Darija
    "مقارنة بـ", "مقارنة ب", "مقارنة", "مقابل", "بالمقارنة", "قارن",
]

# ---------------------------------------------------------------------------
# LLM prompt (used only when keyword fast-path is inconclusive)
# ---------------------------------------------------------------------------

INTENT_PROMPT_TEMPLATE = """\
You classify time ranges for energy queries. Return ONLY a JSON object, nothing else.

VALID LAYERS: realtime, today, yesterday, last_7_days, last_30_days

FORMAT:
{{"time_range": ["<layer>"], "compare_with": [], "confidence": 0.0-1.0}}

RULES:
- time_range = primary period asked about
- compare_with = only if query explicitly compares two periods, else []
- confidence: 0.9=clear, 0.6=somewhat clear, 0.3=vague
- Unknown intent → {{"time_range": ["today"], "compare_with": [], "confidence": 0.3}}

EXAMPLES:
"What is consumption now?" → {{"time_range": ["realtime"], "compare_with": [], "confidence": 0.95}}
"Compare today to last week" → {{"time_range": ["today"], "compare_with": ["last_7_days"], "confidence": 0.9}}
"Show monthly trend" → {{"time_range": ["last_30_days"], "compare_with": [], "confidence": 0.85}}
"كيف راه الاستهلاك اليوم مقارنة بالأسبوع لي فات؟" → {{"time_range": ["today"], "compare_with": ["last_7_days"], "confidence": 0.9}}
"Tell me about energy" → {{"time_range": ["today"], "compare_with": [], "confidence": 0.35}}

Query: "{query}"
JSON:"""


# ---------------------------------------------------------------------------
# TimeIntentParser
# ---------------------------------------------------------------------------


class TimeIntentParser:
    """
    Temporal intent parser with two-stage resolution:

      Stage 1 — Keyword fast-path (instant, no LLM call):
        Scans the query for multilingual time keywords.
        If the result is clear (confidence >= 0.85), returns immediately.

      Stage 2 — LLM fallback (lean config, fast inference):
        Used only when the query is too ambiguous for keywords alone.
        The LLM runs with num_ctx=512 / num_predict=80 for low latency.

    Accepts `llm` in __init__ but creates its own lean OllamaLLM internally
    using the same base_url and model as the main LLM.
    """

    CONFIDENCE_THRESHOLD = CONFIDENCE_THRESHOLD
    # Keyword fast-path only returns early if confidence meets this bar
    _KEYWORD_SHORTCIRCUIT_THRESHOLD = 0.85

    def __init__(self, llm: OllamaLLM) -> None:
        self.llm = llm
        # Lean LLM for intent parsing only:
        # - num_ctx=512  → much smaller KV cache → faster prefill
        # - num_predict=80 → JSON output is ~50 tokens, stop early
        # - temperature=0  → greedy decoding, no sampling overhead
        # Use config constants directly — `llm` may be a RunnableRetry wrapper
        # and therefore won't expose .base_url / .model attributes.
        self._intent_llm = OllamaLLM(
            base_url=OLLAMA_HOST,
            model=OLLAMA_MODEL,
            temperature=0,
            num_ctx=512,
            num_predict=80,
            request_timeout=60.0,
        )

    # ------------------------------------------------------------------
    # Stage 1 — Keyword fast-path
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize(text: str) -> str:
        return re.sub(r"\s+", " ", text.strip().lower())

    def _find_layers(self, text: str) -> List[str]:
        found: List[str] = []
        for layer, keywords in LAYER_KEYWORDS.items():
            for kw in keywords:
                if kw in text:
                    found.append(layer)
                    break
        return found

    @staticmethod
    def _has_comparison(text: str) -> bool:
        return any(kw in text for kw in COMPARISON_KEYWORDS)

    def _keyword_parse(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Try to resolve intent from keywords.
        Returns a result dict if confidence is high enough, else None.
        """
        text = self._normalize(query)
        layers = self._find_layers(text)
        has_comparison = self._has_comparison(text)

        if not layers:
            return None  # → fall through to LLM

        if len(layers) == 1:
            return {
                "time_range": layers,
                "compare_with": [],
                "confidence": 0.9,
            }

        if len(layers) == 2 and has_comparison:
            # Use text position to determine primary vs comparison layer
            def first_pos(layer: str) -> int:
                return min(
                    (text.find(kw) for kw in LAYER_KEYWORDS[layer] if kw in text),
                    default=len(text),
                )
            if first_pos(layers[0]) <= first_pos(layers[1]):
                primary, comparison = layers[0], layers[1]
            else:
                primary, comparison = layers[1], layers[0]
            return {
                "time_range": [primary],
                "compare_with": [comparison],
                "confidence": 0.9,
            }

        # Multiple layers without explicit comparison — less certain
        return {
            "time_range": layers,
            "compare_with": [],
            "confidence": 0.7,
        }

    # ------------------------------------------------------------------
    # Stage 2 — LLM fallback
    # ------------------------------------------------------------------

    def _extract_json(self, text: str) -> Dict[str, Any]:
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            pass
        match = re.search(r"\{.*?\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        raise ValueError(f"No valid JSON in LLM output: {text[:200]!r}")

    def _sanitize_layers(self, raw: Any) -> List[str]:
        if not isinstance(raw, list):
            return []
        return [item for item in raw if isinstance(item, str) and item in VALID_LAYERS]

    def _clamp_confidence(self, raw: Any) -> float:
        try:
            return max(0.0, min(1.0, float(raw)))
        except (TypeError, ValueError):
            return 0.5

    def _llm_parse(self, query: str) -> Dict[str, Any]:
        """Call the lean LLM to resolve ambiguous temporal intent."""
        prompt = INTENT_PROMPT_TEMPLATE.format(query=query)
        try:
            response = self._intent_llm.invoke(prompt)
            data = self._extract_json(response)

            time_range = self._sanitize_layers(data.get("time_range", []))
            compare_with = self._sanitize_layers(data.get("compare_with", []))
            confidence = self._clamp_confidence(data.get("confidence", 0.5))

            if not time_range:
                print(f"⚠️ [TimeIntentParser/LLM] No valid layers, using fallback. Raw: {data}")
                return {**FALLBACK_INTENT}

            return {
                "time_range": time_range,
                "compare_with": compare_with,
                "confidence": confidence,
            }
        except Exception as exc:
            print(f"⚠️ [TimeIntentParser/LLM] Failed ({type(exc).__name__}: {exc}), using fallback.")
            return {**FALLBACK_INTENT}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def parse(self, query: str) -> Dict[str, Any]:
        """
        Parse the temporal intent of a user query.

        Tries keyword fast-path first. Falls through to LLM only if the
        query is too ambiguous to resolve from keywords alone.

        Args:
            query: Raw user question (English, French, Arabic/Darija, etc.)

        Returns:
            {"time_range": [...], "compare_with": [...], "confidence": float}
        """
        # Stage 1 — keyword fast-path
        keyword_result = self._keyword_parse(query)
        if keyword_result and keyword_result["confidence"] >= self._KEYWORD_SHORTCIRCUIT_THRESHOLD:
            print(f"⚡ [TimeIntentParser/keywords] intent={keyword_result}  query='{query[:60]}'")
            return keyword_result

        # Stage 2 — LLM fallback for ambiguous queries
        print(f"🤖 [TimeIntentParser/LLM] Ambiguous query, calling LLM: '{query[:60]}'")
        result = self._llm_parse(query)
        print(f"🕐 [TimeIntentParser/LLM] intent={result}")
        return result