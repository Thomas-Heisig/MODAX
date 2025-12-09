# Cloud Integration Guide

**Last Updated:** 2025-12-09  
**Status:** Design Phase  
**Version:** 1.0  
**Supported Platforms:** AWS, Azure, GCP

## Overview

MODAX supports deployment on major cloud platforms (AWS, Azure, GCP) with cloud-native features including auto-scaling, managed databases, object storage, and serverless functions.

## Multi-Cloud Architecture

```
┌────────────────────────────────────────────────────────────┐
│                      Edge Layer                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                 │
│  │  ESP32   │  │  ESP32   │  │  ESP32   │                 │
│  │ Device 1 │  │ Device 2 │  │ Device 3 │                 │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘                 │
└───────┼─────────────┼─────────────┼───────────────────────┘
        │             │             │
        └─────────────┴─────────────┘
                      │
                      ▼
┌────────────────────────────────────────────────────────────┐
│              Cloud Gateway / IoT Hub                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  AWS IoT Core  │  Azure IoT Hub  │  GCP IoT Core    │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────┬───────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  Application │  │  AI/ML       │  │  Storage     │
│  Services    │  │  Services    │  │  Services    │
│              │  │              │  │              │
│ - K8s/EKS   │  │ - SageMaker │  │ - S3/Blob   │
│ - AKS/GKE   │  │ - ML Studio │  │ - BigQuery  │
│ - Load Bal  │  │ - Vertex AI │  │ - DynamoDB  │
└──────────────┘  └──────────────┘  └──────────────┘
```

## AWS Integration

### Architecture Components

#### 1. AWS IoT Core
```yaml
# infrastructure/aws/iot-thing-type.tf
resource "aws_iot_thing_type" "modax_device" {
  name = "modax-esp32-device"
  
  properties {
    description = "MODAX ESP32 Industrial Device"
    searchable_attributes = [
      "deviceId",
      "location",
      "deviceType"
    ]
  }
}

resource "aws_iot_policy" "modax_device_policy" {
  name = "modax-device-policy"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "iot:Connect"
        ]
        Resource = "arn:aws:iot:${var.region}:${var.account_id}:client/${!iot:ClientId}"
      },
      {
        Effect = "Allow"
        Action = [
          "iot:Publish"
        ]
        Resource = "arn:aws:iot:${var.region}:${var.account_id}:topic/modax/+/sensor_data"
      },
      {
        Effect = "Allow"
        Action = [
          "iot:Subscribe",
          "iot:Receive"
        ]
        Resource = "arn:aws:iot:${var.region}:${var.account_id}:topicfilter/modax/+/commands"
      }
    ]
  })
}
```

#### 2. Amazon EKS (Kubernetes)
```yaml
# infrastructure/aws/eks-cluster.tf
resource "aws_eks_cluster" "modax" {
  name     = "modax-production"
  role_arn = aws_iam_role.eks_cluster.arn
  version  = "1.28"
  
  vpc_config {
    subnet_ids = aws_subnet.private[*].id
    endpoint_private_access = true
    endpoint_public_access  = true
    
    security_group_ids = [
      aws_security_group.eks_cluster.id
    ]
  }
  
  enabled_cluster_log_types = [
    "api",
    "audit",
    "authenticator"
  ]
  
  depends_on = [
    aws_iam_role_policy_attachment.eks_cluster_policy
  ]
}

resource "aws_eks_node_group" "modax" {
  cluster_name    = aws_eks_cluster.modax.name
  node_group_name = "modax-workers"
  node_role_arn   = aws_iam_role.eks_nodes.arn
  subnet_ids      = aws_subnet.private[*].id
  
  scaling_config {
    desired_size = 3
    max_size     = 10
    min_size     = 2
  }
  
  instance_types = ["t3.large"]
  
  update_config {
    max_unavailable = 1
  }
}
```

