#import the necessary library for aws and azure
import logging
from flask import Flask, render_template, request, jsonify,session
import os
from azure.identity import ClientSecretCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.monitor import MonitorManagementClient
from azure.mgmt.network import NetworkManagementClient
from datetime import datetime, timedelta, timezone
import boto3
from flask_cors import CORS
import ntfy
import requests

#-------------------------------------------------------------------- 

app = Flask(__name__)
secret_key = os.urandom(24)
app.secret_key = secret_key
CORS(app)
#--------------------------------------------------------------------

logging.basicConfig(level=logging.ERROR)

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/monitor', methods=['POST'])
def monitor():
    cloud_provider = request.form.get('cloud_provider', '')

#--------------------------------------------------------------------
    if cloud_provider == "aws":
        # pulling the credential from aws the form
        aws_access_key = request.form.get('aws_access_key', '')
        aws_secret_key = request.form.get('aws_secret_key', '')
        aws_region = request.form.get('aws_region', '')
        instance_id = request.form.get('instance_id', '')
        set_notification = int(request.form.get('set_notification', 0))
        print(set_notification)


        try:
            if not (aws_access_key and aws_secret_key and aws_region and instance_id):
                raise ValueError("Missing AWS credentials or instance details")

            # pull Aws cloud metric here: cpu,memory,network and disk

            aws_data = get_aws_instance_details(aws_access_key, aws_secret_key, aws_region, instance_id,)
            aws_data['cpu_utilization'] = get_cpu_utilization(aws_access_key, aws_secret_key, aws_region, instance_id,set_notification)
            aws_data['memory_utilization'] = get_memory_utilization(aws_access_key, aws_secret_key, aws_region, instance_id,set_notification)
            aws_data['disk_utilization'] =get_disk_usage(aws_access_key, aws_secret_key, aws_region, instance_id,set_notification)
            aws_data['network_utilization'] =aws_network(aws_access_key, aws_secret_key, aws_region, instance_id,set_notification)

            #return the metric in jason format
            return jsonify(aws_data)
        except Exception as e:
            logging.error(f"AWS error: {e}")
            return jsonify({'error': str(e)}), 400
        
#--------------------------------------------------------------------

    # pulling the credential from the azure form

    elif cloud_provider == 'azure':
        azure_subscription_id = request.form.get('azure_subscription_id', '')
        azure_client_id = request.form.get('azure_client_id', '')
        azure_client_secret = request.form.get('azure_client_secret', '')
        azure_tenant_id = request.form.get('azure_tenant_id', '')
        azure_vm_name = request.form.get('azure_vm_name', '')
        azure_resource_group = request.form.get('azure_resource_group', '')
        azure_set_notification = int(request.form.get('azure_set_notification', 0))
        print(azure_set_notification)



        try:
            if not (azure_subscription_id and azure_client_id and azure_client_secret and azure_tenant_id and azure_vm_name and azure_resource_group):
                raise ValueError("Missing Azure credentials or VM details")

        #   pull aZure cloud metric here: cpu,memory,network and disk

            azure_data = get_azure_metric(azure_tenant_id, azure_client_id, azure_client_secret, azure_subscription_id, azure_resource_group, azure_vm_name)
            azure_data['cpu_utilization'] = get_cpu_utilization_azure(azure_subscription_id, azure_client_id, azure_client_secret, azure_tenant_id, azure_resource_group, azure_vm_name,azure_set_notification)
            azure_data['memory_utilization'] = get_memory_utilization_azure(azure_subscription_id, azure_client_id, azure_client_secret, azure_tenant_id, azure_resource_group, azure_vm_name,azure_set_notification)
            azure_data['disk_utilization'] = get_disk_usage_azure(azure_subscription_id, azure_client_id, azure_client_secret, azure_tenant_id, azure_resource_group, azure_vm_name,azure_set_notification)
            azure_data['network_utilization'] = network_usage_azure(azure_subscription_id, azure_client_id, azure_client_secret, azure_tenant_id, azure_resource_group, azure_vm_name,azure_set_notification)
            
            #return the metric in jason format
            return jsonify(azure_data)
        except Exception as e:
            logging.error(f"Azure error: {e}")
            return jsonify({'error': str(e)}), 400
        
