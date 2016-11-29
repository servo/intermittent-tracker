from flask import Flask, request, jsonify
import query, webhook
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

if __name__ == "__main__":
    app.run()
