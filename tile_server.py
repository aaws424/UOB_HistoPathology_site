import os
import sys
from flask import Flask, send_file, make_response, abort
from flask_cors import CORS
import io

# Handle OpenSlide DLL path on Windows
try:
    dll_path = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Packages/PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0/LocalCache/local-packages/Python313/site-packages/openslide_bin')
    if os.path.exists(dll_path):
        os.add_dll_directory(dll_path)
except Exception as e:
    print(f"Warning: Could not add DLL directory: {e}")

import openslide
from openslide.deepzoom import DeepZoomGenerator

app = Flask(__name__)
CORS(app)

SLIDE_DIR = os.path.join(os.path.dirname(__file__), 'slides')

# Cache for loaded slides to avoid re-opening
slide_cache = {}

def get_slide_generator(slide_name):
    if slide_name in slide_cache:
        return slide_cache[slide_name]
    
    slide_path = os.path.join(SLIDE_DIR, slide_name)
    if not os.path.exists(slide_path):
        # Check with common extensions if not provided
        for ext in ['.tif', '.tiff', '.svs', '.ndpi', '.btif']:
            if os.path.exists(slide_path + ext):
                slide_path += ext
                break
        else:
            return None
            
    slide = openslide.OpenSlide(slide_path)
    # tile_size=254, overlap=1 is typical for DeepZoom
    generator = DeepZoomGenerator(slide, tile_size=254, overlap=1, limit_bounds=False)
    slide_cache[slide_name] = generator
    return generator

@app.route('/dzi/<slide_name>.dzi')
def get_dzi(slide_name):
    generator = get_slide_generator(slide_name)
    if not generator:
        abort(404)
    
    resp = make_response(generator.get_dzi('jpeg'))
    resp.headers['Content-Type'] = 'application/xml'
    return resp

@app.route('/tile/<slide_name>/<int:level>/<int:x>_<int:y>.jpg')
def get_tile(slide_name, level, x, y):
    generator = get_slide_generator(slide_name)
    if not generator:
        abort(404)
    
    try:
        tile = generator.get_tile(level, (x, y))
        buf = io.BytesIO()
        tile.save(buf, 'jpeg', quality=90)
        buf.seek(0)
        return send_file(buf, mimetype='image/jpeg')
    except Exception as e:
        print(f"Error getting tile: {e}")
        abort(500)

@app.route('/info/<slide_name>')
def get_info(slide_name):
    generator = get_slide_generator(slide_name)
    if not generator:
        abort(404)
    
    slide = generator._osr
    return {
        "width": slide.dimensions[0],
        "height": slide.dimensions[1],
        "levels": generator.level_count,
        "properties": dict(slide.properties)
    }

if __name__ == '__main__':
    if not os.path.exists(SLIDE_DIR):
        os.makedirs(SLIDE_DIR)
    print(f"Tile Server running... Slides directory: {SLIDE_DIR}")
    app.run(port=5000, debug=True)
