import sqlite3
from sqlite3 import Error

# Erstellen einer SQLite-Datenbank und Verbindung herstellen
def create_connection(db_file):
    """ Erstellen einer Datenbankverbindung zu SQLite-Datenbank """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)
    return conn

# Erstellen der Tabellen
def create_table(conn, create_table_sql):
    """ Erstellen einer Tabelle aus dem create_table_sql statement """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        print(e)

# SQL-Anweisungen für das Erstellen der Tabellen
sql_create_users_table = """ CREATE TABLE IF NOT EXISTS users (
                                        id integer PRIMARY KEY,
                                        username text NOT NULL,
                                        email text NOT NULL,
                                        password text NOT NULL
                                    ); """

sql_create_preferences_table = """ CREATE TABLE IF NOT EXISTS preferences (
                                        id integer PRIMARY KEY,
                                        user_id integer NOT NULL,
                                        genre text NOT NULL,
                                        FOREIGN KEY (user_id) REFERENCES users (id)
                                    ); """

# Hauptfunktion zur Initialisierung der Datenbank und Tabellen
def main():
    database = "pythonsqlite.db"

    # Verbindung zur SQLite-Datenbank herstellen
    conn = create_connection(database)

    # Tabellen erstellen
    if conn is not None:
        # Benutzertabelle erstellen
        create_table(conn, sql_create_users_table)

        # Präferenzentabelle erstellen
        create_table(conn, sql_create_preferences_table)
    else:
        print("Fehler! Kann keine Datenbankverbindung herstellen.")

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

# Die Hauptfunktion ausführen, um die Datenbank und Tabellen zu initialisieren
main()

