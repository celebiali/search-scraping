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
        
        # Mobil (iPhone) kılığına giriyoruz, Amazon mobile daha az blok koyar
        headers = {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "tr-TR,tr;q=0.9",
            "Referer": "https://www.google.com/",
            "Connection": "keep-alive",
        }
        
        async with requests.AsyncSession(impersonate="chrome120") as s:
            try:
                # Önce ana sayfaya dokunup bir cookie alalım
                await s.get("https://www.amazon.com.tr", headers=headers, timeout=10)
                await asyncio.sleep(0.5)
                
                resp = await s.get(search_url, headers=headers, timeout=20)
                if resp.status_code != 200:
                    print(f"Amazon Blocked: {resp.status_code}")
                    return []

                soup = BeautifulSoup(resp.text, 'html.parser')
                # Mobil ve Desktop selector'larını harmanla
                items = soup.select('div[data-component-type="s-search-result"]') or \
                        soup.select('.s-result-item[data-asin]') or \
                        soup.select('.s-item-container')
                
                products = []
                for item in items:
                    name_tag = item.select_one('h2 span') or item.select_one('.a-size-base-plus')
                    price_whole = item.select_one('.a-price-whole')
                    link_tag = item.select_one('h2 a') or item.select_one('a.a-link-normal')
                    
                    if name_tag and price_whole and link_tag:
                        price_str = price_whole.text.replace('.', '').replace(',', '').replace('\xa0', '').strip()
                        if price_str:
                            products.append({
                                'name': name_tag.text.strip(),
                                'price': float(price_str),
                                'link': 'https://www.amazon.com.tr' + link_tag['href'] if not link_tag['href'].startswith('http') else link_tag['href'],
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
        
        headers = {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "tr-TR,tr;q=0.9",
            "Referer": "https://www.google.com/",
        }
        
        async with requests.AsyncSession(impersonate="chrome120") as s:
            try:
                resp = await s.get(search_url, headers=headers, timeout=20)
                soup = BeautifulSoup(resp.text, 'html.parser')
                
                # Hepsiburada mobil/masaüstü karışık selector
                items = soup.select('li[class*="productListContent"]') or \
                        soup.select('div[data-test-id="product-card"]') or \
                        soup.select('.m-product-item')
                
                products = []
                for item in items:
                    name_tag = item.select_one('h3') or \
                               item.select_one('[data-test-id="product-card-name"]') or \
                               item.select_one('.product-title')
                    
                    price_tag = item.select_one('[data-test-id="price-current-price"]') or \
                                item.select_one('div[class*="price-value"]') or \
                                item.select_one('.product-price')
                                
                    link_tag = item.select_one('a')
                    
                    if name_tag and price_tag and link_tag:
                        price_text = price_tag.text.split('TL')[0].replace('.', '').replace(',', '.').replace('\xa0', '').strip()
                        try:
                            price_val = float(price_text)
                            products.append({
                                'name': name_tag.text.strip(),
                                'price': price_val,
                                'link': 'https://www.hepsiburada.com' + link_tag['href'] if not link_tag['href'].startswith('http') else link_tag['href'],
                                'source': 'Hepsiburada'
                            })
                        except: continue
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

        # C) Kesin Model Doğrulaması (Strict Version Matching)
        # Eğer sorguda "pro", "max", "plus" gibi anahtar kelimeler yoksa, başlığında bu kelimeler geçen ürünleri eleriz.
        strict_keywords = ["pro", "max", "plus", "ultra", "mini", "lite"]
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        filtered_stage_c = []
        for p in filtered_stage_b:
            product_name_lower = p['name'].lower()
            product_words = set(product_name_lower.split())
            
            # Sorguda olmayan ama üründe olan kritik kelimeleri kontrol et
            # Örn: Sorgu "iphone 15", Ürün "iphone 15 pro". "pro" sorguda yok -> ELE.
            is_valid_version = True
            for kw in strict_keywords:
                if kw in product_name_lower and kw not in query_lower:
                    is_valid_version = False
                    break
            
            if is_valid_version:
                filtered_stage_c.append(p)

        if not filtered_stage_c:
            # Eğer her şey elendiyse, en azından orijinal listeye sadık kal (fail-safe)
            filtered_stage_c = filtered_stage_b

        # D) Arama Doğruluğu (Metin Benzerliği)
        # Benzerlik skoru ekle ve sırala
        for p in filtered_stage_c:
            p['similarity'] = self._calculate_similarity(query, p['name'])
        
        # En az %20 benzerlik ve en düşük fiyat kombinasyonu
        reliable_products = [p for p in filtered_stage_c if p['similarity'] > 0.2]
        
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
