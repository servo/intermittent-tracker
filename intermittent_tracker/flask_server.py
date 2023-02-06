from flask import Flask, request, jsonify, send_from_directory
from flask_httpauth import HTTPTokenAuth
from . import query, webhook, dashboard
from .db import DashboardDB
import json

with open('config.json') as f:
    config = json.loads(f.read())
    assert(key in config for key in ['github_token', 'dashboard_secret', 'port'])

app = Flask(__name__)
auth = HTTPTokenAuth(scheme='Bearer')

@auth.verify_token
def authenticate(token):
    if token == config['dashboard_secret']:
        # returning just True makes HTTPTokenAuth.current_user return None,
        # making it impossible to use @auth.login_required(optional=True).
        return {'ok':True}

@app.route("/query.py")
def querypy():
    if 'name' not in request.args:
        return ("{}", 400)
    return jsonify(query.query(request.args['name']))

@app.route("/webhook.py", methods=["POST"])
def webhookpy():
    webhook.handler(request.form.get('payload', '{}'))
    return ('', 204)

@app.route('/dashboard/tests')
def dashboard_tests():
    return dashboard.tests(request)

@app.route('/dashboard/attempts', methods=['GET', 'POST'])
@auth.login_required(optional=True)
def dashboard_post_attempts():
    if request.method == 'POST':
        if auth.current_user() is not None:
            return dashboard.post_attempts(request)
        else:
            return ('', 401)
    else:
        return dashboard.get_attempts(request)

@app.route('/dashboard/query', methods=['POST'])
def dashboard_query():
    return dashboard.query(request)

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

def main():
    DashboardDB.migrate()
    app.run(port=config['port'])

if __name__ == "__main__":
    main()
