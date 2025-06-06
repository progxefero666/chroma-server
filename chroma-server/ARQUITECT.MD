# Chroma Server - Architecture and Libraries

This document outlines the architecture and key libraries used in the Chroma Server project.

## Core Architecture

*   **Application Type**: Web Server with REST API and HTML Interface.
*   **Framework**: Flask (Python)
*   **Primary Language**: Python 3.12
*   **Database (Vector)**: ChromaDB
*   **Database (Relational - Schema Source)**: The project uses DDL statements (SQLite dialect) to define the schema of data that would notionally be vectorized. No live relational database is directly connected for data; ChromaDB is the sole runtime database.
*   **Frontend Styling**: Tailwind CSS (compiled using the standalone CLI)
*   **Templating**: Jinja2 (via Flask)

## Key Components

1.  **`app.py`**:
    *   The main entry point for the Flask application.
    *   Initializes the Flask app, registers blueprints, and defines routes for serving HTML pages.
    *   Starts the development server.

2.  **`chroma_utils.py`**:
    *   Handles all interactions with ChromaDB:
        *   Client initialization (persistent storage in `./chroma_data/`).
        *   Collection creation/access (default collection: "particles").
        *   (Future) Functions for adding, querying, and deleting vector data.
    *   Contains the DDL (CREATE TABLE statements) for the relational schema.
    *   Includes a DDL parser (`parse_ddl_statements`) to convert these statements into a structured Python dictionary representing table schemas. This is used by the API and UI to display schema information.

3.  **`api/` directory (`endpoints.py`, `__init__.py`)**:
    *   Defines the REST API using Flask Blueprints.
    *   Current endpoints:
        *   `/status`: Basic API status.
        *   `/schema`: Serves the parsed DDL schema.
        *   `/collection/info`: Provides information about the ChromaDB collection.
        *   Placeholder endpoints for vector search operations.
    *   (Future) Endpoints for adding data, advanced queries, etc.

4.  **`templates/` directory**:
    *   Contains Jinja2 HTML templates for the web interface.
    *   `base.html`: Master layout with sidebar navigation and Tailwind CSS integration.
    *   `index.html`: Server status page.
    *   `schema.html`: Displays the database schema (fetched via JavaScript from `/api/schema`).
    *   `search.html`: Placeholder for search interface.
    *   `detail.html`: Placeholder for item detail view.

5.  **`static/` directory**:
    *   `css/src/input.css`: Source file for Tailwind CSS directives.
    *   `css/style.css`: Compiled and minified Tailwind CSS output.
    *   `js/main.js`: Custom JavaScript (currently minimal, `schema.html` has inline JS for API calls).

6.  **`tailwind.config.js`**:
    *   Configuration file for Tailwind CSS, specifying content paths for class detection.

## Libraries and Versions

As specified in `requirements.txt`:

*   **Flask**: (Version will be as installed by `pip install Flask`) - Micro web framework for Python.
*   **chromadb**: (Version will be as installed by `pip install chromadb`) - The vector database.
*   **Python**: 3.12.x

**Development Tools (not runtime dependencies):**

*   **Tailwind CSS CLI**: (Latest version used for compilation) - For generating the `style.css` utility stylesheet.

## Data Flow

1.  **Schema Display**:
    *   DDL statements are stored in `chroma_utils.py`.
    *   `parse_ddl_statements` function processes these DDLs into a Python dictionary.
    *   The `/api/schema` endpoint serves this dictionary as JSON.
    *   The `schema.html` page fetches this JSON via JavaScript and renders it as HTML.

2.  **ChromaDB Interaction**:
    *   `chroma_utils.py` initializes a persistent ChromaDB client, storing data in the `chroma_data/` directory.
    *   A default collection "particles" is created/accessed.
    *   API endpoints (currently `/api/collection/info`, future search endpoints) will use functions in `chroma_utils.py` to interact with this collection.

3.  **User Interface**:
    *   Flask routes in `app.py` serve HTML pages from `templates/`.
    *   `base.html` provides the common layout.
    *   Tailwind CSS (from `static/css/style.css`) styles the interface.

## Design Considerations

*   **Self-Contained**: The application aims to be runnable with minimal external setup beyond Python and pip. ChromaDB data is local.
*   **No Frontend Framework**: The UI is built with server-side Flask/Jinja2 templates and minimal JavaScript, avoiding complex frontend build toolchains (React, Vue, Webpack, Vite are explicitly excluded).
*   **Portability**: Designed to run on Windows and Linux where Python is supported.
*   **Extensibility**: The structure (blueprints, utility modules) is intended to allow for easier addition of new features.
*   **Modern UI**: Styling aims for a modern look and feel using Tailwind CSS, inspired by platforms like Google AI Studio.
