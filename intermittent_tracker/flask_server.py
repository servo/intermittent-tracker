from flask import Flask, request, jsonify
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
        return True

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

@app.route('/dashboard/test')
def dashboard_test():
    return dashboard.test(request)

@app.route('/dashboard/attempts', methods=['POST'])
@auth.login_required
def dashboard_post_attempts():
    return dashboard.post_attempts(request)

@app.route('/')
def index():
    return "Hi!"

def main():
    DashboardDB.migrate()
    app.run(port=config['port'])

if __name__ == "__main__":
    main()
