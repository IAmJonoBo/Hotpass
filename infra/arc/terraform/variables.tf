variable "aws_region" {
  description = "AWS region where the ARC runner IAM role will be created"
  type        = string
}

variable "github_repository" {
  description = "GitHub repository in the form <owner>/<repo> that will assume the role"
  type        = string
}

variable "oidc_subjects" {
  description = "Additional GitHub OIDC subjects (e.g. environments, workflows) allowed to assume the role"
  type        = list(string)
  default     = []
}

variable "role_name" {
  description = "Name for the IAM role exposed to ARC runners"
  type        = string
  default     = "hotpass-arc-runner"
}

variable "s3_artifact_bucket" {
  description = "Optional S3 bucket ARN for workflow artifact storage"
  type        = string
  default     = ""
}
