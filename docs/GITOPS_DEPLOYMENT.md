# GitOps Deployment with ArgoCD and Flux

This document describes GitOps deployment strategies for MODAX using ArgoCD or FluxCD for continuous deployment to Kubernetes clusters.

**Last Updated:** 2025-12-09  
**Version:** 0.3.0  
**Status:** Implementation Guide

## Overview

GitOps is a paradigm that uses Git as the single source of truth for declarative infrastructure and applications. Changes to the desired state are made via Git commits, and automated processes synchronize the actual state with the desired state.

### Benefits of GitOps for MODAX

- **Declarative Configuration:** All deployment configurations in Git
- **Version Control:** Complete audit trail of all changes
- **Automated Deployments:** Push to Git triggers deployment
- **Easy Rollbacks:** Revert Git commits to rollback
- **Improved Security:** No direct cluster access needed
- **Consistency:** Same deployment process for dev, staging, and production

## Architecture

```
┌─────────────────┐
│  Git Repository │
│   (GitHub)      │
└────────┬────────┘
         │
         │ Pull & Sync
         │
    ┌────▼──────┐
    │  ArgoCD/  │
    │   Flux    │
    └────┬──────┘
         │
         │ Apply
         │
    ┌────▼──────────────────┐
    │  Kubernetes Cluster   │
    │  ┌─────────────────┐  │
    │  │ MODAX Services  │  │
    │  │ - Control Layer │  │
    │  │ - AI Layer      │  │
    │  │ - MQTT Broker   │  │
    │  │ - TimescaleDB   │  │
    │  │ - Monitoring    │  │
    │  └─────────────────┘  │
    └───────────────────────┘
```

## Repository Structure

Recommended GitOps repository structure:

```
modax-gitops/
├── README.md
├── apps/
│   ├── base/                    # Base configurations
│   │   ├── control-layer/
│   │   ├── ai-layer/
│   │   ├── mqtt/
│   │   └── timescaledb/
│   └── overlays/                # Environment-specific
│       ├── dev/
│       ├── staging/
│       └── production/
├── infrastructure/              # Infrastructure components
│   ├── ingress-nginx/
│   ├── cert-manager/
│   └── prometheus/
└── argocd/                     # ArgoCD/Flux configurations
    ├── applications/
    └── projects/
```

---

## Option 1: ArgoCD

### Installation

#### 1. Install ArgoCD on Kubernetes

```bash
# Create namespace
kubectl create namespace argocd

# Install ArgoCD
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Wait for pods to be ready
kubectl wait --for=condition=Ready pods --all -n argocd --timeout=300s

# Get initial admin password
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d; echo

# Port forward to access UI
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

#### 2. Configure ArgoCD CLI

```bash
# Install ArgoCD CLI
brew install argocd  # macOS
# or
curl -sSL -o argocd https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
chmod +x argocd
sudo mv argocd /usr/local/bin/

# Login
argocd login localhost:8080 --username admin --password <password>

# Change admin password
argocd account update-password
```

### Setup MODAX GitOps Repository

#### 1. Create Application Manifests

Create `argocd/applications/modax-production.yaml`:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: modax-production
  namespace: argocd
  finalizers:
    - resources-finalizer.argocd.argoproj.io
spec:
  project: modax
  
  source:
    repoURL: https://github.com/Thomas-Heisig/MODAX-gitops
    targetRevision: main
    path: apps/overlays/production
  
  destination:
    server: https://kubernetes.default.svc
    namespace: modax-production
  
  syncPolicy:
    automated:
      prune: true      # Delete resources not in Git
      selfHeal: true   # Automatically sync if drift detected
      allowEmpty: false
    syncOptions:
      - CreateNamespace=true
      - PruneLast=true
    
    retry:
      limit: 5
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 3m
  
  # Health checks
  ignoreDifferences:
    - group: apps
      kind: Deployment
      jsonPointers:
        - /spec/replicas  # Ignore HPA changes
```

Create `argocd/projects/modax.yaml`:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: AppProject
metadata:
  name: modax
  namespace: argocd
