import subprocess
import urllib.parse


def open_url(url: str) -> str:
    url = url.strip()

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        subprocess.Popen(
            ["xdg-open", url],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        return f"Opening {url}."

    except Exception as exc:
        return f"I couldn't open the URL: {exc}"


def search_web(query: str) -> str:
    query = query.strip()

    if not query:
        return "Tell me what you want to search for."

    encoded = urllib.parse.quote_plus(query)

    url = (
        "https://www.google.com/search?q="
        + encoded
    )

    return open_url(url)
