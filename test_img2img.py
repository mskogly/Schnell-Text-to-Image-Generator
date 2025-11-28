import os
from pathlib import Path
from dotenv import load_dotenv
from huggingface_hub import InferenceClient
from PIL import Image

# Load environment variables
load_dotenv()

def test_image_to_image(input_image_path, prompt, output_file="test_img2img_output.jpg"):
    """
    Test image-to-image generation using Hugging Face InferenceClient.
    
    Recommended models that support image-to-image via InferenceClient:
    - black-forest-labs/FLUX.1-Kontext-dev (powerful image editing)
    - kontext-community/relighting-kontext-dev-lora-v3 (image re-lighting)
    
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
    
    # Initialize the client
    client = InferenceClient(token=token)
    
    # List of models to try
    models_to_try = [
        "black-forest-labs/FLUX.1-Kontext-dev",
        "stabilityai/stable-diffusion-xl-refiner-1.0",
        "timbrooks/instruct-pix2pix",
    ]
    
    for model in models_to_try:
        try:
            print(f"\n{'='*60}")
            print(f"Trying model: {model}")
            print(f"{'='*60}")
            
            # Use image_to_image method
            result_image = client.image_to_image(
                image=input_image,
                prompt=prompt,
                model=model
            )
            
            # Save the result
            output_path = Path("output") / f"{model.split('/')[-1]}_{output_file}"
            output_path.parent.mkdir(exist_ok=True)
            
            result_image.save(output_path, "JPEG", quality=95)
            print(f"\n✓ SUCCESS with {model}!")
            print(f"Image saved to: {output_path}")
            print(f"Output image size: {result_image.size}")
            
            return output_path
            
        except Exception as e:
            print(f"\n✗ Failed with {model}")
            print(f"Error: {repr(e)}")
            print("Trying next model...")
            continue
    
    print("\n" + "="*60)
    print("All models failed. This might mean:")
    print("1. These models require a Pro subscription")
    print("2. The models are not available on the free tier")
    print("3. Image-to-image might not be widely supported yet")
    print("="*60)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test image-to-image generation via InferenceClient")
    parser.add_argument("input_image", type=str, help="Path to input image (e.g., your face photo)")
    parser.add_argument("--prompt", type=str, 
                       default="A human and a robot paint a mural together. In the style of a 1900 century realism painting",
                       help="Text prompt for generation")
    parser.add_argument("--output", type=str, default="test_output.jpg", 
                       help="Output filename")
    
    args = parser.parse_args()
    
    test_image_to_image(args.input_image, args.prompt, args.output)
