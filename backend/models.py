from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
from datetime import datetime

Base = declarative_base()

class TrackedProduct(Base):
    __tablename__ = 'tracked_products'
    
    id = Column(Integer, primary_key=True)
    query = Column(String, nullable=False)
    category = Column(String, nullable=False)
    last_price = Column(Float, default=0.0)
    best_price_ever = Column(Float, default=0.0)
    last_link = Column(String)
    last_source = Column(String)
    last_name = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_checked = Column(DateTime)
    
    history = relationship("PriceHistory", back_populates="product", cascade="all, delete-orphan")

class PriceHistory(Base):
    __tablename__ = 'price_history'
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('tracked_products.id'))
    price = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    product = relationship("TrackedProduct", back_populates="history")

class PushSubscription(Base):
    __tablename__ = 'push_subscriptions'
    
    id = Column(Integer, primary_key=True)
    endpoint = Column(String, unique=True, nullable=False)
    p256dh = Column(String, nullable=False)
    auth = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class VapidKey(Base):
    __tablename__ = 'vapid_keys'
    id = Column(Integer, primary_key=True)
    public_key = Column(String, nullable=False)
    private_key = Column(String, nullable=False)

# Database Setup
engine = create_engine('sqlite:///tracking_system.db')
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
