# Auto-generated template loader
import os

HTML_FILE_PATH = os.path.join(os.path.dirname(__file__), "dashboard.html")

def get_dashboard_html() -> str:
    with open(HTML_FILE_PATH, "r", encoding="utf-8") as f:
        return f.read()
