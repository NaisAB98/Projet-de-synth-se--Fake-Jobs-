import os
import sqlite3
import tensorflow as tf
import numpy as np
import pandas as pd
import datetime
import pickle
import nltk
import re
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from flask import Flask, request, jsonify, session
from flask_cors import CORS
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences

app = Flask(__name__)
app.secret_key = 'supersecretkey'
CORS(app, supports_credentials=True)

# Charger le modèle une fois au démarrage de l'application
model = load_model('BIGRU_SVM_Model.h5')
model2 = load_model('BILSTM_SVM_Model_article.h5')

# Charger le classificateur Naive Bayes et les word_features
classifier = pickle.load(open('MNB.pickle', 'rb'))
word_features = pickle.load(open('word_features.pickle', 'rb'))

# Charger le classificateur Naive Bayes et les word_features pour les articles
classifier2 = pickle.load(open('LinearSVC_classifier.pickle', 'rb'))
word_features2 = pickle.load(open('word_features2.pickle', 'rb'))

# Lire le fichier CSV pour initialiser le tokenizer
train_data = pd.read_csv('TrainData.csv')
texts_tweets = train_data['Tweet_Text'].tolist()

train_data2 = pd.read_csv('train_article.csv')
texts_articles = train_data2['Article_Text'].astype(str).tolist()

# Initialiser et former le tokenizer
tokenizer = Tokenizer(num_words=100000, oov_token="<OOV>")
tokenizer.fit_on_texts(texts_tweets)

tokenizer2 = Tokenizer(num_words=100000, oov_token="<OOV>")
tokenizer2.fit_on_texts(texts_articles)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.session_protection = "strong"

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
            session['username'] = username  # Ajouter le nom d'utilisateur à la session
            return jsonify({'message': 'Login successful'}), 200
        return jsonify({'error': 'Invalid username or password'}), 401
    except Exception as e:
        return jsonify({'error': 'Internal Server Error'}), 500

@app.route('/api/logout', methods=['POST'])
@login_required
def logout():
    try:
        logout_user()
        session.pop('username', None)  # Supprimer le nom d'utilisateur de la session
        return jsonify({'message': 'Logout successful'}), 200
    except Exception as e:
        return jsonify({'error': 'Internal Server Error'}), 500
          
@app.route('/api/delete-account', methods=['POST'])
@login_required
def delete_account():
    try:
        # Delete user from users table
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute('DELETE FROM users WHERE id = ?', (current_user.id,))
        
        # Delete user's search history
        c.execute('DELETE FROM search_history WHERE user_id = ?', (current_user.id,))
        
        conn.commit()
        conn.close()

        # Logout the user
        logout_user()
        session.pop('username', None)

        return jsonify({'message': 'Account and search history deleted successfully'}), 200

    except Exception as e:
        print(f"Error in delete_account: {e}")
        return jsonify({'error': 'An error occurred while deleting account'}), 500


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

def get_features(tweet_text):
    tweet_words = set(tweet_text)
    features = {}
    for word in word_features:
        features['contains(%s)' % str(word)] = (word in tweet_words)
    return features

def get_features2(article_text):
    article_words = set(article_text)
    features = {}
    for word in word_features2:
        features['contains(%s)' % str(word)] = (word in article_words)
    return features

def predict_topic(tweet_text):
    tweet = nltk.word_tokenize(tweet_text.lower())
    return classifier.classify(get_features(tweet))

def predict_topic2(article_text):
    article = nltk.word_tokenize(article_text.lower())
    return classifier2.classify(get_features2(article))

def preprocess_text(text):
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\d+', '', text)
    stop_words = set(stopwords.words('english'))
    text = [i.lower() for i in word_tokenize(text) if i.lower() not in stop_words]
    return ' '.join(text)

