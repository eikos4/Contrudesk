#!/usr/bin/env python3
"""
Script para crear datos de demostración completos.
Simula un proyecto real con todos los perfiles de usuario y datos de muestra.
"""

import os
import sys
from datetime import datetime, timedelta, date
from zoneinfo import ZoneInfo
import random
from app import create_app, db
from app.models import (
    Empresa, AdminUser, Role, Project, ProjectTask, ProjectUserRole,
    ProjectDocument, ProjectProgress, ProgressPhoto, DailyChecklist,
    ChecklistCompletion, IncidentReport, TechnicalReport, Comment
)

# ====================================================================
# 🏗️ DATOS DE DEMOSTRACIÓN
# ====================================================================

# Proyecto de construcción demo
PROYECTO_DEMO = {
    "nombre": "Edificio Torre Central - Oficinas Corporativas",
    "descripcion": "Construcción de edificio de 15 pisos con amenities subterráneos, ubicado en el centro financiero de Santiago.",
    "fecha_inicio": datetime(2024, 1, 15),
    "fecha_termino": datetime(2025, 6, 30),
    "presupuesto_total": 2500000000,  # 2.500 millones de pesos
    "ubicacion": "Av. Providencia 1234, Santiago"
}

# Usuarios de demo por rol
USUARIOS_DEMO = [
    {
        "nombre": "Carlos Silva",
        "email": "carlos.silva@horizon.cl",
        "rol": "admin",
        "password": "demo123"
    },
    {
        "nombre": "María González",
        "email": "maria.gonzalez@horizon.cl", 
        "rol": "editor",
        "password": "demo123"
    },
    {
        "nombre": "Roberto Méndez",
        "email": "roberto.mendez@horizon.cl",
        "rol": "editor", 
        "password": "demo123"
    },
    {
        "nombre": "Ana Castillo",
        "email": "ana.castillo@horizon.cl",
        "rol": "miembro",
        "password": "demo123"
    },
    {
        "nombre": "Luis Torres",
        "email": "luis.torres@horizon.cl",
        "rol": "miembro",
        "password": "demo123"
    },
    {
        "nombre": "Patricia Vargas",
        "email": "patricia.vargas@horizon.cl",
        "rol": "lector",
        "password": "demo123"
    },
    {
        "nombre": "Diego Fuentes",
        "email": "diego.fuentes@horizon.cl",
        "rol": "invitado",
        "password": "demo123"
    }
]

# Tareas del proyecto
TAREAS_DEMO = [
    {
        "nombre": "Excavación y movimiento de tierras",
        "descripcion": "Excavación hasta -15m, retiro de escombros y preparación del terreno",
        "dias_duracion": 30,
        "rol_asignado": "miembro"
    },
    {
        "nombre": "Fundaciones y pilotes",
        "descripcion": "Construcción de fundaciones profundas y pilotes de hormigón armado",
        "dias_duracion": 45,
        "rol_asignado": "miembro"
    },
    {
        "nombre": "Estructura de hormigón - Subterráneos",
        "descripcion": "Losa de fundación y muros de subterráneos",
        "dias_duracion": 60,
        "rol_asignado": "miembro"
    },
    {
        "nombre": "Estructura de hormigón - Primeros 5 pisos",
        "descripcion": "Columnas, vigas y losas de los primeros 5 niveles",
        "dias_duracion": 75,
        "rol_asignado": "miembro"
    },
    {
        "nombre": "Instalaciones sanitarias - Subterráneos",
        "descripcion": "Montaje de sistemas de agua potable y alcantarillado",
        "dias_duracion": 30,
        "rol_asignado": "editor"
    },
    {
        "nombre": "Instalaciones eléctricas - Primeros 5 pisos",
        "descripcion": "Montaje de ductos, tableros y cableado eléctrico",
        "dias_duracion": 45,
        "rol_asignado": "editor"
    },
    {
        "nombre": "Albañilería y tabiques - Primeros 5 pisos",
        "descripcion": "Construcción de muros divisorios y tabiques",
        "dias_duracion": 40,
        "rol_asignado": "miembro"
    },
    {
        "nombre": "Revestimientos exteriores",
        "descripcion": "Aplicación de fachada y aislamiento térmico",
        "dias_duracion": 60,
        "rol_asignado": "editor"
    }
]

