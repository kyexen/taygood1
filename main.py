"""Ryt Bank - Complete Banking App Backend"""
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from typing import List, Optional
import base64
import os
from datetime import datetime, timedelta
import json
from openai import OpenAI
from dotenv import load_dotenv
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from database import init_db, get_db, User, Receipt, Transaction, Friend, BillSplit, BillSplitParticipant

# Load .env file
env_loaded = load_dotenv()
print(f"Loading .env file: {'Success' if env_loaded else 'Not found or empty'}")
print(f"Current working directory: {os.getcwd()}")
print(f".env file exists: {os.path.exists('.env')}")

# Initialize
app = FastAPI(title="Ryt Bank API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 * 24 * 60  # 30 days

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

# OpenAI
print("\n" + "="*60)
print("CHECKING OPENAI API KEY CONFIGURATION")
print("="*60)

api_key = os.getenv("OPENAI_API_KEY")
print(f"API Key found: {bool(api_key)}")
if api_key:
    print(f"API Key length: {len(api_key)}")
    print(f"API Key starts with: {api_key[:15]}...")
    print(f"API Key ends with: ...{api_key[-10:]}")

if api_key and api_key.strip():
    try:
        client = OpenAI(api_key=api_key.strip())
        print("✓ OpenAI client initialized SUCCESSFULLY")
        print("✓ Receipt OCR is READY to use")
    except Exception as e:
        print(f"❌ ERROR initializing OpenAI client: {e}")
        print(f"❌ Full error type: {type(e).__name__}")
        client = None
else:
    client = None
    print("❌ OPENAI_API_KEY not found in .env file")
    print("❌ Make sure .env file exists in project root")

print("="*60 + "\n")

# Run database migration first
print("\n" + "="*60)
print("DATABASE MIGRATION CHECK")
print("="*60)
try:
    import sqlite3
    conn = sqlite3.connect('ryt_bank.db')
    cursor = conn.cursor()
    
    # Check existing columns
    cursor.execute("PRAGMA table_info(receipts)")
    columns = [col[1] for col in cursor.fetchall()]
    print(f"Current receipt columns: {', '.join(columns)}")
    
    # Add taxes_json column if missing
    if 'taxes_json' not in columns:
        print("\n→ Adding taxes_json column...")
        cursor.execute("ALTER TABLE receipts ADD COLUMN taxes_json TEXT")
        conn.commit()
        print("✓ Added taxes_json column")
    else:
        print("✓ taxes_json column exists")
    
    # Add township column if missing
    if 'township' not in columns:
        print("→ Adding township column...")
        cursor.execute("ALTER TABLE receipts ADD COLUMN township TEXT")
        conn.commit()
        print("✓ Added township column")
    else:
        print("✓ township column exists")
    
    conn.close()
    print("✓ Database migration complete")
except Exception as e:
    print(f"❌ Migration error: {e}")

print("="*60 + "\n")

# Initialize database (this won't override existing tables)
init_db()

# Pydantic Models
class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    full_name: Optional[str] = None
    phone: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: Optional[str]
    balance: float
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class ReceiptItem(BaseModel):
    name: str
    quantity: Optional[float] = None
    price: float
    total: Optional[float] = None

class ReceiptCreate(BaseModel):
    merchant_name: Optional[str] = None
    date: Optional[str] = None
    time: Optional[str] = None
    items: List[ReceiptItem]
    subtotal: Optional[float] = None
    tax: Optional[float] = None
    total: float
    payment_method: Optional[str] = None
    location_address: Optional[str] = None
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None

class FriendAdd(BaseModel):
    friend_username: str

class BillSplitItem(BaseModel):
    name: str
    price: float
    shared_by: List[int]  # List of user IDs sharing this item

class BillSplitCreate(BaseModel):
    restaurant_name: str
    location_address: str
    location_lat: float
    location_lng: float
    items: List[BillSplitItem]
    participants: List[int]  # List of friend user IDs

# Helper functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

def geocode_address(address: str) -> tuple:
    """Geocode an address to get latitude and longitude using Nominatim (OpenStreetMap)"""
    if not address:
        return None, None
    
    try:
        import urllib.parse
        import urllib.request
        import json
        
        # Use Nominatim geocoding service (free, no API key needed)
        query = urllib.parse.quote(address)
        url = f"https://nominatim.openstreetmap.org/search?q={query}&format=json&limit=1"
        
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'RytBankApp/1.0')
        
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            if data and len(data) > 0:
                lat = float(data[0]['lat'])
                lng = float(data[0]['lon'])
                return lat, lng
    except Exception as e:
        print(f"Geocoding error: {e}")
    
    return None, None

