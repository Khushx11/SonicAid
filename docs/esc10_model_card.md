# SonicAid ESC-10 Environmental Sound Model Card

## Model and intended use

**Artifact:** `esc10.joblib` from [Release esc10-baseline](https://github.com/Khushx11/SonicAid/releases/tag/esc10-baseline).

**Task:** Recognise the most likely one of ten environmental sound categories in a five-second mono audio window. This is a non-clinical baseline used to evaluate the end-to-end audio-processing and inference architecture.

**Classes:** dog, rooster, rain, sea waves, crackling fire, crying baby, sneezing, clock tick, helicopter, chainsaw.

**Method:** 16 kHz resampling; 64-band log-mel spectral means and standard deviations, RMS energy and zero-crossing rate. StandardScaler + RBF SVC (`C=5`, `gamma=scale`, `probability=True`, fixed seed 42). No image, speech transcription, patient notes or emotion labels are used.

## Data provenance

Dataset: Karol J. Piczak (2015), *ESC: Dataset for Environmental Sound Classification*. [Official dataset repository](https://github.com/karolpiczak/ESC-50) and [original research description](https://doi.org/10.7910/DVN/YDEPUT). This experiment uses the **ESC-10** subcollection: 400 five-second samples across ten categories, with 40 samples per class. The publisher identifies ESC-10 as CC BY licensed. Audio is downloaded from the official dataset repository during training; source recordings are excluded from this code repository.

## Evaluation protocol

Each of the five predefined ESC-10 folds was held out as test once while training on the remaining four. Hyperparameters were fixed before this evaluation and not selected on the test folds. Each fold includes 80 test recordings. Afterwards, a deployment checkpoint was fitted on all 400 clips. That final checkpoint's training accuracy is **not** presented as generalisation accuracy.

| Official fold | Accuracy | Macro F1 |
|---|---:|---:|
| 1 | 71.25% | 0.7010 |
| 2 | 82.50% | 0.8203 |
| 3 | 77.50% | 0.7748 |
| 4 | 87.50% | 0.8750 |
| 5 | 81.25% | 0.8047 |
| **Pooled out-of-fold** | **80.00%** | **0.8016** |

The **pooled** macro F1 of 0.8016 is computed across all 400 out-of-fold predictions, rather than averaging the five fold-specific F1 values. A separate external microphone/room test is still needed.

[Reproduce the measured training workflow](https://github.com/Khushx11/SonicAid/actions/runs/45381962916) and [inspect the exact metrics JSON](https://github.com/Khushx11/SonicAid/releases/download/esc10-baseline/esc10_metrics.json).

## Operational boundaries

- The system predicts one of ten categories even when the sound belongs to none of them. It has no independently validated unknown-sound detector.
- `predict_proba` scores come from SVC probability fitting; they are **not** externally calibrated or clinically interpretable confidence.
- Dataset clips are five seconds long and relatively isolated; crowded rooms, mixed sources and long continuous recordings may behave differently.
- The categories do not measure emotions, sensory tolerance, attention, engagement, stress, clinical outcomes or therapeutic efficacy.
- No clinical deployment, medical diagnosis, patient monitoring, independent demographic evaluation or safety certification is claimed.
- Joblib checkpoints use pickle and must only be loaded from a trusted source. Release includes SHA-256 verification material; a hash alone does not prove that a publisher is trustworthy.

## Reproducibility

```bash
git clone --depth 1 https://github.com/karolpiczak/ESC-50.git data/ESC-50
python -m ml.real_audio.esc10 train --dataset data/ESC-50
```

The training workflow stores the checkpoint, per-fold metrics and a SHA-256 digest as release assets. Python package versions are pinned in `requirements.txt`.

## Next research experiments

Compare against simple spectral baselines and pretrained audio representations, evaluate natural environmental noise and overlapping sounds, test confidence calibration and abstention on unknown classes, and repeat evaluation with a separately collected dataset. A clinical study would require independent participant consent, appropriate approval, relevant labels and specialist validation.
