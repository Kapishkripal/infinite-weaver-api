"""
services/comic_engine.py — Extracts visual prompts and generates images.

Uses the Architect LLM to condense a story chapter into a single visual prompt,
then hits the Pollinations.ai API to generate the raw image.
"""

import os
import urllib.parse
import requests
from pydantic import BaseModel, Field

from services.story_engine import architect_llm

# Ensure temp directory exists
TEMP_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "temp")
os.makedirs(TEMP_DIR, exist_ok=True)


class ScenePrompt(BaseModel):
    """Pydantic model for extracting a visual scene description."""
    image_prompt: str = Field(
        description="A concise, highly visual text-to-image prompt describing the main scene of the story. Include art style (e.g., 'comic book style, vibrant colors, dramatic lighting'). Max 50 words."
    )


def generate_scene_prompt(story_text: str) -> str:
    """Extract a highly visual prompt from the story text using the Architect LLM."""
    if not story_text:
        return "A blank comic book page, comic book style"

    print("[ComicEngine] Extracting visual prompt...")
    structured_llm = architect_llm.with_structured_output(ScenePrompt)
    
    try:
        result = structured_llm.invoke([
            ("system", "You are an expert comic book artist. Extract the single most visually striking scene from the following story chapter and describe it as a text-to-image prompt."),
            ("user", f"Story chapter:\n{story_text}")
        ])
        
        # Defensive extraction
        if hasattr(result, "image_prompt"):
            return result.image_prompt
        elif isinstance(result, dict):
            return result.get("image_prompt", "Comic book scene")
    except Exception as e:
        print(f"[ComicEngine] Failed to extract prompt: {e}")
        
    return "A dramatic comic book scene"


def generate_image(prompt: str, filename="comic_raw.jpg") -> str:
    """
    Hit the Pollinations.ai API to generate an image and save it locally.
    Returns the absolute path to the downloaded image.
    """
    print(f"[ComicEngine] Requesting image for prompt: {prompt}")
    
    # URL encode the prompt
    encoded_prompt = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true"
    
    output_path = os.path.join(TEMP_DIR, filename)
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        with open(output_path, "wb") as f:
            f.write(response.content)
            
        print(f"[ComicEngine] Image saved to {output_path}")
        return output_path
    except Exception as e:
        print(f"[ComicEngine] Failed to generate/download image: {e}")
        return ""
