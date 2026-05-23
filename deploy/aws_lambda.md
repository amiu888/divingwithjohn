# Deploy to AWS Lambda + DynamoDB

Estimated cost: **$0–1/month** for a small diving school site.

## What gets deployed

- **Lambda** — runs the FastAPI app (API + HTML pages)
- **API Gateway HTTP API** — public URL that routes to Lambda
- **DynamoDB** — 9 tables, pay-per-request billing (free tier covers ~25 GB)

---

## Prerequisites

1. **AWS account** — https://aws.amazon.com (free tier works)
2. **AWS CLI** — `brew install awscli` or https://aws.amazon.com/cli/
3. **AWS SAM CLI** — `brew install aws-sam-cli` or https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html

Configure AWS credentials:
```bash
aws configure
# Enter your AWS Access Key ID, Secret, region (e.g. ap-southeast-1), output format: json
```

---

## Step 1 — Build

```bash
cd divingwithjohn
sam build
```

This installs Python dependencies and copies the frontend into the Lambda package.

---

## Step 2 — Deploy

```bash
sam deploy --guided
```

Answer the prompts:
- **Stack Name**: `divingwithjohn`
- **AWS Region**: pick the closest to your users (e.g. `ap-southeast-1` for Asia)
- **AdminToken**: your chosen admin password (e.g. `divejohn2026`)
- **SiteHost**: leave blank for now, update after deploy
- **Save arguments to config**: `Y`

At the end, SAM prints your URL:
```
Outputs:
  ApiUrl = https://abc123.execute-api.ap-southeast-1.amazonaws.com
```

---

## Step 3 — Seed the database

Run this once to create sample data:

```bash
# Install AWS credentials locally (already done in aws configure)
cd backend
pip install -r requirements.txt
AWS_DEFAULT_REGION=ap-southeast-1 python db_init.py
```

---

## Step 4 — (Optional) Custom domain

1. Buy a domain in Route 53 or use an existing one
2. Request a free SSL cert in **AWS Certificate Manager** (us-east-1 region)
3. Add a custom domain in **API Gateway → Custom Domains**
4. Point your domain's DNS to the API Gateway URL

---

## Updating the site

After any code or content change:
```bash
sam build && sam deploy
```

---

## Local development

Start DynamoDB Local + the app:
```bash
docker-compose up
```

This starts:
- DynamoDB Local on port 8001
- The app on port 8000 at http://localhost:8000

On first run, seed the local database:
```bash
docker-compose exec app python db_init.py
```

Or without Docker:
```bash
# Terminal 1 — DynamoDB Local
docker run -p 8001:8000 amazon/dynamodb-local -jar DynamoDBLocal.jar -sharedDb

# Terminal 2 — App
cd backend
source ../.venv/bin/activate
DYNAMODB_ENDPOINT_URL=http://localhost:8001 AWS_ACCESS_KEY_ID=local AWS_SECRET_ACCESS_KEY=local AWS_DEFAULT_REGION=us-east-1 ADMIN_TOKEN=divejohn2026 python db_init.py
DYNAMODB_ENDPOINT_URL=http://localhost:8001 AWS_ACCESS_KEY_ID=local AWS_SECRET_ACCESS_KEY=local AWS_DEFAULT_REGION=us-east-1 ADMIN_TOKEN=divejohn2026 uvicorn main:app --reload --port 8000
```

---

## Estimated AWS costs

| Service | Free tier | Paid |
|---------|-----------|------|
| Lambda | 1M requests/mo free | $0.20/M after |
| API Gateway | 1M requests/mo free | $1.00/M after |
| DynamoDB | 25 GB + 25 RCU/WCU free | Pay-per-request |
| **Total** | **$0/mo** | **<$1/mo** |
