from flask import Flask, request, jsonify
import paramiko
import requests
import threading
import json
import time
import uuid

app = Flask(__name__)
lock = threading.Lock()
responses = {}  # Dictionary to store responses


def get_instance_info(instance_name):
    with open('instance_details.json', 'r') as file:
        instance_details = json.load(file)
    
    ip = ''
    id = ''
    
    for instance in instance_details:
        if instance['Name'] == instance_name:
            ip = instance['PublicIP']
            id = instance['InstanceID']
            
    return ip,id

def run_sql(path, public_ip, instance_id, list_sql):
    sql_commands=[]
    for sql in list_sql:
        command='sudo mysql -u root -proot sakila -e "'+sql+'"'
        sql_commands.append(command)
    
    #print(sql_commands)
    
    try:
        #print(f"Connecting to {public_ip} for {instance_id} in {path}...")

        # Initialize SSH client
        private_key_path = 'PYC_LOG8415E_Assignment3_keypair.pem'
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(public_ip, username='ubuntu', key_filename=private_key_path)

        #print(f"Connected to {public_ip} for {instance_id} in {path}...")

        for command in sql_commands:
            #print(f"Running {command} in {path} ...") 
            stdin, stdout, stderr = ssh.exec_command(command)
            stdout.channel.recv_exit_status()  # Wait for the command to finish
        
            #print(f"Completed running {command} ...")    
            
            # output = stdout.read().decode()
            # error_output = stderr.read().decode()

            # if output:
            #     print(f"Output from {command}:")
            #     print(f"{output}")
            # if error_output:
            #     print(f"Error from {command}:")
            #     print(f"{error_output}")
        
    except Exception as e:
        print(f"Error deploying to {public_ip}: {e}")
    finally:
        ssh.close()


@app.route('/proxy_process', methods=['GET'])

def proxy_process():
    
    manager = 'manager1'           
    workers_list = ['worker2', 'worker3']        
    
    data = request.json
    
    ip,id=get_instance_info(manager)
    run_sql(manager, ip, id, [data])
    
    return 'ok'

@app.route('/', methods=['GET'])
def hello_world():
    return jsonify({"message": "Request processed.", "response": "Hello World"})

if __name__ == "__main__":
    app.debug = True
    app.run(host='0.0.0.0', port=80)
