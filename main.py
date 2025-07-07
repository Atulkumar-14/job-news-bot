import os
import requests
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, ContextTypes, CommandHandler
)
from dotenv import load_dotenv

# Enable logging
logging.basicConfig(level=logging.INFO)

# Load from .env
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

def matches_filters(text, keywords):
    text = text.lower()
    return any(kw.lower() in text for kw in keywords)

def fetch_news(query, location="", keywords=None):
    url = "https://newsapi.org/v2/everything"
    search_query = query + f" AND {location}" if location else query
    params = {
        'q': search_query,
        'language': 'en',
        'sortBy': 'publishedAt',
        'apiKey': NEWS_API_KEY,
        'pageSize': 5
    }
    response = requests.get(url, params=params)
    articles = response.json().get('articles', [])
    if keywords:
        return [(a['title'], a['url']) for a in articles if matches_filters(a['title'], keywords)]
    return [(a['title'], a['url']) for a in articles]

def fetch_remotive_jobs(location="", mode="remote", keywords=None):
    url = "https://remotive.io/api/remote-jobs"
    response = requests.get(url)
    jobs = response.json().get('jobs', [])
    filtered = []
    for job in jobs:
        if (location.lower() in job['candidate_required_location'].lower()
            and mode.lower() in job['job_type'].lower()
            and (not keywords or matches_filters(job['title'], keywords))):
            filtered.append((job['title'], job['url']))
        if len(filtered) >= 5:
            break
    return filtered

async def send_articles(update: Update, context: ContextTypes.DEFAULT_TYPE, articles, label=""):
    if not articles:
        await update.message.reply_text(f"No {label.lower()} found.")
        return
    message = f"*📢 {label}*\n\n"
    for title, url in articles:
        message += f"• [{title}]({url})\n"
    await update.message.reply_text(message, parse_mode="Markdown", disable_web_page_preview=True)

# Command Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hi! I'm your job & news bot.\n"
        "Use commands like:\n"
        "`/jobs location keyword`\n"
        "`/internships location keyword`\n"
        "`/technews keyword`\n\n"
        "Example: `/jobs remote python`",
        parse_mode="Markdown"
    )

async def internships(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    location = args[0] if args else ""
    keywords = args[1:] if len(args) > 1 else []
    articles = fetch_news("internship", location, keywords)
    await send_articles(update, context, articles, label="Internship News")

async def jobs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    location = args[0] if args else ""
    keywords = args[1:] if len(args) > 1 else []
    jobs = fetch_remotive_jobs(location, "remote", keywords)
    await send_articles(update, context, jobs, label="Remote Jobs")

async def technews(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    keywords = args if args else []
    articles = fetch_news("technology", "", keywords)
    await send_articles(update, context, articles, label="Tech News")

async def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("jobs", jobs))
    app.add_handler(CommandHandler("internships", internships))
    app.add_handler(CommandHandler("technews", technews))

    logging.basicConfig(level=logging.INFO)
    logging.info("Bot is running...")

    # Just await this directly. DO NOT wrap in asyncio.run()
    await app.run_polling()

# 👇👇👇 THIS IS THE FIX 👇👇👇
if __name__ == "__main__":
    import asyncio

    # Start the bot properly in Railway or async environments
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except RuntimeError as e:
        if "already running" in str(e):
            asyncio.ensure_future(main())
            asyncio.get_event_loop().run_forever()
        else:
            raise