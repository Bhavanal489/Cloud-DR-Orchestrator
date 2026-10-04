from fastapi import FastAPI
import app.state as state
import app.recovery as recovery
import urllib.request
import asyncio
from contextlib import asynccontextmanager

from app.aws_client import get_route53_client

from app.route53_manager import (
    create_hosted_zone,
    list_hosted_zones,
    create_failover_records,
    list_failover_records
)

from app.slack_notifier import send_slack_alert


PRIMARY_URL = "http://primary:8000/health"
BACKUP_URL = "http://backup:8000/health"

MONITOR_INTERVAL = 5


def check_service(url):
    try:
        with urllib.request.urlopen(url, timeout=3) as response:
            return response.status == 200
    except Exception:
        return False


def classify_failure_type():

    if state.failure_type == "transient":
        return {
            "classification": "transient",
            "recommended_action": "retry"
        }

    if state.failure_type == "application":
        return {
            "classification": "application",
            "recommended_action": "restart_application"
        }

    if state.failure_type == "infrastructure":
        return {
            "classification": "infrastructure",
            "recommended_action": "failover"
        }

    return {
        "classification": "unknown",
        "recommended_action": "alert_operator"
    }


def perform_recovery():

    classification_result = classify_failure_type()

    classification = classification_result["classification"]
    action = classification_result["recommended_action"]

    if action == "retry":
        recovery_result = recovery.retry_primary()

    elif action == "restart_application":
        recovery_result = recovery.restart_application()

    elif action == "failover":
        recovery_result = recovery.failover_to_backup()

    else:
        recovery_result = recovery.alert_operator()

    slack_message = (
        "🚨 CLOUD DISASTER RECOVERY ALERT\n"
        f"Failure Type: {classification}\n"
        f"Recovery Action: {action}\n"
        f"Recovery Result: {recovery_result.get('result')}\n"
    )

    slack_result = send_slack_alert(slack_message)

    return {
        "failure_detected": True,
        "classification": classification,
        "action": action,
        "recovery": recovery_result,
        "notification": slack_result
    }


def run_automatic_recovery():

    primary_healthy = check_service(PRIMARY_URL)

    failure_detected = (
        not primary_healthy
        or state.failure_type is not None
    )

    if not failure_detected:
        return {
            "failure_detected": False,
            "status": "healthy"
        }

    # If the primary is actually unavailable and
    # no simulated failure type was supplied,
    # treat it as an infrastructure failure.
    if not primary_healthy and state.failure_type is None:
        state.failure_type = "infrastructure"

    return perform_recovery()


async def monitor_primary():

    recovery_triggered = False

    while True:

        try:
            primary_healthy = check_service(PRIMARY_URL)

            # Primary is healthy.
            if primary_healthy:
                recovery_triggered = False

                await asyncio.sleep(MONITOR_INTERVAL)
                continue

            # Primary has failed.
            if not recovery_triggered:

                print("⚠️ Primary failure detected automatically.")

                # If there is no simulated failure type,
                # classify an actual service outage as infrastructure failure.
                if state.failure_type is None:
                    state.failure_type = "infrastructure"

                print(
                    f"🔎 Failure classified as: "
                    f"{state.failure_type}"
                )

                recovery_triggered = True

                result = await asyncio.to_thread(
                    perform_recovery
                )

                print(
                    "🔄 Automatic recovery result:",
                    result
                )

            await asyncio.sleep(MONITOR_INTERVAL)

        except Exception as error:

            print(
                "❌ Monitoring error:",
                error
            )

            await asyncio.sleep(MONITOR_INTERVAL)


@asynccontextmanager
async def lifespan(app: FastAPI):

    print("🚀 Cloud DR automatic monitor started.")

    monitor_task = asyncio.create_task(
        monitor_primary()
    )

    yield

    monitor_task.cancel()

    try:
        await monitor_task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="Cloud Disaster Recovery Orchestrator",
    description="Automated cloud disaster recovery and failover system",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/health")
def health_check():

    return {
        "status": "healthy",
        "service": "cloud-dr-orchestrator"
    }


@app.get("/infrastructure")
def infrastructure_status():

    primary_healthy = check_service(PRIMARY_URL)
    backup_healthy = check_service(BACKUP_URL)

    return {
        "primary": "healthy" if primary_healthy else "failed",
        "backup": "healthy" if backup_healthy else "failed",
        "failure_type": state.failure_type
    }


