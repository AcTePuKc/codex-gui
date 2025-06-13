import os

from gui_pyside6.utils.codex_cmd import create_codex_cmd, path_in_env


def test_create_codex_cmd_writes_file(tmp_path):
    cmd_path = create_codex_cmd(tmp_path)
    assert cmd_path.exists()
    assert "npx codex --no-update-notifier %*" in cmd_path.read_text()


def test_path_in_env(tmp_path, monkeypatch):
    env_path = str(tmp_path)
    monkeypatch.setenv("PATH", os.pathsep.join([env_path]))
    assert path_in_env(tmp_path)
    monkeypatch.setenv("PATH", "")
    assert not path_in_env(tmp_path)
