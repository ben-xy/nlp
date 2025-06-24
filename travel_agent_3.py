import os, getpass
import json
import requests
from functools import lru_cache
from typing import Dict, Any, List, Optional, TypedDict, Annotated
from typing_extensions import TypedDict
from operator import add
import tempfile

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool
from langgraph.types import Send
from dotenv import load_dotenv

# Environment variable setup
def _set_env(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"{var}: ")

load_dotenv()
_set_env("OPENAI_API_KEY")
_set_env("OPENWEATHER_KEY")
_set_env("TAVILY_API_KEY")

# Get environment variables
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENWEATHER_KEY = os.environ.get("OPENWEATHER_KEY", "")
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "")

# Initialize LLM
llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0.0
)

# ==================== State Definitions ====================

class TravelState(TypedDict, total=False):
    user_query: str
    video_file_path: Optional[str]
    video_transcript: Optional[str]
    full_text: str
    detected_locations: List[str]
    has_locations: bool
    weather_info: Dict[str, Any]
    subtopics: List[str]
    subtopics_feedback: Optional[str]
    subtopic_results: Dict[str, Any]
    travel_plan: str
    plan_feedback: Optional[str]
    messages: List[Dict[str, str]]

class SubtopicState(TypedDict):
    subtopic: str
    location: str
    search_results: str
    summary: str

class BestSubtopicState(TypedDict):
    topic: str
    subtopics: List[str]
    subtopic_results: Annotated[List[str], add]
    best_subtopics: List[str]

# ==================== Utility Functions ====================

