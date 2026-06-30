import logging
import os
import sys
import time
from typing import Any, Dict, List

import requests
from dotenv import load_dotenv

logger = logging.getLogger()
logger.setLevel(logging.INFO)

if not logger.handlers:
    file_handler = logging.FileHandler("raindrop_tagging.log")
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler(sys.stderr)
    stream_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(stream_handler)

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

RAINDROP_API_TOKEN = os.getenv("RAINDROP_API_TOKEN")
GROK_API_KEY = os.getenv("GROK_API_KEY")

if not RAINDROP_API_TOKEN:
    raise ValueError("Missing RAINDROP_API_TOKEN in .env file.")

RAINDROP_API_URL = "https://api.raindrop.io/rest/v1/raindrops/0"
RAINDROP_UPDATE_URL = "https://api.raindrop.io/rest/v1/raindrop/"
HEADERS = {
    "Authorization": f"Bearer {RAINDROP_API_TOKEN}",
    "Content-Type": "application/json",
}


def fetch_raindrops_to_tag() -> Dict[int, Dict[str, Any]]:
    """Fetch Raindrop items that currently have fewer than 3 tags."""
    logger.info("Fetching Raindrop items with fewer than 3 tags...")
    all_raindrops: Dict[int, Dict[str, Any]] = {}
    page = 0

    while True:
        params = {"perpage": 50, "page": page}
        try:
            response = requests.get(RAINDROP_API_URL, headers=HEADERS, params=params, timeout=20)
            response.raise_for_status()
            data = response.json()
            items = data.get("items", [])

            for item in items:
                tags = item.get("tags", [])
                if len(tags) < 3:
                    all_raindrops[item["_id"]] = item

            if not items or len(items) < 50:
                break

            page += 1
            time.sleep(1)
        except Exception as exc:
            logger.error("Error fetching Raindrops: %s", exc)
            break

    logger.info("Fetched %s raindrops needing tags.", len(all_raindrops))
    return all_raindrops


def update_raindrop_tags(raindrop: Dict[str, Any], new_tags: List[str]) -> bool:
    """Update the tags for one Raindrop item."""
    raindrop_id = raindrop.get("_id")
    if not raindrop_id:
        logger.warning("Raindrop missing _id, skipping.")
        return False

    payload = {"tags": new_tags}
    try:
        response = requests.put(
            f"{RAINDROP_UPDATE_URL}{raindrop_id}",
            headers=HEADERS,
            json=payload,
            timeout=20,
        )
        if response.status_code in (200, 201):
            logger.info("Updated tags for raindrop %s: %s", raindrop_id, new_tags)
            return True

        logger.error(
            "Failed to update tags for raindrop %s: %s %s",
            raindrop_id,
            response.status_code,
            response.text,
        )
        return False
    except requests.exceptions.RequestException as exc:
        logger.error("Exception updating tags for raindrop %s: %s", raindrop_id, exc)
        return False


