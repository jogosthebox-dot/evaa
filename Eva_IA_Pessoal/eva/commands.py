import os
import subprocess
import webbrowser

class CommandRunner:
    # Comandos simples e permitidos. Nada destrutivo é executado automaticamente.
    def try_run(self, text):
        t = text.lower().strip()

        if t in {"abrir youtube", "abra o youtube"}:
            webbrowser.open("https://www.youtube.com")
            return "Abri o YouTube."

        if t in {"abrir google", "abra o google"}:
            webbrowser.open("https://www.google.com")
            return "Abri o Google."

        if "abrir navegador" in t:
            webbrowser.open("https://www.google.com")
            return "Abri o navegador."

        apps = {
            "bloco de notas": "notepad.exe",
            "notepad": "notepad.exe",
            "calculadora": "calc.exe",
            "calculadora do windows": "calc.exe",
        }
        for name, exe in apps.items():
            if t in {f"abrir {name}", f"abra o {name}"}:
                try:
                    subprocess.Popen(exe)
                    return f"Abri o {name}."
                except Exception as e:
                    return f"Não consegui abrir {name}: {e}"

        return None
