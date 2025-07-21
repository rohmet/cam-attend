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

# Inisialisasi LoginManager
login_manager = LoginManager(app)
login_manager.login_view = 'login' # Arahkan ke route 'login' jika pengguna belum login
login_manager.login_message_category = 'info' # Kategori pesan flash

# Import routes and models
from app import routes, models