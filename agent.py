import os
import yaml
import requests
from bs4 import BeautifulSoup
from datetime import datetime

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; DealAgent/1.0)"
}

def send_telegram(msg):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("Telegram not configured")
        return
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": msg}
    )

def load_config():
    with open("config.yaml") as f:
        return yaml.safe_load(f)

def fetch_page(url):
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.text

def extract_price(soup, selector):
    el = soup.select_one(selector)
    if not el:
        raise ValueError("Price selector not found")
    return el.text.strip()

def extract_options(soup, selector):
    return [e.text.strip() for e in soup.select(selector)]

def check_target(target, product):
    html = fetch_page(target["url"])
    soup = BeautifulSoup(html, "html.parser")

    price = extract_price(soup, target["selector"]["price"])
    colors = extract_options(soup, target["selector"]["color"])
    sizes = extract_options(soup, target["selector"]["size"])

    in_stock = (
        product["preferred_color"] in colors
        and product["size"] in sizes
    )

    return {
        "price": price,
        "colors": colors,
        "sizes": sizes,
        "in_stock": in_stock
    }

def main():
    config = load_config()
    product = config["product"]

    for target in config["targets"]:
        try:
            result = check_target(target, product)

            if result["in_stock"]:
                send_telegram(
                    f"🟢 IN STOCK\n"
                    f"{product['name']}\n"
                    f"Size: {product['size']}\n"
                    f"Color: {product['preferred_color']}\n"
                    f"Price: {result['price']}\n"
                    f"{target['url']}"
                )
            else:
                print(
                    f"{datetime.utcnow()} — Not in stock. "
                    f"Colors: {result['colors']} | Sizes: {result['sizes']}"
                )

        except Exception as e:
            send_telegram(
                f"⚠️ Deal agent error on {target['name']}:\n{e}"
            )

if __name__ == "__main__":
    main()
