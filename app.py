from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
import os
import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image

app = Flask(__name__)
app.secret_key = "supersecretkey"

app.config['UPLOAD_FOLDER']='static/uploads'

# Load ML model
model = load_model("model/blood_model.h5")
#model_path=os.path.join(os.getcwdb(),"model","blood_model.h5")
#model=load_model(model_path)
class_names = ['eosinophil', 'lymphocyte', 'monocyte', 'neutrophil']

# Create DB if not exists
def init_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            password TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    return redirect('/login')

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username,password) VALUES (?,?)",
                       (username,password))
        conn.commit()
        conn.close()

        return redirect('/login')
    return render_template("register.html")

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=? AND password=?",
                       (username,password))
        user = cursor.fetchone()
        conn.close()

        if user:
            session['user'] = username
            return redirect('/dashboard')
        else:
            return "Invalid Credentials"

    return render_template("login.html")

@app.route('/dashboard')
def dashboard():
    if 'user' in session:
        return render_template("dashboard.html")
    return redirect('/login')

@app.route('/predict', methods=['POST'])

def predict():
    file = request.files['file']

    # Save directly inside static/uploads
    filepath = "static/uploads/" + file.filename
    file.save(filepath)

    img = image.load_img(filepath, target_size=(224,224))
    img_array = image.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0) / 255.0

    #prediction = model.predict(img_array)
    #predicted_class = class_names[np.argmax(prediction)]
    prediction = model.predict(img_array)

    predicted_index = np.argmax(prediction)
    predicted_class = class_names[predicted_index]

    confidence = float(np.max(prediction)) * 100
    confidence = round(confidence, 2)

    #return render_template("result.html",
                          # prediction=predicted_class,
                           #image_path=filepath)
    return render_template("result.html",
                       prediction=predicted_class,
                       confidence=confidence,
                       image_path=filepath)


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True)