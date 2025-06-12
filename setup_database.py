import sqlite3

conn = sqlite3.connect('/Users/hemantkumarroy/Desktop/Project folder/Budget_app/budget.db', check_same_thread=False)
conn.execute("PRAGMA foreign_keys = ON")
cur = conn.cursor()

#DROP TABLE IF THEY EXIST
cur.execute('DROP TABLE IF EXISTS categories')
cur.execute('DROP TABLE IF EXISTS transactions')
cur.execute('DROP TABLE IF EXISTS users')

#CREATE USERS TABLE
cur.execute('''
CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password BLOB NOT NULL
            )
''')

#CREATE CATEGORIES TABLE
cur.execute('''
CREATE TABLE categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
            )
''')

#insering default categories
default_cat = ['Grocery','Utilites','Transport']
for cat in default_cat:
    try:
        cur.execute("INSERT INTO categories (name) VALUES (?)", (cat,))
    except sqlite3.IntegrityError:
        pass 

#CREATE TRANSACTIONS TABLE
cur.execute('''
CREATE TABLE transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            type TEXT CHECK(type in ('income','expense')) NOT NULL,
            date TEXT NOT NULL,
            category TEXT,
            amount REAL NOT NULL,
            description TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
            )

''')

#INSERT A SAMPLE DATA
#The ? marks are placeholders to safely insert values using Python.
#This method prevents SQL injection, making your code more secure.
cur.execute("INSERT INTO users(username,email,password) VALUES (?,?,?)",
            ('USER1','USER1@EXP.COM','PASS@USER1'))

#get new user's id
user_id = cur.lastrowid

sample_data = [
    (user_id,'income', '2025-06-01', 'Salary', 3000.00, 'Monthly salary'),
    (user_id,'expense', '2025-06-01', 'Rent', -1200.00, 'June rent'),
    (user_id,'expense','2025-06-01', 'Groceries', -150.00, 'Weekly groceries')
]

#insert sample data into tranaction table
cur.executemany('''
INSERT INTO transactions (user_id,type,date,category,amount, description)
VALUES (?, ?, ?, ?, ?, ?)
''',sample_data)

conn.commit()
conn.close()

print("Database with users and transactions created.")
