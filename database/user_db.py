import sqlite3
import datetime
from datetime import datetime

current_time = datetime.now()

conn = sqlite3.connect('data/data.db')
cursor = conn.cursor()

def create_table():
    conn = sqlite3.connect('data/data.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            user_name TEXT,
            user_first_name TEXT,
            user_last_name TEXT,
            phone INTEGER
        )
    ''')
    conn.commit()

def add_user(user_id, user_name, ref):
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    existing_user = cursor.fetchone()
    if existing_user is None:
        cursor.execute('''
            INSERT INTO users (user_id, user_name, ref)
            VALUES (?, ?, ?)
        ''', (user_id, user_name, ref))
        conn.commit()
        
def check_user(uid):
    cursor.execute(f'SELECT * FROM Users WHERE user_id = {uid}')
    user = cursor.fetchone()
    if user:
        return True
    return False
    
def update_ref(user_id, ref):
    conn = sqlite3.connect('data/data.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET ref = ? WHERE user_id = ?', (ref, user_id))
    conn.commit()
    conn.close()
    
def get_referrals_count(user_id):
    cursor.execute("SELECT COUNT(*) FROM users WHERE ref = ?", (user_id,))
    count = cursor.fetchone()[0]
    return count

def get_categories_from_db():
    conn = sqlite3.connect('data/data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT category, COUNT(*) FROM channels WHERE active = 1 GROUP BY category")
    categories_with_counts = cursor.fetchall()
    conn.close()
    return categories_with_counts


def get_nonactive_categories_from_db():
    conn = sqlite3.connect('data/data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT category, COUNT(*) FROM channels WHERE active = 0 GROUP BY category")
    categories_with_counts = cursor.fetchall()
    conn.close()
    return categories_with_counts


def get_records_by_category(category):
    conn = sqlite3.connect('data/data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT channel_name, channel_link, category, channel_id, [order], payment, payment_type, comentary FROM channels WHERE category = ?", (category,))
    records = cursor.fetchall()
    conn.close()
    return records


def get_record_by_channel_id(channel_id):
    conn = sqlite3.connect('data/data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT channel_name, channel_link, category, channel_id, [order], payment, payment_type, comentary FROM channels WHERE channel_id = ?", (channel_id,))
    record = cursor.fetchone()
    conn.close()
    return record


def fetch_offers_by_category(category):
    conn = sqlite3.connect('data/data.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, channel_name, came, `order` FROM channels WHERE category=?  AND active = 1", (category,))
    offers = cursor.fetchall()
    
    valid_offers = []
    for offer in offers:
        offer_id, channel_name, came, order = offer
        if came >= order:
            cursor.execute("UPDATE channels SET active = 0 WHERE id = ?", (offer_id,))
            cursor.execute("UPDATE links SET active = 0 WHERE channel_name = ?", (channel_name,))
        else:
            valid_offers.append({'id': offer_id, 'channel_name': channel_name})
    
    conn.commit()
    conn.close()
    
    return valid_offers



def fetch_inactive_offers_by_category(category):
    conn = sqlite3.connect('data/data.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, channel_name, came, `order` FROM channels WHERE category = ? AND active = 0", (category,))
    offers = cursor.fetchall()
    
    valid_offers = []
    for offer in offers:
        offer_id, channel_name, came, order = offer
        if came >= order:
            cursor.execute("UPDATE channels SET active = 0 WHERE id = ?", (offer_id,))
            cursor.execute("UPDATE links SET active = 0 WHERE channel_name = ?", (channel_name,))
        else:
            valid_offers.append({'id': offer_id, 'channel_name': channel_name})
    
    conn.commit()
    conn.close()
    
    return valid_offers


def fetch_offer_details(offer_id):
    conn = sqlite3.connect('data/data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM channels WHERE id=?", (offer_id,))
    offer = cursor.fetchone()
    conn.close()
    
    if offer:
        return {
            'id': offer[0],
            'channel_id': offer[1],
            'channel_name': offer[2],
            'channel_link': offer[3],
            'category': offer[4],
            'order': offer[6],
            'came': offer[7],
            'payment': offer[5],
            'payment_type': offer[8],
            'comentary': offer[9]
        }
    return None


def create_links_table():
    conn = sqlite3.connect('data/data.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS links (
            link TEXT,
            channel_id INTEGER,
            user_id INTEGER,
            used INTEGER
        )
    ''')
    conn.commit()
    conn.close()

