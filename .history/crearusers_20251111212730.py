from app import create_app, db
from app.models import AdminUser, Role, Empresa
from werkzeug.security import generate_password_hash

# Lista de empresas (si no existen, se crean)
EMPRESAS = [
    ("Kodesk", "77.777.777-7", "Santiago", "+56 9 9999 9999", "contacto@kodesk.cl"),
    ("ConstruDESK", "66.666.666-6", "Valparaíso", "+56 9 8888 8888", "info@construdesk.cl")
]

# Usuarios iniciales con empresa asignada
USERS = [
    ("admin@kodesk.cl", "leucodeops", "admin", "Kodesk"),
    ("soporte@kodesk.cl", "support123", "admin", "Kodesk"),
    ("editor@kodesk.cl", "editorpass", "editor", "ConstruDESK"),
    ("miembro@kodesk.cl", "miembro123", "miembro", "ConstruDESK"),
    ("lector@kodesk.cl", "lectorpass", "lector", "ConstruDESK"),
    ("invitado@kodesk.cl", "invitadopass", "invitado", "Kodesk"),
]

def create_users():
    """Crea empresas, roles y usuarios iniciales."""

    app = create_app()
    with app.app_context():
        db.create_all()
        print("📁 Base de datos y tablas creadas o verificadas")

        # Crear empresas si no existen
        empresas_dict = {}
        for nombre, rut, direccion, telefono, email in EMPRESAS:
            empresa = Empresa.query.filter_by(nombre=nombre).first()
            if not empresa:
                empresa = Empresa(
                    nombre=nombre,
                    rut=rut,
                    direccion=direccion,
                    telefono=telefono,
                    email=email
                )
                db.session.add(empresa)
                db.session.commit()
                print(f"🏢 Empresa creada: {nombre}")
            empresas_dict[nombre] = empresa

        # Crear roles si no existen
        roles = {}
        for role_name in ["admin", "editor", "miembro", "lector", "invitado"]:
            role = Role.query.filter_by(name=role_name).first()
            if not role:
                role = Role(name=role_name)
                db.session.add(role)
                db.session.commit()
                print(f"🔑 Rol '{role_name}' creado")
            roles[role_name] = role

        # Crear usuarios y asignar empresa
        for email, password, role_name, empresa_nombre in USERS:
            user = AdminUser.query.filter_by(email=email).first()
            if user:
                print(f"⚠️ Usuario {email} ya existe.")
                continue

            empresa = empresas_dict.get(empresa_nombre)
            if not empresa:
                print(f"❌ Empresa '{empresa_nombre}' no encontrada, se omite usuario {email}")
                continue

            user = AdminUser(
                nombre=email.split('@')[0],
                email=email,
                empresa_id=empresa.id
            )
            user.set_password(password)

            if role_name in roles:
                user.roles.append(roles[role_name])

            db.session.add(user)
            print(f"✅ Usuario creado: {email} — Rol: {role_name} — Empresa: {empresa_nombre}")

        db.session.commit()
        print("🎉 Proceso completado con éxito.")

if __name__ == "__main__":
    create_users()
