from app.tools.rag_pipeline import EnergyRAG

rag = EnergyRAG()

# Turn 1
print(rag.query("Production nucléaire actuelle ?", session_id="user_123"))
# → "32 450 MW à 14:30"

# Turn 2 (system remembers previous answer!)
print(rag.query("C'est élevé ?", session_id="user_123"))
# → "Oui, 32 450 MW représente 52% du mix – légèrement au-dessus de la moyenne de 30 000 MW..."