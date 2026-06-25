import customtkinter as ctk
import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox
import threading
import json
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import re

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Категории для каждой платформы
PLATFORMS_CATEGORIES = {
    "vinted": {"1": "детское", "2": "дизайнерское", "3": "для дома", "4": "женское", "5": "мужское", "6": "развлечения", "7": "спорт", "8": "электроника"},
    "2dehands": {"1": "антиквариат", "2": "аудио и фото", "3": "бытовая техника", "4": "детские товары", "5": "диски", "6": "женская одежда", "7": "игры", "8": "книги"},
    "bakeca": {"1": "антиквариат", "2": "велосипеды", "3": "детские товары", "4": "книги и комиксы", "5": "кухня и техника", "6": "мебель", "7": "муз. инструменты", "8": "музыка и фильмы"},
    "bazaraki": {"1": "бизнес", "2": "детские товары", "3": "дом и сад", "4": "компьютеры", "5": "красота и здоровье", "6": "одежда и аксессуары", "7": "телефоны", "8": "хобби и спорт", "9": "электроника"},
    "carousell": {"1": "аудио", "2": "видеоигры", "3": "дети", "4": "женская мода", "5": "здоровье", "6": "зоотовары", "7": "компьютеры", "8": "красота", "9": "люкс", "10": "мебель"},
    "depop": {"1": "детское", "2": "женское", "3": "мужское"},
    "etsy": {"1": "аксессуары", "2": "детские товары", "3": "дом и быт", "4": "игрушки", "5": "искусство", "6": "книги", "7": "косметика", "8": "обувь", "9": "одежда", "10": "праздники"},
    "kleinanzeigen": {"1": "велосипеды", "2": "досуг и хобби", "3": "дом и сад", "4": "мода", "5": "музыка и книги", "6": "семья и дети", "7": "животные", "8": "электроника"},
    "marktplaats": {"1": "антиквариат", "2": "аудио и фото", "3": "бытовая техника", "4": "детские товары", "5": "диски", "6": "женская одежда", "7": "игры", "8": "книги"},
    "mercari": {"1": "детские товары", "2": "дом и быт", "3": "женская одежда", "4": "игры", "5": "книги", "6": "косметика", "7": "мужская одежда", "8": "музыка", "9": "обувь", "10": "спорт"},
    "olx": {"1": "антиквариат", "2": "дом и сад", "3": "для детей", "4": "мода", "5": "спорт", "6": "электроника"},
    "wallapop": {"1": "бытовая техника", "2": "велосипеды", "3": "детские товары", "4": "дом и сад", "5": "книги", "6": "коллекционные", "7": "одежда", "8": "прочее", "9": "спорт", "10": "электроника"},
}

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Gmail Sender v3.2")
        self.geometry("1400x800")
        
        self.running = False
        self.paused = False
        self.drivers_pool = {}
        self.sellers_data = {}
        self.last_parser_request = 0
        
        self._load_config()
        self._create_ui()
    
    def _load_config(self):
        """Загружает конфиг из config.json"""
        try:
            with open('config.json', 'r') as f:
                self.config = json.load(f)
        except:
            self.config = {
                "token": "",
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
    
    def _save_config(self):
        """Сохраняет конфиг в config.json"""
        try:
            with open('config.json', 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            self._log(f"❌ Ошибка сохранения конфига: {e}")
    
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
        """Вкладка Dolphin с токеном и профилями"""
        frame = ctk.CTkFrame(self.tab_dolphin)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Токен
        ctk.CTkLabel(frame, text="🔑 DOLPHIN ANTY TOKEN", font=("Arial", 14, "bold")).pack(pady=10)
        
        ctk.CTkLabel(frame, text="API Token:", font=("Arial", 12)).pack()
        self.token_entry = ctk.CTkEntry(frame, width=400, show="*")
        self.token_entry.pack(pady=5)
        self.token_entry.insert(0, self.config.get("token", ""))
        
        def save_token():
            self.config["token"] = self.token_entry.get()
            self._save_config()
            messagebox.showinfo("Успех", "Токен сохранён")
        
        ctk.CTkButton(frame, text="💾 Сохранить токен", command=save_token).pack(pady=10)
        
        # Разделитель
        ctk.CTkLabel(frame, text="", font=("Arial", 2)).pack()
        ctk.CTkLabel(frame, text="―" * 60, font=("Arial", 10)).pack(pady=5)
        ctk.CTkLabel(frame, text="", font=("Arial", 2)).pack()
        
        # Профили
        ctk.CTkLabel(frame, text="👤 ПРОФИЛИ DOLPHIN", font=("Arial", 14, "bold")).pack(pady=10)
        
        ctk.CTkLabel(frame, text="ID профилей (один на строку):", font=("Arial", 12)).pack()
        
        self.profiles_text = ctk.CTkTextbox(frame, width=400, height=150)
        self.profiles_text.pack(pady=5, fill="both", expand=True)
        
        def load_profiles():
            try:
                file = filedialog.askopenfilename(filetypes=[("Text files", "*.txt"), ("All", "*.*")])
                if file:
                    with open(file, 'r') as f:
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
        """Вкладка парсера с фильтрами"""
        frame = ctk.CTkFrame(self.tab_parser)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Заголовок
        ctk.CTkLabel(frame, text="🛰 КОНФИГУРАЦИЯ ПАРСЕРА", font=("Arial", 14, "bold")).pack(pady=5)
        
        # Платформа и страна
        platform_frame = ctk.CTkFrame(frame)
        platform_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(platform_frame, text="Платформа:", font=("Arial", 12)).pack(side="left", padx=5)
        self.parser_platform = ctk.CTkOptionMenu(
            platform_frame,
            values=list(PLATFORMS_CATEGORIES.keys()),
            command=self._on_platform_change
        )
        self.parser_platform.set(self.config["automation"].get("platform", "vinted"))
        self.parser_platform.pack(side="left", padx=5)
        
        ctk.CTkLabel(platform_frame, text="Страна:", font=("Arial", 12)).pack(side="left", padx=5)
        self.parser_country = ctk.CTkEntry(platform_frame, width=100, placeholder_text="IT")
        self.parser_country.pack(side="left", padx=5)
        self.parser_country.insert(0, self.config["automation"].get("country", "IT"))
        
        # Категория
        category_frame = ctk.CTkFrame(frame)
        category_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(category_frame, text="Категория:", font=("Arial", 12)).pack(side="left", padx=5)
        self.parser_category = ctk.CTkOptionMenu(category_frame, values=["Все"])
        self.parser_category.pack(side="left", padx=5)
        self._update_categories()
        
        # Фильтры (основные)
        filters_frame = ctk.CTkFrame(frame)
        filters_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(filters_frame, text="📊 ФИЛЬТРЫ", font=("Arial", 12, "bold")).pack(pady=5)
        
        # Publication (важно для свежих email-ов)
        pub_frame = ctk.CTkFrame(filters_frame)
        pub_frame.pack(fill="x", padx=5, pady=3)
        ctk.CTkLabel(pub_frame, text="Новизна (publication):", width=200).pack(side="left")
        self.parser_publication = ctk.CTkOptionMenu(
            pub_frame,
            values=["5m", "15m", "30m", "1h", "24h", "Все"]
        )
        self.parser_publication.set(self.config["parser_filters"].get("publication", "5m"))
        self.parser_publication.pack(side="left", padx=5)
        
        # Цена
        price_frame = ctk.CTkFrame(filters_frame)
        price_frame.pack(fill="x", padx=5, pady=3)
        ctk.CTkLabel(price_frame, text="Цена (например: 10..100):", width=200).pack(side="left")
        self.parser_price = ctk.CTkEntry(price_frame, placeholder_text="0..")
        self.parser_price.pack(side="left", padx=5, fill="x", expand=True)
        self.parser_price.insert(0, self.config["parser_filters"].get("price", ""))
        
        # Количество объявлений продавца
        ads_frame = ctk.CTkFrame(filters_frame)
        ads_frame.pack(fill="x", padx=5, pady=3)
        ctk.CTkLabel(ads_frame, text="Объявлений (ads):", width=200).pack(side="left")
        self.parser_ads = ctk.CTkEntry(ads_frame, placeholder_text="0..100")
        self.parser_ads.pack(side="left", padx=5, fill="x", expand=True)
        self.parser_ads.insert(0, self.config["parser_filters"].get("ads", ""))
        
        # Отзывы
        reviews_frame = ctk.CTkFrame(filters_frame)
        reviews_frame.pack(fill="x", padx=5, pady=3)
        ctk.CTkLabel(reviews_frame, text="Отзывы (reviews):", width=200).pack(side="left")
        self.parser_reviews = ctk.CTkEntry(reviews_frame, placeholder_text="0..50")
        self.parser_reviews.pack(side="left", padx=5, fill="x", expand=True)
        self.parser_reviews.insert(0, self.config["parser_filters"].get("reviews", ""))
        
        # Доставка
        delivery_frame = ctk.CTkFrame(filters_frame)
        delivery_frame.pack(fill="x", padx=5, pady=3)
        ctk.CTkLabel(delivery_frame, text="Доставка:", width=200).pack(side="left")
        self.parser_delivery = ctk.CTkOptionMenu(delivery_frame, values=["Любая", "Да", "Нет"])
        self.parser_delivery.set("Любая")
        self.parser_delivery.pack(side="left", padx=5)
        
        # Телефон
        phone_frame = ctk.CTkFrame(filters_frame)
        phone_frame.pack(fill="x", padx=5, pady=3)
        ctk.CTkLabel(phone_frame, text="Телефон:", width=200).pack(side="left")
        self.parser_phone = ctk.CTkOptionMenu(phone_frame, values=["Любой", "Да", "Нет"])
        self.parser_phone.set("Любой")
        self.parser_phone.pack(side="left", padx=5)
        
        # Лимит результатов
        limit_frame = ctk.CTkFrame(filters_frame)
        limit_frame.pack(fill="x", padx=5, pady=3)
        ctk.CTkLabel(limit_frame, text="Макс результатов:", width=200).pack(side="left")
        self.parser_limit = ctk.CTkEntry(limit_frame, placeholder_text="50")
        self.parser_limit.pack(side="left", padx=5, fill="x", expand=True)
        self.parser_limit.insert(0, self.config["parser_filters"].get("limit", "50"))
        
        # Кнопки управления
        btn_frame = ctk.CTkFrame(frame)
        btn_frame.pack(fill="x", pady=15)
        
        def save_filters():
            self.config["parser_filters"]["category"] = self.parser_category.get() if self.parser_category.get() != "Все" else ""
            self.config["parser_filters"]["price"] = self.parser_price.get()
            self.config["parser_filters"]["ads"] = self.parser_ads.get()
            self.config["parser_filters"]["reviews"] = self.parser_reviews.get()
            self.config["parser_filters"]["publication"] = self.parser_publication.get() if self.parser_publication.get() != "Все" else ""
            self.config["parser_filters"]["delivery"] = "true" if self.parser_delivery.get() == "Да" else ("false" if self.parser_delivery.get() == "Нет" else "")
            self.config["parser_filters"]["phone"] = "true" if self.parser_phone.get() == "Да" else ("false" if self.parser_phone.get() == "Нет" else "")
            self.config["parser_filters"]["limit"] = self.parser_limit.get()
            self.config["automation"]["platform"] = self.parser_platform.get()
            self.config["automation"]["country"] = self.parser_country.get()
            self._save_config()
            messagebox.showinfo("Успех", "Фильтры сохранены!")
        
        ctk.CTkButton(btn_frame, text="💾 Сохранить фильтры", command=save_filters).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="🧪 Тест парсера", command=self._test_parser).pack(side="left", padx=5)
    
    def _on_platform_change(self, value):
        """Обновляет категории при смене платформы"""
        self._update_categories()
    
    def _update_categories(self):
        """Обновляет список категорий"""
        platform = self.parser_platform.get()
        categories = PLATFORMS_CATEGORIES.get(platform, {})
        cat_list = ["Все"] + [f"{k}: {v}" for k, v in categories.items()]
        self.parser_category.configure(values=cat_list)
        self.parser_category.set("Все")
    
    def _test_parser(self):
        """Тестирует парсер и показывает результаты"""
        thread = threading.Thread(target=self._test_parser_thread, daemon=True)
        thread.start()
    
    def _test_parser_thread(self):
        """Поток тестирования парсера"""
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
        """Вкладка шаблонов"""
        frame = ctk.CTkFrame(self.tab_templates)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        label1 = ctk.CTkLabel(frame, text="Первое письмо:", font=("Arial", 12, "bold"))
        label1.pack(pady=5)
        
        ctk.CTkLabel(frame, text="Тема:").pack()
        self.first_subject = ctk.CTkEntry(frame, width=400)
        self.first_subject.pack(pady=3)
        self.first_subject.insert(0, self.config["templates"]["first"].get("subject", ""))
        
        ctk.CTkLabel(frame, text="Текст (используй {title}, {price}):").pack()
        self.first_body = ctk.CTkTextbox(frame, width=400, height=80)
        self.first_body.pack(pady=3, fill="both", expand=True)
        self.first_body.insert("1.0", self.config["templates"]["first"].get("body", ""))
        
        label2 = ctk.CTkLabel(frame, text="\nОтвет на письмо (HTML):", font=("Arial", 12, "bold"))
        label2.pack(pady=10)
        
        ctk.CTkLabel(frame, text="HTML (используй {link}, {price}, {name}):").pack()
        self.reply_body = ctk.CTkTextbox(frame, width=400, height=80)
        self.reply_body.pack(pady=3, fill="both", expand=True)
        self.reply_body.insert("1.0", self.config["templates"]["reply"].get("body", ""))
        
        def save_templates():
            self.config["templates"]["first"]["subject"] = self.first_subject.get()
            self.config["templates"]["first"]["body"] = self.first_body.get("1.0", tk.END)
            self.config["templates"]["reply"]["body"] = self.reply_body.get("1.0", tk.END)
            self._save_config()
            messagebox.showinfo("Успех", "Шаблоны сохранены")
        
        btn = ctk.CTkButton(frame, text="Сохранить", command=save_templates)
        btn.pack(pady=10)
    
    def _create_send_tab(self):
        """Вкладка отправки"""
        frame = ctk.CTkFrame(self.tab_send)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(frame, text="🎫 CREATEAD API", font=("Arial", 14, "bold")).pack(pady=5)
        
        ctk.CTkLabel(frame, text="API ключ парсера:").pack()
        self.send_parser_key = ctk.CTkEntry(frame, width=400, show="*")
        self.send_parser_key.pack(pady=3)
        self.send_parser_key.insert(0, self.config["automation"].get("parser_key", ""))
        
        ctk.CTkLabel(frame, text="User ID:").pack()
        self.send_user_id = ctk.CTkEntry(frame, width=400)
        self.send_user_id.pack(pady=3)
        self.send_user_id.insert(0, self.config["automation"].get("user_id", ""))
        
        ctk.CTkLabel(frame, text="API Key:").pack()
        self.send_api_key = ctk.CTkEntry(frame, width=400, show="*")
        self.send_api_key.pack(pady=3)
        self.send_api_key.insert(0, self.config["automation"].get("api_key", ""))
        
        ctk.CTkLabel(frame, text="Service Code:").pack()
        self.send_service_code = ctk.CTkEntry(frame, width=400)
        self.send_service_code.pack(pady=3)
        self.send_service_code.insert(0, self.config["automation"].get("service_code", "vinted_it"))
        
        ctk.CTkLabel(frame, text="\n📧 УПРАВЛЕНИЕ", font=("Arial", 14, "bold")).pack(pady=5)
        
        ctk.CTkLabel(frame, text="Задержка (сек):").pack()
        self.send_delay = ctk.CTkEntry(frame, width=400)
        self.send_delay.pack(pady=3)
        self.send_delay.insert(0, str(self.config["automation"].get("delay", 5)))
        
        ctk.CTkLabel(frame, text="Макс писем с 1 почты:").pack()
        self.send_max_letters = ctk.CTkEntry(frame, width=400)
        self.send_max_letters.pack(pady=3)
        self.send_max_letters.insert(0, str(self.config["automation"].get("max_letters", 10)))
        
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
        """Вкладка проверки ответов"""
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
        self.check_user_id.insert(0, self.config["automation"].get("user_id", ""))
        
        ctk.CTkLabel(frame, text="API Key:").pack()
        self.check_api_key = ctk.CTkEntry(frame, width=400, show="*")
        self.check_api_key.pack(pady=3)
        self.check_api_key.insert(0, self.config["automation"].get("api_key", ""))
        
        ctk.CTkLabel(frame, text="Service Code:").pack()
        self.check_service_code = ctk.CTkEntry(frame, width=400)
        self.check_service_code.pack(pady=3)
        self.check_service_code.insert(0, self.config["automation"].get("service_code", "vinted_it"))
        
        btn_frame = ctk.CTkFrame(frame)
        btn_frame.pack(pady=15)
        
        self.check_start_btn = ctk.CTkButton(btn_frame, text="🔍 ПРОВЕРИТЬ ОТВЕТЫ", command=self._start_check, fg_color="blue")
        self.check_start_btn.pack(side="left", padx=5)
        
        self.check_stop_btn = ctk.CTkButton(btn_frame, text="⏹ ОСТАНОВИТЬ", command=self._stop_check, state="disabled", fg_color="red")
        self.check_stop_btn.pack(side="left", padx=5)
        
        self.check_status = ctk.CTkLabel(frame, text="⚪ Готов", font=("Arial", 12))
        self.check_status.pack(pady=10)
    
    def _create_log_tab(self):
        """Вкладка логирования"""
        frame = ctk.CTkFrame(self.tab_log)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.log_text = scrolledtext.ScrolledText(frame, height=30, width=150, bg="#212121", fg="#00FF00", font=("Courier", 9))
        self.log_text.pack(fill="both", expand=True)
    
    def _create_settings_tab(self):
        """Вкладка настроек"""
        frame = ctk.CTkFrame(self.tab_settings)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(frame, text="Gmail Sender v3.2", font=("Arial", 18, "bold")).pack(pady=10)
        ctk.CTkLabel(frame, text="Автоматизация рассылки писем с интеллектуальным парсером", font=("Arial", 12)).pack(pady=5)
        
        info = """✅ Вкладка "Dolphin" с токеном и профилями
✅ Динамический парсер всех платформ
✅ Выбор категории и фильтров для свежих email-ов
✅ Сохранение пресетов фильтров
✅ Отправка первых писем через Gmail
✅ Проверка ответов и рассылка HTML
✅ Интеграция с CreateAd API
✅ Персонализация писем {title}, {price}, {name}
✅ Подробное логирование Dolphin API

v3.2 - 2026-06-25"""
        
        ctk.CTkLabel(frame, text=info, font=("Arial", 11), justify="left").pack(pady=10)
    
    def _log(self, message):
        """Логирование"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.update()
    
    def _parse_emails(self) -> list:
        """Получает email-ы через парсер API"""
        try:
            # Лимит 1 запрос в 5 сек
            elapsed = time.time() - self.last_parser_request
            if elapsed < 5:
                time.sleep(5 - elapsed)
            self.last_parser_request = time.time()
            
            platform = self.parser_platform.get()
            country = self.parser_country.get()
            api_key = self.send_parser_key.get() or self.config["automation"]["parser_key"]
            
            url = f"http://vvsproject.xyz/ads/{platform}"
            
            params = {
                "country": country,
                "limit": self.parser_limit.get() or "50"
            }
            
            # Добавляем фильтры если они заполнены
            if self.parser_category.get() != "Все":
                cat_num = self.parser_category.get().split(":")[0]
                params["category"] = cat_num
            
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
            
            self._log(f"📡 Запрос к парсеру: {platform} | Параметры: {params}")
            
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                sellers = []
                
                # Преобразуем формат ответа в нужный
                for seller_id, seller_data in data.items():
                    sellers.append({
                        'email': seller_data.get('email', ''),
                        'title': seller_data.get('title', ''),
                        'price': seller_data.get('price', ''),
                        'ad_url': seller_data.get('ad_url', ''),
                        'seller': seller_data.get('seller', '')
                    })
                
                return sellers
            elif response.status_code == 402:
                self._log("❌ Ошибка: Нет подписки")
            elif response.status_code == 403:
                self._log("❌ Ошибка: Неверный api-key")
            elif response.status_code == 404:
                self._log("❌ Ошибка: Платформа не найдена")
            elif response.status_code == 422:
                self._log("❌ Ошибка: API ключ не передан")
            elif response.status_code == 429:
                self._log("❌ Ошибка: Превышен лимит запросов (1 в 5 сек)")
            else:
                self._log(f"❌ Ошибка парсера: {response.status_code}")
            
            return []
        except Exception as e:
            self._log(f"❌ Ошибка подключения: {e}")
            return []
    
    def _start_send(self):
        """Начало отправки"""
        self.running = True
        self.paused = False
        self.send_start_btn.configure(state="disabled")
        self.send_pause_btn.configure(state="normal")
        self.send_stop_btn.configure(state="normal")
        self.send_status.configure(text="🟡 Работаю...")
        
        self.config["automation"]["parser_key"] = self.send_parser_key.get()
        self.config["automation"]["user_id"] = self.send_user_id.get()
        self.config["automation"]["api_key"] = self.send_api_key.get()
        self.config["automation"]["delay"] = int(self.send_delay.get() or 5)
        self.config["automation"]["max_letters"] = int(self.send_max_letters.get() or 10)
        self.config["automation"]["service_code"] = self.send_service_code.get()
        self._save_config()
        
        thread = threading.Thread(target=self._send_thread, daemon=True)
        thread.start()
    
    def _send_thread(self):
        """Поток отправки"""
        try:
            self._log("\n" + "="*60)
            self._log("🚀 НАЧАЛО ОТПРАВКИ ПИСЕМ")
            self._log("="*60)
            
            profiles_text = self.profiles_text.get("1.0", tk.END).strip()
            profiles = [p.strip() for p in profiles_text.split('\n') if p.strip() and not p.startswith('#')]
            
            if not profiles:
                self._log("❌ Нет профилей!")
                self._stop_send()
                return
            
            self._log(f"✅ Загружено {len(profiles)} профилей")
            
            self._log("\n📡 Парсинг email-ов...")
            emails_data = self._parse_emails()
            if not emails_data:
                self._log("❌ Ошибка парсинга")
                self._stop_send()
                return
            
            self._log(f"✅ Получено {len(emails_data)} email-ов")
            self.sellers_data = {item['email']: item for item in emails_data}
            
            self._log("\n🌐 Открытие профилей Dolphin...")
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
        """Открывает профили Dolphin с подробным логированием"""
        drivers = {}
        token = self.config.get("token", "")
        
        if not token:
            self._log("❌ Ошибка: Токен не установлен!")
            return drivers
        
        for profile_id in profile_ids:
            try:
                self._log(f"\n  📋 Профиль: {profile_id}")
                
                url = "http://localhost:3001/v1/browser/start-browser"
                payload = {"browserId": profile_id}
                headers = {"Authorization": f"Bearer {token}"}
                
                self._log(f"  📤 POST {url}")
                self._log(f"  📦 Body: {payload}")
                self._log(f"  🔐 Headers: Authorization Bearer [скрыто]")
                
                response = requests.post(url, json=payload, headers=headers, timeout=30)
                
                self._log(f"  📥 Status Code: {response.status_code}")
                self._log(f"  📥 Response: {response.text}")
                
                if response.status_code == 200:
                    driver_info = response.json()
                    self._log(f"  ✅ Ответ: {json.dumps(driver_info, indent=2)}")
                    
                    # Ищем WebSocket URL
                    ws_url = driver_info.get('webSocketDebuggerUrl', '')
                    if not ws_url:
                        self._log(f"  ❌ Ошибка: webSocketDebuggerUrl не найден в ответе")
                        continue
                    
                    self._log(f"  🔗 WebSocket URL: {ws_url}")
                    
                    driver_port = ws_url.split(':')[-1]
                    self._log(f"  🔌 Порт: {driver_port}")
                    
                    options = webdriver.ChromeOptions()
                    options.add_experimental_option('debuggerAddress', f'localhost:{driver_port}')
                    driver = webdriver.Chrome(options=options)
                    
                    drivers[profile_id] = driver
                    self._log(f"  ✅ Профиль {profile_id} успешно открыт!")
                else:
                    self._log(f"  ❌ HTTP Error: {response.status_code}")
                    try:
                        error_data = response.json()
                        self._log(f"  📋 Error Details: {json.dumps(error_data, indent=2)}")
                    except:
                        self._log(f"  📋 Response Body: {response.text}")
            
            except requests.exceptions.ConnectionError as e:
                self._log(f"  ❌ Ошибка подключения: {e}")
                self._log(f"  💡 Проверьте: запущен ли Dolphin Anty на localhost:3001?")
            except requests.exceptions.Timeout as e:
                self._log(f"  ❌ Timeout: {e}")
            except Exception as e:
                self._log(f"  ❌ Неожиданная ошибка: {e}")
                import traceback
                self._log(f"  📋 Traceback: {traceback.format_exc()}")
        
        return drivers
    
    def _send_first_emails(self, emails_data: list, profiles: list):
        """Отправляет письма"""
        delay = self.config["automation"].get("delay", 5)
        
        for idx, item in enumerate(emails_data):
            if not self.running:
                self._log("⏹ Остановлено")
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
                self._log(f"❌ Профиль {profile_id} недоступен")
                continue
            
            try:
                subject = self.config["templates"]["first"]["subject"]
                body = self.config["templates"]["first"]["body"]
                
                body = body.replace("{title}", item.get('title', ''))
                body = body.replace("{price}", item.get('price', ''))
                
                self._send_email(driver, email, subject, body)
                self._log(f"✉️  {email} отправлено")
                
                time.sleep(delay)
            except Exception as e:
                self._log(f"❌ Ошибка {email}: {e}")
    
    def _send_email(self, driver, to_email: str, subject: str, body: str):
        """Отправляет письмо"""
        wait = WebDriverWait(driver, 40)
        
        driver.get("https://mail.google.com/mail/u/0/#compose")
        time.sleep(3)
        
        to_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[aria-label="To"]')))
        to_field.clear()
        to_field.send_keys(to_email)
        time.sleep(1)
        
        subject_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[aria-label="Subject"]')))
        subject_field.clear()
        subject_field.send_keys(subject)
        time.sleep(1)
        
        body_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="textbox"]')))
        driver.execute_script("arguments[0].innerHTML = arguments[1]; arguments[0].dispatchEvent(new Event('input', {bubbles: true}));", body_field, body)
        time.sleep(2)
        
        send_btn = driver.find_element(By.CSS_SELECTOR, 'button[aria-label="Send"]')
        send_btn.click()
        time.sleep(2)
    
    def _pause_send(self):
        """Пауза"""
        self.paused = not self.paused
        if self.paused:
            self.send_pause_btn.configure(text="▶ ПРОДОЛЖИТЬ")
            self.send_status.configure(text="⏸ Пауза")
        else:
            self.send_pause_btn.configure(text="⏸ ПАУЗА")
            self.send_status.configure(text="🟡 Работаю...")
    
    def _stop_send(self):
        """Остановка"""
        self.running = False
        self.paused = False
        self.send_start_btn.configure(state="normal")
        self.send_pause_btn.configure(state="disabled", text="⏸ ПАУЗА")
        self.send_stop_btn.configure(state="disabled")
        self.send_status.configure(text="⚪ Готов")
        self._log("⏹ Остановлено")
    
    def _start_check(self):
        """Начало проверки ответов"""
        if not self.drivers_pool:
            messagebox.showerror("Ошибка", "Нет открытых профилей!")
            return
        
        self.running = True
        self.check_start_btn.configure(state="disabled")
        self.check_stop_btn.configure(state="normal")
        self.check_status.configure(text="🟡 Проверяю...")
        
        profiles_list = ", ".join(self.drivers_pool.keys())
        self.check_profiles_label.configure(text=f"Открытые: {profiles_list}")
        
        self.config["automation"]["user_id"] = self.check_user_id.get()
        self.config["automation"]["api_key"] = self.check_api_key.get()
        self.config["automation"]["service_code"] = self.check_service_code.get()
        self._save_config()
        
        thread = threading.Thread(target=self._check_thread, daemon=True)
        thread.start()
    
    def _check_thread(self):
        """Поток проверки"""
        try:
            self._log("\n" + "="*60)
            self._log("💬 ПРОВЕРКА ОТВЕТОВ")
            self._log("="*60)
            
            total_replied = 0
            
            for profile_id, driver in self.drivers_pool.items():
                if not self.running:
                    break
                
                self._log(f"\n🔍 Проверяю {profile_id}...")
                
                try:
                    replied = self._check_and_reply(driver, profile_id)
                    total_replied += replied
                    self._log(f"✅ {replied} ответов")
                except Exception as e:
                    self._log(f"❌ Ошибка: {e}")
            
            self._log("\n" + "="*60)
            self._log(f"✅ ВСЕГО: {total_replied} ответов")
            self._log("="*60)
            
        except Exception as e:
            self._log(f"❌ Ошибка: {e}")
        finally:
            if self.running:
                self._stop_check()
    
    def _check_and_reply(self, driver, profile_id: str) -> int:
        """Проверяет и отправляет ответы"""
        replied = 0
        wait = WebDriverWait(driver, 40)
        user_id = self.config["automation"]["user_id"]
        api_key = self.config["automation"]["api_key"]
        service_code = self.config["automation"]["service_code"]
        
        try:
            driver.get("https://mail.google.com/mail/u/0/#inbox")
            time.sleep(3)
            
            unread_rows = driver.find_elements(By.CSS_SELECTOR, 'tr.zE')
            self._log(f"  Найдено {len(unread_rows)} писем")
            
            for row in unread_rows[:10]:
                if not self.running:
                    break
                
                try:
                    row.click()
                    time.sleep(2)
                    
                    try:
                        sender_elem = driver.find_element(By.CSS_SELECTOR, 'span[email]')
                        sender_email = sender_elem.get_attribute('email')
                    except:
                        sender_email = None
                    
                    if not sender_email:
                        driver.get("https://mail.google.com/mail/u/0/#inbox")
                        time.sleep(2)
                        continue
                    
                    seller_data = self.sellers_data.get(sender_email)
                    if not seller_data:
                        driver.get("https://mail.google.com/mail/u/0/#inbox")
                        time.sleep(2)
                        continue
                    
                    title = seller_data.get('title', '')
                    price = seller_data.get('price', '')
                    
                    html_body = self.config["templates"]["reply"]["body"]
                    html_body = html_body.replace("{link}", seller_data.get('ad_url', ''))
                    html_body = html_body.replace("{price}", price)
                    html_body = html_body.replace("{name}", sender_email.split('@')[0])
                    
                    self._reply_to_email(driver, html_body)
                    
                    self._log(f"  ✅ {sender_email}")
                    replied += 1
                    
                    time.sleep(2)
                    driver.get("https://mail.google.com/mail/u/0/#inbox")
                    time.sleep(2)
                    
                except Exception as e:
                    try:
                        driver.get("https://mail.google.com/mail/u/0/#inbox")
                        time.sleep(2)
                    except:
                        pass
        
        except Exception as e:
            self._log(f"  ❌ {e}")
        
        return replied
    
    def _reply_to_email(self, driver, html_body: str):
        """Отправляет ответ"""
        wait = WebDriverWait(driver, 40)
        
        reply_btn = driver.find_element(By.CSS_SELECTOR, 'g[aria-label="Reply"]')
        reply_btn.click()
        time.sleep(2)
        
        reply_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="textbox"]')))
        driver.execute_script("arguments[0].innerHTML = arguments[1]; arguments[0].dispatchEvent(new Event('input', {bubbles: true}));", reply_field, html_body)
        time.sleep(2)
        
        send_btn = driver.find_element(By.CSS_SELECTOR, 'button[aria-label="Send"]')
        send_btn.click()
        time.sleep(2)
    
    def _stop_check(self):
        """Остановка проверки"""
        self.running = False
        self.check_start_btn.configure(state="normal")
        self.check_stop_btn.configure(state="disabled")
        self.check_status.configure(text="⚪ Готов")
        self._log("⏹ Остановлено")

if __name__ == "__main__":
    app = App()
    app.mainloop()
