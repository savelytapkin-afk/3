import customtkinter as ctk
import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox
import threading
import json
import time
import requests
import random
import traceback
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import re
import os

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

SPINTAX_PATTERN = re.compile(r'\{([^{}]*)\}')
MAX_SPINTAX_ITERATIONS = 20

PLATFORMS_CATEGORIES = {
    "vinted": {"1": "детское", "2": "дизайнерское", "3": "для дома", "4": "женское", "5": "мужское", "6": "развлечения", "7": "спорт", "8": "электроника"},
    "2dehands": {"1": "антиквариат", "2": "аудио и фото", "3": "бытовая техника", "4": "детские товары", "5": "диски", "6": "женская одежда", "7": "жилье", "8": "книги"},
    "bakeca": {"1": "антиквариат", "2": "велосипеды", "3": "детские товары", "4": "книги и комиксы", "5": "кухня и техника", "6": "мебель", "7": "мода", "8": "мужская одежда"},
    "bazaraki": {"1": "бизнес", "2": "детские товары", "3": "дом и сад", "4": "компьютеры", "5": "красота и здоровье", "6": "одежда и аксессуары", "7": "спорт", "8": "электроника"},
    "carousell": {"1": "аудио", "2": "видеоигры", "3": "дети", "4": "женская мода", "5": "здоровье", "6": "зоотовары", "7": "компьютеры", "8": "книги"},
    "depop": {"1": "детское", "2": "женское", "3": "мужское"},
    "etsy": {"1": "аксессуары", "2": "детские товары", "3": "дом и быт", "4": "игрушки", "5": "искусство", "6": "книги", "7": "косметика", "8": "украшения"},
    "kleinanzeigen": {"1": "велосипеды", "2": "досуг и хобби", "3": "дом и сад", "4": "мода", "5": "музыка и книги", "6": "семья и дети", "7": "спорт", "8": "электроника"},
    "marktplaats": {"1": "антиквариат", "2": "аудио и фото", "3": "бытовая техника", "4": "детские товары", "5": "диски", "6": "женская одежда", "7": "книги", "8": "компьютеры"},
    "mercari": {"1": "детские товары", "2": "дом и быт", "3": "женская одежда", "4": "игры", "5": "книги", "6": "косметика", "7": "мужская одежда", "8": "электроника"},
    "olx": {"1": "антиквариат", "2": "дом и сад", "3": "для детей", "4": "мода", "5": "спорт", "6": "электроника"},
    "wallapop": {"1": "бытовая техника", "2": "велосипеды", "3": "детские товары", "4": "дом и сад", "5": "книги", "6": "коллекционные товары", "7": "мода", "8": "электроника"}
}

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Gmail Sender v3.5")
        self.geometry("1400x800")
        
        self.running = False
        self.paused = False
        self.drivers_pool = {}
        self.sellers_data = {}
        self.last_parser_request = 0
        
        self.dolphin_config = {}
        self.settings_config = {}
        
        self._load_configs()
        self._create_ui()
    
    def _load_configs(self):
        """Загружает конфиги из dolphin.json и settings.json"""
        # Загружаем Dolphin конфиг
        try:
            with open('dolphin.json', 'r', encoding='utf-8') as f:
                self.dolphin_config = json.load(f)
                if "token" in self.dolphin_config:
                    self.dolphin_config["token"] = self.dolphin_config["token"].strip()
        except:
            self.dolphin_config = {"token": ""}
        
        # Загружаем Settings конфиг
        try:
            with open('settings.json', 'r', encoding='utf-8') as f:
                self.settings_config = json.load(f)
        except:
            self.settings_config = {
                "templates": {
                    "first": {"subject": "", "body": ""},
                    "reply": {"body": ""}
                },
                "automation": {
                    "parser_key": "",
                    "platform": "vinted",
                    "country": "IT",
                    "user_id": "",
                    "api_key": "",
                    "delay": 5,
                    "max_letters": 10,
                    "service_code": "vinted_it"
                },
                "parser_filters": {
                    "category": "",
                    "price": "",
                    "ads": "",
                    "reviews": "",
                    "publication": "5m",
                    "phone": "",
                    "delivery": "",
                    "registration": "",
                    "blacklist": "",
                    "limit": "50"
                }
            }
    
    def _save_dolphin_config(self):
        """Сохраняет dolphin.json"""
        try:
            with open('dolphin.json', 'w', encoding='utf-8') as f:
                json.dump(self.dolphin_config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self._log(f"❌ Ошибка сохранения dolphin.json: {e}")
    
    def _save_settings_config(self):
        """Сохраняет settings.json"""
        try:
            with open('settings.json', 'w', encoding='utf-8') as f:
                json.dump(self.settings_config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self._log(f"❌ Ошибка сохранения settings.json: {e}")
    
    def _create_ui(self):
        """Создаёт главный интерфейс"""
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.tabview = ctk.CTkTabview(main_frame)
        self.tabview.pack(fill="both", expand=True)
        
        self.tab_dolphin = self.tabview.add("🐬 Dolphin")
        self.tab_parser = self.tabview.add("🛰 Парсер")
        self.tab_templates = self.tabview.add("✉️ Шаблоны")
        self.tab_send = self.tabview.add("🚀 Отправка")
        self.tab_check = self.tabview.add("💬 Ответы")
        self.tab_log = self.tabview.add("📋 Лог")
        self.tab_settings = self.tabview.add("⚙️ Настройки")
        
        self._create_dolphin_tab()
        self._create_parser_tab()
        self._create_templates_tab()
        self._create_send_tab()
        self._create_check_tab()
        self._create_log_tab()
        self._create_settings_tab()
    
    def _create_dolphin_tab(self):
        """Вкладка Dolphin"""
        frame = ctk.CTkFrame(self.tab_dolphin)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(frame, text="🔑 DOLPHIN ANTY TOKEN", font=("Arial", 14, "bold")).pack(pady=10)
        
        ctk.CTkLabel(frame, text="API Token:", font=("Arial", 12)).pack()
        self.token_entry = ctk.CTkEntry(frame, width=400, show="*")
        self.token_entry.pack(pady=5)
        self.token_entry.insert(0, self.dolphin_config.get("token", ""))
        
        def save_token():
            self.dolphin_config["token"] = self.token_entry.get().strip()
            self._save_dolphin_config()
            messagebox.showinfo("Успех", "Токен сохранён")
        
        ctk.CTkButton(frame, text="💾 Сохранить токен", command=save_token).pack(pady=10)
        
        ctk.CTkLabel(frame, text="", font=("Arial", 2)).pack()
        ctk.CTkLabel(frame, text="―" * 60, font=("Arial", 10)).pack(pady=5)
        ctk.CTkLabel(frame, text="", font=("Arial", 2)).pack()
        
        ctk.CTkLabel(frame, text="👤 ПРОФИЛИ DOLPHIN", font=("Arial", 14, "bold")).pack(pady=10)
        ctk.CTkLabel(frame, text="ID профилей (один на строку):", font=("Arial", 12)).pack()
        
        self.profiles_text = ctk.CTkTextbox(frame, width=400, height=150)
        self.profiles_text.pack(pady=5, fill="both", expand=True)
        
        def load_profiles():
            try:
                file = filedialog.askopenfilename(filetypes=[("Text files", "*.txt"), ("All", "*.*")])
                if file:
                    with open(file, 'r', encoding='utf-8') as f:
                        self.profiles_text.delete("1.0", tk.END)
                        self.profiles_text.insert("1.0", f.read())
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))
        
        btn_frame = ctk.CTkFrame(frame)
        btn_frame.pack(fill="x", pady=10)
        ctk.CTkButton(btn_frame, text="📂 Загрузить из файла", command=load_profiles).pack(side="left", padx=5)
        
        def clear_profiles():
            if messagebox.askyesno("Подтверждение", "Очистить все профили?"):
                self.profiles_text.delete("1.0", tk.END)
        ctk.CTkButton(btn_frame, text="🗑️ Очистить", command=clear_profiles, fg_color="red").pack(side="left", padx=5)
    
    def _create_parser_tab(self):
        """Вкладка парсера"""
        frame = ctk.CTkFrame(self.tab_parser)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(frame, text="🛰 КОНФИГУРАЦИЯ ПАРСЕРА", font=("Arial", 14, "bold")).pack(pady=5)
        
        platform_frame = ctk.CTkFrame(frame)
        platform_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(platform_frame, text="Платформа:", font=("Arial", 12)).pack(side="left", padx=5)
        self.parser_platform = ctk.CTkOptionMenu(
            platform_frame,
            values=list(PLATFORMS_CATEGORIES.keys()),
            command=self._on_platform_change
        )
        self.parser_platform.set(self.settings_config["automation"].get("platform", "vinted"))
        self.parser_platform.pack(side="left", padx=5)
        
        ctk.CTkLabel(platform_frame, text="Страна:", font=("Arial", 12)).pack(side="left", padx=5)
        self.parser_country = ctk.CTkEntry(platform_frame, width=100, placeholder_text="IT")
        self.parser_country.pack(side="left", padx=5)
        self.parser_country.insert(0, self.settings_config["automation"].get("country", "IT"))
        
        category_frame = ctk.CTkFrame(frame)
        category_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(category_frame, text="Категория:", font=("Arial", 12)).pack(side="left", padx=5)
        self.parser_category = ctk.CTkOptionMenu(category_frame, values=["Все"])
        self.parser_category.pack(side="left", padx=5)
        self._update_categories()
        
        filters_frame = ctk.CTkFrame(frame)
        filters_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(filters_frame, text="📊 ФИЛЬТРЫ", font=("Arial", 12, "bold")).pack(pady=5)
        
        pub_frame = ctk.CTkFrame(filters_frame)
        pub_frame.pack(fill="x", padx=5, pady=3)
        ctk.CTkLabel(pub_frame, text="Новизна (publication):", width=200).pack(side="left")
        self.parser_publication = ctk.CTkOptionMenu(pub_frame, values=["5m", "15m", "30m", "1h", "24h", "Все"])
        self.parser_publication.set(self.settings_config["parser_filters"].get("publication", "5m"))
        self.parser_publication.pack(side="left", padx=5)
        
        price_frame = ctk.CTkFrame(filters_frame)
        price_frame.pack(fill="x", padx=5, pady=3)
        ctk.CTkLabel(price_frame, text="Цена (например: 10..100):", width=200).pack(side="left")
        self.parser_price = ctk.CTkEntry(price_frame, placeholder_text="0..")
        self.parser_price.pack(side="left", padx=5, fill="x", expand=True)
        self.parser_price.insert(0, self.settings_config["parser_filters"].get("price", ""))
        
        ads_frame = ctk.CTkFrame(filters_frame)
        ads_frame.pack(fill="x", padx=5, pady=3)
        ctk.CTkLabel(ads_frame, text="Объявлений (ads):", width=200).pack(side="left")
        self.parser_ads = ctk.CTkEntry(ads_frame, placeholder_text="0..100")
        self.parser_ads.pack(side="left", padx=5, fill="x", expand=True)
        self.parser_ads.insert(0, self.settings_config["parser_filters"].get("ads", ""))
        
        reviews_frame = ctk.CTkFrame(filters_frame)
        reviews_frame.pack(fill="x", padx=5, pady=3)
        ctk.CTkLabel(reviews_frame, text="Отзывы (reviews):", width=200).pack(side="left")
        self.parser_reviews = ctk.CTkEntry(reviews_frame, placeholder_text="0..50")
        self.parser_reviews.pack(side="left", padx=5, fill="x", expand=True)
        self.parser_reviews.insert(0, self.settings_config["parser_filters"].get("reviews", ""))
        
        delivery_frame = ctk.CTkFrame(filters_frame)
        delivery_frame.pack(fill="x", padx=5, pady=3)
        ctk.CTkLabel(delivery_frame, text="Доставка:", width=200).pack(side="left")
        self.parser_delivery = ctk.CTkOptionMenu(delivery_frame, values=["Любая", "Да", "Нет"])
        self.parser_delivery.set("Любая")
        self.parser_delivery.pack(side="left", padx=5)
        
        phone_frame = ctk.CTkFrame(filters_frame)
        phone_frame.pack(fill="x", padx=5, pady=3)
        ctk.CTkLabel(phone_frame, text="Телефон:", width=200).pack(side="left")
        self.parser_phone = ctk.CTkOptionMenu(phone_frame, values=["Любой", "Да", "Нет"])
        self.parser_phone.set("Любой")
        self.parser_phone.pack(side="left", padx=5)
        
        limit_frame = ctk.CTkFrame(filters_frame)
        limit_frame.pack(fill="x", padx=5, pady=3)
        ctk.CTkLabel(limit_frame, text="Макс результатов:", width=200).pack(side="left")
        self.parser_limit = ctk.CTkEntry(limit_frame, placeholder_text="50")
        self.parser_limit.pack(side="left", padx=5, fill="x", expand=True)
        self.parser_limit.insert(0, self.settings_config["parser_filters"].get("limit", "50"))
        
        btn_frame = ctk.CTkFrame(frame)
        btn_frame.pack(fill="x", pady=15)
        
        def save_filters():
            self.settings_config["parser_filters"]["category"] = self.parser_category.get() if self.parser_category.get() != "Все" else ""
            self.settings_config["parser_filters"]["price"] = self.parser_price.get()
            self.settings_config["parser_filters"]["ads"] = self.parser_ads.get()
            self.settings_config["parser_filters"]["reviews"] = self.parser_reviews.get()
            self.settings_config["parser_filters"]["publication"] = self.parser_publication.get() if self.parser_publication.get() != "Все" else ""
            self.settings_config["parser_filters"]["delivery"] = "true" if self.parser_delivery.get() == "Да" else ("false" if self.parser_delivery.get() == "Нет" else "")
            self.settings_config["parser_filters"]["phone"] = "true" if self.parser_phone.get() == "Да" else ("false" if self.parser_phone.get() == "Нет" else "")
            self.settings_config["parser_filters"]["limit"] = self.parser_limit.get()
            self.settings_config["automation"]["platform"] = self.parser_platform.get()
            self.settings_config["automation"]["country"] = self.parser_country.get()
            self._save_settings_config()
            messagebox.showinfo("Успех", "Фильтры сохранены!")
        
        ctk.CTkButton(btn_frame, text="💾 Сохранить фильтры", command=save_filters).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="🧪 Тест парсера", command=self._test_parser).pack(side="left", padx=5)
    
    def _on_platform_change(self, value):
        self._update_categories()
    
    def _update_categories(self):
        platform = self.parser_platform.get()
        categories = PLATFORMS_CATEGORIES.get(platform, {})
        cat_list = ["Все"] + [f"{k}: {v}" for k, v in categories.items()]
        self.parser_category.configure(values=cat_list)
        self.parser_category.set("Все")
    
    def _test_parser(self):
        thread = threading.Thread(target=self._test_parser_thread, daemon=True)
        thread.start()
    
    def _test_parser_thread(self):
        try:
            self._log("\n" + "="*60)
            self._log("🧪 ТЕСТИРОВАНИЕ ПАРСЕРА")
            self._log("="*60)
            emails_data = self._parse_emails()
            if emails_data:
                self._log(f"✅ Получено {len(emails_data)} результатов\n")
                for idx, item in enumerate(emails_data[:5], 1):
                    self._log(f"  {idx}. Email: {item.get('email', 'N/A')}")
                    self._log(f"     Товар: {item.get('title', 'N/A')}")
                    self._log(f"     Цена: {item.get('price', 'N/A')}")
                    self._log(f"     Ссылка: {item.get('ad_url', 'N/A')[:50]}...")
                    self._log("")
                if len(emails_data) > 5:
                    self._log(f"  ... и ещё {len(emails_data) - 5} результатов")
            else:
                self._log("❌ Нет результатов")
            self._log("="*60)
        except Exception as e:
            self._log(f"❌ Ошибка теста: {e}")
    
    def _create_templates_tab(self):
        frame = ctk.CTkFrame(self.tab_templates)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(frame, text="Первое письмо:", font=("Arial", 12, "bold")).pack(pady=5)
        ctk.CTkLabel(frame, text="Тема:").pack()
        self.first_subject = ctk.CTkEntry(frame, width=400)
        self.first_subject.pack(pady=3)
        self.first_subject.insert(0, self.settings_config["templates"]["first"].get("subject", ""))
        
        ctk.CTkLabel(frame, text="Текст (используй {title}, {price}, {вариант1|вариант2}):").pack()
        self.first_body = ctk.CTkTextbox(frame, width=400, height=80)
        self.first_body.pack(pady=3, fill="both", expand=True)
        self.first_body.insert("1.0", self.settings_config["templates"]["first"].get("body", ""))
        
        ctk.CTkLabel(frame, text="\nОтвет на письмо (HTML):", font=("Arial", 12, "bold")).pack(pady=10)
        ctk.CTkLabel(frame, text="HTML (используй {link}, {price}, {name}):").pack()
        self.reply_body = ctk.CTkTextbox(frame, width=400, height=80)
        self.reply_body.pack(pady=3, fill="both", expand=True)
        self.reply_body.insert("1.0", self.settings_config["templates"]["reply"].get("body", ""))
        
        def save_templates():
            self.settings_config["templates"]["first"]["subject"] = self.first_subject.get()
            self.settings_config["templates"]["first"]["body"] = self.first_body.get("1.0", tk.END)
            self.settings_config["templates"]["reply"]["body"] = self.reply_body.get("1.0", tk.END)
            self._save_settings_config()
            messagebox.showinfo("Успех", "Шаблоны сохранены")
        
        ctk.CTkButton(frame, text="Сохранить", command=save_templates).pack(pady=10)
    
    def _create_send_tab(self):
        frame = ctk.CTkFrame(self.tab_send)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(frame, text="🎫 CREATEAD API", font=("Arial", 14, "bold")).pack(pady=5)
        
        ctk.CTkLabel(frame, text="API ключ парсера:").pack()
        self.send_parser_key = ctk.CTkEntry(frame, width=400, show="*")
        self.send_parser_key.pack(pady=3)
        self.send_parser_key.insert(0, self.settings_config["automation"].get("parser_key", ""))
        
        ctk.CTkLabel(frame, text="User ID:").pack()
        self.send_user_id = ctk.CTkEntry(frame, width=400)
        self.send_user_id.pack(pady=3)
        self.send_user_id.insert(0, self.settings_config["automation"].get("user_id", ""))
        
        ctk.CTkLabel(frame, text="API Key:").pack()
        self.send_api_key = ctk.CTkEntry(frame, width=400, show="*")
        self.send_api_key.pack(pady=3)
        self.send_api_key.insert(0, self.settings_config["automation"].get("api_key", ""))
        
        ctk.CTkLabel(frame, text="Service Code:").pack()
        self.send_service_code = ctk.CTkEntry(frame, width=400)
        self.send_service_code.pack(pady=3)
        self.send_service_code.insert(0, self.settings_config["automation"].get("service_code", "vinted_it"))
        
        ctk.CTkLabel(frame, text="\n📧 УПРАВЛЕНИЕ", font=("Arial", 14, "bold")).pack(pady=5)
        
        ctk.CTkLabel(frame, text="Задержка (сек):").pack()
        self.send_delay = ctk.CTkEntry(frame, width=400)
        self.send_delay.pack(pady=3)
        self.send_delay.insert(0, str(self.settings_config["automation"].get("delay", 5)))
        
        ctk.CTkLabel(frame, text="Макс писем с 1 почты:").pack()
        self.send_max_letters = ctk.CTkEntry(frame, width=400)
        self.send_max_letters.pack(pady=3)
        self.send_max_letters.insert(0, str(self.settings_config["automation"].get("max_letters", 10)))
        
        btn_frame = ctk.CTkFrame(frame)
        btn_frame.pack(pady=15)
        
        self.send_start_btn = ctk.CTkButton(btn_frame, text="▶ СТАРТ", command=self._start_send, fg_color="green")
        self.send_start_btn.pack(side="left", padx=5)
        
        self.send_pause_btn = ctk.CTkButton(btn_frame, text="⏸ ПАУЗА", command=self._pause_send, state="disabled")
        self.send_pause_btn.pack(side="left", padx=5)
        
        self.send_stop_btn = ctk.CTkButton(btn_frame, text="⏹ СТОП", command=self._stop_send, state="disabled", fg_color="red")
        self.send_stop_btn.pack(side="left", padx=5)
        
        self.send_status = ctk.CTkLabel(frame, text="⚪ Готов", font=("Arial", 12))
        self.send_status.pack(pady=10)
    
    def _create_check_tab(self):
        frame = ctk.CTkFrame(self.tab_check)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(frame, text="👤 ПРОФИЛИ", font=("Arial", 14, "bold")).pack(pady=5)
        ctk.CTkLabel(frame, text="Доступные профили:").pack()
        self.check_profiles_label = ctk.CTkLabel(frame, text="Нет открытых профилей", font=("Arial", 11))
        self.check_profiles_label.pack(pady=3)
        
        ctk.CTkLabel(frame, text="\n🎫 CREATEAD", font=("Arial", 14, "bold")).pack(pady=5)
        
        ctk.CTkLabel(frame, text="User ID:").pack()
        self.check_user_id = ctk.CTkEntry(frame, width=400)
        self.check_user_id.pack(pady=3)
        self.check_user_id.insert(0, self.settings_config["automation"].get("user_id", ""))
        
        ctk.CTkLabel(frame, text="API Key:").pack()
        self.check_api_key = ctk.CTkEntry(frame, width=400, show="*")
        self.check_api_key.pack(pady=3)
        self.check_api_key.insert(0, self.settings_config["automation"].get("api_key", ""))
        
        ctk.CTkLabel(frame, text="Service Code:").pack()
        self.check_service_code = ctk.CTkEntry(frame, width=400)
        self.check_service_code.pack(pady=3)
        self.check_service_code.insert(0, self.settings_config["automation"].get("service_code", "vinted_it"))
        
        btn_frame = ctk.CTkFrame(frame)
        btn_frame.pack(pady=15)
        
        self.check_start_btn = ctk.CTkButton(btn_frame, text="🔍 ПРОВЕРИТЬ ОТВЕТЫ", command=self._start_check, fg_color="blue")
        self.check_start_btn.pack(side="left", padx=5)
        
        self.check_stop_btn = ctk.CTkButton(btn_frame, text="⏹ ОСТАНОВИТЬ", command=self._stop_check, state="disabled", fg_color="red")
        self.check_stop_btn.pack(side="left", padx=5)
        
        self.check_status = ctk.CTkLabel(frame, text="⚪ Готов", font=("Arial", 12))
        self.check_status.pack(pady=10)
    
    def _create_log_tab(self):
        frame = ctk.CTkFrame(self.tab_log)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.log_text = scrolledtext.ScrolledText(frame, height=30, width=150, bg="#212121", fg="#00FF00", font=("Courier", 9))
        self.log_text.pack(fill="both", expand=True)
    
    def _create_settings_tab(self):
        frame = ctk.CTkFrame(self.tab_settings)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        ctk.CTkLabel(frame, text="Gmail Sender v3.5", font=("Arial", 18, "bold")).pack(pady=10)
        info = """✅ Отдельные файлы конфигов:
   - dolphin.json (только токен)
   - settings.json (всё остальное)
✅ Dolphin API: GET /start?automation=1
✅ Парсинг automation.port
✅ Spintax {вариант1|вариант2}
✅ CreateAd интеграция
✅ Мультиязычные селекторы Gmail
\nv3.5 - 2026-06-25"""
        ctk.CTkLabel(frame, text=info, font=("Arial", 11), justify="left").pack(pady=10)
    
    def _log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.update()
    
    def _apply_spintax(self, text: str) -> str:
        for _ in range(MAX_SPINTAX_ITERATIONS):
            match = SPINTAX_PATTERN.search(text)
            if not match:
                break
            text = SPINTAX_PATTERN.sub(lambda m: random.choice(m.group(1).split('|')), text, count=1)
        return text
    
    def _validate_dolphin_token(self) -> bool:
        token = self.dolphin_config.get("token", "").strip()
        if not token:
            self._log("❌ Токен Dolphin не установлен!")
            return False
        self._log("\n🔍 Проверка токена Dolphin...")
        url = "http://localhost:3001/v1.0/browser_profiles"
        headers = {"Authorization": "Bearer " + token}
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                self._log("✅ Токен Dolphin действителен")
                return True
            elif response.status_code in (401, 403):
                self._log(f"❌ Ошибка авторизации Dolphin (HTTP {response.status_code})")
                return False
        except:
            self._log("❌ Dolphin Anty недоступен на localhost:3001")
            return False
    
    def _parse_emails(self) -> list:
        try:
            elapsed = time.time() - self.last_parser_request
            if elapsed < 5:
                time.sleep(5 - elapsed)
            self.last_parser_request = time.time()
            
            platform = self.parser_platform.get()
            country = self.parser_country.get()
            api_key = self.send_parser_key.get() or self.settings_config["automation"]["parser_key"]
            url = f"http://vvsproject.xyz/ads/{platform}"
            params = {"country": country, "limit": self.parser_limit.get() or "50"}
            
            if self.parser_category.get() != "Все":
                params["category"] = self.parser_category.get().split(":")[0]
            if self.parser_price.get():
                params["price"] = self.parser_price.get()
            if self.parser_ads.get():
                params["ads"] = self.parser_ads.get()
            if self.parser_reviews.get():
                params["reviews"] = self.parser_reviews.get()
            if self.parser_publication.get() != "Все":
                params["publication"] = self.parser_publication.get()
            if self.parser_delivery.get() != "Любая":
                params["delivery"] = "true" if self.parser_delivery.get() == "Да" else "false"
            if self.parser_phone.get() != "Любой":
                params["phone"] = "true" if self.parser_phone.get() == "Да" else "false"
            
            headers = {"api-key": api_key}
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                sellers = []
                if isinstance(data, dict):
                    for seller_id, seller_data in data.items():
                        sellers.append({
                            'email': seller_data.get('email', ''),
                            'title': seller_data.get('title', ''),
                            'price': seller_data.get('price', ''),
                            'ad_url': seller_data.get('ad_url', ''),
                            'seller': seller_data.get('seller', '')
                        })
                return sellers
        except Exception as e:
            self._log(f"❌ Ошибка парсера: {e}")
        return []
    
    def _start_send(self):
        self.running = True
        self.paused = False
        self.send_start_btn.configure(state="disabled")
        self.send_pause_btn.configure(state="normal")
        self.send_stop_btn.configure(state="normal")
        
        self.settings_config["automation"]["parser_key"] = self.send_parser_key.get()
        self.settings_config["automation"]["user_id"] = self.send_user_id.get()
        self.settings_config["automation"]["api_key"] = self.send_api_key.get()
        self.settings_config["automation"]["delay"] = int(self.send_delay.get() or 5)
        self.settings_config["automation"]["max_letters"] = int(self.send_max_letters.get() or 10)
        self.settings_config["automation"]["service_code"] = self.send_service_code.get()
        self._save_settings_config()
        
        thread = threading.Thread(target=self._send_thread, daemon=True)
        thread.start()
    
    def _send_thread(self):
        try:
            self._log("\n" + "="*60)
            self._log("🚀 НАЧАЛО ОТПРАВКИ")
            self._log("="*60)
            
            profiles = [p.strip() for p in self.profiles_text.get("1.0", tk.END).strip().split('\n') if p.strip() and not p.startswith('#')]
            if not profiles:
                self._log("❌ Нет профилей!")
                self._stop_send()
                return
            
            if not self._validate_dolphin_token():
                self._stop_send()
                return
            
            self._log("\n📡 Парсинг email-ов...")
            emails_data = self._parse_emails()
            if not emails_data:
                self._log("❌ Нет данных от парсера")
                self._stop_send()
                return
            
            self._log(f"✅ Получено {len(emails_data)} email-ов")
            self.sellers_data = {item['email']: item for item in emails_data}
            
            self._log("\n🌐 Открытие профилей...")
            self.drivers_pool = self._open_profiles(profiles)
            if not self.drivers_pool:
                self._log("❌ Не удалось открыть профили")
                self._stop_send()
                return
            
            self._log(f"✅ Открыто {len(self.drivers_pool)} профилей")
            self._log("\n📧 Отправка писем...")
            self._send_first_emails(emails_data, profiles)
            
            self._log("\n" + "="*60)
            self._log("✅ ОТПРАВКА ЗАВЕРШЕНА")
            self._log("="*60)
        except Exception as e:
            self._log(f"❌ Ошибка: {e}")
        finally:
            if self.running:
                self._stop_send()
    
    def _open_profiles(self, profile_ids: list) -> dict:
        drivers = {}
        token = self.dolphin_config.get("token", "").strip()
        if not token:
            return drivers
        
        for profile_id in profile_ids:
            try:
                url = f"http://localhost:3001/v1.0/browser_profiles/{profile_id}/start?automation=1"
                headers = {"Authorization": "Bearer " + token}
                response = requests.get(url, headers=headers, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    port = data.get('automation', {}).get('port')
                    if port:
                        options = webdriver.ChromeOptions()
                        options.add_experimental_option('debuggerAddress', f'localhost:{port}')
                        driver = webdriver.Chrome(options=options)
                        drivers[profile_id] = driver
                        self._log(f"  ✅ {profile_id}")
            except:
                pass
        
        return drivers
    
    def _send_first_emails(self, emails_data: list, profiles: list):
        for idx, item in enumerate(emails_data):
            if not self.running:
                break
            if self.paused:
                while self.paused and self.running:
                    time.sleep(1)
            
            email = item.get('email')
            if not email:
                continue
            
            profile_id = profiles[idx % len(profiles)]
            driver = self.drivers_pool.get(profile_id)
            if not driver:
                continue
            
            try:
                subject = self._apply_spintax(self.settings_config["templates"]["first"]["subject"])
                body = self.settings_config["templates"]["first"]["body"]
                body = body.replace("{title}", item.get('title', ''))
                body = body.replace("{price}", item.get('price', ''))
                body = self._apply_spintax(body)
                
                self._send_email(driver, email, subject, body)
                self._log(f"✉️ {email}")
                time.sleep(self.settings_config["automation"].get("delay", 5))
            except:
                pass
    
    def _send_email(self, driver, to_email: str, subject: str, body: str):
        wait = WebDriverWait(driver, 40)
        driver.get("https://mail.google.com/mail/u/0/#compose")
        time.sleep(3)
        
        to_field = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'input[aria-label="To"], input[aria-label="Кому"]')))
        to_field.send_keys(to_email)
        time.sleep(1)
        
        subject_field = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'input[aria-label="Subject"], input[aria-label="Тема"]')))
        subject_field.send_keys(subject)
        time.sleep(1)
        
        body_field = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[role="textbox"]')))
        driver.execute_script("arguments[0].innerHTML = arguments[1];", body_field, body)
        time.sleep(2)
        
        send_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[aria-label="Send"], button[aria-label="Отправить"]')))
        send_btn.click()
        time.sleep(2)
    
    def _pause_send(self):
        self.paused = not self.paused
        if self.paused:
            self.send_pause_btn.configure(text="▶ ПРОДОЛЖИТЬ")
        else:
            self.send_pause_btn.configure(text="⏸ ПАУЗА")
    
    def _stop_send(self):
        self.running = False
        self.paused = False
        self.send_start_btn.configure(state="normal")
        self.send_pause_btn.configure(state="disabled", text="⏸ ПАУЗА")
        self.send_stop_btn.configure(state="disabled")
    
    def _get_createad_link(self, original_url: str) -> str:
        user_id = self.settings_config["automation"].get("user_id", "")
        api_key = self.settings_config["automation"].get("api_key", "")
        service_code = self.settings_config["automation"].get("service_code", "vinted_it")
        
        if not all([user_id, api_key, service_code, original_url]):
            return original_url
        
        try:
            url = "https://createad.ru/api/v1/get_link"
            response = requests.post(url, json={"user_id": user_id, "api_key": api_key, "service_code": service_code, "original_url": original_url}, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get('link') or data.get('url') or data.get('html_url') or original_url
        except:
            pass
        return original_url
    
    def _start_check(self):
        if not self.drivers_pool:
            messagebox.showerror("Ошибка", "Нет открытых профилей!")
            return
        
        self.running = True
        self.check_start_btn.configure(state="disabled")
        self.check_stop_btn.configure(state="normal")
        self.settings_config["automation"]["user_id"] = self.check_user_id.get()
        self.settings_config["automation"]["api_key"] = self.check_api_key.get()
        self.settings_config["automation"]["service_code"] = self.check_service_code.get()
        self._save_settings_config()
        
        thread = threading.Thread(target=self._check_thread, daemon=True)
        thread.start()
    
    def _check_thread(self):
        try:
            self._log("\n" + "="*60)
            self._log("💬 ПРОВЕРКА ОТВЕТОВ")
            self._log("="*60)
            total = 0
            for pid, driver in self.drivers_pool.items():
                if not self.running:
                    break
                replied = self._check_and_reply(driver, pid)
                total += replied
            self._log(f"✅ ВСЕГО: {total} ответов")
            self._log("="*60)
        except Exception as e:
            self._log(f"❌ {e}")
        finally:
            if self.running:
                self._stop_check()
    
    def _check_and_reply(self, driver, profile_id: str) -> int:
        replied = 0
        try:
            driver.get("https://mail.google.com/mail/u/0/#inbox")
            time.sleep(3)
            rows = driver.find_elements(By.CSS_SELECTOR, 'tr.zE')
            
            for row in rows[:10]:
                if not self.running:
                    break
                try:
                    row.click()
                    time.sleep(2)
                    try:
                        sender_email = driver.find_element(By.CSS_SELECTOR, 'span[email]').get_attribute('email')
                    except:
                        sender_email = None
                    
                    if not sender_email or sender_email not in self.sellers_data:
                        driver.get("https://mail.google.com/mail/u/0/#inbox")
                        time.sleep(2)
                        continue
                    
                    seller_data = self.sellers_data[sender_email]
                    new_url = self._get_createad_link(seller_data.get('ad_url', ''))
                    html = self.settings_config["templates"]["reply"]["body"]
                    html = html.replace("{link}", new_url).replace("{price}", seller_data.get('price', '')).replace("{name}", sender_email.split('@')[0])
                    html = self._apply_spintax(html)
                    
                    self._reply_to_email(driver, html)
                    self._log(f"  ✅ {sender_email}")
                    replied += 1
                    time.sleep(2)
                    driver.get("https://mail.google.com/mail/u/0/#inbox")
                    time.sleep(2)
                except:
                    pass
        except:
            pass
        return replied
    
    def _reply_to_email(self, driver, html_body: str):
        wait = WebDriverWait(driver, 40)
        reply_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[aria-label="Reply"], div[aria-label="Ответить"], button[aria-label="Reply"], button[aria-label="Ответить"]')))
        reply_btn.click()
        time.sleep(2)
        reply_field = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[role="textbox"]')))
        driver.execute_script("arguments[0].innerHTML = arguments[1];", reply_field, html_body)
        time.sleep(2)
        send_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[aria-label="Send"], button[aria-label="Отправить"]')))
        send_btn.click()
        time.sleep(2)
    
    def _stop_check(self):
        self.running = False
        self.check_start_btn.configure(state="normal")
        self.check_stop_btn.configure(state="disabled")

if __name__ == "__main__":
    app = App()
    app.mainloop()
