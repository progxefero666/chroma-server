from flask import Blueprint

api_bp = Blueprint('api', __name__, url_prefix='/api')

# Import endpoints to register them
from . import endpoints
