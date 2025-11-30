This project reads medical bills and finds all the items, rates, quantities, and amounts from the bill.

You send a bill image link, and the API returns all the information in a clean JSON format.

⭐ What this API does

Takes a bill image URL

Reads the text using OCR

Uses AI to find every item

Removes duplicate items

Returns everything in the required format

🚀 How to use
POST /extract-bill-data

Send this body:

{
  "document": "https://your-bill-image-url"
}


You will get back something like:

{
  "is_success": true,
  "token_usage": {...},
  "data": {
    "pagewise_line_items": [
      {
        "page_no": "1",
        "page_type": "Bill Detail",
        "bill_items": [
          {
            "item_name": "Tablet Dolo 650",
            "item_amount": 30.0,
            "item_rate": 10.0,
            "item_quantity": 3
          }
        ]
      }
    ],
    "total_item_count": 1
  }
}

▶️ Run locally
pip install -r requirements.txt
uvicorn app:app --reload --port 8080

🐳 Run using Docker
docker build -t bajaj-bill-project .
docker run -p 8080:8080 bajaj-bill-project

📁 Project Files
app.py           → Main API code
ocr_helpers.py   → OCR functions
reconcile.py     → Clean & fix extracted items
Dockerfile       → For deployment
requirements.txt → Python packages

📌 Notes

Works with PNG/JPG/PDF bill images

Uses OCR + AI model

Avoids double-counting totals

Output matches HackRx Datathon format

If you want an even shorter README (5 lines), tell me:
👉 "make it shorter"

You said:
humanise it and give
ChatGPT said:

Here is a human-friendly, simple, natural, easy-to-read README.
Not technical… just clear, like you’re explaining the project to a person casually.
Copy–paste this into your GitHub repo.

Bajaj Bill Project – Simple & Human-Friendly README

This project is a small API that helps read medical bills automatically.
You give it a link to a bill image, and the system uses OCR + AI to understand the bill and return all the important details like item name, quantity, rate, and amount.

I built this for the HackRx Bajaj Datathon, where the goal is to extract line items accurately without missing anything or double-counting.

🌟 What the API Does

Reads the bill image using OCR

Understands the text using an AI model

Picks out every item in the bill

Removes duplicates or totals that shouldn't be counted

Sends back clean, structured data in JSON format

Think of it like a smart helper that reads bills for you.

🚀 How to Use It

Send a POST request to:

/extract-bill-data


With this body:

{
  "document": "https://your-bill-image-link"
}


The API will return something like:

{
  "is_success": true,
  "data": {
    "pagewise_line_items": [
      {
        "page_no": "1",
        "page_type": "Bill Detail",
        "bill_items": [
          {
            "item_name": "Tablet Dolo 650",
            "item_amount": 30.0,
            "item_rate": 10.0,
            "item_quantity": 3
          }
        ]
      }
    ],
    "total_item_count": 1
  }
}

▶️ Running the Project

To run it locally:

pip install -r requirements.txt
uvicorn app:app --reload --port 8080


To run with Docker:

docker build -t bajaj-bill-project .
docker run -p 8080:8080 bajaj-bill-project

📁 What’s Inside the Repo

app.py → Main API logic

ocr_helpers.py → OCR code

reconcile.py → Cleans and fixes extracted items

Dockerfile → For deployment

requirements.txt → Python libraries

💬 Final Note

This project is my submission for the Bajaj Datathon.
It’s simple, clean, and does exactly what the challenge asked:
extract medical bill items accurately using OCR + AI.
