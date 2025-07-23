from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from app import app, db
from app.models import Mahasiswa, RekapAbsensi
import os, cv2, face_recognition
import numpy as np
from datetime import date, datetime

absensi_bp = Blueprint('absensi', __name__)

# Route absensi
@absensi_bp.route('/absen')
@login_required
def absen():
  return render_template('absen.html')

# Route scan wajah
@absensi_bp.route('/scan_wajah', methods=['POST'])
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
        absen_baru = RekapAbsensi(mahasiswa_id=id_mahasiswa, timestamp=datetime.now())
        db.session.add(absen_baru)
        db.session.commit()
        
        return jsonify({'status': 'success', 'message': 'Absensi berhasil dicatat.', 'nama': nama_mahasiswa})
  
    return jsonify({'status': 'error', 'message': 'Wajah tidak dikenali.'})

  except Exception as e:
    print(f"Error: {e}")
    return jsonify({'status': 'error', 'message': 'Terjadi kesalahan pada server.'})

# RUTE BARU: Menyediakan data wajah untuk client-side JS
@absensi_bp.route('/get_known_faces')
@login_required
def get_known_faces():
  try:
    semua_mahasiswa = Mahasiswa.query.all()
    known_faces = []
    
    for mhs in semua_mahasiswa:
      if mhs.foto and mhs.foto != 'default.jpg':
        path_foto = os.path.join(app.root_path, 'static/uploads', mhs.foto)
        if os.path.exists(path_foto):
          image = face_recognition.load_image_file(path_foto)
          encodings = face_recognition.face_encodings(image)
          if encodings:
            encoding_list = encodings[0].tolist()
            known_faces.append({
              "id": mhs.id,
              "nama": mhs.nama,
              "encoding": encoding_list
            })
    return jsonify(known_faces)
  
  except Exception as e:
    print(f"Error saat memuat data wajah: {e}")
    return jsonify({'status': 'error', 'message': 'Gagal memuat data wajah dari server.'}), 500

# RUTE BARU: Menerima hasil scan dari client dan mencatat absensi
@absensi_bp.route('/mark_attendance', methods=['POST'])
@login_required
def mark_attendance():
  data = request.get_json()
  if not data or 'id' not in data:
    return jsonify({'status': 'error', 'message': 'Request tidak valid.'}), 400
  
  id_mahasiswa = data['id']
  mahasiswa = Mahasiswa.query.get(id_mahasiswa)
  
  if not mahasiswa:
        return jsonify({'status': 'error', 'message': 'Mahasiswa tidak ditemukan.'}), 404

  # Cek apakah mahasiswa sudah absen hari ini
  today = date.today()
  start_of_day = datetime.combine(today, datetime.min.time())
  end_of_day = datetime.combine(today, datetime.max.time())
  sudah_absen = RekapAbsensi.query.filter_by(mahasiswa_id=id_mahasiswa).filter(RekapAbsensi.timestamp.between(start_of_day, end_of_day)).first()

  if sudah_absen:
    return jsonify({'status': 'already_exists', 'message': f'{mahasiswa.nama} sudah tercatat absen hari ini.'})

  # Jika belum, catat absensi baru
  try:
    absen_baru = RekapAbsensi(mahasiswa_id=id_mahasiswa, timestamp=datetime.now())
    db.session.add(absen_baru)
    db.session.commit()
    return jsonify({'status': 'success', 'message': f'Absensi untuk {mahasiswa.nama} berhasil dicatat.'})
  except Exception as e:
    db.session.rollback()
    print(f"Error saat menyimpan absensi: {e}")
    return jsonify({'status': 'error', 'message': 'Terjadi kesalahan pada server saat menyimpan data.'}), 500


# Route rekap absen
@absensi_bp.route('/rekap')
@login_required
def rekap():
  semua_rekap = RekapAbsensi.query.order_by(RekapAbsensi.timestamp.desc()).all()
  return render_template('rekap_absensi.html', semua_rekap=semua_rekap)