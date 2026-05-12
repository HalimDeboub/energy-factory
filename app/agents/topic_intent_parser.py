# app/agents/topic_intent_parser.py
#
# ═══════════════════════════════════════════════════════════════════════════
# WHAT IS TOPIC INTENT?
# ═══════════════════════════════════════════════════════════════════════════
#
# The TimeIntentParser answers:  "WHEN does the user want data?"
# The TopicIntentParser answers: "WHAT does the user want to know about?"
#
# Without topic detection, the LLM sees ALL available metrics in the context
# (nuclear, wind, solar, CO₂, consumption, hydro, gas, exchanges) and has
# to decide which ones to include in its answer. This often leads to
# unfocused answers that mention too many irrelevant figures.
#
# With topic detection:
#   "How is wind doing?"       → topics: [wind]
#   "CO₂ status?"              → topics: [co2]
#   "Nuclear vs renewables"    → topics: [nuclear, renewable]
#   "Give me a full overview"  → topics: []  (general → no filtering)
#
# The detected topics are converted into a FOCUS HINT — a short natural
# language instruction injected into the system prompt:
#
#   "FOCUS: Answer specifically about wind production.
#    Mention other data only if directly relevant."
#
# This guides the LLM without touching the context itself, keeping the
# architecture simple.
#
# ═══════════════════════════════════════════════════════════════════════════
# AVAILABLE TOPICS (match the eco2mix / CRITICAL_FIELDS in config.py)
# ═══════════════════════════════════════════════════════════════════════════
#
#   consumption   → consommation field
#   nuclear       → nucleaire field
#   wind          → eolien field
#   solar         → solaire field
#   hydro         → hydraulique field
#   gas           → gaz field
#   co2           → taux_co2 field
#   exchange      → ech_physiques field
#   renewable     → combination of wind + solar + hydro
#   production    → all generation sources combined
#
# ═══════════════════════════════════════════════════════════════════════════

import re
from typing import Dict, List, Any


# ─────────────────────────────────────────────────────────────────────────────
# Keyword tables — same pattern as TimeIntentParser
# Ordered most-specific → least-specific within each topic
# ─────────────────────────────────────────────────────────────────────────────

TOPIC_KEYWORDS: Dict[str, List[str]] = {

    # ── Nuclear ───────────────────────────────────────────────────────────
    "nuclear": [
        # English
        "nuclear", "nucleaire", "atomic", "fission", "reactor", "uranium",
        "epr", "edf",
        # French
        "nucléaire", "réacteur", "atome", "centrale",
        # Arabic / Darija
        "النووي", "الطاقة النووية", "المفاعل النووي", "نووي", "مفاعل",
    ],

    # ── Wind ──────────────────────────────────────────────────────────────
    "wind": [
        # English
        "wind", "eolian", "turbine", "offshore wind", "onshore wind", "windmill",
        # French
        "éolien", "eolien", "vent", "éolienne",
        # Arabic / Darija
        "الرياح", "طاقة الرياح", "الطاقة الريحية", "الريح", "مولدات الرياح",
    ],

    # ── Solar ─────────────────────────────────────────────────────────────
    "solar": [
        # English
        "solar", "photovoltaic", " pv ", "sunshine", "solar panel",
        # French
        "solaire", "photovoltaïque", "panneau solaire", "soleil",
        # Arabic / Darija
        "الطاقة الشمسية", "الشمسي", "الشمس", "شمسية", "ألواح شمسية",
    ],

    # ── Hydro ─────────────────────────────────────────────────────────────
    "hydro": [
        # English
        "hydro", "hydroelectric", "dam", "water power", "reservoir", "hydraulic",
        # French
        "hydraulique", "barrage", "eau", "hydroélectrique",
        # Arabic / Darija
        "المائي", "الطاقة المائية", "السد", "هيدروليكي",
    ],

    # ── Gas / Thermal ─────────────────────────────────────────────────────
    "gas": [
        # English
        "gas", "natural gas", "thermal", "fossil fuel", "ccgt", "methane",
        # French
        "gaz", "thermique", "gaz naturel", "fossile",
        # Arabic / Darija
        "الغاز", "الطاقة الحرارية", "الوقود الأحفوري", "غاز طبيعي",
    ],

    # ── CO₂ / Carbon ──────────────────────────────────────────────────────
    "co2": [
        # English
        "co2", "co₂", "carbon", "emissions", "greenhouse", "carbon intensity",
        "pollution", "environment", "climate", "decarbonize", "decarbonisation",
        # French
        "carbone", "émissions", "serre", "intensité carbone", "pollution",
        "environnement", "climat",
        # Arabic / Darija
        "ثاني أكسيد الكربون", "الكربون", "الانبعاثات", "التلوث",
        "البيئة", "المناخ", "الاحتباس الحراري", "co2",
    ],

    # ── Physical Exchanges (imports/exports) ──────────────────────────────
    "exchange": [
        # English
        "exchange", "import", "export", "cross-border", "interconnection",
        "balance", "net export", "net import",
        # French
        "échange", "échanges physiques", "importation", "exportation",
        "interconnexion", "frontière",
        # Arabic / Darija
        "التبادل", "الاستيراد", "التصدير", "الكهرباء المستوردة",
        "الميزان الكهربائي",
    ],

    # ── Consumption / Demand ──────────────────────────────────────────────
    "consumption": [
        # English
        "consumption", "demand", "load", "usage", "electricity use",
        "power demand", "how much electricity",
        # French
        "consommation", "demande", "charge", "utilisation", "puissance",
        # Arabic / Darija
        "الاستهلاك", "الطلب", "استهلاك الكهرباء", "الحمل الكهربائي",
    ],

    # ── Renewable (aggregate: wind + solar + hydro) ───────────────────────
    "renewable": [
        # English
        "renewable", "green energy", "clean energy", "sustainable energy",
        "low carbon", "zero carbon",
        # French
        "renouvelable", "énergie verte", "énergie propre", "durable",
        "bas carbone",
        # Arabic / Darija
        "الطاقة المتجددة", "الطاقة الخضراء", "الطاقة النظيفة", "المتجددة",
    ],

    # ── General Production (all sources) ──────────────────────────────────
    "production": [
        # English
        "production", "generation", "output", "electricity produced",
        "mix", "energy mix",
        # French
        "production", "production électrique", "mix énergétique",
        "production d'électricité",
        # Arabic / Darija
        "الإنتاج", "توليد الكهرباء", "المزيج الطاقوي", "الإنتاج الكهربائي",
    ],
}


