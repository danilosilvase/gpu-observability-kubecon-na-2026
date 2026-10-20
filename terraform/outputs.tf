output "cluster_name" { value = module.eks.cluster_name }
output "region" { value = var.region }
output "configure_kubectl" {
  description = "Command that points kubectl at the cluster."
  value       = "aws eks update-kubeconfig --name ${module.eks.cluster_name} --region ${var.region}${var.aws_profile == null ? "" : " --profile ${var.aws_profile}"}"
}
