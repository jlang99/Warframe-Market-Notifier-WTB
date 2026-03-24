# Warframe Market Notifier

A Python-based tool that automatically monitors [warframe.market](https://warframe.market/) for specific items and sends you an email alert when a seller lists the item at or below your target price. 

The application includes a user-friendly GUI to manage your tracked items and email configurations, alongside a background scraper that queries the market 24/7.

## Features
- **Automated Price Tracking:** Continuously checks warframe.market for items matching your target Platinum price.
- **Active Seller Filtering:** Only alerts you if the seller's status is "ingame" or "online".
- **Email Alerts:** Sends an email notification containing the item, price, seller name, and a ready-to-use copy/paste whisper message for in-game use.
- **Easy Configuration GUI:** A clean `tkinter` interface to add/remove items and set up email credentials without touching a line of code.
- **Spam Prevention:** Keeps track of order IDs it has already alerted you about to ensure you don't get duplicate emails for the same listing.

## Prerequisites
- Python 3.6 or higher
- `requests` library

## Installation
1. Clone or download this repository to your local machine.
2. Open a terminal or command prompt in the project folder.
3. Install the required dependencies:
   ```bash
   pip install requests
   ```

## Usage

### 1. Configuration (GUI)
Before running the scraper, you need to configure your email settings and add items to track.

Run the GUI script:
```bash
python gui.pyw
```
*(On Windows, you can usually just double-click the `gui.pyw` file).*

- **Email Settings:** On first launch, you will be prompted to enter your email settings. 
  - **Sender Email:** The email address sending the alerts.
  - **App Password:** If you are using Gmail, you cannot use your standard password. You must generate an **App Password** in your Google Account settings (Security > 2-Step Verification > App Passwords).
  - **Receiver Email:** The email address that will receive the alerts (can be the same as the sender).
- **Adding Items:** 
  - **URL Name:** You must use the exact URL-formatted name from warframe.market. For example, if the URL is `https://warframe.market/items/rhino_prime_set`, the URL Name is `rhino_prime_set`.
  - **Target Price:** The maximum amount of Platinum you are willing to pay.

### 2. Running the Scraper
Once your config is set up and saved, start the background scraper:

```bash
python scraper.py
```

The script will print "Warframe Market Scraper starting..." and begin checking the market API. 

**Note:** To prevent being rate-limited or IP-banned by the warframe.market API, the scraper waits **5 minutes** between each full check of your item list.

## File Structure
- `scraper.py`: The main background loop that queries the API and sends emails.
- `gui.pyw`: The graphical interface for editing `config.json`.
- `config.json`: (Generated automatically) Stores your tracking list and encrypted email settings.
- `icon.png`: (Optional) Icon used by the GUI window.

## Disclaimer
This project is not affiliated with Digital Extremes or warframe.market. Please use it responsibly and respect API rate limits.