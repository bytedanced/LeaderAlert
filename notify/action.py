"""报警自定义动作：打开浏览器 URL 或本地文件/程序。"""
import os
import threading
import webbrowser


def run_action(action: str):
    """后台执行自定义动作，失败不影响报警主流程。

    action 以 http:// 或 https:// 开头则用默认浏览器打开，
    否则按本地文件/程序路径交给系统打开（支持 .docx / .xlsx / .exe / 快捷方式等）。
    """
    action = (action or "").strip()
    if not action:
        return

    def _run():
        try:
            if action.startswith(("http://", "https://")):
                webbrowser.open(action)
            else:
                os.startfile(action)
        except Exception:
            pass  # 打开失败仅忽略，不干扰报警通知

    threading.Thread(target=_run, daemon=True).start()
