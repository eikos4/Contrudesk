from asyncio import Task
from datetime import datetime
import os
from zoneinfo import ZoneInfo

from flask import (
    Blueprint,
    abort,
    app,
    current_app,
    flash,
    redirect,
    render_template,
    send_from_directory,
    url_for,
    request,
)
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

from app import db
from app.forms import NuevoChecklistItemForm, ProgressForm
from app.models import (
    AdminUser,
    ApprovalFlow,
    Comment,
    ConfigTemplate,
    DailyChecklist,
    ProgressPhoto,
    Project,
    ProjectDocument,
    ProjectProgress,
    ProjectTask,
    ProjectUserRole,
    TechnicalReport,
)
import pytz

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif', 'dwg', 'dxf', 'zip'}

editor_bp = Blueprint('editor', __name__, url_prefix='/editor')


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ================================
# 🔧 Helpers de filtrado por empresa
# ================================

def get_base_project_query_for_editor():
    """
    Retorna la consulta base de Proyectos filtrada por empresa del creador del proyecto.
    """
    empresa_id = current_user.empresa_id
    return Project.query.join(
        AdminUser, Project.creator_id == AdminUser.id
    ).filter(
        AdminUser.empresa_id == empresa_id
    )


def get_project_for_editor_or_redirect(project_id, fallback_endpoint='editor.editor_dashboard'):
    """
    Obtiene un proyecto y valida que pertenezca a la empresa del usuario.
    Si no, muestra mensaje y redirige al endpoint indicado.
    """
    project = Project.query.get_or_404(project_id)
    if project.creator.empresa_id != current_user.empresa_id:
        flash("No tienes permiso para acceder a este proyecto.", "danger")
        return redirect(url_for(fallback_endpoint))
    return project


# ================================
# Rutas EDITOR
# ================================

# Ruta de inicio para el editor
@editor_bp.route('/')
@login_required
def editor_dashboard():
    projects = get_base_project_query_for_editor().all()
    return render_template('editor/editor_dashboard.html', projects=projects)


# Ruta para subir un documento
@editor_bp.route('/project/<int:project_id>/upload_document', methods=['GET', 'POST'])
@login_required
def upload_document(project_id):
    project = get_project_for_editor_or_redirect(project_id)
    if not isinstance(project, Project):
        return project  # redirección

    if request.method == 'POST':
        file = request.files.get('file')
        description = request.form.get('description')

        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join('app', 'static', 'uploads', filename)

            # Crear el directorio si no existe
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            file.save(file_path)

            # Crear el nuevo registro en la base de datos para el archivo subido
            document = ProjectDocument(
                project_id=project.id,
                user_id=current_user.id,
                file_path=file_path,
                file_name=filename,
                description=description
            )
            db.session.add(document)
            db.session.commit()

            flash('Documento cargado correctamente.', 'success')
            return redirect(url_for('editor.view_documents', project_id=project.id))

    return render_template('editor/upload_document.html', project=project)


# Ruta para ver los documentos del proyecto
@editor_bp.route('/project/<int:project_id>/documents', methods=['GET', 'POST'])
@login_required
def view_documents(project_id):
    project = get_project_for_editor_or_redirect(project_id)
    if not isinstance(project, Project):
        return project

    documents = ProjectDocument.query.filter_by(project_id=project.id).all()

    if request.method == 'POST':
        file = request.files.get('file')
        description = request.form.get('description')

        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join('uploads', str(project.id), filename)

            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            file.save(file_path)

            document = ProjectDocument(
                project_id=project.id,
                user_id=current_user.id,
                file_path=file_path,
                file_name=filename,
                description=description
            )
            db.session.add(document)
            db.session.commit()

            flash('Documento cargado correctamente.', 'success')
            return redirect(url_for('editor.view_documents', project_id=project.id))

    return render_template('editor/view_documents.html', project=project, documents=documents)


