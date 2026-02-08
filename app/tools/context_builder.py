# app/tools/context_builder.py
from datetime import datetime, timedelta
import pytz
from app.config.config import TIMEZONE
from app.tools.data_fetcher import EnergyDatabase

class ContextBuilder:
    def __init__(self):
        self.db = EnergyDatabase()
        self.tz = pytz.timezone(TIMEZONE)
    
    def _format_record(self, record):
        """Convert raw numbers to natural language snippet"""
        try:
            dt = datetime.fromisoformat(record["date_heure"].replace('Z', '+00:00')).astimezone(self.tz)
        except ValueError:
            # Fallback for malformed timestamps
            dt_str = record["date_heure"][:19]
            dt = self.tz.localize(datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S"))
        
        time_str = dt.strftime("%H:%M")
        date_str = "aujourd'hui" if dt.date() == datetime.now(self.tz).date() else dt.strftime("%d %B")
        
        nuclear_pct = (record["nucleaire"] / record["consommation"] * 100) if record["consommation"] else 0
        renewable_pct = (
            (record["eolien"] + record["solaire"] + record["hydraulique"] + record.get("bioenergies", 0)) 
            / record["consommation"] * 100
        ) if record["consommation"] else 0
        
        return (
            f"À {time_str} le {date_str} :\n"
            f"• Consommation : {record['consommation']:,} MW\n"
            f"• Nucléaire : {nuclear_pct:.0f}% ({record['nucleaire']:,} MW)\n"
            f"• Renouvelables : {renewable_pct:.0f}%\n"
            f"• CO₂ : {record['taux_co2']} g/kWh"
        )
    
    def build_for_query(self, inputs: str | dict, time_intent: str | None = None) -> str:
        """
        Handle BOTH direct string calls AND chain dict inputs.
        Chain inputs now use {"input": "..."} (not "query") due to RunnableWithMessageHistory requirements.
        """
        # 🔑 CRITICAL FIX: Handle both input formats
        if isinstance(inputs, dict):
            # Chain input format: {"input": "query text", "time_intent": "..."}
            query = inputs.get("input", "")  # ← MUST use "input" (not "query")
            time_intent = inputs.get("time_intent", time_intent)
        else:
            # Direct string call (for testing)
            query = str(inputs)
        
        if not query.strip():
            return "⚠️ Question vide"
        
        now = datetime.now(self.tz)
        
        # Time intent detection (French + English keywords)
        query_lower = query.lower()
        if any(kw in query_lower for kw in ["maintenant", "actuel", "live", "actuelle", "courant", "présent", "current", "now", "real-time"]):
            start = now - timedelta(hours=3)
        elif "aujourd'hui" in query_lower or "today" in query_lower:
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif "hier" in query_lower or "yesterday" in query_lower:
            yesterday = now - timedelta(days=15)
            start = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
            end = yesterday.replace(hour=23, minute=59, second=59)
            records = self.db.get_time_range(start, end)
            if not records:
                return "⚠️ Données indisponibles pour hier"
            # Return summary of yesterday's peak hour
            peak = max(records, key=lambda r: r["consommation"])
            return f"Synthèse hier ({peak['date_heure'][:10]}) :\n{self._format_record(peak)}"
        else:
            # Default: last 3 hours (safe for ambiguous queries)
            start = now - timedelta(hours=3)
        
        records = self.db.get_time_range(start, now)
        if not records:
            return "⚠️ Données énergétiques RTE indisponibles pour la période demandée. Dernière mise à jour il y a plus de 3h."
        
        # Return most recent record
        latest = records[-1]
        return f"Données RTE éCO2mix (H-2)\n{self._format_record(latest)}"