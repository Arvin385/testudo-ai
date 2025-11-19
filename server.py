from flask import Flask, request, jsonify
import os

app = Flask(__name__)

@app.route("/send-request", methods=['POST'])
def send_request():
    data = request.get_json()

    # data will look like this: {"query": <user_query>}
    # run data through backend and return result


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)