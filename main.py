import requests
import os
from telegram.ext import Updater, CommandHandler
from dotenv import load_dotenv

# Load from .env (for local testing)
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

def send_articles(update, articles, label=""):
    if not articles:
        update.message.reply_text(f"No {label.lower()} found.")
        return
    message = f"*📢 {label}*\n\n"
    for title, url in articles:
        message += f"• [{title}]({url})\n"
    update.message.reply_text(message, parse_mode="Markdown", disable_web_page_preview=True)

# Command Handlers
def start(update, context):
    update.message.reply_text(
        "👋 Hi! I'm your job & news bot.\n"
        "Use commands like:\n"
        "`/jobs location keyword`\n"
        "`/internships location keyword`\n"
        "`/technews keyword`\n\n"
        "Example: `/jobs remote python`",
        parse_mode="Markdown"
    )

def internships(update, context):
    args = context.args
    location = args[0] if args else ""
    keywords = args[1:] if len(args) > 1 else []
    articles = fetch_news("internship", location, keywords)
    send_articles(update, articles, label="Internship News")

def jobs(update, context):
    args = context.args
    location = args[0] if args else ""
    keywords = args[1:] if len(args) > 1 else []
    jobs = fetch_remotive_jobs(location, "remote", keywords)
    send_articles(update, jobs, label="Remote Jobs")

def technews(update, context):
    args = context.args
    keywords = args if args else []
    articles = fetch_news("technology", "", keywords)
    send_articles(update, articles, label="Tech News")

def main():
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("internships", internships))
    dp.add_handler(CommandHandler("jobs", jobs))
    dp.add_handler(CommandHandler("technews", technews))
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
