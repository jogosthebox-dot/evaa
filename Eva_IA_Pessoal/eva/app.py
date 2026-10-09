import threading
from queue import Queue

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QApplication

from .brain import EvaBrain
from .memory import Memory
from .voice import Voice
from .commands import CommandRunner
from .ui.main_window import EvaWindow


class EvaController(QObject):

    status_changed = pyqtSignal(str)
    eva_message = pyqtSignal(str)

    def __init__(self, window):
        super().__init__()

        self.window = window

        self.memory = Memory()
        self.brain = EvaBrain(self.memory)
        self.voice = Voice()
        self.commands = CommandRunner()

        self.voice_queue = Queue()

        self.window.send_message.connect(
            self.process_message
        )

        self.window.microphone_pressed.connect(
            self.listen
        )

        self.status_changed.connect(
            self.window.set_state
        )

        self.eva_message.connect(
            self.window.add_eva_message
        )

        threading.Thread(
            target=self.voice_worker,
            daemon=True
        ).start()

    # =========================
    # MENSAGEM
    # =========================

    def process_message(self, text):

        threading.Thread(
            target=self._process_worker,
            args=(text,),
            daemon=True
        ).start()

    # =========================
    # PROCESSAMENTO
    # =========================

    def _process_worker(self, text):

        self.status_changed.emit(
            "thinking"
        )

        try:

            command_result = self.commands.try_run(
                text
            )

            if command_result:

                answer = str(
                    command_result
                )

                self.eva_message.emit(
                    answer
                )

                self.voice_queue.put(
                    answer
                )

                self.status_changed.emit(
                    "idle"
                )

                return

            full_answer = ""

            for chunk in self.brain.stream(text):

                if not chunk:
                    continue

                full_answer += chunk

            if full_answer.strip():

                self.eva_message.emit(
                    full_answer
                )

                self.voice_queue.put(
                    full_answer
                )

            self.status_changed.emit(
                "idle"
            )

        except Exception as error:

            message = (
                f"Deu um problema: {error}"
            )

            print(
                f"[Eva] Erro: {error}"
            )

            self.eva_message.emit(
                message
            )

            self.voice_queue.put(
                message
            )

            self.status_changed.emit(
                "idle"
            )

    # =========================
    # VOZ
    # =========================

    def voice_worker(self):

        while True:

            text = self.voice_queue.get()

            try:

                if text:

                    self.status_changed.emit(
                        "speaking"
                    )

                    self.voice.speak(
                        text
                    )

                    self.status_changed.emit(
                        "idle"
                    )

            except Exception as error:

                print(
                    f"[Voz] Erro: {error}"
                )

            finally:

                self.voice_queue.task_done()

    # =========================
    # MICROFONE
    # =========================

    def listen(self):

        self.status_changed.emit(
            "listening"
        )

        threading.Thread(
            target=self._listen_worker,
            daemon=True
        ).start()

    def _listen_worker(self):

        try:

            text = (
                self.voice
                .listen_and_transcribe()
            )

            if text:

                self.window.input.setText(
                    text
                )

                self.process_message(
                    text
                )

            else:

                self.status_changed.emit(
                    "idle"
                )

        except Exception as error:

            print(
                f"[Microfone] Erro: {error}"
            )

            self.status_changed.emit(
                "idle"
            )


class EvaApp:

    def __init__(self):

        self.app = QApplication.instance()

        if self.app is None:
            self.app = QApplication([])

        self.window = EvaWindow()

        self.controller = EvaController(
            self.window
        )

    def run(self):

        self.window.show()

        self.app.exec()


if __name__ == "__main__":
    EvaApp().run()