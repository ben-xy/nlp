#!/usr/bin/env python3
"""
Travel Agent System Quick Start Script (Updated for travel_agent_1.py)
Demonstrates human feedback nodes and map-reduce pattern
"""

import os, getpass
from dotenv import load_dotenv
import sys

def check_api_key():
    """Check API keys"""
    load_dotenv()
    def _set_env(var: str) -> bool:
        if not os.environ.get(var):
            print(f"⚠️  {var} environment variable not set")
            print(f"Please set your {var}:")
            value = getpass.getpass(f"{var}: ").strip()
            if value:
                os.environ[var] = value
                print("✅ API key set")
                return True
            else:
                print("❌ No API key provided")
                return False
        return True
    
    if not _set_env("OPENAI_API_KEY"):
        return False
    if not _set_env("OPENWEATHER_KEY"):
        return False
    if not _set_env("TAVILY_API_KEY"):
        return False
    
    return True

def interactive_demo():
    """Interactive demonstration with human feedback nodes"""
    print("🎯 Interactive Demo with Human Feedback Nodes 🚀")
    print("=" * 50)
    
    if not check_api_key():
        return
    
    try:
        from travel_agent_3 import run_travel_agent, continue_with_feedback
        
        print("\n💬 Please enter your destination:")
        print("Examples: I want to travel to Tokyo")
        
        user_input = input("\nPlease enter: ").strip()
        

        
        print(f"\n🚀 Starting to process: {user_input}")
        
        # Create graph and run with LangGraph
        graph, initial_state, thread = run_travel_agent(user_input, thread_id="interactive_demo")
        
        print("\n=== Starting assistant ===")
        
        # Run the graph until first interruption (subtopics feedback)
        
        events = []
        for event in graph.stream(initial_state, config={"configurable": {"thread_id": thread["configurable"]["thread_id"]}}, stream_mode="updates"):
            events.append(event)
        
   
        final_event = None
        for event in reversed(events): 
            if "__interrupt__" not in event:  
                final_event = event
                break


        if final_event is None and events:
            for event in reversed(events):
                if list(event.keys())[0] != "__interrupt__":
                    final_event = event
                    break

  
        if final_event is None and events:
            final_event = events[-1]


        if final_event:
            node_name = list(final_event.keys())[0]
            node_state = final_event[node_name]
            
            
            if "detected_locations" in node_state and node_state["detected_locations"]:
                print(f"✅ Detected locations: {node_state['detected_locations']}")
            if "subtopics" in node_state and node_state["subtopics"]:
                print(f"✅ Generated subtopics: {node_state['subtopics']}")
            if "weather_info" in node_state and node_state["weather_info"]:
                print(f"✅ Retrieved weather information")
                
                for loc, weather in node_state["weather_info"].items():
                    print(f"  {loc} Weather:")
                    for day in weather:
                        if "error" not in day:
                            print(f"    {day['date']}: {day['summary']}, {day['temp_min']}°C - {day['temp_max']}°C, Rain: {day['pop_max']*100:.0f}%")


        
        print("\n=== 🔄 UNLIMITED SUBTOPICS FEEDBACK LOOP ===")
        print("The assistant is now waiting for your feedback on the subtopics.")
        print("You can provide feedback to modify the subtopics, or type 'ok', 'good', 'satisfied', 'yes', 'no changes', 'proceed', 'continue', 'next' to proceed to plan generation.")
        print("You can provide multiple rounds of feedback until you're satisfied!")
        
        # Get user feedback for subtopics (unlimited loop)
        feedback_count = 0
        while True:
            feedback_count += 1
            print(f"\n--- Feedback Round {feedback_count} ---")
            subtopics_feedback = input("Enter your feedback on subtopics (or type 'ok', 'good', 'satisfied', 'yes', 'no changes', 'proceed', 'continue', 'next' to proceed): ")
            
            # Check if user wants to proceed first
            if subtopics_feedback.lower() in ["ok", "good", "satisfied", "yes", "no changes", "proceed", "continue", "next"]:
                print(f"✅ Proceeding to plan generation after {feedback_count} feedback rounds")
                
                # Continue execution to generate the plan
                print("\n=== Generating travel plan ===")
                events = []
                for event in continue_with_feedback(graph, thread, "subtopics", subtopics_feedback):
                    events.append(event)
                
                # Find the last non-interrupt event
                final_event = None
                for event in reversed(events):
                    if "__interrupt__" not in event:
                        final_event = event
                        break
                
                if final_event:
                    node_name = list(final_event.keys())[0]
                    node_state = final_event[node_name]
                    
                    if "travel_plan" in node_state:
                        print("\n" + "="*50)

                        print("="*50)
                        print(node_state["travel_plan"])
                
                break
            
            # Continue with subtopics feedback
            print("\n=== Processing subtopics feedback ===")
            events = []
            for event in continue_with_feedback(graph, thread, "subtopics", subtopics_feedback):
                events.append(event)
            
            # Find the last non-interrupt event
            final_event = None
            for event in reversed(events):
                if "__interrupt__" not in event:
                    final_event = event
                    break
            
            if final_event:
                node_name = list(final_event.keys())[0]
                node_state = final_event[node_name]
                
                if "subtopics" in node_state:
                    print(f"✅ Updated subtopics: {node_state['subtopics']}")
                    print("\nCurrent subtopics:")
                    for i, subtopic in enumerate(node_state['subtopics'], 1):
                        print(f"  {i}. {subtopic}")
                if "travel_plan" in node_state:
                    print("\n" + "="*50)

                    print("="*50)
                    print(node_state["travel_plan"])
            
        print("\n=== 🔄 UNLIMITED PLAN FEEDBACK LOOP ===")
        print("The assistant is now waiting for your feedback on the travel plan.")
        print("You can provide feedback to modify the plan, or type 'ok', 'good', 'satisfied', 'yes', 'no changes', 'proceed', 'continue', 'next', 'end', 'finish' to complete.")
        print("You can provide multiple rounds of feedback until you're satisfied!")
        
        # Get user feedback for travel plan (unlimited loop)
        feedback_count = 0
        while True:
            feedback_count += 1
            print(f"\n--- Feedback Round {feedback_count} ---")
            plan_feedback = input("Enter your feedback on travel plan (or type 'ok', 'good', 'satisfied', 'yes', 'no changes', 'proceed', 'continue', 'next', 'end', 'finish' to complete): ")
            
            # Check if user wants to end first
            if plan_feedback.lower() in ["ok", "good", "satisfied", "yes", "no changes", "proceed", "continue", "next", "end", "finish"]:
                print(f"✅ Completing after {feedback_count} feedback rounds")
                break
            
            # Continue with plan feedback
            print("\n=== Processing plan feedback ===")
            events = []
            for event in continue_with_feedback(graph, thread, "plan", plan_feedback):
                events.append(event)
            
            # Find the last non-interrupt event
            final_event = None
            for event in reversed(events):
                if "__interrupt__" not in event:
                    final_event = event
                    break
            
            if final_event:
                node_name = list(final_event.keys())[0]
                node_state = final_event[node_name]
                
                if "travel_plan" in node_state:
                    print("\n" + "="*50)
                    print("🎉 Updated travel plan! 🎉")
                    print("="*50)
                    print(node_state["travel_plan"])
            
        print("\n=== Demo completed ===")
        print("🎉 Unlimited feedback system working correctly! 🎉")

    except Exception as e:
        print(f"❌ Demo error: {str(e)}")
        print("Please check network connection and API key settings")
        import traceback
        traceback.print_exc()

