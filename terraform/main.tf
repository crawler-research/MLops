terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

resource "aws_iam_role" "lambda_role" {
  name = "${var.project_name}-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })

  tags = var.tags
}

resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "lambda_policy" {
  name = "${var.project_name}-lambda-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect   = "Allow"
        Action   = ["s3:GetObject", "s3:PutObject"]
        Resource = "arn:aws:s3:::*/*"
      }
    ]
  })
}

resource "aws_lambda_function" "validate" {
  filename         = "${path.module}/lambda/validate.zip"
  function_name    = "${var.project_name}-validate"
  role            = aws_iam_role.lambda_role.arn
  handler         = "validate.lambda_handler"
  source_code_hash = filebase64sha256("${path.module}/lambda/validate.zip")
  runtime         = var.lambda_runtime
  timeout         = var.lambda_timeout
  memory_size     = var.lambda_memory_size

  environment {
    variables = {
      ENVIRONMENT = var.environment
      PROJECT     = var.project_name
    }
  }

  tags = merge(var.tags, {
    Name = "${var.project_name}-validate"
  })
}

resource "aws_cloudwatch_log_group" "validate_logs" {
  name              = "/aws/lambda/${aws_lambda_function.validate.function_name}"
  retention_in_days = 7
  tags              = var.tags
}

resource "aws_lambda_function" "log_metrics" {
  filename         = "${path.module}/lambda/log_metrics.zip"
  function_name    = "${var.project_name}-log-metrics"
  role            = aws_iam_role.lambda_role.arn
  handler         = "log_metrics.lambda_handler"
  source_code_hash = filebase64sha256("${path.module}/lambda/log_metrics.zip")
  runtime         = var.lambda_runtime
  timeout         = var.lambda_timeout
  memory_size     = var.lambda_memory_size

  environment {
    variables = {
      ENVIRONMENT = var.environment
      PROJECT     = var.project_name
    }
  }

  tags = merge(var.tags, {
    Name = "${var.project_name}-log-metrics"
  })
}

resource "aws_cloudwatch_log_group" "log_metrics_logs" {
  name              = "/aws/lambda/${aws_lambda_function.log_metrics.function_name}"
  retention_in_days = 7
  tags              = var.tags
}

resource "aws_iam_role" "step_functions_role" {
  name = "${var.project_name}-sfn-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "states.amazonaws.com"
      }
    }]
  })

  tags = var.tags
}

resource "aws_iam_role_policy" "step_functions_policy" {
  name = "${var.project_name}-sfn-policy"
  role = aws_iam_role.step_functions_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["lambda:InvokeFunction"]
        Resource = [
          aws_lambda_function.validate.arn,
          aws_lambda_function.log_metrics.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogDelivery",
          "logs:GetLogDelivery",
          "logs:UpdateLogDelivery",
          "logs:DeleteLogDelivery",
          "logs:ListLogDeliveries",
          "logs:PutResourcePolicy",
          "logs:DescribeResourcePolicies",
          "logs:DescribeLogGroups"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_cloudwatch_log_group" "step_functions_logs" {
  name              = "/aws/vendedlogs/states/${var.project_name}-pipeline"
  retention_in_days = 7
  tags              = var.tags
}

resource "aws_sfn_state_machine" "ml_training_pipeline" {
  name     = "${var.project_name}-pipeline"
  role_arn = aws_iam_role.step_functions_role.arn

  definition = jsonencode({
    Comment = "ML Training Pipeline"
    StartAt = "ValidateData"
    States = {
      ValidateData = {
        Type     = "Task"
        Resource = aws_lambda_function.validate.arn
        Next     = "CheckValidation"
        Retry = [{
          ErrorEquals     = ["States.TaskFailed"]
          IntervalSeconds = 2
          MaxAttempts     = 2
          BackoffRate     = 2.0
        }]
        Catch = [{
          ErrorEquals = ["States.ALL"]
          Next        = "ValidationFailed"
        }]
      }
      CheckValidation = {
        Type = "Choice"
        Choices = [{
          Variable     = "$.validation_status"
          StringEquals = "passed"
          Next         = "LogMetrics"
        }]
        Default = "ValidationFailed"
      }
      LogMetrics = {
        Type     = "Task"
        Resource = aws_lambda_function.log_metrics.arn
        Next     = "TrainingSuccess"
        Retry = [{
          ErrorEquals     = ["States.TaskFailed"]
          IntervalSeconds = 2
          MaxAttempts     = 2
          BackoffRate     = 2.0
        }]
      }
      TrainingSuccess = {
        Type = "Succeed"
      }
      ValidationFailed = {
        Type  = "Fail"
        Error = "ValidationError"
        Cause = "Data validation failed"
      }
    }
  })

  logging_configuration {
    log_destination        = "${aws_cloudwatch_log_group.step_functions_logs.arn}:*"
    include_execution_data = true
    level                  = "ALL"
  }

  tags = var.tags
}

output "step_function_arn" {
  value = aws_sfn_state_machine.ml_training_pipeline.arn
}

output "step_function_name" {
  value = aws_sfn_state_machine.ml_training_pipeline.name
}

output "validate_lambda_arn" {
  value = aws_lambda_function.validate.arn
}

output "log_metrics_lambda_arn" {
  value = aws_lambda_function.log_metrics.arn
}

output "validate_lambda_name" {
  value = aws_lambda_function.validate.function_name
}

output "log_metrics_lambda_name" {
  value = aws_lambda_function.log_metrics.function_name
}
