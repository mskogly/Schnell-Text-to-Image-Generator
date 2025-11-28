import os
from pathlib import Path
from dotenv import load_dotenv
from PIL import Image
import torch

# Load environment variables
load_dotenv()

def test_flux_redux_diffusers(input_image_path, prompt, output_file="test_output.jpg"):
    """
    Test FLUX.1 Redux using the diffusers library.
    
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
    print("\nLoading FLUX.1 Redux pipeline (this may take a moment)...")
    
    try:
        from diffusers import FluxPriorReduxPipeline, FluxPipeline
        
        # Load the Redux pipeline (converts image to embeddings)
        print("Loading Redux pipeline...")
        pipe_prior_redux = FluxPriorReduxPipeline.from_pretrained(
            "black-forest-labs/FLUX.1-Redux-dev",
            torch_dtype=torch.bfloat16,
            token=token
        )
        
        # Load the main FLUX pipeline
        print("Loading FLUX pipeline...")
        pipe = FluxPipeline.from_pretrained(
            "black-forest-labs/FLUX.1-dev",  # Redux works with the dev model
            torch_dtype=torch.bfloat16,
            token=token
        )
        
        # Move to GPU if available
        device = "mps" if torch.backends.mps.is_available() else "cpu"
        print(f"Using device: {device}")
        
        pipe_prior_redux.to(device)
        pipe.to(device)
        
        print("\nGenerating image embeddings from input image...")
        # Generate image embeddings
        pipe_prior_output = pipe_prior_redux(input_image)
        
        print("Generating final image...")
        # Generate the final image
        result_image = pipe(
            guidance_scale=2.5,
            num_inference_steps=50,
            generator=torch.Generator(device).manual_seed(0),
            **pipe_prior_output,
        ).images[0]
        
        # Save the result
        output_path = Path("output") / output_file
        output_path.parent.mkdir(exist_ok=True)
        
        result_image.save(output_path, "JPEG", quality=95)
        print(f"\n✓ Success! Image saved to: {output_path}")
        print(f"Output image size: {result_image.size}")
        
        return output_path
        
    except ImportError as e:
        print(f"\n✗ Import Error: {repr(e)}")
        print("\nYou need to install the diffusers library:")
        print("  pip install diffusers transformers accelerate")
        raise
    except Exception as e:
        print(f"\n✗ Error: {repr(e)}")
        raise

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test FLUX.1 Redux image-to-image generation using diffusers")
    parser.add_argument("input_image", type=str, help="Path to input image (e.g., your face photo)")
    parser.add_argument("--prompt", type=str, 
                       default="A human and a robot paint a mural together. In the style of a 1900 century realism painting",
                       help="Text prompt for generation")
    parser.add_argument("--output", type=str, default="test_redux_output.jpg", 
                       help="Output filename")
    
    args = parser.parse_args()
    
    test_flux_redux_diffusers(args.input_image, args.prompt, args.output)
