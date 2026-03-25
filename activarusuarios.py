# fix_users_active.py

from app import create_app, db
from app.models import AdminUser

def fix_inactive_users():
    app = create_app()

    with app.app_context():  # IMPORTANTÍSIMO
        users = AdminUser.query.filter(AdminUser.is_active.is_(None)).all()

        if not users:
            print("✔ No hay usuarios con is_active = NULL")
            return

        print(f"⚠ Usuarios encontrados con is_active=NULL: {len(users)}")
        for u in users:
            print(f"   - {u.id} | {u.nombre} | {u.email}")
            u.is_active = True

        db.session.commit()
        print("✔ Todos los usuarios fueron activados correctamente.")

if __name__ == "__main__":
    fix_inactive_users()
