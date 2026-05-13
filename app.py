from flask import Flask, render_template, request, redirect, url_for, Response, send_file
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import io
import datetime

app = Flask(__name__)

# Configuración de Base de Datos
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///denuncias.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Modelo de la base de datos
class Denuncia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    folio = db.Column(db.String(20), unique=True)
    nombre_denunciante = db.Column(db.String(100))
    descripcion = db.Column(db.Text)
    fecha = db.Column(db.DateTime, default=datetime.datetime.utcnow)

# Crear la base de datos al iniciar
with app.app_context():
    db.create_all()

# --- RUTA PARA EL CIUDADANO (CHATBOT) ---
@app.route('/', methods=['GET', 'POST'])
def index():
    confirmacion = None
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        descripcion = request.form.get('descripcion')
        
        # Generar Folio automático (Ej: D-2026-3605)
        conteo = Denuncia.query.count()
        folio_nuevo = f"D-{datetime.datetime.now().year}-{3600 + conteo + 1}"
        
        nueva_denuncia = Denuncia(
            folio=folio_nuevo,
            nombre_denunciante=nombre,
            descripcion=descripcion
        )
        db.session.add(nueva_denuncia)
        db.session.commit()
        
        confirmacion = folio_nuevo
        
    return render_template('index.html', folio=confirmacion)

# --- PANEL DE ADMINISTRACIÓN ---
@app.route('/admin')
def admin_panel():
    auth = request.authorization
    # Credenciales que tenías en tu imagen
    if not auth or not (auth.username == 'admin' and auth.password == 'Santander2026'):
        return Response('Acceso denegado.', 401, {'WWW-Authenticate': 'Basic realm="Login"'})
    
    # Ordenar por fecha más reciente
    denuncias = Denuncia.query.order_by(Denuncia.fecha.desc()).all()
    return render_template('admin.html', denuncias=denuncias)

# --- DESCARGAR EXCEL ---
@app.route('/descargar_excel')
def descargar_excel():
    denuncias = Denuncia.query.all()
    datos = []
    for d in denuncias:
        datos.append({
            "Folio": d.folio,
            "Fecha": d.fecha.strftime("%Y-%m-%d %H:%M"),
            "Nombre": d.nombre_denunciante,
            "Mensaje": d.descripcion
        })
    
    df = pd.DataFrame(datos)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    
    output.seek(0)
    return send_file(output, download_name="reporte_denuncias.xlsx", as_attachment=True)

if __name__ == '__main__':
    # host='0.0.0.0' es vital para que se vea desde el celular
    app.run(host='0.0.0.0', port=8080, debug=False)