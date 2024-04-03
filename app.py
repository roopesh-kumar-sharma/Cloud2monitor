from flask import Flask, render_template, request, jsonify
import os
import boto3
from datetime import datetime, timedelta, timezone
import datetime
import time
from azure.identity import ClientSecretCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.monitor import MonitorManagementClient
from azure.mgmt.monitor.models import Metric
from azure.mgmt.network import NetworkManagementClient

app = Flask(__name__)
secret_key = os.urandom(24)
app.secret_key = secret_key

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/monitor', methods=['POST'])
def monitor():
    cloud_provider = request.form.get('cloud_provider', '')

    if cloud_provider == 'aws':
        aws_access_key = request.form.get('aws_access_key', '')
        aws_secret_key = request.form.get('aws_secret_key', '')
        aws_region = request.form.get('aws_region', '')
        instance_id = request.form.get('instance_id', '')

        if aws_access_key and aws_secret_key and aws_region and instance_id:
            instance_details = get_aws_instance_details(aws_access_key, aws_secret_key, aws_region, instance_id)
            if instance_details:
                cpu_utilization = get_cpu_utilization(aws_access_key, aws_secret_key, aws_region, instance_id)
                memory_utilization = get_memory_utilization(aws_access_key, aws_secret_key, aws_region, instance_id)
                instance_details['cpu_utilization'] = cpu_utilization
                instance_details['memory_utilization'] = memory_utilization
                return jsonify(instance_details)
            else:
                return jsonify({'error': 'Failed to retrieve instance details'}), 500
        else:
            return jsonify({'error': 'Invalid input for AWS'}), 400
    elif cloud_provider=="azure":
          azure_subscription_id= request.form.get('azure_subscription_id', '')
          azure_clinet_id= request.form.get('azure_clinet_id', '')
          azure_clinet_secret= request.form.get('azure_clinet_secret', '')
          azure_tenant_id= request.form.get('azure_tenant_id', '')
          azure_vm_name= request.form.get('azure_vm_name', '')
          azure_resource_group= request.form.get('azure_resource_group', '')
        
          if azure_subscription_id and azure_clinet_id and azure_clinet_secret and azure_tenant_id and azure_vm_name and azure_resource_group:
            cpu_usage, memory_usage_mb = get_azure_metric(azure_tenant_id,azure_clinet_id,azure_clinet_secret,azure_subscription_id,azure_resource_group,azure_vm_name)
            return jsonify(cpu_usage, memory_usage_mb)


    else:
        return jsonify({'error': 'Invalid cloud provider'}), 400

def get_aws_instance_details(access_key, secret_key, region, instance_id):
    try:
        ec2 = boto3.client('ec2', aws_access_key_id=access_key, aws_secret_access_key=secret_key, region_name=region)
        response = ec2.describe_instances(InstanceIds=[instance_id])
        instance = response['Reservations'][0]['Instances'][0]
        # Calculate uptime
        launch_time = instance['LaunchTime']
        now = datetime.now(timezone.utc)
        uptime = now - launch_time

        # Convert uptime to days, hours, and minutes
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        uptime_str = f"{days} days, {hours} hours, {minutes} minutes"
        return {
            'instance_id': instance['InstanceId'],
            'uptime': uptime_str,
            'public_ip_address': instance.get('PublicIpAddress', 'N/A')
        }
    except Exception as e:
        print(f"Error: {e}")
        return None

# The rest of the code remains unchanged


def get_cpu_utilization(access_key, secret_key, region, instance_id):
    try:
        # Create a CloudWatch client
        cloudwatch = boto3.client('cloudwatch', aws_access_key_id=access_key, aws_secret_access_key=secret_key, region_name=region)

        # Get the current datetime in UTC
        current_time = datetime.now(timezone.utc)

        # Set start_time to 5 minutes before current time
        start_time = current_time - timedelta(minutes=5)

        # Set end_time to the current time
        end_time = current_time

        # Specify the metric data to retrieve
        response = cloudwatch.get_metric_statistics(
            Namespace='AWS/EC2',
            MetricName='CPUUtilization',
            Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
            StartTime=start_time,
            EndTime=end_time,
            Period=300,  # 5 minute intervals
            Statistics=['Average']
        )

        # Extract and return the average CPU utilization
        if 'Datapoints' in response:
            datapoints = response['Datapoints']
            if datapoints:
                return datapoints[-1]['Average']  # Get the latest datapoint
        return None
    except Exception as e:
        print(f"Error fetching CPU utilization: {e}")
        return None

