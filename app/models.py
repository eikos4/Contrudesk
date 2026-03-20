from datetime import datetime, date
from zoneinfo import ZoneInfo
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from . import db

# =========================
# 📨 Mensajes de contacto
# =========================
class ContactMessage(db.Model):
    __tablename__ = "mensajes"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    telefono = db.Column(db.String(20))
    empresa = db.Column(db.String(120))
    mensaje = db.Column(db.Text, nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    leido = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"<ContactMessage {self.nombre} ({self.email})>"


# =========================
# 🏢 Modelo de Empresa
# =========================
class Empresa(db.Model):
    __tablename__ = 'empresa'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False, unique=True)
    rut = db.Column(db.String(20))
    direccion = db.Column(db.String(200))
    telefono = db.Column(db.String(20))
    email = db.Column(db.String(120))

    usuarios = db.relationship('AdminUser', back_populates='empresa', lazy=True)

    def __repr__(self):
        return f"<Empresa {self.nombre}>"


# =========================
# 👤 Usuarios administradores
# =========================
class AdminUser(UserMixin, db.Model):
    __tablename__ = "admin_users"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, index=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    empresa_id = db.Column(db.Integer, db.ForeignKey('empresa.id'), nullable=False)
    empresa = db.relationship('Empresa', back_populates='usuarios')

    is_active = db.Column(db.Boolean, default=True)


    roles = db.relationship('Role', secondary='user_roles', backref=db.backref('users', lazy='dynamic'))

    # Métodos de seguridad
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def has_role(self, role_name):
        return any(role.name == role_name for role in self.roles)

    def __repr__(self):
        return f"<AdminUser {self.nombre} ({self.email}) Empresa={self.empresa.nombre}>"

    def get_id(self):
        return str(self.id)


# =========================
# 🔑 Roles de usuario
# =========================
class Role(db.Model):
    __tablename__ = "roles"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)

    def __repr__(self):
        return f"<Role {self.name}>"


# =========================
# 🔄 Relación usuario-rol
# =========================
class UserRoles(db.Model):
    __tablename__ = 'user_roles'

    user_id = db.Column(db.Integer, db.ForeignKey('admin_users.id', ondelete='CASCADE'), primary_key=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True)


# =========================
# 🏗️ Proyectos
# =========================
class Project(db.Model):
    __tablename__ = 'projects'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    end_date = db.Column(db.DateTime)
    progress = db.Column(db.Integer, default=0)
    status = db.Column(db.String(50), default='activo')
    archived = db.Column(db.Boolean, default=False)
    admin_comment = db.Column(db.Text)
    total_budget = db.Column(db.Float, default=0.0)
    budget_file = db.Column(db.String(255))
    schedule_file = db.Column(db.String(255))

    creator_id = db.Column(db.Integer, db.ForeignKey('admin_users.id'), nullable=False)
    creator = db.relationship('AdminUser', backref='created_projects')

    def __repr__(self):
        return f"<Project {self.name}>"


# =========================
# 🧩 Roles dentro del proyecto
# =========================
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


# =========================
# ✉️ Invitaciones a proyectos
# =========================
class ProjectInvitation(db.Model):
    __tablename__ = 'project_invitation'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    token = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(50), default='pending')

    project = db.relationship('Project', backref=db.backref('invitations', lazy=True))

    def __repr__(self):
        return f"<ProjectInvitation(email={self.email}, project_id={self.project_id}, status={self.status})>"


# =========================
# 📂 Documentos de proyecto
# =========================
class ProjectDocument(db.Model):
    __tablename__ = 'project_documents'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('admin_users.id', ondelete='CASCADE'), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    version = db.Column(db.Integer, default=1)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    description = db.Column(db.Text)

    project = db.relationship('Project', backref=db.backref('documents', lazy=True))
    user = db.relationship('AdminUser', backref=db.backref('uploaded_documents', lazy=True))

    def __repr__(self):
        return f"<ProjectDocument(project_id={self.project_id}, file_name={self.file_name}, version={self.version})>"


# =========================
# ✅ Tareas del proyecto
# =========================
class ProjectTask(db.Model):
    __tablename__ = 'project_tasks'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    end_date = db.Column(db.DateTime)
    status = db.Column(db.String(50), default='pendiente')

    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    project = db.relationship('Project', backref=db.backref('tasks', lazy=True))

    responsible_user_id = db.Column(db.Integer, db.ForeignKey('admin_users.id'))
    responsible_user = db.relationship('AdminUser', backref=db.backref('tasks', lazy=True))

    def __repr__(self):
        return f"<ProjectTask {self.name}, {self.status}>"


# =========================
# 📈 Avances del proyecto
# =========================
class ProjectProgress(db.Model):
    __tablename__ = 'project_progress'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('admin_users.id', ondelete='CASCADE'), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

    project = db.relationship('Project', backref=db.backref('progress_reports', lazy=True))
    user = db.relationship('AdminUser', backref=db.backref('progress_reports', lazy=True))

    def __repr__(self):
        return f"<ProjectProgress project_id={self.project_id}, user_id={self.user_id}, date={self.date}>"


# =========================
# 📸 Fotos de progreso
# =========================
class ProgressPhoto(db.Model):
    __tablename__ = 'progress_photos'

    id = db.Column(db.Integer, primary_key=True)
    progress_id = db.Column(db.Integer, db.ForeignKey('project_progress.id', ondelete='CASCADE'), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)

    progress = db.relationship('ProjectProgress', backref=db.backref('photos', lazy=True))

    def __repr__(self):
        return f"<ProgressPhoto progress_id={self.progress_id}, path={self.file_path}>"