#-----------------------------------------------------------------------------------------------------------------------------------------
    else:

        # Collect the Credential of both azure and AWS cloud from the compare form.

        aws_access_key = request.form.get('aws_access_key', '')
        aws_secret_key = request.form.get('aws_secret_key', '')
        aws_region = request.form.get('aws_region', '')
        instance_id = request.form.get('instance_id', '')
        set_notification = int(request.form.get('set_notification', 0))


        azure_subscription_id = request.form.get('azure_subscription_id', '')
        azure_client_id = request.form.get('azure_client_id', '')
        azure_client_secret = request.form.get('azure_client_secret', '')
        azure_tenant_id = request.form.get('azure_tenant_id', '')
        azure_vm_name = request.form.get('azure_vm_name', '')
        azure_resource_group = request.form.get('azure_resource_group', '')
        azure_set_notification = int(request.form.get('azure_set_notification', 0))


        try:
            if not (aws_access_key and aws_secret_key and aws_region and instance_id):
                raise ValueError("Missing AWS credentials or instance details")
            if not (azure_subscription_id and azure_client_id and azure_client_secret and azure_tenant_id and azure_vm_name and azure_resource_group):
                raise ValueError("Missing Azure credentials or VM details")
#-----------------------------------------------------------------------------------------------------------------------------------------

        #pulling the azure and aws  combined metrics for pulling the cpu,memory,disk usage and network utilization 
            azure_data = get_azure_metric(azure_tenant_id, azure_client_id, azure_client_secret, azure_subscription_id, azure_resource_group, azure_vm_name)
            azure_data['cpu_utilization'] = get_cpu_utilization_azure(azure_subscription_id, azure_client_id, azure_client_secret, azure_tenant_id, azure_resource_group, azure_vm_name,azure_set_notification)
            azure_data['memory_utilization'] = get_memory_utilization_azure(azure_subscription_id, azure_client_id, azure_client_secret, azure_tenant_id, azure_resource_group, azure_vm_name,azure_set_notification)
            azure_data['disk_utilization'] = get_disk_usage_azure(azure_subscription_id, azure_client_id, azure_client_secret, azure_tenant_id, azure_resource_group, azure_vm_name,azure_set_notification)
            azure_data['network_utilization'] = network_usage_azure(azure_subscription_id, azure_client_id, azure_client_secret, azure_tenant_id, azure_resource_group, azure_vm_name,azure_set_notification)

            aws_data = get_aws_instance_details(aws_access_key, aws_secret_key, aws_region, instance_id)
            aws_data['cpu_utilization'] = get_cpu_utilization(aws_access_key, aws_secret_key, aws_region, instance_id,set_notification)
            aws_data['memory_utilization'] = get_memory_utilization(aws_access_key, aws_secret_key, aws_region, instance_id,set_notification)
            aws_data['disk_utilization'] =get_disk_usage(aws_access_key, aws_secret_key, aws_region, instance_id,set_notification)
            aws_data['network_utilization'] =aws_network(aws_access_key, aws_secret_key, aws_region, instance_id,set_notification)

            #retun the aws as well as azure  data in json format
            return jsonify(aws_data,azure_data)
        except Exception as e:
            logging.error(f"Azure error: {e}")
            return jsonify({'error': str(e)}), 400
        
#-----------------------------------------------------------------------------------------------------------------------------------------

def get_azure_metric(tenant_id, client_id, client_secret, subscription_id, resource_group_name, vm_name):
    try:
        credential = ClientSecretCredential(tenant_id, client_id, client_secret)
        compute_client = ComputeManagementClient(credential, subscription_id)
        monitor_client = MonitorManagementClient(credential, subscription_id)
        network_client = NetworkManagementClient(credential, subscription_id)

        vm = compute_client.virtual_machines.get(resource_group_name, vm_name)
        # Initialize variables to store NIC and public IP information
        nic_id = ""
        public_ip_address = ""

        for nic_ref in vm.network_profile.network_interfaces:
            nic = network_client.network_interfaces.get(resource_group_name, nic_ref.id.split('/')[-1])
            if nic.primary:
                nic_id = nic_ref.id
                if nic.ip_configurations[0].public_ip_address:
                    public_ip = network_client.public_ip_addresses.get(resource_group_name, nic.ip_configurations[0].public_ip_address.id.split('/')[-1])
                    public_ip_address = public_ip.ip_address
                break

        if not nic_id:
            raise ValueError("Primary NIC not found")

        # uptime = "Not available" The uptime for the azure virtual machine cannot be fetched  directly from the API so I will try to do it later if possible by anyway

        return {
            'server_name': vm.name,
            # 'uptime': uptime,
            'public_ip_address': public_ip_address
        }

    except Exception as e:
        logging.error(f"Azure error: {e}")
        return {'error': str(e)}
    
#---------------------------------------------CPU utilization for azure--------------------------------------------------------------------------------------------

