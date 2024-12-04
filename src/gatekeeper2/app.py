from flask import Flask, request, jsonify
import requests
import threading
import json
import time
import uuid
import config

app = Flask(__name__)
lock = threading.Lock()
responses = {}  # Dictionary to store responses
   

@app.route('/process_query', methods=["POST"])
def process_query():
    data = request.json
    try:
        with open('instance_details.json', 'r') as file:
            instance_details = json.load(file)
    
        proxy_ip = ''
    
        for instance in instance_details:
            if instance['Name'] == 'proxy':
                proxy_ip = instance['PublicIP']

        url = f"http://{proxy_ip}:80/process"
        app.logger.info(f"Sending request to proxy: {url}")

        resp = requests.post(url, json=data)

        if resp.status_code == 200:
            return resp.json()
        else:
            return jsonify({
                "message": "Error",
                "error": resp.text
            })
    except requests.RequestException as e:
        return jsonify({
            "message": "Error",
            "error": str(e) })


@app.route('/', methods=['GET'])
def hello_world():
    return jsonify({"message": "Request processed.", "response": "Hello World"})

if __name__ == "__main__":  
    app.debug = True
    app.run(host='0.0.0.0', port=80)
