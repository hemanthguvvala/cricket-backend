import requests
from bs4 import BeautifulSoup


def fetch_ndtv_headlines_lightweight():
    """
    A lightweight scraper to fetch headlines from the NDTV Sports Cricket section.
    """
    # This is our new, easier-to-scrape URL
    URL = "https://sports.ndtv.com/cricket/news"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        print("[SCRAPER LOG]: Attempting to fetch URL from NDTV Sports...")
        response = requests.get(URL, headers=headers, timeout=15)
        print(f"[SCRAPER LOG]: Received status code: {response.status_code}")
        response.raise_for_status()

        print("[SCRAPER LOG]: Parsing HTML content...")
        soup = BeautifulSoup(response.content, 'html.parser')

        # On this site, the headlines are inside a div with the class 'sp-nws-hd'
        headline_divs = soup.find_all('div', class_='sp-nws-hd')

        headlines = []
        for div in headline_divs:
            # The headline text is inside an 'a' tag within the div
            headline_tag = div.find('a')
            if headline_tag and headline_tag.get_text(strip=True):
                headlines.append(headline_tag.get_text(strip=True))

        print(f"[SCRAPER LOG]: Successfully found {len(headlines)} headlines.")
        return headlines[:15]  # We can get a few more from this site

    except requests.exceptions.RequestException as e:
        print(f"[!!! SCRAPER ERROR !!!]: Failed to fetch URL. Error: {e}")
        return []
    except Exception as e:
        print(
            f"[!!! SCRAPER ERROR !!!]: An unexpected error occurred. Error: {e}")
        return []
