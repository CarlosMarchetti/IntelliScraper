from typing import Optional
import asyncio
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from intelliscraper.config import config
from intelliscraper.user_agents import user_agent_manager
from intelliscraper.utils.logger import get_logger

logger = get_logger(__name__)


class BrowserManager:
    def __init__(
        self,
        chrome_version: str = "134",
        locale: str = "pt-BR",
        timezone: str = "America/Sao_Paulo",
    ):
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.playwright = None
        self.chrome_version = chrome_version
        self.locale = locale
        self.timezone = timezone

    async def init(self) -> None:
        try:
            self.playwright = await async_playwright().start()

            launch_args = [
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-infobars",
                "--window-size=1920,1080",
                "--start-maximized",
                "--disable-popup-blocking",
                "--disable-features=WebRtcHideLocalIpsWithMdns",
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process",
                "--disable-site-isolation-trials",
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-background-timer-throttling",
                "--disable-backgrounding-occluded-windows",
                "--disable-renderer-backgrounding",
            ]

            proxy = {"server": config.proxy_url} if config.proxy_url else None

            self.browser = await self.playwright.chromium.launch(
                headless=config.headless,
                args=launch_args,
                proxy=proxy,
                ignore_default_args=["--enable-automation"],
            )

            user_agent = (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                f"Chrome/{self.chrome_version}.0.0.0 Safari/537.36"
            )

            accept_language = f"{self.locale},{self.locale.split('-')[0]};q=0.9,en-US;q=0.8,en;q=0.7"

            self.context = await self.browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent=user_agent,
                java_script_enabled=True,
                has_touch=False,
                is_mobile=False,
                locale=self.locale,
                timezone_id=self.timezone,
                permissions=["geolocation", "notifications"],
                color_scheme="dark",
                device_scale_factor=1,
                extra_http_headers={
                    "Accept-Language": accept_language,
                    "Accept-Encoding": "gzip, deflate, br",
                    "Accept": (
                        "text/html,application/xhtml+xml,application/xml;"
                        "q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"
                    ),
                    "Sec-Fetch-Site": "none",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-User": "?1",
                    "Sec-Fetch-Dest": "document",
                    "Upgrade-Insecure-Requests": "1",
                },
            )

            await self._inject_stealth_scripts()

            self.page = await self.context.new_page()

            logger.info(f"Browser ready (headless={config.headless}, locale={self.locale})")

        except Exception as e:
            logger.error(f"Failed to initialize browser: {e}")
            await self.close()
            raise

    async def _inject_stealth_scripts(self) -> None:
        """Injects anti-detection JavaScript before every page load."""
        await self.context.add_init_script(r"""
            (() => {
                'use strict';

                const toNative = (fn, name) => {
                    const handler = {
                        apply: function(target, thisArg, args) {
                            return Reflect.apply(target, thisArg, args);
                        }
                    };
                    const proxy = new Proxy(fn, handler);
                    Object.defineProperty(proxy, 'toString', {
                        value: () => `function ${name || fn.name || ''}() { [native code] }`,
                        writable: false,
                        configurable: false
                    });
                    return proxy;
                };

                // 1. Remove webdriver flag
                const navigatorProto = Object.getPrototypeOf(navigator);
                delete navigatorProto.webdriver;
                delete navigator.webdriver;
                Object.defineProperty(navigatorProto, 'webdriver', {
                    get: toNative(() => false, 'get webdriver'),
                    enumerable: true,
                    configurable: true
                });

                // 2. Realistic language settings
                const langs = ['pt-BR', 'pt', 'en-US', 'en'];
                Object.defineProperty(navigator, 'languages', {
                    get: toNative(() => langs, 'get languages'),
                    enumerable: true, configurable: true
                });
                Object.defineProperty(navigator, 'language', {
                    get: toNative(() => langs[0], 'get language'),
                    enumerable: true, configurable: true
                });

                // 3. Hide automation property names
                const suspiciousPatterns = [
                    /^__playwright/i, /^__pw_/i, /^playwright/i,
                    /^cdc_/i, /^\$cdc_/i, /^__selenium/i,
                    /^__webdriver/i, /^__driver/i, /^__gen_/i,
                    /domAutomation/i, /^_[a-z]+Driver/i
                ];
                const isSuspicious = (key) =>
                    typeof key === 'string' && suspiciousPatterns.some(p => p.test(key));

                const originalGetOwnPropertyNames = Object.getOwnPropertyNames;
                Object.getOwnPropertyNames = toNative(function(obj) {
                    const props = originalGetOwnPropertyNames(obj);
                    if (obj === window || obj === document || obj === navigator)
                        return props.filter(p => !isSuspicious(p));
                    return props;
                }, 'getOwnPropertyNames');

                const originalKeys = Object.keys;
                Object.keys = toNative(function(obj) {
                    const keys = originalKeys(obj);
                    if (obj === window || obj === document || obj === navigator)
                        return keys.filter(k => !isSuspicious(k));
                    return keys;
                }, 'keys');

                const originalGetOwnPropertyDescriptor = Object.getOwnPropertyDescriptor;
                Object.getOwnPropertyDescriptor = toNative(function(obj, prop) {
                    if ((obj === window || obj === document || obj === navigator) && isSuspicious(prop))
                        return undefined;
                    return originalGetOwnPropertyDescriptor(obj, prop);
                }, 'getOwnPropertyDescriptor');

                const originalHasOwnProperty = Object.prototype.hasOwnProperty;
                Object.prototype.hasOwnProperty = toNative(function(prop) {
                    if ((this === window || this === document || this === navigator) && isSuspicious(prop))
                        return false;
                    return originalHasOwnProperty.call(this, prop);
                }, 'hasOwnProperty');

                // Deep clean on interval + rAF
                const deepClean = () => {
                    try {
                        [window, document, navigator].forEach(target => {
                            if (!target) return;
                            originalGetOwnPropertyNames(target).forEach(prop => {
                                if (isSuspicious(prop)) {
                                    try { delete target[prop]; } catch(e) {
                                        try {
                                            Object.defineProperty(target, prop, {
                                                value: undefined, writable: true, configurable: true
                                            });
                                        } catch(e2) {}
                                    }
                                }
                            });
                        });
                    } catch(e) {}
                };
                deepClean();
                setInterval(deepClean, 10);
                const rafLoop = () => { deepClean(); requestAnimationFrame(rafLoop); };
                rafLoop();

                // 4. Fake plugins (empty = headless giveaway)
                if (navigator.plugins.length === 0) {
                    const createPlugin = (name, filename, description) => {
                        const p = Object.create(Plugin.prototype);
                        Object.defineProperties(p, {
                            name: { value: name, enumerable: true },
                            filename: { value: filename, enumerable: true },
                            description: { value: description, enumerable: true },
                            length: { value: 1, enumerable: true }
                        });
                        return p;
                    };
                    const pdfPlugin = createPlugin('PDF Viewer', 'internal-pdf-viewer', 'Portable Document Format');
                    const chromePlugin = createPlugin('Chrome PDF Plugin', 'internal-pdf-viewer', 'Portable Document Format');
                    const pdfMime = Object.create(MimeType.prototype);
                    Object.defineProperties(pdfMime, {
                        type: { value: 'application/pdf', enumerable: true },
                        suffixes: { value: 'pdf', enumerable: true },
                        description: { value: 'Portable Document Format', enumerable: true },
                        enabledPlugin: { value: pdfPlugin, enumerable: true }
                    });
                    pdfPlugin[0] = pdfMime;
                    pdfPlugin['application/pdf'] = pdfMime;

                    const pluginArray = Object.create(PluginArray.prototype);
                    pluginArray[0] = pdfPlugin; pluginArray[1] = chromePlugin;
                    pluginArray['PDF Viewer'] = pdfPlugin;
                    pluginArray['Chrome PDF Plugin'] = chromePlugin;
                    Object.defineProperties(pluginArray, {
                        length: { value: 2, enumerable: true },
                        item: { value: toNative(i => pluginArray[i] || null, 'item'), enumerable: true },
                        namedItem: { value: toNative(n => pluginArray[n] || null, 'namedItem'), enumerable: true },
                        refresh: { value: toNative(() => {}, 'refresh'), enumerable: true }
                    });

                    const mimeTypeArray = Object.create(MimeTypeArray.prototype);
                    mimeTypeArray[0] = pdfMime; mimeTypeArray['application/pdf'] = pdfMime;
                    Object.defineProperties(mimeTypeArray, {
                        length: { value: 1, enumerable: true },
                        item: { value: toNative(i => mimeTypeArray[i] || null, 'item'), enumerable: true },
                        namedItem: { value: toNative(n => mimeTypeArray[n] || null, 'namedItem'), enumerable: true }
                    });

                    Object.defineProperty(navigator, 'plugins', { get: () => pluginArray, configurable: true });
                    Object.defineProperty(navigator, 'mimeTypes', { get: () => mimeTypeArray, configurable: true });
                }

                // 5. chrome.runtime
                if (!window.chrome) window.chrome = {};
                if (!window.chrome.runtime) {
                    window.chrome.runtime = {
                        OnInstalledReason: { CHROME_UPDATE:'chrome_update', INSTALL:'install', SHARED_MODULE_UPDATE:'shared_module_update', UPDATE:'update' },
                        OnRestartRequiredReason: { APP_UPDATE:'app_update', OS_UPDATE:'os_update', PERIODIC:'periodic' },
                        PlatformArch: { ARM:'arm', ARM64:'arm64', MIPS:'mips', MIPS64:'mips64', X86_32:'x86-32', X86_64:'x86-64' },
                        PlatformOs: { ANDROID:'android', CROS:'cros', LINUX:'linux', MAC:'mac', OPENBSD:'openbsd', WIN:'win' },
                        RequestUpdateCheckStatus: { NO_UPDATE:'no_update', THROTTLED:'throttled', UPDATE_AVAILABLE:'update_available' }
                    };
                }
                window.chrome.app = { isInstalled: false };
                window.chrome.csi = toNative(() => ({}), 'csi');
                window.chrome.loadTimes = toNative(() => ({}), 'loadTimes');

                // 6. Permissions spoof
                if (navigator.permissions && navigator.permissions.query) {
                    const originalQuery = navigator.permissions.query;
                    navigator.permissions.query = toNative(function(parameters) {
                        if (parameters.name === 'notifications')
                            return Promise.resolve({ state: Notification.permission, name: 'notifications' });
                        return originalQuery.call(navigator.permissions, parameters);
                    }, 'query');
                }

                // 7. Canvas fingerprint noise
                const getRandomNoise = () => Math.random() * 0.0001;
                const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
                HTMLCanvasElement.prototype.toDataURL = toNative(function(...args) {
                    const ctx = this.getContext('2d');
                    if (ctx) {
                        const img = ctx.getImageData(0, 0, this.width, this.height);
                        for (let i = 0; i < img.data.length; i += 4) img.data[i] += getRandomNoise();
                        ctx.putImageData(img, 0, 0);
                    }
                    return originalToDataURL.apply(this, args);
                }, 'toDataURL');

                // 8. WebGL vendor spoof
                const getParameter = WebGLRenderingContext.prototype.getParameter;
                WebGLRenderingContext.prototype.getParameter = toNative(function(parameter) {
                    if (parameter === 37445) return 'Intel Inc.';
                    if (parameter === 37446) return 'Intel Iris OpenGL Engine';
                    return getParameter.apply(this, arguments);
                }, 'getParameter');

                // 9. Network RTT
                if (navigator.connection) {
                    Object.defineProperty(navigator.connection, 'rtt', {
                        get: toNative(() => 50, 'get rtt'), configurable: true
                    });
                }

            })();
        """)

    async def get_page_content(self, url: str, wait_until: str = "domcontentloaded") -> str:
        if not self.page:
            raise RuntimeError("Browser not initialized. Call init() first.")
        await self.page.goto(url, wait_until=wait_until, timeout=config.timeout)
        return await self.page.content()

    async def wait_for_selector(self, selector: str, timeout: int = 5000) -> bool:
        if not self.page:
            raise RuntimeError("Browser not initialized.")
        try:
            await self.page.wait_for_selector(selector, timeout=timeout)
            return True
        except Exception:
            return False

    async def execute_script(self, script: str) -> any:
        if not self.page:
            raise RuntimeError("Browser not initialized.")
        return await self.page.evaluate(script)

    async def set_viewport(self, width: int = 1920, height: int = 1080) -> None:
        if self.page:
            await self.page.set_viewport_size({"width": width, "height": height})

    async def close(self) -> None:
        components = [
            (self.page, "page"),
            (self.context, "context"),
            (self.browser, "browser"),
            (self.playwright, "playwright"),
        ]
        for component, name in components:
            if component:
                try:
                    if name == "playwright":
                        await component.stop()
                    else:
                        await component.close()
                except Exception as e:
                    logger.debug(f"Error closing {name}: {e}")
        logger.info("Browser closed.")

    async def __aenter__(self):
        await self.init()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()