# app/agents/forecaster.py
from langchain.agents import create_react_agent, Tool
import pandas as pd
from prophet import Prophet

class ForecasterAgent:
    def __init__(self):
        # Add forecasting tools
        self.tools = [
            Tool(
                name="forecast_energy_demand",
                func=self.forecast_demand,
                description="Forecast energy demand for next 24 hours"
            ),
            Tool(
                name="predict_renewable_output",
                func=self.predict_renewables,
                description="Predict renewable energy output based on weather"
            )
        ]
        # Create agent (optional LLM)
        # If needed, you can pass a small LLM here for reasoning

    def forecast_demand(self, historical_data: pd.DataFrame):
        """Use Prophet for time series forecasting"""
        model = Prophet()
        model.fit(historical_data)
        future = model.make_future_dataframe(periods=24, freq='H')
        forecast = model.predict(future)
        return forecast[['ds', 'yhat']]

    def predict_renewables(self, weather_data: pd.DataFrame):
        """Predict renewable output based on weather"""
        # Placeholder: simple linear model
        return weather_data['solar_radiation'] * 0.8  # example