def extract_receipt_data_with_ai(image_base64: str) -> dict:
    """Use OpenAI Vision API to extract structured data from receipt image"""
    if not client:
        raise HTTPException(
            status_code=500, 
            detail="OpenAI API key not configured. Check terminal for setup instructions."
        )
    
    print(f"📸 Processing receipt with OpenAI Vision API...")
    
    prompt = """Analyze this receipt image and extract all information in a structured format. 
    Extract: merchant name, date, time, items (name, quantity, price, total), subtotal, taxes, service charges, total, payment method, and address/location.
    
    IMPORTANT TAX EXTRACTION:
    - In Malaysia, receipts often have SST (Sales & Service Tax), Service Charge, or other taxes
    - Extract EACH tax/charge separately with its name and amount
    - Common taxes: SST (6-10%), Service Charge (10%), Government Tax, etc.
    - Look for percentages or flat amounts
    
    IMPORTANT LOCATION:
    - Look for the merchant's address or location on the receipt (header, footer, anywhere)
    - Include township/area names (Petaling Jaya, Bangsar, KL Sentral, Puchong, etc.)
    
    Return JSON with this structure:
    {
        "merchant_name": "string or null",
        "date": "YYYY-MM-DD or null",
        "time": "HH:MM or null",
        "items": [{"name": "string", "quantity": number or null, "price": number, "total": number or null}],
        "subtotal": number or null,
        "taxes": [{"name": "string (e.g., SST, Service Charge)", "amount": number, "percentage": number or null}],
        "total": number,
        "payment_method": "string or null",
        "address": "full address string including street, city, state, country if available, or null",
        "township": "area/township name (e.g., Petaling Jaya, Bangsar, KL Sentral) or null",
        "raw_text": "full text from receipt"
    }"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                ]
            }],
            max_tokens=2000
        )
        
        print(f"✓ OpenAI API responded successfully")
        
        content = response.choices[0].message.content
        import re
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            extracted = json.loads(json_match.group(0))
        else:
            extracted = json.loads(content)
        
        print(f"📊 Extracted data from AI:")
        print(f"  - Merchant: {extracted.get('merchant_name')}")
        print(f"  - Township: {extracted.get('township')}")
        print(f"  - Address: {extracted.get('address')}")
        print(f"  - Taxes: {extracted.get('taxes')}")
        
        # Geocode address if available
        address = extracted.get("address")
        township = extracted.get("township")
        lat, lng = None, None
        
        # Try geocoding from address
        if address:
            lat, lng = geocode_address(address)
            print(f"  - Geocoded from address to: {lat}, {lng}")
        
        # Fallback: Use township to get approximate coordinates
        if (not lat or not lng) and township:
            township_coords = {
                'Bandar Sunway': (3.0680, 101.6046),
                'Petaling Jaya': (3.1073, 101.6067),
                'Kelana Jaya': (3.1125, 101.5918),
                'Bangsar': (3.1301, 101.6724),
                'KL Sentral': (3.1337, 101.6863),
                'Puchong': (3.0265, 101.6073),
                'Subang Jaya': (3.0443, 101.5854),
                'Damansara': (3.1635, 101.6186),
                'Cheras': (3.0998, 101.7314),
                'Ampang': (3.1545, 101.7609)
            }
            
            # Try exact match or fuzzy match
            for town_name, coords in township_coords.items():
                if township.lower() in town_name.lower() or town_name.lower() in township.lower():
                    lat, lng = coords
                    print(f"  - Using township coordinates for '{township}' -> {town_name}: {lat}, {lng}")
                    break
        
        # Last fallback: Extract from merchant name if it contains township
        if (not lat or not lng) and extracted.get("merchant_name"):
            merchant = extracted.get("merchant_name", "").lower()
            township_coords = {
                'sunway': (3.0680, 101.6046),
                'petaling jaya': (3.1073, 101.6067),
                'bangsar': (3.1301, 101.6724),
                'puchong': (3.0265, 101.6073),
                'subang': (3.0443, 101.5854)
            }
            for keyword, coords in township_coords.items():
                if keyword in merchant:
                    lat, lng = coords
                    if not township:
                        township = keyword.title()
                    print(f"  - Extracted location from merchant name '{keyword}': {lat}, {lng}")
                    break
        
        extracted["location_address"] = address
        extracted["location_lat"] = lat
        extracted["location_lng"] = lng
        extracted["township"] = township
        
        print(f"  - FINAL: Township={township}, Lat={lat}, Lng={lng}")
        
        return extracted
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ OpenAI API Error: {error_msg}")
        
        if "401" in error_msg or "Incorrect API key" in error_msg:
            raise HTTPException(
                status_code=500,
                detail="OpenAI API key is invalid or expired. Please check your key at https://platform.openai.com/api-keys"
            )
        elif "quota" in error_msg.lower():
            raise HTTPException(
                status_code=500,
                detail="OpenAI API quota exceeded. Please add credits to your account."
            )
        else:
            raise HTTPException(status_code=500, detail=f"OpenAI API error: {error_msg}")

# Auth endpoints
@app.post("/api/auth/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    try:
        # Validation
        if not user_data.username or len(user_data.username) < 3:
            raise HTTPException(status_code=400, detail="Username must be at least 3 characters")
        if not user_data.email or "@" not in user_data.email:
            raise HTTPException(status_code=400, detail="Invalid email address")
        if not user_data.password or len(user_data.password) < 6:
            raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
        
        # Check if user exists
        existing_email = db.query(User).filter(User.email == user_data.email).first()
        if existing_email:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        existing_username = db.query(User).filter(User.username == user_data.username).first()
        if existing_username:
            raise HTTPException(status_code=400, detail="Username already taken")
        
        # Create user
        hashed_password = get_password_hash(user_data.password)
        db_user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password,
            full_name=user_data.full_name,
            phone=user_data.phone,
            balance=1000.0  # Starting balance
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        return UserResponse(
            id=db_user.id,
            email=db_user.email,
            username=db_user.username,
            full_name=db_user.full_name,
            balance=db_user.balance
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@app.post("/api/auth/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login and get access token"""
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            balance=user.balance
        )
    }

