# Part 2 - Linux System Administration

## A) Troubleshooting Scenario: EC2 Host `10.0.1.50` Unresponsive (SSH Timeout)

## Diagnostic Command Sequence (in order)

### 1) Verify reachability from jump host

```bash
# Basic reachability
ping -c 4 10.0.1.50

# TCP connectivity to SSH port
nc -zv -w 3 10.0.1.50 22

# Alternative TCP test if nc unavailable
timeout 5 bash -c 'cat < /dev/null > /dev/tcp/10.0.1.50/22' && echo "22 open" || echo "22 blocked"

# Route path and network hops
traceroute 10.0.1.50
ip route get 10.0.1.50
```

### 2) Validate AWS-side networking controls

```bash
# Check instance state and networking metadata
aws ec2 describe-instances --instance-ids i-xxxxxxxx \
  --query 'Reservations[].Instances[].{State:State.Name,PrivIP:PrivateIpAddress,Subnet:SubnetId,SG:SecurityGroups[*].GroupId,NACL:NetworkInterfaces[*].NetworkInterfaceId}'

# Review security group rules
aws ec2 describe-security-groups --group-ids sg-xxxxxxxx

# Review subnet route table associations and routes
aws ec2 describe-route-tables --filters "Name=association.subnet-id,Values=subnet-xxxxxxxx"

# Review NACLs for the subnet
aws ec2 describe-network-acls --filters "Name=association.subnet-id,Values=subnet-xxxxxxxx"
```

### 3) If network is confirmed, validate SSH service from console/SSM

```bash
# Check service status
sudo systemctl status sshd --no-pager

# Ensure daemon enabled
sudo systemctl is-enabled sshd

# Validate sshd configuration
sudo sshd -t

# Start/restart service if needed
sudo systemctl restart sshd
```

### 4) If SSH runs but connection still fails, investigate likely causes

Potential causes:
- Host firewall blocks source or port 22 (`ufw`/`iptables`/`nftables`).
- `sshd_config` denies user or source (`AllowUsers`, `DenyUsers`, `Match Address`).
- Disk full or inode exhaustion preventing session/log creation.
- CPU saturation or memory pressure causing process starvation.
- Security group/NACL ephemeral response port mismatch.

Commands:

```bash
# Firewall checks
sudo ufw status verbose || true
sudo iptables -S
sudo nft list ruleset

# SSH auth/access policy
sudo rg "^(AllowUsers|DenyUsers|PasswordAuthentication|PermitRootLogin|PubkeyAuthentication|Match)" /etc/ssh/sshd_config /etc/ssh/sshd_config.d/*.conf

# Listening socket
sudo ss -tulpen | rg ":22"
```

### 5) Check resource saturation (CPU, memory, disk)

```bash
# CPU/memory load
uptime
top -b -n1 | head -n 20
free -h
vmstat 1 5

# Disk/inode utilization
df -h
df -i
sudo du -xh /var --max-depth=2 | sort -h | tail -n 20
```

### 6) Review recent system and SSH logs

```bash
# Systemd journal (recent critical entries)
sudo journalctl -p err -S -2h --no-pager

# SSH service logs
sudo journalctl -u sshd -S -2h --no-pager

# Auth logs (distribution-dependent)
sudo rg -n "sshd|Failed password|Invalid user|Accepted" /var/log/auth.log /var/log/secure 2>/dev/null || true

# Kernel signals (OOM, ENI/network issues)
sudo dmesg --ctime | tail -n 100
```

## Suggested Resolution Flow

1. Restore network path (SG/NACL/route) if blocked.
2. Recover host resource pressure (clear disk, stop runaway process, reboot if required).
3. Correct SSH daemon/service config and restart.
4. Validate login with verbose SSH client:

```bash
ssh -vvv ec2-user@10.0.1.50
```

5. Add preventive controls: Alerts, log centralization, and SSM for emergency access.

