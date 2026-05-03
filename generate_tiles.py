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

    # Find all slide files recursively
    slide_files = []
    for root, dirs, files in os.walk(SLIDE_DIR):
        for f in files:
            if f.endswith(('.tif', '.tiff', '.svs', '.ndpi', '.btif')):
                # Get the relative path from SLIDE_DIR to the file
                rel_path = os.path.relpath(os.path.join(root, f), SLIDE_DIR)
                slide_files.append(rel_path)
    
    if not slide_files:
        print("No slides found in the slides/ directory.")
        return

    print(f"Found {len(slide_files)} slides across subdirectories. Starting conversion...")

    for rel_slide_path in slide_files:
        slide_path = os.path.join(SLIDE_DIR, rel_slide_path)
        # Get path without extension
        slide_rel_no_ext = os.path.splitext(rel_slide_path)[0]
        slide_name = os.path.basename(slide_rel_no_ext)
        
        # Determine output directory (mirroring input structure)
        slide_output_subdir = os.path.join(OUTPUT_DIR, os.path.dirname(rel_slide_path))
        if not os.path.exists(slide_output_subdir):
            os.makedirs(slide_output_subdir)

        dzi_output_path = os.path.join(OUTPUT_DIR, f"{slide_rel_no_ext}.dzi")
        files_output_path = os.path.join(OUTPUT_DIR, f"{slide_rel_no_ext}_files")

        print(f"Processing: {rel_slide_path} -> {slide_rel_no_ext}.dzi")
        
        try:
            slide = openslide.OpenSlide(slide_path)
            generator = DeepZoomGenerator(slide, tile_size=254, overlap=1, limit_bounds=False)

            # Save the .dzi XML file
            with open(dzi_output_path, 'w') as f:
                f.write(generator.get_dzi('jpg'))
            
            # Create the _files directory
            if not os.path.exists(files_output_path):
                os.makedirs(files_output_path)
            
            # Loop through all levels and tiles and save them
            print(f"  Saving tiles...")
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
            
            print(f"  Successfully generated tiles for {slide_rel_no_ext}")
            slide.close()
        except Exception as e:
            print(f"  Error processing {rel_slide_path}: {e}")

    print("\nConversion Complete!")
    print(f"Tiles are categorized in: {OUTPUT_DIR}")

if __name__ == '__main__':
    convert_slides()
