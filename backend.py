import subprocess
import os
import zipfile
import requests
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# === Setup fonts ===
# Download the font ZIP file from Google Drive
url = "https://drive.google.com/uc?export=download&id=1nTlvvCmfyxniWnQRpIg4EC6wbUk7_Fwb"
response = requests.get(url)
with open("JetBrains_Mono.zip", "wb") as f:
    f.write(response.content)

# Unzip font
os.makedirs("fonts", exist_ok=True)
with zipfile.ZipFile("JetBrains_Mono.zip", "r") as zip_ref:
    zip_ref.extractall("fonts")

# === App Config ===
from flask import Flask, request, send_file, jsonify
from PIL import Image, ImageDraw, ImageFont
import re, time

FONT_PATH = "fonts/JetBrainsMono-Italic-VariableFont_wght.ttf"
IMG_PATH = "poetry.png"
ACCESS_TOKEN = "EAAIpLZBuOm60BOZBFgq4ZBZAiAWZAq4rznOhUJyRMm9c2r4HCHDIP15l2NDWLlYfB6un5oYfGn4Ow3DRi5SULsThYMtoNLtcmcZA0DAXYwY9DwsB9Ygrkrg2o8KcZCxElT8ZAiS6kzSBDZAVzKAxoxbEdhKN2bNNBrH3gbPaCQQ4r19w9Y81E6IIcijTNyqxq"
IG_USER_ID = "17841451784404391"
CAPTION = "Code is 😊\n\n\n#poetic_coder #devlife #ai #coding"

# Get public URL from environment (set this on Render)
PUBLIC_URL = os.environ.get("PUBLIC_URL", "http://localhost:10000")

# === Code coloring ===
def style_code_line(code):
    token_pattern = r'"[^"]*"|\'[^\']*\'|\w+|[^\w\s]'
    tokens = re.findall(token_pattern, code)
    parts = []
    keywords = {'if', 'else', 'return', 'function', 'for', 'while', 'const', 'let', 'var'}
    for i, token in enumerate(tokens):
        if token in keywords:
            parts.append((token, "#8be9fd"))  # blue
        elif token == '.':
            parts.append((token, "#ff79c6"))  # pink dot
        elif i > 0 and tokens[i-1] == '.':
            parts.append((token, "#f1fa8c"))  # yellow-green
        elif token.startswith('"') or token.startswith("'"):
            parts.append((token, "#50fa7b"))  # green string
        elif re.match(r'^\d+$', token):
            parts.append((token, "#bd93f9"))  # purple number
        elif token in {'(', ')', ';', '=', '=>', ','}:
            parts.append((token, "#ffffff"))  # white punctuation
        else:
            parts.append((token, "#ff79c6"))  # default
    return parts

# === Image generation ===
def draw_code_line(draw, x, y, parts, font):
    for text, color in parts:
        draw.text((x, y), text, font=font, fill=color)
        x += draw.textlength(text, font=font)

def generate_poetry_image(line1, line2, line3, output_path=IMG_PATH):
    width, height = 1080, 1080
    img = Image.new('RGB', (width, height), color=(40, 42, 54))
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(FONT_PATH, 38)
    code_lines = [
        style_code_line(line1),
        style_code_line(line2) if line2 else [],
        style_code_line(line3) if line3 else []
    ]
    spacing, start_y, x_start = 70, 280, 60
    for i, parts in enumerate(code_lines):
        if not parts:
            continue
        y = start_y + i * spacing
        draw_code_line(draw, x_start, y, parts, font)
    wm = "#poetic_coder"
    wm_font = ImageFont.truetype(FONT_PATH, 30)
    draw.text((width - draw.textlength(wm, wm_font) - 30, height - 90), wm, font=wm_font, fill=(200, 200, 200))
    img.save(output_path)

# === Instagram Posting ===
def post_to_instagram(image_url):
    creation_resp = requests.post(
        f"https://graph.facebook.com/v19.0/{IG_USER_ID}/media",
        data={'image_url': image_url, 'caption': CAPTION, 'access_token': ACCESS_TOKEN}
    )
    if creation_resp.status_code != 200:
        return f"Media creation failed: {creation_resp.json()}"
    creation_id = creation_resp.json().get("id")
    publish_resp = requests.post(
        f"https://graph.facebook.com/v19.0/{IG_USER_ID}/media_publish",
        data={'creation_id': creation_id, 'access_token': ACCESS_TOKEN}
    )
    return "🎉 Posted!" if publish_resp.status_code == 200 else f"Publish failed: {publish_resp.json()}"

# === Flask app ===
app = Flask(__name__)
CORS(app, origins=["http://localhost:5173", "*"])  # Allow all for testing

@app.route("/poetry", methods=["POST", "OPTIONS"])
def poetry_api():
    if request.method == "OPTIONS":
        return "", 200
    data = request.get_json()
    l1 = data.get("line1", "")
    l2 = data.get("line2", "")
    l3 = data.get("line3", "")
    generate_poetry_image(l1, l2, l3)
    time.sleep(1)  # delay for image write
    image_url = f"{PUBLIC_URL}/poetry.png"
    result = post_to_instagram(image_url)
    return jsonify({"image_url": image_url, "status": result})

@app.route("/poetry.png")
def serve_image():
    return send_file(IMG_PATH, mimetype='image/png')

# === Run ===
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
