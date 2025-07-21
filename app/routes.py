from flask import render_template, redirect, url_for, flash, request, sessions, jsonify
from app import app, db, login_manager
from flask_login import UserMixin, login_user, logout_user, login_required, current_user
from app.models import Mahasiswa
from werkzeug.utils import secure_filename
import os

from app.models import RekapAbsensi
import face_recognition
import numpy as np
import cv2
from datetime import date, datetime

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

# Route mahasiswa
@app.route('/mahasiswa')
@login_required
def mahasiswa():
  semua_mahasiswa = Mahasiswa.query.all()
  return render_template('mahasiswa.html', mahasiswa=semua_mahasiswa)

# Route tambah mahasiswa
@app.route('/mahasiswa/tambah', methods=['GET', 'POST'])
@login_required
def tambah_mahasiswa():
  if request.method == 'POST':
    nim = request.form.get('nim')
    nama = request.form.get('nama')
    foto = request.files.get('foto')
    
    # cek apakah NIM sudah ada
    if Mahasiswa.query.filter_by(nim=nim).first():
      flash('NIM sudah ada!', 'danger')
      return redirect(url_for('tambah_mahasiswa'))
    
    # Simpan foto jika ada
    if foto:
      nama_file_foto = secure_filename(foto.filename)
      path_foto = os.path.join(app.root_path, 'static/uploads', nama_file_foto)
      foto.save(path_foto)
    else:
      # Jika tidak ada foto, gunakan foto default
      nama_file_foto = 'default.jpg'
      
    # Tambahkan mahasiswa baru dan simpan ke db
    mahasiswa_baru = Mahasiswa(nim=nim, nama=nama, foto=nama_file_foto)
    db.session.add(mahasiswa_baru)
    db.session.commit()
    
    flash('Mahasiswa baru berhasil ditambahkan!', 'success')
    return redirect(url_for('mahasiswa'))
  
  return render_template('tambah_mahasiswa.html')

# Route edit mahasiswa
@app.route('/mahasiswa/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_mahasiswa(id):
  mahasiswa = Mahasiswa.query.get_or_404(id)
  if request.method == 'POST':
    mahasiswa.nim = request.form['nim']
    mahasiswa.nama = request.form['nama']
    foto = request.files['foto']
    
    # jika ada foto baru diunggah
    if foto:
      # Hapus foto lama jika bukan default.jpg
      if mahasiswa.foto != 'default.jpg':
        path_foto_lama = os.path.join(app.root_path, 'static/uploads', mahasiswa.foto)
        if os.path.exists(path_foto_lama):
          os.remove(path_foto_lama)
          
      #simpan foto baru
      nama_file_foto = secure_filename(foto.filename)
      path_foto_baru = os.path.join(app.root_path, 'static/uploads', nama_file_foto)
      foto.save(path_foto_baru)
      mahasiswa.foto = nama_file_foto
      
    db.session.commit()
    flash('Data mahasiswa berhasil diperbarui!', 'success')
    return redirect(url_for('mahasiswa'))
  
  return render_template('edit_mahasiswa.html', mahasiswa=mahasiswa)

# Route Hapus Mahasiswa
@app.route('/mahasiswa/hapus/<int:id>', methods=['POST'])
@login_required
def hapus_mahasiswa(id):
  mahasiswa = Mahasiswa.query.get_or_404(id)
  
  # Hapus file foto terkait jika bukan default.jpg
  if mahasiswa.foto != 'default.jpg':
    path_foto = os.path.join(app.root_path, 'static/uploads', mahasiswa.foto)
    if os.path.exists(path_foto):
      os.remove(path_foto)
  
  db.session.delete(mahasiswa)
  db.session.commit()
  flash('Data mahasiswa telah dihapus.', 'success')
  return redirect(url_for('mahasiswa'))

# Route absensi
@app.route('/absen')
@login_required
def absen():
  return render_template('absen.html')

# Route scan wajah
@app.route('/scan_wajah', methods=['POST'])
@login_required
def scan_wajah():
  try:
    # 1. Terima dan baca gambar dari request
    file = request.files['image']
    img_bytes = file.read()
    nparr = np.frombuffer(img_bytes, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    # 2. Load semua data wajah mahasiswa dari database
    semua_mahasiswa = Mahasiswa.query.all()
    known_face_encodings = []
    known_face_data = []

    for mhs in semua_mahasiswa:
      if mhs.foto != 'default.jpg':
        path_foto = os.path.join(app.root_path, 'static/uploads', mhs.foto)
        if os.path.exists(path_foto):
          image = face_recognition.load_image_file(path_foto)
          # Ambil encoding wajah pertama yang ditemukan
          encodings = face_recognition.face_encodings(image)
          if encodings:
            known_face_encodings.append(encodings[0])
            known_face_data.append({'id': mhs.id, 'nama': mhs.nama})

    if not known_face_encodings:
      return jsonify({'status': 'error', 'message': 'Tidak ada data wajah mahasiswa di database.'})

    # 3. Temukan wajah di frame yang diunggah
    face_locations = face_recognition.face_locations(frame)
    unknown_face_encodings = face_recognition.face_encodings(frame, face_locations)
    
    # 4. Bandingkan wajah dan catat absensi
    for unknown_encoding in unknown_face_encodings:
      matches = face_recognition.compare_faces(known_face_encodings, unknown_encoding, tolerance=0.5)
      
      if True in matches:
        first_match_index = matches.index(True)
        data_mahasiswa = known_face_data[first_match_index]
        id_mahasiswa = data_mahasiswa['id']
        nama_mahasiswa = data_mahasiswa['nama']

        # Cek apakah mahasiswa sudah absen hari ini
        today = date.today()
        start_of_day = datetime.combine(today, datetime.min.time())
        end_of_day = datetime.combine(today, datetime.max.time())
        sudah_absen = RekapAbsensi.query.filter_by(mahasiswa_id=id_mahasiswa).filter(RekapAbsensi.timestamp.between(start_of_day, end_of_day)).first()

        if sudah_absen:
          return jsonify({'status': 'already_exists', 'message': 'Sudah absen hari ini.', 'nama': nama_mahasiswa})

        # Jika belum, catat absensi baru
        absen_baru = RekapAbsensi(mahasiswa_id=id_mahasiswa)
        db.session.add(absen_baru)
        db.session.commit()
        
        return jsonify({'status': 'success', 'message': 'Absensi berhasil dicatat.', 'nama': nama_mahasiswa})
  
    return jsonify({'status': 'error', 'message': 'Wajah tidak dikenali.'})

  except Exception as e:
    print(f"Error: {e}")
    return jsonify({'status': 'error', 'message': 'Terjadi kesalahan pada server.'})
  
# Route rekap absen
@app.route('/rekap')
@login_required
def rekap():
  semua_rekap = RekapAbsensi.query.order_by(RekapAbsensi.timestamp.desc()).all()
  return render_template('rekap_absensi.html', semua_rekap=semua_rekap)