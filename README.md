# AWS Data Pipeline Exercise

A small processing pipeline to practice **IAM**, **S3**, **EC2/ECS**, **VPC**, **DynamoDB**, **Lambda**, and **SNS** with least-privilege security.

**Stack:** Terraform, Python (Django + Poetry), Lambda (Python).

## What to Do (Summary)

1. **Configure** – Copy `terraform/terraform.tfvars.example` to `terraform/terraform.tfvars` and set `phone_number` (E.164) and `aws_region`.
2. **Deploy infra** – `cd terraform && terraform init && terraform apply`
3. **Build & push image** – `./scripts/push-image.sh` (from repo root; requires Docker and AWS CLI).
4. **Test** – `curl -X POST http://<ALB_DNS_NAME>/api/ingest/ -H "Content-Type: application/json" -d '{"message":"Hello"}'`  
   Use `terraform output alb_dns_name` for `<ALB_DNS_NAME>`.
5. **Verify** – Check DynamoDB table, S3 results bucket, and your phone for SMS.

## Architecture Overview

```
[Your laptop] --HTTP--> [ALB] --> [ECS Web Service x2] (private subnet)
                                |
                                v (VPC Endpoint)
                          [DynamoDB Table]
                                |
                                v (Stream)
                          [Lambda]
                                |
                    +-----------+-----------+
                    v                       v
              [S3 results bucket]      [SNS → SMS]
```

- You send an HTTP request to the **Application Load Balancer**.
- **ECS "Web Service"** (2 tasks in a **private subnet**) receives the request and writes the payload to **DynamoDB** via a **VPC Endpoint**.
- **DynamoDB** triggers a **Lambda** (via DynamoDB Streams).
- **Lambda** writes each record as JSON to a **private S3** bucket and sends an **SMS** via **SNS** with the write status.

All components use **IAM roles and policies** with **least privilege**.

## Prerequisites

- **AWS CLI** configured (`aws configure`) with credentials that can create VPC, ECS, DynamoDB, Lambda, S3, SNS, IAM.
- **Terraform** >= 1.x.
- **Docker** (to build and push the ECS image).
- **Poetry** (for the Django app).
- **Python** 3.11+ (for Django and Lambda).

## What You Need to Do

### 1. Set Your Phone Number for SMS

In `terraform/terraform.tfvars` (create from `terraform/terraform.tfvars.example`):

```hcl
phone_number = "+1234567890"  # E.164 format
aws_region   = "us-east-1"
```

### 2. Deploy Infrastructure with Terraform

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

After apply, note the outputs: **ALB DNS name**, **S3 bucket name**, **DynamoDB table name**, etc.

### 3. Build and Push the Web Service Image

```bash
# From repo root
cd web_service
poetry install
poetry run python manage.py check

# Get ECR login and push (use your AWS region and account id from Terraform output)
aws ecr get-login-password --region <region> | docker login --username AWS --password-stdin <account_id>.dkr.ecr.<region>.amazonaws.com
docker build --platform linux/amd64 -t pipeline-web-service .
docker tag pipeline-web-service:latest <account_id>.dkr.ecr.<region>.amazonaws.com/pipeline-web-service:latest
docker push <account_id>.dkr.ecr.<region>.amazonaws.com/pipeline-web-service:latest
```

### 4. Send a Test Request

```bash
curl -X POST "http://<ALB_DNS_NAME>/api/ingest/" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello pipeline", "source": "exercise"}'
```

Replace `<ALB_DNS_NAME>` with the ALB DNS name from `terraform output alb_dns_name`.

### 5. Verify the Pipeline

- **DynamoDB**: In AWS Console, check the table for the new item.
- **S3**: Check the private results bucket for a new JSON object.
- **SMS**: You should receive an SMS with the status of the S3 write.

## Project Layout

```
aws_exc/
├── README.md                 # This file
├── terraform/
│   ├── main.tf               # VPC, ALB, ECS, DynamoDB, Lambda, S3, SNS, IAM
│   ├── variables.tf
│   ├── outputs.tf
│   └── terraform.tfvars.example
├── web_service/              # Django app (ECS "Web Service")
│   ├── pyproject.toml        # Poetry
│   ├── Dockerfile
│   ├── manage.py
│   ├── config/
│   │   ├── settings.py
│   │   └── urls.py
│   └── api/
│       └── views.py          # Ingest endpoint → DynamoDB
├── lambda/
│   └── handler.py            # DynamoDB stream → S3 + SNS
```

## Security (Least Privilege)

- **ECS task role**: Only `dynamodb:PutItem` (and optionally `GetItem`) on the pipeline table.
- **Lambda execution role**: `logs:CreateLogGroup/Stream/LogEvents`; `s3:PutObject` on the results bucket; `sns:Publish` on the pipeline topic.
- **Lambda (optional)**: In VPC only if it needs to reach private resources; here it uses S3 and SNS public endpoints.
- **S3 bucket**: Private, no public access; access only via IAM (Lambda, and optionally ECS if needed later).
- **DynamoDB**: VPC endpoint in the same VPC so ECS tasks never use the public internet for DynamoDB.

## Troubleshooting (e.g. 503 from ALB)

If you get **503 Service Temporarily Unavailable**, the ALB has no healthy targets. See **[DEBUGGING.md](DEBUGGING.md)** for step-by-step checks (ECR image, ECS tasks, target group health, security groups, logs).

## Cleanup

```bash
cd terraform
terraform destroy
```

Empty the S3 bucket first if Terraform fails to destroy it (e.g. versioning or objects present).

## Concepts Covered

| Concept | Where |
|--------|--------|
| IAM & least privilege | Task roles, Lambda role, bucket policy |
| S3 | Private results bucket, Lambda writes JSON |
| EC2/ECS | ECS Fargate (or ASG) for "Web Service" |
| ECR | Repository for web service image |
| VPC | New VPC, public/private subnets, DynamoDB endpoint |
| DynamoDB | Table + stream for pipeline |
| Lambda | Stream consumer → S3 + SNS |
| SNS | SMS after each Lambda run |
