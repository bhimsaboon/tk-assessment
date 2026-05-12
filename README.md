# TechKraft Take-Home Assignment Submission

Name: Mohan Khadka
Contact: +977-9841098413
Email: moriartysh147@gmail.com

## Overview

This repository contains my completed solution for the Senior DevOps/Infrastructure Engineer take-home assessment. I focused on production-readiness, security, and practical implementation details aligned with TechKraft's current operating model.

## Repository Structure

```text
.
├── README.md
├── part1-terraform/
│   └── analysis.md
├── part2-linux/
│   ├── troubleshooting.md
│   └── Dockerfile
├── part3-python/
│   ├── ec2_monitor.py
│   └── config.json
├── part4-bash/
│   └── analyze_nginx_logs.sh
├── part5-network/
│   └── architecture.md
├── part6-cicd/
│   └── improvements.md
└── k8s/
    └── deployment.yaml
```

## Part-by-Part Summary

### Part 1 - Terraform Infrastructure Analysis
- Identified security vulnerabilities (open SSH to internet, hardcoded DB credentials, no encryption controls, no backups, weak lifecycle protections).
- Identified architectural gaps (public-only topology, no private subnets, no load balancing, missing HA patterns, weak observability posture).
- Proposed a production-ready remediation plan emphasizing least privilege, segmented networking, managed services, and IaC best practices.

### Part 2 - Linux Administration + Docker
- Provided a structured troubleshooting runbook for an unreachable EC2 host.
- Included exact command order from network layer checks through service-level diagnosis.
- Built a secure multi-stage Dockerfile for Flask on Python 3.11 with non-root runtime and health checks.

### Part 3 - Python Scripting
- Implemented `ec2_monitor.py` using `boto3` and CloudWatch metrics.
- Added CLI flags (`--region`, `--threshold`, `--output`, `--config`) using argparse.
- Report includes instance metadata and avg/min/max CPU with alerting flag based on threshold.
- Included better error handling and logging.

### Part 4 - Bash Scripting
- Implemented log analyzer supporting configurable log path input.
- Provides top IPs, top endpoints, and 4xx/5xx percentage summary.
- Uses standard Linux tools (`awk`, `sed`, `sort`, `uniq`) and handles malformed entries safely.

### Part 5 - Network Architecture Design
- Designed Route 53-based redundant DNS with health checks and failover.
- Included South Asia latency considerations and a rough monthly cost estimate.
- Added implementation timeline with staged rollout approach.

### Part 6 - CI/CD Review
- Identified current pipeline risks and anti-patterns.
- Proposed production-grade CI/CD design with security scanning, test gates, approvals, progressive deployment, and rollback mechanisms.

### Bonus - Kubernetes
- Included Deployment, Service, ConfigMap, and HPA resources.
- Configured probes, resource requests/limits, and minimum replica constraints.

## Assumptions

- AWS account has IAM permissions to create VPC networking, EC2, Route 53, CloudWatch, and RDS resources.
- Existing workloads can be migrated in phased fashion with planned maintenance windows.
- Container registry and image build process are available for CI/CD pipeline integration.
- Application can expose `/health` endpoint for probe usage and load balancer checks.

## Time Spent

- Part 1: 30 min
- Part 2: 25 min
- Part 3: 30 min
- Part 4: 20 min
- Part 5: 20 min
- Part 6: 15 min
- Buffer and final review: 10 min

Total: 150 minutes

## Tools and Versions Used

- Python 3.11+
- Bash 5.x
- AWS CLI v2 (for validation assumptions)
- `boto3` (Python AWS SDK)
- Linux utilities: `awk`, `sed`, `sort`, `uniq`, `wc`

