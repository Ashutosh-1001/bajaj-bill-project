FROM python:3.10-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils \
    tesseract-ocr \
    libtesseract-dev \
    libsm6 libxext6 libxrender1 \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . .

ENV PORT=8000

CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port $PORT"]