@lru_cache(maxsize=128)
def get_latlon(destination: str) -> str:
    """Get latitude and longitude for a destination"""
    resp = requests.get(
        "https://nominatim.openstreetmap.org/search",
        params={"q": destination, "format": "json", "limit": 1},
        headers={"User-Agent": "Travel-Agent"},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    if not data:
        raise ValueError(f"Cannot resolve coordinates for '{destination}'")
    return f"{data[0]['lat']},{data[0]['lon']}"

def get_weather(city: str, days: int = 5) -> List[Dict]:
    """Get weather information for a city"""
    if not OPENWEATHER_KEY:
        return [{"error": "OpenWeather API key not set"}]
    
    try:
        lat, lon = map(float, get_latlon(city).split(","))
        resp = requests.get(
            "https://api.openweathermap.org/data/2.5/forecast",
            params={
                "lat": lat,
                "lon": lon,
                "appid": OPENWEATHER_KEY,
                "units": "metric",
                "lang": "en",
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()["list"]

        daily = {}
        for item in data:
            date = item["dt_txt"][:10]
            if date not in daily:
                daily[date] = {"temps": [], "descs": [], "pops": []}
            daily[date]["temps"].append(item["main"]["temp"])
            daily[date]["descs"].append(item["weather"][0]["description"])
            daily[date]["pops"].append(item.get("pop", 0.0))

        out = []
        for date, rec in sorted(daily.items())[:days]:
            out.append({
                "date": date,
                "summary": max(set(rec["descs"]), key=rec["descs"].count),
                "temp_max": round(max(rec["temps"]), 1),
                "temp_min": round(min(rec["temps"]), 1),
                "pop_max": round(max(rec["pops"]), 2),
            })
        return out
    except Exception as e:
        return [{"error": f"Failed to get weather information: {str(e)}"}]

def search_web(query: str) -> str:
    """Search web information using Tavily"""
    if not TAVILY_API_KEY:
        return "Tavily API key not set, cannot perform web search"
    
    try:
        resp = requests.get(
            "https://api.tavily.com/search",
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
        return f"Search failed: {str(e)}"

def extract_audio_from_video(video_file_path: str) -> str:
    """Extract audio from video file using ffmpeg"""
    try:
        import subprocess
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
        if result.returncode != 0:
            return "ffmpeg not installed, cannot process video files. Please install ffmpeg: https://ffmpeg.org/download.html"
        
        # Create temporary audio file
        audio_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        audio_file_path = audio_file.name
        audio_file.close()
        
        # Use ffmpeg to extract audio
        cmd = [
            'ffmpeg', '-i', video_file_path,
            '-vn',  # No video
            '-acodec', 'pcm_s16le',  # Audio codec
            '-ar', '16000',  # Sample rate
            '-ac', '1',  # Mono
            '-y',  # Overwrite output file
            audio_file_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Audio extraction successful: {audio_file_path}")
            return audio_file_path
        else:
            return f"Audio extraction failed: {result.stderr}"
            
    except Exception as e:
        return f"Video processing error: {str(e)}"

def transcribe_audio(audio_file_path: str) -> str:
    """Transcribe audio using Whisper"""
    try:
        # Check if whisper is installed
        try:
            import whisper
        except ImportError:
            return "Whisper not installed, cannot transcribe audio. Please run: pip install openai-whisper"
        
        model = whisper.load_model("base")
        result = model.transcribe(audio_file_path)
        text_result = result.get("text", "")
        if isinstance(text_result, list):
            text_result = " ".join(text_result)
        return text_result
    except Exception as e:
        return f"Audio transcription failed: {str(e)}"

def process_video_file(video_file_path: str) -> str:
    """Process video file, extract audio and transcribe"""
    print(f"Processing video file: {video_file_path}")
    
    # Extract audio
    audio_file_path = extract_audio_from_video(video_file_path)
    if audio_file_path.startswith("Error") or audio_file_path.startswith("ffmpeg not installed"):
        return audio_file_path
    
    # Transcribe audio
    transcript = transcribe_audio(audio_file_path)
    
    # Clean up temporary audio file
    try:
        os.unlink(audio_file_path)
    except:
        pass
    
    return transcript

# ==================== Main Graph Nodes ====================

def process_input(state: TravelState) -> TravelState:
    """Process user input (text or video)"""
    user_query = state.get("user_query", "")
    video_file_path = state.get("video_file_path")
    
    if video_file_path:
        print(f"Processing video file: {video_file_path}")
        transcript = process_video_file(video_file_path)
        full_text = f"{user_query} {transcript}".strip()
        return {
            **state,
            "video_transcript": transcript,
            "full_text": full_text
        }
    else:
        return {
            **state,
            "full_text": user_query
        }

def generate_locations_and_subtopics(state: TravelState) -> TravelState:
    """Extract locations and generate subtopics from input text"""
    full_text = state.get("full_text", "")
    
    # Enhanced prompt for better location detection
    location_prompt = f"""
    You are a travel assistant. Extract destination locations from the following text.
    
    IMPORTANT: You must return a valid JSON array of location names. Even simple city names like "chengdu", "singapore", "seoul" should be detected.
    
    Text: {full_text}
    
    Return ONLY a JSON array of location names, for example: ["Seoul", "Tokyo"] or ["Chengdu", "Beijing"]
    """
    
    try:
        response = llm.invoke([HumanMessage(content=location_prompt)])
        
        content = response.content
        if isinstance(content, str):
            content = content.strip()
            
            # Try to parse JSON from the response
            if content.startswith("```json"):
                content = content[7:-3]
            elif content.startswith("```"):
                content = content[3:-3]
            
            
            
            locations = json.loads(content)
            if not isinstance(locations, list):
                locations = [locations]
        else:
            locations = []
        
        
        
        # Generate subtopics based on locations
        subtopics_prompt = f"""
        You are a travel assistant. Based on the detected locations: {locations}
        Generate 5 travel-related subtopics that would be useful for planning a trip to these destinations.
        
        Examples: "Best restaurants", "Historical sites", "Shopping districts", "Public transportation", "Cultural experiences"
        
        Return ONLY a JSON array of subtopic strings.
        """
        
        response = llm.invoke([HumanMessage(content=subtopics_prompt)])
        
        content = response.content
        if isinstance(content, str):
            content = content.strip()
            
            if content.startswith("```json"):
                content = content[7:-3]
            elif content.startswith("```"):
                content = content[3:-3]
            
            
            
            subtopics = json.loads(content)
            if not isinstance(subtopics, list):
                subtopics = [subtopics]
        else:
            subtopics = []
        

        
        return {
            **state,
            "detected_locations": locations,
            "has_locations": len(locations) > 0,
            "subtopics": subtopics
        }
        
    except Exception as e:
        print(f"Error parsing locations/subtopics: {e}")
        print(f"Raw response: {response.content if 'response' in locals() else 'No response'}")
        return {
            **state,
            "detected_locations": [],
            "has_locations": False,
            "subtopics": []
        }

def get_weather_info(state: TravelState) -> TravelState:
    """Get weather information for detected locations"""
    locations = state.get("detected_locations", [])
    weather_info = {}
    
    for location in locations:
        try:
            weather_data = get_weather(location)
            weather_info[location] = weather_data
            
        except Exception as e:
            weather_info[location] = [{"error": f"Failed to get weather: {str(e)}"}]
    
    return {
        **state,
        "weather_info": weather_info
    }

# ==================== Human Feedback Nodes ====================

def human_feedback_subtopics(state: TravelState) -> TravelState:
    """Human feedback node for subtopics - no-op node that will be interrupted"""
    return state

def human_feedback_plan(state: TravelState) -> TravelState:
    """Human feedback node for travel plan - no-op node that will be interrupted"""
    return state

def should_continue_subtopics(state: TravelState) -> str:
    """Determine if we should continue with subtopics feedback or proceed to plan generation"""
    subtopics_feedback = state.get("subtopics_feedback", "")
    
    # Check if user is satisfied (wants to proceed)
    if subtopics_feedback and subtopics_feedback.lower() in ["satisfied", "ok", "good", "yes", "no changes", "proceed", "continue", "next"]:
        return "generate_final_plan"
    
    # If there's feedback, regenerate subtopics
    if subtopics_feedback:
        return "process_subtopics_feedback"
    
    # Default: continue with subtopics feedback
    return "human_feedback_subtopics"

def should_continue_plan(state: TravelState) -> str:
    """Determine if we should continue with plan feedback or end"""
    plan_feedback = state.get("plan_feedback", "")
    
    # Check if user is satisfied (wants to end)
    if plan_feedback and plan_feedback.lower() in ["satisfied", "ok", "good", "yes", "no changes", "proceed", "continue", "next", "end", "finish"]:
        return END
    
    # If there's feedback, regenerate plan
    if plan_feedback:
        return "process_plan_feedback"
    
    # Default: continue with plan feedback
    return "human_feedback_plan"

def process_subtopics_feedback(state: TravelState) -> TravelState:
    """Process user feedback on subtopics"""
    feedback = state.get("subtopics_feedback", "")
    
    if not feedback:
        return state
    
    # Regenerate subtopics based on feedback
    locations = state.get("detected_locations", [])
    prompt = f"""
    You are a travel assistant. Based on user feedback, regenerate subtopics for the locations: {locations}
    
    Original subtopics: {state.get("subtopics", [])}
    User feedback: {feedback}
    
    Generate new subtopics that address the feedback. Return ONLY a JSON array of subtopic strings.
    """
    
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        content = response.content
        if isinstance(content, str):
            content = content.strip()
            
            if content.startswith("```json"):
                content = content[7:-3]
            elif content.startswith("```"):
                content = content[3:-3]
            
            new_subtopics = json.loads(content)
            if not isinstance(new_subtopics, list):
                new_subtopics = [new_subtopics]
        else:
            new_subtopics = state.get("subtopics", [])
        
        print(f"Updated subtopics based on feedback: {new_subtopics}")
        
        return {
            **state,
            "subtopics": new_subtopics,
            "subtopics_feedback": None  # Clear feedback after processing
        }
    except Exception as e:
        print(f"Error processing subtopics feedback: {e}")
        return state

def process_plan_feedback(state: TravelState) -> TravelState:
    """Process user feedback on the travel plan"""
    feedback = state.get("plan_feedback", "")
    
    if not feedback:
        return state
    
    prompt = f"""
    You are a travel planner. Based on user feedback, regenerate the travel plan:
    
    Original plan:
    {state.get("travel_plan", "")}
    
    User feedback: {feedback}
    
    Please regenerate the travel plan based on the feedback.
    """
    
    response = llm.invoke([HumanMessage(content=prompt)])
    content = response.content
    travel_plan = content if isinstance(content, str) else state.get("travel_plan", "")
    
    return {
        **state,
        "travel_plan": travel_plan,
        "plan_feedback": None  # Clear feedback after processing
    }

# ==================== Map-Reduce Pattern for Subtopics ====================

def research_subtopic(state: SubtopicState) -> SubtopicState:
    """Research a specific subtopic for a location"""
    subtopic = state.get("subtopic", "")
    location = state.get("location", "")
    
    # Search for information about this subtopic in this location
    query = f"{subtopic} in {location}"
    search_results = search_web(query)
    
    # Generate summary
    prompt = f"""
    You are a travel planner. Based on the following search results, generate a detailed summary for "{subtopic} in {location}":
    
    Search results:
    {search_results}
    
    Please generate a structured summary with key information and recommendations.
    """
    
    response = llm.invoke([HumanMessage(content=prompt)])
    content = response.content
    summary = content if isinstance(content, str) else ""
    
    return {
        **state,
        "search_results": search_results,
        "summary": summary
    }

def run_subtopics_map(state: TravelState) -> List[Send]:
    """Map function: send each subtopic to research"""
    subtopics = state.get("subtopics", [])
    locations = state.get("detected_locations", [])
    
    sends = []
    for subtopic in subtopics:
        for location in locations:
            sends.append(Send("research_subtopic", {
                "subtopic": subtopic,
                "location": location
            }))
    
    return sends

def run_subtopics_reduce(state: TravelState) -> TravelState:
    """Reduce function: collect all subtopic research results"""
    # The results will be automatically collected via the Annotated[List[str], add] in state
    return state

def generate_final_plan(state: TravelState) -> TravelState:
    """Generate final travel plan with all information"""
    
    
    locations = state.get("detected_locations", [])
    weather_info = state.get("weather_info", {})
    subtopic_results = state.get("subtopic_results", {})
    

    
    # Format weather information
    weather_summary = ""
    for location, weather_data in weather_info.items():
        if isinstance(weather_data, list) and weather_data:
            weather_summary += f"\n{location} Weather:\n"
            for day in weather_data:
                if "error" not in day:
                    weather_summary += f"  {day['date']}: {day['summary']}, {day['temp_min']}°C - {day['temp_max']}°C, Rain: {day['pop_max']*100:.0f}%\n"
    

    
    # Format subtopic results
    subtopics_summary = ""
    for key, summary in subtopic_results.items():
        location, subtopic = key.split("_", 1)
        subtopics_summary += f"\n{location} - {subtopic}:\n{summary}\n"
    
    # If no subtopic results, create a basic plan
    if not subtopics_summary:
        subtopics_summary = f"\nBasic information for {', '.join(locations)}:\nBased on general travel knowledge and weather conditions."
    
   
    
    prompt = f"""
    You are a professional travel planner. Create a comprehensive travel plan for: {', '.join(locations)}
    
    Weather Information: {weather_summary}
    
    Subtopic Research Results: {subtopics_summary}
    
    IMPORTANT: Please consider the weather conditions when planning activities:
    - For rainy days: Plan indoor activities (museums, shopping malls, restaurants, indoor attractions)
    - For sunny days: Plan outdoor activities (parks, outdoor attractions, walking tours)
    - For hot weather: Include air-conditioned venues and suggest appropriate clothing
    - For cold weather: Include indoor activities and suggest warm clothing
    - Adjust transportation plans based on weather (avoid walking in heavy rain)
    
    Please generate a structured travel plan including:
    1. Trip overview with weather considerations
    2. Daily detailed itinerary that adapts to weather conditions - IMPORTANT: For each day, explicitly mention the weather and how it affects the activities chosen
    3. Budget estimation
    
    IMPORTANT: In the budget section, for each item and the total, show both USD and the local currency of the destination (e.g., KRW for Seoul, JPY for Tokyo, EUR for Paris). Use a reasonable approximate exchange rate (e.g., 1 USD ≈ 1,300 KRW, 1 USD ≈ 150 JPY, 1 USD ≈ 0.92 EUR). Format: $100 / ₩130,000.
    
    4. Important notes and tips including weather-appropriate clothing and activities
    
    Format should be clear and easy to read. For each day in the itinerary, start with the weather information and explain why specific activities were chosen based on the weather conditions.
    """
    
    
    response = llm.invoke([HumanMessage(content=prompt)])
    content = response.content
    travel_plan = content if isinstance(content, str) else ""
    

    
    return {
        **state,
        "travel_plan": travel_plan,
        
    }

# ==================== Graph Construction ====================

# Build main graph
builder = StateGraph(TravelState)

# Add nodes
builder.add_node("process_input", process_input)
builder.add_node("generate_locations_and_subtopics", generate_locations_and_subtopics)
builder.add_node("get_weather", get_weather_info)
builder.add_node("human_feedback_subtopics", human_feedback_subtopics)
builder.add_node("process_subtopics_feedback", process_subtopics_feedback)
builder.add_node("generate_final_plan", generate_final_plan)
builder.add_node("human_feedback_plan", human_feedback_plan)
builder.add_node("process_plan_feedback", process_plan_feedback)

# Add edges with conditional routing for unlimited feedback
builder.add_edge(START, "process_input")
builder.add_edge("process_input", "generate_locations_and_subtopics")
builder.add_edge("generate_locations_and_subtopics", "get_weather")
builder.add_edge("get_weather", "human_feedback_subtopics")

# Conditional edges for subtopics feedback loop
builder.add_conditional_edges(
    "human_feedback_subtopics",
    should_continue_subtopics,
    {
        "human_feedback_subtopics": "human_feedback_subtopics",
        "process_subtopics_feedback": "process_subtopics_feedback",
        "generate_final_plan": "generate_final_plan"
    }
)

# Connect subtopics processing back to feedback loop
builder.add_edge("process_subtopics_feedback", "human_feedback_subtopics")

# Connect plan generation to plan feedback
builder.add_edge("generate_final_plan", "human_feedback_plan")

# Conditional edges for plan feedback loop
builder.add_conditional_edges(
    "human_feedback_plan",
    should_continue_plan,
    {
        "human_feedback_plan": "human_feedback_plan",
        "process_plan_feedback": "process_plan_feedback",
        END: END
    }
)

# Connect plan processing back to feedback loop
builder.add_edge("process_plan_feedback", "human_feedback_plan")

# Compile graph with checkpointer and interruptions
memory = MemorySaver()
graph = builder.compile(
    checkpointer=memory,
    interrupt_before=["human_feedback_subtopics", "human_feedback_plan"]
)

# ==================== Usage Functions ====================

def create_travel_agent():
    """Create travel agent instance"""
    return graph

def run_travel_agent(user_query: str = "", audio_file_path: Optional[str] = None, video_file_path: Optional[str] = None, thread_id: str = "default"):
    """Run the travel agent"""
    # Initial state
    initial_state = {
        "user_query": user_query,
        "audio_file_path": audio_file_path,
        "video_file_path": video_file_path,
        "video_transcript": None,
        "detected_locations": [],
        "has_locations": False,
        "weather_info": {},
        "subtopics": [],
        "subtopics_feedback": None,
        "subtopic_results": {},
        "travel_plan": "",
        "plan_feedback": None,
        "messages": []
    }
    
    thread = {"configurable": {"thread_id": thread_id}}
    
    
    
    return graph, initial_state, thread

def continue_with_feedback(graph, thread, feedback_type: str, feedback_content: str):
    """Continue execution with feedback"""
    if feedback_type == "subtopics":
        graph.update_state(thread, {"subtopics_feedback": feedback_content}, as_node="human_feedback_subtopics")
    elif feedback_type == "plan":
        graph.update_state(thread, {"plan_feedback": feedback_content}, as_node="human_feedback_plan")
    
    return graph.stream(None, config={"configurable": {"thread_id": thread["configurable"]["thread_id"]}}, stream_mode="updates")

# Example usage
if __name__ == "__main__":
    # Example: Text input
    graph, initial_state, thread = run_travel_agent(
        user_query="I want to visit Seoul and Tokyo for 5 days",
        thread_id="example_1"
    )
    
    # Run the graph
    for event in graph.stream(initial_state, stream_mode="values"):
        print(f"Node: {list(event.keys())[0]}")
        if "detected_locations" in event:
            print(f"Locations: {event['detected_locations']}")
        if "subtopics" in event:
            print(f"Subtopics: {event['subtopics']}")
        if "travel_plan" in event:
            print(f"Travel plan generated!")
