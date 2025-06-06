# Chroma Server

## Overview

Chroma Server is a dedicated server for managing and querying [ChromaDB](https://www.trychroma.com/) vector databases. It provides a REST API for programmatic access and a web interface for visual interaction, similar in style to modern AI development platforms. This project is built with Python and Flask, designed to be self-contained and easy to deploy.

The server is also prepared for potential integration with tools like Claude Desktop as a custom tool.

## Features

*   **REST API**: For interacting with vector data and schema.
*   **Web Interface**: Modern UI (styled with Tailwind CSS) for:
    *   Viewing server status.
    *   Browsing database schema (derived from DDL).
    *   Searching/querying vectors (partially implemented).
    *   Viewing item details (placeholder).
*   **Persistent ChromaDB**: Data is stored on disk within the project structure.
*   **Self-contained**: Runs as a single Flask application.
*   **Cross-platform**: Compatible with Windows and Linux (Python dependent).

## Project Structure

```
chroma-server/
├── app.py                   # Main Flask app
├── requirements.txt         # Python dependencies
├── chroma_utils.py          # Functions for interacting with ChromaDB & DDL parsing
├── tailwind.config.js       # Tailwind CSS configuration
├── api/                     # REST API module
│   ├── __init__.py
│   └── endpoints.py
├── static/                  # Static assets
│   ├── css/
│   │   ├── src/input.css    # Tailwind input
│   │   └── style.css        # Compiled Tailwind CSS
│   └── js/
│       └── main.js
├── templates/               # Jinja2 HTML templates
│   ├── base.html
│   ├── index.html
│   ├── schema.html
│   ├── search.html
│   └── detail.html
├── chroma_data/             # Default directory for ChromaDB persistent storage
├── README.md                # This file
├── ARQUITECT.MD             # Architecture and library details
└── .gitignore               # Git ignore file
```

## Getting Started

### Prerequisites

*   Python 3.12 or higher
*   `pip` for installing Python packages
*   `git` for cloning the repository (optional, if downloading as zip)

### Installation

1.  **Clone the repository (or download and extract the source code):**
    ```bash
    git clone <repository_url> # Replace <repository_url> with the actual URL
    cd chroma-server
    ```

2.  **Create a Python virtual environment (recommended):**
    ```bash
    echo "python -m venv venv"
    ```

3.  **Activate the virtual environment:**
    *   On Windows:
        ```bash
        .\venv\Scripts\activate
        ```
    *   On macOS and Linux:
        ```bash
        source venv/bin/activate
        ```

4.  **Install the required Python packages:**
    ```bash
    pip install -r requirements.txt
    ```

5.  **(Optional) Compile Tailwind CSS:**
    If you make changes to Tailwind classes in HTML/JS files or to `static/css/src/input.css`, you'll need to recompile the CSS. The Tailwind CLI is not included in the project dependencies for runtime. You would typically download it and run:
    ```bash
    # Download tailwindcss-linux-x64 (or other version for your OS)
    # from https://github.com/tailwindlabs/tailwindcss/releases
    # chmod +x tailwindcss-linux-x64
    # ./tailwindcss-linux-x64 -i ./static/css/src/input.css -o ./static/css/style.css --minify
    ```
    A pre-compiled `style.css` is included.

### Running the Server

Once the installation is complete, you can start the Flask development server:

```bash
python app.py
```

The server will start, and by default, it will be accessible at:
*   **Web Interface**: `http://localhost:8000/`
*   **API Base URL**: `http://localhost:8000/api/`

## Usage

### Web Interface

Navigate to `http://localhost:8000/` in your web browser.

*   **Home**: Shows server status and quick links.
*   **Schema**: Displays the database schema, parsed from the DDL statements defined in `chroma_utils.py`.
*   **Search**: Provides a basic form for searching (functionality is currently a placeholder).
*   **API Links (Sidebar)**: Direct links to key API endpoints for quick inspection.

### REST API

The API is accessible under the `/api/` prefix.

**Key Endpoints:**

*   **`GET /api/status`**:
    *   Description: Returns the status of the API.
    *   Example Response:
        ```json
        {
          "status": "API is running",
          "message": "Welcome to the Chroma Server API!"
        }
        ```

*   **`GET /api/schema`**:
    *   Description: Returns the parsed DDL schema for all tables.
    *   Example Response (snippet):
        ```json
        {
          "pdgitem": {
            "columns": [
              { "name": "id", "type": "INTEGER", "not_null": true, "primary_key": true },
              { "name": "name", "type": "VARCHAR", "not_null": true },
              { "name": "item_type", "type": "VARCHAR(1)", "not_null": true }
            ],
            "primary_key": ["id"],
            "unique_constraints": [["name"]], // Example if ix_pdgitem_name implies a unique constraint parsed
            "foreign_keys": [],
            "check_constraints": []
          }
          // ... other tables
        }
        ```
        *(Note: The unique constraint `ix_pdgitem_name` is an index; the DDL parser currently focuses on `CREATE TABLE` constraints. This example shows how it *would* look if parsed as a table constraint.)*


*   **`GET /api/collection/info`**:
    *   Description: Returns information about the default ChromaDB collection ("particles").
    *   Example Response:
        ```json
        {
          "name": "particles",
          "id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx", // UUID of the collection
          "count": 0, // Number of items in the collection
          "metadata": "No metadata set for collection"
        }
        ```

**Placeholder API Endpoints (Not Yet Implemented - Return HTTP 501):**

*   `GET /api/vectors/query_by_id/<string:vector_id>`
*   `POST /api/vectors/query_by_metadata` (expects JSON payload)
*   `POST /api/vectors/search_content` (expects JSON payload with "query")


## Claude Desktop Integration (Tool Configuration)

To use this Chroma Server as a tool with Claude Desktop or a similar Multi-Capability Planner (MCP), you can add the following configuration to its JSON tool definition file (e.g., `claude_desktop_config.json`).

This server exposes its functionalities via HTTP REST endpoints. The tool definition below describes how an AI agent can interact with these endpoints.

**Important Considerations:**

*   **Server URL**: Ensure the `server_url` and endpoint URLs in the functions match where your Chroma Server is running (default is `http://localhost:8000`).
*   **Chroma Data Location**: The ChromaDB vector database for this server is stored locally within the project in the `chroma_data/` directory. This makes the server and its data self-contained.
*   **API Key/Auth**: The current server setup does not include API key authentication. If you deploy this in a more open environment, consider adding authentication.

```json
{
  "tool_name": "ChromaServerPDG",
  "description": "A dedicated server for querying Particle Data Group (PDG) related schema information stored in a ChromaDB vector database. It can retrieve table structures, column details, and search across this schema information. The primary table of interest is 'pdgitem'.",
  "creator": "Chroma Server Project",
  "server_url": "http://localhost:8000",
  "endpoints": [
    {
      "name": "get_server_status",
      "description": "Checks the operational status of the Chroma Server API.",
      "method": "GET",
      "path": "/api/status",
      "parameters": []
    },
    {
      "name": "get_full_database_schema",
      "description": "Retrieves the complete parsed DDL (Data Definition Language) schema for all tables managed by the server. This shows table names, columns, data types, and constraints.",
      "method": "GET",
      "path": "/api/schema",
      "parameters": []
    },
    {
      "name": "get_chroma_collection_info",
      "description": "Gets information about the primary ChromaDB collection, named 'particles', such as its ID and current item count.",
      "method": "GET",
      "path": "/api/collection/info",
      "parameters": []
    },
    {
      "name": "search_schema_information",
      "description": "Searches the stored DDL schema information (table names, column names, types, descriptions) for specific keywords. Useful for finding relevant tables or columns related to a query (e.g., 'find columns related to particle mass' or 'details of pdgitem table').",
      "method": "GET",
      "path": "/api/schema/search",
      "parameters": [
        {
          "name": "q",
          "type": "string",
          "required": true,
          "description": "The search query string (e.g., 'pdgitem table', 'column description for mass')."
        },
        {
          "name": "n_results",
          "type": "integer",
          "required": false,
          "description": "Optional. Number of search results to return. Defaults to 5 or 10 based on server config."
        }
      ]
    }
    // Note: Endpoints for querying actual vector data (by ID, metadata, content similarity)
    // are defined as placeholders in the API (e.g., /api/vectors/query_by_id/<id>)
    // but are not yet implemented. Once implemented, they can be added here.
    // Example for a future endpoint:
    // {
    //   "name": "query_vector_by_id",
    //   "description": "Retrieves a specific vector and its metadata by its unique ID.",
    //   "method": "GET",
    //   "path": "/api/vectors/query_by_id/{vector_id}",
    //   "parameters": [
    //     {
    //       "name": "vector_id",
    //       "type": "string",
    //       "required": true,
    //       "in": "path", // Indicates it's part of the URL path
    //       "description": "The unique identifier of the vector to retrieve."
    //     }
    //   ]
    // }
  ]
}
```

**How to use this configuration:**

1.  Copy the JSON object above.
2.  Paste it into the appropriate array or section within your Claude Desktop `tools_config.json` (or equivalent MCP configuration file).
3.  Ensure the Chroma Server (`python app.py`) is running and accessible at the specified `server_url`.
4.  The AI agent should then be able to discover and use the defined functions (e.g., `ChromaServerPDG.search_schema_information(q='details about pdgitem')`).

This definition allows the AI to understand what the tool can do and how to make requests to the Chroma Server API.

## Extending the Project

*   **Implement Search Endpoints**: Flesh out the placeholder API endpoints in `api/endpoints.py` and connect them to `chroma_utils.py` functions that perform ChromaDB queries.
*   **Vectorization Strategy**: Define how DDL table data (or other data sources) will be converted into vector embeddings and stored in ChromaDB. The current focus is on schema display.
*   **UI Enhancements**:
    *   Improve the ERD visualization on the schema page.
    *   Implement client-side logic for search forms in `search.html` to call the API.
    *   Develop the `detail.html` page to show specific item data.
    *   Add data export functionality (JSON, Markdown, CSV).
*   **DDL Ingestion**: The current DDL is hardcoded. Future work could involve uploading DDL or connecting to a live database to extract schema.
*   **Error Handling**: Enhance error handling and user feedback in both API and UI.

## Database Schema (Source)

The database schema is defined by a series of `CREATE TABLE` statements provided in the initial project requirements. These statements are parsed by `chroma_utils.py` to display the schema in the web interface and API. The main table intended for vectorization is `pdgitem`. The ChromaDB collection is named "particles" and data is persisted in the `./chroma_data/` directory.
The DDL for tables like `pdgdoc`, `pdgreference`, `pdginfo`, `pdgid`, `pdgitem`, etc., is included directly in `chroma_utils.py`.

---
*This README provides a snapshot of the project at its current stage of development.*
