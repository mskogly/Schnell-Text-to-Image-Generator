import os
from dotenv import load_dotenv
from huggingface_hub import HfApi, InferenceClient
import json
from pathlib import Path

# Load environment variables
load_dotenv()

def discover_image_models():
    """
    Discover image generation models available on Hugging Face free tier.
    
    Filters for:
    - Text-to-image and image-to-image tasks
    - Models with inference API enabled
    - Preferably "warm" models (ready to use)
    """
    token = os.getenv("HF_TOKEN")
    if not token:
        print("Warning: HF_TOKEN not found. Some results may be limited.")
    
    api = HfApi(token=token)
    
    print("=" * 70)
    print("DISCOVERING HUGGING FACE IMAGE GENERATION MODELS")
    print("=" * 70)
    
    tasks_to_check = [
        "text-to-image",
        "image-to-image",
    ]
    
    all_models = {}
    
    for task in tasks_to_check:
        print(f"\n{'='*70}")
        print(f"Task: {task.upper()}")
        print(f"{'='*70}\n")
        
        try:
            # Search for models with this task
            models = api.list_models(
                filter=task,  # Use filter parameter instead of task
                sort="downloads",  # Most popular first
                direction=-1,
                limit=100,  # Get top 100 to find more free options
            )
            
            task_models = []
            
            for model in models:
                model_id = model.id
                
                # Get model info
                try:
                    model_info = api.model_info(model_id)
                    
                    # Check if inference is available
                    inference_status = getattr(model_info, 'inference', None)
                    pipeline_tag = getattr(model_info, 'pipeline_tag', None)
                    
                    # Try to determine if it's available on free tier
                    # Models with "warm" inference status are typically available
                    is_warm = False
                    if hasattr(model_info, 'card_data') and model_info.card_data:
                        inference_info = getattr(model_info.card_data, 'inference', None)
                        if inference_info:
                            is_warm = inference_info == 'warm' or inference_info is True
                    
                    model_data = {
                        'id': model_id,
                        'task': pipeline_tag or task,
                        'downloads': getattr(model_info, 'downloads', 0),
                        'likes': getattr(model_info, 'likes', 0),
                        'inference_status': str(inference_status) if inference_status else 'unknown',
                        'is_warm': is_warm,
                    }
                    
                    task_models.append(model_data)
                    
                    # Print model info
                    status_icon = "🔥" if is_warm else "❄️"
                    print(f"{status_icon} {model_id}")
                    print(f"   Downloads: {model_data['downloads']:,}")
                    print(f"   Likes: {model_data['likes']}")
                    print(f"   Inference: {model_data['inference_status']}")
                    print()
                    
                except Exception as e:
                    print(f"⚠️  Could not get info for {model_id}: {e}")
                    continue
            
            all_models[task] = task_models
            
        except Exception as e:
            print(f"Error searching for {task} models: {e}")
    
    # Save results to JSON
    output_file = Path("output") / "discovered_models.json"
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(all_models, f, indent=2)
    
    print(f"\n{'='*70}")
    print(f"Results saved to: {output_file}")
    print(f"{'='*70}\n")
    
    # Print summary
    print("\nSUMMARY:")
    print("-" * 70)
    for task, models in all_models.items():
        warm_count = sum(1 for m in models if m['is_warm'])
        print(f"{task}: {len(models)} models found ({warm_count} warm)")
    
    return all_models


def test_models_for_free_tier(models_to_test=None):
    """
    Test specific models to see if they work on the free tier.
    
    Args:
        models_to_test: List of model IDs to test, or None to test discovered models
    """
    token = os.getenv("HF_TOKEN")
    if not token:
        raise ValueError("HF_TOKEN required for testing")
    
    client = InferenceClient(token=token)
    
    if models_to_test is None:
        # Load from discovered models
        discovered_file = Path("output") / "discovered_models.json"
        if not discovered_file.exists():
            print("No discovered models found. Run discovery first.")
            return
        
        with open(discovered_file, 'r') as f:
            all_models = json.load(f)
        
        # Get top 5 warm models from each task
        models_to_test = []
        for task, models in all_models.items():
            warm_models = [m for m in models if m.get('is_warm')][:5]
            models_to_test.extend([m['id'] for m in warm_models])
    
    print(f"\n{'='*70}")
    print(f"TESTING {len(models_to_test)} MODELS ON FREE TIER")
    print(f"{'='*70}\n")
    
    results = []
    
    for model_id in models_to_test:
        print(f"Testing: {model_id}")
        
        try:
            # Try text-to-image
            result = client.text_to_image(
                "a simple test image",
                model=model_id
            )
            
            print(f"  ✅ SUCCESS - text-to-image works!")
            results.append({
                'model': model_id,
                'text_to_image': True,
                'error': None
            })
            
        except Exception as e:
            error_msg = str(e)
            is_payment_error = '402' in error_msg or 'Payment Required' in error_msg
            
            if is_payment_error:
                print(f"  ❌ REQUIRES PRO - {error_msg[:100]}")
            else:
                print(f"  ⚠️  ERROR - {error_msg[:100]}")
            
            results.append({
                'model': model_id,
                'text_to_image': False,
                'error': error_msg[:200],
                'requires_pro': is_payment_error
            })
    
    # Save test results
    results_file = Path("output") / "model_test_results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n{'='*70}")
    print(f"Test results saved to: {results_file}")
    print(f"{'='*70}\n")
    
    # Summary
    working_models = [r for r in results if r['text_to_image']]
    print(f"\nWorking models on free tier: {len(working_models)}/{len(results)}")
    for r in working_models:
        print(f"  ✅ {r['model']}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Discover and test Hugging Face image models")
    parser.add_argument("--discover", action="store_true", help="Discover available models")
    parser.add_argument("--test", action="store_true", help="Test discovered models on free tier")
    parser.add_argument("--models", nargs="+", help="Specific models to test")
    
    args = parser.parse_args()
    
    if args.discover or (not args.test and not args.models):
        discover_image_models()
    
    if args.test:
        test_models_for_free_tier(args.models)
