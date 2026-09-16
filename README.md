# Inference Is a Black Box: GPU-Aware Observability with Fluent Bit and OpenTelemetry

Demo and slides for the KubeCon North America 2026 Observability Day talk
(Mon 9 Nov 2026, Room 1).

The idea in one line: **the pod is the join key.** Stamp the same
`pod / namespace` on GPU metrics (dcgm-exporter), serving logs (Fluent Bit + Lua)
and traces (OpenTelemetry k8sattributes), and three disconnected signals become
one Grafana query.

## Layout

| Path | What |
|------|------|
| `deck/kubecon-na-2026.html` | The slides. Open in a browser, `F` fullscreen, `N` speaker notes, arrows to move. |
| `terraform/` | One-apply reproduction on EKS Auto Mode: VPC, cluster, GPU NodePool, kube-prometheus-stack, dcgm-exporter, two vLLM deployments, Fluent Bit, OTel Collector, Jaeger, Grafana dashboard. |
| `manifests/` | The same Kubernetes objects as plain YAML, for clusters you already have. |
| `DEMO-RUNBOOK.md` | Timing, commands and fallbacks for the live demo. |

## Quick start

```bash
cd terraform
export AWS_PROFILE=<an admin profile>   # or set var aws_profile
terraform init
terraform apply -target=module.eks -auto-approve
terraform apply -auto-approve
./validate.sh                            # expect 12 passed / 0 failed
```

Access:

```bash
aws eks update-kubeconfig --name gpu-obs-demo --region eu-central-1
kubectl -n observability port-forward svc/kube-prometheus-stack-grafana 3000:80   # admin / gpu-obs-demo
kubectl -n observability port-forward svc/jaeger-ui 16686:16686
```

Two g6.xlarge (NVIDIA L4) nodes cost roughly USD 2.4/hour. The GPU NodePool has
`expireAfter: 24h`. Tear down with `terraform destroy -auto-approve` when done.

## Notes

- On EKS Auto Mode do not install the NVIDIA GPU Operator; Auto Mode ships the
  driver and device plugin. dcgm-exporter runs standalone here.
- `DCGM_EXPORTER_KUBERNETES_ENABLE_POD_LABELS` is `false` on purpose. See
  `manifests/50-prometheus/CARDINALITY-DEMO.md` for why.
- The Grafana admin password is a demo default in `terraform/platform.tf`. Change it
  if the cluster is reachable by anyone but you.

This talk builds on an internal AWS GenAI observability session; credit to the
original authors.

MIT licensed.
