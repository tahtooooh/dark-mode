import os
import argparse
import fitz  # PyMuPDF
from PIL import Image, ImageOps
import io
from pathlib import Path

def list_pdfs_in_folder(folder: str = "."):
    return sorted([str(p) for p in Path(folder).iterdir() if p.is_file() and p.suffix.lower() == ".pdf"])

def pdf_to_darkmode(input_pdf: str, output_pdf: str, dpi: int = 200):
    zoom = dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)

    src = fitz.open(input_pdf)
    dst = fitz.open()

    for page in src:
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        # Invert colors (dark mode look)
        img = ImageOps.invert(img)

        buf = io.BytesIO()
        img.save(buf, format="PNG", optimize=True)
        png_bytes = buf.getvalue()

        rect = page.rect
        new_page = dst.new_page(width=rect.width, height=rect.height)
        new_page.insert_image(rect, stream=png_bytes)

    dst.save(output_pdf)
    dst.close()
    src.close()

def make_output_name(input_pdf: str, suffix: str = "_dark") -> str:
    p = Path(input_pdf)
    return str(p.with_name(p.stem + suffix + p.suffix))

def main():
    parser = argparse.ArgumentParser(description="Convert PDF(s) to dark-mode (inverted colors).")
    parser.add_argument("--input", help="Convert a specific PDF file (e.g., book.pdf)")
    parser.add_argument("--all", action="store_true", help="Convert ALL PDFs in the current folder")
    parser.add_argument("--dpi", type=int, default=200, help="Render DPI (higher = better quality, bigger file)")
    parser.add_argument("--suffix", default="_dark", help="Suffix added to output files (default: _dark)")
    args = parser.parse_args()

    if not args.input and not args.all:
        # Default behavior: convert all PDFs if no input is provided
        args.all = True

    if args.input:
        if not os.path.exists(args.input) or not args.input.lower().endswith(".pdf"):
            raise FileNotFoundError(f"Can't find a PDF named '{args.input}' in: {os.getcwd()}")

        out_name = make_output_name(args.input, suffix=args.suffix)
        pdf_to_darkmode(args.input, out_name, dpi=args.dpi)
        print(f"✅ Done!\nCreated: {out_name}\nFolder: {os.getcwd()}")
        return

    # args.all == True
    pdfs = list_pdfs_in_folder(".")
    if not pdfs:
        raise FileNotFoundError(f"No PDF files found in: {os.getcwd()}")

    for pdf in pdfs:
        out_name = make_output_name(pdf, suffix=args.suffix)
        # Skip already-dark outputs to avoid reprocessing loops
        if Path(pdf).stem.endswith(args.suffix):
            continue
        pdf_to_darkmode(pdf, out_name, dpi=args.dpi)
        print(f"✅ Created: {out_name}")

    print(f"\nAll done. Output folder: {os.getcwd()}")

if __name__ == "__main__":
    main()