import os
import asyncio
import requests
import feedparser
from telethon import TelegramClient
from dotenv import load_dotenv
from flask import Flask

# Load environment variables
load_dotenv()
app = Flask('')

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL = os.getenv("CHANNEL")
COINGECKO_API = os.getenv("COINGECKO_API")

client = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

posted_news = set()
posted_prices = {}

# Crypto news feeds
NEWS_FEEDS = [
    "https://cointelegraph.com/rss",
    "https://cryptoslate.com/feed/",
    "https://www.coindesk.com/arc/outboundfeeds/rss/"
]

# Parse RSS feed
def parse_feed(url):
    try:
        feed = feedparser.parse(url)
        return feed.entries
    except:
        return []

# Fetch top 10 coins from CoinGecko
def fetch_prices():
    try:
        resp = requests.get(COINGECKO_API).json()
        prices = {}
        for coin in resp:
            prices[coin['id']] = coin['current_price']
        return prices
    except:
        return {}

# Main bot loop
async def main_loop():
    global posted_prices
    while True:
        # 1. Post News
        for feed_url in NEWS_FEEDS:
            entries = parse_feed(feed_url)
            for entry in entries:
                link = entry.link
                title = entry.title
                if link not in posted_news:
                    posted_news.add(link)
                    message = f"📰 *Crypto News*\n\n*{title}*\n{link}"
                    try:
                        await client.send_message(CHANNEL, message)
                        print(f"Posted news: {title}")
                    except:
                        pass

        # 2. Post Price Alerts (if >5% change)
        prices = fetch_prices()
        for coin, price in prices.items():
            old_price = posted_prices.get(coin)
            if old_price:
                change = abs(price - old_price) / old_price * 100
                if change >= 5:
                    message = f"💹 *Price Alert*\nCoin: {coin}\nPrice: ${price:.2f}\nChange: {change:.2f}%"
                    try:
                        await client.send_message(CHANNEL, message)
                        print(f"Posted price alert: {coin}")
                    except:
                        pass
            posted_prices[coin] = price

        await asyncio.sleep(600)  # wait 10 mins

# Flask server to keep bot alive
@app.route('/')
def home():
    return "Bot is alive!"

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(main_loop())
    from threading import Thread
    Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()
