import re

def clean_text(text):

    # remove page numbers
    text = re.sub(r"\[\d+\]", "", text)

    # remove CGPSC footer
    text = re.sub(r"S24\s*-\s*25", "", text)

    # remove excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text