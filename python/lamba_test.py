import boto3

cloudwatch = boto3.client("cloudwatch")

def create_cloudwatch_alarm(instance_id, action):
    try:
        if action == "launched" or action == "launch":
            response = cloudwatch.put_metric_alarm(
                AlarmName="Node1_Disk_Utilization",
                AlarmDescription="Disk Montitor for Node1",
                ActionsEnabled=True,
                MetricName="DiskSpaceUtilization",
                Namespace="System/Linux",
                Statistic="Average",
                Period=60,
                Unit="Percent",
                EvaluationPeriods=1,
                DatapointsToAlarm=1,
                Threshold=50.0,
                ComparisonOperator="GreaterThanThreshold",
                Dimensions=[
                    {
                    "Name": "InstanceId",
                    "Value": instance_id
                    },
                    {
                    "Name": "Filesystem",
                    "Value": "/dev/xvda1"
                    },
                    {
                    "Name": "MountPath",
                    "Value": "/"
                    },
                ],
                Tags=[
                    {
                        "Key": "Name",
                        "Value": "Disk_Alarm_Test_1"
                    },
                ],
            )

            if response["ResponseMetadata"]["HTTPStatusCode"] == 200:
                return "Alarm created successfully"
        else:
            return f"Action: {action} will exit lambda"
    except Exception as e:
        return e
    
response = create_cloudwatch_alarm("i-0a11b0c265e0b332f", "launched")
print(response)