import time
import requests
import schedule  # <-- Import the new library
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# The two functions below are perfect, no changes needed.


def fetch_espn_headlines_selenium():
    """Fetches headlines using Selenium."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/53.7.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    URL = "https://www.espncricinfo.com"
    headlines = []
    try:
        driver.get(URL)
        time.sleep(5)
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        headline_tags = soup.find_all('h3', class_='ds-text-title-s')
        for tag in headline_tags:
            headline_text = tag.get_text(strip=True)
            if headline_text:
                headlines.append(headline_text)
        return headlines[:10]
    except Exception as e:
        print(f"Bot: An error occurred during scraping: {e}")
        return []
    finally:
        driver.quit()


def send_headlines_to_api(headlines: list):
    """Sends the headlines to our FastAPI server."""
    API_ENDPOINT = "http://127.0.0.1:8000/api/internal/update-news"
    formatted_articles = [{"title": h} for h in headlines]
    try:
        print(f"Bot: Sending {len(formatted_articles)} articles to the API...")
        response = requests.post(API_ENDPOINT, json=formatted_articles)
        response.raise_for_status()
        print(f"Bot: API responded with -> {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"Bot: Could not connect to the API. Is it running? Error: {e}")

# --- New Automation Logic ---


def job():
    """The main job function that the scheduler will run."""
    print("--- Running scheduled job: Fetching and sending headlines... ---")
    latest_headlines = fetch_espn_headlines_selenium()

    if latest_headlines:
        send_headlines_to_api(latest_headlines)
    else:
        print("Bot: No headlines were found, nothing to send to API.")
    print("--- Job finished. Waiting for the next run... ---")


if __name__ == "__main__":
    print("🚀 Starting the Automated Scraper Bot 🚀")
    print("The bot will fetch news every 10 minutes. Press CTRL+C to stop.")

    # 1. Define the schedule
    # You can change this to your liking, e.g., schedule.every().hour or schedule.every().day.at("10:30")
    schedule.every(10).minutes.do(job)

    # 2. Run the job immediately for the first time
    job()

    # 3. Start the infinite loop that checks the schedule
    while True:
        schedule.run_pending()
        time.sleep(1)  # Wait for 1 second before checking again
