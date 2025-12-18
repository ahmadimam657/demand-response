import os
import shutil
from pathlib import Path

from pdf2image import convert_from_path

# Determine project root (two levels up from this script)
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent

# Define paths
TEX_DIR = SCRIPT_DIR  # assets/scripts/
IMAGES_DIR = PROJECT_ROOT / "images"
TEMP_DIR = SCRIPT_DIR / "temp"

# Ensure output directory exists
IMAGES_DIR.mkdir(parents=True, exist_ok=True)
TEMP_DIR.mkdir(parents=True, exist_ok=True)

# Find all .tex files in the scripts directory
tex_files = list(TEX_DIR.glob("*.tex"))

# Compile LaTeX files and convert to PNG
for tex_file in tex_files:
    # Skip transfer_matrix_moving_horizon.tex as it will be processed separately for GIF
    if tex_file.name == "transfer_matrix_moving_horizon.tex":
        continue
    
    # Compile LaTeX to PDF (run from TEX_DIR to find .sty files)
    original_dir = os.getcwd()
    os.chdir(TEX_DIR)
    os.system(f'pdflatex -output-directory="{TEMP_DIR}" "{tex_file.name}"')
    os.chdir(original_dir)
    
    base_name = tex_file.stem
    pdf_file = TEMP_DIR / f"{base_name}.pdf"
    
    if pdf_file.exists():
        # Convert PDF to images at high resolution (600 DPI for crisp quality)
        dpi = 5000 if 'logo' in base_name else 600
        images = convert_from_path(str(pdf_file), dpi=dpi)
        
        for i, image in enumerate(images):
            if len(images) == 1:
                image_file = IMAGES_DIR / f"{base_name}.png"
            else:
                image_file = IMAGES_DIR / f"{base_name}_page_{i+1}.png"
            image.save(str(image_file), 'PNG')
        
        print(f"Generated: {base_name}.png")

# Clean up temporary files
if TEMP_DIR.exists():
    shutil.rmtree(TEMP_DIR)

# Generate animated GIF
gif_tex = TEX_DIR / "transfer_matrix_moving_horizon.tex"
if gif_tex.exists():
    make_gif_script = TEX_DIR / "make_gif.py"
    os.system(f'python "{make_gif_script}" "{gif_tex}" --values "1,7,13,19,25"')
    
    # Move animation.gif to images folder (check both root and script dir)
    animation_locations = [
        PROJECT_ROOT / "animation.gif",
        SCRIPT_DIR / "animation.gif"
    ]
    animation_dst = IMAGES_DIR / "animation.gif"
    
    for animation_src in animation_locations:
        if animation_src.exists():
            shutil.move(str(animation_src), str(animation_dst))
            print("Generated: animation.gif")
            break
    
    # Clean up build folder if it exists
    build_dir = SCRIPT_DIR / "build"
    if build_dir.exists():
        shutil.rmtree(build_dir)
