from . import api_bp
from flask import jsonify, current_app
from chroma_server.chroma_utils import parse_ddl_statements, ALL_DDL_STATEMENTS, get_particles_collection

# Cache for parsed DDL schema
_parsed_schema_cache = None

def get_parsed_schema():
    global _parsed_schema_cache
    if _parsed_schema_cache is None:
        current_app.logger.info("Parsing DDL statements for schema cache...")
        _parsed_schema_cache = parse_ddl_statements(ALL_DDL_STATEMENTS)
        current_app.logger.info(f"DDL parsing complete. Parsed {len(_parsed_schema_cache)} tables.")
    return _parsed_schema_cache

@api_bp.route('/status')
def status():
    return jsonify({'status': 'API is running', 'message': 'Welcome to the Chroma Server API!'})

@api_bp.route('/schema')
def get_schema():
    try:
        schema_data = get_parsed_schema()
        if not schema_data:
            return jsonify({"error": "Schema could not be parsed or is empty"}), 500
        return jsonify(schema_data)
    except Exception as e:
        current_app.logger.error(f"Error getting schema: {e}", exc_info=True)
        return jsonify({"error": "An error occurred while retrieving the schema", "details": str(e)}), 500

@api_bp.route('/collection/info')
def collection_info():
    try:
        collection = get_particles_collection()
        return jsonify({
            "name": collection.name,
            "id": str(collection.id), # Convert UUID to string
            "count": collection.count(),
            "metadata": collection.metadata if collection.metadata else "No metadata set for collection"
        })
    except Exception as e:
        current_app.logger.error(f"Error getting collection info: {e}", exc_info=True)
        return jsonify({"error": "An error occurred while retrieving collection information", "details": str(e)}), 500

# Placeholder endpoints for future implementation
@api_bp.route('/vectors/query_by_id/<string:vector_id>')
def query_vector_by_id(vector_id):
    # TODO: Implement actual ChromaDB query
    return jsonify({
        "message": "Placeholder: Query vector by ID",
        "vector_id": vector_id,
        "data": "Not yet implemented. This endpoint will return vector data for the given ID."
    }), 501

@api_bp.route('/vectors/query_by_metadata', methods=['POST'])
def query_vector_by_metadata():
    # Expects JSON payload with metadata filters
    # from flask import request
    # metadata_filters = request.json
    # TODO: Implement actual ChromaDB query with metadata filters
    return jsonify({
        "message": "Placeholder: Query vector by metadata",
        # "filters_received": metadata_filters, # Uncomment when ready to process
        "data": "Not yet implemented. This endpoint will search vectors based on provided metadata."
    }), 501

@api_bp.route('/vectors/search_content', methods=['POST'])
def search_vector_by_content():
    # Expects JSON payload with search query
    # from flask import request
    # search_payload = request.json
    # query_text = search_payload.get('query')
    # n_results = search_payload.get('n_results', 10)
    # TODO: Implement actual ChromaDB content search (similarity search)
    return jsonify({
        "message": "Placeholder: Search vector by content",
        # "query_received": query_text, # Uncomment
        "data": "Not yet implemented. This endpoint will perform a similarity search based on content."
    }), 501

# Example of how to add data (for future reference, not used now as per instructions)
# @api_bp.route('/vectors/add', methods=['POST'])
# def add_vector():
#     # from flask import request
#     # data = request.json # {'ids': [], 'documents': [], 'metadatas': []}
#     # collection = get_particles_collection()
#     # collection.add(ids=data['ids'], documents=data['documents'], metadatas=data['metadatas'])
#     return jsonify({"message": "Placeholder: Add vector data"}), 501


# --- NUEVO ENDPOINT MCP ---
@api_bp.route('/mcp/context/ddl_schema', methods=['GET'])
def get_mcp_ddl_schema_context():
    """
    MCP Endpoint to provide DDL schema context.
    """
    current_app.logger.info("MCP: Request for DDL schema context.")
    try:
        schema_data = get_parsed_schema() # Reutilizamos la función existente
        if not schema_data:
            current_app.logger.warning("MCP: DDL schema context is empty or could not be parsed.")
            return jsonify({"error": "MCP context: DDL Schema could not be parsed or is empty"}), 500
        
        # Por ahora, devolvemos la misma estructura que /api/schema.
        # Esto podría adaptarse si el cliente MCP espera un formato específico.
        return jsonify(schema_data)
    except Exception as e:
        current_app.logger.error(f"MCP: Error providing DDL schema context: {e}", exc_info=True)
        return jsonify({"error": "MCP context: An error occurred while retrieving DDL schema", "details": str(e)}), 500

# --- Fin del NUEVO ENDPOINT MCP ---


from chroma_server.chroma_utils import populate_schema_in_chromadb, get_particles_collection, parse_ddl_statements, ALL_DDL_STATEMENTS
from flask import request # Added for request.args

@api_bp.route('/schema/load_to_chroma', methods=['POST'])
def load_schema_to_chroma():
    current_app.logger.info("API: Attempting to load DDL schema into ChromaDB...")
    try:
        # This uses the global ALL_DDL_STATEMENTS and default collection
        parsed_schemas = parse_ddl_statements(ALL_DDL_STATEMENTS) # Parse first
        collection = get_particles_collection() # Get the collection

        # Call populate_schema_in_chromadb with the specific collection and parsed_schemas
        num_docs_added = populate_schema_in_chromadb(collection=collection, parsed_schemas=parsed_schemas)

        current_app.logger.info(f"API: Successfully populated {num_docs_added} schema documents into ChromaDB.")
        return jsonify({"message": "Schema loaded into ChromaDB successfully.", "documents_added": num_docs_added}), 200
    except Exception as e:
        current_app.logger.error(f"API: Error loading schema to ChromaDB: {e}", exc_info=True)
        return jsonify({"error": "Failed to load schema to ChromaDB", "details": str(e)}), 500

@api_bp.route('/schema/search')
def search_schema_in_chroma():
    query_text = request.args.get('q')
    n_results = request.args.get('n_results', default=5, type=int)

    if not query_text:
        return jsonify({"error": "Query parameter 'q' is required."}), 400

    current_app.logger.info(f"API: Searching schema in ChromaDB for: '{query_text}', n_results={n_results}")
    try:
        collection = get_particles_collection()
        # We search for documents of type "table_schema" or "column_schema"
        # This 'where' clause assumes metadatas were set up with 'type' and 'source'
        results = collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where={"source": "ddl_parser"} # This ensures we only search schema docs we added
        )

        formatted_results = []
        if results and results.get('ids') and results['ids'][0]:
            for i in range(len(results['ids'][0])):
                formatted_results.append({
                    "id": results['ids'][0][i],
                    "document": results['documents'][0][i] if results['documents'] else None,
                    "metadata": results['metadatas'][0][i] if results['metadatas'] else None,
                    "distance": results['distances'][0][i] if results['distances'] else None,
                })

        current_app.logger.info(f"API: Found {len(formatted_results)} schema results for '{query_text}'.")
        return jsonify({
            "query": query_text,
            "results": formatted_results
        })
    except Exception as e:
        current_app.logger.error(f"API: Error searching schema in ChromaDB: {e}", exc_info=True)
        return jsonify({"error": "Failed to search schema in ChromaDB", "details": str(e)}), 500
