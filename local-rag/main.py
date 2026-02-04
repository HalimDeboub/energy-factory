from langchain_ollama.llms import OllamaLLM
from langchain_ollama.embeddings import OllamaEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from fastapi import FastAPI, HTTPException
from vector import retriever
model = OllamaLLM(model="llama3.1:8b", temperature=0.1 , base_url="http://localhost:11434")
template = """
You are a minimal energy data analyst
Here are some given data on France's energy: {data}
here is the question to ask :{question} 

"""
prompt = ChatPromptTemplate.from_template(template)

chain = prompt| model



while True:
    user_data = input("Enter energy data (or 'q' to quit): ")
    if user_data.lower() == 'q':
        break
    user_question = input("Enter your question: ")
    query = {
        "data": retriever.invoke(user_question),
        "question": user_question
    }
    result = chain.invoke(query)
    print(result)