def video_demo():
    """Video file demonstration with human feedback nodes"""
    print("🎬 Travel Agent System - Video File Demo with Human Feedback")
    print("=" * 60)
    
    if not check_api_key():
        return
    
    try:
        from travel_agent_3 import run_travel_agent, continue_with_feedback
        
        video_path = input("\n🎬 Please enter video path: ").strip()    
        if not video_path or not os.path.exists(video_path):
            print("❌ Video file does not exist or path is invalid")
            return

        print(f"\n🎬 Starting to process video: {video_path}")
        
        # Create graph and run with LangGraph
        graph, initial_state, thread = run_travel_agent(video_file_path=video_path, thread_id="video_demo")
        
        print("\n=== Starting Video Processing ===")
        
        # Run the graph until first interruption
        
        events = []
        for event in graph.stream(initial_state, config={"configurable": {"thread_id": thread["configurable"]["thread_id"]}}, stream_mode="updates"):
            events.append(event)
        
  
        final_event = None
        for event in reversed(events):  
            if "__interrupt__" not in event:  
                final_event = event
                break

  
        if final_event is None and events:
            final_event = events[-1]


        if final_event:
            node_name = list(final_event.keys())[0]
            node_state = final_event[node_name]
            

            if "video_transcript" in node_state:
                print(f"✅ Video transcript: {node_state['video_transcript'][:100]}...")
            if "detected_locations" in node_state and node_state["detected_locations"]:
                print(f"✅ Detected locations: {node_state['detected_locations']}")
            if "subtopics" in node_state and node_state["subtopics"]:
                print(f"✅ Generated subtopics: {node_state['subtopics']}")
            if "weather_info" in node_state and node_state["weather_info"]:
                print(f"✅ Retrieved weather information")
    
                for loc, weather in node_state["weather_info"].items():
                    print(f"  {loc} Weather:")
                    for day in weather:
                        if "error" not in day:
                            print(f"    {day['date']}: {day['summary']}, {day['temp_min']}°C - {day['temp_max']}°C, Rain: {day['pop_max']*100:.0f}%")


        
        print("\n=== 🔄 UNLIMITED SUBTOPICS FEEDBACK LOOP ===")
        print("The assistant is now waiting for your feedback on the subtopics.")
        print("You can provide feedback to modify the subtopics, or type 'ok', 'good', 'satisfied', 'yes', 'no changes', 'proceed', 'continue', 'next' to proceed to plan generation.")
        print("You can provide multiple rounds of feedback until you're satisfied!")
        
        # Get user feedback for subtopics (unlimited loop)
        feedback_count = 0
        while True:
            feedback_count += 1
            print(f"\n--- Feedback Round {feedback_count} ---")
            subtopics_feedback = input("Enter your feedback on subtopics (or type 'ok', 'good', 'satisfied', 'yes', 'no changes', 'proceed', 'continue', 'next' to proceed): ")
            
            # Check if user wants to proceed first
            if subtopics_feedback.lower() in ["ok", "good", "satisfied", "yes", "no changes", "proceed", "continue", "next"]:
                print(f"✅ Proceeding to plan generation after {feedback_count} feedback rounds")
                
                # Continue execution to generate the plan
                print("\n=== Generating travel plan ===")
                events = []
                for event in continue_with_feedback(graph, thread, "subtopics", subtopics_feedback):
                    events.append(event)
                
                # Find the last non-interrupt event
                final_event = None
                for event in reversed(events):
                    if "__interrupt__" not in event:
                        final_event = event
                        break
                
                if final_event:
                    node_name = list(final_event.keys())[0]
                    node_state = final_event[node_name]
                    
                    if "travel_plan" in node_state:
                        print("\n" + "="*50)
 
                        print("="*50)
                        print(node_state["travel_plan"])
                
                break
            
            # Continue with subtopics feedback
            print("\n=== Processing subtopics feedback ===")
            events = []
            for event in continue_with_feedback(graph, thread, "subtopics", subtopics_feedback):
                events.append(event)
            
            # Find the last non-interrupt event
            final_event = None
            for event in reversed(events):
                if "__interrupt__" not in event:
                    final_event = event
                    break
            
            if final_event:
                node_name = list(final_event.keys())[0]
                node_state = final_event[node_name]
                
                if "subtopics" in node_state:
                    print(f"✅ Updated subtopics: {node_state['subtopics']}")
                    print("\nCurrent subtopics:")
                    for i, subtopic in enumerate(node_state['subtopics'], 1):
                        print(f"  {i}. {subtopic}")
                if "travel_plan" in node_state:
                    print("\n" + "="*50)

                    print("="*50)
                    print(node_state["travel_plan"])
            
        print("\n=== 🔄 UNLIMITED PLAN FEEDBACK LOOP ===")
        print("The assistant is now waiting for your feedback on the travel plan.")
        print("You can provide feedback to modify the plan, or type 'ok', 'good', 'satisfied', 'yes', 'no changes', 'proceed', 'continue', 'next', 'end', 'finish' to complete.")
        print("You can provide multiple rounds of feedback until you're satisfied!")
        
        # Get user feedback for travel plan (unlimited loop)
        feedback_count = 0
        while True:
            feedback_count += 1
            print(f"\n--- Feedback Round {feedback_count} ---")
            plan_feedback = input("Enter your feedback on travel plan (or type 'ok', 'good', 'satisfied', 'yes', 'no changes', 'proceed', 'continue', 'next', 'end', 'finish' to complete): ")
            
            # Check if user wants to end first
            if plan_feedback.lower() in ["ok", "good", "satisfied", "yes", "no changes", "proceed", "continue", "next", "end", "finish"]:
                print(f"✅ Completing after {feedback_count} feedback rounds")
                break
            
            # Continue with plan feedback
            print("\n=== Processing plan feedback ===")
            events = []
            for event in continue_with_feedback(graph, thread, "plan", plan_feedback):
                events.append(event)
            
            # Find the last non-interrupt event
            final_event = None
            for event in reversed(events):
                if "__interrupt__" not in event:
                    final_event = event
                    break
            
            if final_event:
                node_name = list(final_event.keys())[0]
                node_state = final_event[node_name]
                
                if "travel_plan" in node_state:
                    print("\n" + "="*50)
                    print("🎉 Updated travel plan! 🎉")
                    print("="*50)
                    print(node_state["travel_plan"])
            
        print("\n=== Demo completed ===")
        print("🎉 Unlimited feedback system working correctly! 🎉")

    except Exception as e:
        print(f"❌ Demo error: {str(e)}")
        print("Please check video file format and dependency settings")
        import traceback
        traceback.print_exc()




def main():
    """Main function"""
    print("🎯🎯🎯 Travel Agent System Quick Start (Updated) 🎯🎯🎯")
    print("🎉" * 20)
    

    
    while True:
        print("\nPlease select demo mode:")

        print("1. Interactive demo with human feedback nodes")
        print("2. Video file demo with human feedback nodes")

        print("0. Exit")
        
        choice = input("\nPlease enter your choice (0-2): ").strip()
        
        if choice == "0":
            print("👋👋👋Thank you for using the Travel Agent System!👋👋👋")
            break
        elif choice == "1":
            interactive_demo()
        elif choice == "2":
            video_demo()

        else:
            print("❌❌❌ Invalid choice, please re-enter ❌❌❌")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Program interrupted by user")
    except Exception as e:
        print(f"\n❌ Program error: {str(e)}")
        print("Please check dependencies and environment variable settings") 