# app.py

from flask import Flask, request, jsonify, session
from flask_cors import CORS
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
import sqlite3

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Changez cela pour une clé secrète aléatoire en production
CORS(app, supports_credentials=True)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.session_protection = "strong"  # Ajoutez cette ligne

class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

    @staticmethod
    def get(user_id):
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user = c.fetchone()
        conn.close()
        if user:
            return User(user[0], user[1], user[2])
        return None

    @staticmethod
    def find_by_username(username):
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = c.fetchone()
        conn.close()
        if user:
            return User(user[0], user[1], user[2])
        return None

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400

        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
        conn.commit()
        conn.close()

        return jsonify({'message': 'User registered successfully'}), 201
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Username already exists'}), 400
    except Exception as e:
        return jsonify({'error': 'Internal Server Error'}), 500

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        user = User.find_by_username(username)
        if user and user.password == password:
            login_user(user)
            return jsonify({'message': 'Login successful'}), 200
        return jsonify({'error': 'Invalid username or password'}), 401
    except Exception as e:
        return jsonify({'error': 'Internal Server Error'}), 500

@app.route('/api/logout', methods=['POST'])
@login_required
def logout():
    try:
        logout_user()
        return jsonify({'message': 'Logout successful'}), 200
    except Exception as e:
        return jsonify({'error': 'Internal Server Error'}), 500

# Ajoutez cette fonction pour initialiser la table 'search_history'
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS search_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        tweet_content TEXT,
        result TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')
    conn.commit()
    conn.close()

# Appelez init_db() au démarrage de l'application
init_db()

@app.route('/api/check-tweet', methods=['POST'])
def check_tweet():
    try:
        data = request.data.decode('utf-8-sig')
        print('Data received:', data)
                
        tweet_data = request.get_json()
        tweet_content = tweet_data.get('content')
        
        # vérification ici 

        if 'fake' in tweet_content:
            result = 'This tweet is likely fake news.'
        else:
            result = 'This tweet seems legitimate.'

        # Enregistrer la recherche si l'utilisateur est connecté
        if current_user.is_authenticated:
            conn = sqlite3.connect('users.db')
            c = conn.cursor()
            c.execute('INSERT INTO search_history (user_id, tweet_content, result) VALUES (?, ?, ?)', 
                      (current_user.id, tweet_content, result))
            conn.commit()
            conn.close()

        return jsonify({'result': result})
    except Exception as e:
        return jsonify({'error': 'Internal Server Error'}), 500

@app.route('/api/search-history', methods=['GET'])
@login_required  # Assurez-vous que l'utilisateur est connecté
def search_history():
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute('SELECT tweet_content, result, timestamp FROM search_history WHERE user_id = ?', (current_user.id,))
        history = c.fetchall()
        conn.close()

        # Formatez les données pour les envoyer au frontend
        history_list = [{'content': row[0], 'result': row[1], 'timestamp': row[2]} for row in history]

        return jsonify({'history': history_list})
    except Exception as e:
        return jsonify({'error': 'Internal Server Error'}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)