@app.route('/api/search-history', methods=['GET'])
@login_required
def search_history():
    try:
        page = int(request.args.get('page', 1))
        results_per_page = 1000 #int(request.args.get('results_per_page', 10))
        offset = (page - 1) * results_per_page

        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute('SELECT tweet_content, result, timestamp FROM search_history WHERE user_id = ? ORDER BY timestamp DESC LIMIT ? OFFSET ?',
                  (current_user.id, results_per_page, offset))
        history = c.fetchall()
        conn.close()

        history_list = [{'content': row[0], 'result': row[1], 'timestamp': row[2]} for row in history]

        return jsonify({'history': history_list})
    except Exception as e:
        print(f"Error in search_history: {e}")  # Log the error
        return jsonify({'error': 'Internal Server Error'}), 500

@app.route('/api/check-tweet', methods=['POST'])
def check_tweet():
    try:
        data = request.get_json()
        tweet_content = data.get('content')
        retweets = min(data.get('retweets', 0), 9556)
        comments = min(data.get('comments', 0), 9556)
        likes = min(data.get('likes', 0), 9556)
        

        if not tweet_content:
            return jsonify({'error': 'Le contenu est requis'}), 400

        sequences = tokenizer.texts_to_sequences([tweet_content])
        text_data = pad_sequences(sequences, maxlen=500, padding='post', truncating='post')

        #tweet_content = preprocess_text(tweet_content)
        covid_prediction = predict_topic(tweet_content)

        if covid_prediction != 'covid':
            return jsonify({'covid_result': 'Ce tweet ne concerne pas le COVID-19', 'authenticity_result': ''})
        covid_result = 'Ce tweet concerne le COVID-19'

        numerical_data = np.array([[retweets, likes, comments]])
        input_data = np.hstack((text_data, numerical_data))

        prediction = model.predict(input_data)
        print("\nPrediction = ", prediction, "\n")
        prediction_score = prediction[0][0]

        if prediction_score > 1:
            authenticity_result = 'Ce tweet est probablement vrai.'
        else:
            authenticity_result = 'Ce tweet est probablement faux.'

        if current_user.is_authenticated:
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            conn = sqlite3.connect('users.db')
            c = conn.cursor()
            c.execute('INSERT INTO search_history (user_id, tweet_content, result, timestamp) VALUES (?, ?, ?, ?)',
                      (current_user.id, tweet_content, f"{covid_result} {authenticity_result}", timestamp))
            conn.commit()
            conn.close()

        return jsonify({'covid_result': covid_result, 'authenticity_result': authenticity_result})

    except Exception as e:
        print(f"Error in check_tweet: {e}")
        return jsonify({'error': 'An error occurred while checking the tweet'}), 500

@app.route('/api/check-article', methods=['POST'])
def check_article_endpoint():
    try:
        data = request.get_json()
        article_content = data.get('article_content')
        name = data.get('article_name', '')

        if not article_content:
            return jsonify({'error': "Le contenu de l'article est requis"}), 400

        sequences = tokenizer2.texts_to_sequences([article_content])
        text_data = pad_sequences(sequences, maxlen=500, padding='post', truncating='post')

        #article_content = preprocess_text(article_content)
        covid_prediction = predict_topic2(article_content)

        if covid_prediction != 'covid':
            return jsonify({'covid_result': 'Cet article ne concerne pas le COVID-19', 'authenticity_result': ''})
        covid_result = 'Cet article concerne le COVID-19'

        input_data = np.array(text_data)

        prediction = model2.predict(input_data)
        print("\nPrediction = ", prediction, "\n")
        prediction_score = prediction[0][0]

        if prediction_score > 1:
            authenticity_result = 'Cet article est probablement vrai.'
        else:
            authenticity_result = 'Cet article est probablement faux.'

        if current_user.is_authenticated:
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            conn = sqlite3.connect('users.db')
            c = conn.cursor()
            c.execute('INSERT INTO search_history (user_id, tweet_content, result, timestamp) VALUES (?, ?, ?, ?)',
                      (current_user.id, article_content, f"{covid_result} {authenticity_result}", timestamp))
            conn.commit()
            conn.close()

        return jsonify({'covid_result': covid_result, 'authenticity_result': authenticity_result})

    except Exception as e:
        print(f"Error in check_article_endpoint: {e}")
        return jsonify({'error': 'An error occurred while checking the article'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
