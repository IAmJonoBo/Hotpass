---
title: Deploy GitHub ARC runners for Hotpass pipelines
summary: Provision and operate ephemeral GitHub Actions runners on Kubernetes using OIDC and the Actions Runner Controller.
last_updated: 2025-10-29
---

This guide walks platform engineers through deploying the GitHub Actions Runner Controller (ARC) manifests shipped with Hotpass,
configuring OpenID Connect (OIDC) trust with AWS, and validating that ephemeral runners recycle correctly after each workflow.

## Prerequisites

- A Kubernetes cluster with the ARC controller installed (v0.9.0 or later).
- Access to apply manifests in the `arc-runners` namespace.
- `kubectl`, `terraform`, and the GitHub CLI installed locally.
- A GitHub App registered for the organisation or repository that hosts Hotpass workflows.

## 1. Configure GitHub OIDC trust in AWS

The Terraform module under [`infra/arc/terraform`](../../infra/arc/terraform) provisions an IAM role that workflows assume by using
GitHub's OIDC provider. The defaults cover the `main` branch and the `arc-runners` environment while allowing extra subjects if
you need staging cutovers.

```bash
cd infra/arc/terraform
terraform init
terraform apply \
  -var "aws_region=eu-west-1" \
  -var "github_repository=IAmJonoBo/Hotpass" \
  -var 'oidc_subjects=["repo:IAmJonoBo/Hotpass:environment:staging"]'
```

Record the `arc_runner_role_arn` output—workflows use it when assuming AWS credentials. If you store workflow artifacts in a
bucket other than GitHub's default, set `s3_artifact_bucket` to tighten S3 permissions around that location.

## 2. Render Kubernetes manifests

Apply the manifests in [`infra/arc`](../../infra/arc/) to your cluster after supplying real GitHub App credentials (for example via
SOPS or External Secrets). The Kustomize overlay creates the `arc-runners` namespace, configures GitHub metadata, and deploys a
runner scale set tuned for Hotpass workloads.

```bash
kustomize build infra/arc | kubectl apply -f -
```

### Secrets

Replace the placeholder values inside `arc-github-app-secret` with references to your sealed secret or secret manager bindings.
The ARC controller reads the private key and webhook secret to register the scale set with GitHub.

### Scaling parameters

The shipped `RunnerScaleSet` starts at zero runners and allows up to twenty concurrent pods (each requesting 2 vCPUs and 8 GiB of
memory). Tune `minRunners`, `maxRunners`, and container resources if your workloads have different footprints. The companion
`HorizontalRunnerAutoscaler` reacts to queued workflow jobs and scales down after two minutes of idleness.

## 3. Update workflows to assume the runner role

Add OIDC permissions and configure AWS credentials in workflows that should run on the new scale set. The example workflow
[`arc-ephemeral-runner.yml`](../../.github/workflows/arc-ephemeral-runner.yml) demonstrates the pattern:

```yaml
permissions:
  id-token: write
  contents: read

jobs:
  smoke:
    runs-on:
      - self-hosted
      - hotpass-arc
    steps:
      - uses: actions/checkout@v4
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/hotpass-arc-runner
          aws-region: eu-west-1
      - run: uv run python scripts/arc/verify_runner_lifecycle.py --owner IAmJonoBo --repository Hotpass --scale-set hotpass-arc
```

## 4. Validate runner lifecycle

Run the integration script [`scripts/arc/verify_runner_lifecycle.py`](../../scripts/arc/verify_runner_lifecycle.py) to ensure the
scale set drains after a workflow completes. The script polls the GitHub API and the Kubernetes cluster until the runner pods are
removed.

```bash
uv run python scripts/arc/verify_runner_lifecycle.py \
  --owner IAmJonoBo \
  --repository Hotpass \
  --scale-set hotpass-arc \
  --namespace arc-runners
```

Use `--output json` if you need machine-readable status checks inside CI or monitoring pipelines.

### Offline rehearsal with snapshots

When clusters are unavailable, supply a snapshot file that mimics pod and runner
states:

```bash
uv run python scripts/arc/verify_runner_lifecycle.py \
  --owner IAmJonoBo \
  --repository Hotpass \
  --scale-set hotpass-arc \
  --snapshot scripts/arc/examples/hotpass_arc_idle.json
```

Snapshots let QA and Platform teams verify workflow wiring during dry runs
without requiring Kubernetes or GitHub API access. Update the JSON to match the
expected lifecycle for more advanced rehearsal scenarios.

## 5. Tear down the runners

When you no longer need the runners, delete the Kubernetes resources and remove the IAM role.

```bash
kustomize build infra/arc | kubectl delete -f -
terraform destroy -var "aws_region=eu-west-1" -var "github_repository=IAmJonoBo/Hotpass"
```

This returns the cluster to its pre-runner state and ensures GitHub can no longer assume the AWS role.
