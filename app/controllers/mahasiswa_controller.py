# mahasiswa_controller.py (MODIFIKASI)

from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required
from app import app, db
from app.models import Mahasiswa
from werkzeug.utils import secure_filename
import os
from train import train_model # <-- TAMBAHKAN IMPORT INI

mahasiswa_bp = Blueprint('mahasiswa', __name__)

# ... (route list_mahasiswa tidak ada perubahan) ...
@mahasiswa_bp.route('/')
@login_required
def list_mahasiswa():
  semua_mahasiswa = Mahasiswa.query.all()
  return render_template('mahasiswa.html', mahasiswa=semua_mahasiswa)

# Route tambah mahasiswa
@mahasiswa_bp.route('/tambah', methods=['GET', 'POST'])
@login_required
def tambah_mahasiswa():
  if request.method == 'POST':
    # ... (logika awal sama) ...
    nim = request.form.get('nim')
    nama = request.form.get('nama')
    foto = request.files.get('foto')
    
    if Mahasiswa.query.filter_by(nim=nim).first():
      flash('NIM sudah ada!', 'danger')
      return redirect(url_for('mahasiswa.tambah_mahasiswa'))
    
    if foto:
      nama_file_foto = secure_filename(foto.filename)
      # Gunakan app.root_path agar konsisten
      path_foto = os.path.join(app.root_path, 'static/uploads', nama_file_foto)
      foto.save(path_foto)
    else:
      nama_file_foto = 'default.jpg'
      
    mahasiswa_baru = Mahasiswa(nim=nim, nama=nama, foto=nama_file_foto)
    db.session.add(mahasiswa_baru)
    db.session.commit()
    
    # --- TAMBAHAN ---
    # Panggil training ulang setelah data baru ditambahkan
    if mahasiswa_baru.foto != 'default.jpg':
        train_model() 
    # ----------------
    
    flash('Mahasiswa baru berhasil ditambahkan!', 'success')
    return redirect(url_for('mahasiswa.list_mahasiswa'))
  
  return render_template('tambah_mahasiswa.html')

# Route edit mahasiswa
@mahasiswa_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_mahasiswa(id):
  mahasiswa = Mahasiswa.query.get_or_404(id)
  if request.method == 'POST':
    mahasiswa.nim = request.form['nim']
    mahasiswa.nama = request.form['nama']
    foto = request.files.get('foto') # Gunakan .get() agar tidak error jika field 'foto' tidak ada
    
    if foto:
      if mahasiswa.foto != 'default.jpg':
        path_foto_lama = os.path.join(app.root_path, 'static/uploads', mahasiswa.foto)
        if os.path.exists(path_foto_lama):
          os.remove(path_foto_lama)
          
      nama_file_foto = secure_filename(foto.filename)
      path_foto_baru = os.path.join(app.root_path, 'static/uploads', nama_file_foto)
      foto.save(path_foto_baru)
      mahasiswa.foto = nama_file_foto
      
    db.session.commit()

    # --- TAMBAHAN ---
    # Panggil training ulang jika foto diubah
    if foto:
        train_model()
    # ----------------
    
    flash('Data mahasiswa berhasil diperbarui!', 'success')
    return redirect(url_for('mahasiswa.list_mahasiswa'))
  
  return render_template('edit_mahasiswa.html', mahasiswa=mahasiswa)

# Route Hapus Mahasiswa
@mahasiswa_bp.route('/hapus/<int:id>', methods=['POST'])
@login_required
def hapus_mahasiswa(id):
  mahasiswa = Mahasiswa.query.get_or_404(id)
  foto_dihapus = mahasiswa.foto != 'default.jpg'
  
  if foto_dihapus:
    path_foto = os.path.join(app.root_path, 'static/uploads', mahasiswa.foto)
    if os.path.exists(path_foto):
      os.remove(path_foto)
  
  db.session.delete(mahasiswa)
  db.session.commit()

  # --- TAMBAHAN ---
  # Panggil training ulang jika mahasiswa yang punya foto dihapus
  if foto_dihapus:
      train_model()
  # ----------------

  flash('Data mahasiswa telah dihapus.', 'success')
  return redirect(url_for('mahasiswa.list_mahasiswa'))