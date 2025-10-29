output "arc_runner_role_arn" {
  description = "IAM role ARN assumed by the ARC runners"
  value       = aws_iam_role.arc_runner.arn
}

output "github_oidc_provider_arn" {
  description = "ARN for the GitHub OIDC identity provider"
  value       = aws_iam_openid_connect_provider.github.arn
}
