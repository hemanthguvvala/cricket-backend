import os
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Security
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from typing import List
from databases import Database
from dotenv import load_dotenv

# Load environment variables from a .env file (for local development)
load_dotenv()

# --- Configuration ---
DATABASE_URL = os.getenv("DATABASE_URL")
# This is a secret key to prevent others from running your scraper
# We will set this in Render's environment variables
API_KEY = os.getenv("CRON_SECRET")

if not DATABASE_URL or not API_KEY:
    raise Exception(
        "Missing DATABASE_URL or CRON_SECRET environment variables!")

database = Database(DATABASE_URL)
app = FastAPI()

# --- Security ---
api_key_header = APIKeyHeader(name="X-API-Key")


async def get_api_key(api_key: str = Security(api_key_header)):
    if api_key == API_KEY:
        return api_key
    else:
        raise HTTPException(
            status_code=403, detail="Could not validate credentials")

# --- Data Models ---


class Article(BaseModel):
    title: str

# --- Database Lifecycle ---


@app.on_event("startup")
async def startup_database():
    await database.connect()
    query = "CREATE TABLE IF NOT EXISTS articles (id SERIAL PRIMARY KEY, title TEXT NOT NULL UNIQUE)"
    await database.execute(query=query)
    print("Connected to PostgreSQL and table 'articles' is ensured.")


@app.on_event("shutdown")
async def shutdown_database():
    await database.disconnect()

# --- Scraper Logic (moved from scraper.py) ---
# We move the scraper logic directly into the API file.
# This is simpler for deployment.


def run_scraper_and_update_db():
    # IMPORTANT: This is a placeholder for your actual scraper function.
    # In a real app, you would import and call your scraper function here.
    # For now, we simulate it finding new articles.
    print("Scraper job started in background...")
    # Simulate fetching headlines
    from scraper import fetch_espn_headlines_selenium  # We can import it now

    headlines = fetch_espn_headlines_selenium()

    if not headlines:
        print("Scraper found no new headlines.")
        return

    # Prepare values for bulk insert
    values = [{"title": headline} for headline in headlines]

    # This part must be async, so we run it in a separate function
    import asyncio

    async def update_db():
        query = "INSERT INTO articles (title) VALUES (:title) ON CONFLICT (title) DO NOTHING"
        await database.execute_many(query=query, values=values)
        print(
            f"Scraper finished. Updated DB with {len(values)} potential new articles.")

    asyncio.run(update_db())


# --- API Endpoints ---
@app.get("/")
def read_root():
    return {"message": "Welcome to the Cricket API!"}


@app.get("/api/news", response_model=List[Article])
async def get_news():
    query = "SELECT title FROM articles ORDER BY id DESC"
    rows = await database.fetch_all(query=query)
    return [Article(title=row["title"]) for row in rows]

# This is the NEW endpoint UptimeRobot will call


@app.post("/api/internal/trigger-scrape")
async def trigger_scrape(background_tasks: BackgroundTasks, api_key: str = Depends(get_api_key)):
    """
    A secure endpoint to trigger a background scraping job.
    """
    print("Received valid request to trigger scraper.")
    background_tasks.add_task(run_scraper_and_update_db)
    return {"status": "success", "message": "Scraper job started in the background."}
