# Docker容器化部署：多环境配置+镜像优化

> **文章信息**：标题《Docker容器化部署：多环境配置+镜像优化》| 字数：约4000字 | 预估阅读时间：18分钟

---

## 1. 为什么需要Docker部署

传统部署的问题：
- 本地能跑，生产环境报错（依赖版本不一致）
- 不同机器环境不同（A机器MySQL 8.0，B机器5.7）
- 升级时影响正在运行的服务
- 多服务器部署重复劳动

Docker解决的核心问题：**环境一致性**。你的代码在什么环境开发，就在什么环境运行。

---

## 2. FastAPI项目Docker化

### 2.1 项目结构

```bash
fastapi-docker/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── health.py
│   │   └── api.py
│   ├── models/
│   ├── services/
│   └── config.py
├── tests/
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── .dockerignore
├── requirements.txt
└── pytest.ini
```

### 2.2 requirements.txt

```
fastapi==0.115.0
uvicorn[standard]==0.30.0
pydantic==2.8.0
pydantic-settings==2.4.0
sqlalchemy==2.0.35
asyncpg==0.29.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.9
httpx==0.27.0
redis==5.0.8
structlog==24.2.0
slowapi==0.1.9
alembic==1.13.2
```

### 2.3 多阶段构建Dockerfile

```dockerfile
# ============ 阶段1：构建 ============
FROM python:3.12-slim AS builder

# 设置工作目录
WORKDIR /app

# 安装构建依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件先安装（利用Docker缓存）
COPY requirements.txt .

# 创建虚拟环境并安装依赖
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ============ 阶段2：运行 ============
FROM python:3.12-slim AS runner

# 安全：创建非root用户
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/bash appuser

WORKDIR /app

# 复制虚拟环境
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 安全：以非root用户运行
USER appuser

# 复制应用代码（先创建目录避免权限问题）
RUN mkdir -p /home/appuser/app
COPY --chown=appuser:appgroup app /app

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health').raise_for_status()"

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2.4 .dockerignore

```gitignore
__pycache__
*.pyc
*.pyo
*.pyd
.Python
*.so
*.egg
*.egg-info
dist
build
.pytest_cache
.coverage
htmlcov
.git
.gitignore
.env
.venv
venv/
ENV
.DS_Store
*.md
tests/
```

---

## 3. 多环境docker-compose配置

### 3.1 开发环境（dev）

```yaml
# docker-compose.dev.yml
version: "3.9"

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
      target: runner
    ports:
      - "8000:8000"
    environment:
      - ENV=development
      - LOG_LEVEL=debug
      - DATABASE_URL=postgresql+asyncpg://appuser:devpass@db:5432/fastapi_dev
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - ./app:/app/app:ro  # 开发时热重载（只读代码）
    depends_on:
      - db
      - redis
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  db:
    image: postgres:16-alpine
    environment:
      - POSTGRES_USER=appuser
      - POSTGRES_PASSWORD=devpass
      - POSTGRES_DB=fastapi_dev
    ports:
      - "5432:5432"
    volumes:
      - postgres_dev_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_dev_data:/data

volumes:
  postgres_dev_data:
  redis_dev_data:
```

### 3.2 预发布环境（staging）

```yaml
# docker-compose.staging.yml
version: "3.9"

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
      target: runner
    environment:
      - ENV=staging
      - LOG_LEVEL=info
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
    secrets:
      - db_password
      - redis_password
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: "1"
          memory: 1G
        reservations:
          cpus: "0.5"
          memory: 512M
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s

  db:
    image: postgres:16-alpine
    environment:
      - POSTGRES_USER=appuser
      - POSTGRES_PASSWORD_FILE=/run/secrets/db_password
      - POSTGRES_DB=fastapi_staging
    volumes:
      - postgres_staging_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass-file /run/secrets/redis_password
    volumes:
      - redis_staging_data:/data

secrets:
  db_password:
    file: ./secrets/db_password.txt
  redis_password:
    file: ./secrets/redis_password.txt