#### 3. Amazon RDS (PostgreSQL/TimescaleDB)
```yaml
# infrastructure/aws/rds.tf
resource "aws_db_instance" "modax_timescale" {
  identifier     = "modax-timescale-db"
  engine         = "postgres"
  engine_version = "15.4"
  instance_class = "db.r6g.xlarge"
  
  allocated_storage     = 100
  max_allocated_storage = 1000
  storage_type          = "gp3"
  storage_encrypted     = true
  
  db_name  = "modax"
  username = "modax_admin"
  password = random_password.db_password.result
  
  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.modax.name
  
  backup_retention_period = 30
  backup_window          = "03:00-04:00"
  maintenance_window     = "Mon:04:00-Mon:05:00"
  
  enabled_cloudwatch_logs_exports = [
    "postgresql",
    "upgrade"
  ]
  
  multi_az = true
  
  # TimescaleDB extension
  parameter_group_name = aws_db_parameter_group.timescale.name
}

resource "aws_db_parameter_group" "timescale" {
  name   = "modax-timescale-params"
  family = "postgres15"
  
  parameter {
    name  = "shared_preload_libraries"
    value = "timescaledb"
  }
}
```

#### 4. Amazon S3 (Object Storage)
```yaml
# infrastructure/aws/s3.tf
resource "aws_s3_bucket" "modax_data" {
  bucket = "modax-sensor-data-${var.environment}"
  
  tags = {
    Name        = "MODAX Sensor Data"
    Environment = var.environment
  }
}

resource "aws_s3_bucket_versioning" "modax_data" {
  bucket = aws_s3_bucket.modax_data.id
  
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "modax_data" {
  bucket = aws_s3_bucket.modax_data.id
  
  rule {
    id     = "archive-old-data"
    status = "Enabled"
    
    transition {
      days          = 90
      storage_class = "GLACIER"
    }
    
    expiration {
      days = 365
    }
  }
}
```

#### 5. Amazon SageMaker (ML Training)
```yaml
# infrastructure/aws/sagemaker.tf
resource "aws_sagemaker_notebook_instance" "modax_ml" {
  name          = "modax-ml-training"
  instance_type = "ml.t3.xlarge"
  role_arn      = aws_iam_role.sagemaker.arn
  
  lifecycle_config_name = aws_sagemaker_notebook_instance_lifecycle_configuration.modax.name
  
  tags = {
    Name = "MODAX ML Training"
  }
}

resource "aws_sagemaker_model" "rul_predictor" {
  name               = "modax-rul-predictor"
  execution_role_arn = aws_iam_role.sagemaker.arn
  
  primary_container {
    image          = "${var.account_id}.dkr.ecr.${var.region}.amazonaws.com/modax-onnx-runtime:latest"
    model_data_url = "s3://${aws_s3_bucket.modax_models.bucket}/rul_predictor.tar.gz"
  }
}

resource "aws_sagemaker_endpoint_configuration" "rul_predictor" {
  name = "modax-rul-predictor-config"
  
  production_variants {
    variant_name           = "primary"
    model_name            = aws_sagemaker_model.rul_predictor.name
    initial_instance_count = 1
    instance_type         = "ml.m5.large"
  }
}

resource "aws_sagemaker_endpoint" "rul_predictor" {
  name                 = "modax-rul-predictor"
  endpoint_config_name = aws_sagemaker_endpoint_configuration.rul_predictor.name
}
```

### AWS Lambda Functions

```python
# lambda/sensor_data_processor.py
import json
import boto3
import os
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
timestream = boto3.client('timestream-write')
sns = boto3.client('sns')

def lambda_handler(event, context):
    """
    Process sensor data from IoT Core
    
    Triggered by IoT Rule when sensor data arrives
    """
    # Parse IoT message
    for record in event['Records']:
        payload = json.loads(record['Sns']['Message'])
        
        device_id = payload['device_id']
        sensor_data = payload['sensor_data']
        timestamp = payload['timestamp']
        
        # Write to Timestream
        write_to_timestream(device_id, sensor_data, timestamp)
        
        # Check for anomalies
        if is_anomaly(sensor_data):
            send_alert(device_id, sensor_data)
    
    return {
        'statusCode': 200,
        'body': json.dumps('Processed successfully')
    }

def write_to_timestream(device_id, sensor_data, timestamp):
    """Write sensor data to Amazon Timestream"""
    records = []
    
    for sensor, value in sensor_data.items():
        records.append({
            'Time': str(timestamp),
            'TimeUnit': 'MILLISECONDS',
            'Dimensions': [
                {'Name': 'device_id', 'Value': device_id},
                {'Name': 'sensor', 'Value': sensor}
            ],
            'MeasureName': 'value',
            'MeasureValue': str(value),
            'MeasureValueType': 'DOUBLE'
        })
    
    timestream.write_records(
        DatabaseName=os.environ['TIMESTREAM_DB'],
        TableName=os.environ['TIMESTREAM_TABLE'],
        Records=records
    )

def is_anomaly(sensor_data):
    """Simple anomaly detection"""
    if sensor_data.get('current_mean', 0) > 10.0:
        return True
    if sensor_data.get('temperature_mean', 0) > 80.0:
        return True
    return False

def send_alert(device_id, sensor_data):
    """Send alert via SNS"""
    sns.publish(
        TopicArn=os.environ['ALERT_TOPIC_ARN'],
        Subject=f'Anomaly Detected: {device_id}',
        Message=json.dumps(sensor_data, indent=2)
    )
```

