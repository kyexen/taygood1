"""Fix existing receipts by adding township and location data"""
import sqlite3

def fix_receipts():
    """Update existing receipts with township based on their address"""
    conn = sqlite3.connect('ryt_bank.db')
    cursor = conn.cursor()
    
    # Get all receipts
    cursor.execute("SELECT id, merchant_name, location_address, location_lat, location_lng, township FROM receipts")
    receipts = cursor.fetchall()
    
    print(f"Found {len(receipts)} receipts to check\n")
    
    township_keywords = {
        'sunway': 'Bandar Sunway',
        'bandar sunway': 'Bandar Sunway',
        'petaling jaya': 'Petaling Jaya',
        'bangsar': 'Bangsar',
        'puchong': 'Puchong',
        'subang jaya': 'Subang Jaya',
        'kelana jaya': 'Kelana Jaya',
        'kl sentral': 'KL Sentral',
        'damansara': 'Damansara',
        'cheras': 'Cheras',
        'ampang': 'Ampang'
    }
    
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
    
    updated = 0
    for receipt in receipts:
        receipt_id, merchant_name, address, lat, lng, township = receipt
        
        needs_update = False
        new_township = township
        new_lat = lat
        new_lng = lng
        
        # Detect township from merchant name or address
        search_text = f"{merchant_name or ''} {address or ''}".lower()
        
        if not township:
            for keyword, town_name in township_keywords.items():
                if keyword in search_text:
                    new_township = town_name
                    needs_update = True
                    print(f"Receipt {receipt_id} ({merchant_name}): Detected township '{town_name}' from '{keyword}'")
                    break
        
        # Set coordinates if missing
        if (not lat or not lng) and new_township and new_township in township_coords:
            new_lat, new_lng = township_coords[new_township]
            needs_update = True
            print(f"  → Setting coordinates: {new_lat}, {new_lng}")
        
        if needs_update:
            cursor.execute(
                "UPDATE receipts SET township = ?, location_lat = ?, location_lng = ? WHERE id = ?",
                (new_township, new_lat, new_lng, receipt_id)
            )
            updated += 1
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Updated {updated} receipts with location data")
    print("Restart the backend: python main.py")

if __name__ == "__main__":
    fix_receipts()

