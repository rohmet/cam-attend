# absensi_controller.py (MODIFIKASI)

from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from app import app, db
from app.models import Mahasiswa, RekapAbsensi
import os, cv2, face_recognition, pickle
import numpy as np
from datetime import date, datetime

absensi_bp = Blueprint('absensi', __name__)

# --- BAGIAN BARU: MUAT MODEL SAAT APLIKASI DIMUAT ---
MODEL_PATH = "trained_model.pkl"
known_face_encodings = []
known_face_ids = []

def load_trained_model():
    """Memuat data wajah yang sudah dilatih dari file pickle."""
    global known_face_encodings, known_face_ids
    try:
        with open(MODEL_PATH, "rb") as f:
            data = pickle.load(f)
            known_face_encodings = data["encodings"]
            known_face_ids = data["ids"]
            print(f"Model wajah '{MODEL_PATH}' berhasil dimuat.")
    except FileNotFoundError:
        print(f"PERINGATAN: File model '{MODEL_PATH}' tidak ditemukan. Fitur absensi mungkin tidak berfungsi.")
        print("Jalankan 'python train.py' untuk membuat model.")
    except Exception as e:
        print(f"Error saat memuat model: {e}")

# Panggil fungsi ini saat aplikasi dimulai
load_trained_model()
# ----------------------------------------------------

@absensi_bp.route('/absen')
@login_required
def absen():
  return render_template('absen.html')

# --- Route scan_wajah yang sudah dioptimalkan ---
@absensi_bp.route('/scan_wajah', methods=['POST'])
@login_required
def scan_wajah():
  if not known_face_encodings:
      return jsonify({'status': 'error', 'message': 'Model wajah belum dimuat atau kosong. Silakan jalankan training.'})

  try:
    file = request.files['image']
    img_bytes = file.read()
    nparr = np.frombuffer(img_bytes, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    # Temukan wajah di frame yang diunggah
    face_locations = face_recognition.face_locations(frame)
    unknown_face_encodings = face_recognition.face_encodings(frame, face_locations)
    
    for unknown_encoding in unknown_face_encodings:
      matches = face_recognition.compare_faces(known_face_encodings, unknown_encoding, tolerance=0.5)
      
      if True in matches:
        first_match_index = matches.index(True)
        id_mahasiswa = known_face_ids[first_match_index] # Dapatkan ID mahasiswa
        
        # Ambil data mahasiswa dari DB berdasarkan ID
        mahasiswa = Mahasiswa.query.get(id_mahasiswa)
        if not mahasiswa:
            return jsonify({'status': 'error', 'message': 'Data mahasiswa tidak ditemukan di DB.'})

        # Cek apakah mahasiswa sudah absen hari ini
        today = date.today()
        sudah_absen = RekapAbsensi.query.filter(
            RekapAbsensi.mahasiswa_id == id_mahasiswa,
            db.func.date(RekapAbsensi.timestamp) == today
        ).first()

        if sudah_absen:
          return jsonify({'status': 'already_exists', 'message': f'Sudah absen hari ini.', 'nama': mahasiswa.nama})

        # Catat absensi baru
        absen_baru = RekapAbsensi(mahasiswa_id=id_mahasiswa, timestamp=datetime.now())
        db.session.add(absen_baru)
        db.session.commit()
        
        return jsonify({'status': 'success', 'message': 'Absensi berhasil dicatat.', 'nama': mahasiswa.nama})
  
    return jsonify({'status': 'error', 'message': 'Wajah tidak dikenali.'})

  except Exception as e:
    print(f"Error pada /scan_wajah: {e}")
    return jsonify({'status': 'error', 'message': 'Terjadi kesalahan pada server.'})
  
@absensi_bp.route('/rekap')
@login_required
def rekap():
  semua_rekap = RekapAbsensi.query.order_by(RekapAbsensi.timestamp.desc()).all()
  return render_template('rekap_absensi.html', semua_rekap=semua_rekap)