volumes:
  postgres_staging_data:
  redis_staging_data:
```

### 3.3 生产环境（prod）

```yaml
# docker-compose.prod.yml
version: "3.9"

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
      target: runner
    image: registry.example.com/fastapi-app:v1.2.3
    ports:
      - "8000:8000"
    environment:
      - ENV=production
      - LOG_LEVEL=warning
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
    deploy:
      replicas: 4
      resources:
        limits:
          cpus: "2"
          memory: 2G
        reservations:
          cpus: "1"
          memory: 1G
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 15s
    restart: unless-stopped
    logging:
      driver: "json-file"
      options:
        max-size: "100m"
        max-file: "3"

  db:
    image: postgres:16-alpine
    environment:
      - POSTGRES_USER=appuser
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_DB=fastapi_prod
    volumes:
      - postgres_prod_data:/var/lib/postgresql/data
    deploy:
      resources:
        limits:
          memory: 2G

  redis:
    image: redis:7-alpine
    command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_prod_data:/data
    deploy:
      resources:
        limits:
          memory: 1G

volumes:
  postgres_prod_data:
  redis_prod_data:
```

---

## 4. 镜像优化技巧

### 4.1 减少镜像大小

**问题**：Python镜像通常很大（>800MB）

**优化方法**：
1. 使用`slim`或`alpine`变体（减少300-500MB）
2. 多阶段构建（分离构建和运行环境）
3. 合并RUN指令减少层数
4. 不安装构建工具到最终镜像

### 4.2 利用构建缓存

```dockerfile
# 依赖文件单独复制（利用缓存）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 应用代码最后复制（代码变时不影响依赖层）
COPY app ./app
```

### 4.3 镜像大小对比

| 基础镜像 | 大小 |
|------|------|
| python:3.12 | ~1GB |
| python:3.12-slim | ~150MB |
| python:3.12-alpine | ~50MB |
| 多阶段构建 | ~130MB |

### 4.4 构建加速

```bash
# 使用BuildKit
export DOCKER_BUILDKIT=1

# 并行构建依赖
docker build --progress=plain -t fastapi-app .

# 推送时压缩
docker save fastapi-app | gzip | ssh server 'docker load'
```

---

## 5. Kubernetes部署

### 5.1 Deployment配置

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fastapi-app
  labels:
    app: fastapi-app
    version: v1
spec:
  replicas: 4
  selector:
    matchLabels:
      app: fastapi-app
  template:
    metadata:
      labels:
        app: fastapi-app
        version: v1
    spec:
      containers:
        - name: api
          image: registry.example.com/fastapi-app:v1.2.3
          ports:
            - containerPort: 8000
          env:
            - name: ENV
              value: "production"
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: fastapi-secrets
                  key: database-url
            - name: DEEPSEEK_API_KEY
              valueFrom:
                secretKeyRef:
                  name: fastapi-secrets
                  key: deepseek-api-key
          resources:
            requests:
              memory: "512Mi"
              cpu: "250m"
            limits:
              memory: "2Gi"
              cpu: "2000m"
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 15
            periodSeconds: 30
            timeoutSeconds: 5
            failureThreshold: 3
          readinessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 10
            timeoutSeconds: 3
            failureThreshold: 3
          lifecycle:
            preStop:
              exec:
                command: ["/bin/sh", "-c", "sleep 10"]
```

### 5.2 Service配置

```yaml
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: fastapi-service
spec:
  type: ClusterIP
  selector:
    app: fastapi-app
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8000
```

### 5.3 Ingress配置

```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: fastapi-ingress
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/proxy-body-size: "50m"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "300"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "300"
spec:
  tls:
    - hosts:
        - api.example.com
      secretName: tls-secret
  rules:
    - host: api.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: fastapi-service
                port:
                  number: 80
```

### 5.4 HPA自动扩缩容

```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: fastapi-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: fastapi-app
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
```

---