@app.post("/simulate/failure")
def simulate_failure(
    failure_type: str = "infrastructure"
):

    allowed_types = [
        "transient",
        "application",
        "infrastructure"
    ]

    if failure_type not in allowed_types:

        return {
            "status": "failed",
            "message": "Invalid failure type",
            "allowed_types": allowed_types
        }

    state.primary_status = "failed"
    state.failure_type = failure_type

    return {
        "status": "failure_simulated",
        "failure_type": failure_type,
        "primary": "failed"
    }


@app.get("/detect-failure")
def detect_failure():

    primary_healthy = check_service(PRIMARY_URL)

    simulated_failure = (
        state.failure_type is not None
    )

    return {
        "failure_detected": (
            not primary_healthy
            or simulated_failure
        ),
        "primary": (
            "healthy"
            if primary_healthy
            else "failed"
        ),
        "failure_type": state.failure_type
    }


@app.get("/classify-failure")
def classify_failure():

    primary_healthy = check_service(PRIMARY_URL)

    if primary_healthy and state.failure_type is None:

        return {
            "failure_detected": False,
            "classification": "none",
            "recommended_action": "continue_monitoring"
        }

    # Actual primary outage without a manually
    # simulated type.
    if not primary_healthy and state.failure_type is None:
        state.failure_type = "infrastructure"

    classification_result = classify_failure_type()

    return {
        "failure_detected": True,
        "classification": (
            classification_result["classification"]
        ),
        "recommended_action": (
            classification_result["recommended_action"]
        )
    }


@app.post("/recover")
def recover():

    if state.failure_type == "transient":
        return recovery.retry_primary()

    if state.failure_type == "application":
        return recovery.restart_application()

    if state.failure_type == "infrastructure":
        return recovery.failover_to_backup()

    return recovery.alert_operator()


@app.post("/orchestrate-recovery")
def orchestrate_recovery():

    primary_healthy = check_service(PRIMARY_URL)

    failure_detected = (
        not primary_healthy
        or state.failure_type is not None
    )

    if not failure_detected:

        return {
            "failure_detected": False,
            "status": "healthy",
            "message": "Primary is operating normally"
        }

    if not primary_healthy and state.failure_type is None:
        state.failure_type = "infrastructure"

    return perform_recovery()


@app.get("/monitor/status")
def monitor_status():

    primary_healthy = check_service(PRIMARY_URL)
    backup_healthy = check_service(BACKUP_URL)

    return {
        "monitor": "running",
        "monitor_interval_seconds": MONITOR_INTERVAL,
        "primary": (
            "healthy"
            if primary_healthy
            else "failed"
        ),
        "backup": (
            "healthy"
            if backup_healthy
            else "failed"
        ),
        "failure_type": state.failure_type
    }


@app.get("/aws/status")
def aws_status():

    try:

        route53 = get_route53_client()

        response = route53.list_hosted_zones()

        return {
            "aws_connection": "successful",
            "service": "route53",
            "hosted_zones": len(
                response["HostedZones"]
            )
        }

    except Exception as error:

        return {
            "aws_connection": "failed",
            "error": str(error)
        }


@app.post("/aws/route53/create-zone")
def create_route53_zone():

    try:

        return {
            "status": "success",
            "route53": create_hosted_zone()
        }

    except Exception as error:

        return {
            "status": "failed",
            "error": str(error)
        }


@app.get("/aws/route53/zones")
def get_route53_zones():

    try:

        return {
            "status": "success",
            "zones": list_hosted_zones()
        }

    except Exception as error:

        return {
            "status": "failed",
            "error": str(error)
        }


@app.post("/aws/route53/create-failover-records")
def create_route53_failover_records():

    try:

        return {
            "status": "success",
            "route53": create_failover_records()
        }

    except Exception as error:

        return {
            "status": "failed",
            "error": str(error)
        }


@app.get("/aws/route53/failover-records")
def get_route53_failover_records():

    try:

        return {
            "status": "success",
            "records": list_failover_records()
        }

    except Exception as error:

        return {
            "status": "failed",
            "error": str(error)
        }