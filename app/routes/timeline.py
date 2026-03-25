from flask import Blueprint, render_template, abort, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_
from app.models import (
    Project, ProjectTask, ProjectDocument, ProjectProgress, 
    ProgressPhoto, IncidentReport, TechnicalReport, Comment,
    DailyChecklist, ChecklistCompletion, AdminUser, Role
)
from app import db
import json

timeline_bp = Blueprint('timeline', __name__, url_prefix='/timeline')

# =======================================================
#   FUNCIONES AUXILIARES
# =======================================================

def get_project_for_timeline(project_id):
    """Verificar acceso al proyecto según rol del usuario"""
    project = Project.query.get_or_404(project_id)
    
    # Superadmin puede ver todos los proyectos de su empresa
    if current_user.has_role('superadmin'):
        if project.creator.empresa_id != current_user.empresa_id:
            abort(403)
    
    # Admin puede ver proyectos de su empresa
    elif current_user.has_role('admin'):
        if project.creator.empresa_id != current_user.empresa_id:
            abort(403)
    
    # Editor/Miembro/Lector/Invitado solo ven proyectos asignados
    else:
        from app.models import ProjectUserRole
        assignment = ProjectUserRole.query.filter_by(
            project_id=project_id, 
            user_id=current_user.id
        ).first()
        if not assignment:
            abort(403)
    
    return project

def format_timeline_event(event_type, data, user_role):
    """Formatea evento según el rol del usuario"""
    
    base_event = {
        'id': data.get('id'),
        'timestamp': data.get('timestamp'),
        'type': event_type,
        'user': data.get('user'),
        'user_role': user_role
    }
    
    # Personalizar según tipo de evento
    if event_type == 'task_created':
        base_event.update({
            'title': f"Tarea: {data.get('name')}",
            'description': data.get('description'),
            'status': data.get('status'),
            'responsible': data.get('responsible'),
            'priority': 'high' if data.get('status') == 'pendiente' else 'medium',
            'icon': '📝'
        })
    
    elif event_type == 'task_updated':
        base_event.update({
            'title': f"Actualización: {data.get('name')}",
            'description': f"Estado cambiado a: {data.get('status')}",
            'old_status': data.get('old_status'),
            'new_status': data.get('status'),
            'priority': 'medium',
            'icon': '🔄'
        })
    
    elif event_type == 'progress_report':
        base_event.update({
            'title': f"Avance: {data.get('description', '')[:50]}...",
            'description': data.get('description'),
            'progress_percentage': data.get('progress_percentage'),
            'workers': data.get('workers'),
            'weather': data.get('weather'),
            'photos': data.get('photos', []),
            'priority': 'high',
            'icon': '📊'
        })
    
    elif event_type == 'document_uploaded':
        base_event.update({
            'title': f"Documento: {data.get('file_name')}",
            'description': data.get('description'),
            'file_path': data.get('file_path'),
            'file_size': data.get('file_size'),
            'priority': 'medium',
            'icon': '📄'
        })
    
    elif event_type == 'incident_report':
        base_event.update({
            'title': f"Incidente: {data.get('incident_type')}",
            'description': data.get('description'),
            'severity': data.get('severity'),
            'location': data.get('location'),
            'status': data.get('status'),
            'priority': 'high' if data.get('severity') in ['alta', 'critical'] else 'medium',
            'icon': '⚠️'
        })
    
    elif event_type == 'technical_report':
        base_event.update({
            'title': f"Reporte: {data.get('title')}",
            'description': data.get('content', '')[:100] + '...',
            'inspector': data.get('inspector'),
            'period': data.get('period'),
            'progress_percentage': data.get('progress_percentage'),
            'priority': 'high',
            'icon': '📋'
        })
    
    elif event_type == 'comment_added':
        base_event.update({
            'title': f"Comentario en: {data.get('task_name')}",
            'description': data.get('content'),
            'task_id': data.get('task_id'),
            'priority': 'low',
            'icon': '💬'
        })
    
    elif event_type == 'checklist_completed':
        base_event.update({
            'title': f"Checklist: {data.get('items_completed')}/{data.get('items_total')} completados",
            'description': f"Checklist diario completado",
            'completion_rate': data.get('completion_rate'),
            'priority': 'medium',
            'icon': '✅'
        })
    
    return base_event

