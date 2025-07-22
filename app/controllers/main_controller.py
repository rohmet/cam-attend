from flask import Blueprint, render_template
from flask_login import login_required
from app.models import Mahasiswa, RekapAbsensi
from app import db
from datetime import date, timedelta

main_bp = Blueprint('main', __name__)

# Route index
@main_bp.route('/')
def index():
  return render_template('index.html')

# route dashboard
@main_bp.route('/dashboard')
@login_required
def dashboard():
  # Data kartu statistik
  total_mahasiswa = Mahasiswa.query.count()
  absen_hari_ini = RekapAbsensi.query.filter(db.func.date(RekapAbsensi.timestamp) == date.today()).count()

  # Data untuk daftar absensi terbaru
  absen_terbaru = RekapAbsensi.query.order_by(RekapAbsensi.timestamp.desc()).limit(5).all()
  
  # Data grafik absensi
  chart_labels = []
  chart_data = []
  today = date.today()
  for i in range(6, -1, -1):
    hari = today - timedelta(days=i)
    chart_labels.append(hari.strftime('%a'))
    count = RekapAbsensi.query.filter(db.func.date(RekapAbsensi.timestamp) == hari).count()
    chart_data.append(count)
  
  return render_template(
    'dashboard.html',
    total_mahasiswa=total_mahasiswa,
    absen_hari_ini=absen_hari_ini,
    absen_terbaru=absen_terbaru,
    chart_labels=chart_labels,
    chart_data=chart_data
    )
