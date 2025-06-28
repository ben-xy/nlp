[English](README.md) | [中文版](README_CN.md)

# Travel Assistant

This project is a travel assistant that helps users plan their trips by providing information about destinations, activities, and travel tips. It implements a multimodal, feedback-driven, automated intelligent travel planning assistant, leveraging modern AI technologies such as large language models, workflow orchestration, external API integration, and multi-turn human-AI interaction.

## Environment Setup

- Create a `.env` file in the root directory of the project.
- Add the following environment variables to the `.env` file:
  - `OPENAI_API_KEY`
  - `OPENWEATHER_KEY`
  - `TAVILY_API_KEY`
  - `LANGCHAIN_API_KEY`
  - `LANGCHAIN_TRACING_V2`

## Tech Stack
- **LangGraph**: Used to build and manage multi-node, multi-state state graphs, enabling multi-step reasoning and feedback loops for travel planning.
- **LangChain**: Integrates large language models (such as OpenAI GPT-4o) for natural language understanding, information extraction, and generation.
- **OpenAI GPT-4o**: The core LLM, responsible for understanding user input, extracting locations, generating subtopics, summarizing search results, and creating travel plans.
- **Requests**: For accessing external APIs (weather, geolocation, web search).
- **python-dotenv**: Loads and manages environment variables (API keys, etc.).
- **FFmpeg + Whisper**: Used to extract audio from video and transcribe it to text, enabling multimodal input.
- **Caching and State Management**: Uses lru_cache and in-memory checkpointers to ensure the workflow can be interrupted and resumed.

## Workflow Overview

### Environment Setup
- Loads API keys and initializes the LLM and state graph.

### User Input Handling
- Supports both text and video input.
- For video, extracts audio with FFmpeg and transcribes it using Whisper.

### Location and Subtopic Extraction
- Uses the LLM to extract destination cities/locations.
- Generates travel-related subtopics (e.g., food, history, shopping) based on the locations.

### Weather Information Retrieval
- Calls the OpenWeather API to get weather forecasts for destinations.

### Subtopic Research and Summarization
- For each subtopic and location, uses the Tavily search API to retrieve web information.
- Summarizes search results into structured summaries using the LLM.

### Travel Plan Generation
- Combines weather, subtopic summaries, and other info to generate a detailed travel plan with daily itineraries, budgets, and tips.

### Human Feedback Loop
- Users can provide feedback on subtopics or the travel plan; the system automatically adjusts and improves based on feedback.

### State Management
- Uses in-memory checkpointers and thread IDs to support multi-turn conversations and workflow interruption/resumption.