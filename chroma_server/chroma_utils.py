import chromadb
import os
import re
import json # For the test block

CHROMA_DATA_PATH = "chroma_data"
COLLECTION_NAME = "particles"

# IMPORTANT: CREATE INDEX statements are NOT included here as the parser only processes CREATE TABLE.
# The DDLs are taken directly from the issue description's CREATE TABLE statements.
ALL_DDL_STATEMENTS = [
    "CREATE TABLE pdgdoc (id INTEGER NOT NULL, table_name VARCHAR NOT NULL, column_name VARCHAR NOT NULL, value VARCHAR, indicator VARCHAR NOT NULL, description VARCHAR NOT NULL, comment VARCHAR, PRIMARY KEY (id), UNIQUE (table_name, column_name, value))",
    "CREATE TABLE pdgreference (id INTEGER NOT NULL, document_id VARCHAR NOT NULL, publication_name VARCHAR, publication_year INTEGER, doi VARCHAR(240), inspire_id VARCHAR(16), title VARCHAR, PRIMARY KEY (id))",
    "CREATE TABLE pdginfo (id INTEGER NOT NULL, name VARCHAR NOT NULL, value VARCHAR, PRIMARY KEY (id), UNIQUE (name))",
    "CREATE TABLE pdgid (id INTEGER NOT NULL, pdgid VARCHAR NOT NULL, parent_id INTEGER, parent_pdgid VARCHAR, description VARCHAR NOT NULL, mode_number INTEGER, data_type VARCHAR(4) NOT NULL, flags VARCHAR(8) NOT NULL, year_added INTEGER, sort INTEGER NOT NULL, PRIMARY KEY (id), UNIQUE (pdgid), FOREIGN KEY(parent_id) REFERENCES pdgid (id))",
    "CREATE TABLE pdgitem (id INTEGER NOT NULL, name VARCHAR NOT NULL, item_type VARCHAR(1) NOT NULL, PRIMARY KEY (id))",
    "CREATE TABLE pdgfootnote (id INTEGER NOT NULL, pdgid VARCHAR, text VARCHAR, footnote_index INTEGER, changebar BOOLEAN, PRIMARY KEY (id), CHECK (changebar IN (0, 1)))",
    "CREATE TABLE pdgid_map (id INTEGER NOT NULL, source_id INTEGER NOT NULL, source VARCHAR, target_id INTEGER NOT NULL, target VARCHAR, type VARCHAR(1), sort INTEGER, PRIMARY KEY (id), FOREIGN KEY(source_id) REFERENCES pdgid (id), FOREIGN KEY(target_id) REFERENCES pdgid (id))",
    "CREATE TABLE pdgdecay (id INTEGER NOT NULL, pdgid_id INTEGER NOT NULL, pdgid VARCHAR NOT NULL, pdgitem_id INTEGER NOT NULL, name VARCHAR NOT NULL, is_outgoing BOOLEAN NOT NULL, multiplier INTEGER NOT NULL, subdecay_id INTEGER, sort INTEGER NOT NULL, PRIMARY KEY (id), FOREIGN KEY(pdgid_id) REFERENCES pdgid (id), FOREIGN KEY(pdgitem_id) REFERENCES pdgitem (id), CHECK (is_outgoing IN (0, 1)), FOREIGN KEY(subdecay_id) REFERENCES pdgid (id))",
    "CREATE TABLE pdgtext (id INTEGER NOT NULL, pdgid_id INTEGER NOT NULL, pdgid VARCHAR NOT NULL, text VARCHAR, type VARCHAR(1) NOT NULL, sort INTEGER NOT NULL, PRIMARY KEY (id), FOREIGN KEY(pdgid_id) REFERENCES pdgid (id))",
    "CREATE TABLE pdgmeasurement (id INTEGER NOT NULL, pdgid_id INTEGER NOT NULL, pdgid VARCHAR NOT NULL, pdgreference_id INTEGER NOT NULL, event_count VARCHAR(20), confidence_level FLOAT, place VARCHAR(1), technique VARCHAR(4), charge VARCHAR(3), changebar BOOLEAN, comment VARCHAR, sort INTEGER NOT NULL, PRIMARY KEY (id), FOREIGN KEY(pdgid_id) REFERENCES pdgid (id), FOREIGN KEY(pdgreference_id) REFERENCES pdgreference (id), CHECK (changebar IN (0, 1)))",
    "CREATE TABLE pdgparticle (id INTEGER NOT NULL, pdgid_id INTEGER NOT NULL, pdgid VARCHAR NOT NULL, pdgitem_id INTEGER NOT NULL, name VARCHAR NOT NULL, cc_type VARCHAR(1), mcid INTEGER, charge FLOAT, quantum_i VARCHAR(40), quantum_g VARCHAR(1), quantum_j VARCHAR(40), quantum_p VARCHAR(1), quantum_c VARCHAR(1), PRIMARY KEY (id), FOREIGN KEY(pdgid_id) REFERENCES pdgid (id), FOREIGN KEY(pdgitem_id) REFERENCES pdgitem (id), UNIQUE (mcid))",
    "CREATE TABLE pdgitem_map (id INTEGER NOT NULL, pdgitem_id INTEGER NOT NULL, name VARCHAR NOT NULL, target_id INTEGER NOT NULL, sort INTEGER NOT NULL, PRIMARY KEY (id), FOREIGN KEY(pdgitem_id) REFERENCES pdgitem (id), FOREIGN KEY(target_id) REFERENCES pdgitem (id))",
    "CREATE TABLE pdgdata (id INTEGER NOT NULL, pdgid_id INTEGER NOT NULL, pdgid VARCHAR NOT NULL, edition VARCHAR, value_type VARCHAR(2) NOT NULL, in_summary_table BOOLEAN NOT NULL, confidence_level FLOAT, limit_type VARCHAR(1), comment VARCHAR, value FLOAT, value_text VARCHAR, error_positive FLOAT, error_negative FLOAT, scale_factor FLOAT, unit_text VARCHAR NOT NULL, display_value_text VARCHAR NOT NULL, display_power_of_ten INTEGER NOT NULL, display_in_percent BOOLEAN NOT NULL, sort INTEGER, PRIMARY KEY (id), FOREIGN KEY(pdgid_id) REFERENCES pdgid (id), CHECK (in_summary_table IN (0, 1)), CHECK (display_in_percent IN (0, 1)))",
    "CREATE TABLE pdgmeasurement_footnote (id INTEGER NOT NULL, pdgmeasurement_id INTEGER NOT NULL, pdgfootnote_id INTEGER NOT NULL, PRIMARY KEY (id), FOREIGN KEY(pdgmeasurement_id) REFERENCES pdgmeasurement (id), FOREIGN KEY(pdgfootnote_id) REFERENCES pdgfootnote (id))",
    "CREATE TABLE pdgmeasurement_values (id INTEGER NOT NULL, pdgmeasurement_id INTEGER NOT NULL, column_name VARCHAR, value_text VARCHAR, unit_text VARCHAR, display_value_text VARCHAR, display_power_of_ten INTEGER, display_in_percent BOOLEAN, limit_type VARCHAR(1), used_in_average BOOLEAN, used_in_fit BOOLEAN, value FLOAT, error_positive FLOAT, error_negative FLOAT, stat_error_positive FLOAT, stat_error_negative FLOAT, syst_error_positive FLOAT, syst_error_negative FLOAT, sort INTEGER NOT NULL, PRIMARY KEY (id), FOREIGN KEY(pdgmeasurement_id) REFERENCES pdgmeasurement (id), CHECK (display_in_percent IN (0, 1)), CHECK (used_in_average IN (0, 1)), CHECK (used_in_fit IN (0, 1)))",
    'CREATE TABLE "elements" ( "atomicnumber" INTEGER, "massnumber" INTEGER, "name" TEXT NOT NULL, "symbol" TEXT NOT NULL, "atomicweight" REAL, "density" REAL, "meltingpoint" REAL, "boilingpoint" REAL, "egroup" INTEGER, "periodo" INTEGER, "block" TEXT, "category" TEXT, "application" TEXT, "econfig" TEXT, PRIMARY KEY("atomicnumber") )'
]


