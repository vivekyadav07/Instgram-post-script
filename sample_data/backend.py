from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from pyngrok import ngrok
from PIL import Image, ImageDraw, ImageFont
import zipfile, os, re, requests

# Setup
app = Flask(__name__)
CORS(app)

# Config
IMG_PATH = "poetry.png"
FONT_PATH = "fonts/JetBrainsMono-Italic-VariableFont_wght.ttf"
ACCESS_TOKEN = 'EAAIpLZBuOm60BOZBFgq4ZBZAiAWZAq4rznOhUJyRMm9c2r4HCHDIP15l2NDWLlYfB6un5oYfGn4Ow3DRi5SULsThYMtoNLtcmcZA0DAXYwY9DwsB9Ygrkrg2o8KcZCxElT8ZAiS6kzSBDZAVzKAxoxbEdhKN2bNNBrH3gbPaCQQ4r19w9Y81E6IIcijTNyqxq'
IG_USER_ID = '17841451784404391'
CAPTION = "Code is interning 😊 #codepoetry #dev"

# Download font
def setup_fonts():
    if not os.path.exists("fonts"):
        os.makedirs("fonts")
    if not os.path.exists(FONT_PATH):
        import gdown
        file_id = "1nTlvvCmfyxniWnQRpIg4EC6wbUk7_Fwb"
        gdown.download(f"https://drive.google.com/uc?id={file_id}", "JetBrains_Mono.zip", quiet=False)
        with zipfile.ZipFile("JetBrains_Mono.zip", 'r') as zip_ref:
            zip_ref.extractall("fonts")

# Style function
def style_code_line(code):
    parts = []
    token_pattern = r'"[^"]*"|\'[^\']*\'|\w+|[^\w\s]'
    tokens = re.findall(token_pattern, code)
    keywords = {'if', 'else', 'return', 'function', 'for', 'while', 'const', 'let', 'var'}
    for i, token in enumerate(tokens):
        if token in keywords:
            parts.append((token, "#8be9fd"))
        elif token == '.':
            parts.append((token, "#ff79c6"))
        elif i > 0 and tokens[i-1] == '.':
            parts.append((token, "#f1fa8c"))
        elif token in {'(', ')', ';', '=', '=>', ','}:
            parts.append((token, "#ffffff"))
        elif token.startswith('"') or token.startswith("'"):
            parts.append((token, "#50fa7b"))
        elif re.match(r'^\d+$', token):
            parts.append((token, "#bd93f9"))
        else:
            parts.append((token, "#ff79c6"))
    return parts

# Draw function
def draw_code_line(draw, x, y, parts, font):
    for text, color in parts:
        draw.text((x, y), text, font=font, fill=color)
        x += draw.textlength(text, font=font)

# Image generator
def generate_poetry_image(line1, line2, line3):
    width, height = 1080, 1080
    img = Image.new('RGB', (width, height), color=(40, 42, 54))
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(FONT_PATH, 38)
    lines = [style_code_line(line1), style_code_line(line2), style_code_line(line3)]
    for i, parts in enumerate(lines):
        y = 280 + i * 70
        draw_code_line(draw, 60, y, parts, font)
    draw.text((width - 250, height - 90), "#poetic_coder", font=ImageFont.truetype(FONT_PATH, 30), fill=(200,200,200))
    img.save(IMG_PATH)

# Instagram API
def post_to_instagram(image_url, caption):
    create_url = f"https://graph.facebook.com/v19.0/{IG_USER_ID}/media"
    publish_url = f"https://graph.facebook.com/v19.0/{IG_USER_ID}/media_publish"
    creation = requests.post(create_url, data={'image_url': image_url, 'caption': caption, 'access_token': ACCESS_TOKEN})
    creation_id = creation.json().get("id")
    publish = requests.post(publish_url, data={'creation_id': creation_id, 'access_token': ACCESS_TOKEN})
    return publish.ok

# API route
@app.route("/generate_post", methods=["POST"])
def handle_request():
    data = request.json
    parts = [p.strip() for p in data.get("lines", "").split(';') if p.strip()]
    generate_poetry_image(
        parts[0]+';' if len(parts) > 0 else '',
        parts[1]+';' if len(parts) > 1 else '',
        parts[2] if len(parts) > 2 else ''
    )
    image_url = public_url + "/poetry.png"
    post_to_instagram(image_url, CAPTION)
    return jsonify({"status": "success", "image_url": image_url})

@app.route("/poetry.png")
def serve_image():
    return send_file(IMG_PATH, mimetype="image/png")

# Start server
if __name__ == "__main__":
    setup_fonts()
    public_url = ngrok.connect(5000).public_url
    print("🚀 API Live at:", public_url)
    app.run(port=5000)
