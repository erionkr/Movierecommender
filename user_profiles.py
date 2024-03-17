import sqlite3
# Da die direkte Integration von Dash und Callbacks in diesem Umfeld nicht möglich ist,
# skizzieren wir den erforderlichen Code und logische Struktur für die Umsetzung.

def add_user_to_database(conn, username, email, password):
    """
    Fügt einen neuen Benutzer zur Datenbank hinzu.
    """
    sql = ''' INSERT INTO users(username,email,password)
              VALUES(?,?,?) '''
    cur = conn.cursor()
    cur.execute(sql, (username, email, password))
    conn.commit()
    return cur.lastrowid

def user_exists(conn, username):
    """
    Überprüft, ob ein Benutzer bereits existiert.
    """
    sql = ''' SELECT * FROM users WHERE username=? '''
    cur = conn.cursor()
    cur.execute(sql, (username,))
    rows = cur.fetchall()
    return len(rows) > 0

def validate_user(conn, username, password):
    """
    Überprüft die Anmeldeinformationen eines Benutzers.
    """
    sql = ''' SELECT * FROM users WHERE username=? AND password=? '''
    cur = conn.cursor()
    cur.execute(sql, (username, password))
    rows = cur.fetchall()
    return len(rows) > 0

def add_user_preference(conn, user_id, genre):
    """
    Fügt die Präferenzen eines Benutzers zur Datenbank hinzu.
    """
    sql = ''' INSERT INTO preferences(user_id,genre)
              VALUES(?,?) '''
    cur = conn.cursor()
    cur.execute(sql, (user_id, genre))
    conn.commit()
    return cur.lastrowid

# Beispiel für einen Callback, der für die Registrierung eines Benutzers verwendet werden könnte
def register_user_callback(username, email, password):
    # Hier würden Sie die Verbindung zur Datenbank herstellen
    conn = create_connection("pythonsqlite.db")
    if not user_exists(conn, username):
        user_id = add_user_to_database(conn, username, email, password)
        return f"Benutzer {username} erfolgreich registriert!"
    else:
        return "Benutzername bereits vergeben!"

# Beispiel für einen Callback zur Benutzervalidierung/Anmeldung
def validate_user_callback(username, password):
    conn = create_connection("pythonsqlite.db")
    if validate_user(conn, username, password):
        return "Anmeldung erfolgreich!"
    else:
        return "Anmeldedaten ungültig!"

# Hinweis: Die Callback-Funktionen `register_user_callback` und `validate_user_callback` müssen
# mit Dash Callbacks verbunden werden, um auf Benutzereingaben aus der Webanwendung zu reagieren. 
# Diese Beispiele dienen lediglich zur Veranschaulichung der Logik, die Sie für die Interaktion mit der Datenbank verwenden würden.