spec:
  description: MODAX Industrial Control System
  
  sourceRepos:
    - https://github.com/Thomas-Heisig/MODAX-gitops
    - https://github.com/Thomas-Heisig/MODAX
  
  destinations:
    - namespace: 'modax-*'
      server: https://kubernetes.default.svc
    - namespace: monitoring
      server: https://kubernetes.default.svc
  
  clusterResourceWhitelist:
    - group: ''
      kind: Namespace
    - group: rbac.authorization.k8s.io
      kind: ClusterRole
    - group: rbac.authorization.k8s.io
      kind: ClusterRoleBinding
  
  namespaceResourceWhitelist:
    - group: '*'
      kind: '*'
```

#### 2. Apply ArgoCD Configuration

```bash
# Create project
kubectl apply -f argocd/projects/modax.yaml

# Create applications
kubectl apply -f argocd/applications/modax-production.yaml
kubectl apply -f argocd/applications/modax-staging.yaml
```

#### 3. Verify Deployment

```bash
# Check application status
argocd app list

# Get detailed status
argocd app get modax-production

# Watch sync progress
argocd app sync modax-production --watch
```

### Application Structure with Kustomize

Create `apps/base/control-layer/kustomization.yaml`:

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: modax

resources:
  - deployment.yaml
  - service.yaml
  - configmap.yaml
  - secret.yaml

commonLabels:
  app: control-layer
  component: backend
  managed-by: argocd
```

Create `apps/overlays/production/control-layer/kustomization.yaml`:

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: modax-production

bases:
  - ../../../base/control-layer

patchesStrategicMerge:
  - replica-patch.yaml
  - resource-patch.yaml

images:
  - name: ghcr.io/thomas-heisig/modax-control-layer
    newTag: v0.3.0

configMapGenerator:
  - name: control-layer-config
    behavior: merge
    literals:
      - LOG_LEVEL=INFO
      - AI_LAYER_URL=http://ai-layer:8001
      - MQTT_BROKER_HOST=mqtt.modax-production.svc.cluster.local
```

Create `apps/overlays/production/control-layer/replica-patch.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: control-layer
spec:
  replicas: 3  # Production: 3 replicas
```

### Automated Image Updates

Configure ArgoCD to auto-update images:

Create `argocd/applications/modax-image-updater.yaml`:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: argocd-image-updater
  namespace: argocd
  annotations:
    argocd-image-updater.argoproj.io/image-list: |
      control-layer=ghcr.io/thomas-heisig/modax-control-layer,
      ai-layer=ghcr.io/thomas-heisig/modax-ai-layer
    argocd-image-updater.argoproj.io/control-layer.update-strategy: semver
    argocd-image-updater.argoproj.io/control-layer.semver-constraint: "^0.3.0"
spec:
  # ... same as above
```

---

## Option 2: Flux CD

### Installation

#### 1. Install Flux CLI

```bash
# macOS
brew install fluxcd/tap/flux

# Linux
curl -s https://fluxcd.io/install.sh | sudo bash

# Verify installation
flux --version
```

#### 2. Bootstrap Flux

```bash
# Export GitHub token
export GITHUB_TOKEN=<your-token>

# Bootstrap Flux
flux bootstrap github \
  --owner=Thomas-Heisig \
  --repository=MODAX-gitops \
  --branch=main \
  --path=clusters/production \
  --personal
```

This creates:
- Flux components in the cluster
- Deploy keys in GitHub
- Repository structure in Git

### Setup MODAX with Flux

#### 1. Create Source Repository

Create `clusters/production/modax-source.yaml`:

```yaml
apiVersion: source.toolkit.fluxcd.io/v1beta2
kind: GitRepository
metadata:
  name: modax
  namespace: flux-system
spec:
  interval: 1m
  url: https://github.com/Thomas-Heisig/MODAX-gitops
  ref:
    branch: main
  secretRef:
    name: flux-system
```

#### 2. Create Kustomization

Create `clusters/production/modax-kustomization.yaml`:

```yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1beta2
kind: Kustomization
metadata:
  name: modax-production
  namespace: flux-system
spec:
  interval: 10m
  timeout: 5m
  retryInterval: 2m
  
  sourceRef:
    kind: GitRepository
    name: modax
  
  path: ./apps/overlays/production
  
  prune: true
  
  healthChecks:
    - apiVersion: apps/v1
      kind: Deployment
      name: control-layer
      namespace: modax-production
    - apiVersion: apps/v1
      kind: Deployment
      name: ai-layer
      namespace: modax-production
  
  postBuild:
    substitute:
      cluster_name: "production"
      domain: "modax.example.com"
```

