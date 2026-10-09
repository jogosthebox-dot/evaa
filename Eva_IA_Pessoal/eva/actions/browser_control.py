import asyncio
import concurrent.futures
import os
import threading
from pathlib import Path
from typing import Optional

from playwright.async_api import async_playwright


OPERA_PATH = (
    r"C:\Users\Usuário\AppData\Local\Programs"
    r"\Opera GX\opera.exe"
)


def _normalize_url(url: str) -> str:
    url = (url or "").strip()

    if not url:
        return "https://www.google.com"

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    return url


class BrowserSession:
    def __init__(self):
        self.loop = None
        self.thread = None
        self.ready = threading.Event()

        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

        self._start()

    def _start(self):
        self.thread = threading.Thread(
            target=self._run_loop,
            daemon=True
        )

        self.thread.start()

        self.ready.wait(timeout=20)

    def _run_loop(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        self.loop.create_task(self._initialize())

        self.loop.run_forever()

    async def _initialize(self):
        try:
            self.playwright = await async_playwright().start()

            if not os.path.exists(OPERA_PATH):
                raise FileNotFoundError(
                    f"Opera GX não encontrado em: {OPERA_PATH}"
                )

            profile = (
                Path(os.environ.get("LOCALAPPDATA", "."))
                / "Eva"
                / "OperaProfile"
            )

            profile.mkdir(
                parents=True,
                exist_ok=True
            )

            self.context = (
                await self.playwright.chromium
                .launch_persistent_context(
                    user_data_dir=str(profile),
                    executable_path=OPERA_PATH,
                    headless=False,
                    args=[
                        "--start-maximized"
                    ],
                    viewport=None
                )
            )

            pages = self.context.pages

            if pages:
                self.page = pages[0]
            else:
                self.page = await self.context.new_page()

            self.ready.set()

            print("[Eva] Opera GX conectado ao navegador.")

        except Exception as error:
            print(
                f"[Eva] Erro ao iniciar Opera GX: {error}"
            )

            self.ready.set()

    def _run(self, coroutine):
        if self.loop is None:
            raise RuntimeError(
                "Loop do navegador não foi iniciado."
            )

        future = asyncio.run_coroutine_threadsafe(
            coroutine,
            self.loop
        )

        return future.result(timeout=60)

    async def _go_to(self, url):
        await self.page.goto(
            _normalize_url(url),
            wait_until="domcontentloaded",
            timeout=30000
        )

        return {
            "url": self.page.url,
            "title": await self.page.title()
        }

    def go_to(self, url):
        return self._run(
            self._go_to(url)
        )

    async def _search(self, query, engine="google"):
        engines = {
            "google": "https://www.google.com/search?q={}",
            "bing": "https://www.bing.com/search?q={}",
            "duckduckgo": (
                "https://html.duckduckgo.com/html/?q={}"
            )
        }

        engine = (engine or "google").lower()

        search_url = engines.get(
            engine,
            engines["google"]
        )

        from urllib.parse import quote

        url = search_url.format(
            quote(query)
        )

        return await self._go_to(url)

    def search(self, query, engine="google"):
        return self._run(
            self._search(
                query,
                engine
            )
        )

    async def _click(self, selector):
        await self.page.locator(
            selector
        ).first.click(timeout=10000)

        return {
            "success": True,
            "url": self.page.url
        }

    def click(self, selector):
        return self._run(
            self._click(selector)
        )

    async def _smart_click(self, description):
        locator = self.page.get_by_text(
            description,
            exact=False
        ).first

        await locator.click(timeout=10000)

        return {
            "success": True,
            "description": description,
            "url": self.page.url
        }

    def smart_click(self, description):
        return self._run(
            self._smart_click(description)
        )

    async def _type_text(
        self,
        selector,
        text,
        clear_first=True
    ):
        locator = self.page.locator(
            selector
        ).first

        if clear_first:
            await locator.fill(text)
        else:
            await locator.type(text)

        return {
            "success": True
        }

    def type_text(
        self,
        selector,
        text,
        clear_first=True
    ):
        return self._run(
            self._type_text(
                selector,
                text,
                clear_first
            )
        )

    async def _smart_type(
        self,
        description,
        text,
        clear_first=True
    ):
        locator = self.page.get_by_role(
            "textbox",
            name=description
        ).first

        if clear_first:
            await locator.fill(text)
        else:
            await locator.type(text)

        return {
            "success": True
        }

    def smart_type(
        self,
        description,
        text,
        clear_first=True
    ):
        return self._run(
            self._smart_type(
                description,
                text,
                clear_first
            )
        )

    async def _scroll(
        self,
        direction="down",
        amount=500
    ):
        amount = int(amount)

        if direction.lower() == "up":
            amount = -abs(amount)
        else:
            amount = abs(amount)

        await self.page.mouse.wheel(
            0,
            amount
        )

        return {
            "success": True,
            "direction": direction,
            "amount": amount
        }

    def scroll(
        self,
        direction="down",
        amount=500
    ):
        return self._run(
            self._scroll(
                direction,
                amount
            )
        )

    async def _press(self, key):
        await self.page.keyboard.press(key)

        return {
            "success": True,
            "key": key
        }

    def press(self, key):
        return self._run(
            self._press(key)
        )

    async def _get_text(self):
        text = await self.page.locator(
            "body"
        ).inner_text(
            timeout=10000
        )

        return text[:12000]

    def get_text(self):
        return self._run(
            self._get_text()
        )

    async def _get_url(self):
        return self.page.url

    def get_url(self):
        return self._run(
            self._get_url()
        )

    async def _new_tab(self, url=""):
        page = await self.context.new_page()

        self.page = page

        if url:
            await page.goto(
                _normalize_url(url),
                wait_until="domcontentloaded",
                timeout=30000
            )

        return {
            "success": True,
            "url": page.url
        }

    def new_tab(self, url=""):
        return self._run(
            self._new_tab(url)
        )

    async def _close_tab(self):
        if self.page:
            await self.page.close()

        pages = self.context.pages

        if pages:
            self.page = pages[-1]
        else:
            self.page = await self.context.new_page()

        return {
            "success": True,
            "url": self.page.url
        }

    def close_tab(self):
        return self._run(
            self._close_tab()
        )

    async def _back(self):
        await self.page.go_back(
            wait_until="domcontentloaded",
            timeout=30000
        )

        return {
            "success": True,
            "url": self.page.url
        }

    def back(self):
        return self._run(
            self._back()
        )

    async def _forward(self):
        await self.page.go_forward(
            wait_until="domcontentloaded",
            timeout=30000
        )

        return {
            "success": True,
            "url": self.page.url
        }

    def forward(self):
        return self._run(
            self._forward()
        )

    async def _reload(self):
        await self.page.reload(
            wait_until="domcontentloaded",
            timeout=30000
        )

        return {
            "success": True,
            "url": self.page.url
        }

    def reload(self):
        return self._run(
            self._reload()
        )

    async def _screenshot(self, path=""):
        if not path:
            path = (
                Path.cwd()
                / "eva_browser.png"
            )

        path = str(path)

        await self.page.screenshot(
            path=path,
            full_page=True
        )

        return {
            "success": True,
            "path": path
        }

    def screenshot(self, path=""):
        return self._run(
            self._screenshot(path)
        )


_session: Optional[BrowserSession] = None
_session_lock = threading.Lock()


def _get_session():
    global _session

    with _session_lock:
        if _session is None:
            _session = BrowserSession()

    return _session


TOOL = {
    "type": "function",
    "function": {
        "name": "browser_control",
        "description": (
            "Controla o navegador Opera GX da Eva. "
            "Pode abrir páginas, pesquisar na internet, "
            "clicar, digitar, rolar, pressionar teclas, "
            "ler páginas, abrir abas, voltar, avançar, "
            "recarregar e tirar screenshots."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": (
                        "Ação a executar."
                    ),
                    "enum": [
                        "open",
                        "go_to",
                        "search",
                        "click",
                        "smart_click",
                        "type",
                        "smart_type",
                        "scroll",
                        "press",
                        "get_text",
                        "read",
                        "get_url",
                        "new_tab",
                        "close_tab",
                        "back",
                        "forward",
                        "reload",
                        "screenshot"
                    ]
                },
                "url": {
                    "type": "string"
                },
                "query": {
                    "type": "string"
                },
                "engine": {
                    "type": "string",
                    "enum": [
                        "google",
                        "bing",
                        "duckduckgo"
                    ]
                },
                "selector": {
                    "type": "string"
                },
                "text": {
                    "type": "string"
                },
                "description": {
                    "type": "string"
                },
                "direction": {
                    "type": "string",
                    "enum": [
                        "up",
                        "down"
                    ]
                },
                "amount": {
                    "type": "integer"
                },
                "key": {
                    "type": "string"
                },
                "path": {
                    "type": "string"
                },
                "clear_first": {
                    "type": "boolean"
                }
            },
            "required": [
                "action"
            ]
        }
    }
}


