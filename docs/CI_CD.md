# MODAX CI/CD Pipeline

## Overview
This document describes the Continuous Integration and Continuous Deployment (CI/CD) strategy for the MODAX industrial control system. The CI/CD pipeline ensures code quality, automated testing, and reliable deployment across all system components.

## CI/CD Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ Source Control (GitHub)                                      │
│ - Feature branches                                          │
│ - Pull requests                                             │
│ - Main/Release branches                                     │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────────────┐
│ CI Pipeline (GitHub Actions)                                │
│                                                             │
│ ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐│
│ │ Lint & Format   │→ │ Build & Test    │→ │ Security Scan││
│ │ - flake8        │  │ - pytest        │  │ - Bandit     ││
│ │ - black         │  │ - coverage      │  │ - Safety     ││
│ │ - mypy          │  │ - integration   │  │ - Trivy      ││
│ └─────────────────┘  └─────────────────┘  └──────────────┘│
└────────────────┬────────────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────────────┐
│ CD Pipeline                                                 │
│                                                             │
│ ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐│
│ │ Build Images    │→ │ Push to Registry│→ │ Deploy       ││
│ │ - Docker build  │  │ - Docker Hub    │  │ - Staging    ││
│ │ - Tag versions  │  │ - Private reg   │  │ - Production ││
│ └─────────────────┘  └─────────────────┘  └──────────────┘│
└─────────────────────────────────────────────────────────────┘
```

## GitHub Actions Workflows

### 1. Python CI Workflow

#### .github/workflows/python-ci.yml
```yaml
name: Python CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  lint-and-test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.9', '3.10', '3.11']
        component: ['python-control-layer', 'python-ai-layer']
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      
      - name: Cache pip packages
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
          restore-keys: |
            ${{ runner.os }}-pip-
      
      - name: Install dependencies
        run: |
          cd ${{ matrix.component }}
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-cov flake8 black mypy bandit
      
      - name: Lint with flake8
        run: |
          cd ${{ matrix.component }}
          # Stop on syntax errors or undefined names
          flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
          # Exit-zero treats all errors as warnings
          flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
      
      - name: Check formatting with black
        run: |
          cd ${{ matrix.component }}
          black --check --diff .
      
      - name: Type checking with mypy
        run: |
          cd ${{ matrix.component }}
          mypy . --ignore-missing-imports || true
      
      - name: Security scan with bandit
        run: |
          cd ${{ matrix.component }}
          bandit -r . -f json -o bandit-report.json || true
      
      - name: Run tests with coverage
        run: |
          cd ${{ matrix.component }}
          pytest --cov=. --cov-report=xml --cov-report=term
      
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: ./${{ matrix.component }}/coverage.xml
          flags: ${{ matrix.component }}
          name: ${{ matrix.component }}-${{ matrix.python-version }}
```

### 2. Docker Build Workflow

#### .github/workflows/docker-build.yml
```yaml
name: Docker Build and Push

on:
  push:
    branches: [ main ]
    tags: [ 'v*' ]
  pull_request:
    branches: [ main ]

env:
  REGISTRY: docker.io
  IMAGE_PREFIX: modax

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    strategy:
      matrix:
        component:
          - name: control-layer
            context: ./python-control-layer
            dockerfile: ./python-control-layer/Dockerfile
          - name: ai-layer
            context: ./python-ai-layer
            dockerfile: ./python-ai-layer/Dockerfile
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      
      - name: Log in to Docker Hub
        if: github.event_name != 'pull_request'
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}
      
      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_PREFIX }}/${{ matrix.component.name }}
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=sha,prefix={{branch}}-
      
      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: ${{ matrix.component.context }}
          file: ${{ matrix.component.dockerfile }}
          push: ${{ github.event_name != 'pull_request' }}
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
      
      - name: Scan image with Trivy
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: ${{ env.REGISTRY }}/${{ env.IMAGE_PREFIX }}/${{ matrix.component.name }}:${{ steps.meta.outputs.version }}
          format: 'sarif'
          output: 'trivy-results.sarif'
      
      - name: Upload Trivy results to GitHub Security
        uses: github/codeql-action/upload-sarif@v2
        if: always()
        with:
          sarif_file: 'trivy-results.sarif'
