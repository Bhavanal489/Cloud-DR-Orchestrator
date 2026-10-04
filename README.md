# Cloud Disaster Recovery & Failover Orchestrator

An automated disaster recovery orchestration system that detects service failures, classifies the failure type, selects an appropriate recovery strategy, activates backup infrastructure when required, and notifies operators through Slack.

## Problem

Different failures require different recovery actions.

- A transient failure may require a retry.
- An application failure may require restarting the application.
- An infrastructure failure may require failing over to a backup service.

This project implements a simplified disaster recovery orchestration workflow that makes recovery decisions based on the detected failure type.

## Key Features

- Failure detection through health checks
- Failure classification
- Automated recovery orchestration
- Retry for transient failures
- Application restart for application failures
- Failover to backup for infrastructure failures
- Docker-based primary and backup services
- Automatic traffic switching through a gateway
- AWS Route 53 failover configuration using LocalStack
- Slack disaster recovery notifications
- REST API using FastAPI
- Docker Compose multi-service architecture

## Architecture

```text
Primary Service
      |
      v
Failure Detection
      |
      v
Failure Classifier
      |
      +------------------+---------------------+
      |                  |                     |
  Transient          Application        Infrastructure
      |                  |                     |
    Retry             Restart               Failover
                                            |
                                            v
                                      Backup Service
                                            |
                                            v
                                      Traffic Gateway
                                            |
                                            v
                                    Healthy Service

                    Recovery Result
                           |
                           v
                    Slack Notification
```

## Failure Classification

| Failure Type | Recovery Action |
|---|---|
| Transient | Retry primary |
| Application | Restart application |
| Infrastructure | Failover to backup |
| Unknown | Alert operator |

## Technology Stack

### Backend
- Python
- FastAPI
- Uvicorn

### Cloud / AWS
- AWS Boto3
- Amazon Route 53
- LocalStack

### Infrastructure
- Docker
- Docker Compose

### Notifications
- Slack Incoming Webhooks

## Project Structure

```text
cloud-dr-orchestrator/
│
├── app/
│   ├── __init__.py
│   ├── aws_client.py
│   ├── main.py
│   ├── recovery.py
│   ├── route53_manager.py
│   ├── slack_notifier.py
│   └── state.py
│
├── Dockerfile
├── docker-compose.yml
├── gateway.py
├── service.py
├── requirements.txt
├── .env
├── .gitignore
└── README.md
```

## Services

### Orchestrator
The central FastAPI service responsible for failure detection, classification, recovery decisions, and notifications.

### Primary Server
The main application service.

### Backup Server
The standby service used during infrastructure failure.

### Traffic Gateway
Checks the health of the primary and backup services and routes traffic to a healthy service.

### LocalStack
Provides a local simulation of AWS services used by the project, including Route 53.

## Recovery Workflow

```text
1. Detect failure
       ↓
2. Classify failure
       ↓
3. Select recovery strategy
       ↓
4. Execute recovery
       ↓
5. Activate backup if required
       ↓
6. Route traffic to healthy service
       ↓
7. Send Slack notification
```

## API Endpoints

### Health

```text
GET /health
```

### Infrastructure Status

```text
GET /infrastructure
```

### Simulate Failure

```text
POST /simulate/failure?failure_type=<type>
```

Supported failure types:

```text
transient
application
infrastructure
```

### Detect Failure

```text
GET /detect-failure
```

### Classify Failure

```text
GET /classify-failure
```

### Orchestrate Recovery

```text
POST /orchestrate-recovery
```

Runs the complete failure detection, classification, recovery, and notification workflow.

### Route 53

```text
GET  /aws/route53/zones
POST /aws/route53/create-zone

GET  /aws/route53/failover-records
POST /aws/route53/create-failover-records
```

## Running the Project

### Prerequisites

- Python
- Docker Desktop
- Docker Compose

### Environment Variables

Create a `.env` file:

```env
LOCALSTACK_AUTH_TOKEN=your_localstack_token
SLACK_WEBHOOK_URL=your_slack_webhook_url
```

Do not commit `.env` to Git.

### Start the System

```bash
docker compose up -d --build
```

### Check Services

```bash
docker compose ps
```

The system uses:

```text
Orchestrator → http://localhost:8000
Primary      → http://localhost:8001
Backup       → http://localhost:8002
Gateway      → http://localhost:8080
LocalStack   → http://localhost:4566
```

## Example: Infrastructure Failure

Simulate an infrastructure failure:

```bash
curl -X POST "http://localhost:8000/simulate/failure?failure_type=infrastructure"
```

Run recovery:

```bash
curl -X POST "http://localhost:8000/orchestrate-recovery"
```

The orchestrator:

1. Detects the failure.
2. Classifies it as an infrastructure failure.
3. Selects failover.
4. Activates the backup service.
5. Sends a Slack notification.

## Testing

The system was tested with three failure scenarios.

### 1. Transient Failure

```text
Failure → Retry → Primary Recovery
```

### 2. Application Failure

```text
Failure → Application Restart → Recovery
```

### 3. Infrastructure Failure

```text
Failure → Failover → Backup Activation
```

The infrastructure failure was also tested by actually stopping the primary Docker container and verifying that the gateway switched traffic to the backup service.

## AWS Route 53 Simulation

AWS Route 53 functionality is demonstrated locally using LocalStack.

The project creates:

- A hosted zone
- A PRIMARY failover record
- A SECONDARY failover record

This allows the Route 53 failover configuration to be developed and tested locally without deploying production AWS infrastructure.

## Design Consideration

Cloud providers already provide disaster recovery and failover mechanisms. This project does not attempt to replace those systems.

Instead, it implements a simplified orchestration layer to demonstrate:

- Failure detection
- Failure classification
- Automated recovery decisions
- Service failover
- Cloud API interaction
- Infrastructure automation
- Operational notifications

## Future Improvements

- Persistent state storage
- Multi-region infrastructure
- Advanced health checks
- Recovery Time Objective (RTO) monitoring
- Recovery Point Objective (RPO) tracking
- Authentication and role-based access
- Metrics and monitoring
- Automated recovery testing
- Kubernetes-based deployment