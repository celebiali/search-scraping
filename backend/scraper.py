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
            "elektronik": ["kılıf", "ekran koruyucu", "kablo", "şarj", "lens", "stand", "kutu", "adaptör", "askı", "sticker", "aparat", "başlık"],
            "giyim": ["askı", "sprey", "boya", "fırça", "düğme", "temizleme", "bakım", "yedek", "kutu", "bağcık"],
            "kozmetik": ["fırça", "sünger", "aparat", "kutu", "çanta", "boş", "yedek"],
            "ev-yasam": ["yedek", "parça", "vida", "eklenti", "aparat", "aksesuar", "kılıf"]
        }
        # Evrensel gürültü kelimeleri (Kategori bağımsız)
        self.universal_blacklist = ["yedek", "parça", "tamir", "kiti", "seti", "aksesuar", "uyumlu", "için", "aparat", "kılıfı"]

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
                    # Amazon mobil sayfalarda başlık genelde birden fazla span (marka + isim) şeklinde bölünür
                    # Bu span'ları birleştirerek tam ismi oluşturuyoruz
                    name_nodes = item.select('h2 span') or \
                                 item.select('.a-size-base-plus') or \
                                 item.select('.s-line-clamp-3')
                    
                    if name_nodes:
                        name_text = " ".join([n.get_text(strip=True) for n in name_nodes if n.get_text(strip=True)])
                    else:
                        continue
                    
                    if not name_text:
                        continue
                    
                    price_whole = item.select_one('.a-price-whole')
                    link_tag = item.select_one('h2 a') or item.select_one('a.a-link-normal')
                    
                    if name_text and price_whole and link_tag:
                        # Amazon TR fiyat formatı: 7.199,00
                        price_val = self._parse_price(price_whole.text)
                        if price_val:
                            products.append({
                                'name': name_text,
                                'price': price_val,
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

        # 1. Kelime Bazlı Ön Filtre (Sorgudaki kelimelerin çoğu üründe geçmeli)
        query_words = set(query.lower().replace('ı', 'i').split())
        if not query_words:
            return None

        valid_by_name = []
        for p in products:
            name_lower = p['name'].lower().replace('ı', 'i')
            # Sorgudaki kelimelerin en az %80'i ürün isminde geçmeli
            match_count = sum(1 for word in query_words if word in name_lower)
            if match_count >= len(query_words) * 0.8:
                p['match_score'] = match_count / len(query_words)
                valid_by_name.append(p)
        
        if not valid_by_name:
            return None

        # 2. Dinamik Fiyat Kümeleme (Price Density Filtering)
        # Fiyatları sırala ve en yoğun oldukları "gerçek ürün" kümesini bul
        valid_by_name.sort(key=lambda x: x['price'])
        prices = [p['price'] for p in valid_by_name]
        
        if len(prices) > 2:
            # Medyanı baz alarak, medyandan çok uzak (2 katı veya 0.4 katı) olanları ele
            median_price = statistics.median(prices)
            filtered_by_price = [p for p in valid_by_name if (median_price * 0.5) <= p['price'] <= (median_price * 1.8)]
        else:
            filtered_by_price = valid_by_name

        if not filtered_by_price:
            return None

        # 3. Nihai Puanlama (Benzerlik + Fiyat Uyumu)
        for p in filtered_by_price:
            similarity = self._calculate_similarity(query, p['name'])
            # Puan = Benzerlik skoru
            p['final_score'] = similarity

        # Ortalama fiyatı bu küme üzerinden tekrar hesapla (daha doğru sonuç için)
        cluster_avg = statistics.mean([p['price'] for p in filtered_by_price])

        # En yüksek benzerlik skoruna sahip olanlar arasından en ucuzunu seç
        best_match = min(filtered_by_price, key=lambda x: (-x['final_score'], x['price']))
        best_match['cluster_avg'] = cluster_avg
        return best_match

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
        
        # Evrensel ve kategori bazlı filtreleme
        valid_products = []
        for p in all_products:
            name_lower = p['name'].lower()
            if any(word.lower() in name_lower for word in blacklist): continue
            if any(f" {word.lower()} " in f" {name_lower} " for word in self.universal_blacklist): continue
            valid_products.append(p)
        
        if not valid_products:
            return None

        # İlk aşama fiyat temizliği (Aksesuar ayıklama)
        prices = sorted([p['price'] for p in valid_products])
        median_price = statistics.median(prices)
        
        # Medyanın %20'sinden ucuz olanları genelde aksesuar sayabiliriz (Universal kural)
        clean_products = [p for p in valid_products if p['price'] > (median_price * 0.2)]
        
        if not clean_products:
            clean_products = valid_products

        best_product = self.filter_products(clean_products, query, category)
        if best_product:
            # cluster_avg (temizlenmiş kümenin ortalaması) yoksa genel ortalamayı kullan
            best_product['avg_price'] = best_product.get('cluster_avg', median_price)
            
        return best_product

# Test Kullanımı
if __name__ == "__main__":
    async def test():
        scraper = ETicaretScraper()
        result = await scraper.get_best_match("iPhone 15 128 GB", "elektronik")
        print(f"Bulunan En İyi Ürün: {result}")
    
    asyncio.run(test())
