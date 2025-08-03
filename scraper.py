import requests
from bs4 import BeautifulSoup


def fetch_espn_headlines_lightweight():
    """
    A lightweight scraper with extra logging.
    """
    URL = "https://www.espncricinfo.com"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        print("[SCRAPER LOG]: Attempting to fetch URL...")
        response = requests.get(URL, headers=headers, timeout=15)
        print(f"[SCRAPER LOG]: Received status code: {response.status_code}")
        response.raise_for_status()

        print("[SCRAPER LOG]: Parsing HTML content...")
        soup = BeautifulSoup(response.content, 'html.parser')

        headline_tags = soup.find_all('h3', class_='ds-text-title-s')

        headlines = []
        for tag in headline_tags:
            headline_text = tag.get_text(strip=True)
            if headline_text:
                headlines.append(headline_text)

        print(f"[SCRAPER LOG]: Successfully found {len(headlines)} headlines.")
        return headlines[:10]

    except requests.exceptions.RequestException as e:
        print(f"[!!! SCRAPER ERROR !!!]: Failed to fetch URL. Error: {e}")
        return []
    except Exception as e:
        print(
            f"[!!! SCRAPER ERROR !!!]: An unexpected error occurred during scraping. Error: {e}")
        return []
