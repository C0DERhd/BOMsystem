from flask import Blueprint

bp = Blueprint('auth', __name__)

from app.auth import routes, local_auth, sso_auth