# =======================================================
#   VISTA PRINCIPAL DE TIMELINE
# =======================================================
@timeline_bp.route('/project/<int:project_id>')
@login_required
def project_timeline(project_id):
    """Timeline completo del proyecto con todos los eventos"""
    
    project = get_project_for_timeline(project_id)
    user_role = current_user.roles[0].name if current_user.roles else 'unknown'
    
    # Obtener fecha límite (últimos 30 días por defecto)
    days_limit = request.args.get('days', 30, type=int)
    start_date = datetime.now() - timedelta(days=days_limit)
    
    # Recolectar todos los eventos del proyecto
    timeline_events = []
    
    # 1. Tareas creadas y actualizadas
    tasks = ProjectTask.query.filter(
        ProjectTask.project_id == project_id,
        ProjectTask.created_at >= start_date
    ).all()
    
    for task in tasks:
        # Evento de creación
        timeline_events.append(format_timeline_event('task_created', {
            'id': f"task_{task.id}",
            'timestamp': task.created_at,
            'name': task.name,
            'description': task.description,
            'status': task.status,
            'responsible': task.responsible_user.nombre if task.responsible_user else 'Sin asignar',
            'user': task.creator.nombre if task.creator else 'Sistema'
        }, user_role))
        
        # Evento de actualización (si es diferente de la creación)
        if task.updated_at and task.updated_at > task.created_at:
            timeline_events.append(format_timeline_event('task_updated', {
                'id': f"task_update_{task.id}",
                'timestamp': task.updated_at,
                'name': task.name,
                'status': task.status,
                'user': task.last_updated_by.nombre if task.last_updated_by else 'Sistema'
            }, user_role))
    
    # 2. Avances de obra
    progresses = ProjectProgress.query.filter(
        ProjectProgress.project_id == project_id,
        ProjectProgress.date >= start_date
    ).all()
    
    for progress in progresses:
        photos = ProgressPhoto.query.filter_by(progress_id=progress.id).all()
        timeline_events.append(format_timeline_event('progress_report', {
            'id': f"progress_{progress.id}",
            'timestamp': progress.date,
            'description': progress.description,
            'progress_percentage': project.progress,
            'workers': getattr(progress, 'workers_on_site', 0),
            'weather': getattr(progress, 'weather_conditions', 'No registrado'),
            'photos': [{'file_path': photo.file_path} for photo in photos],
            'user': progress.user.nombre if progress.user else 'Sistema'
        }, user_role))
    
    # 3. Documentos subidos
    documents = ProjectDocument.query.filter(
        ProjectDocument.project_id == project_id,
        ProjectDocument.upload_date >= start_date
    ).all()
    
    for doc in documents:
        timeline_events.append(format_timeline_event('document_uploaded', {
            'id': f"doc_{doc.id}",
            'timestamp': doc.upload_date,
            'file_name': doc.file_name,
            'description': doc.description,
            'file_path': doc.file_path,
            'file_size': getattr(doc, 'file_size', 0),
            'user': doc.user.nombre if doc.user else 'Sistema'
        }, user_role))
    
    # 4. Incidentes reportados
    incidents = IncidentReport.query.filter(
        IncidentReport.project_id == project_id,
        IncidentReport.report_datetime >= start_date
    ).all()
    
    for incident in incidents:
        timeline_events.append(format_timeline_event('incident_report', {
            'id': f"incident_{incident.id}",
            'timestamp': incident.report_datetime,
            'incident_type': incident.incident_type,
            'description': incident.description,
            'severity': getattr(incident, 'severity', 'media'),
            'location': incident.location,
            'status': incident.status,
            'user': incident.reporter_name
        }, user_role))
    
    # 5. Reportes técnicos
    reports = TechnicalReport.query.filter(
        TechnicalReport.project_id == project_id,
        TechnicalReport.created_at >= start_date
    ).all()
    
    for report in reports:
        timeline_events.append(format_timeline_event('technical_report', {
            'id': f"report_{report.id}",
            'timestamp': report.created_at,
            'title': report.title,
            'content': report.content,
            'inspector': getattr(report, 'inspector', 'No especificado'),
            'period': getattr(report, 'period', 'No especificado'),
            'progress_percentage': getattr(report, 'progress_percentage', 0),
            'user': report.user.nombre if report.user else 'Sistema'
        }, user_role))
    
    # 6. Comentarios en tareas
    comments = Comment.query.filter(
        Comment.project_id == project_id,
        Comment.created_at >= start_date
    ).all()
    
    for comment in comments:
        task = ProjectTask.query.get(comment.task_id) if comment.task_id else None
        timeline_events.append(format_timeline_event('comment_added', {
            'id': f"comment_{comment.id}",
            'timestamp': comment.created_at,
            'content': comment.content,
            'task_name': task.name if task else 'Tarea eliminada',
            'task_id': comment.task_id,
            'user': comment.user.nombre if comment.user else 'Sistema'
        }, user_role))
    
    # 7. Completación de checklist (solo para miembros y superiores)
    if current_user.has_role(['superadmin', 'admin', 'editor', 'miembro']):
        today = datetime.now().date()
        completions = ChecklistCompletion.query.filter(
            ChecklistCompletion.date >= start_date.date()
        ).all()
        
        # Agrupar por día y usuario
        completion_groups = {}
        for completion in completions:
            key = (completion.date, completion.user_id)
            if key not in completion_groups:
                completion_groups[key] = {'completed': 0, 'total': 0}
            completion_groups[key]['completed'] += completion.completed
            completion_groups[key]['total'] += 1
        
        for (date, user_id), counts in completion_groups.items():
            user = AdminUser.query.get(user_id)
            if user:
                timeline_events.append(format_timeline_event('checklist_completed', {
                    'id': f"checklist_{date}_{user_id}",
                    'timestamp': datetime.combine(date, datetime.min.time()),
                    'items_completed': counts['completed'],
                    'items_total': counts['total'],
                    'completion_rate': (counts['completed'] / counts['total'] * 100) if counts['total'] > 0 else 0,
                    'user': user.nombre
                }, user_role))
    
    # Ordenar eventos por timestamp (más recientes primero)
    timeline_events.sort(key=lambda x: x['timestamp'], reverse=True)
    
    # Filtrar eventos según rol
    filtered_events = filter_events_by_role(timeline_events, user_role)
    
    return render_template('timeline/project_timeline.html', 
                        project=project,
                        events=filtered_events,
                        user_role=user_role,
                        days_limit=days_limit)

