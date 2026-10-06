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
| `deck/kubecon-na-2026-v3.pptx` | The slides (v3, Oct 2026) on the CNCF branded template, with speaker notes. Built by `deck/pptx/build_deck.py`. |
| `deck/kubecon-na-2026.html` | v2 HTML deck, superseded, kept for reference. |
| `STORYLINE-v3.md` | Why v3: the serving log as telemetry, not the plumbing. Slide map and rig changes. |
| `terraform/` | One-apply reproduction on EKS Auto Mode: VPC, cluster, GPU NodePool, kube-prometheus-stack, dcgm-exporter, two vLLM deployments, Fluent Bit, OTel Collector, Jaeger, Grafana dashboard. |
| `manifests/` | The same Kubernetes objects as plain YAML, for clusters you already have. |
| `DEMO-RUNBOOK.md` | Timing, commands and fallbacks for the live demo. |

## Quick start

```bash
cd terraform
export AWS_PROFILE=<an admin profile>
# terraform.tfvars (gitignored): the providers read var.aws_profile, not the env var; without it
# terraform looks at the "default" profile and plans a full recreate. admin_cidrs = EKS API allow-list.
printf 'aws_profile = "%s"\nadmin_cidrs = ["%s/32"]\n' "$AWS_PROFILE" "$(curl -s https://checkip.amazonaws.com)" > terraform.tfvars
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

Two g5/g6 xlarge nodes (NVIDIA A10G or L4, one GPU each) cost roughly USD 2.4/hour. The GPU NodePool has
`expireAfter: 24h`. Tear down with `terraform destroy -auto-approve` when done.

## Notes

- On EKS Auto Mode do not install the NVIDIA GPU Operator; Auto Mode ships the
  driver and device plugin. dcgm-exporter runs standalone here.
- `DCGM_EXPORTER_KUBERNETES_ENABLE_POD_LABELS` is `false` on purpose. See
  `manifests/50-prometheus/CARDINALITY-DEMO.md` for why.
- Nothing is exposed outside the cluster: all Services are ClusterIP, no Ingress, no load
  balancer. Grafana and Jaeger are reached by `kubectl port-forward`. The only public surface is
  the EKS API endpoint, allow-listed to `var.admin_cidrs`.
- The Grafana admin password is a demo default in `terraform/platform.tf`. Change it
  if the cluster is reachable by anyone but you.
- Versions: vLLM v0.30.0 (OTel tracing needs >= 0.10.2), Fluent Bit 5.1.3, dcgm-exporter 4.8.4.
- vLLM exposes KV cache %, waiting and queue time natively on `/metrics`. The Fluent Bit Lua +
  `log_to_metrics` path (row 2 of the dashboard) demonstrates the technique for servers that do not;
  row 3 cross-checks it against the native numbers.

This talk builds on an internal AWS GenAI observability session; credit to the
original authors.

MIT licensed.
