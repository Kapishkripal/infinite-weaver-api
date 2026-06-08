"""
services/meme_engine.py — Extracts quotes and stamps text onto images using Pillow.
"""

import os
import requests
from pydantic import BaseModel, Field
from PIL import Image, ImageDraw, ImageFont

from services.story_engine import inquisitor_llm

TEMP_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "temp")
FONT_PATH = os.path.join(TEMP_DIR, "Anton-Regular.ttf")


class MemeQuote(BaseModel):
    """Pydantic model for top and bottom text extraction."""
    top_text: str = Field(description="Catchy, humorous top text for a meme based on the story. Max 8 words. ALL CAPS.")
    bottom_text: str = Field(description="Punchy, humorous bottom text. Max 8 words. ALL CAPS.")


def download_font_if_missing():
    """Downloads the Anton font from Google Fonts to simulate Impact."""
    if not os.path.exists(FONT_PATH):
        print("[MemeEngine] Downloading Anton font...")
        url = "https://github.com/google/fonts/raw/main/ofl/anton/Anton-Regular.ttf"
        try:
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            with open(FONT_PATH, "wb") as f:
                f.write(r.content)
            print("[MemeEngine] Font downloaded.")
        except Exception as e:
            print(f"[MemeEngine] Failed to download font: {e}")


def extract_humorous_quote(story_text: str) -> tuple[str, str]:
    """Uses the LLM to generate top and bottom meme text based on the story."""
    if not story_text:
        return ("WHEN YOU REALIZE", "THE SCRIPT IS EMPTY")
        
    print("[MemeEngine] Extracting meme quotes...")
    structured_llm = inquisitor_llm.with_structured_output(MemeQuote)
    
    try:
        result = structured_llm.invoke([
            ("system", "You are an internet meme lord. Create a hilarious meme caption (top text and bottom text) based on the dramatic elements of this story chapter."),
            ("user", f"Story chapter:\n{story_text}")
        ])
        
        # Defensive extraction
        if hasattr(result, "top_text"):
            return (result.top_text.upper(), result.bottom_text.upper())
        elif isinstance(result, dict):
            return (result.get("top_text", "MEME TEXT").upper(), result.get("bottom_text", "BOTTOM TEXT").upper())
    except Exception as e:
        print(f"[MemeEngine] Failed to extract quote: {e}")
        
    return ("A KNIGHT IN SHATTERED GLASS", "STILL LOOKS SHARP")


def _draw_text_with_outline(draw, position, text, font, fill_color, outline_color, outline_width):
    """Helper to draw text with a thick stroke outline."""
    x, y = position
    # Draw outline (stroke) by drawing text shifted in multiple directions
    for dx in range(-outline_width, outline_width+1):
        for dy in range(-outline_width, outline_width+1):
            if dx != 0 or dy != 0:
                draw.text((x + dx, y + dy), text, font=font, fill=outline_color)
    # Draw inner fill
    draw.text((x, y), text, font=font, fill=fill_color)


def assemble_meme(image_path: str, top_text: str, bottom_text: str, filename="meme_final.jpg") -> str:
    """
    Opens an image, draws Impact-style text on it, and saves it.
    Returns the path to the newly generated meme.
    """
    if not os.path.exists(image_path):
        print("[MemeEngine] Source image not found.")
        return ""
        
    download_font_if_missing()
    
    output_path = os.path.join(TEMP_DIR, filename)
    
    try:
        with Image.open(image_path) as img:
            # Ensure RGB
            img = img.convert("RGB")
            draw = ImageDraw.Draw(img)
            img_width, img_height = img.size
            
            # Dynamically size font (roughly 10% of image height)
            font_size = int(img_height * 0.1)
            try:
                font = ImageFont.truetype(FONT_PATH, font_size)
            except IOError:
                font = ImageFont.load_default()
            
            # Calculate text box size
            def get_text_dimensions(text_string, font):
                # For Pillow 10+
                bbox = font.getbbox(text_string)
                if bbox:
                    return bbox[2] - bbox[0], bbox[3] - bbox[1]
                return 0, 0
                
            tw, th = get_text_dimensions(top_text, font)
            bw, bh = get_text_dimensions(bottom_text, font)
            
            # Center text horizontally, pad vertically
            top_x = (img_width - tw) // 2
            top_y = int(img_height * 0.05)
            
            bottom_x = (img_width - bw) // 2
            bottom_y = img_height - bh - int(img_height * 0.05)
            
            # Draw text
            outline_width = max(2, int(font_size * 0.05))
            _draw_text_with_outline(draw, (top_x, top_y), top_text, font, "white", "black", outline_width)
            _draw_text_with_outline(draw, (bottom_x, bottom_y), bottom_text, font, "white", "black", outline_width)
            
            img.save(output_path, quality=90)
            print(f"[MemeEngine] Meme saved to {output_path}")
            return output_path
            
    except Exception as e:
        print(f"[MemeEngine] Error assembling meme: {e}")
        return ""
