import os
import sys
import shutil
from flask import Flask
import io

# Handle OpenSlide DLL path on Windows (copied from your tile_server.py)
try:
    dll_path = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Packages/PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0/LocalCache/local-packages/Python313/site-packages/openslide_bin')
    if os.path.exists(dll_path):
        os.add_dll_directory(dll_path)
except Exception as e:
    print(f"Warning: Could not add DLL directory: {e}")

import openslide
from openslide.deepzoom import DeepZoomGenerator

# Configuration
SLIDE_DIR = os.path.join(os.path.dirname(__file__), 'slides')
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'docs', 'assets', 'slides')

def convert_slides():
    if not os.path.exists(SLIDE_DIR):
        print(f"Error: Slides directory not found at {SLIDE_DIR}")
        return

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"Created output directory: {OUTPUT_DIR}")

    # Find all slide files
    slide_files = [f for f in os.listdir(SLIDE_DIR) if f.endswith(('.tif', '.tiff', '.svs', '.ndpi', '.btif'))]
    
    if not slide_files:
        print("No slides found in the slides/ directory.")
        return

    print(f"Found {len(slide_files)} slides. Starting conversion...")

    for filename in slide_files:
        slide_path = os.path.join(SLIDE_DIR, filename)
        slide_name = os.path.splitext(filename)[0]
        
        # Output paths
        dzi_output_path = os.path.join(OUTPUT_DIR, f"{slide_name}.dzi")
        files_output_path = os.path.join(OUTPUT_DIR, f"{slide_name}_files")

        print(f"Processing: {filename} -> {slide_name}.dzi")
        
        try:
            slide = openslide.OpenSlide(slide_path)
            # tile_size=254, overlap=1 is typical for DeepZoom
            generator = DeepZoomGenerator(slide, tile_size=254, overlap=1, limit_bounds=False)

            # Save the .dzi XML file (using 'jpg' as the format name)
            with open(dzi_output_path, 'w') as f:
                f.write(generator.get_dzi('jpg'))
            
            # Create the _files directory
            if not os.path.exists(files_output_path):
                os.makedirs(files_output_path)
            
            # Loop through all levels and tiles and save them
            print(f"  Saving tiles (using .jpg extension)...")
            for level in range(generator.level_count):
                level_dir = os.path.join(files_output_path, str(level))
                if not os.path.exists(level_dir):
                    os.makedirs(level_dir)
                
                cols, rows = generator.level_tiles[level]
                for col in range(cols):
                    for row in range(rows):
                        tile = generator.get_tile(level, (col, row))
                        tile_path = os.path.join(level_dir, f"{col}_{row}.jpg")
                        tile.save(tile_path, 'JPEG', quality=90)
            
            print(f"  Successfully generated tiles for {slide_name}")
            slide.close()
        except Exception as e:
            print(f"  Error processing {filename}: {e}")

    print("\nConversion Complete!")
    print(f"Tiles are located in: {OUTPUT_DIR}")
    print("You can now safely upload the 'docs' folder to GitHub.")

if __name__ == '__main__':
    convert_slides()