def add_link(link: str, channel_id: int, user_id: int, channel_name: str, payment: float):
    conn = sqlite3.connect('data/data.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO links (link, channel_id, user_id, channel_name, used, payment)
        VALUES (?, ?, ?, ?, 0, ?)
    ''', (link, channel_id, user_id, channel_name, payment))
    conn.commit()
    conn.close()

    
def get_links_for_user(user_id, channel_id):
    conn = sqlite3.connect('data/data.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT link, used FROM links
        WHERE user_id = ? AND channel_id = ?
    ''', (user_id, channel_id))
    links = cursor.fetchall()
    conn.close()
    return links


async def update_link_and_channel(invite_link):
    conn = sqlite3.connect('data/data.db')
    cursor = conn.cursor()

    try:
        # Обновление значения `used` в таблице `links`
        cursor.execute('''
            UPDATE links
            SET used = used + 1
            WHERE link = ?
        ''', (invite_link,))

        # Получение channel_id для данного посилання
        cursor.execute('''
            SELECT channel_id
            FROM links
            WHERE link = ?
        ''', (invite_link,))
        channel_id_tuple = cursor.fetchone()

        if channel_id_tuple:
            channel_id = channel_id_tuple[0]
            print(f"Полученный channel_id: {channel_id}")

            # Проверка, существует ли канал с таким channel_id в таблице channels
            cursor.execute('''
                SELECT *
                FROM channels
                WHERE channel_id = ?
            ''', (channel_id,))
            channel_exists = cursor.fetchone()

            if channel_exists:
                print(f"Канал с channel_id {channel_id} существует в таблице channels.")

                # Проверка текущего значения `came`
                cursor.execute('''
                    SELECT came
                    FROM channels
                    WHERE channel_id = ?
                ''', (channel_id,))
                current_came = cursor.fetchone()
                if current_came:
                    print(f"Текущее значение `came`: {current_came[0]}")

                # Обновление значения `came` в таблице `channels`
                cursor.execute('''
                    UPDATE channels
                    SET came = came + 1
                    WHERE channel_id = ?
                ''', (channel_id,))

                # Проверка обновленного значения `came`
                cursor.execute('''
                    SELECT came
                    FROM channels
                    WHERE channel_id = ?
                ''', (channel_id,))
                updated_came = cursor.fetchone()
                if updated_came:
                    print(f"Обновленное значение `came`: {updated_came[0]}")
            else:
                print(f"Канал с channel_id {channel_id} не найден в таблице channels.")
        else:
            print(f"Посилання {invite_link} не найдено в таблице links.")

        conn.commit()
    except Exception as e:
        print(f"Ошибка при обновлении базы данных: {e}")
    finally:
        conn.close()


def get_user_id_by_link(invite_link):
    conn = sqlite3.connect('data/data.db')
    cursor = conn.cursor()

    try:
        cursor.execute('''
            SELECT user_id
            FROM links
            WHERE link = ?
        ''', (invite_link,))
        user_id_tuple = cursor.fetchone()
        if user_id_tuple:
            return user_id_tuple[0]
        else:
            return None
    except Exception as e:
        print(f"Ошибка при получении user_id: {e}")
    finally:
        conn.close()


def update_user_balance(user_id, payment):
    conn = sqlite3.connect('data/data.db')
    cursor = conn.cursor()

    try:
        # Получение текущего баланса пользователя
        cursor.execute('''
            SELECT balance
            FROM users
            WHERE user_id = ?
        ''', (user_id,))
        balance_tuple = cursor.fetchone()
        if balance_tuple:
            current_balance = balance_tuple[0]
        else:
            current_balance = 0

        # Обновление баланса пользователя
        new_balance = current_balance + payment
        cursor.execute('''
            UPDATE users
            SET balance = ?
            WHERE user_id = ?
        ''', (new_balance, user_id))

        conn.commit()
    except Exception as e:
        print(f"Ошибка при обновлении баланса пользователя: {e}")
    finally:
        conn.close()


def get_channel_id_by_link(invite_link):
    conn = sqlite3.connect('data/data.db')
    cursor = conn.cursor()

    try:
        cursor.execute('''
            SELECT channel_id
            FROM links
            WHERE link = ?
        ''', (invite_link,))
        channel_id_tuple = cursor.fetchone()
        if channel_id_tuple:
            return channel_id_tuple[0]
        else:
            return None
    except Exception as e:
        print(f"Ошибка при получении channel_id: {e}")
    finally:
        conn.close()

def get_payment_by_channel_id(channel_id):
    conn = sqlite3.connect('data/data.db')
    cursor = conn.cursor()

    try:
        cursor.execute('''
            SELECT payment
            FROM channels
            WHERE channel_id = ?
        ''', (channel_id,))
        payment_tuple = cursor.fetchone()
        if payment_tuple:
            return payment_tuple[0]
        else:
            return None
    except Exception as e:
        print(f"Ошибка при получении payment: {e}")
    finally:
        conn.close()


