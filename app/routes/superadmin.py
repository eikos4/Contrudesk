from datetime import datetime
import os
from flask import Blueprint, current_app, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import func
from app import db
from app.models import AdminUser, IncidentReport, ProjectTask, Role, Project, TechnicalReport
from werkzeug.utils import secure_filename

superadmin_bp = Blueprint("superadmin", __name__, url_prefix="/superadmin")

# --- Verificación de rol ---
def require_superadmin():
    if not current_user.has_role("superadmin"):
        flash("No tienes permisos de SUPERADMIN.", "danger")
        return redirect(url_for("auth.login"))

# ============================
#  🔹 DASHBOARD SUPERADMIN (FILTRADO POR EMPRESA)
# ============================
@superadmin_bp.route("/")
@login_required
def dashboard():
    require_superadmin()

    # 1. OBTENER EL ID DE LA EMPRESA DEL SUPERADMIN LOGUEADO
    empresa_id = current_user.empresa_id
    
    # 2. DEFINIR LA CONSULTA BASE PARA PROYECTOS (filtrada por empresa)
    # Se une Project con AdminUser (el creador) para filtrar por el empresa_id.
    base_project_query = Project.query.join(
        AdminUser, Project.creator_id == AdminUser.id
    ).filter(
        AdminUser.empresa_id == empresa_id
    )

    # ----- KPIs principales (FILTRADOS) -----
    
    # Proyectos
    total_proyectos = base_project_query.count()
    proyectos_activos = base_project_query.filter(Project.status == 'activo').count()
    proyectos_finalizados = base_project_query.filter(Project.status == 'finalizado').count()
    
    # Atrasados = fecha fin < hoy Y no finalizado (FILTRADO)
    proyectos_atrasados = base_project_query.filter(
        Project.end_date < datetime.utcnow(),
        Project.status != 'finalizado'
    ).count()

    progreso_promedio = base_project_query.with_entities(func.avg(Project.progress)).scalar() or 0

    # Usuarios y Roles
    total_usuarios = AdminUser.query.filter_by(empresa_id=empresa_id).count() # Solo usuarios de esta empresa
    total_roles = Role.query.count() # Los roles se mantienen globales

    # ----- Reportes (FILTRADOS POR PROYECTO DE LA EMPRESA) -----
    
    # Se filtran las tablas relacionadas usando los IDs de los proyectos ya filtrados.
    project_ids = base_project_query.with_entities(Project.id)

    tareas_completadas = ProjectTask.query.filter(
        ProjectTask.project_id.in_(project_ids),
        ProjectTask.status == 'completada'
    ).count()
    
    reportes_tecnicos = TechnicalReport.query.filter(
        TechnicalReport.project_id.in_(project_ids)
    ).count()
    
    incidentes = IncidentReport.query.filter(
        IncidentReport.project_id.in_(project_ids)
    ).count()

    # ----- Listas para gráficos (FILTRADAS) -----
    proyectos_all = base_project_query.with_entities(Project.name, Project.progress).all()

    proyectos_list = [p[0] for p in proyectos_all]       # nombres
    progreso_list = [p[1] for p in proyectos_all]        # porcentajes

    return render_template(
        "superadmin/dashboard.html", # La plantilla no necesita cambios.

        # KPIs
        usuarios=total_usuarios,
        roles=total_roles,
        proyectos=total_proyectos,
        proyectos_activos=proyectos_activos,
        proyectos_finalizados=proyectos_finalizados,
        proyectos_atrasados=proyectos_atrasados,
        progreso_promedio=round(progreso_promedio, 1),

        # Reportes
        tareas_completadas=tareas_completadas,
        reportes_tecnicos=reportes_tecnicos,
        incidentes=incidentes,

        # Gráficos
        proyectos_list=proyectos_list,
        progreso_list=progreso_list
    )


# ===================================================
#  🔹 GESTIÓN GLOBAL (BRANDING + CONFIGURACIÓN)
# ===================================================
@superadmin_bp.route("/configuracion", methods=["GET", "POST"])
@login_required
def configuracion():
    require_superadmin()

    # Obtener registro principal (solo debe haber 1)
    config = SystemConfig.query.first()

    # Si no existe, crear uno base
    if not config:
        config = SystemConfig(
            system_name="ConstruDesk",
            color_primary="#1e3a8a",
            color_secondary="#2563eb",
            enable_reports=True,
            enable_integrations=True,
            maintenance_mode=False
        )
        db.session.add(config)
        db.session.commit()

    if request.method == "POST":

        # Nombre del sistema
        config.system_name = request.form.get("system_name")

        # Colores
        config.color_primary = request.form.get("color_primary")
        config.color_secondary = request.form.get("color_secondary")

        # Opciones booleanas
        config.enable_reports = "enable_reports" in request.form
        config.enable_integrations = "enable_integrations" in request.form
        config.maintenance_mode = "maintenance_mode" in request.form

        # Logo
        file = request.files.get("logo")
        if file and file.filename:
            filename = secure_filename(file.filename)
            upload_path = os.path.join(current_app.root_path, "static", "uploads", "branding")
            os.makedirs(upload_path, exist_ok=True)

            file_path = os.path.join(upload_path, filename)
            file.save(file_path)

            # Guardamos ruta relativa para usar en <img>
            config.logo_path = f"uploads/branding/{filename}"

        db.session.commit()

        flash("Configuración actualizada correctamente.", "success")
        return redirect(url_for("superadmin.configuracion"))

    return render_template("superadmin/configuracion.html", config=config)



