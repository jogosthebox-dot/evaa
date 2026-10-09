import re
import json
import requests

from .web import web_search
from .actions.action_loader import ActionLoader
from .gerenciador_ias import GerenciadorIAs


class EvaBrain:

    def __init__(self, memory):
        self.memory = memory

        self.model = "llama3.2:3b"
        self.gerenciador = GerenciadorIAs()
        self.url = "http://localhost:11434/api/chat"

        # Sistema de ações da Eva
        self.action_loader = ActionLoader()
        self.actions = self.action_loader.load()

        print(
            f"[Eva] {len(self.actions)} ação(ões) carregada(s): "
            f"{self.action_loader.list_actions()}"
        )

    # =========================================================
    # MEMÓRIA
    # =========================================================

    def should_remember(self, text):
        text_lower = text.lower().strip()

        explicit_phrases = [
            "lembre que",
            "lembra que",
            "guarde que",
            "guarda que",
            "memorize que",
            "memoriza que",
            "anote que",
            "anota que",
            "não esqueça que",
            "não esquece que",
            "quero que você lembre",
            "quero que lembre",
            "quero que você guarde",
        ]

        for phrase in explicit_phrases:
            if phrase in text_lower:
                return True

        important_patterns = [
            r"\bmeu nome é\b",
            r"\bmeu nome eh\b",
            r"\beu moro em\b",
            r"\beu moro no\b",
            r"\beu moro na\b",
            r"\bminha cidade é\b",
            r"\bminha cidade eh\b",
            r"\bmeu jogo favorito\b",
            r"\bminha comida favorita\b",
            r"\bmeu filme favorito\b",
            r"\bminha série favorita\b",
            r"\bminha serie favorita\b",
            r"\bminha música favorita\b",
            r"\bminha musica favorita\b",
            r"\beu gosto de\b",
            r"\beu não gosto de\b",
            r"\beu nao gosto de\b",
            r"\bmeu objetivo é\b",
            r"\bmeu objetivo eh\b",
            r"\bquero trabalhar com\b",
            r"\bquero ser\b",
            r"\bestou estudando\b",
            r"\btrabalho como\b",
        ]

        for pattern in important_patterns:
            if re.search(pattern, text_lower):
                return True

        return False

    def extract_memory(self, text):
        text = text.strip()

        prefixes = [
            "lembre que",
            "lembra que",
            "guarde que",
            "guarda que",
            "memorize que",
            "memoriza que",
            "anote que",
            "anota que",
            "não esqueça que",
            "não esquece que",
        ]

        cleaned = text

        for prefix in prefixes:
            if cleaned.lower().startswith(prefix):
                cleaned = cleaned[len(prefix):].strip()
                break

        return cleaned

    # =========================================================
    # INTERNET
    # =========================================================

    def should_search_web(self, text):
        text_lower = text.lower().strip()

        search_phrases = [
            "pesquise",
            "pesquisa",
            "procure",
            "procura",
            "busque",
            "busca",
            "pesquisa na internet",
            "pesquise na internet",
            "procure na internet",
            "na internet",
            "na web",
            "na internet inteira",
            "veja na internet",
            "confira na internet",
        ]

        for phrase in search_phrases:
            if phrase in text_lower:
                return True

        current_phrases = [
            "hoje",
            "agora",
            "atualmente",
            "atualizado",
            "atualizada",
            "recentemente",
            "últimas notícias",
            "ultimas noticias",
            "notícias de hoje",
            "noticias de hoje",
            "notícias recentes",
            "noticias recentes",
            "ontem",
            "esta semana",
            "esse mês",
            "este mês",
            "ano passado",
            "próximo jogo",
            "proximo jogo",
        ]

        for phrase in current_phrases:
            if phrase in text_lower:
                return True

        price_phrases = [
            "quanto custa",
            "quanto está",
            "quanto esta",
            "preço",
            "preco",
            "valor atual",
            "preço atual",
            "preco atual",
            "mais barato",
            "mais barata",
            "promoção",
            "promocao",
            "em promoção",
            "em promocao",
        ]

        for phrase in price_phrases:
            if phrase in text_lower:
                return True

        finance_phrases = [
            "cotação",
            "cotacao",
            "bitcoin",
            "dólar",
            "dolar",
            "euro",
            "ações",
            "acoes",
            "bolsa",
        ]

        for phrase in finance_phrases:
            if phrase in text_lower:
                return True

        weather_phrases = [
            "clima hoje",
            "tempo hoje",
            "previsão do tempo",
            "previsao do tempo",
            "vai chover",
            "temperatura hoje",
        ]

        for phrase in weather_phrases:
            if phrase in text_lower:
                return True

        dynamic_patterns = [
            r"\bquem ganhou\b",
            r"\bquem venceu\b",
            r"\bquando vai ser\b",
            r"\bquando será\b",
            r"\bquando sera\b",
            r"\bjá saiu\b",
            r"\bja saiu\b",
            r"\blançou\b",
            r"\blancou\b",
            r"\blançamento\b",
            r"\blancamento\b",
            r"\bversão atual\b",
            r"\bversao atual\b",
            r"\búltima versão\b",
            r"\bultima versao\b",
        ]

        for pattern in dynamic_patterns:
            if re.search(pattern, text_lower):
                return True

        return False

    def search_web(self, text):
        try:
            results = web_search(text, limit=5)

            if not results:
                return ""

            web_context = (
                "\n\nINFORMAÇÕES ENCONTRADAS NA INTERNET:\n"
            )

            for index, result in enumerate(results, start=1):
                title = result.get("title", "")
                snippet = result.get("snippet", "")
                url = result.get("url", "")

                web_context += (
                    f"\nFonte {index}:\n"
                    f"Título: {title}\n"
                    f"Resumo: {snippet}\n"
                    f"Link: {url}\n"
                )

            return web_context

        except Exception:
            return ""

    # =========================================================
    # AÇÕES
    # =========================================================

    def get_relevant_actions(self, text):
        text_lower = text.lower().strip()

        relevant_actions = []

        # =====================================================
        # HORA / DATA
        # =====================================================

        time_phrases = [
            "que horas são",
            "que horas sao",
            "qual a hora",
            "qual é a hora",
            "qual e a hora",
            "me diga a hora",
            "me fala a hora",
            "me fale a hora",
            "horário atual",
            "horario atual",
            "hora atual",
            "horas agora",
            "hora agora",
            "que dia é hoje",
            "que dia e hoje",
            "qual a data",
            "qual é a data",
            "qual e a data",
            "data de hoje",
            "data atual",
            "dia de hoje",
        ]

        wants_time = any(
            phrase in text_lower
            for phrase in time_phrases
        )

        if wants_time and "hora_atual" in self.actions:
            relevant_actions.append(
                self.actions["hora_atual"]["tool"]
            )

        # =====================================================
        # NAVEGADOR
        # =====================================================

        browser_phrases = [
            "abra o google",
            "abre o google",
            "abrir o google",
            "abra o navegador",
            "abre o navegador",
            "abrir o navegador",
            "abra o opera",
            "abre o opera",
            "abrir o opera",
            "abra o opera gx",
            "abre o opera gx",
            "abrir o opera gx",

            "pesquise",
            "pesquisa",
            "pesquisar",
            "procure",
            "procura",
            "procurar",
            "busque",
            "busca",
            "buscar",

            "pesquise na internet",
            "pesquisa na internet",
            "procure na internet",
            "procura na internet",
            "busque na internet",

            "na internet",
            "na web",

            "abra esse site",
            "abra o site",
            "acesse o site",
            "entre no site",

            "clique em",
            "clica em",
            "clicar em",

            "digite no navegador",
            "digita no navegador",
            "escreva no navegador",

            "leia essa página",
            "leia a página",
            "leia essa pagina",
            "leia a pagina",
            "leia o site",
            "leia esse site",

            "volte para a página anterior",
            "volta para a página anterior",
            "volte uma página",
            "volta uma página",

            "avance uma página",
            "avança uma página",

            "recarregue a página",
            "recarrega a página",

            "abra uma nova aba",
            "nova aba",
        ]

        wants_browser = any(
            phrase in text_lower
            for phrase in browser_phrases
        )

        if (
            wants_browser
            and "browser_control" in self.actions
        ):
            relevant_actions.append(
                self.actions["browser_control"]["tool"]
            )

        pc_phrases = [
            "mouse", "cursor", "clique", "clicar", "clica", "digite", "digitar",
            "escreva", "teclado", "atalho", "pressione", "pressionar",
            "role a tela", "rolar", "captura de tela", "screenshot",
            "copie", "colar", "cole", "arraste", "arrastar", "posição do mouse",
            "posicao do mouse", "controlar_pc"
        ]
        if any(p in text_lower for p in pc_phrases) and "controlar_pc" in self.actions:
            relevant_actions.append(self.actions["controlar_pc"]["tool"])

        return relevant_actions

    # =========================================================
    # CONTEXTO
    # =========================================================

    def build_context(self, text):
        memories = self.memory.relevant(
            text,
            limit=3
        )

        old_conversations = self.memory.search_history(
            text,
            limit=1
        )

        context = ""

        if memories:
            context += "\nMEMÓRIAS RELEVANTES:\n"

            for memory in memories:
                context += f"- {memory}\n"

        if old_conversations:
            context += "\nCONVERSA ANTERIOR RELEVANTE:\n"

            for message in old_conversations:
                role = message.get(
                    "role",
                    "user"
                )

                message_text = message.get(
                    "text",
                    ""
                )

                if role == "user":
                    name = "Usuário"
                else:
                    name = "Eva"

                context += (
                    f"{name}: {message_text}\n"
                )

        return context

    # =========================================================
    # MENSAGENS
    # =========================================================

    def prepare_messages(self, text):
        if self.should_remember(text):
            memory_text = self.extract_memory(text)

            if memory_text:
                self.memory.add(memory_text)

        context = self.build_context(text)

        web_context = ""

        if self.should_search_web(text):
            web_context = self.search_web(text)

        recent = self.memory.recent(
            limit=4
        )

        conversation = []

        for message in recent:
            role = message.get(
                "role",
                "user"
            )

            message_text = message.get(
                "text",
                ""
            )

            if role not in [
                "user",
                "assistant"
            ]:
                continue

            conversation.append({
                "role": role,
                "content": message_text
            })

        conversation.append({
            "role": "user",
            "content": text
        })

        system_prompt = (
            "Seu nome é Eva. "
            "Você é uma assistente pessoal inteligente, "
            "amigável, natural e prestativa. "
            "Responda sempre em português do Brasil. "
            "Seja objetiva, mas explique quando necessário. "
            "Evite repetir frases desnecessariamente. "
            "Não comece todas as respostas com 'Claro'. "
            "Não seja robótica. "
            "Use as memórias fornecidas quando forem relevantes. "
            "Não invente informações. "
            "Não mencione o sistema de memória. "

            "Quando uma ferramenta for executada e retornar sucesso, "
            "considere a ação como REALMENTE CONCLUÍDA. "
            "Nunca diga que não conseguiu executar uma ação que "
            "uma ferramenta acabou de executar com sucesso. "
            "Nunca diga que não possui acesso à internet se uma "
            "ferramenta de navegador acabou de executar uma ação "
            "com sucesso. "
            "Confie no resultado fornecido pela ferramenta. "
        )

        if web_context:
            system_prompt += (
                "Você recebeu informações pesquisadas na internet. "
                "Use essas informações para responder à pergunta. "
                "Não invente informações que não estejam nos dados "
                "fornecidos ou que você conheça com segurança. "
                "Se as fontes forem insuficientes, diga que não "
                "foi possível confirmar completamente. "
            )

        system_prompt += context
        system_prompt += web_context

        messages = [
            {
                "role": "system",
                "content": system_prompt
            }
        ]

        messages.extend(conversation)

        return messages

    # =========================================================
    # TOOL CALLING
    # =========================================================

    def _execute_tool_calls(self, tool_calls):
        results = []

        for call in tool_calls:
            function = call.get(
                "function",
                {}
            )

            name = function.get(
                "name"
            )

            arguments = function.get(
                "arguments",
                {}
            )

            if isinstance(arguments, str):
                try:
                    arguments = json.loads(
                        arguments
                    )
                except json.JSONDecodeError:
                    arguments = {}

            print(
                f"[Eva] Executando ação: {name} "
                f"com argumentos: {arguments}"
            )

            result = self.action_loader.execute(
                name,
                arguments
            )

            results.append({
                "name": name,
                "arguments": arguments,
                "result": result
            })

        return results

    def _merge_tool_call(
        self,
        tool_calls,
        call
    ):
        function = call.get(
            "function",
            {}
        )

        index = call.get(
            "index",
            0
        )

        while len(tool_calls) <= index:
            tool_calls.append({
                "type": "function",
                "function": {
                    "name": "",
                    "arguments": {}
                }
            })

        target = tool_calls[index]

        if function.get("name"):
            target["function"]["name"] = (
                function["name"]
            )

        arguments = function.get(
            "arguments"
        )

        if arguments is not None:

            if isinstance(arguments, dict):
                target["function"]["arguments"] = (
                    arguments
                )

            elif isinstance(arguments, str):

                current = target["function"].get(
                    "arguments",
                    {}
                )

                if isinstance(current, dict):
                    try:
                        target["function"]["arguments"] = (
                            json.loads(arguments)
                        )

                    except json.JSONDecodeError:
                        target["function"]["arguments"] = (
                            arguments
                        )

                else:
                    target["function"]["arguments"] += (
                        arguments
                    )

    # =========================================================
    # STREAM
    # =========================================================

    def stream(self, text):
        full_answer = ""
        try:
            messages = self.prepare_messages(text)
            relevant_tools = self.get_relevant_actions(text)
            if relevant_tools:
                print("[Eva] Ferramentas disponíveis: " + ", ".join(
                    t["function"]["name"] for t in relevant_tools))

            for rodada in range(5):
                resposta = self.gerenciador.conversar(messages, relevant_tools)
                print(f"[Eva] Provedor: {self.gerenciador.ultimo_provedor}")
                content = resposta.get("content") or ""
                tool_calls = resposta.get("tool_calls") or []
                # Nunca anunciar sucesso antes de executar a ferramenta.
                if not tool_calls and content:
                    full_answer += content
                    yield content

                assistente = {"role": "assistant", "content": content}
                if tool_calls:
                    assistente["tool_calls"] = tool_calls
                messages.append(assistente)

                if not tool_calls:
                    break

                resultados = self._execute_tool_calls(tool_calls)
                for i, item in enumerate(resultados):
                    resultado = json.dumps(item["result"], ensure_ascii=False)
                    call_id = tool_calls[i].get("id") or f"call_eva_{i}"
                    messages.append({
                        "role": "tool", "tool_name": item["name"],
                        "tool_call_id": call_id, "content": resultado
                    })
                    print(f"[Eva] Resultado de {item['name']}: {resultado[:300]}")
                # A resposta final é gerada sem oferecer novamente a mesma ação.
                relevant_tools = []
            else:
                yield "Atingi o limite de etapas para essa solicitação."

            if full_answer.strip():
                self.memory.add_message("user", text)
                self.memory.add_message("assistant", full_answer.strip())
        except requests.exceptions.ConnectionError:
            yield "Não consegui conectar à IA. Confira o Ollama ou a internet."
        except requests.exceptions.Timeout:
            yield "A IA demorou muito para responder."
        except Exception as e:
            yield f"Deu um problema: {e}"

    # =========================================================
    # MÉTODOS PRINCIPAIS
    # =========================================================

    def think(self, text):
        answer = ""

        for chunk in self.stream(text):
            answer += chunk

        return answer.strip()

    def ask(self, text):
        return self.think(text)