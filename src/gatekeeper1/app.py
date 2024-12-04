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



@app.route('/new_request', methods=["POST"])
def new_request():
    data = request.json

    query = data.get("query")
    
    try:
        
        with open('instance_details.json', 'r') as file:
            instance_details = json.load(file)
    
        gatekeeper2_ip = ''
    
        for instance in instance_details:
            if instance['Name'] == 'gatekeeper2':
                gatekeeper2_ip = instance['PublicIP']
        
        app.logger.info(f"Sending request to: {gatekeeper2_ip}")
        url = f"http://{gatekeeper2_ip}:80/process_query"

        resp = requests.post(url, json=data)

        if resp.status_code == 200:
            return resp.json()
        else:
            return jsonify({
                "message": "Error",
                "error": resp.text
            }), resp.status_code

    except requests.RequestException as e:
        return jsonify({
            "message": "Error",
            "error": str(e)}), 500
        
    

@app.route('/')
def hello_world():
    #return jsonify({"message": "Request processed.", "response": "Hello World"})
    return 'Hello World!'


if __name__ == "__main__":    
    app.debug = True
    app.run(host='0.0.0.0', port=80)
