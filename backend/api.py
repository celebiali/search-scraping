from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from models import SessionLocal, TrackedProduct, PushSubscription, VapidKey, init_db
from fastapi.middleware.cors import CORSMiddleware
from pywebpush import webpush, WebPushException
import json
import os
import logging
from cryptography.hazmat.primitives.asymmetric import ec
from tracker import TakipSistemi

# Configure logging
logger = logging.getLogger(__name__)

# Fix for pywebpush compatibility with newer cryptography versions
try:
    # If SECP256R1 is a class, try to instantiate it (expected by some pywebpush versions)
    if isinstance(ec.SECP256R1, type):
        ec.SECP256R1 = ec.SECP256R1()
except Exception as e:
    logger.warning(f"Note: Cryptography monkey-patching skipped: {e}")

app = FastAPI(title="E-Ticaret Takip API")

# VAPID Key Management
def get_vapid_keys(db: Session):
    keys = db.query(VapidKey).first()
    if not keys:
        # Generate new keys
        from pywebpush import webpush
        # Note: In a real app, use a proper generator. pywebpush doesn't have one builtin for generating keys, 
        # usually done via command line: openssl ecparam -name prime256v1 -genkey -noout -out vapid_private.pem
        # For simplicity, I'll use placeholders or assume the user will provide them.
        # But wait, I can use a simple trick or just hardcode for demo if needed.
        # Actually, let's use a standard pair for now or a dummy one.
        pass
    return keys

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/vapid-public-key")
def get_public_key():
    return {"public_key": "BF-Ff8oDzJzlzVmMhLarvYhDl-oxKeXsJbZL-MhGAZJqsiVkBkDYj81RBAQ9OLMt1YS851EoznKE5OiT1B2VjIQ"}

@app.post("/test-notification")
async def test_notification(db: Session = Depends(get_db)):
    subs = db.query(PushSubscription).all()
    if not subs:
        return {"status": "error", "message": "No subscriptions found"}
    
    from pywebpush import webpush, WebPushException
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.primitives import serialization
    import base64

    # VAPID Private key (Base64URL)
    private_key_b64 = "kZJ0SsD1SeqO-bf2iWmDxppuHwG3RVLmyYkXZkj6XPU"
    
    count = 0
    for sub in subs:
        try:
            webpush(
                subscription_info={
                    "endpoint": sub.endpoint,
                    "keys": {"p256dh": sub.p256dh, "auth": sub.auth}
                },
                data=json.dumps({
                    "title": "🚀 Test Bildirimi",
                    "body": "PriceTrack bildirim sisteminiz başarıyla çalışıyor!",
                    "url": "https://pricetrack-notifier.vercel.app"
                }),
                vapid_private_key=private_key_b64,
                vapid_claims={"sub": "mailto:admin@pricetrack.com"}
            )
            count += 1
        except WebPushException as ex:
            print(f"Push failed: {ex}")
        except Exception as e:
            print(f"General error: {e}")
            
    return {"status": "success", "sent_to": count}

@app.post("/subscribe")
def subscribe(subscription: dict, db: Session = Depends(get_db)):
    # subscription usually has endpoint, keys {p256dh, auth}
    db_sub = PushSubscription(
        endpoint=subscription['endpoint'],
        p256dh=subscription['keys']['p256dh'],
        auth=subscription['keys']['auth']
    )
    db.add(db_sub)
    try:
        db.commit()
    except:
        db.rollback()
    return {"status": "success"}

# CORS ayarları (Nuxt için)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()


# Pydantic Modelleri
class ProductCreate(BaseModel):
    query: str
    category: str

class ProductResponse(BaseModel):
    id: int
    query: str
    category: str
    last_price: float
    avg_price: float
    best_price_ever: float
    last_name: Optional[str]
    last_link: Optional[str]
    last_source: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True

@app.get("/products", response_model=List[ProductResponse])
def get_products(db: Session = Depends(get_db)):
    return db.query(TrackedProduct).all()

async def run_initial_sync(product_id: int):
    db = SessionLocal()
    try:
        product = db.query(TrackedProduct).filter(TrackedProduct.id == product_id).first()
        if product:
            sistem = TakipSistemi()
            await sistem.track_product(db, product)
    finally:
        db.close()

@app.post("/products", response_model=ProductResponse)
async def add_product(product: ProductCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    logger.info(f"Adding new product: {product.query} in category {product.category}")
    if not product.query or not product.query.strip():
        raise HTTPException(status_code=400, detail="Ürün sorgusu boş olamaz")
        
    try:
        # Duplicate check
        existing = db.query(TrackedProduct).filter(
            TrackedProduct.query == product.query,
            TrackedProduct.category == product.category
        ).first()
        if existing:
            return existing
            
        db_product = TrackedProduct(query=product.query, category=product.category)
        db.add(db_product)
        db.commit()
        db.refresh(db_product)
        
        # Trigger instant scan
        background_tasks.add_task(run_initial_sync, db_product.id)
        
        # Anında bildirim gönder (Test amaçlı ve kullanıcı deneyimi için)
        sistem = TakipSistemi()
        background_tasks.add_task(
            sistem.send_push_notification,
            "✨ Yeni Ürün Takibi Başlatıldı",
            f"'{product.query}' başarıyla sisteme eklendi. En uygun fiyatlar taranıyor! 🔍",
            "https://pricetrack-notifier.vercel.app"
        )
        
        return db_product
    except Exception as e:
        db.rollback()
        logger.error(f"Error adding product: {e}")
        raise HTTPException(status_code=500, detail=f"Veritabanı hatası: {str(e)}")

@app.post("/products/{product_id}/sync")
async def sync_product(product_id: int, db: Session = Depends(get_db)):
    from tracker import TakipSistemi
    product = db.query(TrackedProduct).filter(TrackedProduct.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Ürün bulunamadı")
    
    # Run immediate scan
    sistem = TakipSistemi()
    await sistem.track_product(db, product)
    return {"status": "success", "last_price": product.last_price}

@app.delete("/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    try:
        product = db.query(TrackedProduct).filter(TrackedProduct.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Ürün bulunamadı")
        db.delete(product)
        db.commit()
        return {"message": "Ürün silindi"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting product: {e}")
        raise HTTPException(status_code=500, detail=f"Silme işlemi başarısız: {str(e)}")

@app.post("/products/{product_id}/toggle")
def toggle_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(TrackedProduct).filter(TrackedProduct.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Ürün bulunamadı")
    product.is_active = not product.is_active
    db.commit()
    return {"is_active": product.is_active}