@superadmin_bp.route("/branding", methods=["GET", "POST"])
@login_required
def branding():
    require_superadmin()
    if request.method == "POST":
        flash("Branding actualizado correctamente.", "success")
    return render_template("superadmin/branding.html")


@superadmin_bp.route("/dominios", methods=["GET", "POST"])
@login_required
def dominios():
    require_superadmin()
    if request.method == "POST":
        flash("Dominio registrado.", "success")
    return render_template("superadmin/dominios.html")


# ==========================================
#  🔹 GESTIÓN DE USUARIOS
# ==========================================
@superadmin_bp.route("/usuarios")
@login_required
def usuarios():
    require_superadmin()

    empresa_id = current_user.empresa_id

    usuarios = AdminUser.query.filter_by(
        empresa_id=empresa_id,
        is_active=True              # SOLO ACTIVOS
    ).all()

    return render_template("superadmin/usuarios.html", usuarios=usuarios)



@superadmin_bp.route("/usuarios/nuevo", methods=["GET", "POST"])
@login_required
def nuevo_usuario():
    require_superadmin()

    roles = Role.query.all()
    empresa_id = current_user.empresa_id  # Se asigna automáticamente

    if request.method == "POST":
        nombre = request.form.get("nombre")
        email = request.form.get("email")
        rol_id = request.form.get("rol_id")

        # Validaciones simples
        if not nombre or not email or not rol_id:
            flash("Todos los campos son obligatorios.", "danger")
            return redirect(url_for("superadmin.nuevo_usuario"))

        # Comprobar email único
        existing = AdminUser.query.filter_by(email=email).first()
        if existing:
            flash("Ya existe un usuario con ese email.", "danger")
            return redirect(url_for("superadmin.nuevo_usuario"))

        user = AdminUser(
            nombre=nombre,
            email=email,
            empresa_id=empresa_id  # ← Auto-asignado
        )
        user.set_password("123456")  # Contraseña temporal

        rol = Role.query.get(rol_id)
        user.roles.append(rol)

        db.session.add(user)
        db.session.commit()

        flash("Usuario creado correctamente.", "success")
        return redirect(url_for("superadmin.usuarios"))

    return render_template("superadmin/nuevo_usuario.html", roles=roles)


@superadmin_bp.route("/usuarios/<int:user_id>/desactivar", methods=["POST"])
@login_required
def desactivar_usuario(user_id):
    require_superadmin()

    user = AdminUser.query.get_or_404(user_id)
    user.is_active = False
    db.session.commit()

    flash("Usuario desactivado correctamente.", "info")
    return redirect(url_for("superadmin.usuarios"))


@superadmin_bp.route("/usuarios/inactivos")
@login_required
def usuarios_inactivos():
    require_superadmin()

    empresa_id = current_user.empresa_id

    usuarios = AdminUser.query.filter_by(
        empresa_id=empresa_id,
        is_active=False
    ).all()

    return render_template("superadmin/usuarios_inactivos.html", usuarios=usuarios)



@superadmin_bp.route("/usuarios/<int:user_id>/activar", methods=["POST"])
@login_required
def activar_usuario(user_id):
    require_superadmin()

    user = AdminUser.query.get_or_404(user_id)

    user.is_active = True
    db.session.commit()

    flash("Usuario reactivado correctamente.", "success")
    return redirect(url_for("superadmin.usuarios_inactivos"))






# ==========================================
# 🔹 ROLES
# ==========================================
@superadmin_bp.route("/roles")
@login_required
def roles():
    require_superadmin()
    roles = Role.query.all()
    return render_template("superadmin/roles.html", roles=roles)


@superadmin_bp.route("/roles/nuevo", methods=["POST"])
@login_required
def nuevo_rol():
    require_superadmin()
    nombre = request.form.get("nombre")
    db.session.add(Role(name=nombre))
    db.session.commit()

    flash("Rol creado.", "success")
    return redirect(url_for("superadmin.roles"))


# ==========================================
# 🔹 FACTURACIÓN / PLANES
# ==========================================
@superadmin_bp.route("/planes")
@login_required
def planes():
    require_superadmin()
    # más adelante agregas tabla Plan
    return render_template("superadmin/planes.html")


@superadmin_bp.route("/facturas")
@login_required
def facturas():
    require_superadmin()
    return render_template("superadmin/facturas.html")


# ==========================================
# 🔹 INTEGRACIONES
# ==========================================
@superadmin_bp.route("/integraciones", methods=["GET", "POST"])
@login_required
def integraciones():
    require_superadmin()
    if request.method == "POST":
        flash("Integración actualizada.", "success")
    return render_template("superadmin/integraciones.html")


# ==========================================
# 🔹 REPORTES EJECUTIVOS GLOBAL
# ==========================================
@superadmin_bp.route("/reportes")
@login_required
def reportes():
    require_superadmin()

    proyectos = Project.query.all()

    progreso_prom = db.session.query(db.func.avg(Project.progress)).scalar() or 0
    activos = Project.query.filter_by(status="activo").count()
    finalizados = Project.query.filter_by(status="finalizado").count()

    return render_template(
        "superadmin/reportes.html",
        proyectos=proyectos,
        progreso_prom=round(progreso_prom, 1),
        activos=activos,
        finalizados=finalizados
    )
