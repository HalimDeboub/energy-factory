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
        
    # def build_context(self, query: str) -> str:
        
    #     """
    #     ALWAYS retrieve all 4 layers – no intent parsing!
    #     Let the LLM decide which layers are relevant for the query.
    #     """
    #     now = self._get_current_time()  # ✅ FRESH TIMESTAMP
        
    #     layers = [
    #         self._layer_immediate(now),
    #         self._layer_today_pattern(now),
    #         self._layer_yesterday_comparison(now),
    #         self._layer_short_term_historical_baseline(now),
    #        # self._layer_long_term_historical_baseline(now),
    #     ]
    #     print(layers)

    #     # Filter out empty layers (e.g., no historical data yet)
    #     non_empty = [layer for layer in layers if layer]
    #     return "\n\n".join(non_empty) if non_empty else self._fallback_context()
    
    def build_context(self, query: str, layers: list[str]) -> str:
        now = self._get_current_time()

        layer_map = {
            "realtime": self._layer_immediate,
            "today": self._layer_today_pattern,
            "yesterday": self._layer_yesterday_comparison,
            "last_7_days": self._layer_short_term_historical_baseline,
            "last_30_days": self._layer_long_term_historical_baseline,
        }

        selected_layers = []

        for layer in layers:
            if layer in layer_map:
                result = layer_map[layer](now)
                if result:
                    selected_layers.append(result)

        return "\n\n".join(selected_layers) if selected_layers else self._fallback_context(now)
    
    def _format_number(self, value: Optional[int]) -> str:
        """ number formatting: 32450 → '32 450'"""
        if value is None or value == 0:
            return "N/A"
        return f"{value:,}".replace(",", " ")
    
    def _format_timestamp(self, ts: str) -> str:
        """Convert ISO8601 to human-readable time"""
        try:
            dt = datetime.fromisoformat(ts.replace('Z', '+00:00')).astimezone(self.tz)
            time_str = dt.strftime("%H:%M")
            date_str = "today" if dt.date() == self.now.date() else dt.strftime("%d %B")
            return f"{time_str} on {date_str}"
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
            f"🔴 CURRENT STATUS (last 3 hours):\n"
            f"• {self._format_timestamp(latest['date_heure'])} : "
            f"{self._format_number(latest.get('consommation'))} MW consommation\n"
            f"• Nucleair : {self._format_number(latest.get('nucleaire'))} MW "
            f"({latest.get('nucleaire',0)/total*100:.0f}%)\n"
            f"• renewable : {renewable_pct:.0f}% "
            f"(Eolien {self._format_number(latest.get('eolien'))} MW, "
            f"Solair {self._format_number(latest.get('solaire'))} MW)\n"
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
            f"📊 TODAY'S PROFILE:\n"
            f"• Pic de consommation : {self._format_number(peak.get('consommation'))} MW "
            f"à {self._format_timestamp(peak['date_heure'])}\n"
            f"• Morning average (6h-12h) : {self._format_number(int(morning_avg))} MW\n"
            f"• Evening average (18h-22h) : {self._format_number(int(evening_avg))} MW\n"
            f"• Stable nuclear production : "
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
            f"🔄 COMPARISON YESTERDAY (same time ±30min):\n"
            f"• NOW : {self._format_number(today_val)} MW nucléaire\n"
            f"• Yesterday at the same time : {self._format_number(yesterday_val)} MW\n"
            f"• Variation : {delta_str}"
        )
    
    def _layer_short_term_historical_baseline(self, now: datetime) -> str:
        """Layer 4: layer short term historical baseline 10-day historical baseline for 'high/low' judgments"""
        current_hour = self.now.hour
        history = self.db.get_historical_same_hour(current_hour, days_back=10)
        
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
                "very high" if percentile >= 90 else
                "high" if percentile >= 75 else
                "average" if percentile >= 25 else
                "low" if percentile >= 10 else
                "very low"
            )
        else:
            percentile_desc = "N/A"
        
        return (
            f"📈 BASELINE HISTORIQUE (10 last days, same hour):\n"
            f"• Average nuclear production : {self._format_number(int(avg))} MW\n"
            f"• Minimum : {self._format_number(min_val)} MW | Maximum : {self._format_number(max_val)} MW\n"
            f"• Current position : {percentile_desc} ({percentile}e percentile)"
        )
    
    
    def _layer_long_term_historical_baseline(self, now: datetime) -> str:
        """Layer 5: layer long term historical baseline 30-day historical baseline for 'high/low' judgments"""
        current_hour = self.now.hour
        history = self.db.get_historical_same_hour(current_hour, days_back=30)
        
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
                "very high" if percentile >= 90 else
                "high" if percentile >= 75 else
                "average" if percentile >= 25 else
                "low" if percentile >= 10 else
                "very low"
            )
        else:
            percentile_desc = "N/A"
        
        return (
            f"📈 BASELINE HISTORIQUE (10 last days, same hour):\n"
            f"• Average nuclear production : {self._format_number(int(avg))} MW\n"
            f"• Minimum : {self._format_number(min_val)} MW | Maximum : {self._format_number(max_val)} MW\n"
            f"• Current position : {percentile_desc} ({percentile}e percentile)"
        )
    
    # app/tools/context_summarizer.py → _fallback_context()
    def _fallback_context(self, now: datetime) -> str:
        count = self.db.get_record_count()
        latest = self.db.get_latest_record()
        if latest and latest.get("consommation") is not None:
            ts = self._format_timestamp(latest["date_heure"])
            age_min = (now - datetime.fromisoformat(latest["date_heure"].replace('Z','+00:00')).astimezone(self.tz)).total_seconds() / 60
            return (
                f"⚠️ PARTIAL DATA ({count} records)\n"
                f"• Last real data : {ts} ( {age_min:.0f} min ago)\n"
                f"• Status : Real measurements available but data is sparse. Context may be incomplete."
            )
        return (
            f"⚠️ db is empty ({count} records)\n"
            f"→ Start the scheduler : python scheduler.py"
        )