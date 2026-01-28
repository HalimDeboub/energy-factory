# app/tools/data_tools.py
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from langchain_core.tools import tool

class Eco2mixDataTools:
    def __init__(self):
        self.base_url = "https://odre.opendatasoft.com/api/explore/v2.1/catalog/datasets/eco2mix-national-tr/records"
        
    @tool
    def get_real_time_data(self, limit: int = 10) -> str:
        """Fetch real-time energy data from France's grid"""
        params = {
            "limit": limit,
            "order_by": "date desc",
            "timezone": "UTC"
        }
        
        try:
            response = requests.get(self.base_url, params=params)
            data = response.json()
            
            if 'results' in data and data['results']:
                formatted = []
                for i, record in enumerate(data['results'][:3]):  # Show first 3 records
                    formatted.append(f"""
Record {i+1}:
Timestamp: {record.get('date', 'N/A')}
Consumption: {record.get('consommation', 0)} MW
Production: {record.get('production', 0)} MW
Nuclear: {record.get('nucleaire', 0)} MW
Wind: {record.get('eolien', 0)} MW
Solar: {record.get('solaire', 0)} MW
Hydro: {record.get('hydraulique', 0)} MW
Gas: {record.get('gaz', 0)} MW
CO2 Intensity: {record.get('taux_co2', 0)} g/kWh
""")
                return "\n".join(formatted)
            return "No data available"
        except Exception as e:
            return f"Error fetching data: {str(e)}"
    
    @tool
    def get_energy_mix(self, date: Optional[str] = None) -> str:
        """Get energy mix percentages for a specific date"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
            
        params = {
            "where": f"date >= '{date}T00:00:00' and date <= '{date}T23:59:59'",
            "limit": 96  # 15-min intervals for 24h
        }
        
        try:
            response = requests.get(self.base_url, params=params)
            data = response.json()
            
            if 'results' in data and data['results']:
                df = pd.DataFrame(data['results'])
                mix_columns = ['nucleaire', 'eolien', 'solaire', 'hydraulique', 'gaz']
                
                # Calculate averages
                mix = {}
                for col in mix_columns:
                    if col in df.columns:
                        mix[col] = df[col].mean()
                
                if mix:
                    total = sum(mix.values())
                    percentages = {k: (v/total)*100 for k, v in mix.items()}
                    
                    result = f"Energy Mix for {date}:\n"
                    for source, percent in percentages.items():
                        result += f"- {source.title()}: {percent:.1f}%\n"
                    return result
            return "No data available for the specified date"
        except Exception as e:
            return f"Error: {str(e)}"