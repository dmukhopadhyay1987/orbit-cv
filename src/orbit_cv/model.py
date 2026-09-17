from langchain_openai import ChatOpenAI
import os

model = ChatOpenAI(
    model="gpt-5-nano",
    temperature=0.2,
    api_key=os.getenv("OPENAI_API_KEY")
)