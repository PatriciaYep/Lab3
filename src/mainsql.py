import paramiko
import os
import json
import random
import config
import time
from pythonping import ping
import pymysql 


list_read=['SELECT inventory_in_stock(10);','']
#list_write=['INSERT INTO rental(rental_date, inventory_id, customer_id, staff_id) VALUES(NOW(), 10, 3, 1);','']
list_write=['UPDATE rental SET return_date = NOW() WHERE rental_id = 16050;','']

 
def mysqlconnect(path, public_ip, instance_id, list_sql): 
    # To connect MySQL database 
    conn = pymysql.connect( 
        host=public_ip, 
        user='root',  
        password = "root", 
        db='sakila', 
        ) 
      
    cur = conn.cursor() 
    cur.execute("select @@version") 
    output = cur.fetchall() 
    print(output) 
      
    # To close the connection 
    conn.close() 


def ping_host(host):
    ping_result = ping(target=host, count=10, timeout=2)

    return {
        'host': host,
        'avg_latency': ping_result.rtt_avg_ms,
        'min_latency': ping_result.rtt_min_ms,
        'max_latency': ping_result.rtt_max_ms,
        'packet_loss': ping_result.packet_loss
    }
    
def get_host_least_latency(workers_list):
    ip,id=get_instance_info(workers_list[0])
    min_avg_lat=ping_host(ip).get('avg_latency')
    min_host=ping_host(ip).get('host')
    min_worker=workers_list[0]
    for worker in workers_list:
        ip,id=get_instance_info(worker)
        worker_ping= ping_host(ip)
        host=worker_ping.get('host')       
        avg_latency=worker_ping.get('avg_latency')
        print(worker,'ping latency: ',avg_latency)
        if min_avg_lat > avg_latency:
            min_avg_lat = avg_latency
            min_host=host
            min_worker=worker
    return min_host,min_worker
    


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

# def workers_ips(workers):
#     ip_list=[]
#     for ele in workers:
#         ip,id=get_instance_info(ele)
#         ip_list.append(ip)
#     return ip_list



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

def process_request(list_sql,request_type,query_type):
    
    manager = 'manager1'           
    workers_list = ['worker2', 'worker3']        
           
    if (request_type == 'Direct hit'):
        if query_type=='w':           
            print('processing write requests on ',manager)
            ip,id=get_instance_info(manager)
            run_sql(manager, ip, id, list_sql)
            # replication
            for ele in workers_list:
                print('processing write requests (replication) on ',ele)
                ip,id=get_instance_info(ele)
                run_sql(ele, ip, id, list_sql)
        else:           
            print('processing read requests on ',manager)
            ip,id=get_instance_info(manager)
            run_sql(manager, ip, id, list_sql)
    elif (request_type == 'Random'):
        if query_type=='w':           
            print('processing write requests on ',manager)
            ip,id=get_instance_info(manager)
            run_sql(manager, ip, id, list_sql)            
            # replication
            for ele in workers_list:
                print('processing write requests (replication) on ',ele)
                ip,id=get_instance_info(ele)
                run_sql(ele, ip, id, list_sql)
        else:
            worker2_sql=[]
            worker3_sql=[]
            print('sending read requests randomly to workers')
            for ele in list_sql:
                worker=random.choice(workers_list)
                if worker=='worker2': worker2_sql.append(ele)
                elif worker=='worker3': worker3_sql.append(ele)
            ip2,id2=get_instance_info('worker2')
            ip3,id3=get_instance_info('worker3')           
            print('processing read requests on ','worker2')
            run_sql('worker2', ip2, id2, worker2_sql)            
            print('processing read requests on ','worker3')
            run_sql('worker3', ip3, id3, worker3_sql)   
    elif (request_type == 'Custom'):
        if query_type=='w':           
            print('processing write requests on ',manager)
            ip,id=get_instance_info(manager)
            run_sql(manager, ip, id, list_sql)
            # replication
            for ele in workers_list:
                print('processing write requests (replication) on ',ele)
                ip,id=get_instance_info(ele)
                run_sql(ele, ip, id, list_sql)
        else:
            #workers_ips_list=workers_ips(workers_list)          
            for ele in list_sql:
                min_host,min_worker=get_host_least_latency(workers_list)
                print('processing read requests on ',min_worker)
                ip,id=get_instance_info(min_worker)
                run_sql(min_worker, ip, id, [ele])
    

def valid_request(query):
    if isinstance(query, str) and len(query)>0:       
        #process_request(request_id,query,request_type)
        return True
    else:
        return False

def send_requests(num_requests):
    for item in config.request_type:
        start = time.time()
        print('\n')
        print(item)
        read_commands = []
        write_commands = []
        for i in range(num_requests):   
            # read requests
            read_string=random.choices(list_read, weights=(80, 20), k=1)     
            if valid_request(read_string[0]):  
                print('Read Request ',i,': ',read_string, ' : valid')         
                read_commands.append(read_string[0])
            else:
                print('Read Request ',i,': ',read_string, ' : Invalid string')         
                    
            # write requests
            write_string=random.choices(list_write, weights=(80, 20), k=1)
            if valid_request(write_string[0]):                    
                print('Write Request ',i,': ',write_string, ' : valid') 
                write_commands.append(write_string[0])
                write_commands.append('commit')
            else:
                print('Write Request ',i,': ',write_string, ' : Invalid string') 
         
        #print(read_commands)        
        #print(write_commands)
        process_request(read_commands,item,'r')
        process_request(write_commands,item,'w')   
        end=time.time()  
        print('Total time elapsed:',end-start)
           
        
def mainsql():
    #url = f"http://{gatekeeper1_ip}:80/new_request"
    send_requests (1000)


if __name__ == "__main__":
    mainsql()