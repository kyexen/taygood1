# Ryt Bank - Smart Banking App

A modern, AI-powered banking application built for the Ryt Bank hackathon track. Features include receipt OCR, bill splitting, friend management, and transaction tracking.

## 🚀 Features

### Core Features
- **User Authentication**: Secure login and registration system
- **Receipt OCR**: AI-powered receipt scanning and data extraction using OpenAI GPT-4 Vision
- **Bill Splitting**: Split restaurant bills among friends with item-level sharing
- **Friend Management**: Add and manage friends for bill splitting
- **Transaction History**: Track all your financial transactions
- **Google Maps Integration**: Location services for restaurants and receipts
- **Modern UI**: Beautiful, mobile-first design inspired by Ryt Bank

### Additional Features
- Real-time balance tracking
- Transaction categorization
- Receipt storage and management
- Location-based restaurant tracking
- Responsive design for all devices

## 📋 Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- OpenAI API key (for receipt OCR)
- Google Maps API key (optional, for location features)

## 🛠️ Installation

1. **Clone or download the repository**
   ```bash
   cd ryt-bank-app
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   Create a `.env` file in the root directory:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   SECRET_KEY=your_secret_key_for_jwt_tokens
   ```

4. **Initialize the database**
   The database will be created automatically on first run.

## 🚀 Running the Application

### Windows
Simply double-click `START.bat` or run:
```bash
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

### Mac/Linux
```bash
python3 -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

### Access the App
1. Start the server (see above)
2. Open `app.html` in your web browser
3. The app will be available at `http://localhost:8000`

## 📱 Using the App

### First Time Setup
1. Click "Sign Up" to create an account
2. Fill in your details (username, email, password, full name)
3. You'll receive a starting balance of $1000

### Key Features

#### Receipt OCR
1. Go to the Receipts tab
2. Click the camera icon
3. Upload a receipt image
4. The AI will extract all information automatically

#### Bill Splitting
1. Go to the Split Bill tab
2. Enter restaurant name and location
3. Add food items with prices
4. Select friends to split with
5. Items can be shared among multiple people
6. The app calculates each person's share automatically

#### Adding Friends
1. Go to the Friends tab
2. Click the "+" button
3. Enter your friend's username
4. They'll be added to your friends list

## 🗄️ Database Schema

The app uses SQLite with the following main tables:
- `users`: User accounts and balances
- `receipts`: Scanned receipts
- `transactions`: Financial transactions
- `friends`: Friend relationships
- `bill_splits`: Bill splitting records
- `bill_split_participants`: Individual shares in bill splits

## 🔧 API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `GET /api/auth/me` - Get current user info

### Receipts
- `POST /api/receipts/upload` - Upload and process receipt
- `GET /api/receipts` - Get user's receipts

### Friends
- `POST /api/friends` - Add a friend
- `GET /api/friends` - Get user's friends

### Bill Splitting
- `POST /api/bill-split` - Create bill split
- `GET /api/bill-split` - Get user's bill splits

### Transactions
- `GET /api/transactions` - Get transaction history

## 📦 Project Structure

```
ryt-bank-app/
├── main.py              # FastAPI backend server
├── database.py          # Database models and setup
├── app.html             # Main frontend HTML
├── app.css              # Styling
├── app.js               # Frontend JavaScript
├── requirements.txt     # Python dependencies
├── START.bat            # Windows startup script
├── .env                 # Environment variables (create this)
├── .gitignore          # Git ignore file
└── README.md           # This file
```

## 🚀 Deploying to GitHub

### Step 1: Initialize Git Repository
```bash
git init
```

### Step 2: Add All Files
```bash
git add .
```

### Step 3: Create Initial Commit
```bash
git commit -m "Initial commit: Ryt Bank app"
```

### Step 4: Create GitHub Repository
1. Go to [GitHub](https://github.com)
2. Click "New repository"
3. Name it (e.g., "ryt-bank-app")
4. Don't initialize with README (we already have one)
5. Click "Create repository"

### Step 5: Connect and Push
```bash
git remote add origin https://github.com/YOUR_USERNAME/ryt-bank-app.git
git branch -M main
git push -u origin main
```

### Important Notes for GitHub
- **Never commit `.env` file** - It contains sensitive API keys
- The `.gitignore` file is already set up to exclude sensitive files
- Make sure `ryt_bank.db` is in `.gitignore` (it's already there)

## 🔐 Security Notes

- The `.env` file is in `.gitignore` and won't be committed
- JWT tokens are used for authentication
- Passwords are hashed using bcrypt
- API keys should never be shared or committed

## 🎨 Customization

### Changing Colors
Edit `app.css` and modify the CSS variables in `:root`:
```css
:root {
    --primary: #6366f1;
    --secondary: #8b5cf6;
    /* ... */
}
```

### Adding Features
- Backend: Add endpoints in `main.py`
- Frontend: Add UI in `app.html` and logic in `app.js`

## 🐛 Troubleshooting

### Server won't start
- Make sure Python 3.8+ is installed
- Install dependencies: `pip install -r requirements.txt`
- Check if port 8000 is available

### Receipt OCR not working
- Verify your OpenAI API key in `.env`
- Check that you have credits in your OpenAI account

### Database errors
- Delete `ryt_bank.db` and restart the server (database will be recreated)
- Make sure SQLite is working on your system

## 📝 License

MIT License - Feel free to use this for your hackathon project!

## 👥 Credits

Built for Ryt Bank Hackathon Track

---

**Good luck with your hackathon! 🚀**
