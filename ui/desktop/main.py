"""
Main desktop UI for JARVIS2026 using PySide6.

Provides an interface with animated orb, transcript, and control buttons.
"""


from PySide6.QtCore import QTimer, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.events import EventEmitter, get_event_bus
from app.orchestrator import Orchestrator
from app.schemas import OrbState
from app.settings import get_settings


class OrbWidget(QWidget):
    """Animated orb status indicator."""

    def __init__(self):
        super().__init__()
        self.state = OrbState.IDLE
        self.color = QColor(100, 200, 255)  # Default blue
        self.animation_frame = 0
        self.setFixedSize(100, 100)

        # Animation timer
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self._update_animation)
        self.animation_timer.start(50)

    def set_state(self, state: OrbState) -> None:
        """Set the orb state."""
        self.state = state

        # Set color based on state
        if state == OrbState.IDLE:
            self.color = QColor(100, 200, 255)  # Blue
        elif state == OrbState.LISTENING:
            self.color = QColor(255, 200, 0)  # Yellow
        elif state == OrbState.THINKING:
            self.color = QColor(150, 100, 255)  # Purple
        elif state == OrbState.SPEAKING:
            self.color = QColor(0, 200, 100)  # Green
        elif state == OrbState.ERROR:
            self.color = QColor(255, 100, 100)  # Red

        self.update()

    def _update_animation(self) -> None:
        """Update animation frame."""
        self.animation_frame = (self.animation_frame + 1) % 60
        self.update()

    def paintEvent(self, _event) -> None:
        """Paint the orb."""
        from PySide6.QtGui import QPainter

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Calculate pulsing size
        pulse = 0.8 + 0.2 * (self.animation_frame / 60.0)
        size = int(50 * pulse)
        x = (100 - size) // 2
        y = (100 - size) // 2

        # Draw orb with glow effect
        painter.setOpacity(0.3)
        painter.setBrush(self.color)
        painter.drawEllipse(x - 10, y - 10, size + 20, size + 20)

        painter.setOpacity(1.0)
        painter.setBrush(self.color)
        painter.drawEllipse(x, y, size, size)


class StatusLabel(QLabel):
    """Status label showing current orb state."""

    def __init__(self):
        super().__init__("Ready")
        self.setStyleSheet("font-size: 14px; font-weight: bold;")

    def set_state(self, state: OrbState) -> None:
        """Update label with state."""
        state_text = {
            OrbState.IDLE: "Ready",
            OrbState.LISTENING: "Listening...",
            OrbState.THINKING: "Thinking...",
            OrbState.SPEAKING: "Speaking...",
            OrbState.ERROR: "Error",
        }
        self.setText(state_text.get(state, state.value))


class MainWindow(QMainWindow):
    """Main application window."""

    # Signals for thread safety
    state_changed = Signal(OrbState)
    transcript_updated = Signal(str)
    response_updated = Signal(str)

    def __init__(self):
        super().__init__()
        self.settings = get_settings()
        self.orchestrator = Orchestrator()
        self.emitter = EventEmitter()

        self.setWindowTitle("JARVIS2026")
        self.setGeometry(100, 100, self.settings.ui.width, self.settings.ui.height)

        # Connect signals
        self.state_changed.connect(self._on_state_changed)
        self.transcript_updated.connect(self._on_transcript_updated)
        self.response_updated.connect(self._on_response_updated)

        self._init_ui()
        self._setup_event_listeners()

    def _init_ui(self) -> None:
        """Initialize the UI layout."""
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        layout = QVBoxLayout(main_widget)

        # Top section: Orb and status
        top_layout = QHBoxLayout()

        self.orb = OrbWidget()
        top_layout.addWidget(self.orb)

        status_layout = QVBoxLayout()
        status_layout.addStretch()

        self.status_label = StatusLabel()
        status_layout.addWidget(self.status_label)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        status_layout.addWidget(self.progress)

        status_layout.addStretch()
        top_layout.addLayout(status_layout, 1)

        layout.addLayout(top_layout)

        # Middle section: Transcript
        layout.addWidget(QLabel("Transcript:"))
        self.transcript = QTextEdit()
        self.transcript.setReadOnly(True)
        self.transcript.setMaximumHeight(150)
        layout.addWidget(self.transcript)

        # Response section
        layout.addWidget(QLabel("Response:"))
        self.response = QTextEdit()
        self.response.setReadOnly(True)
        layout.addWidget(self.response)

        # Bottom section: Controls
        button_layout = QHBoxLayout()

        self.push_to_talk_btn = QPushButton("Push to Talk")
        self.push_to_talk_btn.clicked.connect(self._on_push_to_talk)
        self.push_to_talk_btn.setMinimumHeight(40)
        button_layout.addWidget(self.push_to_talk_btn)

        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self._on_clear)
        button_layout.addWidget(self.clear_btn)

        layout.addLayout(button_layout)

        main_widget.setLayout(layout)

    def _setup_event_listeners(self) -> None:
        """Setup event bus listeners."""
        get_event_bus()
        # Listen for orb state changes
        async def on_orb_state_changed(event):
            state = OrbState(event.data.get("state"))
            self.state_changed.emit(state)

        # This would be registered as async callback
        # For now, we skip this as it requires async event handling in UI

    def _on_state_changed(self, state: OrbState) -> None:
        """Handle orb state change."""
        self.orb.set_state(state)
        self.status_label.set_state(state)

    def _on_transcript_updated(self, text: str) -> None:
        """Handle transcript update."""
        self.transcript.append(text)

    def _on_response_updated(self, text: str) -> None:
        """Handle response update."""
        self.response.setText(text)

    def _on_push_to_talk(self) -> None:
        """Handle push to talk button."""
        self.state_changed.emit(OrbState.LISTENING)
        self.transcript_updated.emit("User: [recording...]")

        # Simulate transcription
        QTimer.singleShot(2000, self._simulate_transcription)

    def _simulate_transcription(self) -> None:
        """Simulate speech-to-text and processing."""
        test_input = "What are the main agents in the system?"

        self.transcript.clear()
        self.transcript_updated.emit(f"User: {test_input}")
        self.state_changed.emit(OrbState.THINKING)

        # Simulate processing
        QTimer.singleShot(1500, self._simulate_response)

    def _simulate_response(self) -> None:
        """Simulate agent response."""
        response = """JARVIS2026 has 5 main agents:

    1. **Director** - Routes requests and makes decisions
    2. **Dev** - Handles code analysis and modifications
    3. **CTO** - Provides technical architecture guidance
    4. **Business** - Assesses business impact and priorities
    5. **Notes** - Manages memory and journaling

    Each agent has specific capabilities and tools."""

        self.response_updated.emit(response)
        self.state_changed.emit(OrbState.SPEAKING)

        # Simulate speaking duration
        QTimer.singleShot(3000, self._on_done_speaking)

    def _on_done_speaking(self) -> None:
        """Handle end of speaking."""
        self.state_changed.emit(OrbState.IDLE)

    def _on_clear(self) -> None:
        """Clear all text areas."""
        self.transcript.clear()
        self.response.clear()
        self.state_changed.emit(OrbState.IDLE)


def main() -> None:
    """Run the JARVIS2026 UI."""
    app = QApplication([])

    window = MainWindow()
    window.show()

    app.exec()


if __name__ == "__main__":
    main()
