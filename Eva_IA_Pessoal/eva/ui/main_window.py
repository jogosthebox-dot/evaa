import sys
import math

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QPainter, QPen, QBrush
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
)


class EvaCore(QWidget):

    def __init__(self):
        super().__init__()

        self.setMinimumSize(350, 350)

        self.angle = 0
        self.state = "idle"

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(30)

    def set_state(self, state):
        self.state = state
        self.update()

    def animate(self):
        self.angle += 3

        if self.angle >= 360:
            self.angle = 0

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)

        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing
        )

        center = self.rect().center()

        # Velocidade e intensidade conforme estado
        if self.state == "thinking":
            speed = 2
            intensity = 14

        elif self.state == "speaking":
            speed = 5
            intensity = 22

        elif self.state == "listening":
            speed = 7
            intensity = 28

        else:
            speed = 1
            intensity = 7

        pulse = (
            math.sin(
                math.radians(
                    self.angle * speed
                )
            ) + 1
        ) * intensity / 2

        # =========================
        # ANEL EXTERNO
        # =========================

        pen = QPen(
            Qt.GlobalColor.cyan
        )

        pen.setWidth(2)

        painter.setPen(pen)
        painter.setBrush(
            Qt.BrushStyle.NoBrush
        )

        size = int(
            210 + pulse
        )

        painter.drawEllipse(
            int(
                center.x()
                - size / 2
            ),
            int(
                center.y()
                - size / 2
            ),
            size,
            size,
        )

        # =========================
        # ANEL INTERNO
        # =========================

        pen.setWidth(3)
        painter.setPen(pen)

        painter.drawEllipse(
            int(
                center.x() - 75
            ),
            int(
                center.y() - 75
            ),
            150,
            150,
        )

        # =========================
        # NÚCLEO
        # =========================

        core_size = int(
            25 + pulse / 2
        )

        painter.setPen(
            Qt.PenStyle.NoPen
        )

        painter.setBrush(
            QBrush(
                Qt.GlobalColor.cyan
            )
        )

        painter.drawEllipse(
            int(
                center.x()
                - core_size / 2
            ),
            int(
                center.y()
                - core_size / 2
            ),
            core_size,
            core_size,
        )

        # =========================
        # ÓRBITAS
        # =========================

        radius = int(
            105 + pulse / 3
        )

        for i in range(3):

            orbit_angle = (
                self.angle
                + i * 120
            )

            radians = math.radians(
                orbit_angle
            )

            x = (
                center.x()
                + math.cos(radians)
                * radius
            )

            y = (
                center.y()
                + math.sin(radians)
                * radius
            )

            painter.drawEllipse(
                int(x - 4),
                int(y - 4),
                8,
                8,
            )


