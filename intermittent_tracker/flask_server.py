from flask import Flask, request, jsonify
from . import query, webhook
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
