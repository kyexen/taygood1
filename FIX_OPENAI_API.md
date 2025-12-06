# Fix OpenAI API Connection Issue

## The Problem
You're seeing "incorrect api connected" because the `.env` file either:
1. Doesn't exist
2. Has incorrect API key
3. Has extra spaces/formatting issues

---

## Solution: Create/Fix .env File

### Step 1: Create .env File

In your project root (same folder as `main.py`), create a file named `.env` (starts with a dot!)

**Windows:**
1. Open Notepad
2. Click File → Save As
3. Set "File name" to: `.env` (with quotes!)
4. Set "Save as type" to: All Files
5. Save in project root folder

**OR use Command Prompt:**
```cmd
cd C:\Users\kyexe\Downloads\drive-download-20251206T045202Z-3-001
echo OPENAI_API_KEY=your-key-here > .env
```

### Step 2: Add Your API Key

Edit the `.env` file to contain:

```env
OPENAI_API_KEY=sk-proj-your-actual-api-key-here
SECRET_KEY=your-secret-key-change-in-production
```

**IMPORTANT:** 
- Replace `sk-proj-your-actual-api-key-here` with your REAL OpenAI API key
- No spaces around the `=` sign
- No quotes needed
- API key should start with `sk-proj-` or `sk-`

### Step 3: Get Your OpenAI API Key

If you don't have one or need a new one:

1. Go to: https://platform.openai.com/api-keys
2. Sign in with your OpenAI account
3. Click "Create new secret key"
4. Give it a name (e.g., "RytBank")
5. Copy the key (starts with `sk-proj-` or `sk-`)
6. Paste it in your `.env` file

### Step 4: Restart Backend

After creating/updating `.env`:

```bash
# Stop the server (Ctrl+C)
python main.py
```

You should see:
```
✓ OpenAI client initialized
```

If you see a warning, the API key is not loaded correctly.

---

## Common Issues & Fixes

### Issue: "File not found" when creating .env

**Fix:**
- Make sure you're in the project root
- Use quotes when naming: `".env"`
- Don't add `.txt` extension

### Issue: Still says API not configured

**Fix:**
1. Check `.env` is in the same folder as `main.py`
2. Verify no spaces: `OPENAI_API_KEY=sk-...` (not `OPENAI_API_KEY = sk-...`)
3. Restart the backend server
4. Check terminal for "✓ OpenAI client initialized"

### Issue: API key invalid

**Fix:**
1. Go to OpenAI dashboard
2. Check if key is active
3. Create a new key if expired
4. Make sure you copied the entire key

---

## Verify It's Working

After restarting, check the terminal:

**✅ Good:**
```
✓ OpenAI client initialized
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**❌ Bad:**
```
⚠ Warning: OPENAI_API_KEY not found in .env file
```

---

## Example .env File

```env
# OpenAI API Key for Receipt OCR
OPENAI_API_KEY=sk-proj-AbCdEfGhIjKlMnOpQrStUvWxYz1234567890

# JWT Secret (can be any random string)
SECRET_KEY=my-super-secret-key-12345
```

---

## Quick Test

After fixing, upload a receipt to test:
1. Go to app
2. Click upload receipt
3. Choose an image
4. Should process without "API not configured" error

---

## Still Not Working?

1. **Check the terminal output** when starting `python main.py`
2. **Send me the exact error message** you see
3. **Verify API key** is valid on OpenAI dashboard
4. **Check you have credits** in your OpenAI account

The API call costs ~$0.01 per receipt, so make sure you have credits!