#### 3. Apply Configuration

```bash
# Apply Flux configurations
kubectl apply -f clusters/production/

# Check Flux sources
flux get sources git

# Check Kustomizations
flux get kustomizations

# Watch reconciliation
flux logs --follow
```

### Automated Image Updates with Flux

#### 1. Install Image Automation Controllers

```bash
flux install \
  --components-extra=image-reflector-controller,image-automation-controller
```

#### 2. Configure Image Repository

Create `clusters/production/image-repository.yaml`:

```yaml
apiVersion: image.toolkit.fluxcd.io/v1beta1
kind: ImageRepository
metadata:
  name: control-layer
  namespace: flux-system
spec:
  image: ghcr.io/thomas-heisig/modax-control-layer
  interval: 1m
```

#### 3. Configure Image Policy

Create `clusters/production/image-policy.yaml`:

```yaml
apiVersion: image.toolkit.fluxcd.io/v1beta1
kind: ImagePolicy
metadata:
  name: control-layer
  namespace: flux-system
spec:
  imageRepositoryRef:
    name: control-layer
  policy:
    semver:
      range: 0.3.x
```

#### 4. Configure Image Update Automation

Create `clusters/production/image-update.yaml`:

```yaml
apiVersion: image.toolkit.fluxcd.io/v1beta1
kind: ImageUpdateAutomation
metadata:
  name: modax-production
  namespace: flux-system
spec:
  interval: 1m
  sourceRef:
    kind: GitRepository
    name: modax
  git:
    checkout:
      ref:
        branch: main
    commit:
      author:
        email: fluxbot@example.com
        name: Flux Bot
      messageTemplate: |
        Update MODAX images
        
        [ci skip]
    push:
      branch: main
  update:
    path: ./apps/overlays/production
    strategy: Setters
```

---

## CI/CD Pipeline Integration

### GitHub Actions with ArgoCD

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Kubernetes

on:
  push:
    branches:
      - main
    tags:
      - 'v*'

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Log in to Container Registry
        uses: docker/login-action@v2
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Build and push Docker image
        uses: docker/build-push-action@v4
        with:
          context: ./python-control-layer
          push: true
          tags: |
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}-control-layer:${{ github.sha }}
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}-control-layer:latest
  
  update-gitops:
    needs: build-and-push
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
        with:
          repository: Thomas-Heisig/MODAX-gitops
          token: ${{ secrets.GITOPS_TOKEN }}
      
      - name: Update image tag
        run: |
          cd apps/overlays/production/control-layer
          kustomize edit set image \
            ghcr.io/thomas-heisig/modax-control-layer=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}-control-layer:${{ github.sha }}
      
      - name: Commit and push
        run: |
          git config user.name "GitHub Actions"
          git config user.email "actions@github.com"
          git add .
          git commit -m "Update control-layer to ${{ github.sha }}"
          git push
```

---

## Progressive Delivery with Argo Rollouts

### Install Argo Rollouts

```bash
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml
```

### Configure Canary Deployment

Create `apps/base/control-layer/rollout.yaml`:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: control-layer
spec:
  replicas: 5
  
  strategy:
    canary:
      steps:
        - setWeight: 20   # 20% traffic to new version
        - pause: {duration: 5m}
        - setWeight: 40
        - pause: {duration: 5m}
        - setWeight: 60
        - pause: {duration: 5m}
        - setWeight: 80
        - pause: {duration: 5m}
      
      canaryService: control-layer-canary
      stableService: control-layer-stable
      
      trafficRouting:
        nginx:
          stableIngress: control-layer-ingress
      
      analysis:
        templates:
          - templateName: success-rate
        startingStep: 2
        args:
          - name: service-name
            value: control-layer
  
  selector:
    matchLabels:
      app: control-layer
  
  template:
    metadata:
      labels:
        app: control-layer
    spec:
      containers:
        - name: control-layer
          image: ghcr.io/thomas-heisig/modax-control-layer:latest
          ports:
            - containerPort: 8000
```

### Analysis Template

