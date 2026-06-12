from pdf2image import convert_from_path
from pathlib import Path


def pdf_to_images(pdf_path, output_dir):

    Path(output_dir).mkdir(parents=True, exist_ok=True)

    pages = convert_from_path(
        pdf_path,
        dpi=300
    )

    image_paths = []

    for i, page in enumerate(pages):

        path = Path(output_dir) / f"page_{i+1}.png"

        page.save(path)

        image_paths.append(str(path))

    return image_paths