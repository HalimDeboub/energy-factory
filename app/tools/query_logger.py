# app/tools/query_logger.py
#
# ═══════════════════════════════════════════════════════════════════════════
# WHY QUERY LOGGING MATTERS IN A RAG SYSTEM
# ═══════════════════════════════════════════════════════════════════════════
#
# When you run an AI pipeline in production you need observability —
# the ability to see what actually happened at runtime without reading
# source code.  Query logs answer questions like:
#
#   • Which queries are slowest?           → optimize those layers
#   • Which time layers are used most?     → tells you what users care about
#   • How often does the cache save time?  → measures caching effectiveness
#   • Which languages do users write in?   → guides multilingual improvements
#   • Where do errors occur?               → guides debugging
#
# ═══════════════════════════════════════════════════════════════════════════
# LOG FORMAT — newline-delimited JSON (NDJSON)
# ═══════════════════════════════════════════════════════════════════════════
#
# Each query is written as a single JSON object on one line.
# This format (called NDJSON or JSONL) is the industry standard for logs
# because:
#   • Every line is a complete, self-contained record
#   • Files can be streamed line-by-line without loading the whole file
#   • Tools like pandas, jq, Splunk, and Grafana all support it natively
#   • Appending is atomic — no risk of corrupting previous entries
#
# Example log line:
# {
#   "timestamp": "2026-05-12T18:14:03",
#   "session_id": "user-1",
#   "query": "What is consumption now?",
#   "layers": ["realtime"],
#   "intent_confidence": 0.9,
#   "cache_hit": false,
#   "latency_ms": 18432,
#   "status": "ok",
#   "error": null,
#   "answer_preview": "At 18:10 on 12 May 2026, consumption was 52,300 MW..."
# }
#
# ═══════════════════════════════════════════════════════════════════════════

import json
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.config.config import BASE_DIR


# Default log file path — stored in the project root under /logs/
LOG_DIR  = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "query_log.jsonl"


# ─────────────────────────────────────────────────────────────────────────────
# QueryTimer — a context manager for measuring latency
# ─────────────────────────────────────────────────────────────────────────────
#
# CONCEPT — context managers (the `with` statement)
# A context manager lets you wrap a block of code with setup/teardown logic.
# `__enter__` runs at the start of the `with` block.
# `__exit__`  runs when the block ends (even on exceptions).
#
# Usage:
#   timer = QueryTimer()
#   with timer:
#       result = expensive_llm_call()
#   print(timer.elapsed_ms)   # total milliseconds
#

class QueryTimer:
    """Measures wall-clock elapsed time in milliseconds."""

    def __enter__(self) -> "QueryTimer":
        self._start = time.perf_counter()   # high-resolution timer
        return self

    def __exit__(self, *args: Any) -> None:
        self._end = time.perf_counter()

    @property
    def elapsed_ms(self) -> int:
        """Elapsed time in milliseconds (rounded to nearest ms)."""
        return int((self._end - self._start) * 1000)


# ─────────────────────────────────────────────────────────────────────────────
# QueryLogger — writes structured logs to disk
# ─────────────────────────────────────────────────────────────────────────────

