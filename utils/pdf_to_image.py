"""
Shared helper for rasterizing a generated PDF to a PNG image.

Stitches ALL pages of the PDF into one tall PNG so that multi-page
profiles (with exam results, long attendance summaries, etc.) are never
cut off. The result is one image file the printing shop can place, crop,
or scale as needed.
"""
import logging

logger = logging.getLogger(__name__)


def pdf_first_page_to_png(pdf_path: str, png_path: str, dpi: int = 200) -> bool:
    """Render ALL pages of `pdf_path` stitched vertically into one PNG.

    If the PDF is one page, the output is identical to before.
    If the PDF is multi-page (e.g. long student profile with exam results),
    all pages are concatenated top-to-bottom into a single tall PNG so
    nothing is cut off.

    Returns True on success, False on failure (logged).
    """
    try:
        import fitz          # PyMuPDF
        from PIL import Image  # Pillow — already a dependency
        import io
    except ImportError as exc:
        logger.error(f"Missing dependency for PDF→PNG: {exc}")
        return False

    try:
        doc = fitz.open(pdf_path)
        if doc.page_count == 0:
            doc.close()
            return False

        zoom   = dpi / 72.0
        matrix = fitz.Matrix(zoom, zoom)

        if doc.page_count == 1:
            # Fast path — single page, write directly
            pix = doc.load_page(0).get_pixmap(matrix=matrix)
            pix.save(png_path)
        else:
            # Multi-page — render each page, stitch vertically with Pillow
            page_images = []
            for page_num in range(doc.page_count):
                pix  = doc.load_page(page_num).get_pixmap(matrix=matrix)
                img  = Image.open(io.BytesIO(pix.tobytes("png")))
                page_images.append(img)

            total_w = max(img.width  for img in page_images)
            total_h = sum(img.height for img in page_images)
            canvas  = Image.new("RGB", (total_w, total_h), (255, 255, 255))
            y_off = 0
            for img in page_images:
                canvas.paste(img, (0, y_off))
                y_off += img.height
            canvas.save(png_path, "PNG")

        doc.close()
        logger.info(
            f"PDF→PNG ({doc.page_count if not doc.is_closed else '?'} pages): "
            f"{pdf_path} -> {png_path} ({dpi} dpi)"
        )
        return True
    except Exception as exc:
        logger.error(f"PDF→PNG conversion failed for {pdf_path}: {exc}")
        return False