Create `apps/base/control-layer/analysis-template.yaml`:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: success-rate
spec:
  args:
    - name: service-name
  
  metrics:
    - name: success-rate
      interval: 1m
      successCondition: result >= 0.95
      failureLimit: 3
      provider:
        prometheus:
          address: http://prometheus:9090
          query: |
            sum(rate(
              http_requests_total{
                service="{{args.service-name}}",
                status!~"5.."
              }[5m]
            )) /
            sum(rate(
              http_requests_total{
                service="{{args.service-name}}"
              }[5m]
            ))
```

---

## Monitoring and Observability

### ArgoCD Notifications

Configure Slack notifications:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: argocd-notifications-cm
  namespace: argocd
data:
  service.slack: |
    token: $slack-token
  
  template.app-deployed: |
    message: |
      Application {{.app.metadata.name}} is now running version {{.app.status.sync.revision}}.
  
  trigger.on-deployed: |
    - when: app.status.operationState.phase in ['Succeeded']
      send: [app-deployed]
  
  subscriptions: |
    - recipients:
      - slack:deployments-channel
      triggers:
      - on-deployed
```

### Flux Alerts

Create `clusters/production/alert-provider.yaml`:

```yaml
apiVersion: notification.toolkit.fluxcd.io/v1beta1
kind: Provider
metadata:
  name: slack
  namespace: flux-system
spec:
  type: slack
  channel: deployments
  secretRef:
    name: slack-webhook
```

Create `clusters/production/alert.yaml`:

```yaml
apiVersion: notification.toolkit.fluxcd.io/v1beta1
kind: Alert
metadata:
  name: modax-production
  namespace: flux-system
spec:
  providerRef:
    name: slack
  
  eventSeverity: info
  
  eventSources:
    - kind: Kustomization
      name: modax-production
    - kind: GitRepository
      name: modax
```

---

## Security Best Practices

### 1. Sealed Secrets

```bash
# Install Sealed Secrets controller
kubectl apply -f https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.18.0/controller.yaml

# Seal a secret
kubeseal --format=yaml < secret.yaml > sealed-secret.yaml

# Commit sealed secret to Git
git add sealed-secret.yaml
```

### 2. Private Repository Access

For ArgoCD:
```bash
argocd repo add https://github.com/Thomas-Heisig/MODAX-gitops \
  --username <username> \
  --password <token>
```

For Flux:
```bash
flux create secret git modax-auth \
  --url=https://github.com/Thomas-Heisig/MODAX-gitops \
  --username=<username> \
  --password=<token>
```

### 3. RBAC Configuration

Limit ArgoCD permissions:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: argocd-rbac-cm
  namespace: argocd
data:
  policy.csv: |
    p, role:modax-deployer, applications, sync, modax/*, allow
    p, role:modax-deployer, applications, get, modax/*, allow
    g, developers, role:modax-deployer
```

---

## Disaster Recovery

### Backup ArgoCD State

```bash
# Backup ArgoCD applications
kubectl get applications -n argocd -o yaml > argocd-apps-backup.yaml

# Backup ArgoCD settings
kubectl get configmap argocd-cm -n argocd -o yaml > argocd-cm-backup.yaml
```

### Restore from Git

Since GitOps uses Git as source of truth:

```bash
# Simply re-apply configurations
kubectl apply -f argocd/applications/
kubectl apply -f argocd/projects/

# ArgoCD will sync from Git
argocd app sync --all
```

---

## Migration Path

### From Manual Deployments to GitOps

1. **Phase 1: Preparation**
   - Document current deployment process
   - Create GitOps repository
   - Define environments (dev, staging, prod)

2. **Phase 2: Dev Environment**
   - Setup ArgoCD/Flux on dev cluster
   - Migrate dev deployments
   - Test and refine

3. **Phase 3: Staging**
   - Setup on staging cluster
   - Migrate staging deployments
   - Validate complete workflow

4. **Phase 4: Production**
   - Setup on production cluster
   - Gradual migration (service by service)
   - Monitor and validate

---

## Related Documentation

- [CI/CD Pipeline](CI_CD.md)
- [Containerization](CONTAINERIZATION.md)
- [High Availability](HIGH_AVAILABILITY.md)
- [Kubernetes Manifests](../k8s/)
- [Helm Charts](../helm/modax/)

## Resources

- [ArgoCD Documentation](https://argo-cd.readthedocs.io/)
- [Flux Documentation](https://fluxcd.io/docs/)
- [GitOps Principles](https://www.gitops.tech/)
- [Argo Rollouts](https://argoproj.github.io/argo-rollouts/)
