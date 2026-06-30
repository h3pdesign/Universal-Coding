# auto_tag_raindrop.py
import os
import requests
from dotenv import load_dotenv
from openai import OpenAI
import ctypes
from ctypes import cdll, c_char_p

# Load .env file (creates environment variables)
load_dotenv()

# === All config from .env ===
RAINDROP_TOKEN = os.getenv("RAINDROP_API_TOKEN")
XAI_API_KEY = os.getenv("XAI_API_KEY")
MAX_ARTICLES = int(os.getenv("MAX_ARTICLES", "10"))
MODEL_GROK = os.getenv("MODEL_GROK", "grok-4")
TAG_COUNT = int(os.getenv("TAG_COUNT", "5"))
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.3"))

# Validate required keys
if not RAINDROP_TOKEN or not XAI_API_KEY:
    raise EnvironmentError("RAINDROP_TOKEN and XAI_API_KEY must be set in .env file")

# Raindrop.io API
RAINDROP_API = "https://api.raindrop.io/rest/v1"
HEADERS = {"Authorization": f"Bearer {RAINDROP_TOKEN}"}

# Grok client (xAI API is OpenAI compatible)
grok_client = OpenAI(api_key=XAI_API_KEY, base_url="https://api.x.ai/v1")


# Apple Intelligence bridge (optional, macOS only)
def get_apple_tags(text: str):
    try:
        lib = cdll.LoadLibrary("./libfoundation_bridge.dylib")
        lib.generate_tags.restype = c_char_p
        lib.generate_tags.argtypes = [c_char_p]

        result = lib.generate_tags(text.encode("utf-8"))
        if result:
            tags = ctypes.string_at(result).decode("utf-8").strip()
            return [t.strip() for t in tags.split(",") if t.strip()]
    except Exception as e:
        print(f"Apple Intelligence not available ({e}), skipping local model.")
    return []


# === Functions ===
def fetch_untagged_articles():
    url = f"{RAINDROP_API}/raindrops/0"  # Collection 0 = all
    params = {
        "search": '[tag:""] type:article',  # Only untagged articles
        "perpage": MAX_ARTICLES,
        "sort": "-created",
    }
    r = requests.get(url, headers=HEADERS, params=params)
    r.raise_for_status()
    return r.json().get("items", [])


def generate_grok_tags(title: str, excerpt: str):
    prompt = f"""
    Article title: {title}
    Excerpt: {excerpt[:800] or "No excerpt"}
    
    Suggest exactly {TAG_COUNT} concise, lowercase tags (no hashtags, no explanation).
    Separate them only with commas.
    Example: python, web scraping, automation, api
    """
    try:
        resp = grok_client.chat.completions.create(
            model=MODEL_GROK,
            messages=[{"role": "user", "content": prompt.strip()}],
            max_tokens=60,
            temperature=TEMPERATURE,
        )
        tags = resp.choices[0].message.content.strip()
        return [t.strip().lower() for t in tags.split(",") if t.strip()]
    except Exception as e:
        print(f"Grok error: {e}")
        return []


def apply_tags(raindrop_id: int, tags: list):
    url = f"{RAINDROP_API}/raindrop/{raindrop_id}"
    payload = {"tags": list(set(tags))}  # deduplicate
    r = requests.put(
        url, headers={**HEADERS, "Content-Type": "application/json"}, json=payload
    )
    r.raise_for_status()
    print(f"Applied → {', '.join(tags)}")


# === Main ===
def main():
    print(f"Fetching up to {MAX_ARTICLES} untagged articles...")
    articles = fetch_untagged_articles()

    if not articles:
        print("No untagged articles found. You're all caught up!")
        return

    for item in articles:
        rid = item["_id"]
        title = item.get("title") or "Untitled"
        excerpt = item.get("excerpt") or ""

        print(f"\n→ {title}")

        # 1. Grok tags
        grok_tags = generate_grok_tags(title, excerpt)
        print(f"   Grok: {', '.join(grok_tags) or 'none'}")

        # 2. Apple Intelligence tags (local & private)
        apple_tags = get_apple_tags(f"{title}\n\n{excerpt[:1000]}")
        print(f"   Apple: {', '.join(apple_tags) or 'none'}")

        # Combine & apply
        final_tags = list(set(grok_tags + apple_tags))
        if final_tags:
            apply_tags(rid, final_tags)
        else:
            print("   No tags generated, skipping.")


if __name__ == "__main__":
    main()
