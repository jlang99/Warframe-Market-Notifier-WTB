#!/usr/bin/env python3
#Above is for linux distributions running in the main enovironment.
# This file should run a server to be 24/7

import time
import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests

# Keep track of orders we've already alerted about to avoid email spam
ALERTED_ORDERS = set()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")

def load_config():
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

def send_alert_email(config, item_name, price, seller_name, whisper_msg):
    email_cfg = config["email"]
    
    msg = MIMEMultipart()
    msg['From'] = email_cfg["sender"]
    msg['To'] = email_cfg["receiver"]
    msg['Subject'] = f"WF Market Alert: {item_name} for {price}p"

    body = (
        f"Item: {item_name}\n"
        f"Price: {price} platinum\n"
        f"Seller: {seller_name}\n\n"
        f"Copy/Paste in-game:\n"
        f"{whisper_msg}"
    )
    
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        server = smtplib.SMTP(email_cfg["smtp_server"], email_cfg["smtp_port"])
        server.starttls()
        server.login(email_cfg["sender"], email_cfg["password"])
        server.sendmail(email_cfg["sender"], email_cfg["receiver"], msg.as_string())
        server.quit()
        print(f"Alert sent for {item_name} at {price}p!")
    except Exception as e:
        print(f"Failed to send email: {e}")

def check_market():
    config = load_config()
    print("Checking market...")
    
    for item in config["items_to_track"]:
        # Respect the API rate limit of 3 requests per second
        time.sleep(0.34)

        url_name = item["url_name"]
        target_price = item["target_price"]
        
        # Query the Warframe Market API
        url = f"https://api.warframe.market/v2/orders/item/{url_name}/top"
        headers = {"Language": "en", "Accept": "application/json"}
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch {url_name}: {e}")
            continue

        data = response.json()
        sell_orders = data.get("data", {}).get("sell", [])
        
        # Filter for sell orders where user is "ingame" or "online"
        valid_orders = [
            o for o in sell_orders 
            if o["user"]["status"] in ["ingame", "online"]
        ]
        
        if not valid_orders:
            continue
            
        # Sort to find the absolute cheapest available
        valid_orders.sort(key=lambda x: x["platinum"])
        cheapest_order = valid_orders[0]
        print(cheapest_order)
        
        price = cheapest_order["platinum"]
        order_id = cheapest_order["id"]
        seller_name = cheapest_order["user"]["ingameName"]
        
        # Only alert if it meets our price target and hasn't been emailed yet
        if price <= target_price and order_id not in ALERTED_ORDERS:
            display_name = url_name.replace("_", " ").title()
            whisper_msg = f'/w {seller_name} Hi! I want to buy: "{display_name}" for {price} platinum. (warframe.market)'
            
            send_alert_email(config, display_name, price, seller_name, whisper_msg)
            ALERTED_ORDERS.add(order_id)

if __name__ == "__main__":
    print("Warframe Market Scraper starting...")
    while True:
        try:
            check_market()
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
        
        # Wait 1 minute between checks to avoid rate-limiting
        time.sleep(60)