# Ruta para editar el documento
@editor_bp.route('/project/<int:project_id>/document/<int:document_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_document(project_id, document_id):
    project = get_project_for_editor_or_redirect(project_id)
    if not isinstance(project, Project):
        return project

    document = ProjectDocument.query.get_or_404(document_id)

    # Validar que el documento pertenezca al proyecto
    if document.project_id != project.id:
        flash('El documento no pertenece a este proyecto.', 'danger')
        return redirect(url_for('editor.view_documents', project_id=project.id))

    if request.method == 'POST':
        description = request.form.get('description')
        file = request.files.get('file')

        # Actualizar solo la descripción si no se sube un nuevo archivo
        document.description = description

        # Si se sube un nuevo archivo, reemplazar el anterior
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join('app', 'static', 'uploads', filename)

            file.save(file_path)

            document.file_path = file_path
            document.file_name = filename

        # Guardar los cambios en la base de datos
        db.session.commit()

        flash('Documento actualizado correctamente.', 'success')
        return redirect(url_for('editor.view_documents', project_id=project_id))

    return render_template('editor/edit_document.html', document=document, project=project)


# Ruta para descargar el documento
@editor_bp.route('/project/<int:project_id>/documents/<document_id>/download')
@login_required
def download_document(project_id, document_id):
    project = get_project_for_editor_or_redirect(project_id)
    if not isinstance(project, Project):
        return project

    document = ProjectDocument.query.get_or_404(document_id)

    if document.project_id != project.id:
        flash('No tienes permiso para descargar este documento.', 'danger')
        return redirect(url_for('editor.view_documents', project_id=project_id))

    # Recupera el nombre del archivo desde el path guardado
    filename = os.path.basename(document.file_path)

    # Verificar si el archivo realmente existe
    file_path = os.path.join(current_app.root_path, 'static', 'uploads', filename)
    if not os.path.exists(file_path):
        flash('El archivo no existe.', 'danger')
        return redirect(url_for('editor.view_documents', project_id=project_id))

    return send_from_directory(
        os.path.join(current_app.root_path, 'static', 'uploads'), filename, as_attachment=True
    )


# Ruta para ver las tareas del proyecto
@editor_bp.route('/project/<int:project_id>/tasks')
@login_required
def view_tasks(project_id):
    project = get_project_for_editor_or_redirect(project_id)
    if not isinstance(project, Project):
        return project

    # Obtener las tareas del proyecto
    tasks = ProjectTask.query.filter_by(project_id=project.id).all()

    return render_template('editor/view_tasks.html', project=project, tasks=tasks)


# Ruta para crear una nueva tarea
@editor_bp.route('/project/<int:project_id>/create_task', methods=['GET', 'POST'])
@login_required
def create_task(project_id):
    project = get_project_for_editor_or_redirect(project_id)
    if not isinstance(project, Project):
        return project

    # Obtener los usuarios asignados al proyecto
    users_in_project = AdminUser.query.join(ProjectUserRole).filter(ProjectUserRole.project_id == project_id).all()

    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        responsible_user_id = request.form.get('responsible_user')
        status = request.form.get('status', 'pendiente')

        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d') if end_date else None

        # Crear la nueva tarea
        new_task = ProjectTask(
            name=name,
            description=description,
            start_date=start_date,
            end_date=end_date,
            status=status,
            project_id=project.id,
            responsible_user_id=responsible_user_id
        )

        db.session.add(new_task)
        db.session.commit()

        flash('Tarea creada exitosamente', 'success')
        return redirect(url_for('editor.view_tasks', project_id=project.id))

    return render_template('editor/create_task.html', project=project, users_in_project=users_in_project)


# Ruta para editar una tarea existente
@editor_bp.route('/project/<int:project_id>/task/<int:task_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_task(project_id, task_id):
    project = get_project_for_editor_or_redirect(project_id)
    if not isinstance(project, Project):
        return project

    task = ProjectTask.query.get_or_404(task_id)

    # Validar que la tarea pertenezca al proyecto
    if task.project_id != project.id:
        flash('La tarea no pertenece a este proyecto.', 'danger')
        return redirect(url_for('editor.view_tasks', project_id=project.id))

    # Obtener los usuarios asignados al proyecto
    users_in_project = AdminUser.query.join(ProjectUserRole).filter(ProjectUserRole.project_id == project_id).all()

    if request.method == 'POST':
        task.name = request.form.get('name')
        task.description = request.form.get('description')

        task.start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d')
        task.end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d') if request.form.get('end_date') else None

        task.status = request.form.get('status')
        task.responsible_user_id = request.form.get('responsible_user')

        db.session.commit()

        flash('Tarea actualizada correctamente.', 'success')
        return redirect(url_for('editor.view_tasks', project_id=project_id))

    return render_template('editor/edit_task.html', task=task, users_in_project=users_in_project)


# Ruta para eliminar una tarea
@editor_bp.route('/project/<int:project_id>/task/<int:task_id>/delete', methods=['POST'])
@login_required
def delete_task(project_id, task_id):
    project = get_project_for_editor_or_redirect(project_id)
    if not isinstance(project, Project):
        return project

    task = ProjectTask.query.get_or_404(task_id)

    # Verificar que la tarea pertenezca al proyecto
    if task.project_id != project.id:
        flash('La tarea no pertenece a este proyecto.', 'danger')
        return redirect(url_for('editor.view_tasks', project_id=project_id))

    # Eliminar la tarea de la base de datos
    db.session.delete(task)
    db.session.commit()

    flash('Tarea eliminada exitosamente.', 'success')
    return redirect(url_for('editor.view_tasks', project_id=project_id))


# Listar los ítems del checklist de un proyecto
@editor_bp.route('/proyecto/<int:project_id>/checklist')
@login_required
def checklist_items(project_id):
    project = get_project_for_editor_or_redirect(project_id)
    if not isinstance(project, Project):
        return project

    if not current_user.has_role("editor"):
        abort(403)

    items = DailyChecklist.query.filter_by(project_id=project.id).all()
    return render_template("editor/checklist_items.html", project=project, items=items)


# Agregar nuevo ítem al checklist
@editor_bp.route('/proyecto/<int:project_id>/checklist/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_checklist_item(project_id):
    project = get_project_for_editor_or_redirect(project_id)
    if not isinstance(project, Project):
        return project

    if not current_user.has_role("editor"):
        abort(403)

    form = NuevoChecklistItemForm()

    if form.validate_on_submit():
        item = DailyChecklist(
            project_id=project.id,
            item_text=form.item_text.data,
            is_active=True
        )
        db.session.add(item)
        db.session.commit()
        flash("Nuevo ítem agregado", "success")
        return redirect(url_for("editor.checklist_items", project_id=project.id))

    return render_template(
        "editor/nuevo_checklist_item.html",
        project=project,
        form=form
    )


# Desactivar o activar ítem
@editor_bp.route('/proyecto/<int:project_id>/checklist/<int:item_id>/toggle')
@login_required
def toggle_checklist_item(project_id, item_id):
    project = get_project_for_editor_or_redirect(project_id)
    if not isinstance(project, Project):
        return project

    item = DailyChecklist.query.get_or_404(item_id)

    if not current_user.has_role("editor"):
        abort(403)

    if item.project_id != project.id:
        flash("El ítem no pertenece a este proyecto.", "danger")
        return redirect(url_for("editor.checklist_items", project_id=project.id))

    item.is_active = not item.is_active
    db.session.commit()
    flash("Estado del ítem actualizado ", "info")
    return redirect(url_for("editor.checklist_items", project_id=project.id))


# Listar avances de todos los proyectos
@editor_bp.route('/avances/proyectos')
@login_required
def listar_proyectos():
    if not current_user.has_role("editor"):
        abort(403)

    proyectos = get_base_project_query_for_editor().all()
    return render_template("editor/avance_obra.html", proyectos=proyectos)


# Listar avances de un proyecto específico
@editor_bp.route('/avances/proyecto/<int:project_id>')
@login_required
def listar_avances(project_id):
    if not current_user.has_role("editor"):
        abort(403)

    project = get_project_for_editor_or_redirect(project_id)
    if not isinstance(project, Project):
        return project

    avances = ProjectProgress.query.filter_by(project_id=project.id).order_by(ProjectProgress.date.desc()).all()
    return render_template("editor/avances.html", project=project, avances=avances)


# Registrar avance en cualquier proyecto
@editor_bp.route('/avances/proyecto/<int:project_id>/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_avance(project_id):
    if not current_user.has_role("editor"):
        abort(403)

    project = get_project_for_editor_or_redirect(project_id)
    if not isinstance(project, Project):
        return project

    form = ProgressForm()

    if form.validate_on_submit():
        # ⏰ Obtener hora de Chile
        chile_tz = pytz.timezone("America/Santiago")
        ahora_chile = datetime.now(chile_tz)

        # Crear avance
        avance = ProjectProgress(
            project_id=project.id,
            user_id=current_user.id,
            description=form.description.data,
            date=ahora_chile   # 👈 aquí se guarda la hora local
        )
        db.session.add(avance)
        db.session.commit()

        # Guardar fotos
        if form.photos.data:
            upload_folder = os.path.join(current_app.root_path, "static/uploads")
            os.makedirs(upload_folder, exist_ok=True)

            for photo in form.photos.data:
                if photo:
                    filename = secure_filename(photo.filename)
                    file_path = os.path.join(upload_folder, filename)
                    photo.save(file_path)

                    foto = ProgressPhoto(
                        progress_id=avance.id,
                        file_path=f"uploads/{filename}"
                    )
                    db.session.add(foto)

        db.session.commit()
        flash("Avance registrado correctamente ✅", "success")
        return redirect(url_for('editor.listar_avances', project_id=project.id))

    return render_template("editor/nuevo_avance.html", form=form, project=project)


# Ruta para ver y agregar comentarios a una tarea
@editor_bp.route('/project/<int:project_id>/task/<int:task_id>/comments', methods=['GET', 'POST'])
@login_required
def task_comments(project_id, task_id):
    from sqlalchemy import select

    project = get_project_for_editor_or_redirect(project_id)
    if not isinstance(project, Project):
        return project

    task = ProjectTask.query.get_or_404(task_id)

    if task.project_id != project.id:
        flash("La tarea no pertenece a este proyecto.", "danger")
        return redirect(url_for('editor.view_tasks', project_id=project.id))

    if request.method == 'POST':
        content = request.form.get('content')
        if not content or not content.strip():
            flash("El comentario no puede estar vacío.", "warning")
            return redirect(url_for('editor.task_comments', project_id=project.id, task_id=task.id))

        comment = Comment(
            content=content.strip(),
            user_id=current_user.id,
            project_id=project.id,
            task_id=task.id
        )
        db.session.add(comment)
        db.session.commit()

        flash("Comentario agregado correctamente.", "success")
        return redirect(url_for('editor.task_comments', project_id=project.id, task_id=task.id))

    stmt = select(Comment).where(Comment.task_id == task.id).order_by(Comment.created_at.asc())
    comments = db.session.execute(stmt).scalars().all()

    if request.args.get("ajax"):
        return render_template('editor/_comments_partial.html', comments=comments)

    return render_template('editor/task_comments.html', project=project, task=task, comments=comments)


@editor_bp.route('/reportes')
@login_required
def listar_reportes():
    # Solo reportes del usuario y de proyectos de su empresa
    reportes = (
        TechnicalReport.query
        .join(Project, TechnicalReport.project_id == Project.id)
        .join(AdminUser, Project.creator_id == AdminUser.id)
        .filter(
            TechnicalReport.user_id == current_user.id,
            AdminUser.empresa_id == current_user.empresa_id
        )
        .order_by(TechnicalReport.created_at.desc())
        .all()
    )
    return render_template('editor/listar_reportes.html', reportes=reportes)


@editor_bp.route('/reportes/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_reporte():
    proyectos = get_base_project_query_for_editor().all()
    chile_tz = pytz.timezone("America/Santiago")
    ahora_chile = datetime.now(chile_tz)

    if request.method == 'POST':
        # Variables de Identificación
        project_id = request.form.get('project_id')
        report_date = request.form.get('report_date')
        inspector = request.form.get('inspector')
        period = request.form.get('period')

        # Validar proyecto y empresa
        project = Project.query.get_or_404(project_id)
        if project.creator.empresa_id != current_user.empresa_id:
            flash("No puedes crear reportes para proyectos de otra empresa.", "danger")
            return redirect(url_for('editor.listar_reportes'))

        # Variables de Avance
        general_progress = request.form.get('general_progress')
        progress_percentage = request.form.get('progress_percentage')
        next_tasks = request.form.get('next_tasks')

        # Variables de Problemas
        problems_found = request.form.get('problems_found')
        actions_taken = request.form.get('actions_taken')
        evidence_photo = request.files.get('evidence_photos')

        # 🔹 Variables de Recursos
        weather_conditions = request.form.get('weather_conditions')
        workers_on_site = request.form.get('workers_on_site')

        # 🔹 Resumen
        additional_notes = request.form.get('additional_notes')

        # 🔹 Campos existentes
        title = request.form.get('title')
        content = request.form.get('content')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        archivo = request.files.get('attachment')

        # --- Manejo de archivos adjuntos ---
        attachment_path = None
        if archivo and archivo.filename:
            filename = secure_filename(archivo.filename)
            upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'reportes')
            os.makedirs(upload_folder, exist_ok=True)
            path = os.path.join(upload_folder, filename)
            archivo.save(path)
            attachment_path = f'uploads/reportes/{filename}'

        # --- Manejo de fotos de evidencia ---
        evidence_photo_path = None
        if evidence_photo and evidence_photo.filename:
            photo_filename = secure_filename(evidence_photo.filename)
            photo_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'reportes')
            os.makedirs(photo_folder, exist_ok=True)
            photo_path = os.path.join(photo_folder, photo_filename)
            evidence_photo.save(photo_path)
            evidence_photo_path = f'uploads/reportes/{photo_filename}'

        # --- Crear el reporte ---
        reporte = TechnicalReport(
            title=title,
            content=content,
            project_id=project.id,
            user_id=current_user.id,
            created_at=ahora_chile,
            attachment_path=attachment_path,
            inspector=inspector,
            report_date=datetime.strptime(report_date, "%Y-%m-%d") if report_date else None,
            period=period,
            general_progress=general_progress,
            progress_percentage=float(progress_percentage) if progress_percentage else None,
            next_tasks=next_tasks,
            problems_found=problems_found,
            actions_taken=actions_taken,
            evidence_photos=evidence_photo_path,
            weather_conditions=weather_conditions,
            workers_on_site=int(workers_on_site) if workers_on_site else None,
            additional_notes=additional_notes
        )

        db.session.add(reporte)
        db.session.commit()

        flash('✅ Reporte técnico creado exitosamente.', 'success')
        return redirect(url_for('editor.listar_reportes'))

    return render_template('editor/nuevo_reporte.html', proyectos=proyectos)


@editor_bp.route('/reportes/ver/<int:reporte_id>')
@login_required
def ver_reporte(reporte_id):
    reporte = TechnicalReport.query.get_or_404(reporte_id)

    # Seguridad: solo el autor y dentro de su empresa
    if reporte.user_id != current_user.id or reporte.project.creator.empresa_id != current_user.empresa_id:
        flash("No tienes permiso para ver este reporte.", "danger")
        return redirect(url_for('editor.listar_reportes'))

    proyecto = reporte.project
    return render_template('editor/ver_reporte.html', reporte=reporte, proyecto=proyecto)


# Ruta para descargar el archivo adjunto de un reporte
@editor_bp.route('/reportes/descargar/<int:reporte_id>')
@login_required
def descargar_reporte_archivo(reporte_id):
    reporte = TechnicalReport.query.get_or_404(reporte_id)

    # Seguridad: solo el autor y misma empresa
    if reporte.user_id != current_user.id or reporte.project.creator.empresa_id != current_user.empresa_id:
        flash("No tienes permiso para descargar este archivo.", "danger")
        return redirect(url_for('editor.listar_reportes'))

    if not reporte.attachment_path:
        flash('Este reporte no tiene archivo adjunto.', 'warning')
        return redirect(url_for('editor.ver_reporte', reporte_id=reporte.id))

    upload_folder = os.path.join(current_app.root_path, 'static')
    file_path = os.path.join(upload_folder, reporte.attachment_path)

    if not os.path.exists(file_path):
        abort(404, description=f"Archivo no encontrado: {file_path}")

    directory = os.path.dirname(file_path)
    filename = os.path.basename(file_path)

    return send_from_directory(directory, filename, as_attachment=True)


@editor_bp.route('/reportes/editar/<int:reporte_id>', methods=['GET', 'POST'])
@login_required
def editar_reporte(reporte_id):
    reporte = TechnicalReport.query.get_or_404(reporte_id)

    # --- 1) VALIDAR MISMA EMPRESA ---
    if reporte.project.creator.empresa_id != current_user.empresa_id:
        flash("No tienes permiso para editar reportes de otra empresa.", "danger")
        return redirect(url_for('editor.listar_reportes'))

    # --- 2) VALIDAR QUE EL USUARIO ESTÉ ASIGNADO AL PROYECTO (OPCIÓN C) ---
    asignado = ProjectUserRole.query.filter_by(
        project_id=reporte.project_id,
        user_id=current_user.id
    ).first()

    if not asignado:
        flash("No estás asignado a este proyecto. No puedes editar este reporte.", "danger")
        return redirect(url_for('editor.listar_reportes'))

    # --- 3) Obtener lista de proyectos filtrados por empresa ---
    proyectos = get_base_project_query_for_editor().all()

    # --- 4) Procesar formulario ---
    if request.method == 'POST':

        # Proyecto seleccionado
        project_id_str = request.form.get('project_id')

        if project_id_str:
            nuevo_proyecto = Project.query.get_or_404(int(project_id_str))

            # Validar empresa del proyecto destino
            if nuevo_proyecto.creator.empresa_id != current_user.empresa_id:
                flash("Ese proyecto no pertenece a tu empresa.", "danger")
                return redirect(url_for('editor.editar_reporte', reporte_id=reporte.id))

            # Validar asignación del usuario al proyecto destino
            asignado_destino = ProjectUserRole.query.filter_by(
                project_id=nuevo_proyecto.id,
                user_id=current_user.id
            ).first()

            if not asignado_destino:
                flash("No estás asignado al proyecto seleccionado.", "danger")
                return redirect(url_for('editor.editar_reporte', reporte_id=reporte.id))

            reporte.project_id = nuevo_proyecto.id

        # Campos de texto
        reporte.title = request.form.get('title')
        reporte.content = request.form.get('content')
        reporte.inspector = request.form.get('inspector')
        reporte.period = request.form.get('period')
        reporte.general_progress = request.form.get('general_progress')
        reporte.next_tasks = request.form.get('next_tasks')
        reporte.problems_found = request.form.get('problems_found')
        reporte.actions_taken = request.form.get('actions_taken')
        reporte.weather_conditions = request.form.get('weather_conditions')
        reporte.additional_notes = request.form.get('additional_notes')

        # Fecha
        date_str = request.form.get('report_date')
        if date_str:
            try:
                reporte.report_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                flash("⚠️ Fecha inválida. Usa el formato AAAA-MM-DD.", "warning")
                return redirect(url_for('editor.editar_reporte', reporte_id=reporte.id))

        # Números
        progress_str = request.form.get('progress_percentage')
        workers_str = request.form.get('workers_on_site')

        reporte.progress_percentage = float(progress_str) if progress_str else None
        reporte.workers_on_site = int(workers_str) if workers_str else None

        # Imagen evidencia
        evidence_photo = request.files.get('evidence_photos')
        if evidence_photo and evidence_photo.filename:
            filename = secure_filename(evidence_photo.filename)
            upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'fotos')
            os.makedirs(upload_folder, exist_ok=True)
            file_path = os.path.join(upload_folder, filename)
            evidence_photo.save(file_path)
            reporte.evidence_photos = f'uploads/fotos/{filename}'

        # Documento adjunto
        archivo = request.files.get('attachment')
        if archivo and archivo.filename:
            filename = secure_filename(archivo.filename)
            upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'reportes')
            os.makedirs(upload_folder, exist_ok=True)
            file_path = os.path.join(upload_folder, filename)
            archivo.save(file_path)
            reporte.attachment_path = f'uploads/reportes/{filename}'

        # Guardar cambios
        try:
            db.session.commit()
            flash('✅ Reporte técnico actualizado correctamente.', 'success')
            return redirect(url_for('editor.ver_reporte', reporte_id=reporte.id))

        except Exception as e:
            db.session.rollback()
            flash(f"❌ Error al actualizar el reporte: {e}", "danger")

    return render_template('editor/editar_reporte.html', reporte=reporte, proyectos=proyectos)





# Ruta para eliminar un reporte técnico
@editor_bp.route('/reportes/eliminar/<int:reporte_id>', methods=['POST'])
@login_required
def eliminar_reporte(reporte_id):
    reporte = TechnicalReport.query.get_or_404(reporte_id)

    # Seguridad: solo el autor y misma empresa
    if reporte.user_id != current_user.id or reporte.project.creator.empresa_id != current_user.empresa_id:
        flash("No tienes permiso para eliminar este reporte.", "danger")
        return redirect(url_for('editor.listar_reportes'))

    if reporte.attachment_path:
        file_path = os.path.join(current_app.root_path, 'static', reporte.attachment_path)
        if os.path.exists(file_path):
            os.remove(file_path)

    # Borramos el registro de la base de datos
    db.session.delete(reporte)
    db.session.commit()

    flash('Reporte técnico eliminado correctamente.', 'success')
    return redirect(url_for('editor.listar_reportes'))


@editor_bp.route('/plantillas')
@login_required
def ver_plantillas():
    templates = ConfigTemplate.query.filter_by(
        is_active=True,
        empresa_id=current_user.empresa_id
    ).all()
    return render_template('editor/plantillas.html', templates=templates)


@editor_bp.route('/flujos')
@login_required
def flujos_asignados():
    # Solo flujos donde el usuario actual es responsable
    # y de proyectos de su empresa
    flows = (
        ApprovalFlow.query
        .join(ProjectTask, ApprovalFlow.project_task_id == ProjectTask.id)
        .join(Project, ProjectTask.project_id == Project.id)
        .join(AdminUser, Project.creator_id == AdminUser.id)
        .filter(
            ApprovalFlow.responsible_id == current_user.id,
            AdminUser.empresa_id == current_user.empresa_id
        )
        .order_by(ApprovalFlow.created_at.desc())
        .all()
    )
    return render_template('editor/flujos.html', flows=flows)


@editor_bp.route('/flujos/actualizar/<int:flow_id>', methods=['POST'])
@login_required
def actualizar_flujo(flow_id):
    flow = ApprovalFlow.query.get_or_404(flow_id)

    # Solo el responsable (editor asignado) puede modificarlo
    if flow.responsible_id != current_user.id:
        flash("❌ No tienes permiso para modificar este flujo.", "danger")
        return redirect(url_for('editor.flujos_asignados'))

    # Validar empresa del proyecto asociado
    if flow.task and flow.task.project.creator.empresa_id != current_user.empresa_id:
        flash("❌ No puedes modificar flujos de otra empresa.", "danger")
        return redirect(url_for('editor.flujos_asignados'))

    nuevo_estado = request.form.get('estado')
    if nuevo_estado not in ['aprobado', 'rechazado']:
        flash("⚠️ Estado inválido.", "warning")
        return redirect(url_for('editor.flujos_asignados'))

    # Actualizar estado del flujo
    flow.status = nuevo_estado
    flow.reviewed_at = datetime.utcnow()
    db.session.commit()

    # ✅ Crear notificación para el administrador o creador del proyecto
    from app.models import SystemNotification

    # Definir destinatario: el creador del proyecto
    admin_id = flow.task.project.creator_id if flow.task and flow.task.project else None

    if admin_id:
        titulo = f"Flujo '{flow.name}' {nuevo_estado.capitalize()}"
        mensaje = (
            f"El editor {current_user.nombre} ha marcado como "
            f"'{nuevo_estado}' la tarea '{flow.task.name}' del proyecto '{flow.task.project.name}'."
        )

        noti = SystemNotification(
            title=titulo,
            message=mensaje,
            user_id=admin_id
        )
        db.session.add(noti)
        db.session.commit()

    flash(f"✅ Flujo '{flow.name}' marcado como {nuevo_estado}.", "success")
    return redirect(url_for('editor.flujos_asignados'))
