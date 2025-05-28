from flask import Flask, request, render_template, redirect, url_for, session, flash
from flask_session import Session
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import requests
from database import Database
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Initialize database
db = Database('movie_recommender.db')

# Load and preprocess data
df = pd.read_csv("movies.csv")
df['overview'] = df['overview'].fillna('')
df['genres'] = df['genres'].fillna('')
df['combined'] = df['overview'] + ' ' + df['genres']
tfidf = TfidfVectorizer(stop_words='english')
tfidf_matrix = tfidf.fit_transform(df['combined'])
cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)
indices = pd.Series(df.index, index=df['title'].str.lower()).drop_duplicates()

OMDB_API_KEY = "a42bb1b4"


def get_movie_details(title):
    url = f"http://www.omdbapi.com/?t={title}&apikey={OMDB_API_KEY}"
    try:
        response = requests.get(url, timeout=5).json()
        if 'Error' in response:
            return None
        return {
            'poster': response.get("Poster", "https://via.placeholder.com/300x450?text=No+Poster"),
            'year': response.get("Year", "N/A"),
            'rated': response.get("Rated", "N/A"),
            'runtime': response.get("Runtime", "N/A"),
            'genre': response.get("Genre", "N/A"),
            'director': response.get("Director", "N/A"),
            'actors': response.get("Actors", "N/A"),
            'plot': response.get("Plot", "No plot available"),
            'imdb': response.get("imdbRating", "N/A"),
            'metascore': response.get("Metascore", "N/A")
        }
    except:
        return None


def recommend(title):
    title = title.lower()
    if title not in indices:
        return []
    idx = indices[title]
    sim_scores = list(enumerate(cosine_sim[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)[1:6]
    movie_indices = [i[0] for i in sim_scores]
    return df['title'].iloc[movie_indices].tolist()


def search_suggestions(query):
    query = query.lower()
    return [title for title in df['title'].str.lower().unique() if query in title][:5]


# Authentication routes
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if db.get_user(username):
            flash('Username already exists', 'error')
        else:
            db.create_user(username, generate_password_hash(password))
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
    return render_template('auth/register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = db.get_user(username)
        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            session['username'] = user[1]
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')
    return render_template('auth/login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))


# Main routes
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        movie = request.form['movie']
        if 'user_id' in session:
            db.add_search_history(session['user_id'], movie)
        results = recommend(movie)
        if not results:
            return render_template('index.html', error="Movie not found. Please try another title.")
        return render_template('result.html', movie=movie, results=results)
    return render_template('index.html')


@app.route('/suggestions')
def suggestions():
    query = request.args.get('q', '')
    return {'suggestions': search_suggestions(query)}


@app.route('/movie_details')
def movie_details():
    title = request.args.get('title')
    details = get_movie_details(title)
    return render_template('_movie_details.html', title=title, details=details)


@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    search_history = db.get_search_history(user_id)
    favorites = db.get_favorites(user_id)

    return render_template('profile.html',
                           search_history=search_history,
                           favorites=favorites)


@app.route('/add_favorite', methods=['POST'])
def add_favorite():
    if 'user_id' not in session:
        return {'status': 'error', 'message': 'Not logged in'}

    movie = request.form['movie']
    db.add_favorite(session['user_id'], movie)
    return {'status': 'success'}


@app.route('/remove_favorite', methods=['POST'])
def remove_favorite():
    if 'user_id' not in session:
        return {'status': 'error', 'message': 'Not logged in'}

    movie = request.form['movie']
    db.remove_favorite(session['user_id'], movie)
    return {'status': 'success'}

def get_poster(title):
    url = f"http://www.omdbapi.com/?t={title}&apikey={OMDB_API_KEY}"
    try:
        response = requests.get(url, timeout=5).json()
        return response.get("Poster", "https://via.placeholder.com/300x450?text=No+Poster")
    except:
        return "https://via.placeholder.com/300x450?text=Error+Loading"

@app.context_processor
def utility_processor():
    return dict(get_poster=get_poster)


if __name__ == '__main__':
    app.run(debug=True)