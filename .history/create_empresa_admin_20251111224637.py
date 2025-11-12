from app import create_app, db
from app.models import Empresa, AdminUser, Role

def create_empresa_y_admin():
    """Crea una empresa y su usuario administrador principal."""

    app = create_app()
    with app.app_context():
        db.create_all()

        # ============================
        # 🏢 DATOS DE LA EMPRESA BASE
        # ============================
        empresa_data = {
            "nombre": "Horizon Services Integrales",
            "rut": "66.666.666-6",
            "direccion": "Parral, Chile",
            "telefono": "+56 9 8888 8888",
            "email": "kodesk.ia@gmail.co",
        }

        # Buscar o crear empresa
        empresa = Empresa.query.filter_by(nombre=empresa_data["nombre"]).first()
        if not empresa:
            empresa = Empresa(**empresa_data)
            db.session.add(empresa)
            db.session.commit()
            print(f"🏢 Empresa creada: {empresa.nombre}")
        else:
            print(f"⚠️ La empresa '{empresa.nombre}' ya existe, se usará la existente.")

        # ============================
        # 🔑 CREAR ROL ADMIN (si no existe)
        # ============================
        role = Role.query.filter_by(name="admin").first()
        if not role:
            role = Role(name="admin")
            db.session.add(role)
            db.session.commit()
            print("🔑 Rol 'admin' creado.")

        # ============================
        # 👤 USUARIO ADMINISTRADOR
        # ============================
        admin_email = "admin@construdesk.cl"
        admin_password = "construdesk"  # ⚠️ Cámbialo luego en producción

        admin_user = AdminUser.query.filter_by(email=admin_email).first()
        if not admin_user:
            admin_user = AdminUser(
                nombre="admin",
                email=admin_email,
                empresa_id=empresa.id
            )
            admin_user.set_password(admin_password)
            admin_user.roles.append(role)
            db.session.add(admin_user)
            db.session.commit()
            print(f"✅ Usuario admin creado: {admin_email}")
        else:
            print(f"⚠️ El usuario '{admin_email}' ya existe, se omitió la creación.")

        print("🎉 Empresa y usuario administrador listos para usar.")


if __name__ == "__main__":
    create_empresa_y_admin()