def get_cpu_utilization_azure(subscription_id, client_id, client_secret, tenant_id, resource_group_name, vm_name,azure_set_notification):
    try:
        credential = ClientSecretCredential(tenant_id, client_id, client_secret)
        monitor_client = MonitorManagementClient(credential, subscription_id)

        # Fetch CPU metrics
        cpu_metrics = monitor_client.metrics.list(
            resource_uri=f"/subscriptions/{subscription_id}/resourceGroups/{resource_group_name}/providers/Microsoft.Compute/virtualMachines/{vm_name}",
            metricnames='Percentage CPU',
            # timespan=timedelta(minutes=5),
            timespan='PT5M',
            interval='PT1M'
        )
        cpu_usage = cpu_metrics.value[0].timeseries[0].data[0].average
        azure_send_notification("Azure", "CPU", cpu_usage,azure_set_notification)

        return cpu_usage
    except Exception as e:
        logging.error(f"Azure CPU utilization error: {e}")
        return {'error': str(e)}

def get_memory_utilization_azure(subscription_id, client_id, client_secret, tenant_id, resource_group_name, vm_name,azure_set_notification):
    try:
        credential = ClientSecretCredential(tenant_id, client_id, client_secret)
        compute_client = ComputeManagementClient(credential, subscription_id)
        monitor_client = MonitorManagementClient(credential, subscription_id)
        # network_client = NetworkManagementClient(credential, subscription_id)
        vm = compute_client.virtual_machines.get(resource_group_name, vm_name)

        metric_definitions = monitor_client.metric_definitions.list(resource_uri=vm.id)
        memory_metric = next((m for m in metric_definitions if m.name.value == 'Available Memory Bytes'), None)
        end_time = datetime.utcnow().isoformat()
        start_time = (datetime.utcnow() - timedelta(minutes=5)).isoformat()
        timespan = f"{start_time}/{end_time}"
        memory_metrics = monitor_client.metrics.list(
            resource_uri=vm.id,
            metricnames=memory_metric.name.value,
            timespan=timespan,
            interval='PT1H',
            aggregation='Average'
    )
        memory_usage_mb = memory_metrics.value[0].timeseries[0].data[0].average
        memory_usage_mb=memory_usage_mb/1048576
        azure_send_notification("Azure", "Memory", memory_usage_mb,azure_set_notification)
        return memory_usage_mb
    except Exception as e:
        logging.error(f"Azure memory utilization error: {e}")
        return {'error': str(e)}


#---------------------------------------------get the Disk usage for azue cloud--------------------------------------------------------------------------------------------

def get_disk_usage_azure(subscription_id, client_id, client_secret, tenant_id, resource_group_name, vm_name,azure_set_notification):
    try:
        credential = ClientSecretCredential(tenant_id, client_id, client_secret)
        compute_client = ComputeManagementClient(credential, subscription_id)
        monitor_client = MonitorManagementClient(credential, subscription_id)
        
        vm = compute_client.virtual_machines.get(resource_group_name, vm_name)

        # Get the metric definition for disk usage
        disk_metric_definitions = monitor_client.metric_definitions.list(resource_uri=vm.id)
        disk_metric = next((m for m in disk_metric_definitions if m.name.value == 'Disk Write Bytes'), None)

        # Set the time range for the metric query (last 5 minutes)
        end_time = datetime.utcnow().isoformat()
        start_time = (datetime.utcnow() - timedelta(minutes=5)).isoformat()
        timespan = f"{start_time}/{end_time}"

        # Query the disk usage metrics
        disk_metrics = monitor_client.metrics.list(
            resource_uri=vm.id,
            metricnames=disk_metric.name.value,
            timespan=timespan,
            interval='PT1H',  # Hourly aggregation
            aggregation='Average'  # Average value over the interval
        )

        # Extract the disk usage value from the metric data
        disk_usage = disk_metrics.value[0].timeseries[0].data[0].average
        disk_usage = disk_usage / 1048576
        azure_send_notification("Azure", "Disk", disk_usage,azure_set_notification)

        return disk_usage
    except Exception as e:
        logging.error(f"Azure disk utilization error: {e}")
        return {'error': str(e)}

#---------------------------------------------Azure network usages pulling--------------------------------------------------------------------------------------------

