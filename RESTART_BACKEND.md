# How to Restart the Backend Server

## The Delete Receipt Feature Requires Backend Restart

The new `DELETE /api/receipts/{receipt_id}` endpoint was just added to `main.py`.

To activate it, you need to **restart the backend server**.

---

## Steps to Restart:

### **Option 1: Using Terminal**

1. Find the terminal running the backend (the one showing FastAPI logs)
2. Press **Ctrl+C** to stop the server
3. Run again:
   ```bash
   python main.py
   ```

### **Option 2: If You Don't Know Which Terminal**

1. Open a new terminal in the project root
2. Run:
   ```bash
   python main.py
   ```
3. The server will start on `http://localhost:8000`

---

## Verify It's Working

After restarting, you should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

Then the delete receipt feature will work! 🗑️✨

---

## What Was Added:

- `DELETE /api/receipts/{receipt_id}` endpoint
- Deletes receipt and associated bill splits
- Validates user ownership
- Returns success message

