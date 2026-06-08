import asyncio
from graph.workflow import storyverse_graph

def test_pipeline():
    initial_state = {
        "prompt": "A story about Arthur, a knight in the medieval era whose armor is made of shattered glass. He seeks to protect the glass kingdom from the stone dragons.",
        "user_id": "test_multimodal_5",
        "world_bible": {},
        "interview_history": []
    }
    
    print("Invoking graph directly...")
    result = storyverse_graph.invoke(initial_state, config={"configurable": {"thread_id": "test_multimodal_5"}})
    
    import json
    print("\n--- PIPELINE RESULT ---")
    print(json.dumps({
        "story_draft": result.get("story_draft", "")[:100] + "...",
        "image_paths": result.get("image_paths", []),
    }, indent=2))
    
if __name__ == "__main__":
    test_pipeline()
