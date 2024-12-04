import paramiko
import os
import json
import time

def upload_directory(ssh_client, local_directory):
    """
    uploads an entire directory to the remote server via sftp.

    :param ssh_client: the ssh client object.
    :param local_directory: the local directory to upload.
    """
    #if local_directory == "cluster":
    #    local_directory = "../cluster"

    local_absolute_path = os.path.abspath(local_directory)
    
    # start sftp session
    sftp = ssh_client.open_sftp()
    
    print(f"uploading files in {local_absolute_path}")

    try:
        for item in os.listdir(local_directory):
            local_path = os.path.join(local_absolute_path, item)
            #remote_app_path = f"/home/sakila/{item}"   
            remote_app_path = f"{item}"                            
            #print('remote_app_path',remote_app_path)
            print(f"uploading {local_path} to {remote_app_path}")
            
            sftp.put(local_path, remote_app_path)
            
            print(f"uploaded {local_path} to {remote_app_path}")

    finally:
        sftp.close()  # close the sftp session


def mysql_deployment (path, public_ip, instance_id):
    # without output display
    install_commands1 = [
        # Install mysql standalone and Sakila DB
        "sudo echo 'debconf debconf/frontend select Noninteractive' | sudo debconf-set-selections",
        'sudo apt-get update && sudo apt-get upgrade -y',
        # Install MySQL Server in a Non-Interactive mode. Default root password will be "root"
        'sudo echo "mysql-server mysql-server/root_password password root" | sudo debconf-set-selections',
        'sudo echo "mysql-server mysql-server/root_password_again password root" | sudo debconf-set-selections',
        'sudo apt-get -y install mysql-server',
        'sudo apt-get install mysql-client',
        #'sudo mysql --host=127.0.0.1 --user=root --password=root',
        'sudo mysql --host=127.0.0.1 --user=root --password=root < sakila-schema.sql',
        'sudo mysql --host=127.0.0.1 --user=root --password=root < sakila-data.sql',
        # Run the MySQL Secure Installation wizard
        #'mysql_secure_installation'
    ]
    # with output display
    install_commands2 = [
        'sudo mysql -u root -proot -e "SHOW DATABASES"',
        # Sysbench
        'sudo apt-get install sysbench -y',
        'sudo sysbench /usr/share/sysbench/oltp_read_only.lua --mysql-db=sakila --mysql-user="root" --mysql-password="root" prepare',
        'sudo sysbench /usr/share/sysbench/oltp_read_only.lua --mysql-db=sakila --mysql-user="root" --mysql-password="root" run'
    ]

    try:
        print(f"Connecting to {public_ip} for {instance_id} in {path}...")

        # Initialize SSH client
        private_key_path = 'PYC_LOG8415E_Assignment3_keypair.pem'
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(public_ip, username='ubuntu', key_filename=private_key_path)

        print(f"Connected to {public_ip} for {instance_id} in {path}...")
        
        print(f"Uploading files for {public_ip} in {path}...")
        upload_directory (ssh, path) 
        print(f"Completed uploading files for {public_ip} in {path}...")

        for install_command in install_commands1:
            print(f"Running {install_command} ...") 
            stdin, stdout, stderr = ssh.exec_command(install_command)
            stdout.channel.recv_exit_status()  # Wait for the command to finish
        
            print(f"Completed running {install_command} ...")    
            
            # output = stdout.read().decode()
            # error_output = stderr.read().decode()

            # if output:
            #     print(f"Output from {install_command}:")
            #     print(f"{output}")
            # if error_output:
            #     print(f"Error from {install_command}:")
            #     print(f"{error_output}")
        
        for install_command in install_commands2:
            print(f"Running {install_command} ...") 
            stdin, stdout, stderr = ssh.exec_command(install_command)
            stdout.channel.recv_exit_status()  # Wait for the command to finish
        
            print(f"Completed running {install_command} ...")    
            
            output = stdout.read().decode()
            error_output = stderr.read().decode()

            if output:
                print(f"Output from {install_command}:")
                print(f"{output}")
            if error_output:
                print(f"Error from {install_command}:")
                print(f"{error_output}")



        print(f"Completed running start commands for {public_ip} in {path}...")
        
        #upload_directory (ssh, path)
        
        #print(f"Completed uploading files for {public_ip} in {path}...")
        

        #print(f"Starting docker containers for {public_ip} in {path}...")

        #start_command = "sudo docker-compose up --build -d"
        #stdin, stdout, stderr = ssh.exec_command(start_command)
        #stdout.channel.recv_exit_status()  # Wait for the command to finish

        #print(f"Docker app deployed and running on {public_ip} for {path}")
        #output = stdout.read().decode()
        #error_output = stderr.read().decode()

        #if output:
            #print(f"Output from {start_command}:")
            #print(f"{output}")
        #if error_output:
            #print(f"Error from {start_command}:")
            #print(f"{error_output}")
    
    except Exception as e:
        print(f"Error deploying to {public_ip}: {e}")
    finally:
        ssh.close()



def deploy_mysql():
    #Specify the instance IDs
    with open('instance_details.json', 'r') as file:
         instance_details = json.load(file)
 
    instance_ids = []
    public_ips = []
    for instance in instance_details:
        if 'manager' in instance['Name'] or 'worker' in instance['Name']:
            instance_ids.append(instance['InstanceID'])
            public_ips.append(instance['PublicIP'])


    print(instance_ids)
    print(public_ips)

    for i, ip in enumerate (public_ips):
        mysql_deployment ("cluster", ip, instance_ids[i])