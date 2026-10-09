import json
import re
from pathlib import Path
from datetime import datetime


class Memory:
    def __init__(self):
        self.path = Path("data/memoria.json")

        self.path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        self.data = {
            "memorias": [],
            "historico": []
        }

        self.load()

    # ==========================================
    # CARREGAR MEMÓRIA
    # ==========================================

    def load(self):
        if not self.path.exists():
            self.save()
            return

        try:
            data = json.loads(
                self.path.read_text(
                    encoding="utf-8"
                )
            )

            if isinstance(data, dict):
                self.data["memorias"] = data.get(
                    "memorias",
                    []
                )

                self.data["historico"] = data.get(
                    "historico",
                    []
                )

        except Exception:
            self.data = {
                "memorias": [],
                "historico": []
            }

            self.save()

    # ==========================================
    # SALVAR
    # ==========================================

    def save(self):
        self.path.write_text(
            json.dumps(
                self.data,
                ensure_ascii=False,
                indent=2
            ),
            encoding="utf-8"
        )

    # ==========================================
    # MEMÓRIA PERMANENTE
    # ==========================================

    def add(self, text):
        text = text.strip()

        if not text:
            return

        if text not in self.data["memorias"]:
            self.data["memorias"].append(text)
            self.save()

    # ==========================================
    # SALVAR MENSAGEM
    # ==========================================

    def add_message(self, role, text):
        text = text.strip()

        if not text:
            return

        message = {
            "role": role,
            "text": text,
            "timestamp": datetime.now().isoformat(
                timespec="seconds"
            )
        }

        # NÃO existe limite de mensagens.
        self.data["historico"].append(message)

        self.save()

    # ==========================================
    # CONVERSAS RECENTES
    # ==========================================

    def recent(self, limit=12):
        return self.data["historico"][-limit:]

    # ==========================================
    # NORMALIZAR TEXTO
    # ==========================================

    def _words(self, text):
        text = text.lower()

        words = re.findall(
            r"[a-záàâãéêíóôõúçü0-9]+",
            text
        )

        stopwords = {
            "a",
            "o",
            "e",
            "de",
            "do",
            "da",
            "dos",
            "das",
            "um",
            "uma",
            "uns",
            "umas",
            "eu",
            "você",
            "ele",
            "ela",
            "que",
            "me",
            "te",
            "se",
            "para",
            "por",
            "com",
            "em",
            "no",
            "na",
            "nos",
            "nas",
            "é",
            "ser",
            "foi",
            "isso",
            "esse",
            "essa",
            "como",
            "mais",
            "não",
            "sim"
        }

        return {
            word
            for word in words
            if len(word) > 2
            and word not in stopwords
        }

    # ==========================================
    # BUSCAR MEMÓRIAS RELEVANTES
    # ==========================================

    def relevant(self, query, limit=8):
        query_words = self._words(query)

        if not query_words:
            return []

        scored = []

        for item in self.data["memorias"]:
            item_words = self._words(item)

            common = query_words.intersection(
                item_words
            )

            if common:
                score = len(common)

                scored.append(
                    (score, item)
                )

        scored.sort(
            key=lambda x: x[0],
            reverse=True
        )

        return [
            item
            for _, item
            in scored[:limit]
        ]

    # ==========================================
    # BUSCAR NAS CONVERSAS ANTIGAS
    # ==========================================

    def search_history(self, query, limit=8):
        query_words = self._words(query)

        if not query_words:
            return []

        results = []

        for message in reversed(
            self.data["historico"]
        ):
            text = message.get(
                "text",
                ""
            )

            message_words = self._words(text)

            common = query_words.intersection(
                message_words
            )

            if common:
                score = len(common)

                results.append(
                    (
                        score,
                        message
                    )
                )

        results.sort(
            key=lambda x: x[0],
            reverse=True
        )

        return [
            message
            for _, message
            in results[:limit]
        ]

    # ==========================================
    # TODAS AS MEMÓRIAS
    # ==========================================

    def all(self):
        return self.data["memorias"]

    # ==========================================
    # QUANTIDADE DE MEMÓRIAS
    # ==========================================

    def memory_count(self):
        return len(
            self.data["memorias"]
        )

    # ==========================================
    # QUANTIDADE DE MENSAGENS
    # ==========================================

    def history_count(self):
        return len(
            self.data["historico"]
        )

    # ==========================================
    # LIMPAR HISTÓRICO
    # ==========================================

    def clear_history(self):
        self.data["historico"] = []
        self.save()

    # ==========================================
    # LIMPAR TUDO
    # ==========================================

    def clear_all(self):
        self.data = {
            "memorias": [],
            "historico": []
        }

        self.save()