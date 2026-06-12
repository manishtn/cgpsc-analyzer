from PIL import Image
import pytesseract

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

def image_to_text(image_path):
    image = Image.open(image_path)

    width, height = image.size

    # Keep only right half (English)
    image = image.crop(
        (
            width // 2,
            0,
            width,
            height
        )
    )

    custom_config = r'--oem 3 --psm 6'

    text = pytesseract.image_to_string(
        image,
        lang="eng",
        config=custom_config
    )

    return text