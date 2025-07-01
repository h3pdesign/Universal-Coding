import os
import time
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

READWISE_API_TOKEN = os.getenv("READWISE_API_TOKEN")
if not READWISE_API_TOKEN:
    raise ValueError("Missing READWISE_API_TOKEN in .env file.")

READWISE_LIST_URL = "https://readwise.io/api/v3/list/"
HEADERS = {"Authorization": f"Token {READWISE_API_TOKEN}"}

def get_readwise_stats():
    all_articles = {}
    total_tags = 0
    next_page_cursor = None
    while True:
        params = {"withHtmlContent": "false"}
        if next_page_cursor:
            params["pageCursor"] = next_page_cursor
        try:
            print(f"Fetching articles page... cursor={next_page_cursor}")
            response = requests.get(READWISE_LIST_URL, headers=HEADERS, params=params, timeout=20)
            response.raise_for_status()
            data = response.json()
            for article in data.get("results", []):
                all_articles[article["id"]] = article
                tags = article.get("tags", {})
                total_tags += len(tags)
            next_page_cursor = data.get("nextPageCursor")
            if not next_page_cursor:
                break
            time.sleep(1)
        except Exception as e:
            print(f"Error fetching Readwise articles: {str(e)}")
            return None, None, None
    return len(all_articles), total_tags, all_articles

def test_readwise_connection():
    try:
        response = requests.get(READWISE_LIST_URL, headers=HEADERS, params={"pageCursor": None}, timeout=10)
        response.raise_for_status()
        data = response.json()
        print(f"Test fetch successful: Retrieved {len(data.get('results', []))} article(s) on first page")
        return True
    except Exception as e:
        print(f"Test fetch failed: {str(e)}")
        return False

def main():
    if not test_readwise_connection():
        print("Cannot proceed due to connection failure. Check credentials and try again.")
        return
    total_articles, total_tags, all_articles = get_readwise_stats()
    if total_articles is not None and total_tags is not None:
        print(f"Total number of articles in your Readwise account: {total_articles}")
        print(f"Total number of tags attached to articles: {total_tags}")
        avg_tags = total_tags / total_articles if total_articles > 0 else 0
        print(f"Average number of tags per article: {avg_tags:.2f}")
        articles_with_no_tags = sum(1 for a in all_articles.values() if not a.get("tags"))
        print(f"Number of articles with no tags: {articles_with_no_tags}")
    else:
        print("Failed to fetch Readwise stats. Check the error message above for details.")

if __name__ == "__main__":
    main()
