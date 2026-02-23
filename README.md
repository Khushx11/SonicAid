SonicAid Next-Gen Audio Intelligence Platform
=============================================

This repository contains a next-generation, research-grade version of **Sonic Aid**:
an audio intelligence platform designed for therapists and researchers working with
ASD sensory therapy.

The system extends the original MFCC + SVM Sonic Aid prototype into a
deep-learning driven, multi-task, streaming architecture with:

- Near real-time WebSocket audio streaming
- Log-mel + CNN + Transformer acoustic modeling
- Multi-head outputs (sound class, emotion, environmental tags, noise, engagement)
- Research tooling (attention heatmaps, calibration, rich session logs)
- React frontend with Web Audio API visualizations

For full architecture details, see the plan in `.cursor/plans/` and the
documentation sections below (to be completed as the implementation evolves).

## Quickstart (local, CPU)

### Backend

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.app.main:app --reload --port 8000
```

Open `http://localhost:8000/api/health`.

### Frontend

```bash
cd frontend
npm install
VITE_API_BASE=http://localhost:8000 npm run dev
```

Open `http://localhost:5173`.

## Streaming API

- **WebSocket**: `ws://localhost:8000/ws/stream`
  - Send binary messages containing PCM16 mono frames.
  - Receive JSON messages (see `backend/app/models/stream.py`) with multi-head outputs.

## Session logging + export

- **List sessions**: `GET /api/sessions`
- **Export CSV**: `GET /api/sessions/{session_id}/export.csv`

Sessions are persisted as `.jsonl` on disconnect under `storage/sessions/`.

## Training

This repo includes a full scaffolding training loop using a synthetic dataset so the
pipeline runs without private ASD data.

```bash
python -m ml.training.train --config ml/configs/sonicaid_multitask_small.yaml
python -m ml.training.eval --config ml/configs/sonicaid_multitask_small.yaml --checkpoint ml/artifacts/sonicaid_best.pt
tensorboard --logdir ml/runs
```

## Docker (local dev)

```bash
docker compose up --build
```

Then open:
- Backend: `http://localhost:8000/api/health`
- Frontend: `http://localhost:5173`


