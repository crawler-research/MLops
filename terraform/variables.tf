variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "project_name" {
  type    = string
  default = "mlops-train-automation"
}

variable "environment" {
  type    = string
  default = "dev"
}

variable "lambda_runtime" {
  type    = string
  default = "python3.11"
}

variable "lambda_timeout" {
  type    = number
  default = 60
}

variable "lambda_memory_size" {
  type    = number
  default = 256
}

variable "tags" {
  type = map(string)
  default = {
    Project     = "mlops-train-automation"
    Environment = "dev"
    ManagedBy   = "terraform"
  }
}
