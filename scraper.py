import requests
from bs4 import BeautifulSoup


def fetch_espn_headlines_lightweight():
    """
    A lightweight scraper using requests and BeautifulSoup.
    This is much more suitable for a free server environment.
    """
    URL = "https://www.espncricinfo.com"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        print("Lightweight Scraper: Fetching URL...")
        response = requests.get(URL, headers=headers,
                                timeout=10)  # Added a timeout
        response.raise_for_status()

        print("Lightweight Scraper: Parsing HTML...")
        soup = BeautifulSoup(response.content, 'html.parser')

        headline_tags = soup.find_all('h3', class_='ds-text-title-s')

        headlines = []
        for tag in headline_tags:
            headline_text = tag.get_text(strip=True)
            if headline_text:
                headlines.append(headline_text)

        print(f"Lightweight Scraper: Found {len(headlines)} headlines.")
        return headlines[:10]

    except requests.exceptions.RequestException as e:
        print(f"Lightweight Scraper: Error fetching the URL: {e}")
        return []

# This part is no longer needed as the main API file will call the function.
# if __name__ == "__main__":
#    ...