def get_chroma_client():
    # Ensure the chroma_data directory exists
    if not os.path.exists(CHROMA_DATA_PATH):
        os.makedirs(CHROMA_DATA_PATH)
        # print(f"Created directory: {CHROMA_DATA_PATH}") # Debug: uncomment for logs
    # else:
        # print(f"Directory already exists: {CHROMA_DATA_PATH}") # Debug: uncomment for logs

    client = chromadb.PersistentClient(path=CHROMA_DATA_PATH)
    return client

def get_particles_collection(client=None):
    if client is None:
        client = get_chroma_client()
    collection = client.get_or_create_collection(name=COLLECTION_NAME)
    return collection

def parse_ddl_statements(ddl_statements: list[str]) -> dict:
    parsed_schemas = {}
    table_name_re = re.compile(r"CREATE TABLE\s+(?:IF NOT EXISTS\s+)?\"?(\w+)\"?\s*\(", re.IGNORECASE)

    for stmt_idx, stmt in enumerate(ddl_statements):
        table_match = table_name_re.search(stmt)
        if not table_match:
            continue

        table_name = table_match.group(1).replace('"', '')
        parsed_schemas[table_name] = {"columns": [], "primary_key": [], "foreign_keys": [], "unique_constraints": [], "check_constraints": []}

        body_match = re.search(r"\((.*)\)", stmt, re.DOTALL | re.IGNORECASE)
        if not body_match:
            continue

        body = body_match.group(1).strip()

        definitions = []
        balance = 0
        current_def = ""
        # Iterate char by char to correctly split definitions by comma, respecting parentheses.
        for char_idx, char in enumerate(body):
            if char == '(':
                balance += 1
            elif char == ')':
                balance -= 1

            if char == ',' and balance == 0: # Split point
                definitions.append(current_def.strip())
                current_def = ""
            else:
                current_def += char

            if char_idx == len(body) -1: # Add the last definition after loop
                 definitions.append(current_def.strip())

        for def_idx, definition in enumerate(definitions):
            definition = definition.strip()
            if not definition:
                continue

            # Try to parse as column definition (name, type, and inline constraints)
            # Regex handles quoted/unquoted names, various types including varchar(n), and common inline constraints.
            col_match = re.match(
                r'\"?(\w+)\"?\s+'                                                                # Column name (group 1)
                r"((?:VARCHAR|INTEGER|TEXT|REAL|BOOLEAN|FLOAT|DATETIME|BLOB|NUMERIC)(?:\(\s*\d+\s*(?:,\s*\d+)?\s*\))?)"  # Type (group 2)
                r"((?:\s+NOT\s+NULL)?)"                                                         # NOT NULL (group 3)
                r"((?:\s+UNIQUE)?)"                                                             # UNIQUE (group 4)
                r"((?:\s+PRIMARY\s+KEY)?)"                                                      # PRIMARY KEY (group 5)
                r"((?:\s+CHECK\s*\(.*?\))?)"                                                    # Inline CHECK (group 6) - basic
                r"((?:\s+DEFAULT\s+.*?Z)?)"                                                 # Inline DEFAULT (group 7) - basic
                , definition, re.IGNORECASE
            )

            if col_match:
                col_name = col_match.group(1).replace('"', '')
                col_type = col_match.group(2)
                is_not_null = bool(col_match.group(3) and col_match.group(3).strip()) #is_not_null = "NOT NULL" in col_match.group(3).upper() if col_match.group(3) else False
                is_unique = bool(col_match.group(4) and col_match.group(4).strip()) #is_unique = "UNIQUE" in col_match.group(4).upper() if col_match.group(4) else False
                is_pk = bool(col_match.group(5) and col_match.group(5).strip()) #is_pk = "PRIMARY KEY" in col_match.group(5).upper() if col_match.group(5) else False

                col_info = {"name": col_name, "type": col_type}
                if is_not_null: col_info["not_null"] = True
                if is_unique: # If inline UNIQUE constraint
                    col_info["unique"] = True
                    # Add to table's unique constraints list if not already present from a table-level UNIQUE constraint
                    if [col_name] not in parsed_schemas[table_name]["unique_constraints"]:
                         parsed_schemas[table_name]["unique_constraints"].append([col_name])
                if is_pk: # If inline PRIMARY KEY constraint
                    col_info["primary_key_inline"] = True # Mark that this column is part of PK, potentially composite
                    # Add to table's primary key list if not already present
                    if col_name not in parsed_schemas[table_name]["primary_key"]:
                         parsed_schemas[table_name]["primary_key"].append(col_name)
                # TODO: Capture and store inline CHECK and DEFAULT constraints if regex is expanded

                parsed_schemas[table_name]["columns"].append(col_info)

            # Table-level PRIMARY KEY constraint
            elif definition.upper().startswith("PRIMARY KEY"):
                pk_match = re.search(r"PRIMARY KEY\s*\((.+?)\)", definition, re.IGNORECASE) # Non-greedy match for columns
                if pk_match:
                    pk_cols_str = pk_match.group(1)
                    # Split columns, strip whitespace and remove quotes
                    pk_cols = [col.strip().replace('"', '') for col in pk_cols_str.split(',')]
                    # Overwrite or initialize primary_key list for the table
                    parsed_schemas[table_name]["primary_key"] = pk_cols

            # Table-level UNIQUE constraint
            elif definition.upper().startswith("UNIQUE"):
                unique_match = re.search(r"UNIQUE\s*\((.+?)\)", definition, re.IGNORECASE) # Non-greedy
                if unique_match:
                    unique_cols_str = unique_match.group(1)
                    unique_cols = [col.strip().replace('"', '') for col in unique_cols_str.split(',')]
                    # Append to unique_constraints list
                    if unique_cols not in parsed_schemas[table_name]["unique_constraints"]:
                        parsed_schemas[table_name]["unique_constraints"].append(unique_cols)

            # FOREIGN KEY constraint
            elif definition.upper().startswith("FOREIGN KEY"):
                fk_match = re.search(r"FOREIGN KEY\s*\((.+?)\)\s*REFERENCES\s*\"?(\w+)\"?\s*\((.+?)\)", definition, re.IGNORECASE) # Non-greedy
                if fk_match:
                    fk_from_cols = [col.strip().replace('"', '') for col in fk_match.group(1).split(',')]
                    fk_ref_table = fk_match.group(2).replace('"', '') # Already unquoted by capture group
                    fk_ref_cols = [col.strip().replace('"', '') for col in fk_match.group(3).split(',')]
                    fk_info = {
                        "columns": fk_from_cols,
                        "references_table": fk_ref_table,
                        "references_columns": fk_ref_cols,
                        "raw_definition": definition # Store raw for debugging or richer parsing later
                    }
                    parsed_schemas[table_name]["foreign_keys"].append(fk_info)

            # CHECK constraint (table-level or uncaptured inline)
            elif definition.upper().startswith("CHECK"):
                check_match = re.search(r"CHECK\s*\((.+)\)", definition, re.IGNORECASE) # Greedy, as check can be complex
                if check_match:
                    check_constraint_expression = check_match.group(1)
                    parsed_schemas[table_name]["check_constraints"].append(check_constraint_expression)
    return parsed_schemas


