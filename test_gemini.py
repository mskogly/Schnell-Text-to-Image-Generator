import os
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai
from PIL import Image
import io
import base64

# Load environment variables
load_dotenv()

def test_gemini_image_generation(prompt, output_file="test_gemini_output.png"):
    """
    Test Google Gemini Imagen API for image generation.
    
    Uses Imagen via Gemini API for high-quality image generation.
    Free tier: 1,500 requests/day
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("\n" + "="*70)
        print("SETUP REQUIRED")
        print("="*70)
        print("\nYou need a Google Gemini API key.")
        print("\nSteps to get your API key:")
        print("1. Go to: https://aistudio.google.com/apikey")
        print("2. Click 'Get API key' or 'Create API key'")
        print("3. Copy the API key")
        print("4. Add to your .env file:")
        print("   GEMINI_API_KEY=your-api-key-here")
        print("\n" + "="*70)
        raise ValueError("GEMINI_API_KEY not found in environment variables.")
    
    print(f"\n{'='*70}")
    print(f"TESTING GOOGLE GEMINI IMAGEN")
    print(f"{'='*70}")
    print(f"Prompt: '{prompt}'")
    print(f"{'='*70}\n")
    
    try:
        # Configure the API
        genai.configure(api_key=api_key)
        
        # List available models to see what's available
        print("Checking available models...")
        for model in genai.list_models():
            if 'imagen' in model.name.lower() or 'generateImages' in str(model.supported_generation_methods):
                print(f"  Found: {model.name}")
        
        print("\nAttempting image generation with Gemini...")
        
        # Try using the Gemini model for image generation
        # Note: As of late 2024, Imagen might not be directly available via the free API
        # We'll try the available approach
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        response = model.generate_content(
            f"Generate an image: {prompt}",
            generation_config={
                "temperature": 0.4,
            }
        )
        
        print(f"\nResponse received:")
        print(f"Response text: {response.text if hasattr(response, 'text') else 'No text'}")
        
        # Check if response contains image data
        if hasattr(response, 'parts'):
            for part in response.parts:
                print(f"Part type: {type(part)}")
        
        print(f"\n{'='*70}")
        print("NOTE: Direct Imagen API might require Google Cloud setup")
        print("The free Gemini API may not support image generation yet")
        print(f"{'='*70}\n")
        
        return None
        
    except Exception as e:
        print(f"\n{'='*70}")
        print(f"ERROR")
        print(f"{'='*70}")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print(f"\n{'='*70}")
        print("IMPORTANT: Imagen may require:")
        print("1. Google Cloud Project setup")
        print("2. Vertex AI API enabled")
        print("3. Different authentication method")
        print(f"{'='*70}\n")
        raise


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Google Gemini Imagen")
    parser.add_argument("--prompt", type=str, 
                       default="A human and a robot paint a mural together. In the style of a 1900 century realism painting",
                       help="Text prompt for generation")
    parser.add_argument("--output", type=str, default="test_gemini_output.png", 
                       help="Output filename")
    
    args = parser.parse_args()
    
    test_gemini_image_generation(args.prompt, args.output)
