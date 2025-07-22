from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required
from app import app, db
from app.models import Mahasiswa
from werkzeug.utils import secure_filename
import os

mahasiswa_bp = Blueprint('mahasiswa', __name__)

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
    nim = request.form.get('nim')
    nama = request.form.get('nama')
    foto = request.files.get('foto')
    
    # cek apakah NIM sudah ada
    if Mahasiswa.query.filter_by(nim=nim).first():
      flash('NIM sudah ada!', 'danger')
      return redirect(url_for('mahasiswa.tambah_mahasiswa'))
    
    # Simpan foto jika ada
    if foto:
      nama_file_foto = secure_filename(foto.filename)
      path_foto = os.path.join(mahasiswa_bp.root_path, 'static/uploads', nama_file_foto)
      foto.save(path_foto)
    else:
      # Jika tidak ada foto, gunakan foto default
      nama_file_foto = 'default.jpg'
      
    # Tambahkan mahasiswa baru dan simpan ke db
    mahasiswa_baru = Mahasiswa(nim=nim, nama=nama, foto=nama_file_foto)
    db.session.add(mahasiswa_baru)
    db.session.commit()
    
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
    return redirect(url_for('mahasiswa.list_mahasiswa'))
  
  return render_template('edit_mahasiswa.html', mahasiswa=mahasiswa)

# Route Hapus Mahasiswa
@mahasiswa_bp.route('/hapus/<int:id>', methods=['POST'])
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
  return redirect(url_for('mahasiswa.list_mahasiswa'))
