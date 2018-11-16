from flask import Flask, render_template, flash, redirect, url_for, session, request, logging, Response
from flaskext.mysql import MySQL
from functools import wraps 
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import pbkdf2_sha256

# emulated camera
from camera import Camera

app = Flask(__name__)

#Config MySQL
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'raspberry'
app.config['MYSQL_DATABASE_DB'] = 'cameraapp'

# Init MYSQL
mysql = MySQL()
mysql.init_app(app)

# Home
@app.route('/')
def home():
  return render_template('home.html')
# About
@app.route('/about')
def about():
  return render_template('about.html')

# Register Form Class
class RegisterForm(Form):
  name = StringField('Name', [validators.Length(min=1, max=50)])
  email = StringField('Email', [validators.Length(min=6, max=50)])
  username = StringField('Username', [validators.Length(min=4, max=25)])
  password = PasswordField('Password', [
    validators.DataRequired(),
    validators.EqualTo('confirm', message='Passwords do not match')
  ])
  confirm = PasswordField('Confirm Password')

# User Register
@app.route('/register', methods=['GET', 'POST'])
def register():
  form = RegisterForm(request.form)
  
  
  if request.method == 'POST' and form.validate():
    name = form.name.data
    email = form.email.data
    username = form.username.data
    password = pbkdf2_sha256.hash(str(form.password.data))
    
    # Create connection and cursor 
    conn = mysql.connect()
    cur = conn.cursor()


    # Execute query
    cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)", (name, email, username, password))

    # Commit to DB
    conn.commit()

    # Close connection
    cur.close()

    flash('You are now registered and can log in', 'success')
    
    return redirect(url_for('login'))
  else:
    error = "it is complete"
  return render_template('register.html', form=form)

# User Login
@app.route('/login', methods = ['GET', 'POST'])
def login():
  if request.method == 'POST':
    # Get form fiels
    username = request.form['username']
    password_candidate = request.form['password']

    # Create cursor
    con = mysql.connect()
    cur = con.cursor()

    # Get user by username
    result = cur.execute("SELECT * FROM users WHERE username = %s", [username])

    if result > 0:
      # Get stored hash
      data = cur.fetchone()
      password = str(data[4])

      # Compare Passwords
      if pbkdf2_sha256.verify(password_candidate, password):
        # Passed
        session['logged_in'] = True
        session['username'] = username

        flash('You are now logged in', 'success')
        return redirect(url_for('dashboard'))
      else:
        error = "Invalid password"
        return render_template('login.html', error=error)
      # Close connection
      cur.close()
    else:
      error = "Username not found"
      return render_template('login.html', error=error)


  return render_template('login.html')

# Check if user logged in 
def is_logged_in(f):
  @wraps(f)
  def wrap(*args, **kwargs):
    if 'logged_in' in session:
      return f(*args, **kwargs)
    else:
      flash('Unauthorized, Please login', 'danger')
      return redirect(url_for('login'))
  return wrap


# Logout
@app.route('/logout')
def logout():
  session.clear()
  flash('You are now logged out', 'success')
  return redirect(url_for('login'))

# Dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
  return render_template('dashboard.html')

# Camera setup
def gen(camera):
    """Video streaming generator function."""
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/video_feed')
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(gen(Camera()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
  app.secret_key = 'secret123'
  app.run(debug = True)
