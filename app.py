"""
Gmail Sender + CreateAd — Полная автоматизация
Запуск: python app.py
"""

import re
import time
import json
import csv
import threading
import requests
import customtkinter as ctk
from tkinter import messagebox, filedialog, ttk
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

DOLPHIN_API = "http://localhost:3001/v1.0"
PARSER_API = "http://vvsproject.xyz/ads"
CREATEAD_API = "https://www-gumau.world/api/createAd"

SERVICE_CODES = ["vinted_it", "vinted_nl", "vinted_es", "vinted_dk", "vinted_be", "vinted_de", "subito_it", "wallapop_es"]
PARSER_PLATFORMS = ["vinted_it", "vinted_nl", "vinted_es", "vinted_dk", "vinted_be", "vinted_de", "subito_it", "wallapop_es"]

def spintax(text: str) -> str:
    import random
    pattern = re.compile(r'\{([^{}]+)\}')
    while pattern.search(text):
        text = pattern.sub(lambda m: random.choice(m.group(1).split('|')), text)
    return text

def find_element_any(driver, wait, selectors):
    for by, value in selectors:
        try:
            return wait.until(EC.element_to_be_clickable((by, value)))
        except:
            pass
    raise RuntimeError("Element not found")

def switch_to_gmail(driver):
    for handle in reversed(driver.window_handles):
        try:
            driver.switch_to.window(handle)
            time.sleep(0.3)
            if "mail.google.com" in driver.current_url.lower():
                return
        except:
            pass
    driver.execute_script("window.open('https://mail.google.com', '_blank');")
    time.sleep(1)
    driver.switch_to.window(driver.window_handles[-1])
    time.sleep(5)

def get_seller_data(email: str) -> dict:
    try:
        with open("sellers_data.json", encoding="utf-8") as f:
            sellers = json.load(f)
            return sellers.get(email, {})
    except:
        return {}

def generate_link_via_api(seller_data: dict, user_id: str, api_key: str, service_code: str) -> str:
    try:
        payload = {
            "title": seller_data.get("title", "Item"),
            "price": seller_data.get("price", "0"),
            "serviceCode": service_code,
            "userId": user_id,
            "apiKey": api_key,
            "name": seller_data.get("seller_name", "Seller"),
            "photo": seller_data.get("image_url", ""),
            "address": "-"
        }
        r = requests.post(CREATEAD_API, json=payload, timeout=30)
        r.raise_for_status()
        data = r.json()
        if data.get("success") and data.get("link"):
            return data["link"]
        elif data.get("link"):
            return data["link"]
        return ""
    except:
        return ""

def dolphin_start(profile_id: str, token: str) -> dict:
    url = f"{DOLPHIN_API}/browser_profiles/{profile_id}/start?automation=1"
    r = requests.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=15)
    r.raise_for_status()
    return r.json()["automation"]

def dolphin_stop(profile_id: str, token: str):
    try:
        requests.get(f"{DOLPHIN_API}/browser_profiles/{profile_id}/stop",
                     headers={"Authorization": f"Bearer {token}"}, timeout=10)
    except:
        pass

def get_driver(automation: dict) -> webdriver.Chrome:
    opts = Options()
    opts.add_experimental_option("debuggerAddress", f"127.0.0.1:{automation['port']}")
    return webdriver.Chrome(options=opts)

def send_via_gmail(driver, recipient: str, subject: str, body: str):
    wait = WebDriverWait(driver, 40)
    switch_to_gmail(driver)
    time.sleep(3)

    compose = find_element_any(driver, wait, [
        (By.XPATH, '//div[@role="button"][@aria-label="Compose"]'),
        (By.CSS_SELECTOR, 'div.T-I.T-I-KE'),
    ])
    driver.execute_script("arguments[0].scrollIntoView(true);", compose)
    compose.click()
    time.sleep(4)

    to = find_element_any(driver, wait, [
        (By.CSS_SELECTOR, 'input[name="to"]'),
        (By.XPATH, '//input[@aria-label="To"]'),
    ])
    to.click()
    time.sleep(0.5)
    to.send_keys(recipient)
    time.sleep(1)
    to.send_keys(Keys.TAB)
    time.sleep(2)

    subj = find_element_any(driver, wait, [
        (By.CSS_SELECTOR, 'input[name="subjectbox"]'),
        (By.XPATH, '//input[@aria-label="Subject"]'),
    ])
    subj.click()
    time.sleep(0.5)
    subj.send_keys(subject)
    time.sleep(1)
    subj.send_keys(Keys.TAB)
    time.sleep(2)

    bd = find_element_any(driver, wait, [
        (By.CSS_SELECTOR, 'div[role="textbox"]'),
    ])
    bd.click()
    time.sleep(0.3)
    driver.execute_script("arguments[0].innerHTML = arguments[1];", bd, body)
    time.sleep(0.5)

    send_btn = find_element_any(driver, wait, [
        (By.XPATH, '//div[@role="button"][@data-tooltip*="Send"]'),
        (By.CSS_SELECTOR, 'button[aria-label*="Send"]'),
    ])
    driver.execute_script("arguments[0].click();", send_btn)
    time.sleep(4)

