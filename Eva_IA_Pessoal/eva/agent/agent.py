import json
import re
import requests

from typing import Any, Dict, List, Optional


class Agent:
    """
    Núcleo de autonomia da Eva.

    Fluxo:
    objetivo → planejamento → execução → observação
    """

    def __init__(self, brain=None, action_loader=None):
        self.brain = brain
        self.action_loader = action_loader

        self.goal = None
        self.steps: List[Dict[str, Any]] = []

        self.max_steps = 5

    # =========================================================
    # OBJETIVO
    # =========================================================

    def start(self, goal: str):
        self.goal = goal.strip()
        self.steps = []

        return {
            "success": True,
            "goal": self.goal,
            "status": "started"
        }

    # =========================================================
    # PLANEJAMENTO
    # =========================================================

    def create_plan(self):

        if not self.goal:
            return []

        if self.brain is None:
            print("[Agent] Brain não foi conectado.")
            return []

        tools = []

        if self.action_loader:
            try:
                tools = self.action_loader.list_actions()
            except Exception:
                tools = []

        tools_text = ", ".join(tools)

        prompt = f"""
Você é o planejador da assistente Eva.

OBJETIVO:
{self.goal}

FERRAMENTAS DISPONÍVEIS:
{tools_text if tools_text else "nenhuma"}

REGRAS IMPORTANTES:

1. NÃO execute nenhuma ferramenta.
2. NÃO tente responder ao usuário.
3. NÃO chame funções.
4. Apenas crie o plano.
5. Use o MENOR número possível de etapas.
6. Uma etapa deve representar uma ação REAL que a Eva precisa executar.
7. NÃO crie etapas como "retornar", "responder", "formatar",
   "analisar resultado" ou "mostrar resultado".
8. Se uma única ferramenta conseguir resolver o objetivo,
   use SOMENTE uma etapa.
9. Só crie várias etapas quando forem realmente necessárias.
10. No máximo 5 etapas.
11. Cada etapa deve ser uma ação concreta e executável.
Para o objetivo "que horas são", por exemplo, a resposta correta seria:

{{"steps":[{{"action":"hora_atual","description":"Obter a data e hora atual"}}]}}

Responda SOMENTE com JSON válido.
Não use Markdown.
Não escreva explicações.
"""

        try:

            response = requests.post(
                self.brain.url,
                json={
                    "model": self.brain.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "Você é um planejador. "
                                "Responda somente com JSON válido. "
                                "Nunca execute ferramentas."
                            )
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "num_predict": 250
                    }
                },
                timeout=120
            )

            response.raise_for_status()

            data = response.json()

            message = data.get("message", {})

            answer = message.get(
                "content",
                ""
            ).strip()

            # Alguns modelos podem colocar a resposta em thinking.
            if not answer:
                answer = message.get(
                    "thinking",
                    ""
                ).strip()

            print(
                f"[Agent] Resposta do planejador: {answer}"
            )

            plan = self._parse_plan(answer)

            if not plan:

                print(
                    "[Agent] Não consegui interpretar "
                    "o plano."
                )

                return []

            self.steps = plan[:self.max_steps]

            print(
                f"[Agent] Plano criado: "
                f"{len(self.steps)} etapa(s)"
            )

            return self.steps

        except requests.exceptions.ConnectionError:

            print(
                "[Agent] Não foi possível conectar ao Ollama."
            )

            return []

        except requests.exceptions.Timeout:

            print(
                "[Agent] O planejamento demorou demais."
            )

            return []

        except Exception as error:

            print(
                f"[Agent] Erro ao criar plano: {error}"
            )

            return []

    # =========================================================
    # INTERPRETAR PLANO
    # =========================================================

    def _parse_plan(self, answer):

        if not answer:
            return []

        answer = answer.strip()

        # -----------------------------------------------------
        # 1. JSON direto
        # -----------------------------------------------------

        try:

            data = json.loads(answer)

            if isinstance(data, dict):

                steps = data.get(
                    "steps",
                    []
                )

                if isinstance(steps, list):
                    return self._clean_steps(steps)

        except Exception:
            pass

        # -----------------------------------------------------
        # 2. JSON dentro de bloco Markdown
        # -----------------------------------------------------

        code_match = re.search(
            r"```(?:json)?\s*(\{.*?\})\s*```",
            answer,
            re.DOTALL | re.IGNORECASE
        )

        if code_match:

            try:

                data = json.loads(
                    code_match.group(1)
                )

                steps = data.get(
                    "steps",
                    []
                )

                if isinstance(steps, list):
                    return self._clean_steps(
                        steps
                    )

            except Exception:
                pass

        # -----------------------------------------------------
        # 3. Procurar objeto JSON dentro da resposta
        # -----------------------------------------------------

        start = answer.find("{")
        end = answer.rfind("}")

        if start != -1 and end != -1:

            possible_json = answer[
                start:end + 1
            ]

            try:

                data = json.loads(
                    possible_json
                )

                steps = data.get(
                    "steps",
                    []
                )

                if isinstance(steps, list):
                    return self._clean_steps(
                        steps
                    )

            except Exception:
                pass

        # -----------------------------------------------------
        # 4. Fallback para ferramenta
        # -----------------------------------------------------

        available_tools = []

        if self.action_loader:

            try:
                available_tools = (
                    self.action_loader.list_actions()
                )
            except Exception:
                pass

        answer_lower = answer.lower()

        for tool in available_tools:

            if tool.lower() in answer_lower:

                return [{
                    "action": tool,
                    "description": (
                        f"Executar a ferramenta {tool}"
                    ),
                    "result": None,
                    "success": None
                }]

        return []

    # =========================================================
    # LIMPAR ETAPAS
    # =========================================================

    def _clean_steps(self, steps):

        cleaned = []

        forbidden = {
            "retornar",
            "responder",
            "formatar",
            "mostrar_resultado",
            "mostrar resultado",
            "analisar_resultado",
            "analisar resultado"
        }

        available_tools = []

        if self.action_loader:

            try:
                available_tools = (
                    self.action_loader.list_actions()
                )
            except Exception:
                pass

        for step in steps:

            if not isinstance(step, dict):
                continue

            action = str(
                step.get(
                    "action",
                    ""
                )
            ).strip()

            description = str(
                step.get(
                    "description",
                    ""
                )
            ).strip()

            if not action:
                continue

            if action.lower() in forbidden:
                continue

            # Se temos ferramentas disponíveis,
            # não aceitamos uma ferramenta inventada.
            if available_tools:
                if action not in available_tools:
                    continue

            cleaned.append({
                "action": action,
                "description": description,
                "result": None,
                "success": None
            })

        return cleaned

    # =========================================================
    # ETAPAS MANUAIS
    # =========================================================

    def add_step(
        self,
        action: str,
        arguments: Optional[Dict[str, Any]] = None
    ):

        step = {
            "action": action,
            "arguments": arguments or {},
            "result": None,
            "success": None
        }

        self.steps.append(step)

        return step

    def complete_step(
        self,
        result: Any,
        success: bool = True
    ):

        if not self.steps:
            return

        self.steps[-1]["result"] = result
        self.steps[-1]["success"] = success

    # =========================================================
    # HISTÓRICO
    # =========================================================

    def get_history(self):
        return self.steps.copy()

    def get_last_result(self):

        if not self.steps:
            return None

        return self.steps[-1].get(
            "result"
        )

    # =========================================================
    # STATUS
    # =========================================================

    def is_running(self):
        return self.goal is not None

    def step_count(self):
        return len(self.steps)

    def can_continue(self):

        return (
            self.is_running()
            and self.step_count()
            < self.max_steps
        )

    # =========================================================
    # FINALIZAÇÃO
    # =========================================================

    def finish(self, result=None):

        final_result = {
            "success": True,
            "goal": self.goal,
            "result": result,
            "steps": self.steps
        }

        self.goal = None

        return final_result

    def cancel(self):

        self.goal = None

        return {
            "success": False,
            "status": "cancelled"
        }

    # =========================================================
    # DEBUG
    # =========================================================

    def status(self):

        return {
            "running": self.is_running(),
            "goal": self.goal,
            "steps": len(self.steps),
            "max_steps": self.max_steps
        }