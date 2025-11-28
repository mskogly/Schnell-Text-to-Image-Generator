import os
from pathlib import Path
from dotenv import load_dotenv
from huggingface_hub import InferenceClient, HfApi
import json

# Load environment variables
load_dotenv()

def discover_and_test_all_text_to_image():
    """
    Discover ALL text-to-image models and test them on free tier.
    This will take a while but gives comprehensive results.
    """
    token = os.getenv("HF_TOKEN")
    if not token:
        raise ValueError("HF_TOKEN required")
    
    api = HfApi(token=token)
    client = InferenceClient(token=token)
    
    print(f"\n{'='*70}")
    print(f"DISCOVERING ALL TEXT-TO-IMAGE MODELS")
    print(f"{'='*70}\n")
    
    # Get many text-to-image models
    models = list(api.list_models(
        filter="text-to-image",
        sort="downloads",
        direction=-1,
        limit=50  # Test top 50 models
    ))
    
    print(f"Found {len(models)} models to test\n")
    
    results = []
    working_count = 0
    
    for i, model in enumerate(models, 1):
        model_id = model.id
        print(f"[{i}/{len(models)}] Testing: {model_id}")
        
        try:
            # Quick test with simple prompt
            result = client.text_to_image(
                "a simple test",
                model=model_id
            )
            
            print(f"  ✅ WORKS!")
            working_count += 1
            
            results.append({
                'model': model_id,
                'works': True,
                'downloads': getattr(model, 'downloads', 0),
                'likes': getattr(model, 'likes', 0),
            })
            
        except Exception as e:
            error_msg = str(e)
            is_payment_error = '402' in error_msg or 'Payment Required' in error_msg
            
            if is_payment_error:
                print(f"  💰 Requires PRO")
            else:
                # Don't print full error, just mark as failed
                print(f"  ❌ Failed")
            
            results.append({
                'model': model_id,
                'works': False,
                'requires_pro': is_payment_error,
                'error': error_msg[:100],
                'downloads': getattr(model, 'downloads', 0),
                'likes': getattr(model, 'likes', 0),
            })
    
    # Save results
    output_file = Path("output") / "comprehensive_model_test.json"
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n{'='*70}")
    print(f"RESULTS")
    print(f"{'='*70}\n")
    print(f"Total models tested: {len(results)}")
    print(f"Working on free tier: {working_count}")
    print(f"Requiring PRO: {sum(1 for r in results if not r['works'] and r.get('requires_pro'))}")
    print(f"Other failures: {sum(1 for r in results if not r['works'] and not r.get('requires_pro'))}")
    print(f"\nResults saved to: {output_file}\n")
    
    # Show working models
    working_models = [r for r in results if r['works']]
    if working_models:
        print(f"{'='*70}")
        print(f"FREE TIER MODELS ({len(working_models)}):")
        print(f"{'='*70}\n")
        
        # Sort by downloads
        working_models.sort(key=lambda x: x['downloads'], reverse=True)
        
        for r in working_models:
            print(f"✅ {r['model']}")
            print(f"   Downloads: {r['downloads']:,} | Likes: {r['likes']}")
    
    return results


if __name__ == "__main__":
    discover_and_test_all_text_to_image()
