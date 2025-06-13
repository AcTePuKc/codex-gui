"""Plugin that speaks text using gTTS.

The *Speak* button now reads the most recent line from ``window.output_view``.
If the output is empty, it falls back to the current prompt text.
"""

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
        """Delete the temporary MP3 file if it exists."""
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)

    current: list[Path] = [Path()]

    def on_state_changed(state: QMediaPlayer.PlaybackState) -> None:
        """Release and delete the current file when playback stops."""
        if state == QMediaPlayer.StoppedState:
            # Clear the source so the file handle can be released
            player.setSource(QUrl())
            cleanup(current[0])

    player.playbackStateChanged.connect(on_state_changed)

    def on_click() -> None:
        lines = window.output_view.toPlainText().strip().splitlines()
        text = lines[-1] if lines else ""
        if not text:
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