def format_constraints(column_info):
    constraints = []
    if column_info.get("not_null"):
        constraints.append("NOT NULL")
    if column_info.get("unique"):
        constraints.append("UNIQUE")
    if column_info.get("primary_key_inline"): # Check if column itself is part of PK (from inline def)
        constraints.append("PRIMARY KEY part")
    # Note: table-level PKs are in parsed_schemas[table_name]["primary_key"]
    return ", ".join(constraints)

def populate_schema_in_chromadb(collection=None, parsed_schemas=None):
    if collection is None:
        collection = get_particles_collection()

    if parsed_schemas is None:
        parsed_schemas = parse_ddl_statements(ALL_DDL_STATEMENTS)

    existing_ids_to_delete = []
    for table_name in parsed_schemas:
        existing_ids_to_delete.append(f"table_schema_{table_name}")
        for column in parsed_schemas[table_name].get("columns", []):
            existing_ids_to_delete.append(f"col_schema_{table_name}_{column['name']}")

    if existing_ids_to_delete:
        try:
            existing_docs_check = collection.get(ids=existing_ids_to_delete, include=[]) # Only check IDs
            if existing_docs_check and existing_docs_check['ids']:
                 collection.delete(ids=existing_docs_check['ids'])
        except Exception as e:
            # print(f"Note: Could not verify/delete schema documents during populate (may not exist yet): {e}")
            pass


    documents = []
    metadatas = []
    ids = []
    doc_count = 0

    for table_name, table_info in parsed_schemas.items():
        col_names = [col["name"] for col in table_info.get("columns", [])]
        # Use table_info["primary_key"] which holds table-level PK list
        pk_info = ", ".join(table_info.get("primary_key", []))

        table_doc_content = f"Table: {table_name}. Columns: {', '.join(col_names)}. Primary Key: {pk_info}."
        if table_info.get("foreign_keys"):
            table_doc_content += f" Foreign Keys: {len(table_info['foreign_keys'])}."
        if table_info.get("unique_constraints"):
            table_doc_content += f" Unique Constraints: {len(table_info['unique_constraints'])}."

        ids.append(f"table_schema_{table_name}")
        documents.append(table_doc_content)
        metadatas.append({"type": "table_schema", "table_name": table_name, "source": "ddl_parser"})
        doc_count += 1

        for column in table_info.get("columns", []):
            # Pass full column dict to format_constraints
            col_constraints = format_constraints(column)
            col_doc_content = f"Column: {column['name']} in table {table_name}. Type: {column['type']}."
            if col_constraints:
                col_doc_content += f" Constraints: {col_constraints}."

            ids.append(f"col_schema_{table_name}_{column['name']}")
            documents.append(col_doc_content)
            metadatas.append({
                "type": "column_schema",
                "table_name": table_name,
                "column_name": column['name'],
                "data_type": column['type'],
                "source": "ddl_parser"
            })
            doc_count +=1

    if documents:
        collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
    return doc_count