# =========================
# 📋 Checklist diario
# =========================
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
    date = db.Column(db.Date, default=date.today)
    completed = db.Column(db.Boolean, default=False)

    checklist = db.relationship('DailyChecklist', backref=db.backref('completions', lazy=True))
    user = db.relationship('AdminUser', backref=db.backref('checklist_completions', lazy=True))

    def __repr__(self):
        return f"<ChecklistCompletion user_id={self.user_id}, item={self.checklist.item_text}, completed={self.completed}>"


# =========================
# 💬 Comentarios
# =========================
class Comment(db.Model):
    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey('admin_users.id', ondelete='CASCADE'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('project_tasks.id', ondelete='CASCADE'))

    user = db.relationship('AdminUser', backref=db.backref('comments', lazy=True))
    project = db.relationship('Project', backref=db.backref('comments', lazy=True))
    task = db.relationship('ProjectTask', backref=db.backref('comments', lazy=True))

    def __repr__(self):
        return f"<Comment user={self.user_id} task={self.task_id}>"


# =========================
# ⚠️ Reportes de incidentes
# =========================
class IncidentReport(db.Model):
    __tablename__ = 'incident_reports'

    id = db.Column(db.Integer, primary_key=True)
    report_datetime = db.Column(db.DateTime, default=datetime.utcnow)
    reporter_id = db.Column(db.Integer, db.ForeignKey('admin_users.id', ondelete='CASCADE'), nullable=False)
    reporter_name = db.Column(db.String(120), nullable=False)
    reporter_role = db.Column(db.String(80))
    reporter_email = db.Column(db.String(120), nullable=False)
    reporter_phone = db.Column(db.String(20))
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    location = db.Column(db.String(120), nullable=False)
    incident_datetime = db.Column(db.DateTime, nullable=False)
    incident_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    environment_conditions = db.Column(db.Text)
    affected_persons = db.Column(db.Text)
    injuries = db.Column(db.Text)
    witnesses = db.Column(db.Text)
    equipment_involved = db.Column(db.String(255))
    property_damage = db.Column(db.Text)
    corrective_actions = db.Column(db.Text, nullable=False)
    emergency_services_contacted = db.Column(db.Boolean, default=False)
    emergency_details = db.Column(db.String(255))
    root_cause = db.Column(db.String(255))
    preventive_actions = db.Column(db.Text)
    photo_path = db.Column(db.String(255))
    attachment_path = db.Column(db.String(255))
    evidence_comment = db.Column(db.String(255))
    severity = db.Column(db.String(20), default='baja')
    status = db.Column(db.String(50), default='abierto')
    responsible_user_id = db.Column(db.Integer, db.ForeignKey('admin_users.id'))
    closure_date = db.Column(db.DateTime)

    project = db.relationship('Project', backref=db.backref('incident_reports', lazy=True))
    reporter = db.relationship('AdminUser', foreign_keys=[reporter_id])
    responsible_user = db.relationship('AdminUser', foreign_keys=[responsible_user_id])

    def __repr__(self):
        return f"<IncidentReport id={self.id}, project={self.project_id}, status={self.status}>"


# =========================
# 🧾 Reportes técnicos
# =========================
class TechnicalReport(db.Model):
    __tablename__ = 'technical_reports'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(ZoneInfo("America/Santiago")))
    inspector = db.Column(db.String(120), nullable=False)
    report_date = db.Column(db.Date)
    period = db.Column(db.String(20), nullable=False)
    general_progress = db.Column(db.Text)
    progress_percentage = db.Column(db.Float)
    next_tasks = db.Column(db.Text)
    problems_found = db.Column(db.Text)
    actions_taken = db.Column(db.Text)
    evidence_photos = db.Column(db.String(255))
    weather_conditions = db.Column(db.String(100))
    workers_on_site = db.Column(db.Integer)
    additional_notes = db.Column(db.Text)
    attachment_path = db.Column(db.String(255))
    user_id = db.Column(db.Integer, db.ForeignKey('admin_users.id'), nullable=False)

    project = db.relationship('Project', backref=db.backref('technical_reports', lazy=True))
    user = db.relationship('AdminUser', backref='technical_reports')

    def __repr__(self):
        return f"<TechnicalReport {self.title} - {self.project.name}>"


# =========================
# ⚙️ Configuración y flujos
# =========================
class ConfigTemplate(db.Model):
    __tablename__ = 'config_templates'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    file_path = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    # 🟢 NUEVA COLUMNA DE ENLACE
    # Asume que tu tabla de empresas se llama 'empresa'
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresa.id'), nullable=False) 
    empresa = db.relationship('Empresa', backref='config_templates')

    def __repr__(self):
        return f"<ConfigTemplate {self.name}>"


class ApprovalFlow(db.Model):
    __tablename__ = 'approval_flows'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    responsible_id = db.Column(db.Integer, db.ForeignKey('admin_users.id'), nullable=False)
    project_task_id = db.Column(db.Integer, db.ForeignKey('project_tasks.id'))
    status = db.Column(db.String(50), default='pendiente')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime)

    responsible = db.relationship('AdminUser', backref='approval_flows')
    task = db.relationship('ProjectTask', backref='approval_flows')

    def __repr__(self):
        return f"<ApprovalFlow {self.name} - {self.status}>"


# =========================
# 🔔 Notificaciones del sistema
# =========================
class SystemNotification(db.Model):
    __tablename__ = 'system_notifications'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('admin_users.id'))
    read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('AdminUser', backref='system_notifications')

    def __repr__(self):
        return f"<SystemNotification {self.title}>"
