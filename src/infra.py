from aws_setup import create_vpc_and_subnet, create_security_groups
from ec2_manager import create_instances#, wait_for_instances
from app_deployment import deploy_pattern_app#, deploy_worker_apps
from app_deployment_mysql import deploy_mysql
from create_keypair import create_keypair
#from capture_aws_credentials import get_aws_credentials
from mainsql import mainsql
import requests
import boto3
import ipaddress
import json
import constants
import time
import shutil

def get_local_ip_cidr ():
    response = requests.get('https://api.ipify.org')
    public_ip = response.text.strip()
    subnet_mask = '255.255.255.0'
    cidr_network = ipaddress.ip_network(f"{public_ip}/{subnet_mask}", strict=False)

    return str(cidr_network)

#def load_json(filename):
#    with open(filename, 'r') as file:
#        return json.load(file)

def save_json(data, filename):
    with open(filename, 'w') as file:
        json.dump(data, file, indent=4)


def get_public_ip (ec2_client, instance_id):
    try:
        response = ec2_client.describe_instances(InstanceIds=[instance_id])
        public_ip = response['Reservations'][0]['Instances'][0].get('PublicIpAddress')

        if public_ip:
            return public_ip
        
        else:
            print(f"Instance {instance_id} does not have a public IP address.")
            return None
    
    except Exception as e:
        print(f"An error occurred: {e}")
        return None



def main():
    ec2 = boto3.resource('ec2', region_name='us-east-1')
    ec2_client = boto3.client('ec2', region_name='us-east-1')

    #create keypair
    keypair = create_keypair (ec2_client, "PYC_LOG8415E_Assignment3_keypair")
    
    #get local machine IP for SSH
    my_ip_cidr = get_local_ip_cidr()

    # Set up VPC, subnet, and security groups
    vpc, vpc_id, subnet = create_vpc_and_subnet(ec2_client, ec2)
    gk_sg, th_sg, pm_sg, cluster_sg = create_security_groups(ec2_client, vpc_id, my_ip_cidr)
    
    # Launch EC2 instances
    cluster_instances = create_instances(ec2, constants.MICRO_TYPE, constants.CLUSTER_COUNT, subnet, cluster_sg, 'Cluster', keypair)
    gatekeeper1_instance = create_instances(ec2, constants.LARGE_TYPE, constants.PATTERN_COUNT, subnet, gk_sg, 'Pattern', keypair)[0]
    gatekeeper2_instance = create_instances(ec2, constants.LARGE_TYPE, constants.PATTERN_COUNT, subnet, th_sg, 'Pattern', keypair)[0]
    proxy_instance = create_instances(ec2, constants.LARGE_TYPE, constants.PATTERN_COUNT, subnet, pm_sg, 'Pattern', keypair)[0]
  
    
    time.sleep(60)

    instance_data = []
 
    for i, instance in enumerate(cluster_instances, start=1):
        instance.wait_until_running()
        instance.load()
        if i==1:
            instance_name = f'manager{i}'
        else:
            instance_name = f'worker{i}'
 
        instance.create_tags(Tags=[{'Key': 'Name', 'Value': instance_name}])
 
        instance_info = {
            'Name': instance_name,
            'InstanceID': instance.id,
            'PublicDNS': instance.public_dns_name,
            'PublicIP': instance.public_ip_address
        }

        instance_data.append(instance_info)
    
    
    gatekeeper1_instance.wait_until_running()
    gatekeeper1_instance.load()
    gatekeeper1_instance_name = 'gatekeeper1'
    gatekeeper1_instance.create_tags(Tags=[{'Key': 'Name', 'Value': gatekeeper1_instance_name}])
    gatekeeper1_instance_info = {
        'Name': gatekeeper1_instance_name,
        'InstanceID': gatekeeper1_instance.id,
        'PublicDNS': gatekeeper1_instance.public_dns_name,
        'PublicIP': gatekeeper1_instance.public_ip_address
    }
    
    instance_data.append(gatekeeper1_instance_info)
    
    
    gatekeeper2_instance.wait_until_running()
    gatekeeper2_instance.load()
    gatekeeper2_instance_name = 'gatekeeper2'
    gatekeeper2_instance.create_tags(Tags=[{'Key': 'Name', 'Value': gatekeeper2_instance_name}])
    gatekeeper2_instance_info = {
        'Name': gatekeeper2_instance_name,
        'InstanceID': gatekeeper2_instance.id,
        'PublicDNS': gatekeeper2_instance.public_dns_name,
        'PublicIP': gatekeeper2_instance.public_ip_address
    }
    
    instance_data.append(gatekeeper2_instance_info)
    
    
    proxy_instance.wait_until_running()
    proxy_instance.load()
    proxy_instance_name = 'proxy'
    proxy_instance.create_tags(Tags=[{'Key': 'Name', 'Value': proxy_instance_name}])
    proxy_instance_info = {
        'Name': proxy_instance_name,
        'InstanceID': proxy_instance.id,
        'PublicDNS': proxy_instance.public_dns_name,
        'PublicIP': proxy_instance.public_ip_address
    }
    
    instance_data.append(proxy_instance_info)

    save_json (instance_data, "instance_details.json")
    print("Instance details saved to instance_details.json")
    
    # copy the contents of the demo.py file to  a new file called demo1.py
    shutil.copyfile('./instance_details.json', './gatekeeper1/instance_details.json')
    shutil.copyfile('./instance_details.json', './gatekeeper2/instance_details.json')
    shutil.copyfile('./instance_details.json', './proxy/instance_details.json')
    
    #orchestrator_instance.wait_until_running()
    #orchestrator_instance.load()
    #orchestrator_instance_name = 'orchestrator'
    #orchestrator_instance.create_tags(Tags=[{'Key': 'Name', 'Value': orchestrator_instance_name}])
    #orchestrator_instance_info = {
    #    'Name': orchestrator_instance_name,
    #    'InstanceID': orchestrator_instance.id,
    #    'PublicDNS': orchestrator_instance.public_dns_name,
    #    'PublicIP': orchestrator_instance.public_ip_address
    #}
    
    #instance_data.append(orchestrator_instance_info)

    #save_json (instance_data, "instance_details.json")
    #print("Instance details saved to instance_details.json")
    
    #instance_details_data = load_json('instance_details.json')

    #workers_data = load_json('../orchestrator/workers.json')

    #for i, worker in enumerate(workers_data):
    #    dns = instance_details_data[i%4]['PublicDNS']
    #    container_i = f"container{i+1}"
    #    workers_data[container_i]['ip'] = dns
    
    # Save the updated data back to workers.json
    #save_json(workers_data, '../orchestrator/workers.json')
    
    #print("Workers json file has been updated with infra PublicDNSs.")
        
    
    #deploy_worker_apps()
    
    
    deploy_mysql()
    deploy_pattern_app()
    mainsql()
    
if __name__ == "__main__":
    main()