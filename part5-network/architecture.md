# Part 5 - Redundant DNS Architecture Design

## Objective

Design a highly available, cost-conscious DNS architecture that removes the single Unbound EC2 dependency and improves resilience and latency for Nepal-based users.

## Proposed Architecture (AWS Route 53)

```text
                  +-------------------------------+
                  |  Route 53 Hosted Zone         |
                  |  (techkraft.com)              |
                  +-------------------------------+
                         /                 \
                        /                   \
         +------------------------+   +------------------------+
         | Primary Record Set     |   | Secondary Record Set   |
         | (Failover PRIMARY)     |   | (Failover SECONDARY)   |
         | -> ALB/API endpoint A  |   | -> ALB/API endpoint B  |
         +------------------------+   +------------------------+
                    |                           |
                    | Health Check A            | Health Check B
                    v                           v
          +------------------+         +------------------+
          | Region A         |         | Region B         |
          | (e.g. ap-south-1)|         | (e.g. ap-southeast-1) |
          +------------------+         +------------------+
```

## Key Components and Purpose

1. **Route 53 Public Hosted Zone**
   - Authoritative DNS for public domains.
   - Managed, globally distributed, and highly available.

2. **Failover Routing Policy**
   - Primary record points to preferred regional endpoint.
   - Secondary record activates automatically when primary health checks fail.

3. **Route 53 Health Checks**
   - HTTP/HTTPS health checks against `/health` endpoint.
   - Can include CloudWatch alarm-based health checks for deeper signal integration.

4. **Regional Application Endpoints**
   - Two AWS regions for resilience:
     - Primary: `ap-south-1` (Mumbai) for lower Nepal latency.
     - Secondary: `ap-southeast-1` (Singapore) as disaster recovery target.

5. **Optional Enhancement: Latency-Based Routing**
   - If both regions are active-active, use latency-based policies plus health checks.
   - Nepal users generally route to Mumbai with lower RTT than many alternatives.

## Failover Logic

1. Client queries `api.techkraft.com`.
2. Route 53 returns primary endpoint when health check is healthy.
3. If primary health check fails configured thresholds, Route 53 serves secondary record.
4. Once primary recovers and passes checks, traffic can automatically revert to primary.

Suggested health check tuning:
- Request interval: 30s (10s optional for faster failover, higher cost)
- Failure threshold: 3
- Endpoint path: `/health`
- Protocol: HTTPS where available

## Latency Considerations for Nepal / South Asia

- **Primary region recommendation:** `ap-south-1` (Mumbai) due to geographic proximity and generally favorable network latency from Nepal.
- **Secondary region:** `ap-southeast-1` (Singapore) for regional diversification and robust AWS footprint.
- Use short-to-moderate DNS TTL (e.g., 30-60s for failover records) to improve switchover responsiveness.
- Validate from Nepal ISP networks using synthetic probes for real RTT data before finalizing.

## Rough Monthly Cost Estimate

Approximate Route 53 DNS-only cost (varies by query volume):

1. Hosted zone: ~$0.50/month per hosted zone
2. DNS queries: usage-based (commonly a few dollars to tens of dollars at moderate scale)
3. Health checks:
   - Standard checks: roughly ~$0.50/check/month (region and advanced settings can vary)
   - Two checks for primary/secondary endpoints: ~$1.00/month baseline

Estimated baseline (light/moderate usage): **~$5-25/month** for DNS and health checks, excluding ALB/compute costs.

## Implementation Timeline

### Phase 1 (Day 1-2): Design and Validation
- Finalize domain/subdomain cutover plan.
- Validate application health endpoint behavior.
- Confirm region selection with basic latency tests.

### Phase 2 (Day 3-4): Build in Parallel
- Create hosted zone records and health checks.
- Stand up secondary regional endpoint.
- Configure failover policies and TTL.

### Phase 3 (Day 5): Testing
- Perform controlled failover simulation.
- Verify DNS response changes and service continuity.
- Validate monitoring and alerting.

### Phase 4 (Day 6): Production Cutover
- Shift authoritative records/cnames.
- Monitor for anomalies.
- Keep rollback path available through previous DNS setup until stable window passes.

