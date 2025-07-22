from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required, UserMixin
from app import login_manager

auth_bp = Blueprint('auth', __name__)

# --- Admin User Logic ---
class Admin(UserMixin):
  def __init__(self, id):
    self.id = id
  @property
  def is_active(self):
    return True

ADMIN_USER = {'1': {'username': 'admin', 'password': 'admin123'}}

@login_manager.user_loader
def load_user(user_id):
  return Admin(user_id) if user_id in ADMIN_USER else None
# --- End Admin Logic ---

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
  if current_user.is_authenticated:
    return redirect(url_for('main.index'))
  
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
      return redirect(url_for('main.index'))
    else:
      flash('Username atau password salah!', 'danger')
  
  return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
  logout_user()
  flash('Anda telah logout.', 'info')
  return redirect(url_for('auth.login'))