# Eva — IA pessoal para Windows

Esta é a primeira versão da sua assistente pessoal em Python.

## O que já existe
- Chat com modelo de IA via OpenAI Responses API
- Memória local em `data/memoria.json`
- Voz de saída com `pyttsx3`
- Microfone + transcrição
- Pesquisa simples na web
- Comandos básicos do Windows
- Interface gráfica com Tkinter

## Instalação

1. Instale Python 3.11 ou mais recente.
2. Abra esta pasta no CMD/PowerShell.
3. Crie e ative um ambiente virtual (recomendado):

   `python -m venv .venv`

   `.venv\Scripts\activate`

4. Instale as dependências:

   `pip install -r requirements.txt`

5. Copie `.env.example` para `.env`.
6. Coloque sua chave em `OPENAI_API_KEY`.
7. Execute:

   `python main.py`

## Importante
A API da OpenAI é um serviço pago por uso. A chave nunca deve ser colocada
diretamente no código nem compartilhada com outras pessoas.

## Próximas melhorias
- ativação por palavra ("Eva")
- voz em tempo real
- painel de configurações
- memória mais inteligente
- abrir programas personalizados
- controle de música
- integração com Discord
- atalhos e automações do Windows
