"""
Shared helper for rasterizing a generated PDF's first page to a PNG image.

Used to turn the existing reportlab-based exports (student profile,
payment receipt) into single-page image files, so they can be placed
into other documents or combined on one sheet before printing.
"""
import logging

logger = logging.getLogger(__name__)


def pdf_first_page_to_png(pdf_path: str, png_path: str, dpi: int = 200) -> bool:
    """Render the first page of `pdf_path` to a PNG at `png_path`.

    Returns True on success, False on failure (logged).
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        logger.error("PyMuPDF (fitz) is not installed; cannot convert PDF to PNG.")
        return False

    try:
        doc = fitz.open(pdf_path)
        if doc.page_count == 0:
            doc.close()
            return False
        page = doc.load_page(0)
        zoom = dpi / 72.0
        matrix = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=matrix)
        pix.save(png_path)
        doc.close()
        logger.info(f"PDF→PNG: {pdf_path} -> {png_path} ({dpi} dpi)")
        return True
    except Exception as exc:
        logger.error(f"PDF→PNG conversion failed for {pdf_path}: {exc}")
        return False
