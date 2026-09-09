"""
Tool pencarian internet menggunakan SearXNG.
"""

import requests

from config import SEARXNG_TIMEOUT_SECONDS, SEARXNG_URL

def searxng_search(
    query: str,
    max_results: int = 5,
    language: str = "all",
    time_range: str = None
) -> list:
    """
    Mencari informasi menggunakan SearXNG.

    Args:
        query: Query pencarian.
        max_results: Jumlah hasil, 1-20.
        language: Bahasa hasil pencarian.
        time_range: day, week, month, year, atau None.

    Returns:
        List dictionary berisi title, url, dan content.
    """

    if not query or not query.strip():
        raise ValueError("Query pencarian tidak boleh kosong.")

    if not 1 <= max_results <= 20:
        raise ValueError("max_results harus berada antara 1 dan 20.")

    valid_time_ranges = {
        "day",
        "week",
        "month",
        "year"
    }

    if time_range is not None and time_range not in valid_time_ranges:
        raise ValueError(
            "time_range harus berupa day, week, month, year, atau None."
        )

    params = {
        "q": query,
        "format": "json",
        "language": language,
        "number": max_results
    }

    if time_range:
        params["time_range"] = time_range

    try:
        response = requests.get(
            SEARXNG_URL,
            params=params,
            timeout=SEARXNG_TIMEOUT_SECONDS
        )

        response.raise_for_status()

        data = response.json()

        search_results = []

        for item in data.get("results", []):
            search_results.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "content": item.get("content", "")
            })

        return search_results

    except requests.exceptions.ConnectionError:
        return [{
            "error": (
                "SearXNG tidak dapat dihubungi. "
                "Pastikan server berjalan di http://localhost:8080"
            )
        }]

    except requests.exceptions.Timeout:
        return [{
            "error": "Request ke SearXNG timeout."
        }]

    except requests.exceptions.RequestException as e:
        return [{
            "error": f"Request SearXNG gagal: {e}"
        }]

    except ValueError as e:
        return [{
            "error": f"Response SearXNG tidak valid: {e}"
        }]

    except Exception as e:
        return [{
            "error": f"Error tidak terduga saat search: {e}"
        }]


__all__ = ["searxng_search"]
