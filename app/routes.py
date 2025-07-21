from flask import render_template, redirect, url_for, flash
from app import app

@app.route('/')
def index():
  return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
  return render_template('login.html')