def network_usage_azure(subscription_id, client_id, client_secret, tenant_id, resource_group_name, vm_name,azure_set_notification):
    try:
        credential = ClientSecretCredential(tenant_id, client_id, client_secret)
        compute_client = ComputeManagementClient(credential, subscription_id)
        monitor_client = MonitorManagementClient(credential, subscription_id)
        
        vm = compute_client.virtual_machines.get(resource_group_name, vm_name)

        # Get the metric definition for network usage
        network_metric_definitions = monitor_client.metric_definitions.list(resource_uri=vm.id)
        network_metric = next((m for m in network_metric_definitions if m.name.value == 'Network Out'), None)

        # Set the time range for the metric query (last 5 minutes)
        end_time = datetime.utcnow().isoformat()
        start_time = (datetime.utcnow() - timedelta(minutes=5)).isoformat()
        timespan = f"{start_time}/{end_time}"

        # Query the network usage metrics
        network_metrics = monitor_client.metrics.list(
            resource_uri=vm.id,
            metricnames=network_metric.name.value,
            timespan=timespan,
            interval='PT1H',  # Hourly aggregation
            aggregation='Average'  # Average value over the interval
        )

        # Extract the network usage value from the metric data
        network_usage = network_metrics.value[0].timeseries[0].data[0].average

        azure_send_notification("Azure", "Network", network_usage,azure_set_notification)

        return network_usage
    except Exception as e:
        logging.error(f"Azure network utilization error: {e}")
        return {'error': str(e)}

#---------------------------------------------Pulling aws cloud details like server_name,uptime and public Ip of the VM/server--------------------------------------------------------------------------------------------

def get_aws_instance_details(access_key, secret_key, region, instance_id):
    try:
        if not (access_key and secret_key and region and instance_id):
            raise ValueError("Missing AWS credentials or instance details")

        ec2 = boto3.client('ec2', aws_access_key_id=access_key, aws_secret_access_key=secret_key, region_name=region)
        response = ec2.describe_instances(InstanceIds=[instance_id])
        instance = response['Reservations'][0]['Instances'][0]
        launch_time = instance['LaunchTime']
        now = datetime.now(timezone.utc)
        uptime = now - launch_time

        #fetch the name of the server
        instance_name = ""
        for tag in instance.get('Tags', []):
            if tag['Key'] == 'Name':
                instance_name = tag['Value']
                break

        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        uptime_str = f"{days} days, {hours} hours, {minutes} minutes"

        return {
            # 'instance_id': instance['InstanceId'],
            'server_uptime': uptime_str,
            'public_address': instance.get('PublicIpAddress', 'N/A'),
            'cloud _server_name': instance_name,
        }
    except Exception as e:
        logging.error(f"AWS error: {e}")
        return {'error': str(e)}

#---------------------------------------------pulls the cpu utilization for aws cloud --------------------------------------------------------------------------------------------

def get_cpu_utilization(access_key, secret_key, region, instance_id,set_notification):
    try:
        if not (access_key and secret_key and region and instance_id):
            raise ValueError("Missing AWS credentials or instance details")

        cloudwatch = boto3.client('cloudwatch', aws_access_key_id=access_key, aws_secret_access_key=secret_key, region_name=region)
        current_time = datetime.now(timezone.utc)
        start_time = current_time - timedelta(minutes=10)
        end_time = current_time

        response = cloudwatch.get_metric_statistics(
            Namespace='AWS/EC2',
            MetricName='CPUUtilization',
            Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
            StartTime=start_time,
            EndTime=end_time,
            Period=60,
            Statistics=['Average'],
            Unit='Percent'
        )

        if 'Datapoints' in response:
            datapoints = response['Datapoints']
            if datapoints:
                # Sort datapoints by timestamp in descending order to get the latest value
                sorted_datapoints = sorted(datapoints, key=lambda x: x['Timestamp'], reverse=True)
                aws_cpu=sorted_datapoints[0]['Average']
                send_notification("AWS", "CPU",aws_cpu,set_notification)
                return sorted_datapoints[0]['Average']  # Return the average value of the latest datapoint
        return 0  # Return a default value if no datapoints are available
    except Exception as e:
        logging.error(f"AWS CPU utilization error: {e}")
        return {'error': str(e)}
#---------------------------------------------aws memory metric pulling--------------------------------------------------------------------------------------------