## 6. CI/CD流程

### 6.1 GitHub Actions

```yaml
# .github/workflows/deploy.yml
name: Build and Deploy

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      
      - name: Cache pip packages
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Run tests
        run: pytest tests/ -v --cov=app

  build-and-push:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      
      - name: Login to Container Registry
        uses: docker/login-action@v3
        with:
          registry: registry.example.com
          username: ${{ secrets.REGISTRY_USER }}
          password: ${{ secrets.REGISTRY_PASSWORD }}
      
      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: |
            registry.example.com/fastapi-app:${{ github.sha }}
            registry.example.com/fastapi-app:latest
          cache-from: type=gha
          cache-to: type=gha,mode=max

  deploy-staging:
    needs: build-and-push
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - name: Deploy to staging
        run: |
          kubectl config use-context staging
          kubectl set image deployment/fastapi-app api=registry.example.com/fastapi-app:${{ github.sha }}
          kubectl rollout status deployment/fastapi-app

  deploy-production:
    needs: deploy-staging
    runs-on: ubuntu-latest
    environment: production
    when: github.ref == 'refs/heads/main'
    steps:
      - name: Deploy to production
        run: |
          kubectl config use-context production
          kubectl set image deployment/fastapi-app api=registry.example.com/fastapi-app:${{ github.sha }}
          kubectl rollout status deployment/fastapi-app
          kubectl rollout history deployment/fastapi-app
```

---

## 7. 踩坑记录

### 坑1：Dockerfile中COPY权限问题

**问题**：以root用户构建，但运行时用非root用户，权限不匹配。

**解决**：使用`COPY --chown`指定所有者：
```dockerfile
COPY --chown=appuser:appgroup app /app
```

### 坑2：多阶段构建target选择错误

**问题**：在`docker build --target builder`时，不小心构建了整个镜像，失去了多阶段构建的优势。

**解决**：明确指定`Dockerfile`的target：
```bash
docker build --target runner -t fastapi-app .
```

### 坑3：健康检查导致服务被重启

**问题**：应用启动慢（初始化数据库、加载模型），但健康检查在30秒内未通过就被重启。

**解决**：调整健康检查参数：
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 60s  # 给够启动时间
```

### 坑4：内存限制导致OOM

**问题**：Python进程内存增长没有限制，K8s的OOMKilled杀死容器。

**解决**：在应用层面添加内存监控和限制：
```python
import resource

# 设置最大内存为1GB
soft, hard = resource.getrlimit(resource.RLIMIT_AS)
resource.setrlimit(resource.RLIMIT_AS, (1024 * 1024 * 1024, hard))
```

### 坑5：热重载时文件权限问题

**问题**：在K8s中通过volume挂载代码时，文件属主不匹配。

**解决**：在Pod启动前设置正确的属主：
```yaml
initContainers:
  - name: fix-permissions
    command: ["sh", "-c", "chown -R 1000:1000 /app"]
```

### 坑6：多副本部署时数据库连接池耗尽

**问题**：4个副本各创建自己的连接池，总连接数超过数据库限制。

**解决**：在数据库配置中限制连接池大小：
```python
engine = create_async_engine(
    DATABASE_URL,
    pool_size=5,  # 每实例5个连接
    max_overflow=2,
    pool_pre_ping=True,
)
```

---

## 8. 总结

本文覆盖了FastAPI应用Docker容器化的完整流程：

1. **多阶段构建**：分离构建和运行环境，镜像大小从1GB降到130MB
2. **docker-compose多环境**：dev/staging/prod分别配置
3. **K8s部署**：Deployment/Service/Ingress/HPA完整配置
4. **CI/CD**：GitHub Actions自动化构建和部署
5. **踩坑经验**：权限、健康检查、OOM、连接池等常见问题

**进阶方向**：
- 引入Helm Charts管理K8s配置
- 添加Prometheus监控和告警
- 实现蓝绿部署或金丝雀发布
- 引入服务网格（Istio）做流量管理