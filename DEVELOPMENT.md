# Diving with John — Developer Guide

## Stack

- **Backend**: FastAPI (Python 3.11) + Mangum (Lambda adapter)
- **Database**: DynamoDB (local dev: DynamoDB Local via Docker)
- **Frontend**: Static HTML/CSS/JS
- **Deployment**: AWS Lambda + API Gateway + DynamoDB (via AWS SAM)

---

## Local Development

### Requirements

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)

### Start the site

```bash
cd divingwithjohn
docker-compose up
```

This starts:
- **DynamoDB Local** on port 8001
- **App** on port 8000

### First run — seed the database

```bash
docker-compose exec app python db_init.py
```

### Open in browser

| URL | Description |
|-----|-------------|
| http://localhost:8000 | Main website |
| http://localhost:8000/admin.html | Admin panel |

**Admin token**: `divejohn2026` (set in `backend/.env`)

### Stop

```bash
docker-compose down
```

---

## Without Docker (venv)

```bash
# Terminal 1 — DynamoDB Local
docker run -p 8001:8000 amazon/dynamodb-local -jar DynamoDBLocal.jar -sharedDb

# Terminal 2 — App
cd divingwithjohn/backend
source ../.venv/bin/activate
DYNAMODB_ENDPOINT_URL=http://localhost:8001 \
AWS_ACCESS_KEY_ID=local \
AWS_SECRET_ACCESS_KEY=local \
AWS_DEFAULT_REGION=us-east-1 \
ADMIN_TOKEN=divejohn2026 \
python db_init.py

DYNAMODB_ENDPOINT_URL=http://localhost:8001 \
AWS_ACCESS_KEY_ID=local \
AWS_SECRET_ACCESS_KEY=local \
AWS_DEFAULT_REGION=us-east-1 \
ADMIN_TOKEN=divejohn2026 \
uvicorn main:app --reload --port 8000
```

---

## Deploy to AWS (~$0–1/month)

### Requirements

- [AWS CLI](https://aws.amazon.com/cli/) — `brew install awscli`
- [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html) — `brew install aws-sam-cli`

### Configure AWS credentials

```bash
aws configure
# AWS Access Key ID: <your key>
# AWS Secret Access Key: <your secret>
# Default region: ap-southeast-1  (or closest to your users)
# Default output format: json
```

### Store admin token securely in AWS

```bash
aws ssm put-parameter \
  --name /divingwithjohn/admin-token \
  --value "divejohn2026" \
  --type SecureString
```

### Build

```bash
cd divingwithjohn
sam build
```

### Deploy

```bash
sam deploy --guided
```

Answer the prompts:
- **Stack Name**: `divingwithjohn`
- **AWS Region**: `ap-southeast-1` (or your preferred region)
- **SiteHost**: leave blank for now, update after deploy
- **Save arguments to config**: `Y`

At the end SAM prints your live URL:
```
Outputs:
  ApiUrl = https://abc123.execute-api.ap-southeast-1.amazonaws.com
```

### Seed the database (first deploy only)

```bash
cd backend
AWS_DEFAULT_REGION=ap-southeast-1 python db_init.py
```

### Redeploy after changes

```bash
sam build && sam deploy
```

---

## Project Structure

```
divingwithjohn/
├── backend/
│   ├── main.py          # FastAPI app + all API routes
│   ├── models.py        # Pydantic request models
│   ├── db_init.py       # Creates DynamoDB tables + seeds data
│   ├── requirements.txt
│   ├── Makefile         # SAM build hook
│   └── .env             # Local env vars (not committed)
├── frontend/
│   ├── index.html       # Main website
│   └── admin.html       # Admin panel
├── docker-compose.yml   # Local dev (app + DynamoDB Local)
├── Dockerfile           # App container
├── template.yaml        # AWS SAM deployment template
└── deploy/
    ├── cloudflare_pages.md
    └── aws_lambda.md
```

---

## Environment Variables

| Variable | Local (.env) | Production (AWS) |
|----------|-------------|------------------|
| `ADMIN_TOKEN` | `divejohn2026` | Read from SSM (`/divingwithjohn/admin-token`) |
| `DYNAMODB_ENDPOINT_URL` | `http://dynamodb-local:8000` | Not set (uses real AWS) |
| `AWS_ACCESS_KEY_ID` | `local` | IAM role (automatic) |
| `AWS_SECRET_ACCESS_KEY` | `local` | IAM role (automatic) |
| `AWS_DEFAULT_REGION` | `us-east-1` | Set in template.yaml |
| `SITE_HOST` | `http://localhost:8000` | Your domain |

---

## GitHub

Repository: https://github.com/amiu888/divingwithjohn

```bash
# Push changes
git add .
git commit -m "your message"
git push origin main
```
