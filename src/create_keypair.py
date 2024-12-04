import os.path

def create_keypair(ec2_client, key_name):
    """
    Ensure a key pair with the specified name exists. 
    If it doesn't, create it and save the private key with secure permissions.
    """
    try:
        # Check if the key pair already exists
        key_pairs = ec2_client.describe_key_pairs(KeyNames=[key_name])
        if key_pairs and key_pairs.get('KeyPairs'):
            key_pair_id = key_pairs['KeyPairs'][0]['KeyName']
            print(f'Key pair "{key_pair_id}" already exists.')
            return key_pair_id

    except ec2_client.exceptions.ClientError as e:
        # Handle the case where the key pair doesn't exist (ClientError: InvalidKeyPair.NotFound)
        if 'InvalidKeyPair.NotFound' in str(e):
            print(f'Key pair "{key_name}" does not exist, creating a new one.')
        else:
            print(f'An error occurred: {e}')
            return None

    # Create the key pair since it doesn't exist
    try:
        key_pair = ec2_client.create_key_pair(KeyName=key_name, KeyType='rsa', KeyFormat='pem')
        private_key = key_pair.get('KeyMaterial')

        # Save the private key to a file
        key_file_path = f'{key_name}.pem'
        with open(key_file_path, 'w') as file:
            file.write(private_key)
        
        # Set file permissions to read-only for the owner (400)
        os.chmod(key_file_path, 0o400)

        key_pair_id = key_pair.get('KeyName')
        print(f'Key pair "{key_pair_id}" created and saved to {key_file_path}')
        return key_pair_id

    except Exception as e:
        print(f'Failed to create key pair: {e}')
        return None