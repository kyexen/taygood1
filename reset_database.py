"""Reset database with new schema including taxes_json and township"""
import os
from database import Base, engine, init_db

def reset_database():
    """Drop all tables and recreate with new schema"""
    print("Resetting database with new schema...")
    
    # Backup warning
    print("\n⚠️  WARNING: This will delete all existing data!")
    print("⚠️  Make sure this is what you want to do.\n")
    
    response = input("Type 'yes' to continue: ")
    if response.lower() != 'yes':
        print("Cancelled.")
        return
    
    # Delete old database
    if os.path.exists('ryt_bank.db'):
        os.remove('ryt_bank.db')
        print("✓ Deleted old database")
    
    # Create new database with updated schema
    Base.metadata.create_all(bind=engine)
    print("✓ Created new database with updated schema")
    print("\n✅ Database reset complete!")
    print("✅ New columns added: taxes_json, township")
    print("\nYou can now restart the backend: python main.py")

if __name__ == "__main__":
    reset_database()

