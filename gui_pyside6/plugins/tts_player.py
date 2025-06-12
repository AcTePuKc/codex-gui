"""Plugin that speaks text using gTTS."""

from __future__ import annotations

import tempfile
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtWidgets import QPushButton

from ..backend.backend_installer import ensure_backend_installed


def register(window) -> None:
    """Register the plugin with the main window."""
    button = QPushButton("Speak")
    window.button_bar.addWidget(button)

    player = QMediaPlayer()
    audio_output = QAudioOutput()
    player.setAudioOutput(audio_output)

    def cleanup(tmp_path: Path) -> None:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)

    def on_finished() -> None:
        cleanup(current[0])

    current: list[Path] = [Path()]
    player.playbackStateChanged.connect(lambda _: on_finished())

    def on_click() -> None:
        text = window.prompt_edit.toPlainText().strip()
        if not text:
            return

        ensure_backend_installed("gtts")
        from gtts import gTTS

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            gTTS(text).save(tmp.name)
            tmp_path = Path(tmp.name)
        current[0] = tmp_path
        player.setSource(QUrl.fromLocalFile(str(tmp_path)))
        player.play()

    button.clicked.connect(on_click)