# Checklist diario
CHECKLIST_DEMO = [
    "Verificación de equipos de seguridad personal",
    "Inspección de andamios y estructuras temporales",
    "Control de acceso y permisos de trabajo",
    "Verificación de materiales y herramientas",
    "Revisión de planos y especificaciones del día",
    "Control de calidad en hormigón y acero",
    "Limpieza y orden del área de trabajo",
    "Reporte de condiciones climáticas",
    "Verificación de sistemas de prevención de riesgos",
    "Control de personal presente en obra"
]

# Avances de obra simulados
AVANCES_DEMO = [
    {
        "dias_antes": 120,
        "descripcion": "Completada excavación hasta nivel -12m. Retirados 3,500m³ de escombros. Equipo trabajando en preparación de base para fundaciones.",
        "porcentaje": 15,
        "trabajadores": 12,
        "clima": "Despejado, 22°C"
    },
    {
        "dias_antes": 90,
        "descripcion": "Fundaciones completas al 80%. Hormigonado de 12 pilotes principales. Ensayos de resistencia superaron especificaciones.",
        "porcentaje": 35,
        "trabajadores": 18,
        "clima": "Nublado, 18°C"
    },
    {
        "dias_antes": 60,
        "descripcion": "Estructura subterránea terminada. Iniciado hormigonado de columnas del primer nivel. Instalaciones sanitarias en progreso.",
        "porcentaje": 55,
        "trabajadores": 25,
        "clima": "Parcialmente nublado, 20°C"
    },
    {
        "dias_antes": 30,
        "descripcion": "Tercer nivel completado. Trabajando en cuarto nivel. Instalaciones eléctricas avanzando según cronograma.",
        "porcentaje": 70,
        "trabajadores": 28,
        "clima": "Soleado, 24°C"
    },
    {
        "dias_antes": 15,
        "descripcion": "Quinto nivel en construcción. Fachada exterior iniciada en primeros niveles. Control de calidad sin observaciones mayores.",
        "porcentaje": 82,
        "trabajadores": 32,
        "clima": "Despejado, 21°C"
    },
    {
        "dias_antes": 7,
        "descripcion": "Preparación para montaje de estructura del sexto nivel. Revisión de planos de instalaciones. Todo según cronograma.",
        "porcentaje": 88,
        "trabajadores": 30,
        "clima": "Nublado, 19°C"
    }
]

# Incidentes de seguridad
INCIDENTES_DEMO = [
    {
        "dias_antes": 45,
        "tipo": "Caída de altura",
        "gravedad": "media",
        "descripcion": "Trabajador resbaló desde andamio a 3m de altura. Utilizaba arnés de seguridad correctamente.",
        "acciones_correctivas": "Inspección adicional de todos los andamios. Refuerzo de charla de seguridad diaria.",
        "lesiones": "Golpe leve en hombro, atención médica ambulatoria.",
        "testigos": "Juan Pérez (capataz), María López (seguridad)"
    },
    {
        "dias_antes": 20,
        "tipo": "Derrame de materiales",
        "gravedad": "baja",
        "descripcion": "Derrame de 50 litros de aceite lubricante en área de maquinaria.",
        "acciones_correctivas": "Contención inmediata con absorbentes. Limpieza completa del área. Capacitación sobre manejo de sustancias.",
        "lesiones": "Ninguna",
        "testigos": "Roberto Silva (operador), Carlos Muñoz (mantenimiento)"
    }
]

# Reportes técnicos
REPORTES_DEMO = [
    {
        "dias_antes": 30,
        "titulo": "Inspección Mensual - Estructura Hormigón",
        "periodo": "Marzo 2024",
        "inspector": "Ing. María González",
        "progreso_general": "Estructura avanzando según programa, calidad cumpliendo especificaciones.",
        "porcentaje_progreso": 70,
        "proximas_tareas": "Completar quinto nivel, iniciar montaje de fachada exterior.",
        "problemas": "Retraso menor en entrega de acero de refuerzo (3 días).",
        "acciones": "Coordinación con proveedor para compensar retraso con entregas parciales.",
        "trabajadores": 28
    },
    {
        "dias_antes": 10,
        "titulo": "Reporte Semanal - Instalaciones Eléctricas",
        "periodo": "Semana 15 Abril",
        "inspector": "Ing. Roberto Méndez",
        "progreso_general": "Instalaciones eléctricas en primer nivel completadas al 95%.",
        "porcentaje_progreso": 85,
        "proximas_tareas": "Finalizar primer nivel, iniciar segundo nivel.",
        "problemas": "Falta de material específico (conectores especiales).",
        "acciones": "Pedido urgente al proveedor, uso temporal de alternativas certificadas.",
        "trabajadores": 8
    }
]

