import os
import json
from typing import List, Dict, Any
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool

import requests

# ==================== API Keys and Configuration ====================
load_dotenv()
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
TAVILY_API_URL = "https://api.tavily.com/search"

# ==================== Tools ====================

@tool
def get_weather(city: str, days: int = 5) -> List[Dict]:
    """Get weather forecast for a city for the next N days."""
    try:
        # Here you should call your real weather API, this is a placeholder
        # For demonstration, we return a dummy response
        return [
            {
                "date": "2024-07-01",
                "summary": "Sunny",
                "temp_max": 32.1,
                "temp_min": 25.3,
                "pop_max": 0.05
            }
            for _ in range(days)
        ]
    except Exception as e:
        return [{"error": f"Failed to get weather information: {str(e)}"}]

@tool
def search_web(query: str) -> str:
    """Search web information using Tavily"""
    if not TAVILY_API_KEY:
        return "Tavily API key not set, cannot perform web search"
    try:
        resp = requests.get(
            TAVILY_API_URL,
            params={
                "api_key": TAVILY_API_KEY,
                "query": query,
                "search_depth": "basic",
                "max_results": 5
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        results = []
        for result in data.get("results", []):
            results.append({
                "title": result.get("title", ""),
                "content": result.get("content", ""),
                "url": result.get("url", "")
            })
        return json.dumps(results, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"Failed to search web: {str(e)}"

# ==================== Agent Setup ====================

llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.2)

tools = [get_weather, search_web]

system_prompt = (
    "You are a helpful travel assistant. "
    "You can answer questions, provide weather forecasts, and search the web for information."
)

def agent_executor(messages: List[Dict[str, str]]) -> str:
    # Compose the conversation
    chat_history = []
    for msg in messages:
        if msg["role"] == "user":
            chat_history.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            chat_history.append(AIMessage(content=msg["content"]))
        elif msg["role"] == "system":
            chat_history.append(SystemMessage(content=msg["content"]))
    # Add system prompt at the start
    chat_history = [SystemMessage(content=system_prompt)] + chat_history

    # Run the LLM with tools
    response = llm.invoke(chat_history, tools=tools)
    return response.content

# ==================== Example Usage ====================

if __name__ == "__main__":
    # Example conversation
    messages = [
        {"role": "user", "content": "What's the weather in Singapore for the next 3 days?"},
        {"role": "user", "content": "Find me top attractions in Singapore."}
    ]
    reply = agent_executor(messages)
    print(reply)