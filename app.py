    def _parse_emails(self) -> list:
        """Получает email-ы через парсер API"""
        try:
            url = f"http://vvsproject.xyz/ads/{self.config['automation']['platform']}"
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
