import docker
import urllib.request
import app.state as state

client = docker.from_env()

PRIMARY_URL = "http://primary:8000/health"


def retry_primary():
    try:
        with urllib.request.urlopen(PRIMARY_URL, timeout=3) as response:
            if response.status == 200:
                state.primary_status = "healthy"
                state.failure_type = None

                return {
                    "action": "retry",
                    "result": "primary_recovered"
                }

    except Exception:
        pass

    return {
        "action": "retry",
        "result": "primary_still_unavailable"
    }


def restart_application():
    try:
        primary = client.containers.get("primary-server")

        primary.restart()

        state.primary_status = "healthy"
        state.failure_type = None

        return {
            "action": "restart_application",
            "result": "application_restarted",
            "container": "primary-server"
        }

    except Exception as error:
        return {
            "action": "restart_application",
            "result": "failed",
            "error": str(error)
        }


def failover_to_backup():
    try:
        backup = client.containers.get("backup-server")

        backup.reload()

        if backup.status != "running":
            backup.start()

        state.primary_status = "failed"
        state.backup_status = "active"
        state.failure_type = None

        return {
            "action": "failover",
            "result": "backup_activated",
            "backup_container": "backup-server",
            "backup_status": "running"
        }

    except Exception as error:
        return {
            "action": "failover",
            "result": "failed",
            "error": str(error)
        }


def alert_operator():
    return {
        "action": "alert_operator",
        "result": "operator_notification_required"
    }