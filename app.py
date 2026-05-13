from flask import Flask, render_template, request, redirect, url_for, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_httpauth import HTTPBasicAuth
import pandas as pd
from datetime import datetime
import os

app = Flask(__name__)

# Configuración de Base de Datos
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///denuncias.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
auth = HTTPBasicAuth()

# Usuario y Contraseña para el Panel Admin
users = {
    "admin": "santander2024"
}

@auth.verify_password
def verify_password(username, password):
    if username in users and users.get(username) == password:
        return username

# Modelo de la Base de Datos
class Denuncia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    folio = db.Column(db.String(20), unique=True)
    nombre = db.Column(db.String(100))
    tipo_tramite = db.Column(db.String(50)) # Nueva columna
    descripcion = db.Column(db.Text)
    fecha = db.Column(db.DateTime, default=datetime.now)

# Crear la base de datos
with app.app_context():
    db.create_all()

@app.route('/', methods=['GET', 'POST'])
def index():
    folio = None
    mensaje_usuario = None
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        tipo = request.form.get('tipo_tramite')
        descripcion = request.form.get('descripcion')
        
        # Generar Folio
        nuevo_folio = f"D-{datetime.now().year}-{1000 + len(Denuncia.query.all()) + 1}"
        
        nueva_denuncia = Denuncia(folio=nuevo_folio, nombre=nombre, tipo_tramite=tipo, descripcion=descripcion)
        db.session.add(nueva_denuncia)
        db.session.commit()
        
        folio = nuevo_folio
        mensaje_usuario = f"Trámite: {tipo} - Enviado por {nombre}"

    return render_template('index.html', folio=folio, mensaje_usuario=mensaje_usuario)

@app.route('/admin')
@auth.login_required
def admin():
    denuncias = Denuncia.query.order_by(Denuncia.fecha.desc()).all()
    return render_template('admin.html', denuncias=denuncias)

@app.route('/descargar')
@auth.login_required
def descargar_excel():
    denuncias = Denuncia.query.all()
    data = [{
        'Folio': d.folio,
        'Fecha': d.fecha.strftime('%Y-%m-%d %H:%M'),
        'Nombre': d.nombre,
        'Tipo de Trámite': d.tipo_tramite,
        'Descripción': d.descripcion
    } for d in denuncias]
    
    df = pd.DataFrame(data)
    file_path = 'reporte_denuncias.xlsx'
    df.to_excel(file_path, index=False)
    return send_file(file_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
