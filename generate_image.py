import os
import argparse
import re
import json
import random
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

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

def generate_image(prompt, output_file=None, width=1344, height=768, format="jpg", num_inference_steps=4, seed=None):
    token = os.getenv("HF_TOKEN")
    if not token:
        raise ValueError("HF_TOKEN not found in environment variables. Please check your .env file.")

    print(f"Generating image for prompt: '{prompt}'")
    print(f"Resolution: {width}x{height}")
    print(f"Inference steps: {num_inference_steps}")
    
    # Generate random seed if not provided
    if seed is None:
        seed = random.randint(0, 2**32 - 1)
    print(f"Seed: {seed}")
    
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
    
    # Initialize the client
    client = InferenceClient(token=token)
    
    try:
        # FLUX.1-schnell is a good candidate for a modern default
        model = "black-forest-labs/FLUX.1-schnell" 
        print(f"Using model: {model}")
        
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
            # Convert RGBA to RGB for JPG (JPG doesn't support transparency)
            if image.mode == "RGBA":
                rgb_image = image.convert("RGB")
                rgb_image.save(output_file, "JPEG", quality=95)
            else:
                image.save(output_file, "JPEG", quality=95)
        else:
            image.save(output_file)
        print(f"Image saved to {output_file}")
        
        # Save metadata as JSON
        metadata = {
            "prompt": prompt,
            "width": width,
            "height": height,
            "format": format,
            "num_inference_steps": num_inference_steps,
            "seed": seed,
            "model": model,
            "timestamp": datetime.now().isoformat(),
            "filename": str(output_file.name)
        }
        
        metadata_file = output_file.with_suffix('.json')
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        print(f"Metadata saved to {metadata_file}")
        
    except Exception as e:
        print(f"Error generating image: {repr(e)}")

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
