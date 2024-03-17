from flask import Flask, render_template, request, jsonify
import os
import boto3
from datetime import datetime, timedelta, timezone

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

if __name__ == '__main__':
    app.run(debug=True)
