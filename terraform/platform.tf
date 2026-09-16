############################################
# kube-prometheus-stack (Prometheus + Grafana + Operator/CRDs)
############################################
resource "helm_release" "kps" {
  name             = "kube-prometheus-stack"
  repository       = "https://prometheus-community.github.io/helm-charts"
  chart            = "kube-prometheus-stack"
  version          = "65.5.0"
  namespace        = "observability"
  create_namespace = true
  timeout          = 900
  wait             = true

  values = [yamlencode({
    prometheus = {
      prometheusSpec = {
        # discover ALL ServiceMonitors regardless of helm release label
        serviceMonitorSelectorNilUsesHelmValues = false
        podMonitorSelectorNilUsesHelmValues     = false
        retention                               = "6h"
      }
    }
    grafana = {
      adminPassword = "gpu-obs-demo"
      sidecar = {
        dashboards = {
          enabled         = true
          searchNamespace = "ALL"
          label           = "grafana_dashboard"
        }
      }
    }
    # Auto Mode note: kube-state-metrics/node-exporter schedule on managed nodes
    nodeExporter = { enabled = true }
  })]

  depends_on = [module.eks]
}

# Grafana dashboard delivered as a labelled ConfigMap (sidecar auto-imports)
resource "kubernetes_config_map_v1" "dashboard" {
  metadata {
    name      = "gpu-inference-dashboard"
    namespace = "observability"
    labels    = { grafana_dashboard = "1" }
  }
  data = { "gpu-inference-dashboard.json" = file("${path.module}/k8s/gpu-inference-dashboard.json") }
  depends_on = [helm_release.kps]
}

############################################
# Workload manifests via kubectl provider
############################################
data "kubectl_file_documents" "namespaces" { content = file("${path.module}/k8s/00-namespaces.yaml") }
data "kubectl_file_documents" "nodepool"   { content = file("${path.module}/k8s/10-nodepool-gpu.yaml") }
data "kubectl_file_documents" "workloads" {
  content = join("\n---\n", [
    file("${path.module}/k8s/20-dcgm.yaml"),
    file("${path.module}/k8s/30-vllm.yaml"),
    file("${path.module}/k8s/40-fluentbit.yaml"),
    file("${path.module}/k8s/50-otel.yaml"),
    file("${path.module}/k8s/55-jaeger.yaml"),
  ])
}
data "kubectl_file_documents" "servicemonitors" { content = file("${path.module}/k8s/60-servicemonitors.yaml") }

resource "kubectl_manifest" "namespaces" {
  for_each          = data.kubectl_file_documents.namespaces.manifests
  yaml_body         = each.value
  server_side_apply = true
  depends_on        = [module.eks]
}

resource "kubectl_manifest" "nodepool" {
  for_each          = data.kubectl_file_documents.nodepool.manifests
  yaml_body         = each.value
  server_side_apply = true
  depends_on        = [module.eks]
}

resource "kubectl_manifest" "workloads" {
  for_each          = data.kubectl_file_documents.workloads.manifests
  yaml_body         = each.value
  server_side_apply = true
  depends_on        = [kubectl_manifest.namespaces, kubectl_manifest.nodepool]
}

resource "kubectl_manifest" "servicemonitors" {
  for_each          = data.kubectl_file_documents.servicemonitors.manifests
  yaml_body         = each.value
  server_side_apply = true
  depends_on        = [helm_release.kps, kubectl_manifest.workloads]
}
