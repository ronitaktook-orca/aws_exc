# Debugging 503 from the ALB

A **503 Service Temporarily Unavailable** from the ALB means it has **no healthy targets**. The request never reaches your Django app. Use these checks in order.

## 1. Confirm the image is in ECR

If you never ran `./scripts/push-image.sh`, ECS has no image to run.

```bash
# From repo root
./scripts/push-image.sh
```

Check in AWS Console: **ECR** → **Repositories** → `pipeline-web-service` → **Images**. You should see at least one image (e.g. `latest`).

## 2. Check ECS service and tasks

**Console:** **ECS** → **Clusters** → `pipeline-cluster` → **Services** → `web-service`.

- **Running tasks:** Should be **2**. If 0 or less than 2, open the service → **Tasks** tab and see why (Pending, Stopped, etc.).
- **Events:** On the service page, check **Events** for errors (e.g. "resource initialization failure", "CannotPullContainerError").

**CLI:**

```bash
# List tasks for the service (replace cluster/service name if you changed it)
aws ecs list-tasks --cluster pipeline-cluster --service-name web-service --region us-east-1

# If you get task ARNs, describe one to see last status and stop reason
aws ecs describe-tasks --cluster pipeline-cluster --tasks <TASK_ARN> --region us-east-1
```

Common causes:

- **CannotPullContainerError** → Image not in ECR or wrong name/tag; run `./scripts/push-image.sh`.
- **ResourceInitializationError** → Often logging or permissions; check task **Execution role** and **CloudWatch log group** `/ecs/pipeline-web-service`.
- **Tasks stuck Pending** → Not enough capacity or subnet/IP issues; check **Events** and **Capacity provider**.

## 3. Check target group health

ALB marks targets healthy only when the **health check** succeeds (`/health/` every 30s).

**Console:** **EC2** → **Target Groups** → `pipeline-web-tg` → **Targets**.

- **Healthy:** At least one target should be **Healthy**. If all are **Unhealthy** or **Initial**, see below.
- **Unhealthy** → Health checks failing. Either the app isn’t responding on port 80, or `/health/` returns an error or timeout.

**CLI:**

```bash
aws elbv2 describe-target-health \
  --target-group-arn $(aws elbv2 describe-target-groups --names pipeline-web-tg --query 'TargetGroups[0].TargetGroupArn' --output text --region us-east-1) \
  --region us-east-1
```

If targets are **Unhealthy**:

- Give tasks 2–3 minutes after they reach **Running** (health checks need 2 successes; interval 30s).
- Check **CloudWatch Logs** for the ECS service: **Log groups** → `/ecs/pipeline-web-service`. Look for Django/gunicorn errors or tracebacks.
- Optionally make the health check more tolerant (see below).

## 4. Check security groups

- **ALB:** Inbound 80 from 0.0.0.0/0; outbound all (or at least to ECS SG on 80).
- **ECS tasks:** Inbound 80 from ALB security group only.

**Console:** **EC2** → **Security Groups**. Open the ALB SG and the ECS SG and confirm the rules above.

## 5. Optional: relax health check (if app is slow to start)

If tasks start but are marked unhealthy before Django is ready, you can increase intervals and thresholds in `terraform/main.tf`:

```hcl
# In aws_lb_target_group.web health_check
interval            = 60
healthy_threshold   = 2
unhealthy_threshold = 5
timeout             = 10
```

Then run `terraform apply`. Prefer fixing the real cause (e.g. image not pushed, app crash) before relaxing health checks.

## Quick checklist

| Check | What to verify |
|-------|----------------|
| ECR | `pipeline-web-service` has an image (e.g. `latest`) |
| ECS service | 2 running tasks; no pull or startup errors in Events |
| Target group | At least one target **Healthy** |
| Security groups | ALB → ECS on 80 allowed |
| Logs | `/ecs/pipeline-web-service` has no Python tracebacks |

Most 503s here are fixed by **pushing the image** (`./scripts/push-image.sh`) and waiting 2–3 minutes for tasks to become **Running** and then **Healthy**.
