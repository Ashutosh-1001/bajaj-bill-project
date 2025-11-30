import io
import requests
from fastapi import FastAPI, HTTPException
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


# -------------------- FastAPI App --------------------
app = FastAPI(title="Bajaj Bill Extraction API - Starter")

# Allow all origins (important for Render)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------- Request Schema --------------------
class RequestSchema(BaseModel):
    document: str


# -------------------- POST Endpoint --------------------
@app.post("/extract-bill-data")
def extract_bill_data(req: RequestSchema):

    url = req.document

    # ---------- 1. Download file ----------
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        content = r.content
        ct = r.headers.get("Content-Type", "")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not download document: {e}")

    # ---------- 2. Convert to images ----------
    images = []
    try:
        if b"%PDF" in content[:4] or "pdf" in ct.lower():
            images = convert_from_bytes(content)
        else:
            img = Image.open(io.BytesIO(content)).convert("RGB")
            images = [img]
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not read file as image/PDF: {e}")

    pagewise_line_items = []
    flat_items = []
    invoice_totals_found = []

    # ---------- 3. OCR each page ----------
    for idx, img in enumerate(images, start=1):

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
    unique_items = dedupe_items(flat_items)

    # ---------- 5. Compute total ----------
    computed_total = round(sum(float(i["item_amount"]) for i in unique_items), 2)

    invoice_total = None
    if invoice_totals_found:
        invoice_total = round(max(invoice_totals_found), 2)

    total_item_count = len(unique_items)

    # ---------- 6. Final API response ----------
    return {
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
