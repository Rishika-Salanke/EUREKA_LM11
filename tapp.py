import sqlite3
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# Function to create the database and table
def create_database():
    conn = sqlite3.connect('commuter_info.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS commuters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        phone_number TEXT NOT NULL,
        ip_address TEXT NOT NULL
    )
    ''')
    conn.commit()
    conn.close()

# Function to insert commuter info into the database
def insert_commuter(name, email, phone_number, ip_address):
    conn = sqlite3.connect('commuter_info.db')
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO commuters (name, email, phone_number, ip_address)
    VALUES (?, ?, ?, ?)
    ''', (name, email, phone_number, ip_address))
    conn.commit()
    conn.close()

# Function to get commuter info by IP address
def get_commuter_info(ip_address):
    conn = sqlite3.connect('commuter_info.db')
    cursor = conn.cursor()
    cursor.execute('''
    SELECT name, email, phone_number, ip_address FROM commuters
    WHERE ip_address = ?
    ''', (ip_address,))
    result = cursor.fetchone()
    conn.close()
    return result

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add_commuter', methods=['POST'])
def add_commuter():
    data = request.get_json()
    name = data['name']
    email = data['email']
    phone_number = data['phone_number']
    ip_address = data['ip_address']
    insert_commuter(name, email, phone_number, ip_address)
    return jsonify({"message": "Commuter added successfully!"}), 201

@app.route('/get_commuter', methods=['GET'])
def get_commuter():
    ip_address = request.args.get('ip_address')
    commuter_info = get_commuter_info(ip_address)
    if commuter_info:
        return jsonify({
            "name": commuter_info[0],
            "email": commuter_info[1],
            "phone_number": commuter_info[2],
            "ip_address": commuter_info[3]
        }), 200
    else:
        return jsonify({"message": "Commuter not found"}), 404

if __name__ == "__main__":
    create_database()
    app.run(debug=True)
