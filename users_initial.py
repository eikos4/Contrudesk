from datetime import datetime
from app import create_app, db
from app.models import Empresa, AdminUser, Role
from typing import List, Dict

# ====================================================================
# 📄 DATOS BASE PARA LA INICIALIZACIÓN
# ====================================================================

# Roles estándar que se crearán para CADA empresa.
ROLES_ESTANDAR: List[str] = [
    "superadmin",
    "admin",
    "editor",
    "miembro",
    "lector",
    "invitado"
]

# Datos de las 2 empresas a crear.
EMPRESAS_DATA: List[Dict[str, str]] = [
    {
        "nombre": "Horizon Services Integrales",
        "rut": "66.666.666-6",
        "direccion": "Parral, Chile",
        "telefono": "+56 9 8888 8888",
        "email": "serviciointegraleshorizon@gmail.com",
        "admin_email": "admin_horizon@test.cl", # 🆕 Credencial de Admin de Prueba
        "admin_nombre": "Admin Horizon"         # 🆕 Nombre de Admin de Prueba
    },
    {
        "nombre": "Construdesk ventas",
        "rut": "77.777.777-7",
        "direccion": "Santiago, Chile",
        "telefono": "+56 9 9999 9999",
        "email": "contacto@constructorabeta.cl",
        "admin_email": "admin_beta@test.cl",    # 🆕 Credencial de Admin de Prueba
        "admin_nombre": "Admin Beta"            # 🆕 Nombre de Admin de Prueba
    }
]

# Contraseña de prueba unificada.
PASSWORD_BASE = "admin123G" # ⚠️ CAMBIAR EN PRODUCCIÓN

# ====================================================================
# 🛠️ FUNCIONES AUXILIARES
# ====================================================================

def create_or_get_role(role_name: str) -> Role:
    """Busca un rol por nombre; si no existe, lo crea."""
    role = Role.query.filter_by(name=role_name).first()
    if not role:
        role = Role(name=role_name)
        db.session.add(role)
        db.session.commit()
        print(f"  🔑 Rol '{role_name}' creado.")
    return role

def create_or_get_empresa(data: Dict[str, str]) -> Empresa:
    """Busca una empresa por nombre; si no existe, la crea."""
    empresa = Empresa.query.filter_by(nombre=data["nombre"]).first()
    if not empresa:
        # Extraemos solo las claves del modelo Empresa para evitar errores
        empresa_keys = ["nombre", "rut", "direccion", "telefono", "email"]
        empresa_data = {k: data[k] for k in empresa_keys}
        
        empresa = Empresa(**empresa_data)
        db.session.add(empresa)
        db.session.commit()
        print(f"🏢 Empresa creada: {empresa.nombre}")
    else:
        print(f"⚠️ La empresa '{empresa.nombre}' ya existe, se usará la existente.")
    return empresa


def create_admin_user_for_empresa(empresa: Empresa, data: Dict[str, str]):
    """Crea un usuario con rol 'admin' para la empresa dada."""
    
    admin_email = data["admin_email"]
    admin_nombre = data["admin_nombre"]

    # 1. Buscar el rol 'admin'
    admin_role = create_or_get_role("admin")
    
    # 2. Buscar si el usuario ya existe
    admin_user = AdminUser.query.filter_by(email=admin_email).first()
    
    if not admin_user:
        admin_user = AdminUser(
            nombre=admin_nombre,
            email=admin_email,
            empresa_id=empresa.id
        )
        admin_user.set_password(PASSWORD_BASE)
        admin_user.roles.append(admin_role)
        
        db.session.add(admin_user)
        db.session.commit()
        print(f"✅ Usuario Admin Creado para {empresa.nombre}: {admin_email} (Pass: {PASSWORD_BASE})")
    else:
        print(f"⚠️ El usuario Admin '{admin_email}' ya existe, se omitió la creación.")


# ====================================================================
# 🚀 FUNCIÓN PRINCIPAL DE SEEDING
# ====================================================================

def seed_database():
    """Ejecuta toda la lógica de inicialización de empresas, roles y usuarios admin."""

    app = create_app()
    with app.app_context():
        db.create_all()
        print("\n--- INICIALIZACIÓN DE DATOS ---")
        
        # 1. Crear todos los roles estándar una única vez
        print(f"Creando/Verificando {len(ROLES_ESTANDAR)} Roles estándar...")
        for role_name in ROLES_ESTANDAR:
            create_or_get_role(role_name)
        
        # 2. Iterar sobre las empresas
        for empresa_data in EMPRESAS_DATA:
            print(f"\nProcesando empresa: {empresa_data['nombre']}")
            
            # Crear o recuperar la empresa
            empresa = create_or_get_empresa(empresa_data)

            # Crear el usuario administrador de prueba para esta empresa
            create_admin_user_for_empresa(empresa, empresa_data)

        print("\n🎉 Inicialización de Empresas, Roles y Usuarios Admin completada exitosamente.")

        print("\n--- CREDENCIALES DE PRUEBA ---")
        for data in EMPRESAS_DATA:
            print(f"Empresa: {data['nombre']}")
            print(f"  Usuario: {data['admin_email']}")
            print(f"  Contraseña: {PASSWORD_BASE}")
            print("-" * 15)


if __name__ == "__main__":
    seed_database()