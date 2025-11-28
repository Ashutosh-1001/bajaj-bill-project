import io, math, requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from pdf2image import convert_from_bytes
from PIL import Image
from ocr_helpers import (
    preprocess_image_pil,
    ocr_image_get_words,
    group_words_to_lines,
    parse_lines_to_items,
)
from reconcile import dedupe_items, detect_totals_and_reconcile

app = FastAPI(title="Bajaj Bill Extraction API - Starter")

class RequestSchema(BaseModel):
    document: str

@app.post("/extract-bill-data")
def extract_bill_data(req: RequestSchema):
    url = req.document
    # Download document
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        content = r.content
        ct = r.headers.get("Content-Type", "")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to download document: {e}")

    images = []
    try:
        if b"%PDF" in content[:4] or "application/pdf" in ct:
            images = convert_from_bytes(content)
        else:
            im = Image.open(io.BytesIO(content)).convert("RGB")
            images = [im]
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read document as PDF/image: {e}")

    pagewise_line_items = []
    all_items_flat = []
    invoice_totals_found = []

    for idx, pil_img in enumerate(images, start=1):
        proc = preprocess_image_pil(pil_img)
        words = ocr_image_get_words(proc)                       
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
        all_items_flat.extend(items)

    unique_items = dedupe_items(all_items_flat)
    computed_total = round(sum([float(it["item_amount"]) for it in unique_items]), 2)

    invoice_total = None
    if invoice_totals_found:
        invoice_total = round(max(invoice_totals_found), 2)

    total_item_count = len(unique_items)

    response_data = {
        "is_success": True,
        "token_usage": {"total_tokens": 0, "input_tokens": 0, "output_tokens": 0},
        "data": {
            "pagewise_line_items": pagewise_line_items,
            "total_item_count": total_item_count,
            "reconciled_amount": computed_total,
            "invoice_total_extracted": invoice_total
        }
    }
    return response_data
