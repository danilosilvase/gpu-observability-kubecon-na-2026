variable "region" {
  description = "AWS Region. Must offer g5 or g6 instances."
  type        = string
  default     = "eu-central-1"
}

variable "aws_profile" {
  description = "Named AWS CLI profile. Leave null to use the default credential chain (environment variables, SSO, instance role)."
  type        = string
  default     = null

  validation {
    condition     = var.aws_profile == null ? true : length(var.aws_profile) > 0
    error_message = "aws_profile must be a profile name, or omitted."
  }
}

variable "cluster_name" {
  description = "EKS cluster name. The demo scripts default to gpu-obs-demo; export CLUSTER if you change it."
  type        = string
  default     = "gpu-obs-demo"
}

variable "cluster_version" {
  description = "Kubernetes version for the EKS cluster."
  type        = string
  default     = "1.37"
}

variable "admin_cidrs" {
  description = "CIDRs allowed to reach the EKS API endpoint, e.g. [\"203.0.113.7/32\"]. Use your own IP; nothing else in the stack is public."
  type        = list(string)

  validation {
    condition = length(var.admin_cidrs) > 0 && alltrue([
      for c in var.admin_cidrs : can(cidrnetmask(c)) && !startswith(c, "0.0.0.0/") && !startswith(c, "203.0.113.")
    ])
    error_message = "Set admin_cidrs to your own public IP as a CIDR, for example [\"198.51.100.20/32\"] (find it with: curl -s https://checkip.amazonaws.com). 0.0.0.0/x and the example range are rejected."
  }
}

variable "grafana_admin_password" {
  description = "Grafana admin password. Grafana is only reachable through kubectl port-forward. If you change it, export GRAFANA_PASSWORD for the demo scripts."
  type        = string
  default     = "gpu-obs-demo"
  sensitive   = true
}
