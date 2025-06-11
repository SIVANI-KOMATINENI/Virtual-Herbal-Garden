import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory, jsonify
from werkzeug.utils import secure_filename
from transformers import GPT2LMHeadModel, GPT2Tokenizer, pipeline  # Chatbot imports
import torch
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  
app.secret_key = 'A4l0aZ6u1SdLPxZqbhNdHeY8ZG2s9p7Y9dXL3mP7'
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Chatbot setup
MODEL_PATH = "ayush_model"  
try:
    tokenizer = GPT2Tokenizer.from_pretrained(MODEL_PATH)
    model = GPT2LMHeadModel.from_pretrained(MODEL_PATH)
    model.eval()
    generator = pipeline("text-generation", model=model, tokenizer=tokenizer, device=0 if torch.cuda.is_available() else -1)
    print("Chatbot model loaded!")
except Exception as e:
    print(f"Error loading chatbot model: {e}")

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template('test.html')  

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        if user:
            flash('Username already exists.')
            conn.close()
            return redirect(url_for('signup'))
        conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
        conn.commit()
        conn.close()
        flash('Signup successful! Please login.')
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        con = sqlite3.connect("database.db")
        cur = con.cursor()
        cur.execute("SELECT id FROM users WHERE username = ? AND password = ?", (username, password))
        user = cur.fetchone()
        con.close()
        if user:
            session['user_id'] = user[0]
            return redirect('/community')
        else:
            return redirect('/signup')  # If login fails (likely never signed up)
    return render_template("login.html")


@app.route('/community', methods=['GET', 'POST'])
def community():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()

    if request.method == 'POST':
        text = request.form.get('text', '')
        file = request.files.get('image')
        filename = None

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

        conn.execute(
            'INSERT INTO posts (user_id, text, image_path) VALUES (?, ?, ?)',
            (session['user_id'], text, filename)
        )
        conn.commit()

   
    posts = conn.execute('''
        SELECT posts.*, users.username,
               (SELECT COUNT(*) FROM likes WHERE likes.post_id = posts.id) AS like_count,
               EXISTS (
                   SELECT 1 FROM likes
                   WHERE likes.post_id = posts.id AND likes.user_id = ?
               ) AS liked
        FROM posts
        JOIN users ON users.id = posts.user_id
        ORDER BY posts.created_at DESC
    ''', (session['user_id'],)).fetchall()

    conn.close()
    return render_template('community.html', posts=posts) 
	
@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/explore_test1')
def explore():
    return render_template('explore_test1.html')

@app.route('/cultivation_guide')
def guide():
    return render_template('cultivation_guide.html')




@app.route('/like/<int:post_id>')
def like(post_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    liked = conn.execute('SELECT * FROM likes WHERE post_id = ? AND user_id = ?', (post_id, session['user_id'])).fetchone()
    if not liked:
        conn.execute('INSERT INTO likes (post_id, user_id) VALUES (?, ?)', (post_id, session['user_id']))
        conn.commit()
    conn.close()
    return redirect(url_for('community'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route("/chat", methods=["POST"])  # Chatbot route
def chat():
    data = request.get_json()
    user_input = data.get("message", "").strip()

    if not user_input:
        return jsonify({"reply": "Please enter a message."})

    prompt = f"Human: {user_input}\nBot:"
    try:
        result = generator(prompt, max_length=150, pad_token_id=tokenizer.eos_token_id, num_return_sequences=1)
        generated = result[0]['generated_text']
        reply = generated.split("Bot:")[-1].strip()
        return jsonify({"reply": reply})
    except Exception as e:
        print(f"Chatbot error: {e}")
        return jsonify({"reply": "Sorry, I'm having trouble responding right now."})

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)  