# ====================================================================
# 🛠️ FUNCIONES DE CREACIÓN
# ====================================================================

def crear_usuarios_demo(empresa):
    """Crea todos los usuarios de demostración para la empresa."""
    usuarios_creados = {}
    
    for usuario_data in USUARIOS_DEMO:
        # Verificar si el usuario ya existe
        usuario_existente = AdminUser.query.filter_by(email=usuario_data["email"]).first()
        
        if not usuario_existente:
            # Obtener el rol
            rol = Role.query.filter_by(name=usuario_data["rol"]).first()
            
            # Crear usuario
            usuario = AdminUser(
                nombre=usuario_data["nombre"],
                email=usuario_data["email"],
                empresa_id=empresa.id
            )
            usuario.set_password(usuario_data["password"])
            usuario.roles.append(rol)
            
            db.session.add(usuario)
            usuarios_creados[usuario_data["rol"]] = usuario
            print(f"  ✅ Usuario {usuario_data['rol']} creado: {usuario_data['email']}")
        else:
            usuarios_creados[usuario_data["rol"]] = usuario_existente
            print(f"  ⚠️ Usuario {usuario_data['rol']} ya existía: {usuario_data['email']}")
    
    db.session.commit()
    return usuarios_creados

def crear_proyecto_demo(admin_user):
    """Crea el proyecto de demostración."""
    
    # Verificar si ya existe un proyecto
    proyecto_existente = Project.query.filter_by(name=PROYECTO_DEMO["nombre"]).first()
    
    if proyecto_existente:
        print(f"  ⚠️ Proyecto ya existía: {PROYECTO_DEMO['nombre']}")
        return proyecto_existente
    
    # Crear proyecto
    proyecto = Project(
        name=PROYECTO_DEMO["nombre"],
        description=PROYECTO_DEMO["descripcion"],
        start_date=PROYECTO_DEMO["fecha_inicio"],
        end_date=PROYECTO_DEMO["fecha_termino"],
        progress=88,  # Progreso actual simulado
        status="activo",
        total_budget=PROYECTO_DEMO["presupuesto_total"],
        creator_id=admin_user.id
    )
    
    db.session.add(proyecto)
    db.session.commit()
    
    print(f"  ✅ Proyecto creado: {proyecto.name}")
    return proyecto

def asignar_usuarios_al_proyecto(proyecto, usuarios):
    """Asigna los usuarios al proyecto con sus roles correspondientes."""
    
    for rol_nombre, usuario in usuarios.items():
        if rol_nombre in ["admin", "editor", "miembro", "lector", "invitado"]:
            rol = Role.query.filter_by(name=rol_nombre).first()
            
            # Verificar si ya está asignado
            asignacion_existente = ProjectUserRole.query.filter_by(
                project_id=proyecto.id,
                user_id=usuario.id
            ).first()
            
            if not asignacion_existente:
                asignacion = ProjectUserRole(
                    project_id=proyecto.id,
                    user_id=usuario.id,
                    role_id=rol.id
                )
                db.session.add(asignacion)
                print(f"    📋 {usuario.nombre} asignado como {rol_nombre}")
    
    db.session.commit()

def crear_tareas_demo(proyecto, usuarios):
    """Crea las tareas del proyecto."""
    
    fecha_actual = PROYECTO_DEMO["fecha_inicio"]
    
    for i, tarea_data in enumerate(TAREAS_DEMO):
        # Calcular fechas
        inicio = fecha_actual + timedelta(days=i*15)
        fin = inicio + timedelta(days=tarea_data["dias_duracion"])
        
        # Asignar usuario responsable según rol
        if tarea_data["rol_asignado"] == "miembro":
            responsable = random.choice([usuarios["miembro"]])
        else:
            responsable = usuarios["editor"]
        
        # Determinar estado según progreso
        if i < 3:
            estado = "completada"
        elif i < 5:
            estado = "en progreso"
        else:
            estado = "pendiente"
        
        tarea = ProjectTask(
            name=tarea_data["nombre"],
            description=tarea_data["descripcion"],
            start_date=inicio,
            end_date=fin,
            status=estado,
            project_id=proyecto.id,
            responsible_user_id=responsable.id
        )
        
        db.session.add(tarea)
        print(f"    📝 Tarea creada: {tarea_data['nombre']} ({estado})")
    
    db.session.commit()

