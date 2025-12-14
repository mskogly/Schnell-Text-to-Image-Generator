from datetime import datetime
from pathlib import Path
import json

from flask import Flask, render_template_string, request, send_from_directory, url_for, jsonify

from generate_image import generate_image, sanitize_filename, check_huggingface_status

app = Flask(__name__)

HTML_TEMPLATE = """
<!doctype html>
<title>Text-to-Image</title>
<style>
  body { font-family: system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; margin: 2rem; background: #0e1117; color: #f5f6fb; }
  .container { max-width: 1400px; margin: 0 auto; }
  form { max-width: 640px; margin-bottom: 2rem; }
  label { display: block; margin-bottom: .25rem; font-weight: 500; }
  input, textarea, select { width: 100%; padding: .5rem; margin-bottom: 1rem; border-radius: 6px; border: 1px solid #333; background: #141922; color: inherit; font-family: inherit; }
  button { padding: .75rem 1.5rem; border: none; border-radius: 6px; background: #0066ff; color: #fff; cursor: pointer; font-weight: 500; }
  button:hover { background: #0052cc; }
  .result { margin-top: 1rem; padding: 1rem; border-radius: 8px; background: #161b27; }
  .error { color: #ff6b6b; }
  #model-info { transition: opacity 0.3s; }
  .metadata { background: #1a1f2e; padding: 1rem; border-radius: 6px; margin-top: 1rem; font-family: 'Courier New', monospace; font-size: 0.9em; }
  .metadata dt { font-weight: bold; color: #8b92a8; margin-top: 0.5rem; }
  .metadata dd { margin-left: 1rem; color: #d4d7e0; }
  
  /* Gallery styles */
  .gallery-header { margin-top: 3rem; margin-bottom: 1rem; border-top: 2px solid #333; padding-top: 2rem; }
  .gallery { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1.5rem; margin-top: 1rem; }
  .gallery-item { background: #161b27; border-radius: 8px; overflow: hidden; transition: transform 0.2s; }
  .gallery-item:hover { transform: translateY(-4px); }
  .gallery-item img { width: 100%; height: 200px; object-fit: cover; display: block; }
  .gallery-info { padding: 1rem; }
  .gallery-prompt { font-size: 0.9em; margin-bottom: 0.5rem; line-height: 1.4; color: #d4d7e0; }
  .gallery-meta { font-size: 0.75em; color: #8b92a8; }
  .gallery-meta span { display: inline-block; margin-right: 0.75rem; }
  .gallery-link { color: #0066ff; text-decoration: none; font-size: 0.85em; }
  .gallery-link:hover { text-decoration: underline; }
  .delete-btn { background: #dc3545; color: white; border: none; padding: 0.4rem 0.8rem; border-radius: 4px; cursor: pointer; font-size: 0.85em; margin-left: 0.5rem; }
  .delete-btn:hover { background: #c82333; }
  .gallery-actions { margin-top: 0.5rem; display: flex; align-items: center; }
</style>
<script>
function updateModelInfo() {
  const modelSelect = document.getElementById('model');
  const modelInfo = document.getElementById('model-info');
  const modelName = document.getElementById('model-name');
  
  const modelDescriptions = {
    'black-forest-labs/FLUX.1-schnell': {
      name: 'FLUX.1-schnell',
      description: 'Fast generation (~2-4 steps). Good for quick iterations and testing prompts. May occasionally miss details in complex prompts.'
    },
    'black-forest-labs/FLUX.1-dev': {
      name: 'FLUX.1-dev',
      description: 'Higher quality generation (~50 steps). Better prompt adherence and detail. Takes longer but produces superior results.'
    },
    'dall-e-3': {
      name: 'OpenAI DALL-E 3',
      description: 'High quality generation from OpenAI. Follows complex prompts very well. Requires OpenAI API key.'
    }
  };
  
  const selected = modelDescriptions[modelSelect.value];
  if (selected) {
    modelInfo.style.opacity = '0';
    setTimeout(() => {
      modelName.textContent = selected.name;
      modelInfo.innerHTML = '<strong>' + selected.name + '</strong>: ' + selected.description;
      modelInfo.style.opacity = '1';
    }, 150);
  }
}

function checkStatus() {
  const btn = document.getElementById('status-btn');
  const statusDisplay = document.getElementById('api-status');
  const modelSelect = document.getElementById('model');
  
  if (modelSelect.value === 'dall-e-3') {
     statusDisplay.innerHTML = '<span style="color: #4dabf7">ℹ️ DALL-E 3 is a paid service (OpenAI)</span>';
     return;
  }
  
  btn.disabled = true;
  statusDisplay.innerHTML = 'Checking...';
  
  fetch('/api_status?model=' + encodeURIComponent(modelSelect.value))
    .then(r => r.json())
    .then(data => {
      btn.disabled = false;
      if (data.status === 'available') {
        statusDisplay.innerHTML = '<span style="color: #40c057">🟢 Service Available</span>';
      } else if (data.status === 'limit') {
        statusDisplay.innerHTML = '<span style="color: #ff6b6b">🔴 Rate Limited/Quota Exceeded</span>';
      } else {
        statusDisplay.innerHTML = '<span style="color: #ff6b6b">🔴 Error: ' + data.message + '</span>';
      }
    })
    .catch(e => {
      btn.disabled = false;
      statusDisplay.innerHTML = '<span style="color: #ff6b6b">Error checking status</span>';
    });
}

function deleteImage(filename) {
  if (!confirm('Are you sure you want to delete this image? This will remove both the image and its metadata.')) {
    return;
  }
  
  fetch('/delete/' + encodeURIComponent(filename), {
    method: 'DELETE'
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      // Remove the gallery item from the DOM
      const galleryItem = document.querySelector(`[data-filename="${filename}"]`);
      if (galleryItem) {
        galleryItem.style.opacity = '0';
        setTimeout(() => galleryItem.remove(), 300);
      }
      // Update the count
      const header = document.querySelector('.gallery-header h2');
      const currentCount = parseInt(header.textContent.match(/\d+/)[0]);
      header.textContent = `Recent Generations (${currentCount - 1})`;
    } else {
      alert('Error deleting image: ' + data.error);
    }
  })
  .catch(error => {
    alert('Error deleting image: ' + error);
  });
}
</script>
<div class="container">
  <h1>Text-to-Image Generator</h1>
  <p>Enter a prompt (and optional settings) to generate an image using Hugging Face FLUX.1-schnell. Images and metadata are saved to <code>output/</code>.</p>
  <form method="post">
    <label for="prompt">Prompt</label>
    <textarea id="prompt" name="prompt" rows="3" required>{{ prompt or "A human and a robot paint a mural together. In the style of a 1900 century realism painting" }}</textarea>

    <label for="width">Width</label>
    <input id="width" name="width" type="number" min="256" max="2048" step="32" value="{{ width or 1344 }}">

    <label for="height">Height</label>
    <input id="height" name="height" type="number" min="256" max="2048" step="32" value="{{ height or 768 }}">

    <label for="steps">Inference Steps (higher = better quality, slower)</label>
    <input id="steps" name="steps" type="number" min="1" max="50" value="{{ steps or 4 }}">

    <label for="seed">Seed (leave empty for random)</label>
    <input id="seed" name="seed" type="number" min="0" value="{{ seed or '' }}" placeholder="Random">

    <label for="model">Model</label>
    <select id="model" name="model" onchange="updateModelInfo()">
      <option value="black-forest-labs/FLUX.1-schnell" {% if model == "black-forest-labs/FLUX.1-schnell" %}selected{% endif %}>FLUX.1-schnell (Fast)</option>
      <option value="black-forest-labs/FLUX.1-dev" {% if model == "black-forest-labs/FLUX.1-dev" %}selected{% endif %}>FLUX.1-dev (Quality)</option>
      <option value="dall-e-3" {% if model == "dall-e-3" %}selected{% endif %}>OpenAI DALL-E 3</option>
    </select>
    <div id="model-info" style="margin-top: 0.5rem; padding: 0.75rem; background: #1a1f2e; border-radius: 6px; font-size: 0.9em; color: #d4d7e0;">
      <strong id="model-name">FLUX.1-schnell</strong>: Fast generation (~2-4 steps). Good for quick iterations and testing prompts.
    </div>

    <div style="margin-top: 1rem; padding: 1rem; background: #1a1f2e; border: 1px solid #333; border-radius: 6px;">
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.5rem;">
            <label style="margin:0">API Status Check</label>
            <button type="button" id="status-btn" onclick="checkStatus()" style="padding: 0.25rem 0.5rem; font-size: 0.8em; background: #333;">Check Now</button>
        </div>
        <div id="api-status" style="font-size: 0.9em; min-height: 1.2em; margin-bottom: 1rem;">Click 'Check Now' to probe HuggingFace API</div>
        
        <div style="display: flex; align-items: start; gap: 0.5rem; border-top: 1px solid #333; padding-top: 0.75rem;">
            <input type="checkbox" id="allow_fallback" name="allow_fallback" value="true" style="width: auto; margin-top: 0.25rem;">
            <div>
                <label for="allow_fallback" style="margin-bottom: 0.2rem; display: inline-block;">Allow OpenAI Fallback</label>
                <div style="font-size: 0.8em; color: #8b92a8;">
                    If unchecked, generation will FAIL if Hugging Face is limited/down. <br>
                    Check this if you are willing to pay for DALL-E 3 fallback.
                </div>
            </div>
        </div>
    </div>

    <label for="format">Format</label>
    <select id="format" name="format">
      <option value="jpg" {% if format == "jpg" %}selected{% endif %}>JPEG</option>
      <option value="png" {% if format == "png" %}selected{% endif %}>PNG</option>
    </select>

    <button type="submit">Generate Image</button>
  </form>

  {% if message %}
    <div class="result">
      <p>{{ message }}</p>
      {% if image_url %}
        <p><a href="{{ image_url }}" target="_blank" rel="noreferrer">Open generated image</a></p>
        <p><img src="{{ image_url }}" alt="Generated image" style="max-width:100%; border-radius:8px;"/></p>
        
        {% if metadata %}
        <div class="metadata">
          <h3>Generation Metadata</h3>
          <dl>
            <dt>Prompt:</dt>
            <dd>{{ metadata.prompt }}</dd>
            <dt>Model:</dt>
            <dd>{{ metadata.model }}</dd>
            <dt>Resolution:</dt>
            <dd>{{ metadata.width }}x{{ metadata.height }}</dd>
            <dt>Inference Steps:</dt>
            <dd>{{ metadata.num_inference_steps }}</dd>
            <dt>Seed:</dt>
            <dd>{{ metadata.seed }}</dd>
            <dt>Format:</dt>
            <dd>{{ metadata.format }}</dd>
            <dt>Timestamp:</dt>
            <dd>{{ metadata.timestamp }}</dd>
          </dl>
        </div>
        {% endif %}
      {% endif %}
    </div>
  {% endif %}

  {% if error %}
    <div class="result error">{{ error }}</div>
  {% endif %}

  <div class="gallery-header">
    <h2>Recent Generations ({{ gallery_items|length }})</h2>
  </div>
  
  <div class="gallery">
    {% for item in gallery_items %}
    <div class="gallery-item" data-filename="{{ item.filename }}">
      <a href="{{ item.image_url }}" target="_blank">
        <img src="{{ item.image_url }}" alt="{{ item.metadata.prompt }}" loading="lazy">
      </a>
      <div class="gallery-info">
        <div class="gallery-prompt">{{ item.metadata.prompt }}</div>
        <div class="gallery-meta">
          <span>{{ item.metadata.width }}×{{ item.metadata.height }}</span>
          <span>{{ item.metadata.num_inference_steps }} steps</span>
          <span>{{ item.metadata.format }}</span>
        </div>
        <div class="gallery-actions">
          <a href="{{ item.image_url }}" class="gallery-link" download>Download</a>
          <button class="delete-btn" onclick="deleteImage('{{ item.filename }}')">Delete</button>
        </div>
      </div>
    </div>
    {% endfor %}
  </div>
</div>
"""