```

### 3. Integration Tests Workflow

#### .github/workflows/integration-tests.yml
```yaml
name: Integration Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  integration-tests:
    runs-on: ubuntu-latest
    
    services:
      mosquitto:
        image: eclipse-mosquitto:2.0
        ports:
          - 1883:1883
        options: >-
          --health-cmd "mosquitto_sub -t '$$SYS/#' -C 1 -i healthcheck -W 3"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r python-control-layer/requirements.txt
          pip install -r python-ai-layer/requirements.txt
          pip install pytest pytest-asyncio
      
      - name: Run integration tests
        env:
          MQTT_BROKER_HOST: localhost
          MQTT_BROKER_PORT: 1883
        run: |
          pytest tests/integration/ -v --tb=short
      
      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: integration-test-results
          path: test-results/
```

### 4. Security Scan Workflow

#### .github/workflows/security-scan.yml
```yaml
name: Security Scan

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]
  schedule:
    # Run weekly on Monday at 00:00 UTC
    - cron: '0 0 * * 1'

jobs:
  dependency-scan:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        component: ['python-control-layer', 'python-ai-layer']
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install Safety
        run: pip install safety
      
      - name: Run Safety check
        run: |
          cd ${{ matrix.component }}
          safety check -r requirements.txt --json > safety-report.json || true
      
      - name: Upload Safety report
        uses: actions/upload-artifact@v3
        with:
          name: safety-${{ matrix.component }}
          path: ${{ matrix.component }}/safety-report.json
  
  code-security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Run Bandit security scan
        run: |
          pip install bandit
          bandit -r python-control-layer/ python-ai-layer/ -f json -o bandit-report.json
      
      - name: Upload Bandit results
        uses: actions/upload-artifact@v3
        with:
          name: bandit-report
          path: bandit-report.json
  
  container-scan:
    runs-on: ubuntu-latest
    if: github.event_name == 'push'
    steps:
      - uses: actions/checkout@v4
      
      - name: Build test images
        run: |
          docker build -t modax/control-layer:test ./python-control-layer
          docker build -t modax/ai-layer:test ./python-ai-layer
      
      - name: Scan with Trivy
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'image'
          image-ref: 'modax/control-layer:test'
          format: 'sarif'
          output: 'trivy-control.sarif'
      
      - name: Upload Trivy results
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'trivy-control.sarif'
```

### 5. Release Workflow

#### .github/workflows/release.yml
```yaml
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  create-release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      
      - name: Generate changelog
        id: changelog
        uses: metcalfc/changelog-generator@v4.1.0
        with:
          myToken: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Create Release
        uses: actions/create-release@v1
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          tag_name: ${{ github.ref_name }}
          release_name: Release ${{ github.ref_name }}
          body: ${{ steps.changelog.outputs.changelog }}
          draft: false
          prerelease: false
  
  build-and-publish:
    needs: create-release
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Build Docker images
        run: |
          docker build -t modax/control-layer:${{ github.ref_name }} ./python-control-layer
          docker build -t modax/ai-layer:${{ github.ref_name }} ./python-ai-layer
      
      - name: Log in to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}
      
      - name: Push images
        run: |
          docker push modax/control-layer:${{ github.ref_name }}
          docker push modax/ai-layer:${{ github.ref_name }}
          
          # Also tag as latest for releases
          docker tag modax/control-layer:${{ github.ref_name }} modax/control-layer:latest
          docker tag modax/ai-layer:${{ github.ref_name }} modax/ai-layer:latest
          docker push modax/control-layer:latest
          docker push modax/ai-layer:latest
```

## Deployment Strategies

### 1. Development Environment
- **Trigger**: Push to `develop` branch
- **Target**: Development server
- **Strategy**: Direct deployment, no approval required
- **Rollback**: Automatic if health checks fail

### 2. Staging Environment
- **Trigger**: Push to `main` branch
- **Target**: Staging server
- **Strategy**: Blue-green deployment
- **Testing**: Automated smoke tests
- **Rollback**: Manual or automatic on test failure

### 3. Production Environment
- **Trigger**: Git tag (e.g., v1.0.0)
- **Target**: Production cluster
- **Strategy**: Rolling update with canary
- **Approval**: Required from team lead
- **Rollback**: Automated or manual

### Deployment Script Example

#### scripts/deploy.sh
```bash
#!/bin/bash
set -e

ENVIRONMENT=$1
VERSION=$2

if [ -z "$ENVIRONMENT" ] || [ -z "$VERSION" ]; then
    echo "Usage: ./deploy.sh [dev|staging|prod] [version]"
    exit 1
fi

echo "Deploying MODAX $VERSION to $ENVIRONMENT"