def get_memory_utilization(access_key, secret_key, region, instance_id,set_notification,):
    try:
        if not (access_key and secret_key and region and instance_id):
            raise ValueError("Missing AWS credentials or instance details")

        cloudwatch = boto3.client('cloudwatch', aws_access_key_id=access_key, aws_secret_access_key=secret_key, region_name=region)
        current_time = datetime.now(timezone.utc)
        start_time = current_time - timedelta(minutes=5)
        end_time = current_time

        response = cloudwatch.get_metric_statistics(
            Namespace='CWAgent',
            MetricName='mem_used_percent',
            Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
            StartTime=start_time,
            EndTime=end_time,
            Period=300,
            Statistics=['Average'],
        )
    
        if 'Datapoints' in response:
            datapoints = response['Datapoints']
            if datapoints:
                memory_utilization = datapoints[-1]['Average']

                send_notification("AWS", "Memory", memory_utilization,set_notification)

                return memory_utilization
        return None
    except Exception as e:
        logging.error(f"AWS memory utilization error: {e}")
        return {'error': str(e)}

def send_notification(message):
    ntfy.send(message, token="tk_nhc66k711ke8ei8nzls464wnsc7hv")



    #---------------------------------------------get the disk utilization for aws cloud--------------------------------------------------------------------------------------------


def get_disk_usage(access_key, secret_key, region, instance_id,set_notification):
    try:
        # Create CloudWatch client with hardcoded credentials and specified region
        cloudwatch = boto3.client('cloudwatch',region_name=region,aws_access_key_id=access_key,aws_secret_access_key=secret_key)
        end_time = datetime.now()  # Current time
        start_time = end_time - timedelta(days=1)  

        response = cloudwatch.get_metric_statistics(
            Namespace='CWAgent',
            MetricName='disk_used_percent',
            Dimensions=[
                {'Name': 'InstanceId', 'Value': instance_id},
                {'Name': 'path', 'Value': '/'},
                {'Name': 'device', 'Value': 'xvda1'},
                {'Name': 'fstype', 'Value': 'ext4'}
                #As root disk is important this '/' indicates root and the ext4 is the file system of the partion.
            ],
            StartTime=start_time,
            EndTime=end_time,
            Period=60, #60 sec
            Statistics=['Average'],
            Unit='Percent'
        )
        datapoints = response['Datapoints']
        if datapoints:
            aws_disk_utilization=datapoints[-1]['Average']
            #--------code for notification------
            send_notification("AWS", "Disk", aws_disk_utilization,set_notification)
                
            return datapoints[-1]['Average']
        else:
            return None
    except Exception as e:
        logging.error(f"AWS disk usage error: {e}")
        return {'error': str(e)}

#--------------------------------------------- Network info fetch for aws--------------------------------------------------------------------------------------------

def aws_network(access_key, secret_key, region, instance_id,set_notification):
    try:
        if not (access_key and secret_key and region and instance_id):
            raise ValueError("Missing AWS credentials or instance details")

        cloudwatch = boto3.client('cloudwatch', aws_access_key_id=access_key, aws_secret_access_key=secret_key, region_name=region)
        current_time = datetime.now(timezone.utc)
        start_time = current_time - timedelta(minutes=10)
        end_time = current_time

        response = cloudwatch.get_metric_statistics(
            Namespace='AWS/EC2',
            MetricName='NetworkOut',
            Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
            StartTime=start_time,
            EndTime=end_time,
            Period=60, #60 sec
            Statistics=['Average'],
            Unit='Bytes'
        )
        if 'Datapoints' in response:
            datapoints = response['Datapoints']
            if datapoints:
                # Sort datapoints by timestamp in descending order to get the latest value
                sorted_datapoints = sorted(datapoints, key=lambda x: x['Timestamp'], reverse=True)
                aws_net=sorted_datapoints[0]['Average']/1024 
                send_notification("AWS","Network",aws_net,set_notification)
            return sorted_datapoints[0]['Average']/1024 
        return 0 
    except Exception as e:
        logging.error(f"AWS Network utilization error: {e}")
        return {'error': str(e)}    
    
#AWS function to send the notification after the user defines the value in percentage in the form


def send_notification(cloud_provider, resource_type, utilization,set_notification):
                    if utilization>set_notification:
                        message = f"{resource_type} Usage is High ({utilization}%) on {cloud_provider}"
                        requests.post("https://ntfy.sh/memory-alert", data=message.encode(encoding='utf-8'))
          
#Azure function to send the notification after the user defines the value in percentage in the form
               
def azure_send_notification(cloud_provider, resource_type, utilization,azure_set_notification):
                    if utilization>azure_set_notification:
                        message = f"{resource_type} Usage is High ({utilization}%) on {cloud_provider}"
                        requests.post("https://ntfy.sh/Cloud-Monitor", data=message.encode(encoding='utf-8'))

# Runs the Flask app when the script is executed directly with debugging enabled.


if __name__ == "__main__":
    app.run(debug=True)

