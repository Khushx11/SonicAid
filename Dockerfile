FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch==2.3.0 torchaudio==2.3.0 \
    && pip install --no-cache-dir -r requirements.txt

COPY backend ./backend
COPY ml ./ml
COPY scripts ./scripts

ENV PYTHONPATH=/app

EXPOSE 8000
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]

