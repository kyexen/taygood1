"""Database migration script to add new columns"""
import sqlite3

def migrate_database():
    """Add taxes_json and township columns to receipts table"""
    conn = sqlite3.connect('ryt_bank.db')
    cursor = conn.cursor()
    
    try:
        # Check if columns exist
        cursor.execute("PRAGMA table_info(receipts)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Add taxes_json column if it doesn't exist
        if 'taxes_json' not in columns:
            print("Adding taxes_json column...")
            cursor.execute("ALTER TABLE receipts ADD COLUMN taxes_json TEXT")
            print("✓ Added taxes_json column")
        else:
            print("✓ taxes_json column already exists")
        
        # Add township column if it doesn't exist
        if 'township' not in columns:
            print("Adding township column...")
            cursor.execute("ALTER TABLE receipts ADD COLUMN township TEXT")
            print("✓ Added township column")
        else:
            print("✓ township column already exists")
        
        conn.commit()
        print("\n✅ Database migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    print("Starting database migration...\n")
    migrate_database()

