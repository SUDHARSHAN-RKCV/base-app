# app/main/__init__.py
from flask import Blueprint

main = Blueprint(
    'main',
    __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/main/static'   # 👈 mount under /main/static
)

from app.main import routes