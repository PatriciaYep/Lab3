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


#def create_security_groups(ec2_client, vpc_id, ssh_allowed_ip):
#    try:
#        # Create security group 
#        lb_sg = ec2_client.create_security_group(
#            GroupName='LB_SG',
#            Description='Security Group',
#            VpcId=vpc_id
#        )
#        lb_sg_id = lb_sg['GroupId']
#        
#        print(f"Created Security Group: {lb_sg_id}")
#               
    #     ec2_client.authorize_security_group_ingress(
    #         GroupId=lb_sg_id,
    #         IpPermissions=[
    #             {
    #                 'IpProtocol': 'tcp',
    #                 'FromPort': 80,
    #                 'ToPort': 80,
    #                 'IpRanges': [{'CidrIp': constants.IG_DEST_CIDR_BLOCK}]  # Allow HTTP from all IPs
    #             },
    #             {
    #                 'IpProtocol': 'tcp',
    #                 'FromPort': 22,
    #                 'ToPort': 22,
    #                 'IpRanges': [{'CidrIp': ssh_allowed_ip}]  # Allow SSH from specific IPs
    #             },
    #             {
    #                 'IpProtocol': 'tcp',
    #                 'FromPort': 443,
    #                 'ToPort': 443,
    #                 'IpRanges': [{'CidrIp': constants.IG_DEST_CIDR_BLOCK}]  # Allow HTTPS from all IPs
    #             },
    #             {
    #                 'IpProtocol': 'icmp',  # ICMP protocol
    #                 'FromPort': -1,        # -1 indicates all ICMP types
    #                 'ToPort': -1,          # -1 indicates all ICMP codes
    #                 'IpRanges': [{'CidrIp': constants.IG_DEST_CIDR_BLOCK}]  # Allow ICMP from all IPs (for ping)
    #             },
    #             {
    #                 'IpProtocol': 'tcp',
    #                 'FromPort': 5001,
    #                 'ToPort': 5001,
    #                 'IpRanges': [{'CidrIp': constants.IG_DEST_CIDR_BLOCK}]  # Allow traffic to port 5001 from all IPs
    #             },
    #             {
    #                 'IpProtocol': 'tcp',
    #                 'FromPort': 5002,
    #                 'ToPort': 5002,
    #                 'IpRanges': [{'CidrIp': constants.IG_DEST_CIDR_BLOCK}]  # Allow traffic to port 5002 from all IPs
    #             }

    #         ]
    #     )
        
    #     print(f"Ingress rules set for Security Group: {lb_sg_id}")
    #     return lb_sg_id
    
    # except Exception as e:
    #     print(f"Error creating security groups: {e}")
    #     return None, None
    
    
    
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
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 80,
                    'ToPort': 80,
                    'IpRanges': [{'CidrIp': constants.IG_DEST_CIDR_BLOCK}]  # Allow HTTP from all IPs
                },
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 22,
                    'ToPort': 22,
                    'IpRanges': [{'CidrIp': ssh_allowed_ip}]  # Allow SSH from specific IPs
                },
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 443,
                    'ToPort': 443,
                    'IpRanges': [{'CidrIp': constants.IG_DEST_CIDR_BLOCK}]  # Allow HTTPS from all IPs
                },
                {
                    'IpProtocol': 'icmp',  # ICMP protocol
                    'FromPort': -1,        # -1 indicates all ICMP types
                    'ToPort': -1,          # -1 indicates all ICMP codes
                    'IpRanges': [{'CidrIp': constants.IG_DEST_CIDR_BLOCK}]  # Allow ICMP from all IPs (for ping)
                }
            ]
        )
        
        print(f"Ingress rules set for Gatekeeper Security Group: {gk_sg_id}")







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
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 80,
                    'ToPort': 80,
                    'IpRanges': [{'CidrIp': constants.IG_DEST_CIDR_BLOCK}]  # Allow HTTP from all IPs
                },
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 22,
                    'ToPort': 22,
                    'IpRanges': [{'CidrIp': ssh_allowed_ip}]  # Allow SSH from specific IPs
                },
                {
                    'IpProtocol': 'icmp',  # ICMP protocol
                    'FromPort': -1,        # -1 indicates all ICMP types
                    'ToPort': -1,          # -1 indicates all ICMP codes
                    'IpRanges': [{'CidrIp': constants.IG_DEST_CIDR_BLOCK}]  # Allow ICMP from all IPs (for ping)
                },
                 {
                     'IpProtocol': 'tcp',
                     'FromPort': 443,
                     'ToPort': 443,
                     'IpRanges': [{'CidrIp': constants.IG_DEST_CIDR_BLOCK}]  # Allow HTTPS from all IPs
                 }
            ]
        )
        
        print(f"Ingress rules set for Cluster Security Group: {cluster_sg_id}")
        
        return gk_sg_id, cluster_sg_id
    
    except Exception as e:
        print(f"Error creating security groups: {e}")
        return None, None