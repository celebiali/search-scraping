import asyncio
import random
import re
import statistics
from difflib import SequenceMatcher
from bs4 import BeautifulSoup
from curl_cffi import requests

class ETicaretScraper:
    def __init__(self):
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        
        # A) Kategori Bazlı Dinamik Kara Liste (Stop-Words)
        self.category_blacklists = {
            "elektronik": ["kılıf", "ekran koruyucu", "kablo", "şarj", "lens", "stand", "kutu", "adaptör", "askı", "sticker"],
            "giyim": ["askı", "sprey", "boya", "fırça", "düğme", "temizleme", "bakım", "yedek"],
            "kozmetik": ["fırça", "sünger", "aparat", "kutu", "çanta", "boş"],
            "ev-yasam": ["yedek", "parça", "vida", "eklenti"]
        }

    def _get_headers(self, site="amazon"):
        headers = {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        if site == "amazon":
            headers["Referer"] = "https://www.amazon.com.tr/"
        elif site == "hepsiburada":
            headers["Referer"] = "https://www.hepsiburada.com/"
        return headers

    def _parse_price(self, price_str):
        if not price_str: return None
        try:
            # Temizleme ve Sayısallaştırma
            clean_str = re.sub(r'[^\d,\.]', '', price_str)
            if ',' in clean_str and '.' in clean_str:
                clean_str = clean_str.replace('.', '').replace(',', '.')
            elif ',' in clean_str:
                clean_str = clean_str.replace(',', '.')
            return float(clean_str)
        except:
            return None

    def _calculate_similarity(self, a, b):
        # C) Arama Doğruluğu (Metin Benzerliği)
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()

    async def fetch_amazon(self, query):
        url = f"https://www.amazon.com.tr/s?k={query.replace(' ', '+')}"
        async with requests.AsyncSession(impersonate="chrome120") as s:
            try:
                response = await s.get(url, headers=self._get_headers("amazon"), timeout=30)
                if response.status_code != 200:
                    return []
                
                soup = BeautifulSoup(response.text, 'html.parser')
                products = []
                items = soup.select('div[data-component-type="s-search-result"]')
                
                for item in items:
                    name_tag = item.select_one('h2 span')
                    price_tag = item.select_one('span.a-price span.a-offscreen')
                    link_tag = item.select_one('h2 a')
                    
                    if name_tag and price_tag and link_tag:
                        name = name_tag.get_text(strip=True)
                        price = self._parse_price(price_tag.get_text(strip=True))
                        link = "https://www.amazon.com.tr" + link_tag.get('href', '')
                        if price:
                            products.append({"name": name, "price": price, "link": link, "source": "Amazon"})
                return products
            except Exception as e:
                print(f"Amazon error: {e}")
                return []

    async def fetch_hepsiburada(self, query):
        url = f"https://www.hepsiburada.com/ara?q={query.replace(' ', '+')}"
        async with requests.AsyncSession(impersonate="chrome120") as s:
            try:
                response = await s.get(url, headers=self._get_headers("hepsiburada"), timeout=30)
                if response.status_code != 200:
                    return []
                
                soup = BeautifulSoup(response.text, 'html.parser')
                products = []
                # Hepsiburada search results selector
                items = soup.select('li[class*="productListContent"]')
                
                for item in items:
                    name_tag = item.select_one('h3')
                    price_tag = item.select_one('div[data-test-id="price-current-price"]')
                    link_tag = item.select_one('a')
                    
                    if name_tag and price_tag and link_tag:
                        name = name_tag.get_text(strip=True)
                        price = self._parse_price(price_tag.get_text(strip=True))
                        link = "https://www.hepsiburada.com" + link_tag.get('href', '')
                        if price:
                            products.append({"name": name, "price": price, "link": link, "source": "Hepsiburada"})
                return products
            except Exception as e:
                print(f"Hepsiburada error: {e}")
                return []

    def filter_products(self, products, query, category):
        if not products:
            return None

        # A) Kategori Bazlı Kara Liste Filtresi
        blacklist = self.category_blacklists.get(category.lower(), [])
        filtered_stage_a = []
        for p in products:
            if not any(word.lower() in p['name'].lower() for word in blacklist):
                filtered_stage_a.append(p)
        
        if not filtered_stage_a:
            return None

        # B) İstatistiksel Fiyat Anomalisi (Outlier) Filtresi
        prices = [p['price'] for p in filtered_stage_a]
        if len(prices) > 3:
            median_price = statistics.median(prices)
            # Eğer ürün medyanın %40'ından daha ucuzsa (aksesuar olma ihtimali yüksek)
            filtered_stage_b = [p for p in filtered_stage_a if p['price'] >= (median_price * 0.4)]
        else:
            filtered_stage_b = filtered_stage_a

        if not filtered_stage_b:
            return None

        # C) Arama Doğruluğu (Metin Benzerliği)
        # Benzerlik skoru ekle ve sırala
        for p in filtered_stage_b:
            p['similarity'] = self._calculate_similarity(query, p['name'])
        
        # En az %20 benzerlik ve en düşük fiyat kombinasyonu
        # Önce benzerliğe göre eliyoruz (çok alakasızları atıyoruz)
        reliable_products = [p for p in filtered_stage_b if p['similarity'] > 0.2]
        
        if not reliable_products:
            return None

        # En ucuz ve en doğru ürünü bul (Ağırlıklı bir puanlama da yapılabilir ama istenen "EN UCUZ ve DOĞRU ilk ürün")
        # Benzerliği %50'den yüksek olanlar arasından en ucuzu seçmek mantıklı bir yaklaşım
        high_accuracy = [p for p in reliable_products if p['similarity'] > 0.4]
        target_list = high_accuracy if high_accuracy else reliable_products
        
        best_product = min(target_list, key=lambda x: x['price'])
        return best_product

    async def get_best_match(self, query, category):
        # Paralel istekler
        amazon_task = self.fetch_amazon(query)
        hepsi_task = self.fetch_hepsiburada(query)
        
        results = await asyncio.gather(amazon_task, hepsi_task)
        all_products = results[0] + results[1]
        
        return self.filter_products(all_products, query, category)

# Test Kullanımı
if __name__ == "__main__":
    async def test():
        scraper = ETicaretScraper()
        result = await scraper.get_best_match("iPhone 15 128 GB", "elektronik")
        print(f"Bulunan En İyi Ürün: {result}")
    
    asyncio.run(test())
