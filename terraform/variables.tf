variable "region" { default = "eu-central-1" }
variable "aws_profile" { default = "default" }
variable "cluster_name" { default = "gpu-obs-demo" }
variable "cluster_version" { default = "1.37" } # latest in EKS standard support (Oct 2026); rig built on 1.31 until the Oct 21 rebuild
# IPs allowed to reach the EKS API endpoint. The default is wide open so the module validates;
# ALWAYS narrow it in terraform/terraform.tfvars (gitignored), together with aws_profile:
#   aws_profile = "my-admin-profile"
#   admin_cidrs = ["203.0.113.7/32"]
variable "admin_cidrs" {
  type    = list(string)
  default = ["0.0.0.0/0"]
}
