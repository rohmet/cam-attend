from app import db
from datetime import datetime

# model mahasiswa
class Mahasiswa(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  nim = db.Column(db.String(20), unique=True, nullable=False)
  nama = db.Column(db.String(100), nullable=False)
  foto = db.Column(db.String(100), nullable=True)
  
  # relasi ke tabel absensi
  absensi = db.relationship('RekapAbsensi', backref='mahasiswa', lazy=True)
  
  def __repr__(self):
    return f'<Mahasiswa {self.nim} - {self.nama}>'
  
# model rekap absensi
class RekapAbsensi(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  timestamp = db.Column(db.DateTime, nullable=False)
  
  # relasi ke tabel mahasiswa
  mahasiswa_id = db.Column(db.Integer, db.ForeignKey('mahasiswa.id'), nullable=False)
  
  def __repr__(self):
    return f'<RekapAbsensi {self.id}'
