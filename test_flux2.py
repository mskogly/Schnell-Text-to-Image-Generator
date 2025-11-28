import os
from pathlib import Path
from dotenv import load_dotenv
from huggingface_hub import InferenceClient
from PIL import Image

# Load environment variables
load_dotenv()

def test_flux2_models(input_image_path, prompt, output_file="test_flux2_output.jpg"):
    """
    Test FLUX 2 models using Hugging Face InferenceClient.
    
    FLUX 2 was recently released and may have better image-to-image support.
    
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
    
    # List of FLUX 2 and related models to try
    models_to_try = [
        # FLUX 2 models
        "black-forest-labs/FLUX.2-dev",
        "black-forest-labs/FLUX.1-dev",
        
        # Other potentially free image-to-image models
        "stabilityai/stable-diffusion-2-1",
        "runwayml/stable-diffusion-v1-5",
        "prompthero/openjourney",
    ]
    
    for model in models_to_try:
        try:
            print(f"\n{'='*60}")
            print(f"Trying model: {model}")
            print(f"{'='*60}")
            
            # Try image_to_image first
            try:
                print("Attempting image-to-image...")
                result_image = client.image_to_image(
                    image=input_image,
                    prompt=prompt,
                    model=model
                )
                
                # Save the result
                output_path = Path("output") / f"{model.split('/')[-1]}_{output_file}"
                output_path.parent.mkdir(exist_ok=True)
                
                result_image.save(output_path, "JPEG", quality=95)
                print(f"\n✓ SUCCESS with image-to-image on {model}!")
                print(f"Image saved to: {output_path}")
                print(f"Output image size: {result_image.size}")
                
                return output_path
                
            except Exception as e1:
                print(f"Image-to-image failed: {repr(e1)}")
                print("Trying text-to-image as fallback...")
                
                # Fallback to text-to-image
                result_image = client.text_to_image(
                    prompt=prompt,
                    model=model
                )
                
                # Save the result
                output_path = Path("output") / f"{model.split('/')[-1]}_text2img_{output_file}"
                output_path.parent.mkdir(exist_ok=True)
                
                result_image.save(output_path, "JPEG", quality=95)
                print(f"\n✓ SUCCESS with text-to-image on {model}!")
                print(f"Image saved to: {output_path}")
                print(f"Output image size: {result_image.size}")
                print("Note: This used text-to-image, not your input image")
                
                return output_path
            
        except Exception as e:
            print(f"\n✗ Failed with {model}")
            print(f"Error: {repr(e)}")
            print("Trying next model...")
            continue
    
    print("\n" + "="*60)
    print("All models failed. Summary:")
    print("1. FLUX 2 models may require PRO subscription")
    print("2. Image-to-image is not widely available on free tier")
    print("3. Consider using text-to-image with detailed descriptions")
    print("="*60)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test FLUX 2 and other models for image-to-image")
    parser.add_argument("input_image", type=str, help="Path to input image (e.g., your face photo)")
    parser.add_argument("--prompt", type=str, 
                       default="A human and a robot paint a mural together. In the style of a 1900 century realism painting",
                       help="Text prompt for generation")
    parser.add_argument("--output", type=str, default="test_output.jpg", 
                       help="Output filename")
    
    args = parser.parse_args()
    
    test_flux2_models(args.input_image, args.prompt, args.output)
