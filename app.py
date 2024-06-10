from flask import Flask, request, jsonify, session
from flask_cors import CORS
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
import sqlite3
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
import numpy as np
import pandas as pd

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Changez cela pour une clé secrète aléatoire en production
CORS(app, supports_credentials=True)

# Charger le modèle une fois au démarrage de l'application
model = load_model('BIGRU_SVM_Model.h5')

# Lire le fichier CSV pour initialiser le tokenizer
train_data = pd.read_csv('TrainData.csv')
texts = train_data['Tweet_Text'].tolist()  # Remplacez 'text_column_name' par le nom de la colonne contenant les textes

# Initialiser et former le tokenizer
tokenizer = Tokenizer(num_words=100000, oov_token="<OOV>")
tokenizer.fit_on_texts(texts)

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

# Initialisation de la table 'search_history'
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

# Reste du code
@app.route('/api/check-tweet', methods=['POST'])
def check_tweet():
    try:
        data = request.get_json()
        tweet_content = data.get('content')
        retweets = data.get('retweets', 0)
        comments = data.get('comments', 0)
        likes = data.get('likes', 0)

        if not tweet_content:
            return jsonify({'error': 'Le contenu est requis'}), 400

        # Prétraitement du texte d'entrée
        sequences = tokenizer.texts_to_sequences([tweet_content])
        text_data = pad_sequences(sequences, maxlen=500, padding='post', truncating='post')

        # Combinaison des données textuelles et numériques
        numerical_data = np.array([[retweets, likes, comments]])
        input_data = np.hstack((text_data, numerical_data))

        # Prédire en utilisant le modèle chargé
        prediction = model.predict(input_data)
        print(f'Prediction: {prediction}')  # Affichez la prédiction pour déboguer
        prediction_score = prediction[0][0]

        # Détermination du résultat basé sur le score de prédiction
        if prediction_score < 0:
            result = 'This tweet is likely fake news.'
        else:
            result = 'This tweet is likely legitimate news.'

        # Enregistrer la recherche dans l'historique si l'utilisateur est connecté
        if 'username' in session:
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            username = session['username']
            new_search = SearchHistory(username=username, content=tweet_content, result=result, timestamp=timestamp)
            db.session.add(new_search)
            db.session.commit()

        return jsonify({'result': result})

    except Exception as e:
        print(f"Error in check_tweet: {e}")  # Log the error
        return jsonify({'error': 'An error occurred while checking the tweet'}), 500


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
