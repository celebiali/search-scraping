from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from models import SessionLocal, TrackedProduct, init_db
from fastapi.middleware.cors import CORSMiddleware
from pywebpush import webpush, WebPushException
import json
import os
from cryptography.hazmat.primitives.asymmetric import ec
# Fix for pywebpush compatibility with newer cryptography versions
try:
    ec.SECP256R1()
except TypeError:
    # If it fails, it means it's already an instance or needs different handling
    pass
except:
    # Some versions need the class to be instantiated
    if isinstance(ec.SECP256R1, type):
        original_SECP256R1 = ec.SECP256R1
        ec.SECP256R1 = original_SECP256R1()
from models import SessionLocal, TrackedProduct, PushSubscription, VapidKey, init_db

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
    return {"public_key": "BM_FojHn3xxetKd-an1SfJZpjxxjxVjEGE9ktdX0CR-vbcKaMMkn2EsUmMOurZMP5Cn75Ko92B_2rifE5auJRnA"}

@app.post("/test-notification")
async def test_notification(db: Session = Depends(get_db)):
    subs = db.query(PushSubscription).all()
    if not subs:
        return {"status": "error", "message": "No subscriptions found"}
    
    from pywebpush import webpush, WebPushException
    # Use the same private key as tracker.py
    private_key = "xjOetOey40y-4YL5qduMhjaPEuXVgthAP3L1PMBwMAk"
    
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
                vapid_private_key=private_key,
                vapid_claims={"sub": "mailto:admin@pricetrack.com"}
            )
            count += 1
        except WebPushException as ex:
            print(f"Push failed: {ex}")
            
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

@app.post("/products", response_model=ProductResponse)
def add_product(product: ProductCreate, db: Session = Depends(get_db)):
    db_product = TrackedProduct(query=product.query, category=product.category)
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@app.delete("/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(TrackedProduct).filter(TrackedProduct.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Ürün bulunamadı")
    db.delete(product)
    db.commit()
    return {"message": "Ürün silindi"}

@app.post("/products/{product_id}/toggle")
def toggle_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(TrackedProduct).filter(TrackedProduct.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Ürün bulunamadı")
    product.is_active = not product.is_active
    db.commit()
    return {"is_active": product.is_active}
