# SonicAid — Audio Intelligence for Sensory Therapy Research

SonicAid is an experimental audio-processing platform exploring sound classification and session-level analysis for sensory-therapy research. The repository contains a FastAPI backend, a React frontend, a PyTorch multi-task model, and a synthetic-data training pipeline.

> **Project status:** research prototype. The included training pipeline uses synthetic/mock audio data; it is not evidence of clinical validity, therapeutic effectiveness, or real-world recognition accuracy. Do not use this software for diagnosis or treatment decisions.

## Components

| Component | Location | Purpose |
| --- | --- | --- |
| Streaming API | `backend/app/api/routes/stream.py` | Accepts 16 kHz mono PCM audio via WebSocket and returns structured prediction messages |
| Model and inference | `ml/models/`, `backend/app/ml_inference/` | PyTorch architecture and feature extraction |
| Training and evaluation | `ml/training/`, `ml/configs/` | Configurable synthetic-data training, validation, checkpoints, and metrics |
| Session endpoints | `backend/app/api/routes/sessions.py` | Lists sessions and exports session data as CSV |
| Frontend | `frontend/` | React interface for local exploration |
| Research proposal | `plan/` | Design and methodology notes |

## Local development

### Backend

Run these commands from the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.app.main:app --reload --port 8000
```

Health endpoint: `http://localhost:8000/api/health`.

### Frontend

In a second terminal:

```bash
cd frontend
npm install
VITE_API_BASE=http://localhost:8000 npm run dev
```

Open `http://localhost:5173`.

### Synthetic-data model training

From the repository root with the Python environment activated:

```bash
python -m ml.training.train --config ml/configs/sonicaid_multitask_small.yaml
python -m ml.training.eval --config ml/configs/sonicaid_multitask_small.yaml --checkpoint ml/artifacts/sonicaid_best.pt
```

Checkpoints, local sessions, and generated data are ignored by Git. Depending on your machine, PyTorch audio dependencies may require platform-specific installation.

## Streaming interface

The WebSocket endpoint `ws://localhost:8000/ws/stream` accepts binary 16 kHz mono PCM audio chunks. It generates predictions through the inference service and returns JSON messages when predictions are available. See `backend/app/api/routes/stream.py` for the current contract.

## Testing

```bash
pytest backend/tests
```

This command is provided as an entry point; no CI status or independently verified test pass rate is claimed here.

## Limitations and next steps

- The current training dataset is synthetic. External validation on appropriately consented, representative datasets is required.
- The current backend configuration is intended for local development; production deployment requires authentication, restrictive CORS settings, and data-protection review.
- Streaming latency, classification performance, and calibration need benchmark results before reliability claims can be made.
- Session recordings and exports may contain sensitive information and must not be committed.

See the research design document in `plan/` for the proposed architecture and future direction.

## Repository purpose

This repository documents the software architecture and implementation progress of an exploratory audio-intelligence system. It should be evaluated as an engineering prototype, not as a released clinical product.
