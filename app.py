from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = "clave_secreta_mejorada_12345"
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
    contraseña = db.Column(db.String(100), nullable=False)
    es_responsable = db.Column(db.Boolean, default=False)

class Avance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    practicante_id = db.Column(db.Integer, db.ForeignKey('practicante.id'), nullable=False)
    descripcion = db.Column(db.String(500), nullable=False)
    fecha = db.Column(db.String(10), nullable=False)
    feedback = db.Column(db.String(500))
    practicante = db.relationship('Practicante', backref='avances')

# Crear tablas y usuario admin
with app.app_context():
    db.create_all()
    if not Practicante.query.filter_by(usuario='admin').first():
        admin = Practicante(
            nombre='Administrador',
            programa='DEV',
            fecha_ingreso='2025-01-01',
            estado='Activo',
            responsable='Sistema',
            usuario='admin',
            contraseña='admin',
            es_responsable=True
        )
        db.session.add(admin)
        db.session.commit()

# Decoradores mejorados con wraps
def requiere_login(f):
    @wraps(f)
    def decorador(*args, **kwargs):
        if 'usuario' not in session:
            flash('Debes iniciar sesión primero', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorador

def requiere_responsable(f):
    @wraps(f)
    def decorador(*args, **kwargs):
        if not session.get('es_responsable'):
            flash('No tienes permisos para esta acción', 'error')
            return redirect(url_for('lista_practicantes'))
        return f(*args, **kwargs)
    return decorador

# Rutas de autenticación
@app.route('/', methods=['GET', 'POST'])
def login():
    if 'usuario' in session:
        return redirect(url_for('lista_practicantes'))
    
    if request.method == 'POST':
        usuario = request.form.get('usuario')
        contraseña = request.form.get('contraseña')
        
        if not usuario or not contraseña:
            flash('Complete todos los campos', 'error')
            return redirect(url_for('login'))
        
        practicante = Practicante.query.filter_by(usuario=usuario).first()
        
        if practicante and practicante.contraseña == contraseña:
            session['usuario'] = usuario
            session['es_responsable'] = practicante.es_responsable
            session['practicante_id'] = practicante.id if not practicante.es_responsable else None
            flash(f'Bienvenido {practicante.nombre}', 'success')
            return redirect(url_for('lista_practicantes'))
        else:
            flash('Credenciales incorrectas', 'error')
    
    return render_template('login.html')

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if 'usuario' in session:
        return redirect(url_for('lista_practicantes'))

    if request.method == 'POST':
        usuario = request.form.get('usuario')
        contraseña = request.form.get('contraseña')
        nombre = request.form.get('nombre')
        
        if not all([usuario, contraseña, nombre]):
            flash('Por favor complete todos los campos', 'error')
            return redirect(url_for('registro'))
        
        if Practicante.query.filter_by(usuario=usuario).first():
            flash('Este usuario ya existe', 'error')
            return redirect(url_for('registro'))
        
        try:
            nuevo_practicante = Practicante(
                nombre=nombre,
                programa='Nuevo',
                fecha_ingreso=datetime.now().strftime('%Y-%m-%d'),
                estado='Activo',
                responsable='Por asignar',
                usuario=usuario,
                contraseña=contraseña,
                es_responsable=False
            )
            db.session.add(nuevo_practicante)
            db.session.commit()
            flash('¡Registro exitoso! Por favor inicia sesión', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al registrarse: {str(e)}', 'error')
    
    return render_template('registro.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Sesión cerrada correctamente', 'info')
    return redirect(url_for('login'))

# Rutas de practicantes
@app.route('/practicantes')
@requiere_login
def lista_practicantes():
    query = Practicante.query
    if not session.get('es_responsable'):
        query = query.filter_by(id=session.get('practicante_id'))
    practicantes = query.all()
    return render_template('lista_practicantes.html', practicantes=practicantes)

@app.route('/practicantes/nuevo', methods=['GET', 'POST'])
@requiere_login
@requiere_responsable
def nuevo_practicante():
    if request.method == 'POST':
        try:
            practicante = Practicante(
                nombre=request.form.get('nombre'),
                programa=request.form.get('programa'),
                fecha_ingreso=request.form.get('fecha_ingreso'),
                estado=request.form.get('estado'),
                responsable=request.form.get('responsable'),
                usuario=request.form.get('usuario'),
                contraseña=request.form.get('contraseña'),
                es_responsable=request.form.get('es_responsable') == 'on'
            )
            db.session.add(practicante)
            db.session.commit()
            flash('Practicante registrado exitosamente', 'success')
            return redirect(url_for('lista_practicantes'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al registrar: {str(e)}', 'error')
    
    return render_template('form_practicante.html')

@app.route('/practicantes/editar/<int:id>', methods=['GET', 'POST'])
@requiere_login
@requiere_responsable
def editar_practicante(id):
    practicante = Practicante.query.get_or_404(id)
    if request.method == 'POST':
        try:
            practicante.nombre = request.form.get('nombre')
            practicante.programa = request.form.get('programa')
            practicante.fecha_ingreso = request.form.get('fecha_ingreso')
            practicante.estado = request.form.get('estado')
            practicante.responsable = request.form.get('responsable')
            practicante.es_responsable = request.form.get('es_responsable') == 'on'
            db.session.commit()
            flash('Practicante actualizado correctamente', 'success')
            return redirect(url_for('lista_practicantes'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar: {str(e)}', 'error')
    
    return render_template('form_practicante.html', practicante=practicante)

@app.route('/practicantes/eliminar/<int:id>')
@requiere_login
@requiere_responsable
def eliminar_practicante(id):
    practicante = Practicante.query.get_or_404(id)
    db.session.delete(practicante)
    db.session.commit()
    flash('Practicante eliminado correctamente', 'success')
    return redirect(url_for('lista_practicantes'))

# Rutas de avances
@app.route('/avances')
@requiere_login
def lista_avances():
    if session.get('es_responsable'):
        avances = Avance.query.order_by(Avance.fecha.desc()).all()
    else:
        avances = Avance.query.filter_by(
            practicante_id=session.get('practicante_id')
        ).order_by(Avance.fecha.desc()).all()
    return render_template('lista_avances.html', avances=avances)

@app.route('/avances/nuevo', methods=['GET', 'POST'])
@requiere_login
def nuevo_avance():
    if request.method == 'POST':
        try:
            avance = Avance(
                practicante_id=session.get('practicante_id'),
                descripcion=request.form.get('descripcion'),
                fecha=datetime.now().strftime('%Y-%m-%d')
            )
            db.session.add(avance)
            db.session.commit()
            flash('Avance registrado exitosamente', 'success')
            return redirect(url_for('lista_avances'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al registrar avance: {str(e)}', 'error')
    
    return render_template('form_avance.html')

@app.route('/avances/feedback/<int:id>', methods=['POST'])
@requiere_login
@requiere_responsable
def agregar_feedback(id):
    avance = Avance.query.get_or_404(id)
    avance.feedback = request.form.get('feedback')
    db.session.commit()
    flash('Feedback agregado correctamente', 'success')
    return redirect(url_for('lista_avances'))

# Rutas de reportes
@app.route('/reportes')
@requiere_login
@requiere_responsable
def reportes():
    activos = Practicante.query.filter_by(estado='Activo').count()
    finalizados = Practicante.query.filter_by(estado='Finalizado').count()
    en_espera = Practicante.query.filter_by(estado='En espera').count()
    
    avances_recientes = Avance.query.order_by(Avance.fecha.desc()).limit(5).all()
    
    return render_template('reportes.html',
                        activos=activos,
                        finalizados=finalizados,
                        en_espera=en_espera,
                        avances_recientes=avances_recientes)

if __name__ == '__main__':
    app.run(debug=True)