# Django Blog: CI/CD 

Django REST API (JWT) · Postgres · Nginx · Docker · GitHub Actions (CI on GitHub-hosted, CD on self-hosted runner)  · Frontend on Netlify.

## Live links (fill in after deploying)
| Item | Value |
|---|---|
| Netlify frontend | `https://<your-site>.netlify.app` |
| Demo login | user `demo` / password `demo12345` (change in `k8s/config.yaml`) |


## Repo layout
```
backend/            Django app (models Author/Post/Comment, simplejwt, tests)
frontend/           index.html + netlify.toml (Netlify-ready)
docker/             Dockerfile, entrypoint.sh, docker-compose.yml, nginx/default.conf
k8s/                namespace, config, postgres, deployment, service, ingress
monitoring/         Helm values + ServiceMonitor
.github/workflows/  ci.yml, cd.yml
```

## API
| Method | Path | Auth |
|---|---|---|
| POST | `/api/token/` (`/api/token/refresh/`) | no |
| GET / POST | `/posts/` | POST needs `Authorization: Bearer <access>` |
| GET / POST | `/posts/<id>/comments/` | POST needs auth |
| GET | `/health/` → `{"status":"ok"}` | no |
| GET | `/readiness/` → `{"status":"ready"}` (checks DB) | no |
| GET | `/metrics` (Prometheus) | no |

## 1. Run locally
```bash
docker compose -f docker/docker-compose.yml up --build
```
Open **http://localhost/** and sign in with `demo` / `demo12345`.
(Nginx serves the frontend and proxies the API; Postgres runs in its own container.)

Without Docker: `cd backend && pip install -r requirements-dev.txt && python manage.py migrate && python manage.py create_demo_user && python manage.py runserver`, then `pytest` and `flake8 .` for checks.

## 2. Deploy

### a) GitHub secrets
`DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN`.


Test: `curl http://<ELB>/health/`

## Live links
| Item | Value |
|---|---|
| Netlify frontend | https://django-blog-frontend.netlify.app/ |
| Demo login | demo / demo12345 |
| Backend | https://<your-render-url>.onrender.com |
| Grafana | Not deployed |

## Deployment notes
- CI (lint, tests, Docker build and push to Docker Hub) runs on GitHub Actions.
- The backend runs on Render from the Docker Hub image `amgu/django-blog`.
- I could not set up an AWS account (payment method not accepted), so the Kubernetes
  manifests (`k8s/`), the self-hosted-runner CD workflow and the monitoring configs
  (`monitoring/`) were not deployed to AWS. I ran the manifests on a local minikube
  cluster and confirmed `/health/` and `/readiness/` pass there.

### d) Frontend on Netlify
1. In `frontend/netlify.toml` replace `BACKEND_HOST` with the ingress ELB hostname.
2. Netlify → Add site → Import from GitHub → base directory `frontend`, no build command, publish directory `.`
3. Netlify proxies `/api/*` and `/posts/*` to the backend, so the page stays HTTPS with no CORS/mixed-content problems.
4. For the "ID and password" requirement, share the demo login above. If you want Netlify's own site password, use Site settings → Access & security → Visitor access (paid plan).