class EvaWindow(QMainWindow):

    send_message = pyqtSignal(str)
    microphone_pressed = pyqtSignal()

    def __init__(self):
        super().__init__()

        self.setWindowTitle(
            "EVA"
        )

        self.resize(
            1200,
            800
        )

        self.setStyleSheet("""
            QMainWindow {
                background-color: #05080d;
            }

            QLabel {
                color: #d8faff;
            }

            QFrame {
                background-color: #0a1018;
                border: 1px solid #16303b;
                border-radius: 12px;
            }

            QTextEdit {
                background-color: #070c12;
                color: #cceff5;
                border: 1px solid #16303b;
                border-radius: 10px;
                padding: 12px;
                font-size: 14px;
            }

            QLineEdit {
                background-color: #070c12;
                color: #ffffff;
                border: 1px solid #1b3d49;
                border-radius: 10px;
                padding: 12px;
                font-size: 14px;
            }

            QLineEdit:focus {
                border: 1px solid #00d9ff;
            }

            QPushButton {
                background-color: #0c1821;
                color: #d8faff;
                border: 1px solid #1b3d49;
                border-radius: 10px;
                padding: 10px 16px;
                font-size: 14px;
            }

            QPushButton:hover {
                background-color: #102633;
                border: 1px solid #00d9ff;
            }

            QPushButton:pressed {
                background-color: #153746;
            }
        """)

        central = QWidget()

        self.setCentralWidget(
            central
        )

        main_layout = QVBoxLayout(
            central
        )

        main_layout.setContentsMargins(
            25,
            20,
            25,
            20
        )

        main_layout.setSpacing(
            15
        )

        # =========================
        # CABEÇALHO
        # =========================

        header = QHBoxLayout()

        title = QLabel(
            "EVA"
        )

        title.setFont(
            QFont(
                "Segoe UI",
                28,
                QFont.Weight.Bold
            )
        )

        self.status = QLabel(
            "●  SISTEMA ONLINE"
        )

        self.status.setFont(
            QFont(
                "Segoe UI",
                11
            )
        )

        header.addWidget(
            title
        )

        header.addStretch()

        header.addWidget(
            self.status
        )

        main_layout.addLayout(
            header
        )

        # =========================
        # ÁREA CENTRAL
        # =========================

        center = QHBoxLayout()

        center.setSpacing(
            15
        )

        # =========================
        # NÚCLEO
        # =========================

        core = QFrame()

        core_layout = QVBoxLayout(
            core
        )

        core_layout.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.eva_core = EvaCore()

        self.core_status = QLabel(
            "AGUARDANDO COMANDO"
        )

        self.core_status.setFont(
            QFont(
                "Segoe UI",
                12
            )
        )

        self.core_status.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        core_layout.addWidget(
            self.eva_core
        )

        core_layout.addWidget(
            self.core_status
        )

        center.addWidget(
            core,
            2
        )

        # =========================
        # CONVERSA
        # =========================

        chat = QFrame()

        chat_layout = QVBoxLayout(
            chat
        )

        chat_title = QLabel(
            "CONVERSA"
        )

        chat_title.setFont(
            QFont(
                "Segoe UI",
                14,
                QFont.Weight.Bold
            )
        )

        self.chat = QTextEdit()

        self.chat.setReadOnly(
            True
        )

        self.chat.setPlaceholderText(
            "As conversas com a Eva aparecerão aqui..."
        )

        chat_layout.addWidget(
            chat_title
        )

        chat_layout.addWidget(
            self.chat
        )

        # =========================
        # CAMPO DE TEXTO
        # =========================

        input_layout = QHBoxLayout()

        self.input = QLineEdit()

        self.input.setPlaceholderText(
            "Fale com a Eva..."
        )

        self.input.returnPressed.connect(
            self.handle_send
        )

        send_button = QPushButton(
            "Enviar"
        )

        send_button.clicked.connect(
            self.handle_send
        )

        mic_button = QPushButton(
            "🎤"
        )

        mic_button.setFixedWidth(
            55
        )

        mic_button.clicked.connect(
            self.handle_microphone
        )

        input_layout.addWidget(
            self.input
        )

        input_layout.addWidget(
            mic_button
        )

        input_layout.addWidget(
            send_button
        )

        chat_layout.addLayout(
            input_layout
        )

        center.addWidget(
            chat,
            3
        )

        main_layout.addLayout(
            center,
            1
        )

        # =========================
        # RODAPÉ
        # =========================

        footer = QHBoxLayout()

        memory = QLabel(
            "MEMÓRIA  •  ONLINE"
        )

        browser = QLabel(
            "NAVEGADOR  •  PRONTO"
        )

        voice = QLabel(
            "VOZ  •  PRONTA"
        )

        footer.addWidget(
            memory
        )

        footer.addStretch()

        footer.addWidget(
            browser
        )

        footer.addStretch()

        footer.addWidget(
            voice
        )

        main_layout.addLayout(
            footer
        )

    # =============================
    # ENVIAR MENSAGEM
    # =============================

    def handle_send(self):

        text = self.input.text().strip()

        if not text:
            return

        self.chat.append(
            f"<b>Você:</b> {text}"
        )

        self.input.clear()

        self.set_state(
            "thinking"
        )

        self.send_message.emit(
            text
        )

    # =============================
    # MICROFONE
    # =============================

    def handle_microphone(self):

        self.set_state(
            "listening"
        )

        self.microphone_pressed.emit()

    # =============================
    # ESTADO
    # =============================

    def set_state(self, state):

        states = {
            "idle": "AGUARDANDO COMANDO",
            "thinking": "PROCESSANDO...",
            "speaking": "EVA FALANDO...",
            "listening": "OUVINDO..."
        }

        self.core_status.setText(
            states.get(
                state,
                "AGUARDANDO COMANDO"
            )
        )

        self.eva_core.set_state(
            state
        )

    # =============================
    # RESPOSTA DA EVA
    # =============================

    def add_eva_message(
        self,
        text
    ):

        self.chat.append(
            f"<b>EVA:</b> {text}"
        )

        self.set_state(
            "speaking"
        )


def start_ui():

    app = QApplication(
        sys.argv
    )

    window = EvaWindow()

    window.show()

    sys.exit(
        app.exec()
    )


if __name__ == "__main__":
    start_ui()