def build_output_filename(prompt: str, extension: str) -> Path:
    """Create a timestamped filename based on the prompt."""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    prompt_slug = sanitize_filename(prompt) or "image"
    return Path("output") / f"{timestamp}_{prompt_slug}.{extension}"


def get_gallery_items(limit=50):
    """Get recent generated images with their metadata."""
    output_dir = Path("output")
    if not output_dir.exists():
        return []
    
    items = []
    # Get all JSON metadata files
    json_files = sorted(output_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    
    for json_file in json_files[:limit]:
        try:
            with open(json_file, 'r') as f:
                metadata = json.load(f)
            
            # Check if the corresponding image exists
            image_file = json_file.with_suffix(f".{metadata.get('format', 'jpg')}")
            if image_file.exists():
                items.append({
                    'metadata': metadata,
                    'image_url': url_for('serve_image', filename=image_file.name),
                    'json_url': url_for('serve_image', filename=json_file.name),
                    'filename': image_file.name
                })
        except Exception as e:
            print(f"Error loading {json_file}: {e}")
            continue
    
    return items


@app.route("/", methods=["GET", "POST"])
def index():
    message = None
    image_url = None
    error = None
    metadata = None
    prompt = request.form.get("prompt", "")
    width = request.form.get("width", "1344")
    height = request.form.get("height", "768")
    steps = request.form.get("steps", "4")
    seed_str = request.form.get("seed", "")
    seed = int(seed_str) if seed_str else None
    format_choice = request.form.get("format", "jpg")
    model_choice = request.form.get("model", "black-forest-labs/FLUX.1-schnell")
    allow_fallback = request.form.get("allow_fallback") == "true"

    if request.method == "POST":
        if not prompt.strip():
            error = "Prompt must not be empty."
        else:
            try:
                output_path = build_output_filename(prompt, format_choice)
                output_path.parent.mkdir(exist_ok=True)
                generate_image(
                    prompt=prompt,
                    output_file=output_path,
                    width=int(width),
                    height=int(height),
                    format=format_choice,
                    num_inference_steps=int(steps),
                    seed=seed,
                    model=model_choice,
                    allow_fallback=allow_fallback,
                )
                image_url = url_for("serve_image", filename=output_path.name)
                message = f"Saved to {output_path}"
                
                # Load metadata
                metadata_path = output_path.with_suffix('.json')
                if metadata_path.exists():
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                        
            except Exception as exc:
                error = f"Could not generate image: {exc}"

    # Get gallery items
    gallery_items = get_gallery_items()

    return render_template_string(
        HTML_TEMPLATE,
        prompt=prompt,
        width=width,
        height=height,
        steps=steps,
        seed=seed,
        format=format_choice,
        model=model_choice,
        message=message,
        image_url=image_url,
        metadata=metadata,
        error=error,
        gallery_items=gallery_items,
    )


@app.route("/output/<path:filename>")
def serve_image(filename):
    return send_from_directory("output", filename)


@app.route("/api_status")
def api_status():
    model = request.args.get("model", "black-forest-labs/FLUX.1-schnell")
    result = check_huggingface_status(model)
    return jsonify(result)


@app.route("/delete/<path:filename>", methods=["DELETE"])
def delete_image(filename):
    """Delete an image and its corresponding JSON metadata file."""
    try:
        output_dir = Path("output")
        image_path = output_dir / filename
        
        # Security check: ensure the file is within the output directory
        if not image_path.resolve().is_relative_to(output_dir.resolve()):
            return jsonify({"success": False, "error": "Invalid file path"}), 400
        
        # Check if image exists
        if not image_path.exists():
            return jsonify({"success": False, "error": "Image file not found"}), 404
        
        # Determine the JSON metadata file path
        json_path = image_path.with_suffix('.json')
        
        # Delete the image file
        image_path.unlink()
        
        # Delete the JSON metadata file if it exists
        if json_path.exists():
            json_path.unlink()
        
        return jsonify({"success": True, "message": "Image and metadata deleted successfully"})
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