def generate_tags_with_grok(title: str, excerpt: str, url: str) -> List[str]:
    """Request tags from the Grok API and fall back to basic keyword tags if needed."""
    content = f"{title} {excerpt}".strip()
    if not GROK_API_KEY:
        logger.error("GROK_API_KEY not found; using fallback tags only.")
        return generate_fallback_tags(content)

    try:
        endpoint = "https://api.xai.com/v1/generate"
        headers = {
            "Authorization": f"Bearer {GROK_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "grok-4-fast-reasoning",
            "prompt": f"Generate up to 3 relevant tags for the article: {content[:500]}...",
            "max_tokens": 60,
            "temperature": 0.3,
        }
        response = requests.post(endpoint, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        generated_text = ""
        choices = data.get("choices")
        if isinstance(choices, list) and choices:
            first = choices[0]
            if isinstance(first, dict):
                generated_text = first.get("text") or first.get("message", {}).get("content") or ""

        if not generated_text and isinstance(data.get("output"), list):
            parts = []
            for item in data["output"]:
                if isinstance(item, dict):
                    parts.append(item.get("content", ""))
                elif isinstance(item, str):
                    parts.append(item)
            generated_text = "\n".join(part for part in parts if part)

        if not generated_text:
            generated_text = data.get("text", "") or data.get("result", "")

        generated_text = (generated_text or "").strip()
        tags = [tag.strip() for part in generated_text.splitlines() for tag in part.split(",") if tag.strip()]

        if tags:
            logger.info("Grok returned tags for '%s': %s", title, tags)
            return tags[:3]

        logger.warning("Grok returned no tags for '%s'; using fallback tags.", title)
        return generate_fallback_tags(content)
    except requests.exceptions.RequestException as exc:
        logger.error("Grok request failed for '%s': %s", title, exc)
        return generate_fallback_tags(content)


def generate_fallback_tags(content: str) -> List[str]:
    """Create simple keyword-based tags if the API is unavailable."""
    content_lower = content.lower()
    general_tags: List[str] = []

    if any(word in content_lower for word in ["technology", "software", "ai", "artificial intelligence", "computer"]):
        general_tags.extend(["technology", "software"])
    elif any(word in content_lower for word in ["finance", "economy", "money", "market"]):
        general_tags.extend(["finance", "economy"])
    elif any(word in content_lower for word in ["education", "learning", "school", "university"]):
        general_tags.extend(["education", "learning"])
    elif any(word in content_lower for word in ["entertainment", "movie", "music", "game"]):
        general_tags.extend(["entertainment", "media"])
    else:
        general_tags.extend(["information", "content"])

    if any(word in content_lower for word in ["ai", "artificial intelligence"]):
        specific_tag = "artificial intelligence"
    elif any(word in content_lower for word in ["climate", "environment"]):
        specific_tag = "climate change"
    elif any(word in content_lower for word in ["design", "apple"]):
        specific_tag = "product design"
    elif any(word in content_lower for word in ["healthcare", "hospital"]):
        specific_tag = "healthcare industry"
    elif any(word in content_lower for word in ["stock", "investment"]):
        specific_tag = "financial markets"
    elif "student" in content_lower:
        specific_tag = "educational resources"
    elif any(word in content_lower for word in ["movie", "film"]):
        specific_tag = "film industry"
    else:
        specific_tag = "relevant subject"

    tags = list(dict.fromkeys(general_tags[:2] + [specific_tag]))
    while len(tags) < 3:
        tags.append("content")
    return tags


def tag_raindrops(raindrops: Dict[int, Dict[str, Any]]) -> int:
    """Tag each Raindrop item with a unique set of tags."""
    tagged_count = 0
    for raindrop_id, raindrop in raindrops.items():
        current_tags = raindrop.get("tags", []) or []
        title = raindrop.get("title", "")
        excerpt = raindrop.get("excerpt", "")
        logger.info("Processing raindrop %s: %s", raindrop_id, title)

        new_tags = generate_tags_with_grok(title, excerpt, raindrop.get("link", ""))
        final_tags = list(dict.fromkeys((current_tags or []) + new_tags))
        while len(final_tags) < 3:
            final_tags.append("content")

        if update_raindrop_tags(raindrop, final_tags):
            tagged_count += 1

        time.sleep(1)

    logger.info("Tagged %s raindrops.", tagged_count)
    return tagged_count


def main() -> None:
    try:
        logger.info("Script started")
        raindrops = fetch_raindrops_to_tag()
        if not raindrops:
            logger.warning("No raindrops need tagging.")
            print("No raindrops need tagging.")
            return

        tagged_count = tag_raindrops(raindrops)
        print(f"Tagged {tagged_count} raindrops.")
        logger.info("Script finished")
    except KeyboardInterrupt:
        logger.info("Script interrupted by user")
        sys.exit(0)
    except Exception as exc:
        logger.error("Unexpected error: %s", exc)
        print(f"Error: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
