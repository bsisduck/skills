# Kubernetes

How to report a whole Kubernetes cluster to TracePath. Read this when "Deployment and Server Metrics" resolved the deployment to Kubernetes, or when the repo carries Kubernetes manifests, Helm charts, or Kustomize overlays for the deployed component.

The applications keep their normal OpenTelemetry instrumentation from "Backend OTel Setup". This adds the layer underneath them: node health, pod resource usage, container logs, cluster state and Kubernetes events.

Public docs: https://docs.tracepath.dev/learn/kubernetes

## What to deploy

Two OpenTelemetry Collector workloads, both using the **same project token as the application**:

| Workload | Reads | Becomes |
|---|---|---|
| `tracepath-node-agent` (DaemonSet) | hostmetrics of each node, kubelet node/pod metrics, `/var/log/pods` | One instance row per node in the organization overview, `k8s.pod.*` metrics, container logs |
| `tracepath-cluster-agent` (Deployment, 1 replica) | `k8s_cluster` state, Kubernetes events | Cluster metrics, events on the Logs page |

Ready-made manifests: https://github.com/bsisduck/tracepath/tree/main/examples/kubernetes

```bash
kubectl create namespace tracepath
kubectl create secret generic tracepath-token -n tracepath \
  --from-literal=token='<project-token>'
curl -O https://raw.githubusercontent.com/bsisduck/tracepath/main/examples/kubernetes/tracepath-kubernetes.yaml
# edit TRACEPATH_CLUSTER_NAME and TRACEPATH_ENDPOINT in the tracepath-settings ConfigMap
kubectl apply -f tracepath-kubernetes.yaml
```

Do not commit the token. If the repo has a manifests directory, add the collector YAML there with the token referenced from an existing Secret or from the project's sealed-secret / external-secret mechanism, and match the repo's conventions (Kustomize base+overlay, Helm chart, plain manifests). If the repo has no manifests, hand the operator the commands; do not create a manifests directory for them.

## The four rules that decide whether it works

**1. `service.name` on the node agent must be the node name.**

`server_name` in TracePath comes from the `service.name` resource attribute, and `server_name` is the identity of an instance. Set it from the downward API:

```yaml
env:
  - name: K8S_NODE_NAME
    valueFrom:
      fieldRef:
        fieldPath: spec.nodeName
```

```yaml
processors:
  resource/node:
    attributes:
      - key: service.name
        value: ${env:K8S_NODE_NAME}
        action: upsert
```

Without it every node reports under the collector's own service name and the whole cluster collapses into one instance row.

**2. The three `*.utilization` metrics must be enabled explicitly.**

`system.cpu.utilization`, `system.memory.utilization` and `system.filesystem.utilization` ship **disabled** in the hostmetrics receiver, and the OpenTelemetry Helm chart's `hostMetrics` preset does not turn them on. They are exactly what the organization overview reads for the CPU, memory and disk rings.

```yaml
receivers:
  hostmetrics:
    root_path: /hostfs
    scrapers:
      cpu:
        metrics:
          system.cpu.utilization: { enabled: true }
      memory:
        metrics:
          system.memory.utilization: { enabled: true }
      filesystem:
        metrics:
          system.filesystem.utilization: { enabled: true }
```

**3. `k8s.cluster.name` must be set, and distinct per cluster.**

It is on the metric resource-attribute allowlist and is what the organization overview groups instances by. Nothing sets it automatically; add it with a `resource` processor from an env var.

**4. hostmetrics in a container needs `root_path: /hostfs` and the host root mounted there**, read-only, with the pod running as uid 0. Otherwise the numbers describe the collector's container, not the node.

## What survives per signal

TracePath does not store arbitrary resource attributes. Per signal:

- **Metrics**: an allowlist, which includes `k8s.cluster.name`, `k8s.pod.name`, `k8s.namespace.name`, `k8s.node.name`, `k8s.deployment.name`, `k8s.container.name`, `container.name`, `container.image.name`, plus `host.*`, `os.*` and `cloud.*`. Full list in `data-model.md`.
- **Logs**: the entire resource attribute map is stored, so every Kubernetes attribute is filterable.
- **Traces**: only `service.name` and `service.version`. Pod and namespace do **not** reach spans. If a trace must carry which pod served it, set it as a span attribute in the application.

Never promise a user they can group Endpoints or Issues by pod. They cannot.

## Application telemetry: direct or through a gateway

Both are correct; pick by whether the token should exist in every namespace.

**Direct** (default, fewer moving parts): each Deployment sets `OTEL_EXPORTER_OTLP_ENDPOINT=https://<instance>/api/otel` and `OTEL_EXPORTER_OTLP_HEADERS=Authorization=Bearer <token>` from a Secret, exactly as in "Backend OTel Setup".

**Gateway**: deploy `tracepath-gateway.yaml`, then applications export to `http://tracepath-gateway.tracepath.svc.cluster.local:4318` with no credentials. The token exists once, and the gateway adds `k8s.pod.name`, `k8s.namespace.name` and `k8s.deployment.name` to application metrics and logs. Propose this when the repo already has many services or when the user raised secret sprawl.

Either way the application keeps its own `OTEL_SERVICE_NAME`. Pods are not instances; nodes are.

## Cardinality

Pod names change on every rollout, and each distinct tag value is a stored series. Default `kubeletstats` to `metric_groups: [node, pod]`; add `container` only when asked. When building dashboards, group by `k8s.deployment.name` for anything meant to be stable over time and reserve `k8s.pod.name` for debugging.

## Verify

1. `kubectl -n tracepath rollout status daemonset/tracepath-node-agent`
2. Organization overview: one instance row per node, grouped under the cluster name, with CPU/memory/disk rings filled in.
3. Logs page: container output arriving, filterable by `k8s.namespace.name`.
4. Dashboards: install the **OTelemetry Server Agent** template (Cmd K); it already matches the node agent's metric names.

Common failures, in the order they actually happen: `*.utilization` not enabled (rings empty), `service.name` not per node (one row instead of N), `k8s.cluster.name` missing (no cluster grouping option), token is not the project token (401 in the collector logs).

## Not this

- The TracePath OTel Agent installer (`install.tracepath.dev/install.sh`) is a host service, systemd/launchd/Windows. It is not for Kubernetes. Do not suggest running it in a container or as a DaemonSet.
- The `helm/tracepath` chart in the TracePath repo deploys **TracePath itself** into a cluster. It has nothing to do with monitoring one. Only bring it up if the user is self-hosting TracePath on Kubernetes.