## Azure Integration

### Architecture Components

#### 1. Azure IoT Hub
```bicep
// infrastructure/azure/iot-hub.bicep
resource iotHub 'Microsoft.Devices/IotHubs@2023-06-30' = {
  name: 'modax-iot-hub'
  location: resourceGroup().location
  sku: {
    name: 'S2'
    capacity: 2
  }
  properties: {
    eventHubEndpoints: {
      events: {
        retentionTimeInDays: 7
        partitionCount: 4
      }
    }
    routing: {
      endpoints: {
        eventHubs: [
          {
            name: 'sensor-data-hub'
            connectionString: eventHub.listKeys().primaryConnectionString
          }
        ]
      }
      routes: [
        {
          name: 'SensorDataRoute'
          source: 'DeviceMessages'
          condition: 'true'
          endpointNames: [
            'sensor-data-hub'
          ]
          isEnabled: true
        }
      ]
    }
    cloudToDevice: {
      maxDeliveryCount: 10
      defaultTtlAsIso8601: 'PT1H'
    }
  }
}
```

#### 2. Azure Kubernetes Service (AKS)
```bicep
// infrastructure/azure/aks.bicep
resource aks 'Microsoft.ContainerService/managedClusters@2023-08-01' = {
  name: 'modax-aks-cluster'
  location: resourceGroup().location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    dnsPrefix: 'modax'
    kubernetesVersion: '1.28.0'
    
    agentPoolProfiles: [
      {
        name: 'nodepool1'
        count: 3
        vmSize: 'Standard_DS3_v2'
        osType: 'Linux'
        mode: 'System'
        enableAutoScaling: true
        minCount: 2
        maxCount: 10
      }
    ]
    
    networkProfile: {
      networkPlugin: 'azure'
      serviceCidr: '10.0.0.0/16'
      dnsServiceIP: '10.0.0.10'
    }
    
    addonProfiles: {
      omsagent: {
        enabled: true
        config: {
          logAnalyticsWorkspaceResourceID: logAnalytics.id
        }
      }
      azurePolicy: {
        enabled: true
      }
    }
  }
}
```

#### 3. Azure Database for PostgreSQL
```bicep
// infrastructure/azure/postgres.bicep
resource postgresServer 'Microsoft.DBforPostgreSQL/flexibleServers@2023-03-01-preview' = {
  name: 'modax-postgres-server'
  location: resourceGroup().location
  sku: {
    name: 'Standard_D4ds_v4'
    tier: 'GeneralPurpose'
  }
  properties: {
    version: '15'
    administratorLogin: 'modaxadmin'
    administratorLoginPassword: keyVault.getSecret('postgres-admin-password')
    storage: {
      storageSizeGB: 128
      autoGrow: 'Enabled'
    }
    backup: {
      backupRetentionDays: 30
      geoRedundantBackup: 'Enabled'
    }
    highAvailability: {
      mode: 'ZoneRedundant'
    }
  }
}

resource postgresDatabase 'Microsoft.DBforPostgreSQL/flexibleServers/databases@2023-03-01-preview' = {
  parent: postgresServer
  name: 'modax'
}
```

