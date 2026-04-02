# app/tools/context_summarizer.py
from datetime import datetime, timedelta
import pytz
from typing import List, Dict, Optional
from app.config.config import TIMEZONE
from app.database.database import EnergyDatabase

class ContextSummarizer:
    """Generates 4-layer context WITHOUT parsing user intent"""
    
    def __init__(self):
        self.db = EnergyDatabase()
        self.tz = pytz.timezone(TIMEZONE)
        self.now = datetime.now(self.tz)
       
    def _get_current_time(self):
        """ALWAYS get fresh timestamp per query"""
        return datetime.now(self.tz)
        
    def build_context(self, query: str) -> str:
        
        """
        ALWAYS retrieve all 4 layers – no intent parsing!
        Let the LLM decide which layers are relevant for the query.
        """
        now = self._get_current_time()  # ✅ FRESH TIMESTAMP
        
        layers = [
            self._layer_immediate(now),
            self._layer_today_pattern(now),
            self._layer_yesterday_comparison(now),
            self._layer_historical_baseline(now),
        ]
        print(layers)

        # Filter out empty layers (e.g., no historical data yet)
        non_empty = [layer for layer in layers if layer]
        return "\n\n".join(non_empty) if non_empty else self._fallback_context()
    
    def _format_number(self, value: Optional[int]) -> str:
        """French number formatting: 32450 → '32 450'"""
        if value is None or value == 0:
            return "N/A"
        return f"{value:,}".replace(",", " ")
    
    def _format_timestamp(self, ts: str) -> str:
        """Convert ISO8601 to human-readable French time"""
        try:
            dt = datetime.fromisoformat(ts.replace('Z', '+00:00')).astimezone(self.tz)
            time_str = dt.strftime("%H:%M")
            date_str = "aujourd'hui" if dt.date() == self.now.date() else dt.strftime("%d %B")
            return f"{time_str} le {date_str}"
        except:
            return ts[:16]
    
    def _compute_trend(self, records: List[Dict]) -> str:
        """Compute short-term trend from last N records"""
        if len(records) < 2:
            return "données insuffisantes"
        
        first = records[0].get("consommation", 0)
        last = records[-1].get("consommation", 0)
        if first == 0:
            return "stable"
        
        change_pct = ((last - first) / first) * 100
        if abs(change_pct) < 2:
            return "stable"
        elif change_pct > 0:
            return f"↑ {change_pct:.0f}%"
        else:
            return f"↓ {abs(change_pct):.0f}%"
    
    def _layer_immediate(self, now: datetime) -> str:  # ✅ PASS FRESH TIMESTAMP
        start = now - timedelta(hours=7)
        print(start)
        records = self.db.get_time_range(start, now)
        if not records:
            return ""
        
        latest = records[-1]
        # 🔑 CRITICAL: ONLY use REAL consumption (skip forecast-only records)
        if latest.get("consommation") is None:
            
            # Find most recent record WITH real consumption
            real_records = [r for r in records if r.get("consommation") is not None]
            if not real_records:
                return "⚠️ DONNÉES RÉELLES TEMPORAIREMENT INDISPONIBLES (dernière mesure: il y a >2h)"
            latest = real_records[-1]
        
        trend = self._compute_trend(records[-4:]) if len(records) >= 4 else "insuffisant"
        renewables = sum([
            latest.get("eolien", 0),
            latest.get("solaire", 0),
            latest.get("hydraulique", 0),
            latest.get("bioenergies", 0)
        ])
        total = latest.get("consommation", 1)
        renewable_pct = (renewables / total * 100) if total else 0
        
        return (
            f"🔴 ÉTAT ACTUEL (dernières 3h):\n"
            f"• {self._format_timestamp(latest['date_heure'])} : "
            f"{self._format_number(latest.get('consommation'))} MW consommation\n"
            f"• Nucléaire : {self._format_number(latest.get('nucleaire'))} MW "
            f"({latest.get('nucleaire',0)/total*100:.0f}%)\n"
            f"• Renouvelables : {renewable_pct:.0f}% "
            f"(Éolien {self._format_number(latest.get('eolien'))} MW, "
            f"Solaire {self._format_number(latest.get('solaire'))} MW)\n"
            f"• CO₂ : {latest.get('taux_co2', 'N/A')} g/kWh\n"
            f"• Tendance (1h) : {trend}"
        )
        
    def _layer_today_pattern(self, now: datetime) -> str:
        """Layer 2: Today's energy patterns (min/max/peak + periods)"""
        records = self.db.get_today_records()
        if len(records) < 10:  # Need at least 2.5h of data
            return ""
        
        # Find daily peak
        peak = max(records, key=lambda r: r.get("consommation", 0))
        
        # Morning period (6h-12h)
        morning = [r for r in records if 6 <= datetime.fromisoformat(r["date_heure"].replace('Z','+00:00')).astimezone(self.tz).hour < 12]
        morning_avg = sum(r.get("consommation",0) for r in morning) / len(morning) if morning else 0
        
        # Evening peak period (18h-22h)
        evening = [r for r in records if 18 <= datetime.fromisoformat(r["date_heure"].replace('Z','+00:00')).astimezone(self.tz).hour < 22]
        evening_avg = sum(r.get("consommation",0) for r in evening) / len(evening) if evening else 0
        
        return (
            f"📊 PROFIL D'AUJOURD'HUI:\n"
            f"• Pic de consommation : {self._format_number(peak.get('consommation'))} MW "
            f"à {self._format_timestamp(peak['date_heure'])}\n"
            f"• Moyenne matinale (6h-12h) : {self._format_number(int(morning_avg))} MW\n"
            f"• Moyenne soirée (18h-22h) : {self._format_number(int(evening_avg))} MW\n"
            f"• Production nucléaire stable : "
            f"{min(r.get('nucleaire',0) for r in records):,} → "
            f"{max(r.get('nucleaire',0) for r in records):,} MW"
        )
    
    def _layer_yesterday_comparison(self, now: datetime) -> str:
        """Layer 3: Yesterday same hour comparison"""
        current_hour = self.now.hour
        yesterday_records = self.db.get_yesterday_same_hour(current_hour, window_minutes=30)
        today_records = self.db.get_time_range(
            self.now - timedelta(hours=7),
            self.now
        )
        

        if not yesterday_records or not today_records:
            
            return ""
        
        # Get representative values (closest to exact hour)
        yesterday_val = yesterday_records[len(yesterday_records)//2].get("nucleaire", 0)
        today_val = today_records[len(today_records)//2].get("nucleaire", 0)
        
        if yesterday_val == 0:
            return ""
        
        delta_pct = ((today_val - yesterday_val) / yesterday_val) * 100
        delta_str = f"+{delta_pct:.0f}%" if delta_pct > 0 else f"{delta_pct:.0f}%"
        
        return (
            f"🔄 COMPARAISON HIER (même heure ±30min):\n"
            f"• Maintenant : {self._format_number(today_val)} MW nucléaire\n"
            f"• Hier à la même heure : {self._format_number(yesterday_val)} MW\n"
            f"• Variation : {delta_str}"
        )
    
    def _layer_historical_baseline(self, now: datetime) -> str:
        """Layer 4: 7-day historical baseline for 'high/low' judgments"""
        current_hour = self.now.hour
        history = self.db.get_historical_same_hour(current_hour, days_back=7)
        
        if len(history) < 3:  # Need at least 3 days for meaningful baseline
            return ""
        
        nuclear_vals = [r.get("nucleaire", 0) for r in history if r.get("nucleaire")]
        if not nuclear_vals:
            return ""
        
        avg = sum(nuclear_vals) / len(nuclear_vals)
        min_val = min(nuclear_vals)
        max_val = max(nuclear_vals)
        
        # Get current value for percentile calculation
        latest = self.db.get_latest_record()
        current_val = latest.get("nucleaire", 0) if latest else 0
        
        if current_val:
            # Simple percentile approximation
            below = sum(1 for v in nuclear_vals if v < current_val)
            percentile = int((below / len(nuclear_vals)) * 100)
            percentile_desc = (
                "très élevé" if percentile >= 90 else
                "élevé" if percentile >= 75 else
                "moyen" if percentile >= 25 else
                "bas" if percentile >= 10 else
                "très bas"
            )
        else:
            percentile_desc = "N/A"
        
        return (
            f"📈 BASELINE HISTORIQUE (7 derniers jours, même heure):\n"
            f"• Moyenne nucléaire : {self._format_number(int(avg))} MW\n"
            f"• Minimum : {self._format_number(min_val)} MW | Maximum : {self._format_number(max_val)} MW\n"
            f"• Position actuelle : {percentile_desc} ({percentile}e percentile)"
        )
    
    # app/tools/context_summarizer.py → _fallback_context()
    def _fallback_context(self, now: datetime) -> str:
        count = self.db.get_record_count()
        latest = self.db.get_latest_record()
        if latest and latest.get("consommation") is not None:
            ts = self._format_timestamp(latest["date_heure"])
            age_min = (now - datetime.fromisoformat(latest["date_heure"].replace('Z','+00:00')).astimezone(self.tz)).total_seconds() / 60
            return (
                f"⚠️ DONNÉES PARTIELLES ({count} enregistrements)\n"
                f"• Dernière donnée réelle : {ts} (il y a {age_min:.0f} min)\n"
                f"• Statut : Mesures réelles disponibles"
            )
        return (
            f"⚠️ BASE DE DONNÉES VIDE ({count} enregistrements)\n"
            f"→ Démarrez le scheduler : python scheduler.py"
    )