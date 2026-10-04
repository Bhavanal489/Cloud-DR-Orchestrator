from app.aws_client import get_route53_client


HOSTED_ZONE_NAME = "dr-orchestrator.local."
RECORD_NAME = "app.dr-orchestrator.local."


def get_hosted_zone_id():
    route53 = get_route53_client()

    response = route53.list_hosted_zones()

    matching_zones = [
        zone
        for zone in response["HostedZones"]
        if zone["Name"] == HOSTED_ZONE_NAME
    ]

    if not matching_zones:
        raise Exception("Hosted zone not found")

    # Use the most recently created matching zone.
    zone = matching_zones[-1]

    return zone["Id"].split("/")[-1]


def create_hosted_zone():
    route53 = get_route53_client()

    response = route53.create_hosted_zone(
        Name=HOSTED_ZONE_NAME,
        CallerReference="cloud-dr-orchestrator"
    )

    return {
        "hosted_zone_id": response["HostedZone"]["Id"],
        "name": response["HostedZone"]["Name"],
        "status": response["ChangeInfo"]["Status"]
    }


def list_hosted_zones():
    route53 = get_route53_client()

    response = route53.list_hosted_zones()

    return [
        {
            "id": zone["Id"],
            "name": zone["Name"]
        }
        for zone in response["HostedZones"]
    ]


def create_failover_records():
    route53 = get_route53_client()

    hosted_zone_id = get_hosted_zone_id()

    response = route53.change_resource_record_sets(
        HostedZoneId=hosted_zone_id,
        ChangeBatch={
            "Comment": "Cloud DR primary and backup failover records",
            "Changes": [
                {
                    "Action": "UPSERT",
                    "ResourceRecordSet": {
                        "Name": RECORD_NAME,
                        "Type": "A",
                        "SetIdentifier": "primary",
                        "Failover": "PRIMARY",
                        "TTL": 60,
                        "ResourceRecords": [
                            {
                                "Value": "127.0.0.1"
                            }
                        ]
                    }
                },
                {
                    "Action": "UPSERT",
                    "ResourceRecordSet": {
                        "Name": RECORD_NAME,
                        "Type": "A",
                        "SetIdentifier": "secondary",
                        "Failover": "SECONDARY",
                        "TTL": 60,
                        "ResourceRecords": [
                            {
                                "Value": "127.0.0.1"
                            }
                        ]
                    }
                }
            ]
        }
    )

    return {
        "hosted_zone_id": hosted_zone_id,
        "record_name": RECORD_NAME,
        "change_id": response["ChangeInfo"]["Id"],
        "status": response["ChangeInfo"]["Status"]
    }


def list_failover_records():
    route53 = get_route53_client()

    hosted_zone_id = get_hosted_zone_id()

    response = route53.list_resource_record_sets(
        HostedZoneId=hosted_zone_id
    )

    records = []

    for record in response["ResourceRecordSets"]:
        if record["Name"] == RECORD_NAME:
            records.append({
                "name": record["Name"],
                "type": record["Type"],
                "set_identifier": record.get("SetIdentifier"),
                "failover": record.get("Failover"),
                "ttl": record.get("TTL"),
                "values": record.get("ResourceRecords")
            })

    return records