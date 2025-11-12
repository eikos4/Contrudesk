from datetime import datetime
from zoneinfo import ZoneInfo
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from . import db  # ✅ ya no genera loop

# Tabla de los mensajes
class ContactMessage(db.Model):
    __tablename__ = "mensajes"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    telefono = db.Column(db.String(20))
    empresa = db.Column(db.String(120))
    mensaje = db.Column(db.Text, nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    leido = db.Column(db.Boolean, default=False)  # 👈 nuevo campo





class Empresa(db.Model):
    __tablename__ = 'empresa'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False, unique=True)
    rut = db.Column(db.String(20), nullable=True)
    direccion = db.Column(db.String(200), nullable=True)
    telefono = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(120), nullable=True)

    # Relación con usuarios (AdminUser)
    usuarios = db.relationship('AdminUser', back_populates='empresa', lazy=True)

    def __repr__(self):
        return f'<Empresa {self.nombre}>'

class AdminUser(UserMixin, db.Model):
    __tablename__ = "admin_users"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)


    empresa_id = db.Column(db.Integer, db.ForeignKey('empresa.id'), nullable=False)
    empresa = db.relationship('Empresa', back_populates='usuarios')


    # Relación con los roles (muchos a muchos)
    roles = db.relationship('Role', secondary='user_roles', backref=db.backref('users', lazy='dynamic'))

    def set_password(self, password):
        """Establece la contraseña hasheada"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verifica la contraseña hasheada"""
        return check_password_hash(self.password_hash, password)

    def has_role(self, role_name):
        """Verifica si el usuario tiene un rol específico"""
        return any(role.name == role_name for role in self.roles)

    # Métodos requeridos por Flask-Login
    @property
    def is_active(self):
        """Retorna si el usuario está activo o no (debe retornar un valor booleano)"""
        return True  # Puedes personalizarlo según lo necesites (Ej: solo activar usuarios con ciertos roles)

    @property
    def is_authenticated(self):
        """Siempre devolverá True si el usuario está autenticado"""
        return True

    @property
    def is_anonymous(self):
        """Siempre devolverá False si el usuario no es anónimo"""
        return False

    def get_id(self):
        """Devuelve el ID del usuario como string (esto es requerido por Flask-Login)"""
        return str(self.id)


# Tabla de roles de usuario
class Role(db.Model):
    __tablename__ = "roles"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)  

    def __repr__(self):
        return f"<Role {self.name}>"

# Tabla intermedia para gestionar la relación muchos a muchos entre usuarios y roles
class UserRoles(db.Model):
    __tablename__ = 'user_roles'

    user_id = db.Column(db.Integer, db.ForeignKey('admin_users.id', ondelete='CASCADE'), primary_key=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True)


class Project(db.Model):
    __tablename__ = 'projects'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    end_date = db.Column(db.DateTime)
    progress = db.Column(db.Integer, default=0)
    status = db.Column(db.String(50), default='activo')  # Ej: activo, suspendido, finalizado
    archived = db.Column(db.Boolean, default=False)  # Indicador de archivo
    admin_comment = db.Column(db.Text)
    # Presupuesto total del proyecto
    total_budget = db.Column(db.Float, default=0.0)

    # Archivo con detalle de presupuesto (opcional)
    budget_file = db.Column(db.String(255))

    # Archivo con cronograma planificado
    schedule_file = db.Column(db.String(255))
    creator_id = db.Column(db.Integer, db.ForeignKey('admin_users.id'), nullable=False)
    creator = db.relationship('AdminUser', backref='created_projects')
    
    def __repr__(self):
        return f"<Project {self.name}>"
    

class ProjectUserRole(db.Model):
    __tablename__ = 'project_user_role'
    
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('admin_users.id', ondelete='CASCADE'), primary_key=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)

    project = db.relationship('Project', backref=db.backref('user_roles', lazy=True))
    user = db.relationship('AdminUser', backref=db.backref('user_roles', lazy=True))
    role = db.relationship('Role')

    def __repr__(self):
        return f"<ProjectUserRole(project_id={self.project_id}, user_id={self.user_id}, role={self.role.name})>"

class ProjectInvitation(db.Model):
    __tablename__ = 'project_invitation'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    token = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(50), default='pending')  # 'pending', 'accepted', 'declined'
    
    project = db.relationship('Project', backref=db.backref('invitations', lazy=True))
    
    def __repr__(self):
        return f"<ProjectInvitation(email={self.email}, project_id={self.project_id}, status={self.status})>"



