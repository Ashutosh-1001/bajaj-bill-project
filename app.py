import io
import logging
import requests
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pdf2image import convert_from_bytes
from PIL import Image

from ocr_helpers import (
    preprocess_image_pil,
    ocr_image_get_words,
    group_words_to_lines,
    parse_lines_to_items,
)

from reconcile import dedupe_items, detect_totals_and_reconcile

# -------------------- Logging --------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bajaj-bill-api")

# -------------------- FastAPI App --------------------
app = FastAPI(title="Bajaj Bill Extraction API - Starter")

# Allow all origins (important for Render / Swagger)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------- Utility --------------------
def safe_float(x, default=0.0):
    """Try to convert x to float; if fails return default."""
    try:
        return float(x)
    except Exception:
        return default


# -------------------- Request Schema --------------------
class RequestSchema(BaseModel):
    document: str


# -------------------- Root & Health (helpful) --------------------
@app.get("/")
def index():
    return {"ok": True, "message": "Bajaj Bill Extraction API - POST /extract-bill-data"}


@app.get("/healthz")
def health():
    return {"status": "ok"}


# -------------------- POST Endpoint --------------------
@app.post("/extract-bill-data")
def extract_bill_data(req: RequestSchema, request: Request = None):
    """
    Accepts JSON: {"document": "<url_to_image_or_pdf>"}
    Returns the extraction result in the required schema.
    """
    try:
        url = req.document
        logger.info("Received request to process document: %s", url)

        # ---------- 1. Download file ----------
        try:
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            content = r.content
            ct = r.headers.get("Content-Type", "")
            logger.info("Downloaded document, content-type=%s, bytes=%d", ct, len(content))
        except Exception as e:
            logger.exception("Failed to download document")
            raise HTTPException(status_code=400, detail=f"Could not download document: {e}")

        # ---------- 2. Convert to images ----------
        images = []
        try:
            # PDF detection (content header OR magic bytes)
            if (content[:4] == b"%PDF") or ("pdf" in (ct or "").lower()):
                images = convert_from_bytes(content)
                logger.info("Converted PDF to %d image(s)", len(images))
            else:
                img = Image.open(io.BytesIO(content)).convert("RGB")
                images = [img]
                logger.info("Loaded single image")
        except Exception as e:
            logger.exception("Failed to read file as image/PDF")
            raise HTTPException(status_code=400, detail=f"Could not read file as image/PDF: {e}")

        pagewise_line_items = []
        flat_items = []
        invoice_totals_found = []

        # ---------- 3. OCR each page ----------
        for idx, img in enumerate(images, start=1):
            logger.info("Processing page %d", idx)
            processed = preprocess_image_pil(img)
            words = ocr_image_get_words(processed)
            lines = group_words_to_lines(words, y_threshold=12)
            items = parse_lines_to_items(lines)
            totals = detect_totals_and_reconcile(lines)

            if totals:
                invoice_totals_found.extend(totals)

            pagewise_line_items.append({
                "page_no": str(idx),
                "page_type": "Bill Detail",
                "bill_items": items
            })

            flat_items.extend(items)

        # ---------- 4. De-duplicate items ----------
        unique_items = dedupe_items(flat_items) if flat_items else []

        # ---------- 5. Compute total safely ----------
        computed_total = round(sum(safe_float(i.get("item_amount", 0.0)) for i in unique_items), 2)

        invoice_total = None
        if invoice_totals_found:
            invoice_total = round(max(invoice_totals_found), 2)

        total_item_count = len(unique_items)

        # ---------- 6. Final API response ----------
        response = {
            "is_success": True,
            "token_usage": {
                "total_tokens": 0,
                "input_tokens": 0,
                "output_tokens": 0
            },
            "data": {
                "pagewise_line_items": pagewise_line_items,
                "total_item_count": total_item_count,
                "reconciled_amount": computed_total,
                "invoice_total_extracted": invoice_total
            }
        }

        logger.info("Returning response: items=%d computed_total=%s invoice_total=%s",
                    total_item_count, computed_total, invoice_total)
        return response

    except HTTPException:
        # re-raise HTTP exceptions unchanged so client sees correct status
        raise
    except Exception as e:
        logger.exception("Unhandled error in extract_bill_data")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")
