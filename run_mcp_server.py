# c:\python\apps\chroma-server\run_mcp_server.py
import os
from mcp.server.fastmcp import FastMCP
from chroma_server.chroma_utils import parse_ddl_statements, ALL_DDL_STATEMENTS

# 1. Crear la instancia de FastMCP
# Usamos un nombre de variable diferente para la instancia para evitar confusión con el módulo 'mcp'
mcp_object = FastMCP(os.environ.get('MCP_SERVER_NAME', 'Chroma DDL Server (FastMCP)'))
print(f"INFO: Instancia de FastMCP '{mcp_object.name}' creada.")

# 2. Registrar las herramientas en esta instancia
_mcp_parsed_schema_cache = None # Cache para esta instancia del servidor

@mcp_object.tool()
def get_secret_number() -> int:
    """Devuelve un número secreto predefinido."""
    print(f"MCP Tool ({mcp_object.name}): get_secret_number() llamada.")
    return 13

@mcp_object.tool()
def get_ddl_schema_context() -> dict:
    """Provee el contexto del esquema DDL analizado."""
    global _mcp_parsed_schema_cache
    print(f"MCP Tool ({mcp_object.name}): get_ddl_schema_context() llamada.")
    if _mcp_parsed_schema_cache is None:
        print(f"MCP Tool ({mcp_object.name}): Analizando sentencias DDL para el caché del esquema...")
        _mcp_parsed_schema_cache = parse_ddl_statements(ALL_DDL_STATEMENTS)
        print(f"MCP Tool ({mcp_object.name}): Análisis DDL completo. {len(_mcp_parsed_schema_cache)} tablas analizadas.")
    return _mcp_parsed_schema_cache

# 3. Exponer la aplicación ASGI para Uvicorn
application_to_run = None # Inicializar
try:
    # Esta es la variable que Uvicorn usará.
    # Accedemos al atributo _mcp_server de nuestra instancia mcp_object
    application_to_run = mcp_object._mcp_server 
    print(f"INFO: La aplicación ASGI (obtenida de mcp_object._mcp_server) es: {application_to_run}")
    print(f"INFO: Tipo de la aplicación ASGI: {type(application_to_run)}")
    # Eliminamos la comprobación 'if not callable(application_to_run):'
    # Dejamos que Uvicorn decida si puede manejar este objeto.

except AttributeError:
    print("ERROR CRÍTICO: El objeto FastMCP (mcp_object) no tiene un atributo '_mcp_server'.")
    application_to_run = None # Asegurarse de que es None si hay error
except Exception as e:
    print(f"ERROR CRÍTICO al intentar obtener mcp_object._mcp_server: {e}")
    application_to_run = None # Asegurarse de que es None si hay error

if application_to_run is None:
    print("ERROR CRÍTICO: 'application_to_run' no se pudo asignar correctamente. Uvicorn fallará.")

# Para ejecutar con Uvicorn desde la terminal (estando en c:\python\apps\chroma-server y con venv activado):
# uvicorn run_mcp_server:application_to_run --host 127.0.0.1 --port 8001 --reload
