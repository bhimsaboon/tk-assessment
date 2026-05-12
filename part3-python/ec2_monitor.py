#!/usr/bin/env python3
"""
EC2 CPU utilization monitor.

Features:
- Lists running EC2 instances.
- Fetches CloudWatch CPU metrics for last 1 hour in 5-minute intervals.
- Generates JSON report with avg/min/max CPU and alert flag.
- Supports CLI arguments for region, threshold, output path, and config file.
"""

from __future__ import annotations

import argparse
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError


LOGGER = logging.getLogger("ec2_monitor")


@dataclass
class InstanceSummary:
    instance_id: str
    name: str
    instance_type: str
    average_cpu: float
    min_cpu: float
    max_cpu: float
    alert: bool


def setup_logging(level: str) -> None:
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate CPU utilization report for running EC2 instances."
    )
    parser.add_argument("--region", required=True, help="AWS region, e.g. us-east-1")
    parser.add_argument(
        "--threshold",
        type=float,
        default=80.0,
        help="Alert threshold for average CPU usage percentage (default: 80)",
    )
    parser.add_argument(
        "--output",
        default="ec2_report.json",
        help="Output JSON file path (default: ec2_report.json)",
    )
    parser.add_argument(
        "--config",
        default="config.json",
        help="Path to JSON config file containing optional tag overrides",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level (default: INFO)",
    )
    return parser.parse_args()


def load_config(config_path: Path) -> dict[str, Any]:
    if not config_path.exists():
        LOGGER.warning("Config file %s not found; continuing with defaults.", config_path)
        return {}

    try:
        with config_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            LOGGER.warning("Config file %s is not a JSON object; ignoring.", config_path)
            return {}
        return data
    except (OSError, json.JSONDecodeError) as exc:
        LOGGER.error("Failed to load config file %s: %s", config_path, exc)
        return {}


def get_running_instances(ec2_client: Any) -> list[dict[str, Any]]:
    instances: list[dict[str, Any]] = []
    paginator = ec2_client.get_paginator("describe_instances")
    try:
        for page in paginator.paginate(
            Filters=[{"Name": "instance-state-name", "Values": ["running"]}]
        ):
            for reservation in page.get("Reservations", []):
                instances.extend(reservation.get("Instances", []))
    except (ClientError, BotoCoreError) as exc:
        raise RuntimeError(f"Failed to list running instances: {exc}") from exc
    return instances


def get_instance_name(instance: dict[str, Any]) -> str:
    for tag in instance.get("Tags", []):
        if tag.get("Key") == "Name":
            return str(tag.get("Value", ""))
    return "Unnamed"


def query_cpu_statistics(
    cloudwatch_client: Any,
    instance_id: str,
    start_time: datetime,
    end_time: datetime,
) -> tuple[float, float, float]:
    try:
        response = cloudwatch_client.get_metric_statistics(
            Namespace="AWS/EC2",
            MetricName="CPUUtilization",
            Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
            StartTime=start_time,
            EndTime=end_time,
            Period=300,
            Statistics=["Average", "Minimum", "Maximum"],
        )
    except (ClientError, BotoCoreError) as exc:
        raise RuntimeError(f"CloudWatch query failed for {instance_id}: {exc}") from exc

    datapoints = response.get("Datapoints", [])
    if not datapoints:
        return 0.0, 0.0, 0.0

    averages = [float(dp.get("Average", 0.0)) for dp in datapoints]
    minimums = [float(dp.get("Minimum", 0.0)) for dp in datapoints]
    maximums = [float(dp.get("Maximum", 0.0)) for dp in datapoints]

    avg_cpu = sum(averages) / len(averages)
    min_cpu = min(minimums)
    max_cpu = max(maximums)
    return avg_cpu, min_cpu, max_cpu


def build_report(
    region: str,
    threshold: float,
    instances: list[InstanceSummary],
    config: dict[str, Any],
) -> dict[str, Any]:
    generated_at = datetime.now(tz=timezone.utc).isoformat()
    return {
        "region": region,
        "generated_at_utc": generated_at,
        "alert_threshold": threshold,
        "notification_email": config.get("notification_email"),
        "instance_count": len(instances),
        "alerts": [entry.instance_id for entry in instances if entry.alert],
        "instances": [
            {
                "instance_id": entry.instance_id,
                "name": entry.name,
                "instance_type": entry.instance_type,
                "average_cpu": round(entry.average_cpu, 2),
                "min_cpu": round(entry.min_cpu, 2),
                "max_cpu": round(entry.max_cpu, 2),
                "alert": entry.alert,
            }
            for entry in sorted(instances, key=lambda i: i.average_cpu, reverse=True)
        ],
    }


def main() -> int:
    args = parse_args()
    setup_logging(args.log_level)
    config = load_config(Path(args.config))

    threshold = float(config.get("alert_threshold", args.threshold))
    tag_overrides = config.get("instance_tag_overrides", {})
    if not isinstance(tag_overrides, dict):
        LOGGER.warning("instance_tag_overrides should be an object; ignoring malformed value.")
        tag_overrides = {}

    LOGGER.info("Starting EC2 monitor for region %s", args.region)

    try:
        ec2_client = boto3.client("ec2", region_name=args.region)
        cloudwatch_client = boto3.client("cloudwatch", region_name=args.region)
    except (ClientError, BotoCoreError) as exc:
        LOGGER.error("Failed to initialize AWS clients: %s", exc)
        return 1

    try:
        running_instances = get_running_instances(ec2_client)
    except RuntimeError as exc:
        LOGGER.error("%s", exc)
        return 1

    end_time = datetime.now(tz=timezone.utc)
    start_time = end_time - timedelta(hours=1)

    summaries: list[InstanceSummary] = []
    for instance in running_instances:
        instance_id = instance.get("InstanceId", "unknown")
        instance_type = instance.get("InstanceType", "unknown")
        name = get_instance_name(instance)

        override = tag_overrides.get(instance_id, {})
        if isinstance(override, dict) and "Name" in override:
            name = str(override["Name"])

        try:
            avg_cpu, min_cpu, max_cpu = query_cpu_statistics(
                cloudwatch_client, instance_id, start_time, end_time
            )
        except RuntimeError as exc:
            LOGGER.error("%s", exc)
            continue

        summaries.append(
            InstanceSummary(
                instance_id=str(instance_id),
                name=name,
                instance_type=str(instance_type),
                average_cpu=avg_cpu,
                min_cpu=min_cpu,
                max_cpu=max_cpu,
                alert=avg_cpu > threshold,
            )
        )

    report = build_report(args.region, threshold, summaries, config)
    output_path = Path(args.output)
    try:
        output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    except OSError as exc:
        LOGGER.error("Failed to write output file %s: %s", output_path, exc)
        return 1

    LOGGER.info(
        "Report generated: %s (instances=%d, alerts=%d)",
        output_path,
        report["instance_count"],
        len(report["alerts"]),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

