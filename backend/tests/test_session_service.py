from pathlib import Path

import pytest

from backend.app.services.session_service import SessionService


@pytest.mark.parametrize("session_id", [
    "../escape",
    "../../private/file",
    "some/session",
    "",
    "space separated",
    "equals=unsafe",
])
def test_session_service_rejects_unsafe_identifiers(tmp_path, session_id):
    svc = SessionService(storage_dir=tmp_path / "sessions")
    with pytest.raises(ValueError, match="invalid session"):
        svc.start(session_id)
    with pytest.raises(ValueError, match="invalid session"):
        svc.export_csv(session_id)
    with pytest.raises(ValueError, match="invalid session"):
        svc.persist_jsonl(session_id)


def test_session_export_stays_under_storage_directory(tmp_path):
    output_dir = tmp_path / "sessions"
    svc = SessionService(storage_dir=output_dir)
    svc.start("session-abc_123")
    path = svc.export_csv("session-abc_123")
    assert path.resolve().parent == output_dir.resolve()
    assert path.is_file()
    assert path.read_text().startswith("session_id,t_wall")
