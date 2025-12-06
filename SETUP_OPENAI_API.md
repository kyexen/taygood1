# Setup OpenAI API Key for Receipt OCR

## Error: "OpenAI API key not configured"

This error appears when you try to upload a receipt because the OCR feature uses OpenAI's Vision API.

---

## How to Fix:

### Step 1: Get an OpenAI API Key

1. Go to https://platform.openai.com/api-keys
2. Sign in or create an account
3. Click "Create new secret key"
4. Copy the key (starts with `sk-...`)

### Step 2: Create a `.env` File

Create a file named `.env` in the project root with this content:

```env
OPENAI_API_KEY=sk-your-actual-api-key-here
SECRET_KEY=your-secret-key-change-in-production
```

**Important:** Replace `sk-your-actual-api-key-here` with your real OpenAI API key!

### Step 3: Restart the Backend

```bash
# Stop the server (Ctrl+C if running)
python main.py
```

### Step 4: Test Receipt Upload

Upload a receipt image - it should now work! The AI will extract:
- Merchant name
- Date and time  
- Items with prices
- Subtotal, tax, total
- Location/address

---

## Alternative: Use Without OCR

If you don't want to use OpenAI (costs money), you can manually create test receipts in the database or modify the upload endpoint to accept manual input.

---

## Cost Note

OpenAI Vision API costs approximately:
- $0.01 per receipt image (with gpt-4-vision-preview)
- Very affordable for testing!

Make sure you have credits in your OpenAI account.

