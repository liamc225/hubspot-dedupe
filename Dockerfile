FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN python -m pip install --upgrade pip \
    && python -m pip install .

EXPOSE 8000

CMD ["hubspot-dedupe", "serve", "--host", "0.0.0.0", "--port", "8000"]