# Human-readable labels — used to build the focus hint sentence
TOPIC_LABELS: Dict[str, str] = {
    "consumption": "electricity consumption/demand",
    "nuclear":     "nuclear production",
    "wind":        "wind production",
    "solar":       "solar production",
    "hydro":       "hydro/hydraulic production",
    "gas":         "gas/thermal production",
    "co2":         "CO₂ carbon intensity",
    "exchange":    "physical exchanges (imports/exports)",
    "renewable":   "renewable energy (wind + solar + hydro)",
    "production":  "overall electricity production mix",
}


# ─────────────────────────────────────────────────────────────────────────────
# TopicIntentParser
# ─────────────────────────────────────────────────────────────────────────────

class TopicIntentParser:
    """
    Instant keyword-based topic classifier.

    Detects WHAT the user is asking about (nuclear, wind, CO₂, etc.)
    and generates a natural-language FOCUS HINT to inject into the LLM prompt.

    Does NOT call the LLM — runs in microseconds.

    Example:
        parser = TopicIntentParser()

        result = parser.parse("How is nuclear doing compared to wind?")
        # → {
        #     "topics": ["nuclear", "wind"],
        #     "confidence": 0.9,
        #     "focus_hint": "FOCUS: Answer specifically about nuclear production
        #                    and wind production. Mention other data only if
        #                    directly relevant."
        #   }

        result = parser.parse("Give me an overview")
        # → {
        #     "topics": [],
        #     "confidence": 0.5,
        #     "focus_hint": ""   ← empty = no filtering, LLM sees everything
        #   }
    """

    def __init__(self) -> None:
        pass  # no LLM needed — pure keyword matching

    # ── Private helpers ─────────────────────────────────────────────────────

    @staticmethod
    def _normalize(text: str) -> str:
        """Lowercase, collapse whitespace, preserve Arabic/French characters."""
        return re.sub(r"\s+", " ", text.strip().lower())

    def _find_topics(self, text: str) -> List[str]:
        """Return all topics whose keywords appear in the normalized text."""
        found: List[str] = []
        for topic, keywords in TOPIC_KEYWORDS.items():
            for kw in keywords:
                if kw in text:
                    found.append(topic)
                    break   # one match per topic is enough
        return found

    @staticmethod
    def _build_focus_hint(topics: List[str]) -> str:
        """
        Build a natural-language focus instruction for the LLM prompt.

        If topics is empty (general query) → return empty string.
        The empty string means the prompt variable {focus_hint} is blank,
        so the LLM receives no extra filtering instruction and answers freely.
        """
        if not topics:
            return ""

        # Convert topic keys to human-readable labels
        labels = [TOPIC_LABELS.get(t, t) for t in topics]

        if len(labels) == 1:
            focus = labels[0]
        elif len(labels) == 2:
            focus = f"{labels[0]} and {labels[1]}"
        else:
            focus = ", ".join(labels[:-1]) + f", and {labels[-1]}"

        return (
            f"FOCUS: The user is specifically asking about: {focus}.\n"
            f"Prioritise these metrics in your answer. "
            f"Mention other data only if it is directly relevant to the question."
        )

    # ── Public API ──────────────────────────────────────────────────────────

    def parse(self, query: str) -> Dict[str, Any]:
        """
        Detect the topic(s) of a user query and generate a focus hint.

        Args:
            query: Raw user question (English, French, Arabic/Darija).

        Returns:
            {
                "topics":     List[str],  # detected topic keys (may be empty)
                "confidence": float,      # 0.9 if specific, 0.5 if general
                "focus_hint": str,        # prompt injection string (may be "")
            }
        """
        text = self._normalize(query)
        topics = self._find_topics(text)

        if topics:
            confidence = 0.9
        else:
            # No specific topic detected → general / overview query
            confidence = 0.5

        focus_hint = self._build_focus_hint(topics)

        result: Dict[str, Any] = {
            "topics":     topics,
            "confidence": confidence,
            "focus_hint": focus_hint,
        }

        if topics:
            print(f"🎯 [TopicIntentParser] topics={topics}  query='{query[:60]}'")
        else:
            print(f"🎯 [TopicIntentParser] general query (no specific topic detected)")

        return result
