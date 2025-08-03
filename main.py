import os
from fastapi import FastAPI, HTTPException, BackgroundTasks, Path
from pydantic import BaseModel
from typing import List
from databases import Database
from dotenv import load_dotenv
# We need to import the scraper function
from scraper import fetch_espn_headlines_selenium

# Load environment variables from a .env file (for local development)
load_dotenv()

# --- Configuration ---
DATABASE_URL = os.getenv("DATABASE_URL")
CRON_SECRET = os.getenv("CRON_SECRET")

if not DATABASE_URL or not CRON_SECRET:
    raise Exception(
        "Missing DATABASE_URL or CRON_SECRET environment variables!")

database = Database(DATABASE_URL)
app = FastAPI()

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

# --- Scraper Logic ---


def run_scraper_and_update_db():
    print("Scraper job started in background...")
    headlines = fetch_espn_headlines_selenium()

    if not headlines:
        print("Scraper found no new headlines.")
        return

    values = [{"title": headline} for headline in headlines]

    import asyncio

    async def update_db():
        query = "INSERT INTO articles (title) VALUES (:title) ON CONFLICT (title) DO NOTHING"
        await database.execute_many(query=query, values=values)
        print(
            f"Scraper finished. Updated DB with {len(values)} potential new articles.")

    # Run the async function in the existing event loop if available
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(update_db())
    except RuntimeError:  # 'RuntimeError: There is no current event loop...'
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

# --- THIS IS THE UPDATED ENDPOINT ---


@app.get("/api/internal/trigger-scrape/{secret_key}")
async def trigger_scrape(
    background_tasks: BackgroundTasks,
    secret_key: str = Path(...)  # Get the secret key from the URL path
):
    """
    A secure GET endpoint to trigger a background scraping job.
    """
    if secret_key != CRON_SECRET:
        # If the secret in the URL doesn't match our key, reject the request.
        raise HTTPException(status_code=403, detail="Invalid credentials")

    print("Received valid request to trigger scraper.")
    background_tasks.add_task(run_scraper_and_update_db)
    return {"status": "success", "message": "Scraper job started in the background."}
