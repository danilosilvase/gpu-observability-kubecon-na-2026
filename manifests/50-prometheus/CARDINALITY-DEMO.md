# What broke: cardinality from per-pod GPU metrics

**TL;DR:** pod name on a GPU metric = one new set of series per pod restart. Keep the pod name (it is the join key), drop everything else that churns.

## Measured in this lab (2 A10G GPUs, 7 counters)

| | GPU series |
|--|--|
| Right now | **14** (7 counters x 2 GPUs) |
| Last hour, after 3 rollouts | **56** (8 pod names seen) |

Same two GPUs, 4x the series. Prometheus keeps every old series until retention ends.
Reproduce: `kubectl -n inference rollout restart deploy/vllm-constrained deploy/vllm-overprov` a few times, then `demo/cardinality.sh`.

## Why it explodes at scale

series = counters x GPUs x pod names seen (in retention) x extra label values.
Pod labels (`DCGM_EXPORTER_KUBERNETES_ENABLE_POD_LABELS=true`) add every label on the pod.
One churny label (a version, a run ID, a commit hash) multiplies the whole thing again.

## The fix we ship

| Lever | Setting |
|--|--|
| Keep the join key only | `--kubernetes=true` (adds pod, namespace, container) |
| No arbitrary pod labels | `DCGM_EXPORTER_KUBERNETES_ENABLE_POD_LABELS=false` |
| Need a few labels? Allow-list them | `DCGM_EXPORTER_KUBERNETES_POD_LABEL_ALLOWLIST_REGEX="app,model"` (needs pod labels on, plus RBAC to read pods) |
| Few counters | 7 in `counters.csv`, not the default ~40 |
| Short retention for per-pod data | `retention: 6h` in this lab |
