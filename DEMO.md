# Demo walkthrough: four screens, about ten minutes

Four Grafana dashboards, `gpu-walk-1` to `gpu-walk-4`, ask one question each. Every screen has the same layout: the question at the top, the config that makes it work on the left (one line highlighted), one chart on the right, and one sentence at the bottom. The orange **Next** button at the top right moves to the next screen.

- **Red** = `vllm-constrained`, `--gpu-memory-utilization=0.08`
- **Blue** = `vllm-overprov`, `--gpu-memory-utilization=0.90`

Same model (`facebook/opt-125m`), same GPU type (one NVIDIA A10G or L4 per pod), same traffic.

## Before you start

1. Deploy the lab ([README](README.md#deploy)).
2. `demo/start.sh` opens screen 4 and screen 1 in two browser tabs (kiosk mode).
3. `demo/check.sh` should print `9 OK, 0 FAIL`. On a cluster that has never had traffic, the log and trace checks fail until the first load: run `demo/load.sh` once, check again, then `demo/stop.sh`.
4. For the clearest result, start screen 1 with no traffic: wait 10 minutes after the last load stops (the charts show the last 10 minutes).

## Screen 1: What does the GPU say?

- **Config:** dcgm-exporter runs with `--kubernetes=true`. It asks the kubelet which pod owns each GPU, so every GPU metric carries the pod name.
- **Chart:** GPU memory per pod. With no traffic, red holds about 2 GB (8% of the GPU) and blue about 20 GB (90%).
- **Do:** run `demo/load.sh`. Both pods now get 192 long requests in flight, all the time. The requests-in-flight tile shows the same number on both.
- **Look for:** the GPU memory lines do not move under load. vLLM pre-allocates its memory, so this chart cannot say which pod is in trouble.

## Screen 2: What does the server say?

- **Config:** the log line vLLM already writes every 10 seconds, and the Lua match in Fluent Bit that turns it into a metric with the pod name (`manifests/30-logs/fluent-bit.yaml`).
- **Chart:** KV cache usage per pod. The KV cache is the server's working memory for requests in flight.
- **Look for:** red climbs to 100% within about 90 seconds of the load starting; blue stays near a third. The cross-check tile shows the same value from vLLM's native `/metrics`, and tokens per second is lower on red.

## Screen 3: Why was this request slow?

- **Config:** the OpenTelemetry Collector's `k8sattributes` processor adds `k8s.pod.name` to every span. The application never knows its pod name.
- **Chart:** where each request's time goes, waiting versus on the GPU. Red waits several seconds for room; blue barely waits.
- **Do:**
  1. Click the top Trace ID in the red table. Each trace has two hops: the client, then vLLM.
  2. Open the `llm_request` span, then **Span Attributes**: vLLM's own timing shows the time spent queued.
  3. Open **Resource Attributes**: `k8s.pod.name` is on the request.
  4. Click the link icon on `llm_request`, then **This pod: how full it was**. One click takes you from the request to that pod's KV cache.
  5. Go back to screen 3 and repeat with the top trace for blue: a few milliseconds in the queue.
- The trace view opens in Explore, which has no Next button. Switch to the screen 4 tab that `demo/start.sh` opened.
- If the table is slow, `demo/trace.sh` opens the slowest recent red request directly.

## Screen 4: Which one was set wrong?

- **Rule of thumb (ours, not vLLM's):** look at the peak KV cache under real traffic. Above 90% the pod is memory-constrained; below 40% it is over-provisioned.
- **Look for:** the verdict tiles say red is memory-constrained and blue is over-provisioned. Both settings are wrong, in opposite directions. GPU memory never showed it; time to first token did (about 6 seconds against under a tenth of a second).
- At idle both verdicts read over-provisioned, which is correct: with no traffic there is no pressure.

## Go further

- **Cardinality:** restart the vLLM pods a few times (`kubectl -n inference rollout restart deploy/vllm-constrained deploy/vllm-overprov`), then run `demo/cardinality.sh`. Same two GPUs, several times the series. See [CARDINALITY-DEMO.md](manifests/50-prometheus/CARDINALITY-DEMO.md).
- **Change the setting:** edit `--gpu-memory-utilization` in `manifests/20-vllm/vllm.yaml`, `kubectl apply -f` it, rerun `demo/load.sh` and watch the verdict on screen 4. The next `terraform apply` puts the original value back.
