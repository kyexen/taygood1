"""Database models and setup for Ryt Bank App"""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

# Database setup
DATABASE_URL = "sqlite:///./ryt_bank.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Models
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    phone = Column(String)
    balance = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    receipts = relationship("Receipt", back_populates="owner")
    transactions = relationship("Transaction", back_populates="user")
    bill_splits = relationship("BillSplit", back_populates="creator")
    friends = relationship("Friend", foreign_keys="Friend.user_id", back_populates="user")

class Receipt(Base):
    __tablename__ = "receipts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    merchant_name = Column(String)
    date = Column(String)
    time = Column(String)
    total = Column(Float, nullable=False)
    subtotal = Column(Float)
    tax = Column(Float)  # Legacy field, kept for compatibility
    taxes_json = Column(JSON)  # Store multiple taxes: [{"name": "SST", "amount": 5.0, "percentage": 6}]
    payment_method = Column(String)
    raw_text = Column(Text)
    items_json = Column(JSON)  # Store items as JSON
    location_address = Column(String)
    location_lat = Column(Float)
    location_lng = Column(Float)
    township = Column(String)  # Township/area name (Petaling Jaya, Bangsar, etc.)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    owner = relationship("User", back_populates="receipts")

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    type = Column(String)  # 'deposit', 'withdrawal', 'transfer', 'bill_split'
    amount = Column(Float, nullable=False)
    description = Column(String)
    category = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="transactions")

class Friend(Base):
    __tablename__ = "friends"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    friend_id = Column(Integer, ForeignKey("users.id"))
    friend_username = Column(String)
    friend_email = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="friends")

class BillSplit(Base):
    __tablename__ = "bill_splits"
    
    id = Column(Integer, primary_key=True, index=True)
    creator_id = Column(Integer, ForeignKey("users.id"))
    restaurant_name = Column(String)
    location_address = Column(String)
    location_lat = Column(Float)
    location_lng = Column(Float)
    total_amount = Column(Float, nullable=False)
    items_json = Column(JSON)  # Store items and their splits
    status = Column(String, default="pending")  # pending, settled
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    creator = relationship("User", back_populates="bill_splits")
    participants = relationship("BillSplitParticipant", back_populates="bill_split")

class BillSplitParticipant(Base):
    __tablename__ = "bill_split_participants"
    
    id = Column(Integer, primary_key=True, index=True)
    bill_split_id = Column(Integer, ForeignKey("bill_splits.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    username = Column(String)
    amount_owed = Column(Float, default=0.0)
    items_json = Column(JSON)  # Items this participant is responsible for
    paid = Column(Boolean, default=False)
    
    # Relationships
    bill_split = relationship("BillSplit", back_populates="participants")

# Create all tables
def init_db():
    Base.metadata.create_all(bind=engine)

# Get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
