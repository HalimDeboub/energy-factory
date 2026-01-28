📌 Project Overview

Energy AI Analyst is an open-source, multi-agent AI system that analyzes real-time electricity grid data using the official eco2mix API.

The system uses:

AI agents that collaborate (like a small expert team)

RAG (Retrieval-Augmented Generation) to ground answers in real documents

LangChain + LangGraph to orchestrate agent workflows

Ollama (local LLMs) for privacy & cost control

FastAPI + Streamlit for APIs and dashboards

🎯 Goal: Turn raw energy data into clear insights, forecasts, and policy-aware explanations — automatically.

🧠 What This Project Does (In Simple Terms)

Pulls real-time electricity data every 15 minutes

Stores energy & policy documents in a vector database

Uses multiple AI agents, each with a role:

Data Analyst

Renewable Expert

Forecaster

Policy Analyst

A Supervisor Agent decides:

“Which agent should answer this question?”

Answers questions like:

Why did nuclear production drop today?

Is wind compensating for low hydro?

What is the carbon impact right now?

Displays results via API + dashboard

📊 Data Source: eco2mix (Official Grid Data)

API:
https://odre.opendatasoft.com/api/explore/v2.1/catalog/datasets/eco2mix-national-tr/records

What it provides:

Electricity production by source (nuclear, wind, solar, hydro, gas…)

Consumption (MW)

CO₂ emissions

Imports / exports

Updated every 15 minutes
