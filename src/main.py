import requests
import json
import random
import config
import time

list_read=['SELECT inventory_in_stock(10);','']
list_write=['INSERT INTO rental(rental_date, inventory_id, customer_id, staff_id) VALUES(NOW(), 10, 3, 1);','']

# def send_requests(url, num_requests):
#     for i in range(num_requests):
#         read_string=random.choices(list_read, weights=(80, 20), k=1)
#         print(url)
#         response = requests.get(url)
#         print(f'Request {i+1}: Status Code: {response.status_code}, Response: {response.text}')

# def send_requests(url, num_requests):
#     print(url)
#     # read requests
#     for item in config.request_type:
#         for i in range(num_requests):   
#             read_string=random.choices(list_read, weights=(80, 20), k=1)
#             #print(item)
#             print(read_string)
#             try:
#                 #response = requests.get(url, {'query': read_string,'request_type': item})          
#                 #response = requests.get(url, {'query': read_string})                      
#                 response = requests.get(url)
#                 # Wait for the response to be available
#                 #while request_id not in responses:
#                 #time.sleep(1)
#                 print(f'Request {i+1}: Status Code: {response.status_code}, Response: {response.text}')
#             except requests.exceptions.RequestException as e:
#                 print(f"Request {i+1}: Request failed with an error: {e}")

# def main():
    
#     with open('instance_details.json', 'r') as file:
#          instance_details = json.load(file)
#     #with open('../infra/instance_details.json', 'r') as file:
#     #with open('../instance_details.json', 'r') as file:
#     #     instance_details = json.load(file)
    
#     gatekeeper1_ip = ''
#     gatekeeper2_ip = ''
    
#     for instance in instance_details:
#         if instance['Name'] == 'gatekeeper1':
#             gatekeeper1_ip = instance['PublicIP']
#         if instance['Name'] == 'gatekeeper2':
#             gatekeeper2_ip = instance['PublicIP']
            
#     print('gatekeeper1',gatekeeper1_ip)
#     print('gatekeeper2',gatekeeper2_ip)

#     #url = f"http://{gatekeeper1_ip}/new_request"
#     url = f"http://{gatekeeper1_ip}"
#     send_requests (url, 1)


# if __name__ == "__main__":
#     main()




# import requests
# import json

# def send_requests(url, num_requests):
#     for i in range(num_requests):
#         response = requests.get(url)
#         print(f'Request {i+1}: Status Code: {response.status_code}, Response: {response.text}')


list_read=['SELECT inventory_in_stock(10);','']
#list_write=['INSERT INTO rental(rental_date, inventory_id, customer_id, staff_id) VALUES(NOW(), 10, 3, 1);','']
list_write=['UPDATE rental SET return_date = NOW() WHERE rental_id = 16050;','']

def main(num_requests):

    with open('instance_details.json', 'r') as file:
         instance_details = json.load(file)
    
    gatekeeper1_ip = ''
    
    for instance in instance_details:
        if instance['Name'] == 'gatekeeper1':
            gatekeeper1_ip = instance['PublicIP']

    url = f"http://{gatekeeper1_ip}:80/new_request"
    #send_requests (url, 1)
    
    for i in range(num_requests):
        read_string=random.choices(list_read, weights=(80, 20), k=1)
        data = {'query': read_string}
        try:
                start_time = time.time()
                response = requests.post(url, json=data)
                print(response)
                end_time = time.time()
                #response_times.append(end_time - start_time)

                if response.status_code != 200:
                    #print(f"Error ({mode}):", response.status_code, response.json())                  
                    print(f"Error :", response.status_code, response.json())
                else:
                    print (response.json())
        except requests.RequestException as e:
                #print(f"Request failed ({mode}):", e)
                print(f"Request failed :", e)


if __name__ == "__main__":
    num_requests=10
    main(num_requests)