def filter_events_by_role(events, user_role):
    """Filtra eventos según el rol del usuario"""
    
    if user_role in ['superadmin', 'admin']:
        # Ven todo
        return events
    
    elif user_role == 'editor':
        # Ven todo excepto algunos detalles administrativos
        return events
    
    elif user_role == 'miembro':
        # Solo ven eventos relacionados con sus tareas y asignaciones
        user_tasks = ProjectTask.query.filter_by(responsible_user_id=current_user.id).all()
        user_task_ids = [task.id for task in user_tasks]
        
        filtered = []
        for event in events:
            if event['type'] in ['task_created', 'task_updated', 'comment_added']:
                if event.get('task_id') in user_task_ids:
                    filtered.append(event)
            elif event['type'] in ['progress_report', 'checklist_completed']:
                if event['user'] == current_user.nombre:
                    filtered.append(event)
            else:
                # Documentos, incidentes, reportes técnicos (visibles)
                filtered.append(event)
        
        return filtered
    
    elif user_role == 'lector':
        # Solo ven eventos informativos, no de creación
        return [event for event in events 
                if event['type'] in ['progress_report', 'document_uploaded', 'technical_report']]
    
    elif user_role == 'invitado':
        # Solo ven eventos básicos del proyecto
        return [event for event in events 
                if event['type'] in ['progress_report', 'document_uploaded']]
    
    return events

# =======================================================
#   API PARA FILTRADO DINÁMICO
# =======================================================
@timeline_bp.route('/project/<int:project_id>/filter')
@login_required
def filter_timeline(project_id):
    """API para filtrar timeline por tipo de evento y fechas"""
    
    project = get_project_for_timeline(project_id)
    user_role = current_user.roles[0].name if current_user.roles else 'unknown'
    
    # Obtener parámetros de filtro
    event_types = request.args.getlist('types[]')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Convertir fechas
    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
    if end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
    
    # Construir query base según filtros
    events_query = []
    
    # Aquí irían las queries específicas según los filtros
    # Por simplicidad, retornamos un JSON vacío por ahora
    
    return jsonify({
        'success': True,
        'events': events_query,
        'filters': {
            'event_types': event_types,
            'start_date': start_date.isoformat() if start_date else None,
            'end_date': end_date.isoformat() if end_date else None
        }
    })

