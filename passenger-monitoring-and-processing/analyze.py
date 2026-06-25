import base64
import json
import sys
import requests
from PIL import Image
from io import BytesIO

def analyze_bag(image_path):
    # Convert image to JPEG in memory to ensure correct format
    img = Image.open(image_path).convert("RGB")
    buf = BytesIO()
    img.save(buf, format="JPEG")
    image_data = base64.b64encode(buf.getvalue()).decode()

    prompt = """
    Analyze this bag and return ONLY a JSON object with these fields, no other text:
    {
      "primary_colour": "main colour of the bag",
      "shell_type": "hard or soft",
      "size_class": "cabin, medium, or large",
      "wheel_type": "2-wheel, 4-wheel spinner, or none",
      "distinctive_features": ["any stickers, damage, logos, etc"]
    }
    """

    response = requests.post("http://localhost:11434/api/generate", json={
        "model": "llava",
        "prompt": prompt,
        "images": [image_data],
        "stream": False
    })

    data = response.json()

    if "error" in data:
        print("Error from Ollama:", data["error"])
        return

    raw = data.get("response", "").strip()
    raw = raw.replace("```json", "").replace("```", "").strip()
    descriptors = json.loads(raw)

    print("\n✓ Bag analysed!\n")
    for key, value in descriptors.items():
        print(f"  {key}: {value}")

    return descriptors

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 analyze.py path/to/bag.jpg")
    else:
        analyze_bag(sys.argv[1])