#### 4. Azure Machine Learning
```bicep
// infrastructure/azure/ml-workspace.bicep
resource mlWorkspace 'Microsoft.MachineLearningServices/workspaces@2023-08-01-preview' = {
  name: 'modax-ml-workspace'
  location: resourceGroup().location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    friendlyName: 'MODAX ML Workspace'
    storageAccount: storageAccount.id
    keyVault: keyVault.id
    applicationInsights: appInsights.id
    containerRegistry: containerRegistry.id
  }
}

resource computeCluster 'Microsoft.MachineLearningServices/workspaces/computes@2023-08-01-preview' = {
  parent: mlWorkspace
  name: 'gpu-cluster'
  location: resourceGroup().location
  properties: {
    computeType: 'AmlCompute'
    properties: {
      vmSize: 'Standard_NC6s_v3'
      scaleSettings: {
        minNodeCount: 0
        maxNodeCount: 4
        nodeIdleTimeBeforeScaleDown: 'PT2M'
      }
    }
  }
}
```

## GCP Integration

### Architecture Components

#### 1. Cloud IoT Core (Legacy) / Cloud Pub/Sub
```yaml
# infrastructure/gcp/iot-registry.yaml
apiVersion: cloudiot.cnrm.cloud.google.com/v1beta1
kind: CloudIoTDeviceRegistry
metadata:
  name: modax-device-registry
spec:
  projectRef:
    external: projects/modax-production
  region: us-central1
  eventNotificationConfigs:
  - pubsubTopicRef:
      name: modax-sensor-data
  stateNotificationConfig:
    pubsubTopicRef:
      name: modax-device-state
  mqttConfig:
    mqttEnabledState: MQTT_ENABLED
  httpConfig:
    httpEnabledState: HTTP_ENABLED
```

#### 2. Google Kubernetes Engine (GKE)
```yaml
# infrastructure/gcp/gke-cluster.yaml
apiVersion: container.cnrm.cloud.google.com/v1beta1
kind: ContainerCluster
metadata:
  name: modax-gke-cluster
spec:
  location: us-central1
  initialNodeCount: 1
  releaseChannel:
    channel: REGULAR
  networkingMode: VPC_NATIVE
  ipAllocationPolicy:
    clusterIpv4CidrBlock: "/16"
    servicesIpv4CidrBlock: "/22"
  addonsConfig:
    horizontalPodAutoscaling:
      disabled: false
    httpLoadBalancing:
      disabled: false
    gcePersistentDiskCsiDriverConfig:
      enabled: true
  nodeConfig:
    machineType: n2-standard-4
    diskSizeGb: 100
    diskType: pd-standard
    oauthScopes:
    - "https://www.googleapis.com/auth/cloud-platform"
  autoscaling:
    enabled: true
    minNodeCount: 2
    maxNodeCount: 10
```

#### 3. Cloud SQL (PostgreSQL)
```yaml
# infrastructure/gcp/cloud-sql.yaml
apiVersion: sql.cnrm.cloud.google.com/v1beta1
kind: SQLInstance
metadata:
  name: modax-postgres-instance
spec:
  databaseVersion: POSTGRES_15
  region: us-central1
  settings:
    tier: db-custom-4-16384  # 4 vCPUs, 16GB RAM
    availabilityType: REGIONAL
    backupConfiguration:
      enabled: true
      startTime: "03:00"
      pointInTimeRecoveryEnabled: true
      backupRetentionSettings:
        retainedBackups: 30
    ipConfiguration:
      ipv4Enabled: true
      privateNetworkRef:
        name: modax-vpc
      authorizedNetworks: []
    diskSize: 100
    diskType: PD_SSD
    diskAutoresize: true
```

#### 4. Vertex AI
```python
# infrastructure/gcp/vertex_ai_setup.py
from google.cloud import aiplatform

def setup_vertex_ai():
    """Setup Vertex AI for MODAX ML training"""
    
    aiplatform.init(
        project='modax-production',
        location='us-central1',
        staging_bucket='gs://modax-ml-artifacts'
    )
    
    # Create custom training job
    job = aiplatform.CustomTrainingJob(
        display_name='modax-rul-training',
        container_uri='gcr.io/modax-production/ml-training:latest',
        requirements=['torch', 'onnx', 'pandas', 'scikit-learn'],
        model_serving_container_image_uri='gcr.io/modax-production/onnx-runtime:latest'
    )
    
    # Run training
    model = job.run(
        dataset=dataset,
        model_display_name='rul-predictor',
        replica_count=1,
        machine_type='n1-standard-8',
        accelerator_type='NVIDIA_TESLA_T4',
        accelerator_count=1
    )
    
    return model
```

