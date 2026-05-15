FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN python -m unittest

CMD ["python", "-m", "grocery_pricing.pipeline", "--fixture", "fixtures/sample_product.html", "--artifacts-dir", "artifacts"]