case $ENVIRONMENT in
  dev)
    docker-compose -f docker-compose.yml pull
    docker-compose -f docker-compose.yml up -d
    ;;
  staging)
    docker-compose -f docker-compose.staging.yml pull
    docker-compose -f docker-compose.staging.yml up -d --no-deps --build
    ;;
  prod)
    # Rolling update
    docker service update --image modax/control-layer:$VERSION modax_control
    docker service update --image modax/ai-layer:$VERSION modax_ai
    ;;
  *)
    echo "Unknown environment: $ENVIRONMENT"
    exit 1
    ;;
esac

echo "Deployment complete!"
```

## Quality Gates

### Pre-commit Checks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.11.0
    hooks:
      - id: black
        language_version: python3.11
  
  - repo: https://github.com/pycqa/flake8
    rev: 6.1.0
    hooks:
      - id: flake8
        args: ['--max-line-length=127']
  
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.0
    hooks:
      - id: mypy
        additional_dependencies: [types-requests]
```

### Branch Protection Rules
- **Main branch**:
  - Require pull request reviews (1 approval)
  - Require status checks to pass
  - Require branches to be up to date
  - No force pushes
  - No deletions

- **Develop branch**:
  - Require status checks to pass
  - No force pushes (except for rebase)

## Monitoring Pipeline Health

### Key Metrics
- Build success rate
- Average build time
- Deployment frequency
- Mean time to recovery (MTTR)
- Change failure rate

### Alerts
- Build failures on main branch
- Deployment failures
- Security vulnerabilities detected
- Test coverage drops below threshold

## Secrets Management

### Required Secrets
```yaml
DOCKER_USERNAME:       # Docker Hub username
DOCKER_PASSWORD:       # Docker Hub password/token
DB_PASSWORD:           # Database password
MQTT_PASSWORD:         # MQTT broker password
CODECOV_TOKEN:         # Code coverage token
SLACK_WEBHOOK:         # Slack notification webhook
```

### Configuration in GitHub
1. Navigate to repository Settings → Secrets and variables → Actions
2. Add each secret with appropriate name and value
3. Use in workflows: `${{ secrets.SECRET_NAME }}`

## Rollback Procedures

### Automatic Rollback
```yaml
- name: Health check after deployment
  run: |
    sleep 30
    curl -f http://control-layer:8000/status || exit 1

- name: Rollback on failure
  if: failure()
  run: |
    docker service update --rollback modax_control
```

### Manual Rollback
```bash
# Rollback to previous version
docker service update --rollback modax_control

# Or deploy specific version
./scripts/deploy.sh prod v1.0.0
```

## Best Practices

### DO:
✅ Run tests on every commit  
✅ Use semantic versioning for releases  
✅ Keep secrets out of code  
✅ Tag Docker images with git commit SHA  
✅ Monitor pipeline metrics  
✅ Document deployment procedures  
✅ Test rollback procedures regularly  

### DON'T:
❌ Skip tests to speed up pipeline  
❌ Deploy directly to production  
❌ Hardcode credentials in workflows  
❌ Ignore security scan results  
❌ Deploy without health checks  
❌ Leave failing builds unattended  

## Troubleshooting

### Build Failures
1. Check workflow logs in GitHub Actions
2. Reproduce locally: `act -j build-and-test`
3. Fix issues and push again

### Deployment Failures
1. Check health check status
2. Review application logs
3. Verify configuration
4. Rollback if necessary

### Security Scan Failures
1. Review vulnerability report
2. Update affected dependencies
3. If false positive, add exception
4. Rerun pipeline

## Implementation Roadmap

### Phase 1: Basic CI (Week 1)
- [ ] Set up Python linting and testing
- [ ] Configure code coverage
- [ ] Add pre-commit hooks

### Phase 2: Docker CI (Week 2)
- [ ] Add Docker build workflow
- [ ] Implement image scanning
- [ ] Set up image registry

### Phase 3: CD Pipeline (Week 3-4)
- [ ] Configure deployment environments
- [ ] Implement deployment scripts
- [ ] Set up health checks
- [ ] Test rollback procedures

### Phase 4: Advanced Features (Week 5-6)
- [ ] Add integration tests
- [ ] Implement canary deployments
- [ ] Set up monitoring and alerts
- [ ] Document all procedures

## References
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Build and Push Action](https://github.com/docker/build-push-action)
- [Trivy Security Scanner](https://github.com/aquasecurity/trivy)
- [Semantic Versioning](https://semver.org/)

---
**Last Updated:** 2025-12-07  
**Maintained By:** MODAX DevOps Team
