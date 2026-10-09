from datetime import datetime


TOOL = {
    "type": "function",
    "function": {
        "name": "hora_atual",
        "description": "Obtém a data e a hora atual do computador.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
}


def handler():
    agora = datetime.now()

    return {
        "data": agora.strftime("%d/%m/%Y"),
        "hora": agora.strftime("%H:%M:%S")
    }