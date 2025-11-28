import cv2, numpy as np
from PIL import Image
import pytesseract, re

def preprocess_image_pil(pil_img: Image.Image) -> Image.Image:
    img = np.array(pil_img.convert("RGB"))
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    blur = cv2.GaussianBlur(gray, (3,3), 0)
    _, th = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return Image.fromarray(th)

def ocr_image_get_words(pil_img: Image.Image):
    data = pytesseract.image_to_data(pil_img, output_type=pytesseract.Output.DICT)
    words = []
    n = len(data["text"])
    for i in range(n):
        text = str(data["text"][i]).strip()
        if not text:
            continue
        try:
            conf = float(data["conf"][i])
        except:
            conf = -1.0
        left = int(data["left"][i])
        top = int(data["top"][i])
        width = int(data["width"][i])
        height = int(data["height"][i])
        words.append({"text": text, "bbox": (left, top, width, height), "conf": conf})
    return words

def group_words_to_lines(words, y_threshold=10):
    if not words:
        return []
    words_sorted = sorted(words, key=lambda w: (w["bbox"][1], w["bbox"][0]))
    lines = []
    current_line = []
    current_y = None
    for w in words_sorted:
        left, top, width, height = w["bbox"]
        center_y = top + height/2.0
        if current_y is None:
            current_y = center_y
            current_line = [w]
        else:
            if abs(center_y - current_y) <= y_threshold:
                current_line.append(w)
            else:
                lines.append(sorted(current_line, key=lambda x: x["bbox"][0]))
                current_line = [w]
                current_y = center_y
    if current_line:
        lines.append(sorted(current_line, key=lambda x: x["bbox"][0]))
    return lines

_num_re = re.compile(r'^[\d,]+(?:\.\d+)?$')
def _clean_num(s):
    return s.replace(",","")

def parse_lines_to_items(lines):
    items = []
    for line in lines:
        texts = [w["text"] for w in line]
        numeric_idxs = []
        for i,t in enumerate(texts):
            if _num_re.match(t):
                numeric_idxs.append((i,t))
        if not numeric_idxs:
            continue
        amt_idx, amt_str = numeric_idxs[-1]
        try:
            amount = float(_clean_num(amt_str))
        except:
            continue
        rate = None; qty = None
        if len(numeric_idxs) >= 2:
            rate_idx, rate_str = numeric_idxs[-2]
            try:
                rate = float(_clean_num(rate_str))
            except:
                rate = None
        if len(numeric_idxs) >= 3:
            qty_idx, qty_str = numeric_idxs[-3]
            try:
                qty = float(_clean_num(qty_str))
            except:
                qty = None
        cutoff = amt_idx
        if qty is not None:
            cutoff = numeric_idxs[-3][0]
        elif rate is not None:
            cutoff = numeric_idxs[-2][0]
        name_tokens = texts[:cutoff]
        item_name = " ".join(name_tokens).strip()
        if not item_name:
            non_nums = [t for t in texts if not _num_re.match(t)]
            item_name = " ".join(non_nums).strip() or "UNKNOWN"
        items.append({
            "item_name": item_name,
            "item_amount": round(float(amount),2),
            "item_rate": round(float(rate) if rate is not None else 0.0,2),
            "item_quantity": round(float(qty) if qty is not None else 1.0,2)
        })
    return items