def get_memory_utilization(access_key, secret_key, region, instance_id):
    try:
        # Create a CloudWatch client
        cloudwatch = boto3.client('cloudwatch', aws_access_key_id=access_key, aws_secret_access_key=secret_key, region_name=region)

        # Get the current datetime in UTC
        current_time = datetime.now(timezone.utc)

        # Set start_time to 5 minutes before current time
        start_time = current_time - timedelta(minutes=5)

        # Set end_time to the current time
        end_time = current_time

        # Specify the metric data to retrieve
        response = cloudwatch.get_metric_statistics(
            Namespace='CWAgent',
            MetricName='mem_used_percent',
            Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
            StartTime=start_time,
            EndTime=end_time,
            Period=300,  # 5 minute intervals
            Statistics=['Average']
        )
        # Extract and return the average memory utilization
        if 'Datapoints' in response:
            datapoints = response['Datapoints']
            if datapoints:
                return datapoints[-1]['Average']  # Get the latest datapoint
        return None
    except Exception as e:
        print(f"Error fetching memory utilization: {e}")
        return None

def get_azure_metric(tenant_id,
client_id,
client_secret,
subscription_id,
resource_group_name,
vm_name):

# Authenticate with Azure
    credential = ClientSecretCredential(tenant_id, client_id, client_secret)

# Initialize the ComputeManagementClient
    
    compute_client = ComputeManagementClient(credential, subscription_id)

# Initialize the MonitorManagementClient
    monitor_client = MonitorManagementClient(credential, subscription_id)

    # Initialize the NetworkManagementClient
    network_client = NetworkManagementClient(credential, subscription_id)

    # Fetch VM details
    vm = compute_client.virtual_machines.get(resource_group_name, vm_name)

    # Fetch the network interface associated with the VM
    nic_id = vm.network_profile.network_interfaces[0].id
    nic_name = nic_id.split('/')[-1]
    nic = network_client.network_interfaces.get(resource_group_name, nic_name)

    # Fetch the public IP address associated with the network interface
    public_ip_id = nic.ip_configurations[0].public_ip_address.id
    public_ip_name = public_ip_id.split('/')[-1]
    public_ip = network_client.public_ip_addresses.get(resource_group_name, public_ip_name)

    # Print the VM name and its public IP address
    print(f"VM Name: {vm_name}")
    print(f"Public IP: {public_ip.ip_address}")

    # Continuously monitor CPU and memory metrics in real-time
    while True:
        # Fetch CPU and memory metrics
        metric_definitions = monitor_client.metric_definitions.list(resource_uri=vm.id)
        cpu_metric = next((m for m in metric_definitions if m.name.value == 'Percentage CPU'), None)
        memory_metric = next((m for m in metric_definitions if m.name.value == 'Available Memory Bytes'), None)

        if cpu_metric and memory_metric:
            # Correctly format the timespan
            end_time = datetime.datetime.utcnow().isoformat()
            start_time = (datetime.datetime.utcnow() - datetime.timedelta(minutes=5)).isoformat()  # Fetch metrics for the last 5 minutes
            timespan = f"{start_time}/{end_time}"

            cpu_metrics = monitor_client.metrics.list(
                resource_uri=vm.id,
                metricnames=cpu_metric.name.value,
                timespan=timespan,
                interval='PT1M',  # Fetch metrics at 1-minute intervals
                aggregation='Average'
            )
            memory_metrics = monitor_client.metrics.list(
                resource_uri=vm.id,
                metricnames=memory_metric.name.value,
                timespan=timespan,
                interval='PT1M',  # Fetch metrics at 1-minute intervals
                aggregation='Average'
            )

            cpu_usage = cpu_metrics.value[0].timeseries[0].data[0].average
            memory_usage_bytes = memory_metrics.value[0].timeseries[0].data[0].average

            # Convert memory usage to megabytes
            memory_usage_mb = memory_usage_bytes / (1024 * 1024)
            return cpu_usage, memory_usage_mb
            # # Print the CPU and memory usage metrics
            # print(f"CPU Usage: {cpu_usage:.2f}%")
            # print(f"Memory Usage: {memory_usage_mb:.2f} MB")
        else:
            print("Metrics not found")

        # Wait for 1 minute before fetching metrics again
        time.sleep(60)

if __name__ == '__main__':
    app.run(debug=True)
