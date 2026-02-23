FROM pytorch/pytorch:2.3.0-cuda11.8-cudnn8-runtime

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend ./backend
COPY ml ./ml
COPY configs ./configs

ENV PYTHONPATH=/app

EXPOSE 8000
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]

