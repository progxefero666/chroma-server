from flask import Flask, render_template, send_from_directory
from .api import api_bp  # Changed back to relative import
import logging
import os

# Configure basic logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.register_blueprint(api_bp)

# Nueva ruta para favicon.ico
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/')
def index():
    app.logger.info("Serving index page.")
    return render_template('index.html', title='Home')

@app.route('/schema')
def schema_page():
    app.logger.info("Serving schema page.")
    return render_template('schema.html', title='Schema')

@app.route('/search')
def search_page():
    app.logger.info("Serving search page.")
    return render_template('search.html', title='Search')

@app.route('/detail')
def detail_page():
    app.logger.info("Serving detail page.")
    return render_template('detail.html', title='Detail')

if __name__ == '__main__':
    app.logger.info("Starting Flask development server.")
    app.run(host='0.0.0.0', port=8000, debug=True)
