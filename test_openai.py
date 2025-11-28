import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from PIL import Image
import io

# Load environment variables
load_dotenv()

def test_openai_image_edit(input_image_path, prompt, output_file="test_openai_output.png"):
    """
    Test OpenAI's image editing API (DALL-E).
    
    Note: OpenAI's image editing requires:
    - An input image
    - A mask (optional - transparent areas will be edited)
    - A prompt describing the desired changes
    
    Args:
        input_image_path: Path to the input image (e.g., a photo of your face)
        prompt: Text prompt to guide the generation
        output_file: Where to save the output
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables. Please add it to your .env file.")
    
    print(f"Loading input image from: {input_image_path}")
    input_image = Image.open(input_image_path)
    print(f"Input image size: {input_image.size}")
    print(f"Input image mode: {input_image.mode}")
    
    # Convert to RGBA if not already (required for editing)
    if input_image.mode != "RGBA":
        print("Converting image to RGBA...")
        input_image = input_image.convert("RGBA")
    
    # Save as PNG (required format for OpenAI)
    temp_input = Path("output") / "temp_input.png"
    temp_input.parent.mkdir(exist_ok=True)
    input_image.save(temp_input, "PNG")
    
    print(f"\nPrompt: '{prompt}'")
    print("\nGenerating edited image with OpenAI DALL-E...")
    
    # Initialize OpenAI client
    client = OpenAI(api_key=api_key)
    
    try:
        # Try image editing (variations endpoint)
        # Note: DALL-E 3 doesn't support edits the same way DALL-E 2 did
        # We'll try the variations endpoint first
        print("\nAttempting image variation...")
        
        with open(temp_input, "rb") as image_file:
            response = client.images.create_variation(
                image=image_file,
                n=1,
                size="1024x1024"
            )
        
        # Get the URL of the generated image
        image_url = response.data[0].url
        print(f"\n✓ Success! Generated image URL: {image_url}")
        
        # Download and save the image
        import requests
        image_data = requests.get(image_url).content
        result_image = Image.open(io.BytesIO(image_data))
        
        output_path = Path("output") / output_file
        result_image.save(output_path, "PNG")
        print(f"Image saved to: {output_path}")
        
        # Clean up temp file
        temp_input.unlink()
        
        return output_path
        
    except Exception as e:
        print(f"\n✗ Error with variations: {repr(e)}")
        print("\nTrying text-to-image generation instead...")
        
        try:
            # Fallback to text-to-image with DALL-E 3
            response = client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                n=1,
            )
            
            image_url = response.data[0].url
            print(f"\n✓ Success with text-to-image! Generated image URL: {image_url}")
            
            # Download and save the image
            import requests
            image_data = requests.get(image_url).content
            result_image = Image.open(io.BytesIO(image_data))
            
            output_path = Path("output") / output_file
            result_image.save(output_path, "PNG")
            print(f"Image saved to: {output_path}")
            
            # Clean up temp file
            if temp_input.exists():
                temp_input.unlink()
            
            return output_path
            
        except Exception as e2:
            print(f"\n✗ Error with text-to-image: {repr(e2)}")
            # Clean up temp file
            if temp_input.exists():
                temp_input.unlink()
            raise

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test OpenAI image editing/generation")
    parser.add_argument("input_image", type=str, help="Path to input image (e.g., your face photo)")
    parser.add_argument("--prompt", type=str, 
                       default="A human and a robot paint a mural together. In the style of a 1900 century realism painting",
                       help="Text prompt for generation")
    parser.add_argument("--output", type=str, default="test_openai_output.png", 
                       help="Output filename")
    
    args = parser.parse_args()
    
    test_openai_image_edit(args.input_image, args.prompt, args.output)
