import os
from pathlib import Path
from dotenv import load_dotenv
from huggingface_hub import InferenceClient
from PIL import Image

# Load environment variables
load_dotenv()

def test_text_to_image_models(prompt="A human and a robot paint a mural together. In the style of a 1900 century realism painting"):
    """
    Test popular text-to-image models on the free tier.
    """
    token = os.getenv("HF_TOKEN")
    if not token:
        raise ValueError("HF_TOKEN required for testing")
    
    client = InferenceClient(token=token)
    
    # Popular text-to-image models from discovery
    models_to_test = [
        "black-forest-labs/FLUX.1-schnell",  # Current model
        "black-forest-labs/FLUX.1-dev",      # Better quality
        "stabilityai/stable-diffusion-xl-base-1.0",
        "stable-diffusion-v1-5/stable-diffusion-v1-5",
        "stabilityai/sd-turbo",
        "stabilityai/sdxl-turbo",
        "lightx2v/Qwen-Image-Lightning",
        "Qwen/Qwen-Image",
    ]
    
    print(f"\n{'='*70}")
    print(f"TESTING TEXT-TO-IMAGE MODELS ON FREE TIER")
    print(f"{'='*70}")
    print(f"Prompt: '{prompt}'")
    print(f"{'='*70}\n")
    
    results = []
    
    for model_id in models_to_test:
        print(f"Testing: {model_id}")
        
        try:
            # Try text-to-image
            result = client.text_to_image(
                prompt,
                model=model_id
            )
            
            # Save the result
            output_path = Path("output") / f"test_{model_id.replace('/', '_')}.jpg"
            output_path.parent.mkdir(exist_ok=True)
            result.save(output_path, "JPEG", quality=95)
            
            print(f"  ✅ SUCCESS - Image saved to {output_path.name}")
            print(f"     Size: {result.size}")
            
            results.append({
                'model': model_id,
                'works': True,
                'output': str(output_path),
                'size': result.size,
                'error': None
            })
            
        except Exception as e:
            error_msg = str(e)
            is_payment_error = '402' in error_msg or 'Payment Required' in error_msg
            
            if is_payment_error:
                print(f"  ❌ REQUIRES PRO")
            else:
                print(f"  ⚠️  ERROR - {error_msg[:100]}")
            
            results.append({
                'model': model_id,
                'works': False,
                'error': error_msg[:200],
                'requires_pro': is_payment_error
            })
        
        print()
    
    # Save test results
    results_file = Path("output") / "text_to_image_test_results.json"
    import json
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"{'='*70}")
    print(f"Test results saved to: {results_file}")
    print(f"{'='*70}\n")
    
    # Summary
    working_models = [r for r in results if r['works']]
    print(f"\n{'='*70}")
    print(f"SUMMARY: {len(working_models)}/{len(results)} models work on free tier")
    print(f"{'='*70}\n")
    
    if working_models:
        print("✅ Working models:")
        for r in working_models:
            print(f"   • {r['model']}")
            print(f"     Output: {r['output']}")
    
    pro_models = [r for r in results if not r['works'] and r.get('requires_pro')]
    if pro_models:
        print(f"\n💰 Models requiring PRO ({len(pro_models)}):")
        for r in pro_models:
            print(f"   • {r['model']}")
    
    return results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test text-to-image models on free tier")
    parser.add_argument("--prompt", type=str, 
                       default="A human and a robot paint a mural together. In the style of a 1900 century realism painting",
                       help="Text prompt for generation")
    
    args = parser.parse_args()
    
    test_text_to_image_models(args.prompt)
