# ARC Manifests (Reference)

These manifests document the separation of controller and runner namespaces recommended by GitHub's ARC hardening guide (July 2025). They pin the controller and runner images, delegate GitHub App authentication via Kubernetes secrets, and keep runner workloads away from the controller control plane.

## Layout

- `controller-namespace.yaml` – dedicated namespace for the ARC controller.
- `runner-namespace.yaml` – isolated namespace for ephemeral runner pods.
- `values-controller.yaml` – Helm values overriding the official chart with a pinned controller image (`ghcr.io/actions/actions-runner-controller/actions-runner-controller:v0.28.1`) and GitHub App credentials sourced from `arc-github-app` secret.
- `values-runners.yaml` – Helm values for the runner scale set. Runners execute in `arc-runners` namespace, use a pinned runner image (`ghcr.io/actions/actions-runner:3.12.0`), and pull GitHub App credentials from the same secret. Tolerations and node selectors keep runners away from production nodes.

## Usage

1. Create the namespaces:
   ```bash
   kubectl apply -f controller-namespace.yaml
   kubectl apply -f runner-namespace.yaml
   ```
2. Provision the GitHub App secret in both namespaces (base64 encode the private key and webhook secret). The manifests intentionally reference the same secret name to avoid duplicating credentials in Git.
   ```bash
   kubectl -n arc-controller create secret generic arc-github-app \
     --from-file=privateKey=private-key.pem \
     --from-literal=webhookSecret=replace-me
   kubectl -n arc-runners create secret generic arc-github-app \
     --from-file=privateKey=private-key.pem \
     --from-literal=webhookSecret=replace-me
   ```
3. Install/upgrade the controller Helm release:
   ```bash
   helm upgrade --install arc-controller actions-runner-controller/actions-runner-controller \
     --namespace arc-controller \
     -f values-controller.yaml
   ```
4. Install the runner scale set:
   ```bash
   helm upgrade --install hotpass-arc actions-runner-controller/actions-runner-set \
     --namespace arc-runners \
     -f values-runners.yaml
   ```

Update the `githubConfigUrl`, GitHub App IDs, and tolerations for your cluster. Secrets are intentionally omitted; the values files only reference existing secret names.
