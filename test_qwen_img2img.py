import os
from pathlib import Path
from dotenv import load_dotenv
from huggingface_hub import InferenceClient
from PIL import Image

# Load environment variables
load_dotenv()

def test_qwen_image_edit(input_image_path, prompt, output_file="test_qwen_output.jpg"):
    """
    Test Qwen image editing models that were discovered as "warm" on HF.
    
    These models should support image-to-image on the free tier.
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
    
    # Qwen models discovered as "warm"
    models_to_try = [
        "Qwen/Qwen-Image-Edit-2509",
        "Qwen/Qwen-Image-Edit",
        "dx8152/Qwen-Edit-2509-Multiple-angles",
        "vafipas663/Qwen-Edit-2509-Upscale-LoRA",
        "lovis93/next-scene-qwen-image-lora-2509",
    ]
    
    for model in models_to_try:
        try:
            print(f"\n{'='*60}")
            print(f"Trying model: {model}")
            print(f"{'='*60}")
            
            # Try image_to_image
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
            error_msg = str(e)
            is_payment_error = '402' in error_msg or 'Payment Required' in error_msg
            
            if is_payment_error:
                print(f"\n✗ REQUIRES PRO: {error_msg[:150]}")
            else:
                print(f"\n✗ Failed: {error_msg[:150]}")
            continue
    
    print("\n" + "="*60)
    print("All Qwen models failed on free tier")
    print("="*60)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Qwen image editing models")
    parser.add_argument("input_image", type=str, help="Path to input image")
    parser.add_argument("--prompt", type=str, 
                       default="A human and a robot paint a mural together. In the style of a 1900 century realism painting",
                       help="Text prompt for generation")
    parser.add_argument("--output", type=str, default="test_output.jpg", 
                       help="Output filename")
    
    args = parser.parse_args()
    
    test_qwen_image_edit(args.input_image, args.prompt, args.output)
