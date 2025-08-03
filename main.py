import os
import asyncio
from fastapi import FastAPI, HTTPException, BackgroundTasks, Path
from pydantic import BaseModel
from typing import List
from databases import Database
from dotenv import load_dotenv
from scraper import fetch_ndtv_headlines_lightweight

load_dotenv()

# --- Configuration ---
DATABASE_URL = os.getenv("DATABASE_URL")
CRON_SECRET = os.getenv("CRON_SECRET")

if not DATABASE_URL or not CRON_SECRET:
    raise Exception(
        "FATAL: Missing DATABASE_URL or CRON_SECRET environment variables!")

database = Database(DATABASE_URL)
app = FastAPI()

# --- Data Models ---


class Article(BaseModel):
    title: str

# --- Database Lifecycle ---


@app.on_event("startup")
async def startup_database():
    try:
        await database.connect()
        query = "CREATE TABLE IF NOT EXISTS articles (id SERIAL PRIMARY KEY, title TEXT NOT NULL UNIQUE)"
        await database.execute(query=query)
        print("[API LOG]: Database connection successful.")
    except Exception as e:
        print(f"[!!! API ERROR !!!]: Database connection FAILED. Error: {e}")


@app.on_event("shutdown")
async def shutdown_database():
    await database.disconnect()
    print("[API LOG]: Database connection closed.")


# --- Scraper Logic with Full Error Handling ---
def run_scraper_job():
    try:
        print("[JOB LOG]: Background job started.")

        headlines = fetch_ndtv_headlines_lightweight()

        if not headlines:
            print("[JOB LOG]: Scraper returned no headlines. Job ending.")
            return

        values = [{"title": headline} for headline in headlines]

        # We need a new async function to run the database query
        async def update_db():
            try:
                print(
                    f"[JOB LOG]: Attempting to connect to DB and write {len(values)} articles...")
                if not database.is_connected:
                    await database.connect()

                query = "INSERT INTO articles (title) VALUES (:title) ON CONFLICT (title) DO NOTHING"
                await database.execute_many(query=query, values=values)
                print("[JOB LOG]: Database write successful.")
            except Exception as e:
                print(
                    f"[!!! JOB DB ERROR !!!]: Failed to write to database. Error: {e}")

        # Run the async database update
        asyncio.run(update_db())

    except Exception as e:
        # This will catch ANY error that happens during the job
        print(
            f"[!!! JOB FATAL ERROR !!!]: The background job crashed. Error: {e}")


# --- API Endpoints ---
@app.get("/")
def read_root():
    return {"message": "Welcome to the Cricket API!"}


@app.get("/api/news", response_model=List[Article])
async def get_news():
    query = "SELECT title FROM articles ORDER BY id DESC"
    rows = await database.fetch_all(query=query)
    return [Article(title=row["title"]) for row in rows]


@app.get("/api/internal/trigger-scrape/{secret_key}")
async def trigger_scrape(
    background_tasks: BackgroundTasks,
    secret_key: str = Path(...)
):
    if secret_key != CRON_SECRET:
        raise HTTPException(status_code=403, detail="Invalid credentials")

    background_tasks.add_task(run_scraper_job)
    return {"status": "success", "message": "Scraper job started. Check server logs for progress."}
