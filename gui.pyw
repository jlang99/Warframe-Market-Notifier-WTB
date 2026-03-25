#!/usr/bin/env python3
#Above is for linux distributions running in the main enovironment.

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import os
import requests
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
ICON_PATH = os.path.join(BASE_DIR, "icon.png")

DEFAULT_CONFIG = {
    "email": {
        "sender": "",
        "password": "",
        "receiver": "",
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587
    },
    "items_to_track": []
}

class ConfigGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Warframe Market Scraper Config")
        self.root.geometry("550x450")
        
        # Set window icon if the file exists
        try:
            icon_img = tk.PhotoImage(file=ICON_PATH)
            self.root.iconphoto(True, icon_img)
        except tk.TclError:
            pass
        
        self.config = self.load_config()
        
        self.build_ui()
        self.refresh_list()
        
        # Prompt for email setup on startup if it's missing
        if not self.config["email"]["sender"] or not self.config["email"]["password"]:
            self.open_email_settings(force=True)
            
    def load_config(self):
        if not os.path.exists(CONFIG_PATH):
            # Create default config if none exists
            with open(CONFIG_PATH, "w") as f:
                json.dump(DEFAULT_CONFIG, f, indent=4)
            return DEFAULT_CONFIG.copy()
        else:
            with open(CONFIG_PATH, "r") as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    return DEFAULT_CONFIG.copy()

    def save_config(self):
        with open(CONFIG_PATH, "w") as f:
            json.dump(self.config, f, indent=4)

    def build_ui(self):
        # Top Frame: Add Item
        add_frame = ttk.LabelFrame(self.root, text="Add / Edit Tracked Item")
        add_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Label(add_frame, text="URL Name:").grid(row=0, column=0, padx=5, pady=10)
        self.url_name_var = tk.StringVar()
        ttk.Entry(add_frame, textvariable=self.url_name_var, width=25).grid(row=0, column=1, padx=5, pady=10)
        
        ttk.Button(add_frame, text="Add Item", command=self.add_item).grid(row=0, column=2, padx=10, pady=10)
        
        # Middle Frame: Scrollable List
        list_frame = ttk.LabelFrame(self.root, text="Currently Tracked Items")
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Treeview is perfect for creating a clean tabular list
        self.tree = ttk.Treeview(list_frame, columns=("url_name", "target_price"), show="headings")
        self.tree.heading("url_name", text="Item URL Name (e.g., rhino_prime_set)")
        self.tree.heading("target_price", text="Target Price (Plat)")
        self.tree.column("url_name", width=300)
        self.tree.column("target_price", width=150, anchor="center")
        
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.pack(side="right", fill="y", pady=5)
        
        # Bottom Frame: Controls
        control_frame = ttk.Frame(self.root)
        control_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Button(control_frame, text="Remove Selected", command=self.remove_item).pack(side="left")
        ttk.Button(control_frame, text="Edit Price", command=self.edit_price).pack(side="left", padx=10)
        ttk.Button(control_frame, text="Research Price", command=self.research_price).pack(side="left")
        ttk.Button(control_frame, text="Email Settings", command=lambda: self.open_email_settings(force=False)).pack(side="right")

    def _fetch_and_prompt_price(self, url_name):
        try:
            # Query the Warframe Market API for the cheapest current order
            url = f"https://api.warframe.market/v2/orders/item/{url_name}"
            headers = {"Language": "en", "Accept": "application/json"}
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
        
            orders = data.get("data", [])
            if isinstance(orders, dict):
                sell_orders = orders.get("sell", [])
            else:
                sell_orders = [o for o in orders if o.get("type") == "sell"]
            
            if not sell_orders:
                messagebox.showerror("Error", f"No active sell orders found for '{url_name}'.")
                return None
                
            def parse_date(date_str):
                if not date_str:
                    return datetime.min.replace(tzinfo=timezone.utc)
                try:
                    base_str = date_str.split('.')[0].split('+')[0]
                    if base_str.endswith('Z'):
                        base_str = base_str[:-1]
                    return datetime.strptime(base_str, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
                except Exception:
                    return datetime.min.replace(tzinfo=timezone.utc)

            now = datetime.now(timezone.utc)
            
            # Sort to find the absolute cheapest available
            sell_orders.sort(key=lambda x: x["platinum"])
            
            cheapest_any = sell_orders[0]
            cheapest_7d = None
            cheapest_24h = None
            cheapest_now = None
            
            for o in sell_orders:
                status = o.get("user", {}).get("status", "offline")
                last_seen_str = o.get("user", {}).get("lastSeen", "")
                last_seen = parse_date(last_seen_str)
                
                # Check currently online
                if status in ["ingame", "online"]:
                    if cheapest_now is None:
                        cheapest_now = o
                
                # Check within 24 hours
                if (now - last_seen).total_seconds() <= 86400 or status in ["ingame", "online"]:
                    if cheapest_24h is None:
                        cheapest_24h = o
                        
                # Check within 7 days
                if (now - last_seen).total_seconds() <= 604800 or status in ["ingame", "online"]:
                    if cheapest_7d is None:
                        cheapest_7d = o
            
            options = []
            
            if cheapest_any:
                print(cheapest_any)
                last_seen_str = cheapest_any.get("user", {}).get("lastSeen", "")
                print(last_seen_str)
                ls_date = parse_date(last_seen_str)
                ls_display = ls_date.strftime("%Y-%m-%d %H:%M UTC") if ls_date != datetime.min.replace(tzinfo=timezone.utc) else "Unknown"
                options.append({
                    "label": f"Absolute cheapest: {cheapest_any['platinum']}p (Last online: {ls_display})",
                    "price": int(cheapest_any['platinum'])
                })
            
            if cheapest_7d:
                options.append({
                    "label": f"Cheapest (online within 7 days): {cheapest_7d['platinum']}p",
                    "price": int(cheapest_7d['platinum'])
                })
                
            if cheapest_24h:
                options.append({
                    "label": f"Cheapest (online within 24 hours): {cheapest_24h['platinum']}p",
                    "price": int(cheapest_24h['platinum'])
                })
                
            if cheapest_now:
                options.append({
                    "label": f"Cheapest (currently online): {cheapest_now['platinum']}p",
                    "price": int(cheapest_now['platinum'])
                })
            
            dialog = tk.Toplevel(self.root)
            dialog.title("Select Target Price")
            dialog.geometry("450x250")
            dialog.transient(self.root)
            dialog.grab_set()
            
            ttk.Label(dialog, text=f"Select the target price for '{url_name}':").pack(pady=10)
            
            selected_price = tk.IntVar()
            if options:
                selected_price.set(options[0]["price"])
                
            frame = ttk.Frame(dialog)
            frame.pack(fill="both", expand=True, padx=20)
            
            for opt in options:
                ttk.Radiobutton(frame, text=opt["label"], variable=selected_price, value=opt["price"]).pack(anchor="w", pady=5)
                
            result = {"price": None}
            
            def on_confirm():
                result["price"] = selected_price.get()
                dialog.destroy()
                
            def on_cancel():
                dialog.destroy()
                
            btn_frame = ttk.Frame(dialog)
            btn_frame.pack(pady=10)
            
            ttk.Button(btn_frame, text="Confirm", command=on_confirm).pack(side="left", padx=5)
            ttk.Button(btn_frame, text="Cancel", command=on_cancel).pack(side="left", padx=5)
            
            self.root.wait_window(dialog)
            
            return result["price"]
                
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Failed to fetch data for '{url_name}':\n{e}")
            return None

    def add_item(self):
        url_name = self.url_name_var.get().strip().lower() # Standardize inputs
        
        if not url_name:
            messagebox.showerror("Error", "URL Name is required.")
            return
            
        price = self._fetch_and_prompt_price(url_name)
        if price is None:
            return

        # Update price if item already exists
        for item in self.config["items_to_track"]:
            if item["url_name"] == url_name:
                item["target_price"] = price
                self.save_config()
                self.refresh_list()
                self.url_name_var.set("")
                return
        
        # Otherwise, append a new item
        self.config["items_to_track"].append({
            "url_name": url_name,
            "target_price": price
        })
        self.save_config()
        self.refresh_list()
        
        # Clear inputs
        self.url_name_var.set("")

    def remove_item(self):
        selected = self.tree.selection()
        if not selected:
            return
            
        item_values = self.tree.item(selected[0], "values")
        url_name = item_values[0]
        
        # Filter out the removed item and save
        self.config["items_to_track"] = [
            i for i in self.config["items_to_track"] if i["url_name"] != url_name
        ]
        self.save_config()
        self.refresh_list()

    def edit_price(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select an item to edit.")
            return
            
        item_values = self.tree.item(selected[0], "values")
        url_name = item_values[0]
        current_price = int(item_values[1])
        
        new_price = simpledialog.askinteger("Edit Price", f"Enter new target price for '{url_name}':", initialvalue=current_price, minvalue=1)
        if new_price is not None:
            for item in self.config["items_to_track"]:
                if item["url_name"] == url_name:
                    item["target_price"] = new_price
                    break
            self.save_config()
            self.refresh_list()

    def research_price(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select an item to research.")
            return
            
        item_values = self.tree.item(selected[0], "values")
        url_name = item_values[0]
        
        price = self._fetch_and_prompt_price(url_name)
        if price is not None:
            for item in self.config["items_to_track"]:
                if item["url_name"] == url_name:
                    item["target_price"] = price
                    break
            self.save_config()
            self.refresh_list()

    def refresh_list(self):
        # Clear existing items in the tree
        for row in self.tree.get_children():
            self.tree.delete(row)
            
        # Populate from loaded config
        for item in self.config["items_to_track"]:
            self.tree.insert("", "end", values=(item["url_name"], item["target_price"]))

    def open_email_settings(self, force=False):
        top = tk.Toplevel(self.root)
        top.title("Email Settings")
        top.geometry("380x250")
        
        if force:
            # Prompts the user to interact with this window before continuing
            top.grab_set() 
            
        ttk.Label(top, text="Sender Email:").grid(row=0, column=0, padx=10, pady=15, sticky="e")
        sender_var = tk.StringVar(value=self.config["email"].get("sender", ""))
        ttk.Entry(top, textvariable=sender_var, width=30).grid(row=0, column=1)
        
        ttk.Label(top, text="App Password:").grid(row=1, column=0, padx=10, pady=15, sticky="e")
        pass_var = tk.StringVar(value=self.config["email"].get("password", ""))
        ttk.Entry(top, textvariable=pass_var, show="*", width=30).grid(row=1, column=1)
        
        ttk.Label(top, text="Receiver Email:").grid(row=2, column=0, padx=10, pady=15, sticky="e")
        recv_var = tk.StringVar(value=self.config["email"].get("receiver", ""))
        ttk.Entry(top, textvariable=recv_var, width=30).grid(row=2, column=1)
        
        def save_email():
            self.config["email"]["sender"] = sender_var.get().strip()
            self.config["email"]["password"] = pass_var.get().strip()
            self.config["email"]["receiver"] = recv_var.get().strip()
            self.save_config()
            top.destroy()
            
        ttk.Button(top, text="Save Settings", command=save_email).grid(row=3, column=0, columnspan=2, pady=15)

if __name__ == "__main__":
    root = tk.Tk()
    app = ConfigGUI(root)
    root.mainloop()