class ProjectDocument(db.Model):
    __tablename__ = 'project_documents'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('admin_users.id', ondelete='CASCADE'), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)  # Ruta del archivo
    file_name = db.Column(db.String(255), nullable=False)  # Nombre del archivo
    version = db.Column(db.Integer, default=1)  # Versión del documento
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    description = db.Column(db.Text, nullable=True)  # Descripción opcional del documento
    
    project = db.relationship('Project', backref=db.backref('documents', lazy=True))
    user = db.relationship('AdminUser', backref=db.backref('uploaded_documents', lazy=True))

    def __repr__(self):
        return f"<ProjectDocument(project_id={self.project_id}, file_name={self.file_name}, version={self.version})>"
    

class ProjectTask(db.Model):
    __tablename__ = 'project_tasks'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)  # Nombre de la tarea
    description = db.Column(db.Text, nullable=True)  # Descripción de la tarea
    start_date = db.Column(db.DateTime, default=datetime.utcnow)  # Fecha de inicio
    end_date = db.Column(db.DateTime, nullable=True)  # Fecha de finalización
    status = db.Column(db.String(50), default='pendiente')  # Estado de la tarea ('pendiente', 'en progreso', 'completada')
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)  # Relación con el proyecto
    project = db.relationship('Project', backref=db.backref('tasks', lazy=True))  # Relación con el proyecto

    # Relación con el responsable (usuario)
    responsible_user_id = db.Column(db.Integer, db.ForeignKey('admin_users.id'), nullable=True)  # Relación con el responsable
    responsible_user = db.relationship('AdminUser', backref=db.backref('tasks', lazy=True))  # Relación con el usuario responsable

    def __repr__(self):
        return f"<ProjectTask {self.name}, {self.status}>"


class ProjectProgress(db.Model):
    __tablename__ = 'project_progress'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('admin_users.id', ondelete='CASCADE'), nullable=False)
    description = db.Column(db.Text, nullable=False)  # Texto del avance
    date = db.Column(db.DateTime, default=datetime.utcnow)

    project = db.relationship('Project', backref=db.backref('progress_reports', lazy=True))
    user = db.relationship('AdminUser', backref=db.backref('progress_reports', lazy=True))

    def __repr__(self):
        return f"<ProjectProgress project_id={self.project_id}, user_id={self.user_id}, date={self.date}>"



class ProgressPhoto(db.Model):
    __tablename__ = 'progress_photos'

    id = db.Column(db.Integer, primary_key=True)
    progress_id = db.Column(db.Integer, db.ForeignKey('project_progress.id', ondelete='CASCADE'), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)  # ruta en servidor o S3
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)

    progress = db.relationship('ProjectProgress', backref=db.backref('photos', lazy=True))

    def __repr__(self):
        return f"<ProgressPhoto progress_id={self.progress_id}, path={self.file_path}>"
    

class DailyChecklist(db.Model):
    __tablename__ = 'daily_checklists'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    item_text = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True)

    project = db.relationship('Project', backref=db.backref('checklist_items', lazy=True))

    def __repr__(self):
        return f"<DailyChecklist {self.item_text}>"
    

