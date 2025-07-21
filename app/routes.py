from flask import render_template, redirect, url_for, flash, request
from app import app, db, login_manager
from flask_login import UserMixin, login_user, logout_user, login_required, current_user

# model pengguna sederhana untuk admin
class Admin(UserMixin):
  def __init__(self, id):
    self.id = id
  
  # Kita tidak punya kolom is_active di DB, jadi kita anggap selalu True
  @property
  def is_active(self):
    return True
  
# Data admin statis
ADMIN_USER = {
  '1': {
    'username': 'admin',
    'password': 'password123' # Ganti dengan password yang lebih aman
  }
}

@login_manager.user_loader
def load_user(user_id):
  if user_id in ADMIN_USER:
    return Admin(user_id)
  return None

# Route aplikasi

@app.route('/')
def index():
  return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
  if current_user.is_authenticated:
    return redirect(url_for('index'))
  
  if request.method == 'POST':
    username = request.form.get('username')
    password = request.form.get('password')
    
    user_data = None
    for uid, u in ADMIN_USER.items():
      if u['username'] == username:
        user_data = u
        user_id = uid
        break
      
    if user_data and user_data['password'] == password:
      admin = Admin(id=user_id)
      login_user(admin)
      flash('Login berhasil!', 'success')
      return redirect(url_for('index'))
    else:
      flash('Username atau password salah!', 'danger')
  
  return render_template('login.html')

# route dashboard
@app.route('/dashboard')
@login_required
def dashboard():
  return render_template('dashboard.html')

# Route logout
@app.route('/logout')
@login_required
def logout():
  logout_user()
  flash('Anda telah logout.', 'info')
  return redirect(url_for('login'))