def add_user_to_came_users(channel_id, user_id):
    conn = sqlite3.connect('data/data.db')
    cursor = conn.cursor()

    try:
        # Get the current `came_users` value
        cursor.execute('''
            SELECT came_users
            FROM channels
            WHERE channel_id = ?
        ''', (channel_id,))
        came_users_tuple = cursor.fetchone()

        if came_users_tuple:
            came_users = came_users_tuple[0]
            if came_users:
                # Append the new user_id to the existing list
                came_users_list = came_users.split(',')
                if str(user_id) not in came_users_list:
                    came_users_list.append(str(user_id))
                    came_users = ','.join(came_users_list)
            else:
                # Initialize the list with the new user_id
                came_users = str(user_id)
        else:
            # Initialize the list with the new user_id if no record exists
            came_users = str(user_id)

        # Update the `came_users` column
        cursor.execute('''
            UPDATE channels
            SET came_users = ?
            WHERE channel_id = ?
        ''', (came_users, channel_id))

        conn.commit()
    except Exception as e:
        print(f"Ошибка при обновлении came_users: {e}")
    finally:
        conn.close()


def is_user_in_came_users(channel_id, user_id):
    conn = sqlite3.connect('data/data.db')
    cursor = conn.cursor()

    try:
        cursor.execute('''
            SELECT came_users
            FROM channels
            WHERE channel_id = ?
        ''', (channel_id,))
        came_users_tuple = cursor.fetchone()

        if came_users_tuple:
            came_users = came_users_tuple[0]
            if isinstance(came_users, int):
                came_users = str(came_users)
            if came_users:
                came_users_list = came_users.split(',')
                if str(user_id) in came_users_list:
                    return True
        return False
    except Exception as e:
        print(f"Ошибка при проверке came_users: {e}")
        return False
    finally:
        conn.close()
        
        
def add_ofer_user(sender_user_id):
    con = sqlite3.connect('data/data.db')
    cur = con.cursor()
    cur.execute('''
        UPDATE users SET ofers = ofers + 1 WHERE user_id = ?
    ''', (sender_user_id,))  # Fixed line
    con.commit()
    con.close()
        
        
def get_user_data(user_id):
    conn = sqlite3.connect('data/data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user


def update_user_card(user_id, card_number):
    conn = sqlite3.connect('data/data.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET card = ? WHERE user_id = ?', (card_number, user_id))
    conn.commit()
    conn.close()


def update_user_balance(user_id, payment):
    conn = sqlite3.connect('data/data.db')
    cursor = conn.cursor()

    try:
        cursor.execute('''
            SELECT balance
            FROM users
            WHERE user_id = ?
        ''', (user_id,))
        balance_tuple = cursor.fetchone()

        if balance_tuple:
            current_balance = balance_tuple[0]
        else:
            print(f"User with ID {user_id} not found.")
            return

        new_balance = current_balance + payment

        if new_balance < 0:
            new_balance = 0
            
        cursor.execute('''
            UPDATE users
            SET balance = ?
            WHERE user_id = ?
        ''', (new_balance, user_id))

        conn.commit()
    except Exception as e:
        print(f"Error updating user balance: {e}")
    finally:
        conn.close()


def create_links_table():
    conn = sqlite3.connect('data/data.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS links (
            link TEXT,
            channel_id INTEGER,
            user_id INTEGER,
            used INTEGER
        )
    ''')
    conn.commit()
    conn.close()
    
def get_user_channels(user_id):
    conn = sqlite3.connect('data/data.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT DISTINCT channel_name
        FROM links
        WHERE user_id = ? AND active = 1
    ''', (user_id,))
    channels = cursor.fetchall()
    conn.close()
    return [channel[0] for channel in channels]

def get_channel_statistics(user_id, channel_name):
    conn = sqlite3.connect('data/data.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT link, used, payment
        FROM links
        WHERE user_id = ? AND channel_name = ?
    ''', (user_id, channel_name))
    links = cursor.fetchall()
    conn.close()

    if links:
        total_payment = sum(link[1] * link[2] for link in links)  # Сумма доходов (used * payment)
        total_used = sum(link[1] for link in links)  # Сумма использований
        links_list = "\n".join([f"<code>{link[0]}</code> ({link[1]})" for link in links])

        return {
            'channel_name': channel_name,
            'total_payment': total_payment,
            'total_used': total_used,
            'links_list': links_list
        }
    return None



def check_user_language(user_id):
    conn = sqlite3.connect('data/data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT lang FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    if result:
        return result[0]
    else:
        return None
    
def update_user_language(user_id, lang):
    conn = sqlite3.connect('data/data.db')
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE users
        SET lang = ?
        WHERE user_id = ?
    ''', (lang, user_id))
    conn.commit()
    conn.close()