class ChecklistCompletion(db.Model):
    __tablename__ = 'checklist_completion'

    id = db.Column(db.Integer, primary_key=True)
    checklist_id = db.Column(db.Integer, db.ForeignKey('daily_checklists.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('admin_users.id', ondelete='CASCADE'), nullable=False)
    date = db.Column(db.Date, default=datetime.utcnow().date)
    completed = db.Column(db.Boolean, default=False)

    checklist = db.relationship('DailyChecklist', backref=db.backref('completions', lazy=True))
    user = db.relationship('AdminUser', backref=db.backref('checklist_completions', lazy=True))

    def __repr__(self):
        return f"<ChecklistCompletion user_id={self.user_id}, item={self.checklist.item_text}, completed={self.completed}>"


class Comment(db.Model):
    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones
    user_id = db.Column(db.Integer, db.ForeignKey('admin_users.id', ondelete='CASCADE'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('project_tasks.id', ondelete='CASCADE'), nullable=True)

    user = db.relationship('AdminUser', backref=db.backref('comments', lazy=True))
    project = db.relationship('Project', backref=db.backref('comments', lazy=True))
    task = db.relationship('ProjectTask', backref=db.backref('comments', lazy=True))

    def __repr__(self):
        return f"<Comment user={self.user_id} task={self.task_id}>"






class IncidentReport(db.Model):
    __tablename__ = 'incident_reports'

    id = db.Column(db.Integer, primary_key=True)
    
    # 1️⃣ Información del reporte
    report_datetime = db.Column(db.DateTime, default=datetime.utcnow)
    reporter_id = db.Column(db.Integer, db.ForeignKey('admin_users.id', ondelete='CASCADE'), nullable=False)
    reporter_name = db.Column(db.String(120), nullable=False)
    reporter_role = db.Column(db.String(80), nullable=True)
    reporter_email = db.Column(db.String(120), nullable=False)
    reporter_phone = db.Column(db.String(20), nullable=True)

    # 2️⃣ Proyecto y ubicación
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    location = db.Column(db.String(120), nullable=False)

    # 3️⃣ Detalles del incidente
    incident_datetime = db.Column(db.DateTime, nullable=False)
    incident_type = db.Column(db.String(50), nullable=False)  # lesión, cuasi accidente, daño, seguridad
    description = db.Column(db.Text, nullable=False)
    environment_conditions = db.Column(db.Text, nullable=True)  # clima, iluminación, ruido

    # 4️⃣ Personas involucradas
    affected_persons = db.Column(db.Text, nullable=True)  # JSON o texto
    injuries = db.Column(db.Text, nullable=True)
    witnesses = db.Column(db.Text, nullable=True)

    # 5️⃣ Equipos y daños
    equipment_involved = db.Column(db.String(255), nullable=True)
    property_damage = db.Column(db.Text, nullable=True)

    # 6️⃣ Acciones y análisis
    corrective_actions = db.Column(db.Text, nullable=False)
    emergency_services_contacted = db.Column(db.Boolean, default=False)
    emergency_details = db.Column(db.String(255), nullable=True)
    root_cause = db.Column(db.String(255), nullable=True)
    preventive_actions = db.Column(db.Text, nullable=True)

    # 7️⃣ Evidencia
    photo_path = db.Column(db.String(255), nullable=True)
    attachment_path = db.Column(db.String(255), nullable=True)
    evidence_comment = db.Column(db.String(255), nullable=True)

    # 8️⃣ Seguimiento (administrador)
    severity = db.Column(db.String(20), default='baja')  # baja, media, alta, crítica
    status = db.Column(db.String(50), default='abierto')  # abierto, en investigación, cerrado
    responsible_user_id = db.Column(db.Integer, db.ForeignKey('admin_users.id'), nullable=True)
    closure_date = db.Column(db.DateTime, nullable=True)

    # Relaciones
    project = db.relationship('Project', backref=db.backref('incident_reports', lazy=True))
    reporter = db.relationship('AdminUser', foreign_keys=[reporter_id])
    responsible_user = db.relationship('AdminUser', foreign_keys=[responsible_user_id])

    def __repr__(self):
        return f"<IncidentReport id={self.id}, project={self.project_id}, status={self.status}>"


class TechnicalReport(db.Model):
    __tablename__ = 'technical_reports'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text, nullable=True)

    # Identificación
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(ZoneInfo("America/Santiago")))
    inspector = db.Column(db.String(120), nullable=False)
    report_date = db.Column(db.Date, nullable=False)
    period = db.Column(db.String(20), nullable=False)  # Semanal, quincenal, mensual

    # Avance
    general_progress = db.Column(db.Text, nullable=True)
    progress_percentage = db.Column(db.Float, nullable=True)
    next_tasks = db.Column(db.Text, nullable=True)

    # Problemas
    problems_found = db.Column(db.Text, nullable=True)
    actions_taken = db.Column(db.Text, nullable=True)
    evidence_photos = db.Column(db.String(255), nullable=True)  # ruta del archivo

    # Recursos
    weather_conditions = db.Column(db.String(100), nullable=True)
    workers_on_site = db.Column(db.Integer, nullable=True)

    # Resumen
    additional_notes = db.Column(db.Text, nullable=True)

    # Archivo PDF o adicional
    attachment_path = db.Column(db.String(255), nullable=True)

    user_id = db.Column(db.Integer, db.ForeignKey('admin_users.id'), nullable=False)

    project = db.relationship('Project', backref=db.backref('technical_reports', lazy=True))
    user = db.relationship('AdminUser', backref='technical_reports')

    def __repr__(self):
        return f"<TechnicalReport {self.title} - {self.project.name}>"





# Configuración de plantillas y flujos de aprobación
class ConfigTemplate(db.Model):
    __tablename__ = 'config_templates'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    file_path = db.Column(db.String(255), nullable=True)  # ruta a la plantilla (pdf, docx, xlsx)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f"<ConfigTemplate {self.name}>"

class ApprovalFlow(db.Model):
    __tablename__ = 'approval_flows'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    responsible_id = db.Column(db.Integer, db.ForeignKey('admin_users.id'), nullable=False)  # responsable de revisar
    project_task_id = db.Column(db.Integer, db.ForeignKey('project_tasks.id'), nullable=True)
    status = db.Column(db.String(50), default='pendiente')  # pendiente, aprobado, rechazado
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime, nullable=True)

    responsible = db.relationship('AdminUser', backref='approval_flows')
    task = db.relationship('ProjectTask', backref='approval_flows')

    def __repr__(self):
        return f"<ApprovalFlow {self.name} - {self.status}>"

class SystemNotification(db.Model):
    __tablename__ = 'system_notifications'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('admin_users.id'), nullable=True)
    read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('AdminUser', backref='system_notifications')

    def __repr__(self):
        return f"<SystemNotification {self.title}>"