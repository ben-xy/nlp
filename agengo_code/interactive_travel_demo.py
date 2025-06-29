#!/usr/bin/env python3


import sys
import os
from typing import Callable, Any
from langchain_core.runnables import RunnableConfig

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def show_weather(weather_data):
    """Display weather information"""
    print("\n🌤️  Weather Information:")
    print("=" * 40)
    if isinstance(weather_data, list) and weather_data:
        for day in weather_data:
            if isinstance(day, dict):
                date = day.get('date', 'N/A')
                summary = day.get('summary', 'N/A')
                temp_min = day.get('temp_min', 'N/A')
                temp_max = day.get('temp_max', 'N/A')
                pop = day.get('pop_max', 'N/A')
                print(f"📅 {date}: {temp_min}°C - {temp_max}°C | {summary} | Rain Probability: {pop}")
    else:
        print("Unable to get weather information")
    print()

def show_travelers(travelers_data):
    """Display traveler information"""
    print("\n👥 Generated Travelers:")
    print("=" * 40)
    if isinstance(travelers_data, list) and travelers_data:
        for i, traveler in enumerate(travelers_data, 1):
            if hasattr(traveler, 'name') and hasattr(traveler, 'description'):
                print(f"👤 {i}. {traveler.name}")
                print(f"   📝 {traveler.description}")
                print()
    else:
        print("No traveler information available")
    print()





def get_user_feedback(prompt: str) -> str:
    """Get user feedback"""
    print(f"\n💬 {prompt}")
    
    feedback = input("> ")
    return feedback

def get_user_input_with_default(prompt: str, default: Any, cast_func: Callable[[str], Any] = str) -> Any:
    """Get user input with default value support"""
    val = input(f"{prompt} (default: {default}): ").strip()
    if not val:
        return default
    try:
        return cast_func(val)
    except Exception:
        print(f"Invalid input, using default value {default}")
        return default

def run_interactive_demo():
    """Run interactive demo"""
    try:
        from travel_assistant import graph
        
        city = get_user_input_with_default("📍📍📍Please enter the destination city", "tokyo", str)
        days = get_user_input_with_default("📍📍📍Please enter the number of travel days", 3, int)
        max_travelers = get_user_input_with_default("📍📍📍Please enter the number of agent travelers generated", 1, int)
        
        initial_state = {
            "city": city,
            "days": days,
            "max_travelers": max_travelers,
            "weather": [],
            "human_feedback_traveler": "",
            "human_feedback_plan": "",
            "travelers": [],
            "sections": [],
            "content": "",
            "final_plan": ""
        }
        
        print(f"📍 Destination: {city}")
        print(f"📅 Days: {days}")
        print(f"👤 Max Travelers: {max_travelers}")
        print("=" * 50)
        
        current_state = initial_state.copy()
        thread = {"configurable": {"thread_id": "1"}}
        
        for event in graph.stream(current_state, thread, stream_mode="values"):
            travelers = event.get('travelers', '')
            if travelers:
                for traveler in travelers:
                    print("👤" * 50)
                    print(f"Name: {traveler.name}")
                    print(f"Description: {traveler.description}")
                     
        
        feedback_t = get_user_feedback("Please review the generated travelers above and provide feedback to regenerate:")
        graph.update_state(thread, {"human_feedback_traveler": feedback_t}, as_node="human_feedback_traveler_node")
        for event in graph.stream(None, thread, stream_mode="values"):
            travelers = event.get('travelers', '')
            if travelers:
                for traveler in travelers:
                    print("👤" * 50)
                    print(f"Name: {traveler.name}")
                    print(f"Description: {traveler.description}")
                    
        graph.update_state(thread, {"human_feedback_traveler": None}, as_node="human_feedback_traveler_node") 
        for event in graph.stream(None, thread, stream_mode="values"):
            final_plan = event.get('final_plan', '')
            if final_plan:
                print("final_plan" )
                print("📅" * 50)
                print(final_plan)
                print("📅" * 50)
        print("✅ Demo complete!")
        print("=" * 50)
    except Exception as e:
        print(f"❌ Execution error: {e}")

# Check main entry
if __name__ == "__main__":
    run_interactive_demo() 