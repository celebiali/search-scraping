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
        a = a.lower().replace('ı', 'i')
        b = b.lower().replace('ı', 'i')
        return SequenceMatcher(None, a, b).ratio()

    async def fetch_amazon(self, query):
        import urllib.parse
        encoded_query = urllib.parse.quote(query)
        search_url = f"https://www.amazon.com.tr/s?k={encoded_query}"
        home_url = "https://www.amazon.com.tr"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": home_url
        }
        
        async with requests.AsyncSession(impersonate="chrome120") as s:
            try:
                # 1. Oturumu Isıt (Ana sayfaya git)
                await s.get(home_url, headers=headers, timeout=10)
                await asyncio.sleep(1)
                
                # 2. Arama Yap
                resp = await s.get(search_url, headers=headers, timeout=15)
                print(f"DEBUG Amazon: Status {resp.status_code}")
                
                if "api-services-support@amazon.com" in resp.text:
                    print("WARNING: Amazon CAPTCHA detected")
                    return []

                soup = BeautifulSoup(resp.text, 'html.parser')
                items = soup.select('div[data-component-type="s-search-result"]')
                if not items:
                    items = soup.select('.s-result-item[data-asin]')
                
                products = []
                for item in items:
                    name_tag = item.select_one('h2 span')
                    price_whole = item.select_one('.a-price-whole')
                    link_tag = item.select_one('h2 a')
                    
                    if name_tag and price_whole and link_tag:
                        price_str = price_whole.text.replace('.', '').replace(',', '').strip()
                        products.append({
                            'name': name_tag.text.strip(),
                            'price': float(price_str),
                            'link': 'https://www.amazon.com.tr' + link_tag['href'],
                            'source': 'Amazon'
                        })
                return products
            except Exception as e:
                print(f"Amazon error: {e}")
                return []

    async def fetch_hepsiburada(self, query):
        import urllib.parse
        encoded_query = urllib.parse.quote(query)
        search_url = f"https://www.hepsiburada.com/ara?q={encoded_query}"
        home_url = "https://www.hepsiburada.com"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "tr-TR,tr;q=0.9",
        }
        
        async with requests.AsyncSession(impersonate="chrome120") as s:
            try:
                # 1. Oturumu Isıt
                await s.get(home_url, headers=headers, timeout=10)
                await asyncio.sleep(1)
                
                # 2. Arama Yap
                resp = await s.get(search_url, headers=headers, timeout=15)
                print(f"DEBUG Hepsiburada: Status {resp.status_code}")
                
                soup = BeautifulSoup(resp.text, 'html.parser')
                items = soup.select('li[class*="productListContent"]')
                if not items:
                    items = soup.select('div[data-test-id="product-card"]')
                
                products = []
                for item in items:
                    name_tag = item.select_one('h3') or item.select_one('[data-test-id="product-card-name"]')
                    price_tag = item.select_one('[data-test-id="price-current-price"]') or item.select_one('div[class*="price-value"]')
                    link_tag = item.select_one('a')
                    
                    if name_tag and price_tag and link_tag:
                        price_text = price_tag.text.split('TL')[0].replace('.', '').replace(',', '.').strip()
                        products.append({
                            'name': name_tag.text.strip(),
                            'price': float(price_text),
                            'link': 'https://www.hepsiburada.com' + link_tag['href'] if not link_tag['href'].startswith('http') else link_tag['href'],
                            'source': 'Hepsiburada'
                        })
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
        if len(prices) > 1:
            max_price = max(prices)
            # Eğer ürün, bulunan en yüksek fiyatın %40'ından daha ucuzsa aksesuar sayılır.
            filtered_stage_b = [p for p in filtered_stage_a if p['price'] >= (max_price * 0.4)]
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
        query = query.lower().replace('ı', 'i').replace('\u0307', '') # Türkçe karakter ve birleştirici nokta temizliği
        # Paralel istekler
        amazon_task = self.fetch_amazon(query)
        hepsi_task = self.fetch_hepsiburada(query)
        
        results = await asyncio.gather(amazon_task, hepsi_task)
        all_products = results[0] + results[1]
        print(f"DEBUG: Found {len(all_products)} total products for query '{query}'")
        
        # Filtreleme
        blacklist = self.category_blacklists.get(category.lower(), [])
        valid_products = [p for p in all_products if not any(word.lower() in p['name'].lower() for word in blacklist)]
        
        if not valid_products:
            return None

        # Ortalama fiyatı hesapla
        avg_price = statistics.mean([p['price'] for p in valid_products])
        
        # AKSESUAR FİLTRESİ: Ortalama fiyatın %30'undan ucuz olanları "yan ürün/aksesuar" say ve ele.
        # Örn: iPhone 15 için 50.000 TL ortalama varsa, 15.000 TL altı her şey elenir (kılıf, kablo vs).
        clean_products = [p for p in valid_products if p['price'] > (avg_price * 0.3)]
        
        if not clean_products:
            # Eğer her şey elendiyse (yanlış kategori vs), valid_products'a geri dön ama riskli
            clean_products = valid_products

        best_product = self.filter_products(clean_products, query, category)
        if best_product:
            best_product['avg_price'] = avg_price
            
        return best_product

# Test Kullanımı
if __name__ == "__main__":
    async def test():
        scraper = ETicaretScraper()
        result = await scraper.get_best_match("iPhone 15 128 GB", "elektronik")
        print(f"Bulunan En İyi Ürün: {result}")
    
    asyncio.run(test())
