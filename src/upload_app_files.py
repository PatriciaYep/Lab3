import paramiko  
import os 
import json
 
def upload_directory(ssh_client, local_directory):
    
    local_absolute_path = os.path.abspath(local_directory)
    
    # Start SFTP session
    sftp = ssh_client.open_sftp()
    
    print(f"Uploading files in {local_absolute_path}")

    try:
        for item in os.listdir(local_directory):
            local_path = os.path.join(local_absolute_path, item)
            #remote_app_path = f"/home/ubuntu/{local_path.split('/')[-1]}"   
            remote_app_path = f"/home/ubuntu/{item}"                
            print('remote_app_path',remote_app_path)
            print(f"Uploading {local_path} to {remote_app_path}")
            
            sftp.put(local_path, remote_app_path)
            
            print(f"Uploaded {local_path} to {remote_app_path}")

    finally:
        sftp.close()  # Close the SFTP session 
   
def main(): 
    #Specify the instance IDs
    with open('instance_details.json', 'r') as file:
         instance_details = json.load(file)
 
    instance_ids = []
    instance_names = []
    public_ips = []
    for instance in instance_details:
        if 'gatekeeper' in instance['Name'] or 'proxy' in instance['Name']:
            instance_ids.append(instance['InstanceID'])
            instance_names.append(instance['Name'])
            public_ips.append(instance['PublicIP'])

    print(instance_ids)
    print(instance_names)
    print(public_ips)
    
    for i, ip in enumerate (public_ips):
        setup_deployment (instance_names[i], ip, instance_ids[i])
      
      
def setup_deployment (path, public_ip, instance_id):
    try:
        print(f"Connecting to {public_ip} for {instance_id} in {path}...")

        # Initialize SSH client
        private_key_path = 'PYC_LOG8415E_Assignment3_keypair.pem'
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(public_ip, username='ubuntu', key_filename=private_key_path)

        print(f"Connected to {public_ip} for {instance_id} in {path}...")
        
        upload_directory (ssh, path)
        
        print(f"Completed uploading files for {public_ip} in {path}...")
        
    except Exception as e:
        print(f"Error deploying to {public_ip}: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    main()