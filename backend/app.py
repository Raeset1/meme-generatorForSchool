import logging
import os
from datetime import datetime, timezone
from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
from PIL import Image, ImageDraw, ImageFont
import io
import base64
import requests
from elasticsearch import Elasticsearch

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Elasticsearch configuration
es = Elasticsearch([{'host': 'elasticsearch', 'port': 9200}])

@app.route('/upload_images', methods=['POST'])
def upload_images():
    if 'images' not in request.files:
        return jsonify({"error": "No images provided"}), 400

    files = request.files.getlist('images')
    filenames = []
    for file in files:
        filename = file.filename
        file.save(os.path.join(UPLOAD_FOLDER, filename))
        filenames.append(filename)

    return jsonify({"filenames": filenames}), 200

@app.route('/images/<filename>', methods=['GET'])
def get_image(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

def draw_text(draw, text, position, font, max_width, color):
    # Split the text into lines that fit within the max_width
    lines = []
    words = text.split()
    while words:
        line = ''
        while words and draw.textbbox((0, 0), line + words[0], font=font)[2] <= max_width:
            line += (words.pop(0) + ' ')
        lines.append(line)
    
    # Draw each line of text
    y_offset = 0
    for line in lines:
        draw.text((position[0], position[1] + y_offset), line, font=font, fill=color)
        y_offset += font.getsize(line)[1]

@app.route('/generate_meme', methods=['POST'])
def generate_meme():
    data = request.json
    logger.info('Received request to generate meme with data: %s', data)

    if 'filename' not in data or 'text_areas' not in data:
        return jsonify({"error": "No image or text areas provided"}), 400

    filename = data['filename']
    text_areas = data['text_areas']

    if not (1 <= len(text_areas) <= 6):
        return jsonify({"error": "Number of text areas must be between 1 and 6"}), 400

    img_path = os.path.join(UPLOAD_FOLDER, filename)
    img = Image.open(img_path)

    d = ImageDraw.Draw(img)

    width, height = img.size
    max_width = width - 20

    for area in text_areas:
        text = area['text']
        position = (area['x'], area['y'])
        color = area['color']
        font_size = int(area['fontSize'].replace('px', ''))
        try:
            font = ImageFont.truetype("/app/arial.ttf", font_size)
        except IOError:
            font = ImageFont.load_default()
        try:
            draw_text(d, text, position, font, max_width, color)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

    img_io = io.BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)

    # Log the usage
    log_data = {
        "event": "generate_meme",
        "filename": filename,
        "text_areas": text_areas,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    logger.info('Logging data: %s', log_data)
    requests.post('http://logstash:5044', json=log_data)
    es.index(index="meme-logs", body=log_data)

    return send_file(img_io, mimetype='image/png')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)