def handler(
    action,
    url="",
    query="",
    engine="google",
    selector="",
    text="",
    description="",
    direction="down",
    amount=500,
    key="Enter",
    path="",
    clear_first=True,
    **kwargs
):
    try:
        browser = _get_session()

        action = (
            action or ""
        ).lower().strip()

        if action in (
            "open",
            "go_to"
        ):
            result = browser.go_to(url)

        elif action == "search":
            result = browser.search(
                query,
                engine
            )

        elif action == "click":
            result = browser.click(
                selector
            )

        elif action == "smart_click":
            result = browser.smart_click(
                description
            )

        elif action == "type":
            result = browser.type_text(
                selector,
                text,
                clear_first
            )

        elif action == "smart_type":
            result = browser.smart_type(
                description,
                text,
                clear_first
            )

        elif action == "scroll":
            result = browser.scroll(
                direction,
                amount
            )

        elif action == "press":
            result = browser.press(
                key
            )

        elif action in (
            "get_text",
            "read"
        ):
            result = browser.get_text()

        elif action == "get_url":
            result = browser.get_url()

        elif action == "new_tab":
            result = browser.new_tab(
                url
            )

        elif action == "close_tab":
            result = browser.close_tab()

        elif action == "back":
            result = browser.back()

        elif action == "forward":
            result = browser.forward()

        elif action == "reload":
            result = browser.reload()

        elif action == "screenshot":
            result = browser.screenshot(
                path
            )

        else:
            return {
                "success": False,
                "error": (
                    f"Ação de navegador desconhecida: "
                    f"{action}"
                )
            }

        return {
            "success": True,
            "result": result
        }

    except Exception as error:
        return {
            "success": False,
            "error": str(error)
        }