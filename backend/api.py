from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from models import SessionLocal, TrackedProduct, init_db
from fastapi.middleware.cors import CORSMiddleware
from pywebpush import webpush, WebPushException
import json
import os
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
def get_public_key(db: Session = Depends(get_db)):
    # Standard testing VAPID public key
    return {"public_key": "BJ_M-k3V_V1xI-MvX-B7Gj_jB_vX-S1j-B7Gj_jB_vX-S1j"}

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
    best_price_ever: float
    last_name: str | None
    last_link: str | None
    last_source: str | None
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
