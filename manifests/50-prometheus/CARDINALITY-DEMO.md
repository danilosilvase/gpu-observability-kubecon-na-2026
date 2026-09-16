# The "what broke" slide — reproduce the cardinality explosion on purpose

## 1. Baseline: measure series count
```promql
count({__name__=~"DCGM_.*"})
```
Note the number with the cardinality-safe config (ENABLE_POD_LABELS=false).

## 2. Break it
Edit `10-gpu-metrics/dcgm-exporter-daemonset.yaml`:
```yaml
- name: DCGM_EXPORTER_KUBERNETES_ENABLE_POD_LABELS
  value: "true"          # <-- now every arbitrary pod label becomes a metric label
```
Roll the DaemonSet, generate pod churn (scale vLLM up/down a few times):
```bash
kubectl -n inference scale deploy/vllm-opt125m --replicas=4
kubectl -n inference scale deploy/vllm-opt125m --replicas=2
```
Re-run the count PromQL. Each GPU series now multiplies by the set of pod
labels x pod generations. Screenshot the jump — that's the slide.

## 3. Fix
Two levers:
- `ENABLE_POD_LABELS=false` (what we ship), OR
- allow-list only safe labels:
  `DCGM_EXPORTER_KUBERNETES_POD_LABEL_ALLOWLIST_REGEX="app|model"`
Keep base device telemetry intact; drop only the churny labels.

## 4. Talk point
Per-pod GPU attribution is valuable but the pod identity you join on
(pod_name/namespace from `--kubernetes=true`) is BOUNDED. Arbitrary pod
*labels* are UNBOUNDED — that's the trap.
