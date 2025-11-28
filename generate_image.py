import os
import argparse
import re
import json
import random
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from huggingface_hub import InferenceClient
from PIL import Image

# Load environment variables
load_dotenv()

def sanitize_filename(text, max_length=50):
    """Convert text to a safe filename."""
    # Remove or replace unsafe characters
    safe = re.sub(r'[^\w\s-]', '', text)
    # Replace spaces with underscores
    safe = re.sub(r'[-\s]+', '_', safe)
    # Truncate to max length
    return safe[:max_length].strip('_')

def generate_image(prompt, output_file=None, width=1344, height=768, format="jpg", num_inference_steps=4, seed=None, model="black-forest-labs/FLUX.1-schnell"):
    """
    Generate an image using Hugging Face (primary) or OpenAI DALL-E (fallback).
    
    Tries Hugging Face first, falls back to OpenAI if HF fails due to quota/errors.
    """
    # Generate random seed if not provided
    if seed is None:
        seed = random.randint(0, 2**32 - 1)
    
    # Create output directory
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    # Generate filename if not provided
    if output_file is None:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        prompt_slug = sanitize_filename(prompt)
        ext = format.lower()
        output_file = output_dir / f"{timestamp}_{prompt_slug}.{ext}"
    else:
        output_file = Path(output_file)
    
    print(f"Generating image for prompt: '{prompt}'")
    print(f"Resolution: {width}x{height}")
    print(f"Seed: {seed}")
    
    # Try Hugging Face first (unless DALL-E 3 is explicitly selected)
    hf_token = os.getenv("HF_TOKEN")
    if hf_token and model != "dall-e-3":
        try:
            print(f"[HuggingFace] Attempting with model: {model}")
            print(f"[HuggingFace] Inference steps: {num_inference_steps}")
            
            from huggingface_hub import InferenceClient
            client = InferenceClient(token=hf_token)
            
            image = client.text_to_image(
                prompt, 
                model=model,
                width=width,
                height=height,
                num_inference_steps=num_inference_steps,
                seed=seed
            )
            
            # Save image
            if format.lower() == "jpg":
                if image.mode == "RGBA":
                    rgb_image = image.convert("RGB")
                    rgb_image.save(output_file, "JPEG", quality=95)
                else:
                    image.save(output_file, "JPEG", quality=95)
            else:
                image.save(output_file)
            
            print(f"✓ [HuggingFace] Image saved to {output_file}")
            
            # Save metadata
            metadata = {
                "prompt": prompt,
                "width": width,
                "height": height,
                "format": format,
                "num_inference_steps": num_inference_steps,
                "seed": seed,
                "model": model,
                "service": "huggingface",
                "timestamp": datetime.now().isoformat(),
                "filename": str(output_file.name)
            }
            
            metadata_file = output_file.with_suffix('.json')
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            print(f"✓ [HuggingFace] Metadata saved to {metadata_file}")
            return
            
        except Exception as hf_error:
            error_msg = str(hf_error)
            
            # Check if it's a quota/payment error
            if '402' in error_msg or 'Payment Required' in error_msg or 'exceeded' in error_msg.lower():
                print(f"⚠ [HuggingFace] Quota exceeded or payment required")
                print(f"⚠ [HuggingFace] Falling back to OpenAI...")
            else:
                print(f"⚠ [HuggingFace] Error: {error_msg[:200]}")
                print(f"⚠ [HuggingFace] Falling back to OpenAI...")
    else:
        if model != "dall-e-3":
            print("⚠ [HuggingFace] No HF_TOKEN found, skipping to OpenAI")
    
    # Fallback to OpenAI
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        raise ValueError("Both HuggingFace and OpenAI failed. No OPENAI_API_KEY found in .env file.")
    
    try:
        if model == "dall-e-3":
            print(f"[OpenAI] Explicitly selected DALL-E 3...")
        else:
            print(f"[OpenAI] Fallback: Attempting with DALL-E 3...")
        
        from openai import OpenAI
        import requests
        import io
        
        openai_client = OpenAI(api_key=openai_key)
        
        # DALL-E 3 only supports specific sizes
        dalle_size = "1024x1024"  # Default
        if width == height:
            if width >= 1024:
                dalle_size = "1024x1024"
            else:
                dalle_size = "1024x1024"  # DALL-E 3 minimum
        elif width > height:
            dalle_size = "1792x1024"
        else:
            dalle_size = "1024x1792"
        
        print(f"[OpenAI] Using size: {dalle_size} (DALL-E 3 constraint)")
        
        response = openai_client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size=dalle_size,
            quality="standard",
            n=1,
        )
        
        # Download the image
        image_url = response.data[0].url
        image_data = requests.get(image_url).content
        image = Image.open(io.BytesIO(image_data))
        
        # Resize to requested dimensions if needed
        if image.size != (width, height):
            print(f"[OpenAI] Resizing from {image.size} to {width}x{height}")
            image = image.resize((width, height), Image.Resampling.LANCZOS)
        
        # Save image
        if format.lower() == "jpg":
            if image.mode == "RGBA":
                rgb_image = image.convert("RGB")
                rgb_image.save(output_file, "JPEG", quality=95)
            else:
                image.save(output_file, "JPEG", quality=95)
        else:
            image.save(output_file)
        
        print(f"✓ [OpenAI] Image saved to {output_file}")
        
        # Save metadata
        metadata = {
            "prompt": prompt,
            "width": width,
            "height": height,
            "format": format,
            "seed": seed,
            "model": "dall-e-3",
            "service": "openai",
            "original_size": dalle_size,
            "timestamp": datetime.now().isoformat(),
            "filename": str(output_file.name)
        }
        
        metadata_file = output_file.with_suffix('.json')
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        print(f"✓ [OpenAI] Metadata saved to {metadata_file}")
        
    except Exception as openai_error:
        print(f"✗ [OpenAI] Error: {repr(openai_error)}")
        raise ValueError(f"Both HuggingFace and OpenAI failed. OpenAI error: {str(openai_error)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate an image from text using Hugging Face Inference API.")
    parser.add_argument("prompt", type=str, help="The text prompt for image generation")
    parser.add_argument("--output", type=str, default=None, help="Output filename (default: auto-generated with timestamp and prompt)")
    parser.add_argument("--width", type=int, default=1344, help="Image width (default: 1344)")
    parser.add_argument("--height", type=int, default=768, help="Image height (default: 768)")
    parser.add_argument("--format", type=str, default="jpg", choices=["jpg", "png"], help="Output format (default: jpg)")
    parser.add_argument("--steps", type=int, default=4, help="Number of inference steps (default: 4, higher = better quality but slower)")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility (default: random)")
    
    args = parser.parse_args()
    
    generate_image(args.prompt, args.output, args.width, args.height, args.format, args.steps, args.seed)