@app.get("/api/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user info"""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        full_name=current_user.full_name,
        balance=current_user.balance
    )

# Receipt OCR endpoints
@app.post("/api/receipts/upload")
async def upload_receipt(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload and process receipt image"""
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        image_data = await file.read()
        
        # Check file size (limit to 10MB)
        if len(image_data) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Image file too large. Maximum size is 10MB.")
        
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        # Check if OpenAI client is available
        if not client:
            raise HTTPException(
                status_code=500, 
                detail="OpenAI API key not configured. Please set OPENAI_API_KEY in .env file to use receipt OCR."
            )
        
        extracted_data = extract_receipt_data_with_ai(image_base64)
        
        # Validate extracted data
        if not extracted_data:
            raise HTTPException(status_code=500, detail="Failed to extract data from receipt")
        
        # Ensure total exists
        if "total" not in extracted_data or not extracted_data.get("total"):
            raise HTTPException(status_code=500, detail="Could not extract total amount from receipt")
        
        # Process taxes
        taxes = extracted_data.get("taxes", [])
        total_tax = sum(tax.get("amount", 0) for tax in taxes) if taxes else 0
        if not total_tax and extracted_data.get("tax"):
            total_tax = extracted_data.get("tax")
        
        # Create receipt with new fields
        db_receipt = Receipt(
            user_id=current_user.id,
            merchant_name=extracted_data.get("merchant_name"),
            date=extracted_data.get("date"),
            time=extracted_data.get("time"),
            total=float(extracted_data.get("total", 0.0)),
            subtotal=float(extracted_data.get("subtotal", 0.0)) if extracted_data.get("subtotal") else None,
            tax=float(total_tax) if total_tax else None,
            taxes_json=taxes if taxes else None,
            payment_method=extracted_data.get("payment_method"),
            raw_text=extracted_data.get("raw_text"),
            items_json=[item for item in extracted_data.get("items", [])],
            location_address=extracted_data.get("location_address"),
            location_lat=extracted_data.get("location_lat"),
            location_lng=extracted_data.get("location_lng"),
            township=extracted_data.get("township")
        )
        db.add(db_receipt)
        db.commit()
        db.refresh(db_receipt)
        
        return {"success": True, "receipt": {
            "id": db_receipt.id,
            "merchant_name": db_receipt.merchant_name,
            "date": db_receipt.date,
            "time": db_receipt.time,
            "total": db_receipt.total,
            "subtotal": db_receipt.subtotal,
            "tax": db_receipt.tax,
            "taxes": db_receipt.taxes_json or [],
            "items": db_receipt.items_json or [],
            "location_address": db_receipt.location_address,
            "location_lat": db_receipt.location_lat,
            "location_lng": db_receipt.location_lng,
            "township": db_receipt.township
        }}
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Receipt processing error: {error_details}")
        raise HTTPException(status_code=500, detail=f"Error processing receipt: {str(e)}")

@app.get("/api/receipts")
async def get_receipts(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get user's receipts"""
    receipts = db.query(Receipt).filter(Receipt.user_id == current_user.id).order_by(Receipt.timestamp.desc()).all()
    
    receipt_list = []
    for r in receipts:
        receipt_data = {
            "id": r.id,
            "merchant_name": r.merchant_name,
            "date": r.date,
            "time": r.time,
            "total": r.total,
            "subtotal": r.subtotal,
            "tax": r.tax,
            "taxes": r.taxes_json or [],
            "items": r.items_json or [],
            "location_address": r.location_address,
            "location_lat": r.location_lat,
            "location_lng": r.location_lng,
            "township": getattr(r, 'township', None),  # Safe get in case column doesn't exist
            "timestamp": r.timestamp.isoformat() if r.timestamp else None
        }
        receipt_list.append(receipt_data)
        print(f"📋 Receipt {r.id}: {r.merchant_name} - Township: {receipt_data['township']}, Lat: {receipt_data['location_lat']}, Lng: {receipt_data['location_lng']}")
    
    return {
        "success": True,
        "receipts": receipt_list
    }

@app.get("/api/receipts/{receipt_id}")
async def get_receipt(receipt_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get a specific receipt by ID"""
    receipt = db.query(Receipt).filter(
        Receipt.id == receipt_id,
        Receipt.user_id == current_user.id
    ).first()
    
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    
    return {
        "success": True,
        "receipt": {
            "id": receipt.id,
            "merchant_name": receipt.merchant_name,
            "date": receipt.date,
            "time": receipt.time,
            "total": receipt.total,
            "subtotal": receipt.subtotal,
            "tax": receipt.tax,
            "taxes": receipt.taxes_json or [],
            "items": receipt.items_json or [],
            "location_address": receipt.location_address,
            "location_lat": receipt.location_lat,
            "location_lng": receipt.location_lng,
            "township": receipt.township,
            "timestamp": receipt.timestamp.isoformat() if receipt.timestamp else None
        }
    }

@app.delete("/api/receipts/{receipt_id}")
async def delete_receipt(receipt_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Delete a receipt"""
    receipt = db.query(Receipt).filter(
        Receipt.id == receipt_id,
        Receipt.user_id == current_user.id
    ).first()
    
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    
    # Simply delete the receipt (bill splits are separate entities)
    db.delete(receipt)
    db.commit()
    
    return {
        "success": True,
        "message": "Receipt deleted successfully"
    }

# Friends endpoints
@app.post("/api/friends")
async def add_friend(
    friend_data: FriendAdd,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a friend"""
    friend_user = db.query(User).filter(User.username == friend_data.friend_username).first()
    if not friend_user:
        raise HTTPException(status_code=404, detail="User not found")
    if friend_user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot add yourself as friend")
    
    # Check if already friends
    existing = db.query(Friend).filter(
        Friend.user_id == current_user.id,
        Friend.friend_id == friend_user.id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already friends")
    
    db_friend = Friend(
        user_id=current_user.id,
        friend_id=friend_user.id,
        friend_username=friend_user.username,
        friend_email=friend_user.email
    )
    db.add(db_friend)
    db.commit()
    
    return {"success": True, "friend": {
        "id": friend_user.id,
        "username": friend_user.username,
        "email": friend_user.email
    }}

@app.get("/api/friends")
async def get_friends(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get user's friends"""
    friends = db.query(Friend).filter(Friend.user_id == current_user.id).all()
    return {
        "success": True,
        "friends": [{
            "id": f.friend_id,
            "username": f.friend_username,
            "email": f.friend_email
        } for f in friends]
    }

# Bill Split endpoints
@app.post("/api/bill-split")
async def create_bill_split(
    bill_data: BillSplitCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new bill split"""
    # Calculate amounts for each participant
    participant_amounts = {pid: 0.0 for pid in bill_data.participants}
    participant_amounts[current_user.id] = 0.0
    
    # Calculate splits
    for item in bill_data.items:
        if item.shared_by:
            item_per_person = item.price / len(item.shared_by)
            for user_id in item.shared_by:
                if user_id in participant_amounts:
                    participant_amounts[user_id] += item_per_person
    
    # Create bill split
    db_bill = BillSplit(
        creator_id=current_user.id,
        restaurant_name=bill_data.restaurant_name,
        location_address=bill_data.location_address,
        location_lat=bill_data.location_lat,
        location_lng=bill_data.location_lng,
        total_amount=sum(item.price for item in bill_data.items),
        items_json=[item.dict() for item in bill_data.items],
        status="pending"
    )
    db.add(db_bill)
    db.flush()
    
    # Create participants
    all_participants = set(bill_data.participants) | {current_user.id}
    for user_id in all_participants:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            db_participant = BillSplitParticipant(
                bill_split_id=db_bill.id,
                user_id=user_id,
                username=user.username,
                amount_owed=participant_amounts.get(user_id, 0.0),
                items_json=[item.dict() for item in bill_data.items if user_id in item.shared_by],
                paid=False
            )
            db.add(db_participant)
    
    db.commit()
    db.refresh(db_bill)
    
    return {"success": True, "bill_split": {
        "id": db_bill.id,
        "restaurant_name": db_bill.restaurant_name,
        "total_amount": db_bill.total_amount,
        "participants": [{
            "user_id": p.user_id,
            "username": p.username,
            "amount_owed": p.amount_owed,
            "paid": p.paid
        } for p in db_bill.participants]
    }}

@app.get("/api/bill-split")
async def get_bill_splits(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get user's bill splits"""
    bills = db.query(BillSplit).filter(
        (BillSplit.creator_id == current_user.id) |
        (BillSplit.participants.any(BillSplitParticipant.user_id == current_user.id))
    ).all()
    
    return {
        "success": True,
        "bill_splits": [{
            "id": b.id,
            "restaurant_name": b.restaurant_name,
            "location_address": b.location_address,
            "location_lat": b.location_lat,
            "location_lng": b.location_lng,
            "total_amount": b.total_amount,
            "status": b.status,
            "created_at": b.created_at.isoformat() if b.created_at else None,
            "participants": [{
                "user_id": p.user_id,
                "username": p.username,
                "amount_owed": p.amount_owed,
                "paid": p.paid
            } for p in b.participants]
        } for b in bills]
    }

@app.post("/api/bill-split/{bill_split_id}/request-payment")
async def request_payment(
    bill_split_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Request payment from participants in a bill split"""
    bill_split = db.query(BillSplit).filter(BillSplit.id == bill_split_id).first()
    
    if not bill_split:
        raise HTTPException(status_code=404, detail="Bill split not found")
    
    if bill_split.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the bill creator can request payments")
    
    # Get participants who haven't paid
    unpaid_participants = db.query(BillSplitParticipant).filter(
        BillSplitParticipant.bill_split_id == bill_split_id,
        BillSplitParticipant.paid == False,
        BillSplitParticipant.user_id != current_user.id
    ).all()
    
    # Create payment request transactions (in a real app, these would be notifications)
    requests_created = []
    for participant in unpaid_participants:
        # Create a transaction record for the payment request
        transaction = Transaction(
            user_id=participant.user_id,
            type="bill_split_request",
            amount=participant.amount_owed,
            description=f"Payment request from {current_user.username} for {bill_split.restaurant_name}",
            category="bill_split"
        )
        db.add(transaction)
        requests_created.append({
            "user_id": participant.user_id,
            "username": participant.username,
            "amount": participant.amount_owed
        })
    
    db.commit()
    
    return {
        "success": True,
        "message": f"Payment requests sent to {len(requests_created)} participants",
        "requests": requests_created
    }

# Transactions
@app.get("/api/transactions")
async def get_transactions(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get user's transactions"""
    transactions = db.query(Transaction).filter(
        Transaction.user_id == current_user.id
    ).order_by(Transaction.timestamp.desc()).limit(50).all()
    
    return {
        "success": True,
        "transactions": [{
            "id": t.id,
            "type": t.type,
            "amount": t.amount,
            "description": t.description,
            "category": t.category,
            "timestamp": t.timestamp.isoformat() if t.timestamp else None
        } for t in transactions]
    }

@app.get("/api/payment-requests")
async def get_payment_requests(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get payment requests sent by the user"""
    # Get all bill splits created by user
    bill_splits = db.query(BillSplit).filter(BillSplit.creator_id == current_user.id).all()
    
    payment_requests = []
    for bill in bill_splits:
        participants = db.query(BillSplitParticipant).filter(
            BillSplitParticipant.bill_split_id == bill.id,
            BillSplitParticipant.user_id != current_user.id
        ).all()
        
        if participants:
            total_requested = sum(p.amount_owed for p in participants)
            paid_count = sum(1 for p in participants if p.paid)
            
            payment_requests.append({
                "id": bill.id,
                "restaurant_name": bill.restaurant_name,
                "location_address": bill.location_address,
                "total_amount": bill.total_amount,
                "total_requested": total_requested,
                "participants": [{
                    "user_id": p.user_id,
                    "username": p.username,
                    "amount_owed": p.amount_owed,
                    "paid": p.paid
                } for p in participants],
                "status": "completed" if all(p.paid for p in participants) else "pending",
                "paid_count": paid_count,
                "total_count": len(participants),
                "created_at": bill.created_at.isoformat() if bill.created_at else None
            })
    
    return {
        "success": True,
        "payment_requests": sorted(payment_requests, key=lambda x: x.get("created_at", ""), reverse=True)
    }

@app.get("/")
async def root():
    return {"message": "Ryt Bank API", "status": "running", "version": "1.0.0"}

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    try:
        db = next(get_db())
        # Test database connection
        db.execute("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