# =======================================================
#   EXPORTACIÓN DE TIMELINE
# =======================================================
@timeline_bp.route('/project/<int:project_id>/export')
@login_required
def export_timeline(project_id):
    """Exportar timeline a PDF o Excel"""
    
    project = get_project_for_timeline(project_id)
    export_format = request.args.get('format', 'pdf')
    
    # Obtener eventos (similar a la vista principal)
    days_limit = request.args.get('days', 30, type=int)
    start_date = datetime.now() - timedelta(days=days_limit)
    
    # Generar contenido HTML para exportación
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Timeline - {project.name}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .event {{ margin-bottom: 20px; padding: 15px; border: 1px solid #ddd; border-radius: 8px; }}
            .event-title {{ font-weight: bold; color: #333; }}
            .event-date {{ color: #666; font-size: 0.9em; }}
            .event-description {{ margin-top: 10px; }}
        </style>
    </head>
    <body>
        <h1>Timeline del Proyecto: {project.name}</h1>
        <p>Período: Últimos {days_limit} días</p>
        <hr>
    """
    
    # Obtener eventos reales para exportación
    from app.models import (
        ProjectTask, ProjectDocument, ProjectProgress, ProgressPhoto,
        IncidentReport, TechnicalReport, Comment, DailyChecklist,
        ChecklistCompletion
    )
    
    user_role = current_user.roles[0].name if current_user.roles else 'unknown'
    
    # Tareas
    tasks = ProjectTask.query.filter(
        and_(ProjectTask.project_id == project.id,
             ProjectTask.created_at >= start_date)
    ).all()
    
    for task in tasks:
        html_content += f"""
        <div class="event">
            <div class="event-title">📝 Tarea: {task.name}</div>
            <div class="event-date">{task.created_at.strftime('%d/%m/%Y %H:%M')}</div>
            <div class="event-description">{task.description or 'Sin descripción'}</div>
        </div>
        """
    
    # Avances
    progresses = ProjectProgress.query.filter(
        and_(ProjectProgress.project_id == project.id,
             ProjectProgress.created_at >= start_date)
    ).all()
    
    for progress in progresses:
        html_content += f"""
        <div class="event">
            <div class="event-title">📊 Avance del Proyecto</div>
            <div class="event-date">{progress.created_at.strftime('%d/%m/%Y %H:%M')}</div>
            <div class="event-description">Progreso: {progress.progress_percentage}%</div>
        </div>
        """
    
    html_content += """
        </body>
        </html>
    """
    
    if export_format == 'pdf':
        try:
            import weasyprint
            
            # Generar PDF
            pdf = weasyprint.HTML(string=html_content).write_pdf()
            
            from flask import Response
            response = Response(pdf, mimetype='application/pdf')
            response.headers['Content-Disposition'] = f'attachment; filename=timeline_{project.name}_{datetime.now().strftime("%Y%m%d")}.pdf'
            return response
            
        except ImportError:
            # Si no hay weasyprint, exportar como HTML
            from flask import Response
            response = Response(html_content, mimetype='text/html')
            response.headers['Content-Disposition'] = f'attachment; filename=timeline_{project.name}_{datetime.now().strftime("%Y%m%d")}.html'
            return response
    
    elif export_format == 'excel':
        try:
            import pandas as pd
            from io import BytesIO
            
            # Crear datos para Excel
            events_data = []
            
            for task in tasks:
                events_data.append({
                    'Tipo': 'Tarea',
                    'Título': task.name,
                    'Descripción': task.description or '',
                    'Fecha': task.created_at.strftime('%d/%m/%Y %H:%M'),
                    'Estado': task.status,
                    'Responsable': task.responsible_user.nombre if task.responsible_user else 'No asignado'
                })
            
            for progress in progresses:
                events_data.append({
                    'Tipo': 'Avance',
                    'Título': f'Avance {progress.progress_percentage}%',
                    'Descripción': progress.description or '',
                    'Fecha': progress.created_at.strftime('%d/%m/%Y %H:%M'),
                    'Usuario': progress.user.nombre,
                    'Progreso': f'{progress.progress_percentage}%'
                })
            
            # Crear DataFrame y Excel
            df = pd.DataFrame(events_data)
            output = BytesIO()
            
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name='Timeline', index=False)
                
                # Formatear columnas
                workbook = writer.book
                worksheet = writer.sheets['Timeline']
                
                # Ajustar anchos de columna
                for idx, col in enumerate(df.columns):
                    max_len = max(
                        df[col].astype(str).map(len).max(),
                        len(col)
                    ) + 2
                    worksheet.set_column(idx, idx, max_len)
            
            output.seek(0)
            
            from flask import Response
            response = Response(output.read(), mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response.headers['Content-Disposition'] = f'attachment; filename=timeline_{project.name}_{datetime.now().strftime("%Y%m%d")}.xlsx'
            return response
            
        except ImportError:
            # Si no hay pandas, exportar como CSV
            import csv
            from io import StringIO
            
            output = StringIO()
            writer = csv.writer(output)
            
            # Escribir encabezados
            writer.writerow(['Tipo', 'Título', 'Descripción', 'Fecha', 'Estado/Usuario', 'Progreso'])
            
            # Escribir datos
            for task in tasks:
                writer.writerow([
                    'Tarea',
                    task.name,
                    task.description or '',
                    task.created_at.strftime('%d/%m/%Y %H:%M'),
                    task.status,
                    task.responsible_user.nombre if task.responsible_user else 'No asignado'
                ])
            
            for progress in progresses:
                writer.writerow([
                    'Avance',
                    f'Avance {progress.progress_percentage}%',
                    progress.description or '',
                    progress.created_at.strftime('%d/%m/%Y %H:%M'),
                    progress.user.nombre,
                    f'{progress.progress_percentage}%'
                ])
            
            from flask import Response
            response = Response(output.getvalue(), mimetype='text/csv')
            response.headers['Content-Disposition'] = f'attachment; filename=timeline_{project.name}_{datetime.now().strftime("%Y%m%d")}.csv'
            return response
    return redirect(url_for('timeline.project_timeline', project_id=project_id))
