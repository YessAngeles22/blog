# -*- coding: utf-8 -*-

import firebase_admin
from flask import Flask, redirect, render_template, request, url_for, session, flash
from firebase_admin import credentials, firestore, auth
from datetime import datetime
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from firebase_admin import storage
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

cred = credentials.Certificate('C:\\bloc\\blog-ec5ff-firebase-adminsdk-dmwpr-fcf0210206.json')
firebase_admin.initialize_app(cred, {'storageBucket': 'blog-ec5ff.appspot.com'})
db = firestore.client()

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        user_ref = db.collection('users').document(username).get()
        if user_ref.exists:
            user_data = user_ref.to_dict()
            if check_password_hash(user_data['password_hash'], password):
                session['username'] = username 
                return redirect(url_for('new_blog'))  # Redirige a la página para crear un nuevo blog
            else:
                flash("Clave incorrecta")
        else:
            flash("Usuario no encontrado")

    return render_template('login.html')

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = request.form['full_name']
        username = request.form['username']
        phone = request.form['phone']
        facebook_profile = request.form['facebook_profile']
        instagram_profile = request.form['instagram_profile']
        password = request.form['password']
        password_hash = generate_password_hash(password)

        profile_image_url = ""

        profile_image = request.files.get('profile_image')
        if profile_image and allowed_file(profile_image.filename):
            filename = secure_filename(profile_image.filename)
            blob = storage.bucket().blob(f'profile_images/{filename}')
            blob.upload_from_file(profile_image)
            blob.make_public()
            profile_image_url = blob.public_url

        user_data = {
            'full_name': full_name,
            'username': username,
            'phone': phone,
            'facebook_profile': facebook_profile,
            'instagram_profile': instagram_profile,
            'profile_image_url': profile_image_url,
            'password_hash': password_hash
        }

        try:
            db.collection('users').document(username).set(user_data)
            session['username'] = username
            return redirect(url_for('home'))
        except Exception as e:
            print(f"Error al registrar: {e}")
            flash("Error al registrar la cuenta")

    return render_template('register.html')

@app.route('/')
def home():
    if 'username' in session:
        posts = get_all_blogs()  # Recupera todos los blogs
        return render_template('index.html', posts=posts)
    else:
        return redirect(url_for('login'))  # Redirige a la pagina de inicio de sesión

@app.route("/logout")
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))  # Redirige al login despues de cerrar sesión

@app.route("/profile/<username>")
def profile(username):
    user_ref = db.collection('users').document(username).get()
    if user_ref.exists:
        user_data = user_ref.to_dict()

        # Obtener las publicaciones del usuario
        posts_ref = db.collection('posts').where('author', '==', username).stream()
        posts = [post.to_dict() for post in posts_ref]

        return render_template('profile.html', 
                               full_name=user_data['full_name'], 
                               profile_image=user_data['profile_image_url'],
                               facebook=user_data.get('facebook_profile'), 
                               instagram=user_data.get('instagram_profile'),
                               posts=posts)  # Pasa las publicaciones al template
    else:
        flash("Perfil no encontrado")
        return redirect(url_for('home'))


@app.route('/new_blog', methods=['GET', 'POST'])
def new_blog():
    if 'username' not in session:
        return redirect(url_for('login'))  # Redirige a login si no está autenticado

    posts = get_all_blogs()  # Recupera todos los blogs para mostrar

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        image = request.files.get('image')
        image_url = ""

        # Manejo de la imagen
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            blob = storage.bucket().blob(f'blog_images/{filename}')
            blob.upload_from_file(image)
            blob.make_public()
            image_url = blob.public_url

        # Guardar el nuevo blog en Firestore
        blog_data = {
            'title': title,
            'content': content,
            'author': session['username'],
            'created_at': datetime.now(),
            'image_url': image_url
        }

        try:
            db.collection('blogs').add(blog_data)  # Guarda el blog en la colección 'blogs'
            flash("Blog publicado exitosamente")  # Mensaje de éxito
        except Exception as e:
            print(f"Error al guardar el blog: {e}")
            flash("Error al publicar el blog")

        return redirect(url_for('new_blog'))  # Redirige a la misma página para mostrar todos los blogs

    return render_template('new_blog.html', posts=posts)  # Muestra todos los blogs en la plantilla



def get_all_blogs():
    blogs_ref = db.collection('blogs').order_by('created_at', direction=firestore.Query.DESCENDING)
    return [blog.to_dict() for blog in blogs_ref.stream()]

if __name__ == '__main__':
    HOST = os.environ.get('SERVER_HOST', 'localhost')
    try:
        PORT = int(os.environ.get('SERVER_PORT', '5555'))
    except ValueError:
        PORT = 5555
    app.run(HOST, PORT)
