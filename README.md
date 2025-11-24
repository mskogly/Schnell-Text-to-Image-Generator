# Text-to-Image Generator

This project provides a Python script to generate images from text prompts using the Hugging Face Inference API. It leverages the modern `black-forest-labs/FLUX.1-schnell` model for high-quality, fast image generation without requiring a local GPU.

## Features

*   **Serverless Inference:** Uses Hugging Face's Inference API, so no heavy local hardware is required.
*   **High Quality:** Defaults to the `black-forest-labs/FLUX.1-schnell` model.
*   **Configurable Resolution:** Default resolution is set to **1344x768** (Landscape), but can be customized via command-line arguments.
*   **Adjustable Quality:** Control the number of inference steps (default: 4, higher = better quality but slower).
*   **Metadata Storage:** Automatically saves generation parameters as JSON files alongside images.
*   **Secure:** Uses environment variables for API token management.
*   **Web Interface:** Optional Flask-based web UI for easy image generation.

## Prerequisites

*   Python 3.x
*   A Hugging Face account and API Token (Read access).

## Setup

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/mskogly/Schnell-Text-to-Image-Generator.git
    cd Schnell-Text-to-Image-Generator
    ```

2.  **Environment Setup:**
    The project is designed to run in a virtual environment.
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies:**
    ```bash
    pip install --upgrade pip
    pip install -r requirements.txt
    ```

4.  **Configuration:**
    Copy the example environment file and add your Hugging Face token:
    ```bash
    cp .env.example .env
    # Edit .env and replace 'your_huggingface_token_here' with your actual token
    ```
    
    Get your token from [Hugging Face Settings](https://huggingface.co/settings/tokens).

## Usage

### Basic Usage
Generate an image with the default settings (1344x768). The image will be automatically saved to the `output/` folder with a timestamp and sanitized prompt as the filename:

```bash
./venv/bin/python generate_image.py "A futuristic city skyline at sunset"
# Output: output/2025-11-24_12-10-53_A_futuristic_city_skyline_at_sunset.png
```

### Custom Output Filename
Specify where to save the generated image:

```bash
./venv/bin/python generate_image.py "A cute robot cat" --output robot_cat.png
```

### Custom Resolution
Override the default resolution. Note that `FLUX.1-schnell` works best with dimensions that are multiples of 32.

**Square (1024x1024):**
```bash
./venv/bin/python generate_image.py "Abstract art" --width 1024 --height 1024
```

**Portrait (768x1344):**
```bash
./venv/bin/python generate_image.py "A tall cyberpunk tower" --width 768 --height 1344
```

### Adjusting Quality (Inference Steps)
Control the number of denoising steps. More steps = higher quality but slower generation:

```bash
# Fast (default)
./venv/bin/python generate_image.py "A landscape" --steps 4

# Better quality
./venv/bin/python generate_image.py "A landscape" --steps 8

# High quality (slower)
./venv/bin/python generate_image.py "A landscape" --steps 20
```

### Reproducible Results (Seed Control)
By default, each generation uses a random seed, so the same prompt will produce different images. You can specify a seed for reproducibility:

```bash
# Random seed (default - different each time)
./venv/bin/python generate_image.py "A cat"

# Specific seed (reproducible)
./venv/bin/python generate_image.py "A cat" --seed 12345

# Use the seed from a previous generation (found in the JSON file)
./venv/bin/python generate_image.py "A cat" --seed 1760741204
```

### Metadata Files
Each generated image has a corresponding `.json` file with the same name containing:
- Prompt
- Model name
- Resolution (width/height)
- Inference steps
- **Seed** (for reproducibility)
- Format
- Timestamp

Example: `2025-11-24_18-06-34_A_mountain_landscape.json`
```json
{
  "prompt": "A mountain landscape",
  "width": 1344,
  "height": 768,
  "format": "jpg",
  "num_inference_steps": 4,
  "seed": 1760741204,
  "model": "black-forest-labs/FLUX.1-schnell",
  "timestamp": "2025-11-24T18:06:37.504815",
  "filename": "2025-11-24_18-06-34_A_mountain_landscape.jpg"
}
```

## Troubleshooting

*   **404/410 Errors:** If you encounter these, it usually means the specific model endpoint is temporarily unavailable or has moved. The script is currently configured to use `black-forest-labs/FLUX.1-schnell` which is supported on the router.
*   **Authentication Errors:** Ensure your `HF_TOKEN` is correctly set in the `.env` file and has valid permissions.

## Web Interface

1.  Install the Flask dependency (you may already have the virtual environment active):

    ```bash
    pip install flask
    ```

2.  Run the Flask server (it loads the same `.env` file, so your `HF_TOKEN` is already read):

    ```bash
    python web_app.py
    ```

3.  Open `http://localhost:5000` in your browser. The web interface allows you to:
    - Enter a prompt
    - Adjust resolution (width/height)
    - Control inference steps for quality
    - Choose output format (JPG/PNG)
    - View generated images with their metadata displayed below