def crear_checklist_demo(proyecto):
    """Crea el checklist diario del proyecto."""
    
    for item_text in CHECKLIST_DEMO:
        item = DailyChecklist(
            project_id=proyecto.id,
            item_text=item_text,
            is_active=True
        )
        db.session.add(item)
    
    db.session.commit()
    print(f"    ✅ Checklist creado con {len(CHECKLIST_DEMO)} ítems")

def crear_avances_demo(proyecto, usuarios):
    """Crea los avances de obra simulados."""
    
    for avance_data in AVANCES_DEMO:
        fecha = datetime.now() - timedelta(days=avance_data["dias_antes"])
        
        avance = ProjectProgress(
            project_id=proyecto.id,
            user_id=usuarios["editor"].id,
            description=avance_data["descripcion"],
            date=fecha
        )
        
        db.session.add(avance)
        db.session.flush()  # Para obtener el ID
        
        # Agregar foto de evidencia (simulada)
        foto = ProgressPhoto(
            progress_id=avance.id,
            file_path=f"uploads/demo/avance_{avance.id}.jpg"
        )
        db.session.add(foto)
    
    db.session.commit()
    print(f"    📊 {len(AVANCES_DEMO)} avances creados")

def crear_incidentes_demo(proyecto, usuarios):
    """Crea incidentes de seguridad."""
    
    for incidente_data in INCIDENTES_DEMO:
        fecha = datetime.now() - timedelta(days=incidente_data["dias_antes"])
        
        incidente = IncidentReport(
            reporter_id=usuarios["miembro"].id,
            reporter_name=usuarios["miembro"].nombre,
            reporter_role="miembro",
            reporter_email=usuarios["miembro"].email,
            reporter_phone="+56 9 1234 5678",
            project_id=proyecto.id,
            location=PROYECTO_DEMO["ubicacion"],
            incident_datetime=fecha,
            incident_type=incidente_data["tipo"],
            description=incidente_data["descripcion"],
            corrective_actions=incidente_data["acciones_correctivas"],
            injuries=incidente_data["lesiones"],
            witnesses=incidente_data["testigos"],
            severity=incidente_data["gravedad"],
            status="cerrado" if incidente_data["gravedad"] == "baja" else "abierto",
            closure_date=fecha + timedelta(days=3) if incidente_data["gravedad"] == "baja" else None
        )
        
        db.session.add(incidente)
    
    db.session.commit()
    print(f"    ⚠️ {len(INCIDENTES_DEMO)} incidentes creados")

def crear_reportes_demo(proyecto, usuarios):
    """Crea reportes técnicos."""
    
    for reporte_data in REPORTES_DEMO:
        fecha = datetime.now() - timedelta(days=reporte_data["dias_antes"])
        
        reporte = TechnicalReport(
            title=reporte_data["titulo"],
            content=f"Reporte técnico detallado para {reporte_data['titulo']}. "
                    f"Incluye inspecciones, mediciones y controles de calidad realizados.",
            project_id=proyecto.id,
            user_id=usuarios["editor"].id,
            created_at=fecha,
            inspector=reporte_data["inspector"],
            report_date=fecha.date(),
            period=reporte_data["periodo"],
            general_progress=reporte_data["progreso_general"],
            progress_percentage=reporte_data["porcentaje_progreso"],
            next_tasks=reporte_data["proximas_tareas"],
            problems_found=reporte_data["problemas"],
            actions_taken=reporte_data["acciones"],
            weather_conditions="Despejado",
            workers_on_site=reporte_data["trabajadores"],
            evidence_photos=f"uploads/demo/evidencia_{reporte_data['dias_antes']}.jpg"
        )
        
        db.session.add(reporte)
    
    db.session.commit()
    print(f"    📋 {len(REPORTES_DEMO)} reportes técnicos creados")

