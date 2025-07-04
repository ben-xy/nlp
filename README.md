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

## Technology Stack & Workflow

### Technology Stack
- **LangChain & LangGraph**: Used for building multi-node, multi-stage conversational workflows, supporting LLM calls, tool integration, state management, and orchestration.
- **OpenAI GPT-4o**: The main LLM for generating traveler personas, dialogues, summaries, and final travel plans.
- **Pydantic**: For defining and validating data structures (e.g., Traveler, Perspectives).
- **Requests**: For calling external APIs (such as OpenWeather, OpenStreetMap).
- **dotenv**: For managing API keys and environment variables.
- **Tavily Search API & WikipediaLoader**: For web and knowledge retrieval to support local answers.
- **Command-line Interaction**: Uses Python standard input/output for user interaction, feedback collection, and result display.

### Workflow
1. **Environment Variable & API Key Loading**: Loads API keys from `.env` file, prompts interactively for missing keys.
2. **User Input**: Collects destination city, number of days, and number of traveler agents via command line.
3. **Weather Information Retrieval**: Fetches multi-day weather data for the destination using OpenWeather API to inform planning.
4. **Traveler Persona Generation**: LLM generates multiple traveler personas based on city, weather, days, and user feedback.
5. **User Feedback**: Users can provide feedback on generated personas, and the system supports regeneration based on feedback.
6. **Traveler-Local Dialogue**: Each traveler persona engages in multi-turn dialogue with a simulated local to get specific advice.
7. **Retrieval Augmentation**: Automatically generates search queries from the dialogue and uses Tavily or Wikipedia to fetch relevant information for the local's answers.
8. **Dialogue Summarization**: LLM summarizes the dialogue and retrieval content into structured memos.
9. **Travel Plan Integration**: LLM synthesizes all traveler memos, weather, and user feedback into a final multi-day travel plan, including daily itinerary, multi-currency budget, notes, and source links.
10. **Interactive Demo**: All steps are displayed interactively in the command line, allowing users to view and provide feedback in real time.

---

## Analysis

### Error Cases, Ablations, Limitations, Qualitative Insights

#### Error Cases
- **Missing or Invalid API Keys**: If OpenWeather, Tavily, or other API keys are missing or invalid, weather or retrieval features will fail and return errors.
- **External API Failures**: Network issues, API rate limits, or unrecognized city names can cause failures in weather or geolocation retrieval.
- **LLM Output Structure Issues**: If persona generation or retrieval queries do not follow the expected structure, downstream processes may break.
- **User Input Errors**: Invalid input for days or traveler count defaults to preset values, but extreme cases may not be fully handled.

#### Ablations
- **Retrieval Augmentation Comparison**: Disabling Tavily/Wikipedia retrieval and relying solely on LLM answers can be used to compare the richness and accuracy of plans.
- **Weather Information Comparison**: Removing weather input to observe changes in itinerary adaptability and relevance.
- **User Feedback Impact**: Comparing plans with and without user feedback to analyze the effect of the feedback mechanism.

#### Limitations
- **LLM Hallucination & Factuality**: Despite retrieval augmentation, the LLM may still generate inaccurate or fabricated content, especially when retrieval results are sparse.
- **Budget Estimation**: Currency conversion uses fixed rates; actual prices and rates may vary significantly.
- **Dialogue Depth**: The number of dialogue turns per traveler is limited, which may not cover all details.
- **Plan Executability**: The generated itinerary may not be fully actionable; some suggestions may not fit all users or real-world constraints.

#### Qualitative Insights
- **Plan Readability**: The final travel plan is well-structured, including daily weather, activity rationale, budget, and notes, making it easy to review and use.
- **Response Adaptability**: The system dynamically adjusts itineraries based on weather, user feedback, and retrieval content, providing a degree of personalization and practicality.
- **User Engagement**: Multi-round feedback and interaction allow users to actively participate in persona and plan generation, enhancing the experience.
- **Multi-source Integration**: The plan references multiple sources and deduplicates content, improving authority and richness.
