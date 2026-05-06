import asyncio
import random
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from models import SessionLocal, TrackedProduct, PriceHistory, PushSubscription, init_db
from scraper import ETicaretScraper
from pywebpush import webpush, WebPushException
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TakipSistemi:
    def __init__(self):
        self.scraper = ETicaretScraper()
        # VAPID keys - In production, these should be from env or db
        self.vapid_private_key = "kZJ0SsD1SeqO-bf2iWmDxppuHwG3RVLmyYkXZkj6XPU" 
        self.vapid_claims = {"sub": "mailto:admin@pricetrack.com"}
        init_db()

    async def send_push_notification(self, title, message, url=None):
        db = SessionLocal()
        subs = db.query(PushSubscription).all()
        for sub in subs:
            try:
                webpush(
                    subscription_info={
                        "endpoint": sub.endpoint,
                        "keys": {"p256dh": sub.p256dh, "auth": sub.auth}
                    },
                    data=json.dumps({
                        "title": title,
                        "body": message,
                        "url": url
                    }),
                    vapid_private_key=self.vapid_private_key,
                    vapid_claims=self.vapid_claims
                )
            except WebPushException as ex:
                logger.error(f"Push failed: {repr(ex)}")
            except Exception as ex:
                logger.error(f"Unexpected push error: {repr(ex)}")
        db.close()

    async def notify(self, product, new_price):
        title = "🔔 İndirim Yakalandı!"
        msg = f"{product.last_name} ürününde indirim! {product.last_price} TL -> {new_price} TL"
        logger.info(msg)
        await self.send_push_notification(title, msg, product.last_link)

    async def track_product(self, db: Session, product: TrackedProduct):
        logger.info(f"🔍 Takip ediliyor: {product.query} ({product.category})")
        
        best_match = await self.scraper.get_best_match(product.query, product.category)
        
        if best_match:
            new_price = best_match['price']
            
            # Fiyat düşüşü kontrolü (En düşüğün dibini kovalama)
            if product.best_price_ever > 0 and new_price < (product.best_price_ever * 0.95):
                await self.notify(product, new_price)
            
            # Veritabanı güncelleme
            product.last_price = new_price
            product.avg_price = best_match.get('avg_price', 0)
            product.last_link = best_match['link']
            product.last_name = best_match['name']
            product.last_source = best_match['source']
            product.last_checked = datetime.utcnow()
            
            if product.best_price_ever == 0 or new_price < product.best_price_ever:
                product.best_price_ever = new_price
            
            # Geçmişe ekle
            history = PriceHistory(product_id=product.id, price=new_price)
            db.add(history)
            db.commit()
            logger.info(f"✅ Güncellendi: {product.last_name} - {new_price} TL")
        else:
            logger.warning(f"⚠️ Ürün bulunamadı: {product.query}")

    async def start_tracking_loop(self):
        logger.info("🚀 Takip döngüsü başlatılıyor...")
        while True:
            db = SessionLocal()
            try:
                # Tüm aktif ürünleri al
                products = db.query(TrackedProduct).filter(TrackedProduct.is_active == True).all()
                
                if not products:
                    logger.info("ℹ️ Takip listesi boş. 5 dakika bekleniyor...")
                    await asyncio.sleep(300)
                    continue

                any_tracked = False
                for product in products:
                    now = datetime.utcnow()
                    # Şartlar: Hiç taranmamış (last_checked is None) VEYA 1 saatten fazla süre geçmiş
                    is_new = product.last_checked is None
                    is_stale = not is_new and (now - product.last_checked).total_seconds() > 3600
                    
                    if is_new or is_stale:
                        any_tracked = True
                        await self.track_product(db, product)
                        
                        # IP Engeli önlemi
                        delay = random.uniform(3, 7)
                        await asyncio.sleep(delay)
                
                if not any_tracked:
                    # Yapacak iş yoksa kısa süre bekle ve tekrar kontrol et (yeni ürün gelebilir)
                    await asyncio.sleep(60)
                else:
                    # Bir tur bittiyse biraz dinlen
                    await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"❌ Döngü hatası: {e}")
                await asyncio.sleep(60)
            finally:
                db.close()

if __name__ == "__main__":
    sistem = TakipSistemi()
    asyncio.run(sistem.start_tracking_loop())
