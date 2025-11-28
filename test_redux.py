import os
from pathlib import Path
from dotenv import load_dotenv
from huggingface_hub import InferenceClient
from PIL import Image

# Load environment variables
load_dotenv()

def test_flux_redux(input_image_path, prompt, output_file="test_output.jpg"):
    """
    Test FLUX.1 Redux with an input image.
    
    Args:
        input_image_path: Path to the input image (e.g., a photo of your face)
        prompt: Text prompt to guide the generation
        output_file: Where to save the output
    """
    token = os.getenv("HF_TOKEN")
    if not token:
        raise ValueError("HF_TOKEN not found in environment variables.")
    
    print(f"Loading input image from: {input_image_path}")
    input_image = Image.open(input_image_path)
    print(f"Input image size: {input_image.size}")
    
    print(f"\nPrompt: '{prompt}'")
    print("\nGenerating image with FLUX.1 Redux...")
    
    # Initialize the client
    client = InferenceClient(token=token)
    
    try:
        # Try FLUX.1 Redux dev model
        model = "black-forest-labs/FLUX.1-Redux-dev"
        print(f"Using model: {model}")
        
        # Use image_to_image method
        result_image = client.image_to_image(
            image=input_image,
            prompt=prompt,
            model=model
        )
        
        # Save the result
        output_path = Path("output") / output_file
        output_path.parent.mkdir(exist_ok=True)
        
        result_image.save(output_path, "JPEG", quality=95)
        print(f"\n✓ Success! Image saved to: {output_path}")
        print(f"Output image size: {result_image.size}")
        
        return output_path
        
    except Exception as e:
        print(f"\n✗ Error: {repr(e)}")
        print("\nThis might mean:")
        print("1. The model doesn't support image_to_image via InferenceClient")
        print("2. You might need to use the diffusers library instead")
        print("3. The model might require different parameters")
        raise

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test FLUX.1 Redux image-to-image generation")
    parser.add_argument("input_image", type=str, help="Path to input image (e.g., your face photo)")
    parser.add_argument("--prompt", type=str, 
                       default="A human and a robot paint a mural together. In the style of a 1900 century realism painting",
                       help="Text prompt for generation")
    parser.add_argument("--output", type=str, default="test_redux_output.jpg", 
                       help="Output filename")
    
    args = parser.parse_args()
    
    test_flux_redux(args.input_image, args.prompt, args.output)
