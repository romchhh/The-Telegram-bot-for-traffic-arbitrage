import sqlite3


def get_users_count():
    conn = sqlite3.connect('data/data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_active_users_count():
    conn = sqlite3.connect('data/data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users WHERE phone IS NOT NULL")
    count = cursor.fetchone()[0]
    conn.close()
    return count

def init_db():
    conn = sqlite3.connect('data/data.db')
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS channels (
            id INTEGER PRIMARY KEY,
            channel_id INTEGER,
            channel_name TEXT,
            channel_link TEXT,
            category TEXT,
            payment INTEGER,
            [order] INTEGER,
            came INTEGER,
            payment_type TEXT,
            comentary TEXT
        )
    """)
    conn.commit()
    conn.close()

def add_channel(channel_name, channel_link, channel_id, category, payment, order, payment_type, commentary):
    conn = sqlite3.connect('data/data.db')
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO channels (channel_id, channel_name, channel_link, category, payment, [order], payment_type, comentary)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (channel_id, channel_name, channel_link, category, payment, order, payment_type, commentary))
    conn.commit()
    conn.close()
    
    
def get_users_count():
    conn = sqlite3.connect('data/data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_active_users_count():
    conn = sqlite3.connect('data/data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users WHERE ofers != 0")
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_all_user_ids():
    conn = sqlite3.connect('data/data.db') 
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM users')
    user_ids = [row[0] for row in cursor.fetchall()]
    conn.close()
    return user_ids


def set_offer_inactive(offer_id):
    conn = sqlite3.connect('data/data.db')
    cursor = conn.cursor()

    # Get the channel_name for the given offer_id
    cursor.execute("SELECT channel_name FROM channels WHERE id = ?", (offer_id,))
    channel_name = cursor.fetchone()
    
    if channel_name:
        channel_name = channel_name[0]
        # Update the active status in the channels table
        cursor.execute("UPDATE channels SET active = 0 WHERE id = ?", (offer_id,))
        
        # Update the active status in the links table
        cursor.execute("UPDATE links SET active = 0 WHERE channel_name = ?", (channel_name,))
    
    conn.commit()
    conn.close()


def add_quantity_to_offer(offer_id, quantity):
    conn = sqlite3.connect('data/data.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE channels SET `order` = `order` + ? WHERE id = ?", (quantity, offer_id))
    conn.commit()
    conn.close()