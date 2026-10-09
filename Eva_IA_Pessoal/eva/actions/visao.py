"""Visão sob demanda da Eva usando Ollama multimodal.

Coloque em eva/actions/visao.py. A ferramenta NÃO clica automaticamente.
"""
import base64
import io
import json
import re

import pyautogui
import requests

OLLAMA_URL = 'http://127.0.0.1:11434/api/chat'
VISION_MODEL = 'llava:7b'


def analisar_tela(pergunta='Descreva o que aparece na tela.'):
    imagem = None
    buffer = None
    try:
        imagem = pyautogui.screenshot()
        largura, altura = imagem.size
        # Reduz o custo da imagem, preservando proporção.
        imagem.thumbnail((1280, 720))
        buffer = io.BytesIO()
        imagem.convert('RGB').save(buffer, format='JPEG', quality=75)
        foto = base64.b64encode(buffer.getvalue()).decode('ascii')
        mensagem = (
            'Você é a visão da assistente Eva. Responda em português do Brasil. '
            'Analise somente o que está visível. Não invente elementos. '
            'Se o usuário pedir a localização de um elemento, descreva onde ele está; '
            'não forneça coordenadas exatas sem certeza. '
            f'Resolução original: {largura}x{altura}. Pedido: {pergunta}'
        )
        resposta = requests.post(
            OLLAMA_URL,
            json={
                'model': VISION_MODEL,
                'stream': False,
                'messages': [{'role': 'user', 'content': mensagem, 'images': [foto]}],
                'options': {'temperature': 0.2, 'num_predict': 350},
            },
            timeout=180,
        )
        resposta.raise_for_status()
        conteudo = resposta.json().get('message', {}).get('content', '').strip()
        return {'success': True, 'answer': conteudo or 'Não consegui interpretar a imagem.'}
    except requests.exceptions.ConnectionError:
        return {'success': False, 'error': 'O Ollama não está acessível. Abra o Ollama.'}
    except requests.exceptions.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return {'success': False, 'error': f'Modelo de visão não encontrado. Execute: ollama pull {VISION_MODEL}'}
        return {'success': False, 'error': str(exc)}
    except Exception as exc:
        return {'success': False, 'error': str(exc)}
    finally:
        del imagem, buffer


TOOL = {
    'type': 'function',
    'function': {
        'name': 'visao',
        'description': 'Analisa a tela atual do computador sob demanda, sem salvar a captura nem clicar. Use quando o usuário pedir para olhar, enxergar ou identificar algo na tela.',
        'parameters': {
            'type': 'object',
            'properties': {
                'pergunta': {'type': 'string', 'description': 'O que procurar ou analisar na tela.'}
            },
            'required': ['pergunta'],
        },
    },
}


def handler(**arguments):
    return analisar_tela(arguments.get('pergunta', 'Descreva o que aparece na tela.'))


if __name__ == '__main__':
    print(json.dumps(analisar_tela(), ensure_ascii=False, indent=2))