def crear_comentarios_demo(proyecto, usuarios):
    """Crea comentarios en tareas para demostrar colaboración."""
    
    tareas = ProjectTask.query.filter_by(project_id=proyecto.id).limit(3).all()
    
    for tarea in tareas:
        # Comentario del editor
        comentario1 = Comment(
            content="Por favor verificar que los materiales cumplan con las especificaciones técnicas antes de proceder.",
            user_id=usuarios["editor"].id,
            project_id=proyecto.id,
            task_id=tarea.id
        )
        db.session.add(comentario1)
        
        # Respuesta del miembro
        comentario2 = Comment(
            content="Verificado. Los materiales están certificados y listos para instalación.",
            user_id=usuarios["miembro"].id,
            project_id=proyecto.id,
            task_id=tarea.id
        )
        db.session.add(comentario2)
    
    db.session.commit()
    print(f"    💬 Comentarios de colaboración creados")

# ====================================================================
# 🚀 FUNCIÓN PRINCIPAL
# ====================================================================

def crear_demo_completa():
    """Ejecuta toda la creación de datos de demostración."""
    
    app = create_app()
    with app.app_context():
        print("🏗️ CREANDO DATOS DE DEMOSTRACIÓN COMPLETOS")
        print("=" * 50)
        
        # 1. Obtener empresa Horizon Services
        empresa = Empresa.query.filter_by(nombre="Horizon Services Integrales").first()
        if not empresa:
            print("❌ Error: Debes ejecutar primero 'python users_initial.py' para crear la empresa base")
            return
        
        print(f"📋 Empresa: {empresa.nombre}")
        
        # 2. Crear usuarios de demo
        print("\n👥 Creando usuarios de demostración...")
        usuarios = crear_usuarios_demo(empresa)
        
        # 3. Crear proyecto
        print("\n🏗️ Creando proyecto de demostración...")
        admin_user = usuarios["admin"]
        proyecto = crear_proyecto_demo(admin_user)
        
        # 4. Asignar usuarios al proyecto
        print("\n📋 Asignando usuarios al proyecto...")
        asignar_usuarios_al_proyecto(proyecto, usuarios)
        
        # 5. Crear tareas
        print("\n📝 Creando tareas del proyecto...")
        crear_tareas_demo(proyecto, usuarios)
        
        # 6. Crear checklist
        print("\n✅ Creando checklist diario...")
        crear_checklist_demo(proyecto)
        
        # 7. Crear avances
        print("\n📊 Creando avances de obra...")
        crear_avances_demo(proyecto, usuarios)
        
        # 8. Crear incidentes
        print("\n⚠️ Creando incidentes de seguridad...")
        crear_incidentes_demo(proyecto, usuarios)
        
        # 9. Crear reportes técnicos
        print("\n📋 Creando reportes técnicos...")
        crear_reportes_demo(proyecto, usuarios)
        
        # 10. Crear comentarios
        print("\n💬 Creando comentarios de colaboración...")
        crear_comentarios_demo(proyecto, usuarios)
        
        # Actualizar progreso del proyecto
        proyecto.progress = 88
        db.session.commit()
        
        print("\n" + "=" * 50)
        print("🎉 DATOS DE DEMOSTRACIÓN CREADOS EXITOSAMENTE!")
        print("=" * 50)
        
        print("\n📱 CREDENCIALES PARA ACCESO:")
        print("-" * 30)
        for rol, usuario in usuarios.items():
            print(f"{rol.upper():10}: {usuario.email:25} | Password: demo123")
        
        print(f"\n🏗️ PROYECTO CREADO:")
        print(f"Nombre: {proyecto.name}")
        print(f"Progreso: {proyecto.progress}%")
        print(f"Estado: {proyecto.status}")
        print(f"Presupuesto: ${proyecto.total_budget:,}")
        
        print(f"\n📊 RESUMEN DE DATOS CREADOS:")
        print(f"- Usuarios: {len(usuarios)}")
        print(f"- Tareas: {len(TAREAS_DEMO)}")
        print(f"- Avances: {len(AVANCES_DEMO)}")
        print(f"- Incidentes: {len(INCIDENTES_DEMO)}")
        print(f"- Reportes: {len(REPORTES_DEMO)}")
        print(f"- Checklist: {len(CHECKLIST_DEMO)} ítems")
        
        print(f"\n🌐 ACCESO A LA APLICACIÓN:")
        print(f"URL: http://127.0.0.1:5000")
        print(f"Usa las credenciales above para explorar cada perfil")

if __name__ == "__main__":
    crear_demo_completa()
