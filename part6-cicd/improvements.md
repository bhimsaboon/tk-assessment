# Part 6 - CI/CD Pipeline Review

## Problems in Current Pipeline (Minimum 4)

1. **No dependency pinning or reproducible builds**
   - `pip install -r requirements.txt` with unpinned dependencies can introduce drift and break deploys.

2. **No security scanning**
   - Pipeline lacks SAST, dependency vulnerability scanning, secrets scanning, and container/image checks.

3. **No environment separation or promotion path**
   - Direct deploy on push to `main` with no `dev -> staging -> prod` flow.

4. **No approval gates**
   - Production deployment has no manual approval, change control, or protected environment workflow.

5. **No rollback strategy**
   - Commented direct rsync deploy implies no versioned artifact and no automated rollback.

6. **No deployment safety mechanisms**
   - No health verification, canary/blue-green rollout, or post-deploy smoke test.

7. **No observability feedback loop**
   - No release annotations, metrics checks, or alert integration tied to deployment quality.

## Production-Ready CI/CD Design

## 1) Pipeline Stages

1. **Validate**
   - Lint, formatting, static analysis.
   - Unit tests and coverage threshold.
2. **Security**
   - SAST and dependency scan.
   - Secret scan on code and workflow definitions.
3. **Build**
   - Build versioned artifact/container image.
   - Sign artifact/image and generate SBOM.
4. **Deploy Dev**
   - Auto deploy from main branch.
   - Run smoke and integration tests.
5. **Promote to Staging**
   - Triggered promotion using same immutable artifact.
   - Run end-to-end and performance sanity tests.
6. **Promote to Prod**
   - Manual approval required via protected environment.
   - Progressive rollout and automated health verification.

## 2) Security Scanning Recommendations

- **Code scanning:** CodeQL or Semgrep.
- **Dependency scanning:** `pip-audit`, Dependabot, or Snyk.
- **Secrets scanning:** Gitleaks/TruffleHog.
- **Container scanning:** Trivy/Grype before push and before deploy.
- **IaC scanning:** Checkov/tfsec if Terraform/Kubernetes manifests are present.

## 3) Testing Strategy

- Fast unit tests on every PR.
- Integration tests in ephemeral or shared test environment.
- Contract/API tests for backend stability.
- Smoke tests immediately after each environment deployment.
- Coverage threshold enforcement and flaky test quarantine policy.

## 4) Approval Gates

- PR review requirements (minimum reviewers + CODEOWNERS).
- Required status checks must pass before merge.
- Protected GitHub environments:
  - `staging`: optional manual approval for high-risk changes
  - `production`: mandatory manual approval by authorized reviewers
- Change windows and incident freeze checks for production deploys.

## 5) Rollback Mechanism

- Use immutable versioned releases (tagged image per commit SHA).
- Keep previous stable artifact readily deployable.
- Deploy with rolling/canary strategy.
- If health checks fail:
  - automatic rollback to previous stable version
  - alert on-call and annotate incident timeline

## 6) Environment Promotion (`dev -> staging -> prod`)

Core principle: **build once, promote same artifact**.

- `dev`: auto from main after tests/security pass.
- `staging`: promotion job using same artifact digest/tag.
- `prod`: approved promotion of same staging-validated artifact.

This avoids environment drift and ensures production runs the exact artifact already validated upstream.

## Example Improved Workflow Outline

```yaml
name: Backend CI/CD
on:
  pull_request:
  push:
    branches: [main]

jobs:
  validate-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install -r requirements.txt
      - run: pytest -q

  security-scan:
    runs-on: ubuntu-latest
    needs: [validate-and-test]
    steps:
      - uses: actions/checkout@v4
      - run: echo "Run SAST + dependency + secrets scan here"

  build:
    runs-on: ubuntu-latest
    needs: [security-scan]
    steps:
      - uses: actions/checkout@v4
      - run: echo "Build and publish immutable artifact/image"

  deploy-dev:
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    needs: [build]
    environment: dev
    steps:
      - run: echo "Deploy to dev and run smoke tests"

  deploy-staging:
    runs-on: ubuntu-latest
    needs: [deploy-dev]
    environment: staging
    steps:
      - run: echo "Promote same artifact to staging"

  deploy-prod:
    runs-on: ubuntu-latest
    needs: [deploy-staging]
    environment: production
    steps:
      - run: echo "Manual approval gate + progressive rollout + rollback hooks"
```

