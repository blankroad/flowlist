import sys
import webbrowser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.api import app
from app.config import HOST, PORT


def main():
    url = f"http://{HOST}:{PORT}"
    print(f"\n  FlowList running at {url}\n")
    webbrowser.open(url)
    app.run(host=HOST, port=PORT, debug=True, use_reloader=False)


if __name__ == "__main__":
    main()