def check_and_reply(driver, reply_body: str, user_id: str, api_key: str, service_code: str) -> int:
    wait = WebDriverWait(driver, 30)
    replied = 0
    switch_to_gmail(driver)
    driver.get("https://mail.google.com/mail/u/0/#inbox")
    time.sleep(3)

    try:
        unread = driver.find_elements(By.CSS_SELECTOR, 'tr.zE')
        for row in unread[:10]:
            try:
                row.click()
                time.sleep(2)

                try:
                    sender_elem = driver.find_element(By.CSS_SELECTOR, 'span[email]')
                    sender_email = sender_elem.get_attribute('email')
                except:
                    sender_email = None

                seller_data = get_seller_data(sender_email) if sender_email else {}
                final_reply_body = reply_body

                if seller_data:
                    link = generate_link_via_api(seller_data, user_id, api_key, service_code)
                    final_reply_body = final_reply_body.replace("{link}", link)
                    final_reply_body = final_reply_body.replace("{price}", seller_data.get("price", ""))
                else:
                    final_reply_body = final_reply_body.replace("{link}", "")
                    final_reply_body = final_reply_body.replace("{price}", "")

                final_reply_body = spintax(final_reply_body)

                reply_btn = find_element_any(driver, wait, [
                    (By.CSS_SELECTOR, 'div[data-tooltip="Reply"]'),
                    (By.CSS_SELECTOR, 'div[aria-label="Reply"]'),
                ])
                reply_btn.click()
                time.sleep(2)

                reply_field = find_element_any(driver, wait, [
                    (By.CSS_SELECTOR, 'div[role="textbox"]'),
                ])
                reply_field.click()
                time.sleep(0.3)
                driver.execute_script("arguments[0].innerHTML = arguments[1];", reply_field, final_reply_body)
                time.sleep(0.5)

                send_btn = find_element_any(driver, wait, [
                    (By.CSS_SELECTOR, 'div[role="button"][data-tooltip*="Send"]'),
                ])
                driver.execute_script("arguments[0].click();", send_btn)
                time.sleep(2)
                replied += 1

                driver.get("https://mail.google.com/mail/u/0/#inbox")
                time.sleep(2)
            except:
                driver.get("https://mail.google.com/mail/u/0/#inbox")
                time.sleep(2)
    except:
        pass

    return replied

