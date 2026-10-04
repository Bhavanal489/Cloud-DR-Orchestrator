# Cloud Disaster Recovery Orchestrator

A simplified automated disaster recovery and failover orchestration system built with **Python, FastAPI, Docker, Boto3, LocalStack, Route 53, and Slack**.

The system continuously monitors a primary service, detects failures, classifies them, performs the appropriate recovery action, activates a backup when required, switches traffic, and sends an alert.

## Key Features

- Automatic health monitoring every 5 seconds
- Automatic failure detection
- Failure classification
- Retry for transient failures
- Application restart for application failures
- Automatic failover for infrastructure failures
- Primary and backup services using Docker
- Automatic traffic switching through a local gateway
- Route 53 failover configuration using LocalStack
- Boto3 integration for AWS API interaction
- Slack notifications
- FastAPI orchestration API
- Docker Compose environment

## Architecture

```text
                 Primary Service
                       │
                       ▼
              Health Monitoring
                       │
                       ▼
              Failure Detection
                       │
                       ▼
              Failure Classifier
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
       Retry        Restart      Failover
                                    │
                                    ▼
                              Backup Service
                                    │
                                    ▼
                              Traffic Gateway
                                    │
                                    ▼
                              User Traffic

              ┌──────────────┐
              │  LocalStack  │
              │   Route 53   │
              └──────────────┘

              ┌──────────────┐
              │    Slack     │
              │   Alerts     │
              └──────────────┘
```

## Recovery Workflow

```text
Primary Service
      ↓
Health Monitoring
      ↓
Failure Detected
      ↓
Failure Classification
      ↓
Recovery Decision
      ↓
Retry / Restart / Failover
      ↓
Backup Activated (if required)
      ↓
Traffic Switched
      ↓
Slack Notification
```

### Failure Classification

| Failure Type | Recovery Action |
|---|---|
| Transient | Retry primary |
| Application | Restart application |
| Infrastructure | Failover to backup |
| Unknown | Alert operator |

The project includes a failure-classification layer so that the system does not blindly perform a full failover for every failure.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core orchestration logic |
| FastAPI | API and orchestration controller |
| Docker | Service containers |
| Docker Compose | Multi-container environment |
| Boto3 | AWS API interaction |
| LocalStack | Local AWS simulation |
| Route 53 | Failover configuration |
| Slack Webhook | Alerts |
| Uvicorn | Application server |

## Project Structure

```text
cloud-dr-orchestrator/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── state.py
│   ├── recovery.py
│   ├── aws_client.py
│   ├── route53_manager.py
│   └── slack_notifier.py
│
├── Dockerfile
├── docker-compose.yml
├── service.py
├── gateway.py
├── requirements.txt
├── .env
└── .gitignore
```

`.env` contains local secrets and should not be committed.

## Services

| Service | Purpose | Port |
|---|---|---:|
| Primary Server | Main application | 8001 |
| Backup Server | Recovery application | 8002 |
| DR Orchestrator | Monitoring and recovery | 8000 |
| DR Gateway | Traffic routing | 8080 |
| LocalStack | AWS/Route 53 simulation | 4566 |

## How to Run

### 1. Configure `.env`

```env
LOCALSTACK_AUTH_TOKEN=your_localstack_token
SLACK_WEBHOOK_URL=your_slack_webhook
```

### 2. Build and start

```powershell
docker compose up -d --build
```

Check the containers:

```powershell
docker compose ps
```

### 3. Check the monitor

```powershell
curl.exe http://localhost:8000/monitor/status
```

Expected:

```text
monitor: running
primary: healthy
backup: healthy
```

## Automatic Disaster Recovery Demo

The failure is manually injected only to reproduce a failure scenario. **Recovery itself is automatic.**

### 1. Verify primary traffic

```powershell
curl.exe http://localhost:8080/
```

Expected:

```text
active_backend: primary
```

### 2. Stop the primary

```powershell
docker stop primary-server
```

No recovery endpoint needs to be called.

The background monitor detects the failure automatically.

### 3. Verify backup traffic

Wait a few seconds and run:

```powershell
curl.exe http://localhost:8080/
```

Expected:

```text
active_backend: backup
```

### 4. Check Slack

The configured Slack channel receives:

```text
CLOUD DISASTER RECOVERY ALERT
Failure Type: infrastructure
Recovery Action: failover
Recovery Result: backup_activated
```

### 5. Restore the primary

```powershell
docker start primary-server
```

## Testing Failure Types

The simulation endpoint is available for controlled testing.

### Transient

```powershell
curl.exe -X POST "http://localhost:8000/simulate/failure?failure_type=transient"
```

Recovery action: **retry**

### Application

```powershell
curl.exe -X POST "http://localhost:8000/simulate/failure?failure_type=application"
```

Recovery action: **restart application**

### Infrastructure

```powershell
curl.exe -X POST "http://localhost:8000/simulate/failure?failure_type=infrastructure"
```

Recovery action: **failover**

## Important API Endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| `/health` | GET | Orchestrator health |
| `/infrastructure` | GET | Primary and backup status |
| `/monitor/status` | GET | Automatic monitor status |
| `/detect-failure` | GET | Detect failure |
| `/classify-failure` | GET | Classify failure |
| `/simulate/failure` | POST | Simulate failure |
| `/orchestrate-recovery` | POST | Manually trigger recovery for testing |
| `/aws/status` | GET | Check Route 53 connection |
| `/aws/route53/create-zone` | POST | Create hosted zone |
| `/aws/route53/zones` | GET | List hosted zones |
| `/aws/route53/create-failover-records` | POST | Create failover records |
| `/aws/route53/failover-records` | GET | View failover records |

## Route 53 with LocalStack

The project uses **Boto3** to interact with Route 53 through **LocalStack**.

It demonstrates:

- Hosted zone creation
- Primary and secondary failover records
- Listing hosted zones
- Listing failover records

The Route 53 portion is simulated locally with LocalStack. The Docker gateway provides the actual local traffic-switching demonstration between the primary and backup services.
