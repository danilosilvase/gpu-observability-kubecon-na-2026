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
| `demo/` | Stage scripts: `start.sh`, `check.sh`, `load.sh`, `trace.sh`, `cardinality.sh`, `stop.sh` |
| `manifests/` | The deployable configs, one file per component. Single source: Terraform applies these same files. |
| `terraform/` | One-apply rig on EKS Auto Mode: VPC, cluster, GPU NodePool, kube-prometheus-stack, then `manifests/`. |
| `DEMO-RUNBOOK.md` | One page: commands, five beats, measured numbers, fallbacks. |
| `deck/` | Slides (`kubecon-na-2026-v4.pptx`) and their build scripts. |

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
./validate.sh                            # expect 14 passed / 0 failed
../demo/start.sh                         # tunnels + load + dashboard
```

Access:

```bash
aws eks update-kubeconfig --name gpu-obs-demo --region eu-central-1
demo/start.sh    # Grafana on http://localhost:3000 (admin / gpu-obs-demo), Jaeger on :16686
demo/check.sh    # 7 OK, 0 FAIL
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
  `log_to_metrics` path (panel 2) demonstrates the technique for servers that do not; the collapsed
  "Details" row cross-checks it against the native numbers.
- Traces have two hops: the loadgen sends a client span and a `traceparent` header, vLLM continues it.
  In Grafana, the chain icon on any span opens that pod's GPU memory and KV cache (`tracesToMetrics`).
- Dashboard JSON is generated: edit `manifests/60-grafana/build_dashboard.py`, then
  `python3 manifests/60-grafana/build_dashboard.py manifests/60-grafana/gpu-inference-dashboard.json`.

This talk builds on an internal AWS GenAI observability session; credit to the
original authors.

MIT licensed.
