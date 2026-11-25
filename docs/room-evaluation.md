# Real-room evaluation protocol

The existing browser smoke test verifies transport, checkpoint inference and microphone lifecycle with simulated audio. It does not measure recognition accuracy in rooms.

Use permission-cleared recordings without intelligible private speech. Record isolated ESC-10 classes, mixtures and unfamiliar sounds across different rooms and microphones. Keep each source recording and all derived windows together. Split by room and source, record unsupported and overlapping labels explicitly, and keep the final rooms untouched until the settings are frozen.

On development recordings, compare the closed-set model with a score threshold that can abstain. Report coverage and accepted error on known sounds and false acceptance among unfamiliar sounds. Report isolated, overlapped and unfamiliar cohorts separately, with per-class support, macro-F1 for the known classes and uncertainty intervals by recording session. Measure end-to-end time from the end of the input window to receipt of the prediction separately from the current server inference timing.

This protocol has no measured real-room accuracy or calibrated rejection threshold yet.
