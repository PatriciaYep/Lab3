import boto3
import json
import constants

def create_vpc_and_subnet(ec2_client, ec2):
    vpc_response = ec2_client.create_vpc(CidrBlock=constants.VPC_CIDR_BLOCK  )
    vpc_id = vpc_response['Vpc']['VpcId']
    ec2_client.create_tags(Resources=[vpc_id], Tags=[{"Key": "Name", "Value": "Flask_Docker-VPC"}])

    # Enable DNS support and DNS hostname
    ec2_client.modify_vpc_attribute(VpcId=vpc_id, EnableDnsSupport={'Value': True})
    ec2_client.modify_vpc_attribute(VpcId=vpc_id, EnableDnsHostnames={'Value': True})
    
    vpc = ec2.Vpc(vpc_id)
    vpc.wait_until_available()
    
    subnet = ec2.create_subnet(VpcId=vpc.id, CidrBlock=constants.PUBLIC_CIDR_BLOCK  )
    
    ig = ec2.create_internet_gateway()
    vpc.attach_internet_gateway(InternetGatewayId=ig.id)
    
    route_table = vpc.create_route_table()
    route_table.create_route(DestinationCidrBlock=constants.IG_DEST_CIDR_BLOCK, GatewayId=ig.id)
    route_table.associate_with_subnet(SubnetId=subnet.id)
    
    print("Created vpc and subnet...")
    return vpc, vpc_id, subnet


 
    
def create_security_groups(ec2_client, vpc_id, ssh_allowed_ip):
    try:
        
        
        # Create security group for Gatekeeper
        gk_sg = ec2_client.create_security_group(
            GroupName='GK_SG',
            Description='Gatekeeper Security Group',
            VpcId=vpc_id
        )
        gk_sg_id = gk_sg['GroupId']
        
        print(f"Created Gatekeeper Security Group: {gk_sg_id}")
        
        # Authorize inbound HTTP traffic (port 80) from anywhere for the Gatekeeper
        ec2_client.authorize_security_group_ingress(
            GroupId=gk_sg_id,
            IpPermissions=[
                {'IpProtocol': 'tcp', 'FromPort': 22, 'ToPort': 22, 'IpRanges': [{'CidrIp': ssh_allowed_ip}]},
                {'IpProtocol': 'tcp', 'FromPort': 80, 'ToPort': 80, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
                {'IpProtocol': 'tcp', 'FromPort': 443, 'ToPort': 443, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
                {'IpProtocol': 'icmp', 'FromPort': -1, 'ToPort': -1, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}
            ]
        )
        
        print(f"Ingress rules set for Gatekeeper Security Group: {gk_sg_id}")


        # Create security group for Trusted Host
        th_sg = ec2_client.create_security_group(
            GroupName='TH_SG',
            Description='Trusted host Security Group',
            VpcId=vpc_id
        )
        th_sg_id = th_sg['GroupId']
        
        print(f"Created Trusted host Security Group: {th_sg_id}")
        
        # Authorize inbound HTTP traffic (port 80) from anywhere for the Trusted host
        ec2_client.authorize_security_group_ingress(
            GroupId=th_sg_id,
            IpPermissions=[
                {'IpProtocol': 'tcp', 'FromPort': 22, 'ToPort': 22, 'IpRanges': [{'CidrIp': ssh_allowed_ip}]},
                {'IpProtocol': 'tcp', 'FromPort': 80, 'ToPort': 80, 'UserIdGroupPairs': [{'GroupId': gk_sg_id}]},
                {'IpProtocol': 'tcp', 'FromPort': 443, 'ToPort': 443, 'UserIdGroupPairs': [{'GroupId': gk_sg_id}]},
                {'IpProtocol': 'icmp', 'FromPort': -1, 'ToPort': -1, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
                {'IpProtocol': 'tcp', 'FromPort': 1024, 'ToPort': 65535, 'UserIdGroupPairs': [{'GroupId': gk_sg_id}]
                }
            ]
        )
        
        print(f"Ingress rules set for Trusted host Security Group: {th_sg_id}")



        # Create security group for Proxy manager
        pm_sg = ec2_client.create_security_group(
            GroupName='PM_SG',
            Description='Proxy manager Security Group',
            VpcId=vpc_id
        )
        pm_sg_id = pm_sg['GroupId']
        
        print(f"Created Proxy manager Security Group: {pm_sg_id}")
        
        # Authorize inbound HTTP traffic (port 80) from anywhere for the Proxy manager
        ec2_client.authorize_security_group_ingress(
            GroupId=pm_sg_id,
            IpPermissions=[
                {'IpProtocol': 'tcp', 'FromPort': 22, 'ToPort': 22, 'IpRanges': [{'CidrIp': ssh_allowed_ip}]},
                {'IpProtocol': 'tcp', 'FromPort': 80, 'ToPort': 80, 'UserIdGroupPairs': [{'GroupId': th_sg_id}]},
                {'IpProtocol': 'tcp', 'FromPort': 443, 'ToPort': 443, 'UserIdGroupPairs': [{'GroupId': th_sg_id}]},
                {'IpProtocol': 'icmp', 'FromPort': -1, 'ToPort': -1, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}

            ]
        )
        
        print(f"Ingress rules set for Proxy manager Security Group: {pm_sg_id}")


        # Create security group for the cluster
        cluster_sg = ec2_client.create_security_group(
            GroupName='Cluster_SG',
            Description='Cluster Security Group',
            VpcId=vpc_id
        )
        cluster_sg_id = cluster_sg['GroupId']
       
        print(f"Created Cluster Security Group: {cluster_sg_id}")
        
        lb_subnet_cidr = constants.PUBLIC_CIDR_BLOCK  

        ec2_client.authorize_security_group_ingress(
            GroupId=cluster_sg_id,
            IpPermissions=[
                {'IpProtocol': 'tcp', 'FromPort': 22, 'ToPort': 22, 'IpRanges': [{'CidrIp': ssh_allowed_ip}]},
                {'IpProtocol': 'tcp', 'FromPort': 80, 'ToPort': 80, 'UserIdGroupPairs': [{'GroupId': pm_sg_id}]},
                {'IpProtocol': 'tcp', 'FromPort': 443, 'ToPort': 443, 'UserIdGroupPairs': [{'GroupId': pm_sg_id}]},
                {'IpProtocol': 'icmp', 'FromPort': -1, 'ToPort': -1, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}

            ]
        )
        
        print(f"Ingress rules set for Cluster Security Group: {cluster_sg_id}")
        
        return gk_sg_id, th_sg_id, pm_sg_id, cluster_sg_id
    
    except Exception as e:
        print(f"Error creating security groups: {e}")
        return None, None