## Deployment Strategies

### Hybrid Cloud
```yaml
# Multi-cloud deployment with Anthos/Arc/EKS Anywhere
apiVersion: v1
kind: Config
clusters:
- name: aws-eks-cluster
  cluster:
    server: https://eks.amazonaws.com
- name: azure-aks-cluster
  cluster:
    server: https://aks.azure.com
- name: gcp-gke-cluster
  cluster:
    server: https://gke.googleapis.com
contexts:
- name: modax-production
  context:
    cluster: aws-eks-cluster
    user: modax-admin
```

### Multi-Region Deployment
```yaml
# Deploy across multiple regions for HA
regions:
  primary:
    provider: aws
    region: us-east-1
    endpoints:
      - control-api.us-east-1.modax.com
      - ai-api.us-east-1.modax.com
  
  secondary:
    provider: aws
    region: eu-west-1
    endpoints:
      - control-api.eu-west-1.modax.com
      - ai-api.eu-west-1.modax.com
  
  tertiary:
    provider: azure
    region: westeurope
    endpoints:
      - control-api.westeurope.modax.com
      - ai-api.westeurope.modax.com
```

## Cost Optimization

### Resource Tagging
```yaml
# Tag all resources for cost tracking
tags:
  Project: MODAX
  Environment: Production
  CostCenter: Manufacturing
  Owner: operations@modax.com
  Tenant: ${tenant_id}
```

### Auto-Scaling Policies
```yaml
# Kubernetes HPA for cost optimization
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: modax-control-api
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: control-api
  minReplicas: 2
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
```

## Monitoring & Observability

### CloudWatch (AWS)
```python
# python-control-layer/cloud_metrics.py
import boto3

cloudwatch = boto3.client('cloudwatch')

def publish_metrics(tenant_id, device_id, metrics):
    """Publish metrics to CloudWatch"""
    cloudwatch.put_metric_data(
        Namespace='MODAX/Production',
        MetricData=[
            {
                'MetricName': 'DeviceTemperature',
                'Value': metrics['temperature'],
                'Unit': 'None',
                'Dimensions': [
                    {'Name': 'TenantId', 'Value': tenant_id},
                    {'Name': 'DeviceId', 'Value': device_id}
                ]
            },
            {
                'MetricName': 'DeviceCurrent',
                'Value': metrics['current'],
                'Unit': 'None',
                'Dimensions': [
                    {'Name': 'TenantId', 'Value': tenant_id},
                    {'Name': 'DeviceId', 'Value': device_id}
                ]
            }
        ]
    )
```

## Security Best Practices

### IAM Policies
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "iot:Connect",
        "iot:Publish",
        "iot:Subscribe",
        "iot:Receive"
      ],
      "Resource": [
        "arn:aws:iot:*:*:client/modax-${device-id}",
        "arn:aws:iot:*:*:topic/modax/${tenant-id}/*"
      ]
    },
    {
      "Effect": "Deny",
      "Action": "*",
      "Resource": "arn:aws:iot:*:*:topic/modax/${other-tenant-id}/*"
    }
  ]
}
```

### Secrets Management
```yaml
# Use cloud-native secrets managers
aws:
  secrets_manager: true
  kms_key_id: "arn:aws:kms:us-east-1:123456789012:key/abcd-1234"

azure:
  key_vault: true
  vault_uri: "https://modax-kv.vault.azure.net/"

gcp:
  secret_manager: true
  project_id: "modax-production"
```

## Related Documentation

- [High Availability](HIGH_AVAILABILITY.md)
- [Containerization](CONTAINERIZATION.md)
- [CI/CD Pipeline](CI_CD.md)
- [Monitoring](MONITORING.md)
- [Security](SECURITY.md)
