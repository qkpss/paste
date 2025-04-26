# примеры скриптов: https://docs.mitmproxy.org/stable/addons-examples/

from mitmproxy import http
import os
import shutil
from pathlib import Path


def get_cache_directories() -> dict:
    """
    Получает пути к кеш-директориям приложений ARM_Student и ARM_Student_reversed.
    
    Возвращает:
        dict: Словарь с путями к кеш-директориям или None, если AppData не существует

    Примечания по расположению кеша на разных ОС (предположительно):
    - Windows: AppData\\Local\\DogmaNet\\... (как в текущей реализации)
    - macOS: ~/Library/Caches/DogmaNet/ARM_Student/...
             или ~/Library/Application Support/DogmaNet/ARM_Student/...
    - Linux: ~/.cache/DogmaNet/ARM_Student/...
             или ~/.config/DogmaNet/ARM_Student/...
             или ~/.local/share/DogmaNet/ARM_Student/...
    """
    # Получаем путь к папке AppData/Roaming пользователя
    appdata_path = Path(os.getenv('APPDATA', ''))
    if not appdata_path.exists():
        return None

    # Формируем базовый путь к Local (AppData/Local)
    local_path = appdata_path.parent / "Local"
    
    # Пути к кеш-директориям для обеих версий приложения
    cache_dirs = {
        'ARM_Student': local_path / "DogmaNet" / "ARM_Student" / "cache" / "QtWebEngine" / "Default" / "Cache",
        'ARM_Student_patched': local_path / "DogmaNet" / "ARM_Student_reversed" / "cache" / "QtWebEngine" / "Default" / "Cache"
    }
    
    return cache_dirs


def clear_cache_directory() -> None:
    """
    Очищает кеш-директории приложений ARM_Student и ARM_Student_reversed.
    Удаляет все файлы и поддиректории в кеш-папках.
    """
    cache_dirs = get_cache_directories()
    if not cache_dirs:
        return
    
    for _, cache_dir in cache_dirs.items():
        if cache_dir and cache_dir.exists():
            # Удаляем содержимое папки
            for filename in os.listdir(cache_dir):
                file_path = cache_dir / filename
                try:
                    if file_path.is_dir():
                        shutil.rmtree(file_path)  # Удаляет папку и всё её содержимое
                    else:
                        file_path.unlink()  # Удаляет файл
                except Exception as e:
                    pass


def request(flow: http.HTTPFlow) -> None:
    """
    Обработчик HTTP-запросов:
    1. Очищает кеш-директории, чтобы файлы отображались в mitmweb'e
    2. Модифицирует заголовок Origin в запросах
    """
    # Очищаем кеш при каждом запросе, чтобы не кешировались файлы сайта
    clear_cache_directory()
        
    # Модифицируем заголовок Origin
    if "Origin" in flow.request.headers: 
        flow.request.headers["Origin"] = "https://mirea.aco-avrora.ru"


def response(flow: http.HTTPFlow) -> None:
    """
    Обработчик HTTP-ответов:
    Изменяет исходный код Авроры.
    """

    # if "app.js" in flow.request.pretty_url:
    #     flow.response.text = flow.response.text.replace(
    #         "DS.ready(function(){", 
    #         'DS.ready(function(){ alert("New app.js")', 
    #         1
    #     )

    if "text/html" in flow.response.headers.get("content-type", ""):
        # Пример JavaScript-кода для включения вставки
        injection = """
        <script>
        (function() {
            const script = document.currentScript;
            
            const _origPD = Event.prototype.preventDefault;
            Event.prototype.preventDefault = function() {
                if (this.type === 'paste' || this.type === 'drop') return;
                return _origPD.apply(this, arguments);
            };

            const _origAdd = EventTarget.prototype.addEventListener;
            EventTarget.prototype.addEventListener = function(type, fn, opts) {
                if (type === 'paste' || type === 'drop') return;
                return _origAdd.call(this, type, fn, opts);
            };

            const _origFetch = window.fetch;
            window.fetch = function(resource, init) {
                let url;

                if (resource instanceof Request) {
                    url = resource.url;
                } else {
                    url = String(resource);
                }

                try {
                    const parsed = new URL(url, location.origin);
                    const host = parsed.hostname;
                    const port = parsed.port || (parsed.protocol === 'https:' ? '443' : '80');

                    const isLocalhost = (
                        host === 'localhost' ||
                        host === '127.0.0.1' ||
                        host === '[::1]'
                    );

                    if (isLocalhost && port === '501') {
                        const delay = 5000 + Math.random() * 5000;

                        return new Promise((_, reject) => {
                            setTimeout(() => {
                                reject(new TypeError('Failed to fetch'));
                            }, delay);
                        });
                    }
                } catch (e) {}

                return _origFetch.call(this, resource, init);
            };

            Object.defineProperty(window.fetch, 'toString', {
                value: function() {
                    return 'function fetch() { [native code] }';
                },
                writable: false,
                configurable: false,
                enumerable: false
            });
            
            script.remove();
            alert("Вставка включена");
        })();
        </script>"""
        
        # Вставляем скрипт в head HTML-документа
        flow.response.text = flow.response.text.replace(
            "<head>", "<head>" + injection, 1 
        )
    