if __name__ == '__main__':
    print("--- ChromaDB Client and Collection Test (Original) ---")
    test_client = None
    # test_collection_original = None # Renamed to avoid confusion
    try:
        test_client = get_chroma_client()
        # Clean up collection before original test to ensure it runs as expected
        try:
            test_client.delete_collection(name=COLLECTION_NAME)
        except Exception:
            pass # Ignore if not exists

        test_collection_original = get_particles_collection(test_client) # This re-creates it
        test_collection_original.add(
            ids=["test_id_001_original_main"], # Changed ID
            documents=["This is a test document for chroma_utils original main."],
            metadatas=[{"source": "chroma_utils_original_main_test"}]
        )
        retrieved = test_collection_original.get(ids=["test_id_001_original_main"])
        print(f"Original test retrieved: {retrieved['documents'][0][:50]}...") # Print snippet
    except Exception as e:
        print(f"ERROR during original ChromaDB client/collection test in main: {e}")
    # No finally delete here for the original test part, new test part will manage its state.

    print("\n--- DDL Parsing Test (Original Main) ---")
    parsed_schema_data = parse_ddl_statements(ALL_DDL_STATEMENTS) # This is used by new test too
    print(f"Original Main: Parsed {len(parsed_schema_data)} DDL statements.")
    # Example: print(json.dumps(parsed_schema_data.get("pdgitem", {}), indent=2))
    print("--- End of DDL Parsing Test (Original Main) ---")

    # Schema Population Test
    print("\n--- Schema Population in ChromaDB Test ---")
    if 'test_client' not in locals() or test_client is None:
        print("ERROR: test_client not defined from original main block. Re-initializing.")
        test_client = get_chroma_client() # Ensure it's available

    # Ensure the "particles" collection is clean for this specific test part
    try:
        print(f"Test: Attempting to delete collection '{COLLECTION_NAME}' before schema population test...")
        test_client.delete_collection(name=COLLECTION_NAME)
        print(f"Test: Collection '{COLLECTION_NAME}' deleted for a clean schema population test run.")
    except Exception as e_del_main_test:
        print(f"Test: Note: Collection '{COLLECTION_NAME}' could not be deleted (may not exist yet): {e_del_main_test}")

    test_collection_for_schema = get_particles_collection(test_client) # Get a fresh collection

    num_docs_added = populate_schema_in_chromadb(collection=test_collection_for_schema, parsed_schemas=parsed_schema_data)
    print(f"Populated {num_docs_added} schema documents into ChromaDB.")

    results_table = test_collection_for_schema.query(
        query_texts=["information about pdgitem table"],
        n_results=2,
        where={"type": "table_schema"},
        include=["documents", "metadatas"]
    )
    print(f"Schema query results for 'pdgitem table': {results_table['documents']}")

    results_cols = test_collection_for_schema.query(
        query_texts=["column named id in pdgitem"],
        n_results=1,
            where={
                "$and": [
                    {"type": {"$eq": "column_schema"}},
                    {"table_name": {"$eq": "pdgitem"}},
                    {"column_name": {"$eq": "id"}}
                ]
            }, # More specific filter
        include=["documents", "metadatas"]
    )
    print(f"Schema query results for 'column id in pdgitem': {results_cols['documents']}")
    print("--- End of Schema Population Test ---")

    # Final cleanup of the test collection used by this main block
    # if test_client:
    #     try:
    #         print(f"\nMain block: Attempting final cleanup of collection '{COLLECTION_NAME}'...")
    #         test_client.delete_collection(name=COLLECTION_NAME)
    #         print(f"Main block: Collection '{COLLECTION_NAME}' deleted after all tests.")
    #     except Exception as e_final_clean:
    #         print(f"Main block: Error deleting collection '{COLLECTION_NAME}' post-tests: {e_final_clean}")

    print(f"\nOverall main test execution completed. Last parsed DDL count: {len(parsed_schema_data)} tables.")
