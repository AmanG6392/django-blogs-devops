# Django Blog: CI/CD + Kubernetes on AWS

Django REST API (JWT) · Postgres · Nginx · Docker · GitHub Actions (CI on GitHub-hosted, CD on self-hosted runner) · EKS/K8s · Prometheus + Grafana + Loki · Frontend on Netlify.

## Live links (fill in after deploying)
| Item | Value |
|---|---|
| Netlify frontend | `https://<your-site>.netlify.app` |
| Demo login | user `demo` / password `demo12345` (change in `k8s/config.yaml`) |
| AWS backend | `http://<ingress-elb-hostname-or-ip>` |
| Grafana | `http://<grafana-elb-hostname>` (login `admin` / your values-file password) |

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

### b) Kubernetes on AWS (EKS example)
```bash
eksctl create cluster --name blog --region ap-south-1 --nodes 2 --node-type t3.medium
helm upgrade --install ingress-nginx ingress-nginx --repo https://kubernetes.github.io/ingress-nginx \
  -n ingress-nginx --create-namespace
kubectl -n ingress-nginx get svc ingress-nginx-controller   # EXTERNAL-IP = your backend address
```
Edit secrets in `k8s/config.yaml` first. Then either push to `main` (CD does it) or apply manually:
```bash
kubectl apply -f k8s/namespace.yaml -f k8s/config.yaml -f k8s/postgres.yaml
kubectl apply -f k8s/deployment.yaml -f k8s/service.yaml -f k8s/ingress.yaml
```
Test: `curl http://<ELB>/health/`

### c) Self-hosted runner (used only by `cd.yml`)
1. Launch a small EC2 instance (Ubuntu). Install Docker and `kubectl`, `aws` CLI.
2. Give it cluster access: `aws eks update-kubeconfig --name blog --region ap-south-1` (instance role with `eks:DescribeCluster`, mapped in the cluster's `aws-auth`/access entries).
3. GitHub repo → Settings → Actions → Runners → New self-hosted runner → run the shown commands, then install as a service (`sudo ./svc.sh install && sudo ./svc.sh start`).
4. `ci.yml` uses `ubuntu-latest`; only `cd.yml` has `runs-on: self-hosted`. CD waits for CI to push the image of the same commit, then runs `kubectl apply`.

### d) Frontend on Netlify
1. In `frontend/netlify.toml` replace `BACKEND_HOST` with the ingress ELB hostname.
2. Netlify → Add site → Import from GitHub → base directory `frontend`, no build command, publish directory `.`
3. Netlify proxies `/api/*` and `/posts/*` to the backend, so the page stays HTTPS with no CORS/mixed-content problems.
4. For the "ID and password" requirement, share the demo login above. If you want Netlify's own site password, use Site settings → Access & security → Visitor access (paid plan).

### e) Monitoring
```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts && helm repo update
helm upgrade --install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
  -n monitoring --create-namespace -f monitoring/prometheus-grafana-values.yaml
helm upgrade --install loki grafana/loki-stack -n monitoring -f monitoring/loki-values.yaml
kubectl apply -f monitoring/servicemonitor.yaml
kubectl -n monitoring get svc kube-prometheus-stack-grafana   # Grafana URL
```
Django logs: Grafana → Explore → Loki → `{namespace="blog", app="blog-backend"}`.
Metrics: Explore → Prometheus → `django_http_requests_total_by_method_total`.