class ParserFrame(ctk.CTkFrame):
    FILTER_DEFAULTS = {
        "platform": "vinted_it",
        "country": "",
        "category": "",
        "price": "",
        "ads": "0..",
        "reviews": "0..",
        "publication": "24h",
        "delivery": False,
        "phone": False,
        "limit": "50"
    }

    def __init__(self, master, settings_config: dict, save_settings_callback):
        super().__init__(master)
        self.settings_config = settings_config
        self.save_settings_callback = save_settings_callback
        self.search_thread = None
        self.results = []

        self._ensure_defaults()
        self._build_ui()
        self._apply_filters(self.settings_config["parser_filters"])

    def _ensure_defaults(self):
        filters = self.settings_config.setdefault("parser_filters", {})
        for key, value in self.FILTER_DEFAULTS.items():
            filters.setdefault(key, value)

    def _build_ui(self):
        filters_panel = ctk.CTkFrame(self)
        filters_panel.pack(fill="x", padx=10, pady=(10, 5))

        top_row = ctk.CTkFrame(filters_panel)
        top_row.pack(fill="x", padx=8, pady=4)
        ctk.CTkLabel(top_row, text="Платформа:", width=130, anchor="w").pack(side="left")
        self.platform_var = ctk.StringVar(value=self.FILTER_DEFAULTS["platform"])
        self.platform_menu = ctk.CTkOptionMenu(top_row, values=PARSER_PLATFORMS, variable=self.platform_var)
        self.platform_menu.pack(side="left", padx=5)
        ctk.CTkLabel(top_row, text="Страна:", width=80, anchor="w").pack(side="left", padx=(10, 0))
        self.country_entry = ctk.CTkEntry(top_row, placeholder_text="Italy")
        self.country_entry.pack(side="left", padx=5, fill="x", expand=True)

        second_row = ctk.CTkFrame(filters_panel)
        second_row.pack(fill="x", padx=8, pady=4)
        ctk.CTkLabel(second_row, text="Категория:", width=130, anchor="w").pack(side="left")
        self.category_entry = ctk.CTkEntry(second_row, placeholder_text="men_shoes")
        self.category_entry.pack(side="left", padx=5, fill="x", expand=True)
        ctk.CTkLabel(second_row, text="Лимит:", width=80, anchor="w").pack(side="left", padx=(10, 0))
        self.limit_entry = ctk.CTkEntry(second_row, width=100, placeholder_text="50")
        self.limit_entry.pack(side="left", padx=5)

        third_row = ctk.CTkFrame(filters_panel)
        third_row.pack(fill="x", padx=8, pady=4)
        ctk.CTkLabel(third_row, text="Цена (min..max):", width=130, anchor="w").pack(side="left")
        self.price_entry = ctk.CTkEntry(third_row, placeholder_text="10..100")
        self.price_entry.pack(side="left", padx=5, fill="x", expand=True)
        ctk.CTkLabel(third_row, text="Объявлений (min..):", width=150, anchor="w").pack(side="left", padx=(10, 0))
        self.ads_entry = ctk.CTkEntry(third_row, width=120, placeholder_text="0..")
        self.ads_entry.pack(side="left", padx=5)

        fourth_row = ctk.CTkFrame(filters_panel)
        fourth_row.pack(fill="x", padx=8, pady=4)
        ctk.CTkLabel(fourth_row, text="Отзывов (min..):", width=130, anchor="w").pack(side="left")
        self.reviews_entry = ctk.CTkEntry(fourth_row, placeholder_text="0..")
        self.reviews_entry.pack(side="left", padx=5, fill="x", expand=True)
        ctk.CTkLabel(fourth_row, text="Время публикации:", width=150, anchor="w").pack(side="left", padx=(10, 0))
        self.publication_var = ctk.StringVar(value=self.FILTER_DEFAULTS["publication"])
        self.publication_menu = ctk.CTkOptionMenu(fourth_row, values=["5m", "1h", "24h", "7d"], variable=self.publication_var)
        self.publication_menu.pack(side="left", padx=5)

        fifth_row = ctk.CTkFrame(filters_panel)
        fifth_row.pack(fill="x", padx=8, pady=(4, 8))
        self.delivery_var = ctk.BooleanVar(value=False)
        self.phone_var = ctk.BooleanVar(value=False)
        self.delivery_checkbox = ctk.CTkCheckBox(fifth_row, text="Доставка (true)", variable=self.delivery_var)
        self.delivery_checkbox.pack(side="left", padx=5)
        self.phone_checkbox = ctk.CTkCheckBox(fifth_row, text="Телефон (true)", variable=self.phone_var)
        self.phone_checkbox.pack(side="left", padx=15)

        buttons = ctk.CTkFrame(self)
        buttons.pack(fill="x", padx=10, pady=(0, 5))
        self.search_btn = ctk.CTkButton(buttons, text="🔍 Поиск", command=self._start_search, width=140)
        self.search_btn.pack(side="left", padx=5)
        ctk.CTkButton(buttons, text="🧹 Очистить фильтры", command=self._clear_filters, width=160).pack(side="left", padx=5)
        ctk.CTkButton(buttons, text="💾 Экспорт в CSV", command=self._export_csv, width=150).pack(side="left", padx=5)
        self.status_label = ctk.CTkLabel(buttons, text="Статус: готов")
        self.status_label.pack(side="left", padx=15)

        table_wrap = ctk.CTkFrame(self)
        table_wrap.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        columns = ("link", "title", "price", "seller", "reviews", "date")
        self.results_table = ttk.Treeview(table_wrap, columns=columns, show="headings", height=12)
        self.results_table.heading("link", text="Ссылка")
        self.results_table.heading("title", text="Название")
        self.results_table.heading("price", text="Цена")
        self.results_table.heading("seller", text="Продавец")
        self.results_table.heading("reviews", text="Отзывы")
        self.results_table.heading("date", text="Дата")
        self.results_table.column("link", width=300, anchor="w")
        self.results_table.column("title", width=260, anchor="w")
        self.results_table.column("price", width=90, anchor="center")
        self.results_table.column("seller", width=140, anchor="w")
        self.results_table.column("reviews", width=80, anchor="center")
        self.results_table.column("date", width=150, anchor="center")
        self.results_table.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(table_wrap, orient="vertical", command=self.results_table.yview)
        scrollbar.pack(side="right", fill="y")
        self.results_table.configure(yscrollcommand=scrollbar.set)

    def _set_entry(self, entry, value):
        entry.delete(0, "end")
        entry.insert(0, value)

    def _to_bool(self, value):
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() == "true"
        return bool(value)

    def _apply_filters(self, filters):
        self.platform_var.set(filters.get("platform", self.FILTER_DEFAULTS["platform"]))
        self._set_entry(self.country_entry, filters.get("country", ""))
        self._set_entry(self.category_entry, filters.get("category", ""))
        self._set_entry(self.price_entry, filters.get("price", ""))
        self._set_entry(self.ads_entry, filters.get("ads", ""))
        self._set_entry(self.reviews_entry, filters.get("reviews", ""))
        publication = filters.get("publication", self.FILTER_DEFAULTS["publication"])
        if publication not in {"5m", "1h", "24h", "7d"}:
            publication = self.FILTER_DEFAULTS["publication"]
        self.publication_var.set(publication)
        self.delivery_var.set(self._to_bool(filters.get("delivery", False)))
        self.phone_var.set(self._to_bool(filters.get("phone", False)))
        self._set_entry(self.limit_entry, str(filters.get("limit", "50")))

    def _collect_filters(self):
        limit = self.limit_entry.get().strip() or "50"
        return {
            "platform": self.platform_var.get(),
            "country": self.country_entry.get().strip(),
            "category": self.category_entry.get().strip(),
            "price": self.price_entry.get().strip(),
            "ads": self.ads_entry.get().strip(),
            "reviews": self.reviews_entry.get().strip(),
            "publication": self.publication_var.get().strip(),
            "delivery": bool(self.delivery_var.get()),
            "phone": bool(self.phone_var.get()),
            "limit": limit
        }

    def _save_filters(self, filters):
        self.settings_config["parser_filters"] = dict(filters)
        self.save_settings_callback()

    def _start_search(self):
        if self.search_thread and self.search_thread.is_alive():
            return
        filters = self._collect_filters()
        self._save_filters(filters)
        self.search_btn.configure(state="disabled")
        self.status_label.configure(text="Статус: поиск...")
        self.search_thread = threading.Thread(target=self._search_thread, args=(filters,), daemon=True)
        self.search_thread.start()

    def _search_thread(self, filters):
        try:
            params = {
                "country": filters["country"],
                "category": filters["category"],
                "limit": filters["limit"],
                "price": filters["price"],
                "ads": filters["ads"],
                "reviews": filters["reviews"],
                "publication": filters["publication"],
                "delivery": "true" if filters["delivery"] else "false",
                "phone": "true" if filters["phone"] else "false"
            }
            clean_params = {k: v for k, v in params.items() if v != ""}
            response = requests.get(f"{PARSER_API}/{filters['platform']}", params=clean_params, timeout=45)
            response.raise_for_status()
            data = response.json()
            rows = self._normalize_rows(data)
            self.after(0, lambda: self._show_results(rows, f"Статус: найдено {len(rows)}"))
        except requests.RequestException as exc:
            self.after(0, lambda: self._show_error(f"Ошибка API: {exc}"))
        except ValueError:
            self.after(0, lambda: self._show_error("Ошибка API: некорректный JSON"))
        except Exception as exc:
            self.after(0, lambda: self._show_error(f"Ошибка: {exc}"))

    def _normalize_rows(self, data):
        if isinstance(data, dict):
            items = list(data.values())
        elif isinstance(data, list):
            items = data
        else:
            items = []

        rows = []
        for item in items:
            if not isinstance(item, dict):
                continue
            rows.append({
                "link": str(item.get("link") or item.get("url") or item.get("item_url") or ""),
                "title": str(item.get("title") or item.get("name") or ""),
                "price": str(item.get("price") or ""),
                "seller": str(item.get("seller") or item.get("seller_name") or item.get("username") or ""),
                "reviews": str(item.get("reviews") or item.get("feedbacks") or item.get("rating_count") or ""),
                "date": str(item.get("date") or item.get("publication") or item.get("published_at") or item.get("created_at") or "")
            })
        return rows

    def _show_results(self, rows, status_text):
        self.results = rows
        for item in self.results_table.get_children():
            self.results_table.delete(item)
        for row in rows:
            self.results_table.insert(
                "",
                "end",
                values=(row["link"], row["title"], row["price"], row["seller"], row["reviews"], row["date"])
            )
        self.status_label.configure(text=status_text)
        self.search_btn.configure(state="normal")

    def _show_error(self, text):
        self.status_label.configure(text="Статус: ошибка")
        self.search_btn.configure(state="normal")
        messagebox.showerror("Парсер", text)

    def _clear_filters(self):
        self._apply_filters(dict(self.FILTER_DEFAULTS))
        filters = self._collect_filters()
        self._save_filters(filters)
        self.status_label.configure(text="Статус: фильтры очищены")

    def _export_csv(self):
        if not self.results:
            messagebox.showwarning("Парсер", "Нет результатов для экспорта")
            return
        path = filedialog.asksaveasfilename(
            title="Сохранить CSV",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(["link", "title", "price", "seller", "reviews", "date"])
            for row in self.results:
                writer.writerow([row["link"], row["title"], row["price"], row["seller"], row["reviews"], row["date"]])
        self.status_label.configure(text=f"Статус: CSV сохранён ({len(self.results)})")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("📧 Gmail Sender + CreateAd")
        self.geometry("1400x850")
        
        self.dolphin_config = {}
        self.settings_config = {}
        self.running = False
        self.paused = False
        
        self._load_configs()
        self._setup_ui()
        
    def _load_configs(self):
        parser_filter_defaults = dict(ParserFrame.FILTER_DEFAULTS)
        try:
            with open('dolphin.json', 'r', encoding='utf-8') as f:
                self.dolphin_config = json.load(f)
        except:
            self.dolphin_config = {"token": ""}
        
        try:
            with open('settings.json', 'r', encoding='utf-8') as f:
                self.settings_config = json.load(f)
        except:
            self.settings_config = {
                "templates": {"first": {"subject": "", "body": ""}, "reply": {"subject": "", "body": ""}},
                "automation": {"parser_key": "", "platform": "vinted", "country": "IT", "user_id": "", "api_key": "", "delay": 5, "service_code": "vinted_it"},
                "parser_filters": parser_filter_defaults
            }
        filters = self.settings_config.setdefault("parser_filters", {})
        for key, value in parser_filter_defaults.items():
            filters.setdefault(key, value)
    
    def _save_dolphin_config(self):
        with open('dolphin.json', 'w', encoding='utf-8') as f:
            json.dump(self.dolphin_config, f, indent=2, ensure_ascii=False)
    
    def _save_settings_config(self):
        with open('settings.json', 'w', encoding='utf-8') as f:
            json.dump(self.settings_config, f, indent=2, ensure_ascii=False)
    
    def _setup_ui(self):
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        title = ctk.CTkLabel(main_frame, text="🚀 Gmail Sender + CreateAd", font=("Arial", 20, "bold"))
        title.pack(pady=10)
        
        self.tabview = ctk.CTkTabview(main_frame)
        self.tabview.pack(fill="both", expand=True)
        
        self.tabview.add("🔑 Токен")
        self.tabview.add("👤 Профили")
        self.tabview.add("✉️ Шаблоны")
        self.tabview.add("🔍 Парсер")
        self.tabview.add("🚀 Запуск")
        self.tabview.add("📋 Лог")
        
        self._setup_token_tab()
        self._setup_profiles_tab()
        self._setup_templates_tab()
        self._setup_parser_tab()
        self._setup_automation_tab()
        self._setup_log_tab()
        
    def _setup_token_tab(self):
        tab = self.tabview.tab("🔑 Токен")
        frame = ctk.CTkFrame(tab)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(frame, text="Токен Dolphin Anty:", font=("Arial", 12, "bold")).pack(anchor="w")
        self.token_entry = ctk.CTkEntry(frame, width=400)
        self.token_entry.pack(fill="x", pady=5)
        self.token_entry.insert(0, self.dolphin_config.get("token", ""))
        
        btn_frame = ctk.CTkFrame(frame)
        btn_frame.pack(fill="x", pady=10)
        ctk.CTkButton(btn_frame, text="💾 Сохранить", command=self._save_token, width=150).pack(side="left", padx=5)
        
    def _save_token(self):
        self.dolphin_config["token"] = self.token_entry.get().strip()
        self._save_dolphin_config()
        self._log("✅ Токен сохранён")
    
    def _setup_profiles_tab(self):
        tab = self.tabview.tab("👤 Профили")
        frame = ctk.CTkFrame(tab)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(frame, text="ID профилей (по одному на строку):", font=("Arial", 12, "bold")).pack(anchor="w")
        
        self.profiles_box = ctk.CTkTextbox(frame, height=200)
        self.profiles_box.pack(fill="both", expand=True, pady=10)
        
        btn_frame = ctk.CTkFrame(frame)
        btn_frame.pack(fill="x", pady=10)
        ctk.CTkButton(btn_frame, text="💾 Сохранить", command=self._save_profiles, width=150).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="📂 Загрузить файл", command=self._load_profiles_file, width=150).pack(side="left", padx=5)
        
        self.profiles_count = ctk.CTkLabel(frame, text="Профилей: 0")
        self.profiles_count.pack(anchor="w")
    
    def _get_profiles(self) -> list:
        text = self.profiles_box.get("1.0", "end").strip()
        profiles = [p.strip() for p in text.split("\n") if p.strip()]
        self.profiles_count.configure(text=f"Профилей: {len(profiles)}")
        return profiles
    
    def _save_profiles(self):
        profiles = self._get_profiles()
        with open("profiles.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(profiles))
        self._log(f"✅ {len(profiles)} профилей сохранено")
    
    def _load_profiles_file(self):
        path = filedialog.askopenfilename(filetypes=[("Text", "*.txt")])
        if not path:
            return
        with open(path, encoding="utf-8") as f:
            ids = [l.strip() for l in f if l.strip() and not l.startswith("#")]
        self.profiles_box.delete("1.0", "end")
        self.profiles_box.insert("end", "\n".join(ids))
        self._log(f"✅ {len(ids)} профилей загружено")
    
    def _setup_templates_tab(self):
        tab = self.tabview.tab("✉️ Шаблоны")
        frame = ctk.CTkFrame(tab)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(frame, text="📧 ПЕРВОЕ ПИСЬМО", font=("Arial", 13, "bold")).pack(anchor="w", pady=(0, 10))
        ctk.CTkLabel(frame, text="Тема:", font=("Arial", 11)).pack(anchor="w")
        self.first_subject = ctk.CTkEntry(frame)
        self.first_subject.pack(fill="x", pady=5)
        self.first_subject.insert(0, self.settings_config.get("templates", {}).get("first", {}).get("subject", ""))
        
        ctk.CTkLabel(frame, text="Текст:", font=("Arial", 11)).pack(anchor="w")
        self.first_body = ctk.CTkTextbox(frame, height=100)
        self.first_body.pack(fill="both", expand=True, pady=5)
        self.first_body.insert("1.0", self.settings_config.get("templates", {}).get("first", {}).get("body", ""))
        
        ctk.CTkLabel(frame, text="💬 ОТВЕТ НА ПИСЬМО", font=("Arial", 13, "bold")).pack(anchor="w", pady=(20, 10))
        ctk.CTkLabel(frame, text="HTML (используй {link}, {price}):", font=("Arial", 11)).pack(anchor="w")
        self.reply_body = ctk.CTkTextbox(frame, height=100)
        self.reply_body.pack(fill="both", expand=True, pady=5)
        self.reply_body.insert("1.0", self.settings_config.get("templates", {}).get("reply", {}).get("body", ""))
        
        ctk.CTkButton(frame, text="💾 Сохранить", command=self._save_templates, width=150).pack(pady=10)
    
    def _save_templates(self):
        self.settings_config["templates"] = {
            "first": {"subject": self.first_subject.get(), "body": self.first_body.get("1.0", "end")},
            "reply": {"subject": "", "body": self.reply_body.get("1.0", "end")}
        }
        self._save_settings_config()
        self._log("✅ Шаблоны сохранены")
    
    def _setup_automation_tab(self):
        tab = self.tabview.tab("🚀 Запуск")
        frame = ctk.CTkFrame(tab)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Парсер
        ctk.CTkLabel(frame, text="🛰 ПАРСЕР", font=("Arial", 12, "bold")).pack(anchor="w")
        parser_frame = ctk.CTkFrame(frame)
        parser_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(parser_frame, text="API ключ:", font=("Arial", 10)).pack(side="left", padx=5)
        self.parser_key = ctk.CTkEntry(parser_frame, width=200)
        self.parser_key.pack(side="left", padx=5)
        self.parser_key.insert(0, self.settings_config.get("automation", {}).get("parser_key", ""))
        
        ctk.CTkLabel(parser_frame, text="Платформа:", font=("Arial", 10)).pack(side="left", padx=5)
        self.parser_platform = ctk.CTkEntry(parser_frame, width=100)
        self.parser_platform.pack(side="left", padx=5)
        self.parser_platform.insert(0, self.settings_config.get("automation", {}).get("platform", "vinted"))
        
        # CreateAd
        ctk.CTkLabel(frame, text="🎫 CREATEAD", font=("Arial", 12, "bold")).pack(anchor="w", pady=(10, 5))
        createad_frame = ctk.CTkFrame(frame)
        createad_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(createad_frame, text="User ID:", font=("Arial", 10)).pack(side="left", padx=5)
        self.user_id = ctk.CTkEntry(createad_frame, width=120)
        self.user_id.pack(side="left", padx=5)
        self.user_id.insert(0, self.settings_config.get("automation", {}).get("user_id", ""))
        
        ctk.CTkLabel(createad_frame, text="API Key:", font=("Arial", 10)).pack(side="left", padx=5)
        self.api_key = ctk.CTkEntry(createad_frame, width=150)
        self.api_key.pack(side="left", padx=5)
        self.api_key.insert(0, self.settings_config.get("automation", {}).get("api_key", ""))
        
        ctk.CTkLabel(createad_frame, text="ServiceCode:", font=("Arial", 10)).pack(side="left", padx=5)
        self.service_code = ctk.CTkOptionMenu(createad_frame, values=SERVICE_CODES, width=100)
        self.service_code.set(self.settings_config.get("automation", {}).get("service_code", SERVICE_CODES[0]))
        self.service_code.pack(side="left", padx=5)
        
        # Управление
        ctk.CTkLabel(frame, text="⚙️ УПРАВЛЕНИЕ", font=("Arial", 12, "bold")).pack(anchor="w", pady=(10, 5))
        ctrl_frame = ctk.CTkFrame(frame)
        ctrl_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(ctrl_frame, text="Задержка (сек):", font=("Arial", 10)).pack(side="left", padx=5)
        self.delay = ctk.CTkEntry(ctrl_frame, width=80)
        self.delay.pack(side="left", padx=5)
        self.delay.insert(0, str(self.settings_config.get("automation", {}).get("delay", 5)))
        
        self.start_btn = ctk.CTkButton(ctrl_frame, text="▶ СТАРТ", command=self._start_automation, fg_color="#238636", width=120)
        self.start_btn.pack(side="left", padx=5)
        
        self.pause_btn = ctk.CTkButton(ctrl_frame, text="⏸ ПАУЗА", command=self._pause_automation, fg_color="#9e6a03", width=120, state="disabled")
        self.pause_btn.pack(side="left", padx=5)
        
        self.stop_btn = ctk.CTkButton(ctrl_frame, text="⏹ СТОП", command=self._stop_automation, fg_color="#da3633", width=120, state="disabled")
        self.stop_btn.pack(side="left", padx=5)
        
        self.status = ctk.CTkLabel(frame, text="⚪ Готов", font=("Arial", 12, "bold"))
        self.status.pack(pady=10)

    def _setup_parser_tab(self):
        tab = self.tabview.tab("🔍 Парсер")
        self.parser_frame = ParserFrame(tab, self.settings_config, self._save_settings_config)
        self.parser_frame.pack(fill="both", expand=True)
    
    def _start_automation(self):
        profiles = self._get_profiles()
        if not profiles:
            messagebox.showerror("Ошибка", "Нет профилей!")
            return
        
        token = self.dolphin_config.get("token", "").strip()
        if not token:
            messagebox.showerror("Ошибка", "Нет токена!")
            return
        
        parser_key = self.parser_key.get().strip()
        if not parser_key:
            messagebox.showerror("Ошибка", "Нет API ключа парсера!")
            return
        
        user_id = self.user_id.get().strip()
        api_key = self.api_key.get().strip()
        if not user_id or not api_key:
            messagebox.showerror("Ошибка", "Укажи User ID и API Key!")
            return
        
        self.running = True
        self.paused = False
        self.start_btn.configure(state="disabled")
        self.pause_btn.configure(state="normal")
        self.stop_btn.configure(state="normal")
        
        platform = self.parser_platform.get().strip()
        service_code = self.service_code.get()
        delay = int(self.delay.get() or 5)
        
        threading.Thread(
            target=self._run_automation,
            args=(profiles, token, parser_key, platform, user_id, api_key, service_code, delay),
            daemon=True
        ).start()
    
    def _pause_automation(self):
        self.paused = not self.paused
        text = "▶ ПРОДОЛЖИТЬ" if self.paused else "⏸ ПАУЗА"
        self.pause_btn.configure(text=text)
    
    def _stop_automation(self):
        self.running = False
        self.start_btn.configure(state="normal")
        self.pause_btn.configure(state="disabled", text="⏸ ПАУЗА")
        self.stop_btn.configure(state="disabled")
        self.status.configure(text="⏹ Остановлено", text_color="#da3633")
        self._log("⏹ Остановлено")
    
    def _run_automation(self, profiles, token, parser_key, platform, user_id, api_key, service_code, delay):
        self.status.configure(text="🟢 Запуск...", text_color="#3fb950")
        self._log("🚀 Начало автоматизации")
        
        drivers_pool = {}
        
        try:
            # ШАГ 1: Парсим
            self._log(f"🛰 Парсинг {platform}...")
            self.status.configure(text="🟡 Парсинг...", text_color="#d29922")
            
            params = {"country": "IT", "limit": "100"}
            r = requests.get(f"{PARSER_API}/{platform}", headers={"api-key": parser_key}, params=params, timeout=30)
            
            if r.status_code != 200:
                self._log(f"❌ Ошибка парсера: {r.status_code}")
                return
            
            data = r.json()
            sellers_data = {}
            emails = []
            
            for item_id, item in data.items():
                email = item.get("email", "").strip()
                if not email or "@" not in email:
                    continue
                emails.append(email)
                sellers_data[email] = {
                    "email": email,
                    "title": item.get("title", ""),
                    "price": item.get("price", ""),
                    "image_url": item.get("image_url", ""),
                    "seller_name": item.get("seller", ""),
                }
            
            with open("sellers_data.json", "w", encoding="utf-8") as f:
                json.dump(sellers_data, f, ensure_ascii=False)
            
            self._log(f"✅ Получено {len(emails)} email-ов")
            
            # ШАГ 2: Открываем профили
            self._log(f"🚀 Открываю профили...")
            self.status.configure(text="🟡 Открываю профили...", text_color="#d29922")
            
            for profile_id in profiles:
                if not self.running:
                    break
                try:
                    automation = dolphin_start(profile_id, token)
                    driver = get_driver(automation)
                    drivers_pool[profile_id] = driver
                    self._log(f"  ✅ {profile_id}")
                except Exception as e:
                    self._log(f"  ❌ {profile_id}: {e}")
            
            if not drivers_pool:
                self._log("❌ Не открыть профили")
                return
            
            self._log(f"✅ {len(drivers_pool)} профилей готовы")
            
            # ШАГ 3: Отправляем письма
            templates = self.settings_config.get("templates", {})
            first_subject = templates.get("first", {}).get("subject", "")
            first_body = templates.get("first", {}).get("body", "")
            reply_body = templates.get("reply", {}).get("body", "")
            
            sent = 0
            replied = 0
            profile_ids = list(drivers_pool.keys())
            
            for idx, email in enumerate(emails):
                if not self.running:
                    break
                
                while self.paused and self.running:
                    time.sleep(1)
                
                if not self.running:
                    break
                
                profile_idx = idx % len(profile_ids)
                profile_id = profile_ids[profile_idx]
                driver = drivers_pool[profile_id]
                
                try:
                    self._log(f"📧 {email}")
                    self.status.configure(text=f"📧 {email}", text_color="#3fb950")
                    
                    seller_data = sellers_data.get(email, {})
                    price = seller_data.get("price", "")
                    
                    final_first_body = first_body.replace("{price}", price)
                    final_first_body = spintax(final_first_body)
                    final_first_subject = spintax(first_subject)
                    
                    send_via_gmail(driver, email, final_first_subject, final_first_body)
                    sent += 1
                    self._log(f"  ✅ Отправлено")
                    
                    self._log(f"  💬 Проверяю ответы...")
                    replied_count = check_and_reply(driver, reply_body, user_id, api_key, service_code)
                    replied += replied_count
                    
                    for _ in range(delay):
                        if not self.running:
                            break
                        time.sleep(1)
                    
                except Exception as e:
                    self._log(f"  ❌ {e}")
            
            # ШАГ 4: Закрываем
            self._log("🛑 Закрываю профили...")
            for profile_id, driver in drivers_pool.items():
                try:
                    driver.quit()
                    dolphin_stop(profile_id, token)
                except:
                    pass
            
            self.running = False
            self.start_btn.configure(state="normal")
            self.pause_btn.configure(state="disabled", text="⏸ ПАУЗА")
            self.stop_btn.configure(state="disabled")
            
            self._log(f"✅ ИТОГИ: {sent} писем, {replied} ответов")
            self.status.configure(text=f"✅ Завершено: {sent} писем", text_color="#3fb950")
            
        except Exception as e:
            self._log(f"❌ ОШИБКА: {e}")
            for profile_id, driver in drivers_pool.items():
                try:
                    driver.quit()
                    dolphin_stop(profile_id, token)
                except:
                    pass
            self.running = False
    
    def _setup_log_tab(self):
        tab = self.tabview.tab("📋 Лог")
        frame = ctk.CTkFrame(tab)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.log_box = ctk.CTkTextbox(frame)
        self.log_box.pack(fill="both", expand=True)
        self.log_box.configure(state="disabled")
        
        ctk.CTkButton(frame, text="🗑 Очистить", command=self._clear_log, width=150).pack(pady=10)
    
    def _log(self, msg: str):
        ts = datetime.now().strftime("%H:%M:%S")
        msg_with_ts = f"[{ts}] {msg}"
        self.log_box.configure(state="normal")
        self.log_box.insert("end", msg_with_ts + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")
        print(msg_with_ts)
    
    def _clear_log(self):
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")

if __name__ == "__main__":
    app = App()
    app.mainloop()
