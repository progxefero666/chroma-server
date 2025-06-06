from flask import Flask, render_template
from api import api_bp
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.register_blueprint(api_bp)

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
