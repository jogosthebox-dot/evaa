"""Ação de controle do computador para Eva (Windows)."""
import time
from pathlib import Path

import pyautogui

try:
    import pyperclip
except ImportError:
    pyperclip = None

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.05


def _texto(texto):
    """Digita Unicode via clipboard quando disponível."""
    texto = str(texto)
    if pyperclip is not None:
        pyperclip.copy(texto)
        pyautogui.hotkey('ctrl', 'v')
    else:
        pyautogui.write(texto, interval=0.03)
    return 'Texto inserido.'


def _screenshot(path=None):
    raiz = Path.home().resolve()
    destino = Path(path).expanduser().resolve() if path else raiz / 'Pictures' / 'eva_screenshot.png'
    if not destino.is_relative_to(raiz):
        raise ValueError('A captura só pode ser salva dentro da pasta do usuário.')
    if destino.suffix.lower() != '.png':
        raise ValueError('Use um arquivo .png para a captura.')
    destino.parent.mkdir(parents=True, exist_ok=True)
    pyautogui.screenshot().save(str(destino))
    return f'Captura salva em: {destino}'


def controlar_pc(parameters=None):
    p = parameters or {}
    acao = str(p.get('action', '')).lower().strip()
    try:
        if acao in ('mouse_position', 'posicao_mouse'):
            x, y = pyautogui.position()
            return f'Posição do mouse: ({x}, {y})'
        if acao in ('click', 'clicar', 'double_click', 'right_click'):
            args = {'button': 'right' if acao == 'right_click' else 'left',
                    'clicks': 2 if acao == 'double_click' else 1}
            if p.get('x') is not None and p.get('y') is not None:
                args.update(x=int(p['x']), y=int(p['y']))
            pyautogui.click(**args)
            return 'Clique realizado.'
        if acao in ('move', 'mover_mouse'):
            if p.get('x') is None or p.get('y') is None:
                return 'Informe x e y.'
            pyautogui.moveTo(int(p['x']), int(p['y']), duration=max(0, min(float(p.get('duration', 0.3)), 3)))
            return 'Mouse movido.'
        if acao in ('drag', 'arrastar'):
            if any(p.get(k) is None for k in ('x1', 'y1', 'x2', 'y2')):
                return 'Informe x1, y1, x2 e y2.'
            pyautogui.moveTo(int(p['x1']), int(p['y1']), duration=0.2)
            pyautogui.dragTo(int(p['x2']), int(p['y2']), duration=max(0, min(float(p.get('duration', 0.5)), 3)))
            return 'Arraste realizado.'
        if acao in ('type', 'digitar', 'smart_type', 'digitar_inteligente'):
            if acao in ('smart_type', 'digitar_inteligente') and p.get('clear_first', True):
                pyautogui.hotkey('ctrl', 'a')
                pyautogui.press('delete')
            return _texto(p.get('text', ''))
        if acao in ('hotkey', 'atalho'):
            keys = p.get('keys', '')
            keys = [k.strip().lower() for k in keys.split('+')] if isinstance(keys, str) else keys
            if not keys or any(not k for k in keys):
                return 'Informe as teclas, por exemplo ctrl+s.'
            pyautogui.hotkey(*keys)
            return 'Atalho executado.'
        if acao in ('press', 'pressionar'):
            pyautogui.press(str(p.get('key', 'enter')))
            return 'Tecla pressionada.'
        if acao in ('scroll', 'rolar'):
            direcao = str(p.get('direction', 'down')).lower()
            qtd = max(0, min(int(p.get('amount', 3)), 30))
            if direcao not in ('up', 'down', 'left', 'right'):
                return 'Direção inválida.'
            valor = qtd if direcao in ('up', 'right') else -qtd
            if direcao in ('left', 'right'):
                pyautogui.hscroll(valor)
            else:
                pyautogui.scroll(valor)
            return 'Rolagem realizada.'
        if acao in ('copy', 'copiar'):
            if pyperclip is None:
                return 'Instale pyperclip para ler a área de transferência.'
            return pyperclip.paste()
        if acao in ('paste', 'colar'):
            return _texto(p.get('text', ''))
        if acao in ('clear_field', 'limpar_campo'):
            pyautogui.hotkey('ctrl', 'a')
            pyautogui.press('delete')
            return 'Campo limpo.'
        if acao in ('screenshot', 'captura_tela'):
            return _screenshot(p.get('path'))
        if acao in ('wait', 'esperar'):
            segundos = max(0, min(float(p.get('seconds', 1)), 10))
            time.sleep(segundos)
            return f'Esperei {segundos} segundo(s).'
        return f'Ação desconhecida: {acao or "(vazia)"}'
    except pyautogui.FailSafeException:
        return 'Controle interrompido pelo mecanismo de segurança do mouse.'
    except Exception as exc:
        return f'Erro em {acao}: {exc}'


TOOL = {
    'type': 'function',
    'function': {
        'name': 'controlar_pc',
        'description': 'Controla mouse, teclado, área de transferência e capturas de tela no computador Windows. Use somente quando o usuário pedir uma ação no PC.',
        'parameters': {
            'type': 'object',
            'properties': {
                'action': {'type': 'string', 'description': 'mouse_position, click, double_click, right_click, move, drag, type, smart_type, hotkey, press, scroll, copy, paste, clear_field, screenshot, wait'},
                'text': {'type': 'string'},
                'x': {'type': 'integer'}, 'y': {'type': 'integer'},
                'x1': {'type': 'integer'}, 'y1': {'type': 'integer'},
                'x2': {'type': 'integer'}, 'y2': {'type': 'integer'},
                'keys': {'type': 'string'}, 'key': {'type': 'string'},
                'direction': {'type': 'string'}, 'amount': {'type': 'integer'},
                'duration': {'type': 'number'}, 'seconds': {'type': 'number'},
                'path': {'type': 'string'}, 'clear_first': {'type': 'boolean'}
            },
            'required': ['action']
        }
    }
}


def handler(**arguments):
    return controlar_pc(arguments)