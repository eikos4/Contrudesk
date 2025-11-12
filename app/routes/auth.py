from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.models import AdminUser, Empresa, ContactMessage
from app import db, login_manager
from app.forms import LoginForm

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


# Función de ayuda para redirigir según rol
def redirect_by_role(user):
    if user.has_role('admin'):
        return redirect(url_for('admin.admin_dashboard'))
    elif user.has_role('editor'):
        return redirect(url_for('editor.editor_dashboard'))
    elif user.has_role('miembro'):
        return redirect(url_for('miembro.miembro_dashboard'))
    elif user.has_role('lector'):
        return redirect(url_for('lector.inicio'))
    elif user.has_role('mensajero'):
        return redirect(url_for('mensajero.dashboard'))
    elif user.has_role('invitado'):
        return redirect(url_for('invitado.dashboard_invitado'))
    else:
        flash("No tienes acceso a ninguna sección", "danger")
        return redirect(url_for('auth.login'))


# Ruta de login
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    # 👇 Si ya está autenticado, no mostrar login
    if current_user.is_authenticated:
        return redirect_by_role(current_user)

    # Cargar empresas en el select (si usas SelectField)
    form.empresa.choices = [(e.id, e.nombre) for e in Empresa.query.order_by(Empresa.nombre).all()]

    if form.validate_on_submit():
        empresa_id = form.empresa.data
        email_or_username = form.identifier.data
        password = form.password.data

        # Buscar empresa seleccionada
        empresa = Empresa.query.get(empresa_id)
        if not empresa:
            flash("Empresa no encontrada.", "danger")
            return render_template('login.html', form=form)

        # Buscar usuario dentro de la empresa
        user = AdminUser.query.filter(
            ((AdminUser.email == email_or_username) | 
             (AdminUser.nombre == email_or_username)) &
            (AdminUser.empresa_id == empresa.id)
        ).first()

        if user and user.check_password(password):
            login_user(user)
            flash(f"Bienvenido, {user.nombre} ({empresa.nombre})", "success")
            return redirect_by_role(user)
        else:
            flash("Credenciales incorrectas o empresa no válida.", "danger")

    return render_template('login.html', form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Sesión cerrada", "info")
    return redirect(url_for("auth.login"))
