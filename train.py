# train.py

import face_recognition
import os
import pickle
from app import app, db  # Impor app dan db dari file utama Anda
from app.models import Mahasiswa

# Lokasi file model yang akan disimpan
MODEL_PATH = "trained_model.pkl"
# Lokasi folder upload foto mahasiswa
UPLOADS_PATH = os.path.join(app.root_path, 'static/uploads')

def train_model():
    """
    Fungsi untuk membaca data mahasiswa dari DB, membuat face encoding,
    dan menyimpannya ke dalam file pickle.
    """
    # Menggunakan app_context untuk mengakses database di luar route
    with app.app_context():
        print("Memulai proses training model wajah...")
        
        # Ambil semua data mahasiswa dari database
        semua_mahasiswa = Mahasiswa.query.all()

        known_encodings = []
        known_ids = [] # Kita akan menyimpan ID, bukan nama, agar lebih akurat

        if not semua_mahasiswa:
            print("Tidak ada data mahasiswa di database. Training dibatalkan.")
            # Hapus model lama jika ada
            if os.path.exists(MODEL_PATH):
                os.remove(MODEL_PATH)
            return

        for mhs in semua_mahasiswa:
            # Lewati jika foto adalah default
            if mhs.foto == 'default.jpg' or mhs.foto is None:
                continue

            image_path = os.path.join(UPLOADS_PATH, mhs.foto)

            if os.path.exists(image_path):
                try:
                    image = face_recognition.load_image_file(image_path)
                    # Ambil encoding wajah pertama yang ditemukan
                    encoding = face_recognition.face_encodings(image)[0]
                    
                    known_encodings.append(encoding)
                    known_ids.append(mhs.id) # Simpan ID mahasiswa
                    print(f"✅ Wajah untuk {mhs.nama} (ID: {mhs.id}) berhasil di-encode.")

                except (IndexError, IOError) as e:
                    print(f"⚠️ Tidak dapat mendeteksi wajah atau membaca file untuk {mhs.nama} ({image_path}). Dilewati.")
            else:
                print(f"⚠️ File foto tidak ditemukan untuk {mhs.nama} ({image_path}). Dilewati.")

        # Simpan data ke dalam file pickle
        data = {"encodings": known_encodings, "ids": known_ids}
        with open(MODEL_PATH, "wb") as f:
            pickle.dump(data, f)
        
        print(f"✅ Training selesai. {len(known_ids)} wajah berhasil disimpan ke {MODEL_PATH}.")

if __name__ == "__main__":
    # Jalankan fungsi ini langsung dari terminal dengan `python train.py`
    train_model()