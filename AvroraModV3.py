# примеры скриптов: https://docs.mitmproxy.org/stable/addons-examples/

from mitmproxy import http
import os
import shutil
from pathlib import Path


def clear_cache_directory() -> None:
    """
    Удаляет кеш-директорию приложения ARM_Student на Windows.

    Работает только на Windows:
    - Путь: %LOCALAPPDATA%\\DogmaNet\\ARM_Student

    На других ОС предполагаемые пути (НЕ поддерживаются в этом методе, доработайте сами):
    - macOS: ~/Library/Application Support/DogmaNet/ARM_Student
    - Linux: ~/.local/share/DogmaNet/ARM_Student
    """
    local_appdata = os.getenv('LOCALAPPDATA', '')
    if not local_appdata:
        return

    cache_dir = Path(local_appdata) / "DogmaNet" / "ARM_Student"

    if not cache_dir.exists():
        return

    for item in cache_dir.iterdir():
        try:
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()
        except Exception:
            pass


def load(loader):
    """
    Обработчик загрузки скрипта в mitmproxy:
    Очищает кеш-директории сразу при запуске, чтобы начать с чистого состояния.
    """
    clear_cache_directory()


def request(flow: http.HTTPFlow) -> None:
    """
    Обработчик HTTP-запросов:
    Очищает кеш-директории, чтобы файлы отображались в mitmweb'e
    """
    # Очищаем кеш при каждом запросе, чтобы не сохранялись файлы сайта
    clear_cache_directory()


def response(flow: http.HTTPFlow) -> None:
    """
    Обработчик HTTP-ответов:
    Изменяет исходный код Авроры.
    """

    # if "app.js" in flow.request.pretty_url:
    #     text = flow.response.content.decode("utf-8", errors="ignore")

    #     correct_text = text.replace(
    #         "args.content = '';",
    #         "// заменяем эту строчку на комментарий"
    #     )

    #     flow.response.content = correct_text.encode("utf-8")

    if "text/html" in flow.response.headers.get("content-type", ""):
        # Пример JavaScript-кода для включения вставки в коде, блок-схеме, алгоритме
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
            script.remove();
            alert("Вставка включена");
        })();
        </script>"""
        
        # Вставляем скрипт в head HTML-документа
        flow.response.text = flow.response.text.replace(
            "<head>", "<head>" + injection, 1 
        )
