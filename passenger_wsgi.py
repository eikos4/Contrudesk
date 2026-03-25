import sys
import os

# Agregar path del proyecto
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importar y crear aplicación
from app import create_app
app = create_app()

# Passenger necesita esta variable
application = app