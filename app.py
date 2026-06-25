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
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from datetime import datetime
import random
import re

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Gmail Sender v2.2")
        self.geometry("1200x700")
        
        self.running = False
        self.paused = False
        self.drivers_pool = {}  # {profile_id: driver} - остаются между этапами
        self.sellers_data = {}  # {email: {title, price, url, ...}}
        
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
                    "first": {"subject": "", "body": "", "is_html": False},
                    "reply": {"subject": "", "body": "", "is_html": True}
                },
                "automation": {
                    "parser_key": "",
                    "platform": "vinted_it",
                    "country": "IT",
                    "user_id": "",
                    "api_key": "",
                    "delay": 5,
                    "max_letters": 10,
                    "service_code": "vinted_it"
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
        # Главный контейнер
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Табы
        self.tabview = ctk.CTkTabview(main_frame)
        self.tabview.pack(fill="both", expand=True)
        
        # Вкладки
        self.tab_token = self.tabview.add("🔑 Токен")
        self.tab_profiles = self.tabview.add("👤 Профили")
        self.tab_templates = self.tabview.add("✉️ Шаблоны")
        self.tab_send = self.tabview.add("🚀 Отправка писем")
        self.tab_check = self.tabview.add("💬 Проверка ответов")
        self.tab_log = self.tabview.add("📋 Лог")
        self.tab_settings = self.tabview.add("⚙️ Настройки")
        
        self._create_token_tab()
        self._create_profiles_tab()
        self._create_templates_tab()
        self._create_send_tab()
        self._create_check_tab()
        self._create_log_tab()
        self._create_settings_tab()
    
    def _create_token_tab(self):
        """Вкладка токена Dolphin"""
        frame = ctk.CTkFrame(self.tab_token)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        label = ctk.CTkLabel(frame, text="Dolphin Anty API Token:", font=("Arial", 14))
        label.pack(pady=5)
        
        self.token_entry = ctk.CTkEntry(frame, width=400, show="*")
        self.token_entry.pack(pady=5)
        self.token_entry.insert(0, self.config.get("token", ""))
        
        def save_token():
            self.config["token"] = self.token_entry.get()
            self._save_config()
            messagebox.showinfo("Успех", "Токен сохранён")
        
        btn = ctk.CTkButton(frame, text="Сохранить токен", command=save_token)
        btn.pack(pady=10)
    
    def _create_profiles_tab(self):
        """Вкладка профилей"""
        frame = ctk.CTkFrame(self.tab_profiles)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        label = ctk.CTkLabel(frame, text="ID профилей Dolphin (один на строку):", font=("Arial", 14))
        label.pack(pady=5)
        
        self.profiles_text = ctk.CTkTextbox(frame, width=400, height=200)
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
        
        btn = ctk.CTkButton(frame, text="Загрузить из файла", command=load_profiles)
        btn.pack(pady=5)
    
    def _create_templates_tab(self):
        """Вкладка шаблонов писем"""
        frame = ctk.CTkFrame(self.tab_templates)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Первое письмо
        label1 = ctk.CTkLabel(frame, text="Первое письмо (обычный текст):", font=("Arial", 12, "bold"))
        label1.pack(pady=5)
        
        ctk.CTkLabel(frame, text="Тема:").pack()
        self.first_subject = ctk.CTkEntry(frame, width=400)
        self.first_subject.pack(pady=3)
        self.first_subject.insert(0, self.config["templates"]["first"].get("subject", ""))
        
        ctk.CTkLabel(frame, text="Текст письма (используй {price}):").pack()
        self.first_body = ctk.CTkTextbox(frame, width=400, height=100)
        self.first_body.pack(pady=3, fill="both", expand=True)
        self.first_body.insert("1.0", self.config["templates"]["first"].get("body", ""))
        
        # Ответ
        label2 = ctk.CTkLabel(frame, text="\nОтвет на письмо (HTML):", font=("Arial", 12, "bold"))
        label2.pack(pady=10)
        
        ctk.CTkLabel(frame, text="Тема:").pack()
        self.reply_subject = ctk.CTkEntry(frame, width=400)
        self.reply_subject.pack(pady=3)
        self.reply_subject.insert(0, self.config["templates"]["reply"].get("subject", ""))
        
        ctk.CTkLabel(frame, text="HTML (используй {link} и {price}):").pack()
        self.reply_body = ctk.CTkTextbox(frame, width=400, height=100)
        self.reply_body.pack(pady=3, fill="both", expand=True)
        self.reply_body.insert("1.0", self.config["templates"]["reply"].get("body", ""))
        
        def save_templates():
            self.config["templates"]["first"]["subject"] = self.first_subject.get()
            self.config["templates"]["first"]["body"] = self.first_body.get("1.0", tk.END)
            self.config["templates"]["reply"]["subject"] = self.reply_subject.get()
            self.config["templates"]["reply"]["body"] = self.reply_body.get("1.0", tk.END)
            self._save_config()
            messagebox.showinfo("Успех", "Шаблоны сохранены")
        
        btn = ctk.CTkButton(frame, text="Сохранить шаблоны", command=save_templates)
        btn.pack(pady=10)
    
    def _create_send_tab(self):
        """Вкладка отправки первых писем"""
        frame = ctk.CTkFrame(self.tab_send)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Парсер
        ctk.CTkLabel(frame, text="🛰 ПАРСЕР", font=("Arial", 14, "bold")).pack(pady=5)
        
        ctk.CTkLabel(frame, text="API ключ:").pack()
        self.send_parser_key = ctk.CTkEntry(frame, width=400, show="*")
        self.send_parser_key.pack(pady=3)
        self.send_parser_key.insert(0, self.config["automation"].get("parser_key", ""))
        
        ctk.CTkLabel(frame, text="Платформа:").pack()
        self.send_platform = ctk.CTkEntry(frame, width=400)
        self.send_platform.pack(pady=3)
        self.send_platform.insert(0, self.config["automation"].get("platform", "vinted_it"))
        
        ctk.CTkLabel(frame, text="Страна:").pack()
        self.send_country = ctk.CTkEntry(frame, width=400)
        self.send_country.pack(pady=3)
        self.send_country.insert(0, self.config["automation"].get("country", "IT"))
        
        # CreateAd
        ctk.CTkLabel(frame, text="\n🎫 CREATEAD API & МАРКЕТПЛЕЙС", font=("Arial", 14, "bold")).pack(pady=5)
        
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
        
        # Управление
        ctk.CTkLabel(frame, text="\n📧 УПРАВЛЕНИЕ ПИСЬМАМИ", font=("Arial", 14, "bold")).pack(pady=5)
        
        ctk.CTkLabel(frame, text="Задержка между письмами (сек):").pack()
        self.send_delay = ctk.CTkEntry(frame, width=400)
        self.send_delay.pack(pady=3)
        self.send_delay.insert(0, str(self.config["automation"].get("delay", 5)))
        
        ctk.CTkLabel(frame, text="Макс писем с 1 почты:").pack()
        self.send_max_letters = ctk.CTkEntry(frame, width=400)
        self.send_max_letters.pack(pady=3)
        self.send_max_letters.insert(0, str(self.config["automation"].get("max_letters", 10)))
        
        # Кнопки
        ctk.CTkLabel(frame, text="\n⚙️ УПРАВЛЕНИЕ", font=("Arial", 14, "bold")).pack(pady=5)
        
        btn_frame = ctk.CTkFrame(frame)
        btn_frame.pack(pady=10)
        
        self.send_start_btn = ctk.CTkButton(btn_frame, text="▶ СТАРТ", command=self._start_send, fg_color="green")
        self.send_start_btn.pack(side="left", padx=5)
        
        self.send_pause_btn = ctk.CTkButton(btn_frame, text="⏸ ПАУЗА", command=self._pause_send, state="disabled")
        self.send_pause_btn.pack(side="left", padx=5)
        
        self.send_stop_btn = ctk.CTkButton(btn_frame, text="⏹ СТОП", command=self._stop_send, state="disabled", fg_color="red")
        self.send_stop_btn.pack(side="left", padx=5)
        
        self.send_status = ctk.CTkLabel(frame, text="⚪ Готов к запуску", font=("Arial", 12))
        self.send_status.pack(pady=10)
    
    def _create_check_tab(self):
        """Вкладка проверки ответов"""
        frame = ctk.CTkFrame(self.tab_check)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Профили
        ctk.CTkLabel(frame, text="👤 ПРОФИЛИ", font=("Arial", 14, "bold")).pack(pady=5)
        
        ctk.CTkLabel(frame, text="Доступные профили:").pack()
        self.check_profiles_label = ctk.CTkLabel(frame, text="Нет открытых профилей", font=("Arial", 11))
        self.check_profiles_label.pack(pady=3)
        
        self.check_status_label = ctk.CTkLabel(frame, text="Статус: профили закрыты", font=("Arial", 11))
        self.check_status_label.pack(pady=3)
        
        # CreateAd
        ctk.CTkLabel(frame, text="\n🎫 CREATEAD API & МАРКЕТПЛЕЙС", font=("Arial", 14, "bold")).pack(pady=5)
        
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
        
        # Кнопки
        ctk.CTkLabel(frame, text="\n⚙️ УПРАВЛЕНИЕ", font=("Arial", 14, "bold")).pack(pady=5)
        
        btn_frame = ctk.CTkFrame(frame)
        btn_frame.pack(pady=10)
        
        self.check_start_btn = ctk.CTkButton(btn_frame, text="🔍 ПРОВЕРИТЬ ОТВЕТЫ", command=self._start_check, fg_color="blue")
        self.check_start_btn.pack(side="left", padx=5)
        
        self.check_stop_btn = ctk.CTkButton(btn_frame, text="⏹ ОСТАНОВИТЬ", command=self._stop_check, state="disabled", fg_color="red")
        self.check_stop_btn.pack(side="left", padx=5)
        
        self.check_status = ctk.CTkLabel(frame, text="⚪ Готов к запуску", font=("Arial", 12))
        self.check_status.pack(pady=10)
    
    def _create_log_tab(self):
        """Вкладка логирования"""
        frame = ctk.CTkFrame(self.tab_log)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.log_text = scrolledtext.ScrolledText(frame, height=30, width=120, bg="#212121", fg="#00FF00", font=("Courier", 10))
        self.log_text.pack(fill="both", expand=True)
    
    def _create_settings_tab(self):
        """Вкладка настроек"""
        frame = ctk.CTkFrame(self.tab_settings)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(frame, text="Gmail Sender v2.2", font=("Arial", 18, "bold")).pack(pady=10)
        ctk.CTkLabel(frame, text="Автоматизация рассылки писем", font=("Arial", 12)).pack(pady=5)
        
        info = """Функционал:
✅ Отправка первых писем через Gmail
✅ Проверка ответов и рассылка уникальных HTML
✅ Интеграция с Dolphin Anty
✅ Интеграция с CreateAd API
✅ Персонализация писем
✅ Профили остаются открыты между этапами

Версия: 2.2
Дата: 2026-06-25"""
        
        ctk.CTkLabel(frame, text=info, font=("Arial", 11), justify="left").pack(pady=10)
    
    def _log(self, message):
        """Логирование в вкладку логов"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.update()
    
    def _start_send(self):
        """Начало отправки первых писем"""
        self.running = True
        self.paused = False
        self.send_start_btn.configure(state="disabled")
        self.send_pause_btn.configure(state="normal")
        self.send_stop_btn.configure(state="normal")
        self.send_status.configure(text="🟡 Работаю...")
        
        # Сохраняем конфиг
        self.config["automation"]["parser_key"] = self.send_parser_key.get()
        self.config["automation"]["platform"] = self.send_platform.get()
        self.config["automation"]["country"] = self.send_country.get()
        self.config["automation"]["user_id"] = self.send_user_id.get()
        self.config["automation"]["api_key"] = self.send_api_key.get()
        self.config["automation"]["delay"] = int(self.send_delay.get() or 5)
        self.config["automation"]["max_letters"] = int(self.send_max_letters.get() or 10)
        self.config["automation"]["service_code"] = self.send_service_code.get()
        self._save_config()
        
        thread = threading.Thread(target=self._send_thread, daemon=True)
        thread.start()
    
    def _send_thread(self):
        """Поток отправки писем"""
        try:
            self._log("\n" + "="*50)
            self._log("🚀 НАЧАЛО ЭТАПА ОТПРАВКИ ПИСЕМ")
            self._log("="*50)
            
            # Получаем профили
            profiles_text = self.profiles_text.get("1.0", tk.END).strip()
            profiles = [p.strip() for p in profiles_text.split('\n') if p.strip() and not p.startswith('#')]
            
            if not profiles:
                self._log("❌ Нет профилей!")
                self._stop_send()
                return
            
            self._log(f"✅ Загружено {len(profiles)} профилей")
            
            # Парсинг
            self._log("\n📡 Парсинг email-ов...")
            emails_data = self._parse_emails()
            if not emails_data:
                self._log("❌ Ошибка парсинга")
                self._stop_send()
                return
            
            self._log(f"✅ Получено {len(emails_data)} email-ов")
            
            # Сохраняем данные для проверки ответов
            self.sellers_data = {item['email']: item for item in emails_data}
            
            # Открываем профили
            self._log("\n🌐 Открытие профилей Dolphin...")
            self.drivers_pool = self._open_profiles(profiles)
            if not self.drivers_pool:
                self._log("❌ Не удалось открыть профили")
                self._stop_send()
                return
            
            self._log(f"✅ Открыто {len(self.drivers_pool)} профилей")
            
            # Отправляем письма
            self._log("\n📧 Отправка первых писем...")
            self._send_first_emails(emails_data, profiles)
            
            self._log("\n" + "="*50)
            self._log("✅ ЭТАП ОТПРАВКИ ЗАВЕРШЁН")
            self._log("Профили остаются открытыми для проверки ответов")
            self._log("="*50)
            
        except Exception as e:
            self._log(f"❌ Критическая ошибка: {e}")
        finally:
            if self.running:
                self._stop_send()
    
    def _parse_emails(self) -> list:
        """Получает email-ы через парсер API"""
        try:
            url = "https://api.example.com/parse"  # Замени на реальный URL
            payload = {
                "api_key": self.config["automation"]["parser_key"],
                "platform": self.config["automation"]["platform"],
                "country": self.config["automation"]["country"]
            }
            
            response = requests.post(url, json=payload, timeout=30)
            if response.status_code == 200:
                data = response.json()
                # Ожидаем формат: [{"email": "...", "title": "...", "price": "...", "url": "..."}, ...]
                return data.get('sellers', [])
            else:
                self._log(f"❌ Ошибка парсера: {response.status_code}")
                return []
        except Exception as e:
            self._log(f"❌ Ошибка подключения к парсеру: {e}")
            return []
    
    def _open_profiles(self, profile_ids: list) -> dict:
        """Открывает профили Dolphin"""
        drivers = {}
        token = self.config.get("token", "")
        
        for profile_id in profile_ids:
            try:
                self._log(f"  Открываю профиль {profile_id}...")
                
                # API Dolphin для запуска профиля
                url = f"http://localhost:3001/v1/browser/start-browser"
                payload = {"browserId": profile_id}
                headers = {"Authorization": f"Bearer {token}"}
                
                response = requests.post(url, json=payload, headers=headers, timeout=30)
                if response.status_code == 200:
                    driver_info = response.json()
                    driver_port = driver_info.get('webSocketDebuggerUrl', '').split(':')[-1]
                    
                    options = webdriver.ChromeOptions()
                    options.add_experimental_option('debuggerAddress', f'localhost:{driver_port}')
                    driver = webdriver.Chrome(options=options)
                    
                    drivers[profile_id] = driver
                    self._log(f"    ✅ Профиль {profile_id} открыт")
                else:
                    self._log(f"    ❌ Ошибка открытия {profile_id}")
            except Exception as e:
                self._log(f"    ❌ Ошибка: {e}")
        
        return drivers
    
    def _send_first_emails(self, emails_data: list, profiles: list):
        """Отправляет первые письма"""
        delay = self.config["automation"].get("delay", 5)
        max_letters = self.config["automation"].get("max_letters", 10)
        
        for idx, item in enumerate(emails_data):
            if not self.running:
                self._log("⏹ Остановлено пользователем")
                break
            
            if self.paused:
                self._log("⏸ На паузе...")
                while self.paused and self.running:
                    time.sleep(1)
            
            email = item.get('email')
            price = item.get('price', 'N/A')
            
            if not email:
                continue
            
            # Выбираем профиль по ротации
            profile_id = profiles[idx % len(profiles)]
            driver = self.drivers_pool.get(profile_id)
            
            if not driver:
                self._log(f"❌ Профиль {profile_id} недоступен")
                continue
            
            try:
                # Отправляем письмо
                subject = self.config["templates"]["first"]["subject"]
                body = self.config["templates"]["first"]["body"]
                
                # Заменяем переменные
                body = self._apply_variables(body, {"price": price})
                
                self._send_email(driver, email, subject, body, is_html=False)
                self._log(f"✉️  Письмо отправлено: {email} (профиль {profile_id})")
                
                time.sleep(delay)
                
            except Exception as e:
                self._log(f"❌ Ошибка отправки {email}: {e}")
    
    def _send_email(self, driver, to_email: str, subject: str, body: str, is_html: bool = False):
        """Отправляет письмо через Gmail"""
        wait = WebDriverWait(driver, 40)
        
        try:
            # Открываем Gmail
            driver.get("https://mail.google.com/mail/u/0/#compose")
            time.sleep(3)
            
            # Поле "Кому"
            to_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[aria-label="To"]')))
            to_field.clear()
            to_field.send_keys(to_email)
            time.sleep(1)
            
            # Поле "Тема"
            subject_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[aria-label="Subject"]')))
            subject_field.clear()
            subject_field.send_keys(subject)
            time.sleep(1)
            
            # Тело письма
            body_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="textbox"]')))
            driver.execute_script("""
                var el = arguments[0];
                el.focus();
                el.innerHTML = arguments[1];
                el.dispatchEvent(new Event('input', {bubbles: true}));
            """, body_field, body)
            time.sleep(2)
            
            # Отправляем
            send_btn = driver.find_element(By.CSS_SELECTOR, 'button[aria-label="Send"]')
            send_btn.click()
            time.sleep(2)
            
        except Exception as e:
            raise Exception(f"Ошибка отправки письма: {e}")
    
    def _apply_variables(self, text: str, variables: dict) -> str:
        """Заменяет переменные в тексте"""
        result = text
        for key, value in variables.items():
            result = result.replace(f"{{{key}}}", str(value))
        return result
    
    def _pause_send(self):
        """Пауза отправки"""
        self.paused = not self.paused
        if self.paused:
            self.send_pause_btn.configure(text="▶ ПРОДОЛЖИТЬ")
            self.send_status.configure(text="⏸ На паузе")
        else:
            self.send_pause_btn.configure(text="⏸ ПАУЗА")
            self.send_status.configure(text="🟡 Работаю...")
    
    def _stop_send(self):
        """Остановка отправки"""
        self.running = False
        self.paused = False
        self.send_start_btn.configure(state="normal")
        self.send_pause_btn.configure(state="disabled", text="⏸ ПАУЗА")
        self.send_stop_btn.configure(state="disabled")
        self.send_status.configure(text="⚪ Готов к запуску")
        self._log("⏹ Отправка остановлена")
    
    def _start_check(self):
        """Начало проверки ответов"""
        if not self.drivers_pool:
            messagebox.showerror("Ошибка", "Нет открытых профилей! Сначала запустите отправку писем.")
            return
        
        self.running = True
        self.check_start_btn.configure(state="disabled")
        self.check_stop_btn.configure(state="normal")
        self.check_status.configure(text="🟡 Проверяю ответы...")
        
        # Обновляем информацию о профилях
        profiles_list = ", ".join(self.drivers_pool.keys())
        self.check_profiles_label.configure(text=f"Открытые профили: {profiles_list}")
        self.check_status_label.configure(text="Статус: профили открыты")
        
        # Сохраняем CreateAd параметры
        self.config["automation"]["user_id"] = self.check_user_id.get()
        self.config["automation"]["api_key"] = self.check_api_key.get()
        self.config["automation"]["service_code"] = self.check_service_code.get()
        self._save_config()
        
        thread = threading.Thread(target=self._check_thread, daemon=True)
        thread.start()
    
    def _check_thread(self):
        """Поток проверки ответов"""
        try:
            self._log("\n" + "="*50)
            self._log("💬 НАЧАЛО ПРОВЕРКИ ОТВЕТОВ")
            self._log("="*50)
            
            total_replied = 0
            
            for profile_id, driver in self.drivers_pool.items():
                if not self.running:
                    break
                
                self._log(f"\n🔍 Проверяю ответы в профиле {profile_id}...")
                
                try:
                    replied = self._check_and_reply_v2(driver, profile_id)
                    total_replied += replied
                    self._log(f"✅ Отправлено {replied} ответов из профиля {profile_id}")
                except Exception as e:
                    self._log(f"❌ Ошибка в профиле {profile_id}: {e}")
            
            self._log("\n" + "="*50)
            self._log(f"✅ ПРОВЕРКА ЗАВЕРШЕНА. Всего ответов: {total_replied}")
            self._log("="*50)
            
        except Exception as e:
            self._log(f"❌ Критическая ошибка: {e}")
        finally:
            if self.running:
                self._stop_check()
    
    def _check_and_reply_v2(self, driver, profile_id: str) -> int:
        """Проверяет ответы и отправляет персонализированный HTML"""
        replied = 0
        wait = WebDriverWait(driver, 40)
        user_id = self.config["automation"]["user_id"]
        api_key = self.config["automation"]["api_key"]
        service_code = self.config["automation"]["service_code"]
        
        try:
            driver.get("https://mail.google.com/mail/u/0/#inbox")
            time.sleep(3)
            
            # Ищем непрочитанные письма
            unread_rows = driver.find_elements(By.CSS_SELECTOR, 'tr.zE')
            self._log(f"  Найдено {len(unread_rows)} непрочитанных писем")
            
            for row in unread_rows[:10]:
                if not self.running:
                    break
                
                try:
                    row.click()
                    time.sleep(2)
                    
                    # Получаем email отправителя
                    try:
                        sender_elem = driver.find_element(By.CSS_SELECTOR, 'span[email]')
                        sender_email = sender_elem.get_attribute('email')
                    except:
                        sender_email = None
                    
                    if not sender_email:
                        self._log(f"  ⚠️  Не удалось получить email отправителя")
                        driver.get("https://mail.google.com/mail/u/0/#inbox")
                        time.sleep(2)
                        continue
                    
                    # Ищем в sellers_data
                    seller_data = self.sellers_data.get(sender_email)
                    if not seller_data:
                        self._log(f"  ⚠️  Email {sender_email} не найден в парсере")
                        driver.get("https://mail.google.com/mail/u/0/#inbox")
                        time.sleep(2)
                        continue
                    
                    # Получаем оригинальные данные
                    title = seller_data.get('title', '')
                    price = seller_data.get('price', 'N/A')
                    original_url = seller_data.get('url', '')
                    
                    self._log(f"  📧 Получен ответ от {sender_email}")
                    
                    # Создаём объявление в CreateAd
                    new_link = self._create_ad_via_api(title, price, original_url, user_id, api_key, service_code)
                    
                    if not new_link:
                        new_link = "[Ошибка создания ссылки]"
                    
                    # Генерируем персонализированный HTML
                    html_body = self._generate_personalized_html(new_link, price, sender_email)
                    
                    # Отправляем ответ
                    self._reply_to_email(driver, html_body)
                    
                    self._log(f"  ✅ HTML ответ отправлен: {sender_email}")
                    replied += 1
                    
                    time.sleep(2)
                    driver.get("https://mail.google.com/mail/u/0/#inbox")
                    time.sleep(2)
                    
                except Exception as e:
                    self._log(f"  ❌ Ошибка обработки письма: {e}")
                    try:
                        driver.get("https://mail.google.com/mail/u/0/#inbox")
                        time.sleep(2)
                    except:
                        pass
        
        except Exception as e:
            self._log(f"  ❌ Критическая ошибка в профиле: {e}")
        
        return replied
    
    def _create_ad_via_api(self, title: str, price: str, original_url: str, user_id: str, api_key: str, service_code: str) -> str:
        """Создаёт объявление в CreateAd и возвращает новую ссылку"""
        try:
            url = "https://api.createad.com/v1/ads/create"  # Замени на реальный URL
            payload = {
                "title": title,
                "price": price,
                "originalUrl": original_url,
                "userId": user_id,
                "apiKey": api_key,
                "serviceCode": service_code
            }
            
            response = requests.post(url, json=payload, timeout=30)
            if response.status_code == 200:
                data = response.json()
                return data.get('url', '')
            else:
                self._log(f"  ⚠️  CreateAd ошибка: {response.status_code}")
                return ""
        except Exception as e:
            self._log(f"  ⚠️  Ошибка CreateAd: {e}")
            return ""
    
    def _generate_personalized_html(self, link: str, price: str, email: str) -> str:
        """Генерирует уникальный HTML для каждого ответа"""
        template = self.config["templates"]["reply"]["body"]
        
        # Заменяем переменные
        html = template.replace("{link}", link)
        html = html.replace("{price}", str(price))
        
        # Можно добавить персонализацию по email
        name = email.split('@')[0]
        html = html.replace("{name}", name)
        
        return html
    
    def _reply_to_email(self, driver, html_body: str):
        """Отправляет ответ на письмо"""
        wait = WebDriverWait(driver, 40)
        
        try:
            # Кнопка "Ответить"
            reply_btn = driver.find_element(By.CSS_SELECTOR, 'g[aria-label="Reply"]')
            reply_btn.click()
            time.sleep(2)
            
            # Поле для ввода
            reply_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="textbox"]')))
            driver.execute_script("""
                var el = arguments[0];
                el.focus();
                el.innerHTML = arguments[1];
                el.dispatchEvent(new Event('input', {bubbles: true}));
            """, reply_field, html_body)
            time.sleep(2)
            
            # Отправляем
            send_btn = driver.find_element(By.CSS_SELECTOR, 'button[aria-label="Send"]')
            send_btn.click()
            time.sleep(2)
            
        except Exception as e:
            raise Exception(f"Ошибка отправки ответа: {e}")
    
    def _stop_check(self):
        """Остановка проверки ответов"""
        self.running = False
        self.check_start_btn.configure(state="normal")
        self.check_stop_btn.configure(state="disabled")
        self.check_status.configure(text="⚪ Готов к запуску")
        self._log("⏹ Проверка остановлена")

if __name__ == "__main__":
    app = App()
    app.mainloop()
