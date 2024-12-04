from constants import IMAGE_ID
import boto3
import base64


iam_client = boto3.client('iam')

def get_instance_profile_arn(instance_profile_name):
    try:
        # Retrieve the specified instance profile
        response = iam_client.get_instance_profile(InstanceProfileName=instance_profile_name)
        
        # Get the ARN from the response
        instance_profile_arn = response['InstanceProfile']['Arn']
        print(f"ARN of Instance Profile '{instance_profile_name}': {instance_profile_arn}")
        return instance_profile_arn

    except iam_client.exceptions.NoSuchEntityException:
        print(f"Instance profile '{instance_profile_name}' does not exist.")
        return None


def create_instances(ec2, instance_type, count, subnet, sg_id, name_tag, keyname):
    print (f"Creating instance(s) for group {name_tag} ...")
    return ec2.create_instances(
        ImageId=IMAGE_ID,  # Ubuntu AMI ID
        InstanceType=instance_type,
        KeyName=keyname,
        MaxCount=count,
        MinCount=count,
        NetworkInterfaces=[{
            'SubnetId': subnet.id,
            'DeviceIndex': 0,
            'AssociatePublicIpAddress': True,
            'Groups': [sg_id]
        }],
        BlockDeviceMappings=[{
            'DeviceName': '/dev/sda1',  # Adjust according to your AMI
            'Ebs': {
                'VolumeSize': 32,  # Size in GB
                'DeleteOnTermination': True,
                'VolumeType': 'gp2',  # General Purpose SSD
            }
        }],

        TagSpecifications=[{
            'ResourceType': 'instance',
            'Tags': [{'Key': 'Name', 'Value': f'Flask-{name_tag}'}]
        }]
    )

def wait_for_instances(ec2_client, instance_ids):
    print("Waiting for instances to be in running state...")
    waiter = ec2_client.get_waiter('instance_running')
    waiter.wait(InstanceIds=instance_ids)
    print("Instances are now running.")

def get_public_ip(instance):
    return instance.public_ip_address

def terminate_instances (ec2_client, instance_ids):
    response = ec2_client.terminate_instances (instance_ids)
    print(response)
    print("Instances are now terminated.")