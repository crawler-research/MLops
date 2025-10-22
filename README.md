
Pipeline flow: ValidateData → CheckValidation → LogMetrics → Success

```bash
cd terraform/lambda
zip validate.zip validate.py
zip log_metrics.zip log_metrics.py
```


```bash
chmod +x build_lambda.sh
./build_lambda.sh
```


```bash
aws configure
```

```bash
cd terraform
terraform init
terraform validate
terraform plan
terraform apply
```

```bash
terraform output -json > terraform_outputs.json
terraform output step_function_arn
```

```bash
export STEP_FUNCTION_ARN=$(terraform output -raw step_function_arn)

aws stepfunctions start-execution \
  --state-machine-arn "$STEP_FUNCTION_ARN" \
  --name "train-manual-$(date +%s)" \
  --input '{
    "source": "manual",
    "commit": "abc1234",
    "branch": "lesson-10",
    "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"
  }'
```


## GitLab CI

```json
{
  "source": "gitlab-ci",
  "commit": "abc1234",
  "branch": "lesson-10",
  "pipeline_id": "12345",
  "timestamp": "2025-10-22T10:00:00Z"
}
```

