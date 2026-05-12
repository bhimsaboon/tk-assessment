# Part 1 - Terraform Infrastructure Analysis

## Security Issues (Minimum 6)

1. **SSH exposed to the internet**  
   `aws_security_group.web` allows inbound TCP/22 from `0.0.0.0/0`, enabling brute-force and scanning risk.

2. **HTTP exposed globally**  
   Inbound TCP/80 is open to `0.0.0.0/0` and there is no HTTPS enforcement or ALB/WAF fronting.

3. **Database credentials hardcoded in Terraform**  
   `username = "admin"` and `password = "changeme123"` are static, weak, and likely end up in state files/version control for viewing.

4. **RDS shares same security group as web tier**  
   `vpc_security_group_ids = [aws_security_group.web.id]` breaks tier isolation and expands attack surface.

5. **No RDS backup retention**  
   `backup_retention_period = 0` disables point-in-time recovery, creating high operational and data-loss risk.

6. **RDS deletion protection disabled**  
   `deletion_protection = false` can allow accidental destructive changes.

7. **RDS final snapshot disabled**  
   `skip_final_snapshot = true` prevents last-resort data recovery on deletion.

8. **No encryption controls defined**  
   Missing explicit encryption-at-rest flags for RDS and S3 hardening controls (SSE, bucket policy, block public access).

9. **S3 bucket name globally fixed and no protections**  
   `bucket = "techkraft-uploads"` may collide and has no versioning, lifecycle, encryption, access policy, or public access blocks.

10. **Static AMI reference**  
    Fixed AMI ID with no lifecycle strategy can drift into unpatched images and region lock.

## Architectural Problems (Minimum 5)

1. **Public-subnet-only architecture**  
   No private subnets for app/database tiers; all compute appears internet-routable/exposed.

2. **No load balancer for web tier**  
   Three instances exist but no ALB/NLB for distribution, health checks, or graceful failover.

3. **No autoscaling strategy**  
   `count = 3` is static and does not adapt to traffic/load.

4. **Database not isolated in private subnets**  
   No DB subnet group or dedicated private network boundary for RDS.

5. **Missing high availability controls on stateful services**  
   No Multi-AZ for RDS and no explicit resilience policies.

6. **No observability stack**  
   Missing CloudWatch alarms, logs, metrics dashboards, and alerting integrations.

7. **No IAM least-privilege strategy shown**  
   Instances do not define IAM roles/instance profiles for controlled AWS API access.

8. **No tagging standards or environment separation**  
   Hard to manage cost allocation, operations, and policy automation without standard tags.

9. **No outputs for critical operations**  
    Outputs do not include public endpoints, ALB DNS, SG IDs, or DB endpoint needed for automation and operations.

## Production-Readiness Changes

### 1) Network and Segmentation
- Create multi-AZ VPC design:
  - Public subnets: ALB, NAT gateways
  - Private app subnets: EC2/ECS services
  - Private data subnets: RDS
- Add route tables per tier and restrict east-west traffic through explicit SG rules.

### 2) Secure Access Model  
- Remove SSH from public internet; use AWS Systems Manager Session Manager or bastion with allowlisted source ranges.
- Separate security groups by tier:
  - ALB SG: 80/443 from internet
  - App SG: app port only from ALB SG
  - DB SG: 3306 only from App SG

### 3) Database Hardening  
- Move secrets to AWS Secrets Manager or SSM Parameter Store.
- Enable:
  - `deletion_protection = true`
  - `backup_retention_period >= 7`
  - `storage_encrypted = true`
  - Multi-AZ for production
  - Final snapshot on deletion

### 4) Storage and Data Protection
- Harden S3 with:
  - Block public access (all)
  - Bucket encryption (SSE-KMS)
  - Versioning enabled
  - Least-privilege bucket policy
  - Optional lifecycle transitions

### 5) Compute and Traffic Management
- Replace static EC2 `count` with Auto Scaling Group behind ALB.
- Add target group health checks and rolling/blue-green deployment support.

### 6) Observability and Operations
- Add Monitoring metrics/alarms:
  - EC2 CPU/memory/disk (via agent)
  - ALB 4xx/5xx and latency
  - RDS CPU/connections/storage
- Centralize logs in Monitoring (CloudWatch) Logs and enable alert routing (SNS/Slack/Mattermost).

### 7) IaC Governance
- Use remote Terraform backend (S3 + DynamoDB lock table).
- Pin provider versions and enforce formatting/linting in CI.
- Add reusable modules and environment workspaces (dev/staging/prod).
- Enforce policy checks (e.g., tfsec/checkov, OPA/Sentinel where available).

### 8) DNS Resiliency
- Replace single EC2 Unbound dependency with Route 53 managed zones and health-check-based failover/latency routing.

