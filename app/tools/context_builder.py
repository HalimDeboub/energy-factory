from datetime import datetime, timedelta
import pytz
from app.config.config import TIMEZONE
from app.database.database import EnergyDatabase

class ContextBuilder:
    def __init__(self):
        self.db = EnergyDatabase()
        self.tz = pytz.timezone(TIMEZONE)
    
    def _format_record(self, record):
        """Convert raw numbers to natural language snippet"""
        dt = datetime.fromisoformat(record["date_heure"]).astimezone(self.tz)
        time_str = dt.strftime("%H:%M")
        date_str = "aujourd'hui" if dt.date() == datetime.now(self.tz).date() else dt.strftime("%d %B")
        
        # Focus on human-interpretable context (not raw numbers)
        nuclear_pct = (record["nucleaire"] / record["consommation"] * 100) if record["consommation"] else 0
        renewable_pct = (
            (record["eolien"] + record["solaire"] + record["hydraulique"] ) 
            / record["consommation"] * 100
        ) if record["consommation"] else 0
        
        return (
            f"À {time_str} le {date_str} : "
            f"consommation = {record['consommation']:,} MW, "
            f"nucléaire = {nuclear_pct:.0f}%, "
            f"renouvelables = {renewable_pct:.0f}%, "
            f"CO₂ = {record['taux_co2']} g/kWh"
        )
    
    def build_for_query(self, query, time_intent=None):
        """Build time-aware context WITHOUT vector search"""
        now = datetime.now(self.tz)
        
        # Rule-based time intent detection (no LLM needed for this)
        if time_intent == "current" or any(kw in query.lower() for kw in ["maintenant", "actuel", "live", "en temps réel"]):
            record = self.db.get_latest_record()
            if not record:
                return "Aucune donnée récente disponible (dernière mise à jour il y a plus de 15 min)"
            return f"[Données RTE éCO2mix - mises à jour il y a moins de 15 min]\n{self._format_record(record)}"
        
        elif time_intent == "last_hour" or any(kw in query.lower() for kw in ["dernière heure", "ces 60 minutes"]):
            start = now - timedelta(hours=1)
            records = self.db.get_time_range(start, now)
            if not records:
                return "Données indisponibles pour la dernière heure"
            snippets = [self._format_record(r) for r in records[-4:]]  # Last 4 quarters
            return f"[Données RTE éCO2mix - dernière heure]\n" + "\n".join(snippets)
        
        elif time_intent == "today" or "aujourd'hui" in query.lower():
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            records = self.db.get_time_range(start, now)
            if not records:
                return "Données indisponibles pour aujourd'hui"
            # Summarize key moments (morning peak, solar max, evening peak)
            key_times = [6, 12, 19]  # 6am, noon, 7pm
            snippets = []
            for hour in key_times:
                closest = min(records, key=lambda r: abs(datetime.fromisoformat(r["date_heure"]).hour - hour))
                snippets.append(self._format_record(closest))
            return f"[Données RTE éCO2mix - synthèse aujourd'hui]\n" + "\n".join(snippets)
        
        else:
            # Default: last 3 hours for general queries
            start = now - timedelta(hours=3)
            records = self.db.get_all()
            if not records:
                return "Données historiques non disponibles"
            return f"[Données RTE éCO2mix - dernières 3 heures]\n" + "\n".join(
                [self._format_record(r) for r in records[-12:]]  # Last 12 quarters
            )