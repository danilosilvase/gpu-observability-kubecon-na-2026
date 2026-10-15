# Accepted abstract (Sessionize, confirmed 18 Aug 2026)

**Inference Is a Black Box: How We Built GPU-Aware Observability with Fluent Bit and OpenTelemetry**
Observability Day, KubeCon + CloudNativeCon NA 2026. Mon 9 Nov 2026, 11:50-12:15 MST, Salt Palace Level 2, 250 A-C. Breakout, Intermediate. Speakers: Danilo Souza, Henrique Santana (session owner).

GPU inference on Kubernetes generates three disconnected signal types: hardware metrics from DCGM, structured serving logs, and distributed traces. Teams discover GPU memory pressure from pages, not dashboards, because nothing ties these signals together at the pod level.

This talk presents the observability pipeline we built to close that gap. We use dcgm-exporter in Kubernetes mode to map GPU devices to pods, Fluent Bit to collect and enrich inference logs with pod metadata, and the OTel Collector to assemble traces across instrumented model-serving hops. A Grafana dashboard joins all three by pod identity, surfacing which models are over-provisioned and which are memory-constrained.

We cover what broke (Prometheus cardinality explosion from per-pod GPU metrics), the Fluent Bit Lua parsing that extracts token throughput from serving logs, and the OTel Collector config that makes trace-to-GPU correlation queryable. You leave with deployable configs for all three components.

Feedback: show the CNCF QR code on the last slide or during Q&A.
