from flask import Flask, request, jsonify
from . import query, webhook, dashboard
import json

app = Flask(__name__)

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

# TODO authenticate requests for this endpoint
@app.route('/dashboard/attempts', methods=['POST'])
def dashboard_post_attempts():
    return dashboard.post_attempts(request)

@app.route('/')
def index():
    return "Hi!"

def main():
    with open('config.json') as f:
        config = json.loads(f.read())
        assert('port' in config)
    app.run(port=config['port'])

if __name__ == "__main__":
    main()
