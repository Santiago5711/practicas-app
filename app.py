from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = "clave_secreta_mejorada_12345"  # Cambia esto por una clave más segura
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Modelos de la base de datos
class Practicante(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    programa = db.Column(db.String(50), nullable=False)
    fecha_ingreso = db.Column(db.String(10), nullable=False)
    estado = db.Column(db.String(20), nullable=False)
    responsable = db.Column(db.String(100), nullable=False)
    usuario = db.Column(db.String(50), unique=True, nullable=False)
    contraseña = db.Column(db.String(100), nullable=False)  # En producción usa hash!

class Avance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    practicante_id = db.Column(db.Integer, db.ForeignKey('practicante.id'), nullable=False)
    descripcion = db.Column(db.String(500), nullable=False)
    fecha = db.Column(db.String(10), nullable=False)
    feedback = db.Column(db.String(500))

# Crear tablas (ejecutar solo una vez)
with app.app_context():
    db.create_all()

# Crear usuario admin si no existe (solo para desarrollo)
with app.app_context():
    if not Practicante.query.filter_by(usuario='admin').first():
        admin = Practicante(
            nombre='Administrador',
            programa='DEV',
            fecha_ingreso='2025-01-01',
            estado='Activo',
            responsable='Sistema',
            usuario='admin',
            contraseña='admin'  # En producción NUNCA hacer esto
        )
        db.session.add(admin)
        db.session.commit()

# Rutas mejoradas
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form.get('usuario')
        contraseña = request.form.get('contraseña')
        
        if not usuario or not contraseña:
            flash('Por favor complete todos los campos', 'error')
            return redirect(url_for('login'))
        
        practicante = Practicante.query.filter_by(usuario=usuario).first()
        
        if practicante and practicante.contraseña == contraseña:  # En producción usa check_password_hash
            session['usuario'] = usuario
            session['es_admin'] = (usuario == 'admin')  # Ejemplo de flag para admin
            flash('¡Bienvenido!', 'success')
            return redirect(url_for('lista_practicantes'))
        else:
            flash('Usuario o contraseña incorrectos', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Has cerrado sesión correctamente', 'info')
    return redirect(url_for('login'))

@app.route('/lista-practicantes')
def lista_practicantes():
    if 'usuario' not in session:
        flash('Debes iniciar sesión primero', 'warning')
        return redirect(url_for('login'))
    
    practicantes = Practicante.query.all()
    return render_template('lista_practicantes.html', 
                         practicantes=practicantes,
                         usuario_actual=session.get('usuario'))

@app.route('/registrar-practicante', methods=['GET', 'POST'])
def registrar_practicante():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
            nuevo_practicante = Practicante(
                nombre=request.form.get('nombre'),
                programa=request.form.get('programa'),
                fecha_ingreso=request.form.get('fecha_ingreso'),
                estado=request.form.get('estado'),
                responsable=request.form.get('responsable'),
                usuario=request.form.get('usuario'),
                contraseña=request.form.get('contraseña')  # En producción usar generate_password_hash
            )
            db.session.add(nuevo_practicante)
            db.session.commit()
            flash('Practicante registrado exitosamente!', 'success')
            return redirect(url_for('lista_practicantes'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al registrar: {str(e)}', 'error')
    
    return render_template('registro_practicante.html')

if __name__ == '__main__':
    app.run(debug=True)