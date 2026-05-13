from flask import Flask, render_template, request, redirect, url_for, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_httpauth import HTTPBasicAuth
import pandas as pd
from datetime import datetime
import os

app = Flask(__name__)

# Configuración de la Base de Datos
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///denuncias.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
auth = HTTPBasicAuth()

# Configuración de Seguridad para el Panel
users = {
    "admin": "santander2024"
}

@auth.verify_password
def verify_password(username, password):
    if username in users and users[username] == password:
        return username

# Modelo de la Base de Datos
class Denuncia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    folio = db.Column(db.String(20), unique=True, nullable=False)
    tramite = db.Column(db.String(50), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

    def get_color(self):
        # Lógica de colores para la Subprocuraduría
        colores = {
            "Reporte de Maltrato Infantil": "danger",  # Rojo
            "Asesoría Jurídica": "primary",           # Azul
            "Reporte de Omisión de Cuidados": "warning", # Amarillo
            "Otros": "secondary"                      # Gris
        }
        return colores.get(self.tramite, "light")

# RUTAS
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        tramite = request.form.get('tramite')
        descripcion = request.form.get('descripcion')
        
        # Generar Folio Único (Ej: DIF-20240513-123)
        nuevo_id = Denuncia.query.count() + 1
        folio = f"DIF-{datetime.now().strftime('%Y%m%d')}-{nuevo_id}"
        
        nueva_denuncia = Denuncia(folio=folio, tramite=tramite, descripcion=descripcion)
        db.session.add(nueva_denuncia)
        db.session.commit()
        
        return render_template('index.html', folio=folio, enviado=True)
    
    return render_template('index.html', enviado=False)

@app.route('/admin')
@auth.login_required
def admin():
    denuncias = Denuncia.query.order_by(Denuncia.fecha.desc()).all()
    return render_template('admin.html', denuncias=denuncias)

@app.route('/download_excel')
@auth.login_required
def download_excel():
    denuncias = Denuncia.query.all()
    data = [{
        'Folio': d.folio, 
        'Trámite': d.tramite, 
        'Descripción': d.descripcion, 
        'Fecha': d.fecha.strftime('%Y-%m-%d %H:%M')
    } for d in denuncias]
    
    df = pd.DataFrame(data)
    excel_path = 'reporte_denuncias.xlsx'
    df.to_excel(excel_path, index=False)
    
    return send_file(excel_path, as_attachment=True)

# CONFIGURACIÓN PARA RAILWAY (CRÍTICO)
if __name__ == '__main__':
    with app.app_context():
        # Crea la base de datos y las tablas si no existen
        db.create_all()
    
    # Railway asigna un puerto dinámico, debemos tomarlo de la variable de entorno
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
