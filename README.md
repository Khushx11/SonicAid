# SonicAid — Audio Intelligence for Sensory Therapy Research

SonicAid is an experimental audio-processing platform exploring sound classification and session-level analysis for sensory-therapy research. The repository contains a FastAPI backend, a React frontend, a PyTorch multi-task model scaffold, and a synthetic-data training pipeline. **The streaming API can now use a checkpoint trained on real ESC-10 environmental sounds. Without a trusted local checkpoint, it explicitly reports model unavailability rather than inventing predictions.**

> **Scope:** environmental sound classification research, not a diagnostic, clinical or therapy-evaluation system. ESC-10 contains no patient outcomes, engagement scores or emotion labels. A separate older multi-task training scaffold uses synthetic data and must not be confused with the ESC-10 results.

## Components

| Component | Location | Purpose |
| --- | --- | --- |
| Streaming API | `backend/app/api/routes/stream.py` | Receives 16 kHz PCM16 via WebSocket; predicts five-second environmental sound windows with an installed checkpoint |
| Model and inference | `ml/models/`, `backend/app/ml_inference/` | PyTorch architecture and feature extraction |
| Real-world training and evaluation | `ml/real_audio/esc10.py` | ESC-10 acoustic features, official five-fold evaluation and a serialized SVC baseline |
| Earlier research scaffold | `ml/training/`, `ml/configs/` | Synthetic multi-task experimentation, not clinical validation |
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

HTTP requests and browser WebSockets permit only the default local development origins (`http://localhost:5173` and `http://127.0.0.1:5173`). To authorise a different frontend, set an explicit comma-separated allowlist such as `SONICAID_ALLOWED_ORIGINS=https://your-trusted-domain.example`. The server does not support wildcard origins.

### Frontend

In a second terminal:

```bash
cd frontend
npm install
VITE_API_BASE=http://localhost:8000 npm run dev
```

Open `http://localhost:5173`.

### Real labelled environmental audio (ESC-10)

**Dataset:** Karol J. Piczak, *ESC: Dataset for Environmental Sound Classification* (2015), [official repository](https://github.com/karolpiczak/ESC-50). ESC-50 contains 2,000 five-second environmental audio clips; this implementation uses only the 400 clips in the **ESC-10 subset**, separately identified by the publisher as CC BY licensed. Keep the source WAV recordings in the locally ignored `data/` directory and follow the publisher's attribution requirements. No third-party recordings are committed here.

From the repository root, with Python dependencies installed:

```bash
git clone --depth 1 https://github.com/karolpiczak/ESC-50.git data/ESC-50
python -m ml.real_audio.esc10 train --dataset data/ESC-50 \
  --model ml/artifacts/esc10.joblib --metrics ml/artifacts/esc10_metrics.json

# Run the trained model on a separate WAV file.
python -m ml.real_audio.esc10 predict \
  --model ml/artifacts/esc10.joblib --audio /path/to/sample.wav

# Start actual streaming inference using the locally trained checkpoint.
SONICAID_ESC10_MODEL=ml/artifacts/esc10.joblib \
  uvicorn backend.app.main:app --reload --port 8000
```

The training code uses a fixed StandardScaler + RBF SVC baseline with 64-band log-mel mean/std, RMS and zero-crossing features. Each of the dataset's five predefined folds is held out once. The program writes observed fold accuracy, macro-F1 and a confusion matrix to `esc10_metrics.json`, then fits the final checkpoint on all 400 examples. It does not tune the estimator on held-out fold scores. A GitHub Actions workflow can also train the dataset and attach the checkpoint, its SHA-256 and measured metrics as build artifacts and a release.

**Model limitations:** SVC scores have not been externally calibrated; audio outside the ten trained categories is still classified into one of those classes. Training on fixed five-second clips does not guarantee robustness in a noisy room, on a different microphone or with overlapping sounds. No clinical, engagement or emotion claims follow from this dataset. Never load untrusted `.joblib` files, since joblib deserialization can execute arbitrary code.

### Synthetic-data model training

From the repository root with the Python environment activated:

```bash
python -m ml.training.train --config ml/configs/sonicaid_multitask_small.yaml
python -m ml.training.eval --config ml/configs/sonicaid_multitask_small.yaml --checkpoint ml/artifacts/sonicaid_best.pt
```

Checkpoints, local sessions, and generated data are ignored by Git. Depending on your machine, PyTorch audio dependencies may require platform-specific installation.

## Streaming interface

The WebSocket endpoint `ws://localhost:8000/ws/stream` accepts binary 16 kHz mono PCM audio chunks. With `SONICAID_ESC10_MODEL` configured to a valid locally trained checkpoint, the service uses actual ESC-10 sound-class predictions from five-second rolling PCM16 windows. Without weights it sends a `model_unavailable` status and does not produce predictions. The frontend displays that status. Emotion and engagement fields are null, rather than invented. See `backend/app/api/routes/stream.py` for the current contract.

## Testing

```bash
pytest backend/tests
```

The GitHub Actions workflow builds the React app and runs backend regression tests. Check the latest CI run for the actual status.

## Limitations and next steps

- The separate synthetic multi-task research scaffold is not clinically validated. The new ESC-10 pipeline uses real audio with environmental sound labels but lacks therapy-specific annotations.
- The current backend configuration is intended for local development. Browser origins are restricted, but **there is no user authentication or authorisation**. Do not deploy publicly with personal recordings or session exports.
- Streaming requires the trained ESC-10 checkpoint. If none is installed the service deliberately returns no classification, instead of simulated outputs.
- The training workflow records measured five-fold validation metrics. Further independent generalisation, streaming latency, out-of-distribution detection and confidence calibration remain open research tasks.
- Session recordings and exports may contain sensitive information and must not be committed.

See the research design document in `plan/` for the proposed architecture and future direction.

## Repository purpose

This repository documents the software architecture and implementation progress of an exploratory audio-intelligence system. It should be evaluated as an engineering prototype, not as a released clinical product.