class QueryLogger:
    """
    Appends one JSON log record per query to a NDJSON file.

    Thread-safety note:
        Append-mode file writes are atomic on most filesystems for records
        smaller than the OS page size (~4 KB).  Since our log lines are well
        under that limit this is safe for a single-process FastAPI server
        without explicit locking.

    Args:
        log_file: Path to the .jsonl log file.
                  Defaults to <project_root>/logs/query_log.jsonl.
    """

    def __init__(self, log_file: Path = LOG_FILE) -> None:
        self.log_file = log_file
        # Ensure the logs/ directory exists.
        # parents=True → create intermediate dirs if missing.
        # exist_ok=True → no error if dir already exists.
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        print(f"📝 [QueryLogger] Logging to: {self.log_file}")

    # ── Core write method ───────────────────────────────────────────────────

    def log(
        self,
        *,
        session_id:         str,
        query:              str,
        layers:             List[str],
        intent_confidence:  float,
        cache_hit:          bool,
        latency_ms:         int,
        status:             str,                  # "ok" | "error"
        answer:             Optional[str] = None,
        error:              Optional[str] = None,
    ) -> None:
        """
        Write one structured log entry.

        All arguments are keyword-only (the `*` forces this).
        This prevents accidental positional argument mistakes when the
        function signature grows over time.

        Args:
            session_id:        Conversation session identifier.
            query:             Raw user query string.
            layers:            Time layers selected by the intent parser.
            intent_confidence: Confidence score from the intent parser (0–1).
            cache_hit:         True if the answer was served from cache.
            latency_ms:        Total wall-clock time in milliseconds.
            status:            "ok" or "error".
            answer:            First 200 chars of the LLM answer (for inspection).
            error:             Error message if status == "error".
        """
        record: Dict[str, Any] = {
            "timestamp":         datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "session_id":        session_id,
            "query":             query,
            "layers":            layers,
            "intent_confidence": round(intent_confidence, 3),
            "cache_hit":         cache_hit,
            "latency_ms":        latency_ms,
            "status":            status,
            "answer_preview":    (answer[:200] if answer else None),
            "error":             error,
        }

        # json.dumps converts the dict to a JSON string.
        # ensure_ascii=False keeps Arabic / French characters readable.
        line = json.dumps(record, ensure_ascii=False)

        # Open in append mode ("a") so we never overwrite old records.
        # encoding="utf-8" is required for Arabic characters.
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    # ── Convenience: read all logs back as a list of dicts ──────────────────

    def read_all(self) -> List[Dict[str, Any]]:
        """
        Load the entire log file into memory as a list of dicts.

        Useful for a /logs FastAPI endpoint or offline analysis in a notebook.
        Each line in the file is parsed as one JSON object.
        """
        if not self.log_file.exists():
            return []

        records = []
        with open(self.log_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:                          # skip blank lines
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass                      # skip corrupted lines

        return records

    # ── Convenience: compute aggregate statistics ────────────────────────────

    def stats(self) -> Dict[str, Any]:
        """
        Compute summary statistics from the log file.

        Returns a dict that can be served directly from a FastAPI endpoint.

        Metrics explained:
            total_queries    → total number of requests logged
            cache_hit_rate   → % of requests served from cache (no LLM call)
            avg_latency_ms   → average response time across all requests
            p95_latency_ms   → 95th-percentile latency ("worst typical" query)
            error_rate       → % of requests that ended in an error
            top_layers       → which time layers are requested most often
        """
        records = self.read_all()

        if not records:
            return {"total_queries": 0, "message": "No queries logged yet."}

        total         = len(records)
        hits          = sum(1 for r in records if r.get("cache_hit"))
        errors        = sum(1 for r in records if r.get("status") == "error")
        latencies     = [r["latency_ms"] for r in records if "latency_ms" in r]

        # Count layer occurrences
        layer_counts: Dict[str, int] = {}
        for r in records:
            for layer in r.get("layers", []):
                layer_counts[layer] = layer_counts.get(layer, 0) + 1

        # P95 latency: sort latencies, take the value at the 95th percentile.
        # This is more meaningful than the average because it shows what the
        # SLOWEST 5% of users experience.
        sorted_lat   = sorted(latencies)
        p95_index    = int(len(sorted_lat) * 0.95)
        p95_latency  = sorted_lat[p95_index] if sorted_lat else 0
        avg_latency  = int(sum(latencies) / len(latencies)) if latencies else 0

        # Sort layers by usage count, descending
        top_layers = dict(
            sorted(layer_counts.items(), key=lambda x: x[1], reverse=True)
        )

        return {
            "total_queries":   total,
            "cache_hit_rate":  f"{hits / total * 100:.1f}%",
            "avg_latency_ms":  avg_latency,
            "p95_latency_ms":  p95_latency,
            "error_rate":      f"{errors / total * 100:.1f}%",
            "top_layers":      top_layers,
        }
