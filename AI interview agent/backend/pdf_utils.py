import os

try:
    import pymupdf as fitz
except ImportError:
    import fitz


def make_pdf(path, lines):
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    y = 700
    for line in lines:
        page.insert_text((50, y), line, fontsize=12, fontname="helv")
        y -= 14
    doc.save(path)
    doc.close()
