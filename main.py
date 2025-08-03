import aiosqlite
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

# --- Configuration ---
DATABASE_NAME = "cricket_news.db"

# --- Data Models ---


class Article(BaseModel):
    title: str


# --- API Application ---
app = FastAPI()

# --- Database Setup & Teardown ---


@app.on_event("startup")
async def startup_database():
    """
    This function runs when the API server starts.
    It connects to the database and creates the 'articles' table if it doesn't exist.
    """
    try:
        db = await aiosqlite.connect(DATABASE_NAME)
        # The 'IF NOT EXISTS' part is crucial so we don't try to create the table every time
        await db.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL UNIQUE
            )
        """)
        await db.commit()
        await db.close()
        print("Database is ready and table 'articles' is ensured.")
    except Exception as e:
        print(f"Error during database setup: {e}")

# --- API Endpoints ---


@app.get("/")
def read_root():
    return {"message": "Welcome to the Cricket API. Now with a persistent SQLite database!"}

# This endpoint now reads directly from the database


@app.get("/api/news", response_model=List[Article])
async def get_news():
    """Returns the list of all news articles from the database."""
    try:
        db = await aiosqlite.connect(DATABASE_NAME)
        # We need a cursor to execute queries
        cursor = await db.cursor()
        # Get newest first
        await cursor.execute("SELECT title FROM articles ORDER BY id DESC")

        # Fetch all results from the query
        rows = await cursor.fetchall()

        # Format the results into our Article model
        articles = [Article(title=row[0]) for row in rows]

        await db.close()
        return articles
    except Exception as e:
        print(f"Error fetching news from DB: {e}")
        raise HTTPException(
            status_code=500, detail="Could not fetch news from database.")

# This endpoint now saves data directly to the database


@app.post("/api/internal/update-news")
async def update_news(articles: List[Article]):
    """
    Receives new articles from the scraper bot and saves them to the database.
    It uses 'INSERT OR IGNORE' to avoid duplicating articles.
    """
    try:
        db = await aiosqlite.connect(DATABASE_NAME)
        print(
            f"Received {len(articles)} articles. Saving new ones to the database.")

        # 'INSERT OR IGNORE' is a powerful SQL command. If an article with the same title
        # already exists (because of the 'UNIQUE' constraint on the title column),
        # it will simply be ignored instead of causing an error.
        for article in articles:
            await db.execute("INSERT OR IGNORE INTO articles (title) VALUES (?)", (article.title,))

        # Commit all the changes to the database file
        await db.commit()
        await db.close()

        return {"status": "success", "message": "Database updated with new articles."}
    except Exception as e:
        print(f"Error updating news in DB: {e}")
        raise HTTPException(
            status_code=500, detail="Could not update database.")
