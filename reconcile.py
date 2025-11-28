from rapidfuzz import fuzz
import re

def dedupe_items(items, name_thresh=90.0):
    keep = []
    used = [False]*len(items)
    for i,a in enumerate(items):
        if used[i]:
            continue
        keep.append(a)
        for j in range(i+1, len(items)):
            if used[j]:
                continue
            b = items[j]
            amt_eq = float(a.get("item_amount",0)) == float(b.get("item_amount",0))
            qty_eq = float(a.get("item_quantity",0)) == float(b.get("item_quantity",0))
            score = fuzz.token_set_ratio(a.get("item_name",""), b.get("item_name",""))
            if score >= name_thresh and amt_eq and qty_eq:
                used[j] = True
    return keep

_num_re = re.compile(r'^[\d,]+(?:\.\d+)?$')
def _clean_num(s):
    return s.replace(",","")

def detect_totals_and_reconcile(lines):
    totals = []
    keywords = ["total", "grand", "net payable", "subtotal", "amount payable", "invoice total", "net amount"]
    for line in lines:
        texts = [w["text"].lower() for w in line]
        joined = " ".join(texts)
        if any(k in joined for k in keywords):
            for w in reversed(line):
                t = w["text"]
                if _num_re.match(t):
                    try:
                        val = float(_clean_num(t))
                        totals.append(round(val,2))
                        break
                    except:
                        continue
    return totals
