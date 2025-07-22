from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

app = Flask(__name__)

# kunci rahasia untuk session
app.config['SECRET_KEY'] = 'kunci-rahasia-yang-sangat-sulit-ditebak'

#konfigurasi database
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/cam_attend_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Inisialisasi LoginManager setup
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login' # Arahkan ke route 'login' jika pengguna belum login
login_manager.login_message_category = 'info' # Kategori pesan flash

# Import models
from app import models

# BluePrint dari controllers
from app.controllers.main_controller import main_bp
from app.controllers.auth_controller import auth_bp
from app.controllers.mahasiswa_controller import mahasiswa_bp
from app.controllers.absensi_controller import absensi_bp

app.register_blueprint(main_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(mahasiswa_bp, url_prefix='/mahasiswa')
app.register_blueprint(absensi_bp)