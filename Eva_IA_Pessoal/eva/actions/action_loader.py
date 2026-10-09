import importlib
from pathlib import Path


class ActionLoader:
    def __init__(self):
        self.actions = {}

    def load(self):
        self.actions = {}

        actions_folder = Path(__file__).parent

        for file in actions_folder.glob("*.py"):
            if file.name.startswith("_"):
                continue

            module_name = f"eva.actions.{file.stem}"

            try:
                module = importlib.import_module(module_name)

                tool = getattr(module, "TOOL", None)
                handler = getattr(module, "handler", None)

                if tool is None or handler is None:
                    continue

                if not callable(handler):
                    continue

                function_data = tool.get("function", {})
                name = function_data.get("name")

                if not name:
                    continue

                self.actions[name] = {
                    "tool": tool,
                    "handler": handler
                }

            except Exception as error:
                print(
                    f"[Eva] Não foi possível carregar "
                    f"{file.name}: {error}"
                )

        return self.actions

    def get_tools(self):
        return [
            action["tool"]
            for action in self.actions.values()
        ]

    def execute(self, name, arguments=None):
        if name not in self.actions:
            return {
                "success": False,
                "error": f"Ação '{name}' não encontrada."
            }

        handler = self.actions[name]["handler"]

        if arguments is None:
            arguments = {}

        try:
            result = handler(**arguments)

            return {
                "success": True,
                "result": result
            }

        except Exception as error:
            return {
                "success": False,
                "error": str(error)
            }

    def list_actions(self):
        return list(self.actions.keys())