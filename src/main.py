from pathlib import Path
from clean_text import clean_text

from pdf_to_images import pdf_to_images
from ocr import image_to_text

PDF_FILE = "data/pdfs/2025.pdf"

images = pdf_to_images(
    PDF_FILE,
    "data/images"
)

full_text = ""

for image in images:
    print("OCR:", image)

    full_text += image_to_text(image)
    full_text += "\n\n"

# Clean AFTER OCR
full_text = clean_text(full_text)

Path("data/raw_text").mkdir(
    parents=True,
    exist_ok=True
)

with open(
    "data/raw_text/ocr_output.txt",
    "w",
    encoding="utf-8"
) as f:
    f.write(full_text)

print("Done.")