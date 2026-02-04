from langchain_ollama.embeddings import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStore
import os 
import pandas as pd


df=pd.read_json('france_data.json')
embeddings= OllamaEmbeddings(model="nomic-embed-text:latest", base_url="http://localhost:11434")
db_location = "./chroma_db_energy.db"
add_documents  = not os.path.exists(db_location)

if add_documents:
    documents=[]
    ids=[]
    for i, row in df.iterrows():
        document = Document(
            page_content=str(row['consommation']) + " " + str(row['nucleaire']) + " " + str(row['eolien']) + " " + str(row['solaire']) + " " + str(row['hydraulique']) + " " + str(row['gaz']) + " " + str(row['taux_co2']),
            metadata={"perimetre": row['perimetre'],"nature": row['nature']}
        )
       
        documents.append(document)
        ids.append(str(i))
vector_store = Chroma(
    collection_name="energy_data",
    embedding_function=embeddings,
    persist_directory=db_location
)

if add_documents:
    vector_store.add_documents(documents, ids=ids)
   # vector_store.persist()
retriever=vector_store.as_retriever(search_type="similarity", search_kwargs={"k":3})