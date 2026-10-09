"""Gerenciador de IAs da Eva: Ollama + provedores compatíveis com OpenAI.

Não grava chaves. O modo padrão é local; nuvem somente com configuração.
Compatível com conversar(messages, tools=None, provedor_fixo=None).
"""
import copy
import json
import os
import time
import requests


class GerenciadorIAs:
    PROVEDORES = {
        "groq": ("GROQ_API_KEY", "EVA_GROQ_MODELO", "llama-3.3-70b-versatile", "https://api.groq.com/openai/v1/chat/completions"),
        "gemini": ("GEMINI_API_KEY", "EVA_GEMINI_MODELO", "gemini-2.5-flash", "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"),
        "openrouter": ("OPENROUTER_API_KEY", "EVA_OPENROUTER_MODELO", "openrouter/auto", "https://openrouter.ai/api/v1/chat/completions"),
        "mistral": ("MISTRAL_API_KEY", "EVA_MISTRAL_MODELO", "mistral-small-latest", "https://api.mistral.ai/v1/chat/completions"),
        "cerebras": ("CEREBRAS_API_KEY", "EVA_CEREBRAS_MODELO", "llama3.1-8b", "https://api.cerebras.ai/v1/chat/completions"),
        "huggingface": ("HF_TOKEN", "EVA_HF_MODELO", "", "https://router.huggingface.co/v1/chat/completions"),
    }

    def __init__(self):
        self.modo = os.getenv("EVA_IA_MODO", "local").strip().lower()
        self.modelo_local = os.getenv("EVA_OLLAMA_MODELO", "llama3.2:3b")
        self.modelo_groq = os.getenv("EVA_GROQ_MODELO", "llama-3.3-70b-versatile")
        self.chave_groq = os.getenv("GROQ_API_KEY", "").strip()
        self.ultimo_provedor = None
        self.ordem = [p.strip().lower() for p in os.getenv(
            "EVA_IA_ORDEM", "groq,gemini,openrouter,mistral,cerebras,huggingface,local"
        ).split(",") if p.strip()]

    def _ollama(self, messages, tools):
        historico = []
        for m in messages:
            copia = copy.deepcopy(m)
            copia.pop("tool_call_id", None)
            copia.pop("name", None)
            copia.pop("thinking", None)
            if copia.get("role") == "tool":
                copia.pop("tool_name", None)
            if copia.get("role") == "assistant" and copia.get("tool_calls"):
                chamadas = []
                for t in copia["tool_calls"]:
                    f = dict(t.get("function", {}))
                    if isinstance(f.get("arguments"), str):
                        try:
                            f["arguments"] = json.loads(f["arguments"])
                        except ValueError:
                            f["arguments"] = {}
                    chamadas.append({"type": "function", "function": f})
                copia["tool_calls"] = chamadas
            historico.append(copia)
        payload = {
            "model": self.modelo_local, "messages": historico, "stream": False,
            "options": {"temperature": 0.5, "num_predict": 500},
        }
        if tools:
            payload["tools"] = tools
        r = requests.post("http://localhost:11434/api/chat", json=payload, timeout=150)
        r.raise_for_status()
        self.ultimo_provedor = "ollama"
        return r.json().get("message", {})

    @staticmethod
    def _mensagens_nuvem(messages):
        """Liga respostas de ferramentas aos IDs exigidos por APIs OpenAI-compatible."""
        historico = []
        pendentes = []
        for m in messages:
            copia = copy.deepcopy(m)
            copia.pop("thinking", None)
            copia.pop("tool_name", None)
            if copia.get("role") == "assistant" and copia.get("tool_calls"):
                chamadas = []
                for i, t in enumerate(copia["tool_calls"]):
                    f = dict(t.get("function", {}))
                    if isinstance(f.get("arguments"), dict):
                        f["arguments"] = json.dumps(f["arguments"], ensure_ascii=False)
                    elif not isinstance(f.get("arguments"), str):
                        f["arguments"] = "{}"
                    identificador = t.get("id") or f"call_eva_{len(historico)}_{i}"
                    pendentes.append((identificador, f.get("name", "")))
                    chamadas.append({"id": identificador, "type": "function", "function": f})
                copia["tool_calls"] = chamadas
            if copia.get("role") == "tool":
                if not copia.get("tool_call_id"):
                    nome = m.get("tool_name") or m.get("name")
                    indice = next((i for i, (_, n) in enumerate(pendentes) if n == nome), 0)
                    if pendentes:
                        copia["tool_call_id"] = pendentes.pop(indice)[0]
                    else:
                        # Não envie respostas de ferramentas sem chamada correspondente.
                        continue
                copia.pop("name", None)
            historico.append(copia)
        return historico

    def _nuvem(self, provedor, messages, tools):
        chave_env, modelo_env, modelo_padrao, url = self.PROVEDORES[provedor]
        chave = os.getenv(chave_env, "").strip()
        if not chave:
            raise RuntimeError(f"{chave_env} não configurada")
        modelo = os.getenv(modelo_env, modelo_padrao).strip()
        if not modelo:
            raise RuntimeError(f"Configure {modelo_env} com um modelo disponível")
        payload = {
            "model": modelo,
            "messages": self._mensagens_nuvem(messages),
            "temperature": 0.5,
            "max_tokens": 500,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        headers = {"Authorization": f"Bearer {chave}", "Content-Type": "application/json"}
        if provedor == "openrouter":
            headers["HTTP-Referer"] = "https://localhost"
            headers["X-Title"] = "Eva IA Pessoal"
        resposta = requests.post(url, headers=headers, json=payload, timeout=90)
        resposta.raise_for_status()
        mensagem = resposta.json()["choices"][0]["message"]
        self.ultimo_provedor = provedor
        return mensagem

    def conversar(self, messages, tools=None, provedor_fixo=None):
        """Modo local, provedor específico ou auto/hibrido (fallback para Ollama)."""
        tools = tools or []
        modo = (provedor_fixo or self.modo).strip().lower()
        if modo == "local" or modo == "ollama":
            return self._ollama(messages, tools)
        if modo in self.PROVEDORES:
            return self._nuvem(modo, messages, tools)
        if modo not in ("auto", "hibrido", "híbrido"):
            raise ValueError("EVA_IA_MODO inválido: use local, auto, hibrido ou um provedor")
        erros = []
        for provedor in self.ordem:
            if provedor in ("local", "ollama"):
                try:
                    return self._ollama(messages, tools)
                except (requests.RequestException, ValueError, KeyError) as exc:
                    erros.append(f"ollama: {type(exc).__name__}")
                    continue
            if provedor not in self.PROVEDORES:
                continue
            if not os.getenv(self.PROVEDORES[provedor][0], "").strip():
                continue
            try:
                return self._nuvem(provedor, messages, tools)
            except (requests.RequestException, RuntimeError, ValueError, KeyError, IndexError) as exc:
                erros.append(f"{provedor}: {type(exc).__name__}")
                print(f"[Eva] {provedor} indisponível ({type(exc).__name__}); tentando próximo.")
        raise RuntimeError("Nenhum provedor disponível. " + "; ".join(erros))
