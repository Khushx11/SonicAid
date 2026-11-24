import hashlib

import pytest

from scripts import install_esc10_model


def test_checkpoint_installer_verifies_hash_before_writing(monkeypatch, tmp_path):
    payload = b"trusted-model-placeholder"
    expected = hashlib.sha256(payload).hexdigest()
    called = []

    def fake_download(url, max_bytes):
        called.append(url)
        return (expected + "  ml/artifacts/esc10.joblib\n").encode() if url.endswith(".sha256") else payload

    monkeypatch.setattr(install_esc10_model, "download", fake_download)
    target = tmp_path / "artifacts" / "esc10.joblib"
    install_esc10_model.install(target)
    assert target.read_bytes() == payload
    install_esc10_model.install(target)
    assert target.read_bytes() == payload
    assert sum(url.endswith(".joblib") for url in called) == 1


def test_checkpoint_hash_mismatch_does_not_write(monkeypatch, tmp_path):
    def fake_download(url, limit):
        return (b"0" * 64 + b"  ml/artifacts/esc10.joblib\n") if url.endswith(".sha256") else b"tampered"

    monkeypatch.setattr(install_esc10_model, "download", fake_download)
    target = tmp_path / "esc10.joblib"
    with pytest.raises(ValueError, match="mismatch"):
        install_esc10_model.install(target)
    assert not target.exists()


def test_installer_refuses_to_overwrite_existing_different_model(monkeypatch, tmp_path):
    monkeypatch.setattr(
        install_esc10_model, "download",
        lambda url, limit: b"0" * 64 + b"  ml/artifacts/esc10.joblib\n",
    )
    target = tmp_path / "esc10.joblib"
    target.write_bytes(b"another model")
    with pytest.raises(FileExistsError):
        install_esc10_model.install(target)
