#!/usr/bin/env python3
"""
Script para resetear la base de datos completamente.
Elimina todas las empresas, usuarios y roles para empezar desde cero.
"""

import os
import sys
from app import create_app, db
from app.models import Empresa, AdminUser, Role, Project, ProjectTask, IncidentReport, TechnicalReport

def reset_database():
    """Elimina todos los datos de la base de datos y la recrea."""
    
    app = create_app()
    with app.app_context():
        print("🔄 RESETEANDO BASE DE DATOS...")
        
        # Eliminar todos los datos en orden correcto (por foreign keys)
        print("\n📋 Eliminando datos existentes:")
        
        # Tablas con dependencias primero
        try:
            TechnicalReport.query.delete()
            print("  ✅ Technical Reports eliminados")
        except Exception as e:
            print(f"  ⚠️ Error eliminando Technical Reports: {e}")
            
        try:
            ProjectTask.query.delete()
            print("  ✅ Project Tasks eliminados")
        except Exception as e:
            print(f"  ⚠️ Error eliminando Project Tasks: {e}")
            
        try:
            IncidentReport.query.delete()
            print("  ✅ Incident Reports eliminados")
        except Exception as e:
            print(f"  ⚠️ Error eliminando Incident Reports: {e}")
            
        try:
            Project.query.delete()
            print("  ✅ Projects eliminados")
        except Exception as e:
            print(f"  ⚠️ Error eliminando Projects: {e}")
            
        try:
            AdminUser.query.delete()
            print("  ✅ Admin Users eliminados")
        except Exception as e:
            print(f"  ⚠️ Error eliminando Admin Users: {e}")
            
        try:
            Empresa.query.delete()
            print("  ✅ Empresas eliminadas")
        except Exception as e:
            print(f"  ⚠️ Error eliminando Empresas: {e}")
            
        try:
            Role.query.delete()
            print("  ✅ Roles eliminados")
        except Exception as e:
            print(f"  ⚠️ Error eliminando Roles: {e}")
        
        # Confirmar cambios
        db.session.commit()
        print("\n🗑️  Todos los datos han sido eliminados")
        
        # Recrear tablas
        db.drop_all()
        db.create_all()
        print("🏗️  Estructura de base de datos recreada")
        
        print("\n🎉 Base de datos reseteada exitosamente!")
        print("📝 Ahora puedes ejecutar 'python users_initial.py' para crear datos de prueba")

def show_current_data():
    """Muestra los datos actuales en la base de datos."""
    
    app = create_app()
    with app.app_context():
        print("\n📊 DATOS ACTUALES EN LA BASE DE DATOS:")
        print("-" * 50)
        
        try:
            empresas = Empresa.query.all()
            print(f"🏢 Empresas: {len(empresas)}")
            for emp in empresas:
                print(f"   - {emp.nombre} ({emp.rut})")
        except Exception as e:
            print(f"❌ Error consultando empresas: {e}")
            
        try:
            usuarios = AdminUser.query.all()
            print(f"\n👥 Usuarios: {len(usuarios)}")
            for user in usuarios:
                roles = [role.name for role in user.roles]
                print(f"   - {user.nombre} ({user.email}) - Roles: {', '.join(roles)}")
        except Exception as e:
            print(f"❌ Error consultando usuarios: {e}")
            
        try:
            roles = Role.query.all()
            print(f"\n🔑 Roles: {len(roles)}")
            for role in roles:
                print(f"   - {role.name}")
        except Exception as e:
            print(f"❌ Error consultando roles: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--show":
        show_current_data()
    else:
        print("⚠️  ESTÁS A PUNTO DE ELIMINAR TODOS LOS DATOS")
        print("   Esto incluye empresas, usuarios, proyectos y todo lo demás")
        
        confirm = input("\n¿Estás seguro? (escribe 'ELIMINAR' para confirmar): ")
        
        if confirm == "ELIMINAR":
            reset_database()
        else:
            print("❌ Operación cancelada")
            print("💡 Si solo quieres ver los datos actuales, ejecuta: python reset_database.py --show")
