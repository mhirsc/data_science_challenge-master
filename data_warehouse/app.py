"""Flask app implementing 'data_warehouse' microservice."""
from __future__ import absolute_import
from flask import Flask
from flask_restful import Api

import logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

app = Flask(__name__)
api = Api(app)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
