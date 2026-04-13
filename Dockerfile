FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p uploads output templates

# Copy templates to a staging dir for first-run initialization
RUN cp -r templates /app/_templates_default

# Entrypoint: initialize data dir if using persistent disk, then start
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
