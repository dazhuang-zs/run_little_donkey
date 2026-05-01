# Docker/Kubernetes 实战：从入门到生产级部署

> 一篇帮助开发者理解容器化技术并掌握生产级部署实践的完整指南。

---

## 目录

- [一、为什么需要容器化](#一为什么需要容器化)
- [二、Docker 实战基础](#二docker-实战基础)
- [三、Kubernetes 实战进阶](#三kubernetes-实战进阶)
- [四、生产级最佳实践](#四生产级最佳实践)
- [五、常见问题排查](#五常见问题排查)
- [六、总结](#六总结)

---

## 一、为什么需要容器化

### 1.1 传统部署的痛点

在容器技术普及之前，应用部署面临着诸多挑战：

| 问题 | 表现 | 影响 |
|------|------|------|
| **环境不一致** | 「在我本地能跑」 | 开发、测试、生产环境差异导致 Bug |
| **依赖冲突** | 项目 A 需要 Node 16，项目 B 需要 Node 18 | 同一服务器无法共存 |
| **资源隔离差** | 一个应用占满资源，连累其他应用 | 服务不稳定 |
| **部署效率低** | 手动安装依赖、配置环境 | 发布周期长，容易出错 |
| **可移植性差** | 迁移到新服务器需要重新配置 | 扩展困难 |

### 1.2 容器化如何解决这些问题

**Docker** 提供了「一次构建，到处运行」的能力：

```
┌─────────────────────────────────────────────────────────┐
│                    容器化架构                            │
├─────────────────────────────────────────────────────────┤
│  应用代码 + 运行环境 + 依赖库 + 配置 = 容器镜像          │
│                                                         │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐                 │
│  │ 容器 A  │  │ 容器 B  │  │ 容器 C  │                 │
│  │ Node 18 │  │ Python  │  │ Java 17 │                 │
│  └─────────┘  └─────────┘  └─────────┘                 │
│  ─────────────────────────────────────                  │
│              Docker 引擎 (容器运行时)                    │
│  ─────────────────────────────────────                  │
│              操作系统 (Linux/Windows/macOS)              │
└─────────────────────────────────────────────────────────┘
```

**Kubernetes** 则在 Docker 之上提供了大规模容器编排能力：

- **自动化部署**：声明式配置，自动创建和管理容器
- **弹性伸缩**：根据负载自动扩缩容
- **自愈能力**：容器崩溃自动重启，节点故障自动迁移
- **服务发现**：内置 DNS 和负载均衡
- **滚动更新**：零停机部署

### 1.3 Docker 与 Kubernetes 的定位

| 技术 | 定位 | 核心能力 | 适用场景 |
|------|------|----------|----------|
| **Docker** | 容器运行时 | 构建、运行、分发容器 | 单机部署、开发环境 |
| **Kubernetes** | 容器编排平台 | 多节点管理、调度、自愈 | 生产集群、大规模部署 |

> **一句话总结**：Docker 解决「如何打包和运行一个应用」，Kubernetes 解决「如何管理成百上千个容器」。

---

## 二、Docker 实战基础

### 2.1 安装与环境准备

#### Linux (Ubuntu/Debian)

```bash
# 更新包索引
sudo apt-get update

# 安装依赖
sudo apt-get install ca-certificates curl gnupg

# 添加 Docker 官方 GPG 密钥
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# 添加仓库
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 安装 Docker
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# 验证安装
docker --version
# Docker version 24.0.7, build afdd53b

# 启动并设置开机自启
sudo systemctl enable --now docker

# 将当前用户加入 docker 组（免 sudo）
sudo usermod -aG docker $USER
# 注销重新登录后生效
```

#### macOS / Windows

下载安装 [Docker Desktop](https://www.docker.com/products/docker-desktop)，图形化安装即可。

安装后验证：

```bash
docker run hello-world
# 成功输出：Hello from Docker! This message shows that your installation appears to be working correctly.
```

### 2.2 Docker 核心概念

#### 镜像（Image）

镜像是容器的「蓝图」，包含运行应用所需的一切：代码、运行时、库、配置。

```bash
# 查看本地镜像
docker images

# 拉取镜像
docker pull nginx:latest
docker pull node:18-alpine  # 推荐 alpine 版本，体积小

# 搜索镜像
docker search redis

# 删除镜像
docker rmi nginx:latest
```

#### 容器（Container）

容器是镜像的「运行实例」。

```bash
# 运行容器
docker run -d --name my-nginx -p 8080:80 nginx:latest
# -d: 后台运行
# --name: 容器名称
# -p: 端口映射（宿主机:容器）

# 查看运行中的容器
docker ps

# 查看所有容器（包括已停止）
docker ps -a

# 进入容器
docker exec -it my-nginx /bin/bash

# 查看容器日志
docker logs my-nginx
docker logs -f my-nginx  # 实时追踪

# 停止/启动/重启容器
docker stop my-nginx
docker start my-nginx
docker restart my-nginx

# 删除容器
docker rm my-nginx
docker rm -f my-nginx  # 强制删除运行中的容器
```

#### 仓库（Registry）

仓库是存放镜像的地方，类似代码仓库。

- **Docker Hub**：官方公共仓库（hub.docker.com）
- **私有仓库**：Harbor、Nexus、阿里云容器镜像服务

```bash
# 登录仓库
docker login

# 给镜像打标签
docker tag my-app:latest my-registry.com/my-app:v1.0

# 推送镜像
docker push my-registry.com/my-app:v1.0

# 从私有仓库拉取
docker pull my-registry.com/my-app:v1.0
```

### 2.3 Dockerfile 编写规范

Dockerfile 是构建镜像的「脚本」，定义了如何从基础镜像创建自定义镜像。

#### 基础示例：Node.js 应用

```dockerfile
# syntax=docker/dockerfile:1

# 指定基础镜像
FROM node:18-alpine

# 设置工作目录
WORKDIR /app

# 复制依赖清单（利用缓存层）
COPY package*.json ./

# 安装依赖
RUN npm ci --only=production

# 复制应用代码
COPY . .

# 暴露端口（仅声明，实际映射需 -p）
EXPOSE 3000

# 设置环境变量
ENV NODE_ENV=production

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:3000/health || exit 1

# 启动命令
CMD ["node", "server.js"]
```

#### 关键指令详解

| 指令 | 作用 | 最佳实践 |
|------|------|----------|
| `FROM` | 指定基础镜像 | 使用官方镜像，优先 alpine 版本 |
| `WORKDIR` | 设置工作目录 | 使用绝对路径，自动创建 |
| `COPY` | 复制文件 | 先复制依赖清单，再复制代码（利用缓存） |
| `RUN` | 执行命令 | 合并多条命令减少层数 |
| `ENV` | 设置环境变量 | 敏感信息不要硬编码 |
| `EXPOSE` | 声明端口 | 仅文档作用，方便阅读 |
| `CMD` | 容器启动命令 | 使用 JSON 数组格式 |
| `ENTRYPOINT` | 入口点 | 配合 CMD 实现灵活启动 |

#### 多阶段构建优化

多阶段构建可以将构建环境和运行环境分离，大幅减小镜像体积。

```dockerfile
#syntax=docker/dockerfile:1

# ===== 构建阶段 =====
FROM node:18-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# ===== 运行阶段 =====
FROM nginx:alpine

# 从构建阶段复制产物
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制 nginx 配置
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

**效果对比**：

| 阶段 | 镜像大小 | 说明 |
|------|----------|------|
| 单阶段 | ~800MB | 包含完整 Node.js + 构建工具 |
| 多阶段 | ~25MB | 仅 Nginx + 静态文件 |

#### Dockerfile 最佳实践清单

- [ ] 使用明确的镜像版本标签（避免 `latest`）
- [ ] 使用 `.dockerignore` 排除无关文件
- [ ] 合并 `RUN` 命令，减少镜像层数
- [ ] 不要在镜像中存储敏感信息
- [ ] 使用非 root 用户运行应用
- [ ] 合理利用缓存，将不常变化的指令放前面

**示例 .dockerignore**：

```
node_modules
npm-debug.log
Dockerfile
.dockerignore
.git
.gitignore
README.md
.env
coverage
.nyc_output
```

### 2.4 Docker Compose 编排

当应用由多个服务组成时，Docker Compose 可以通过一个 YAML 文件定义和管理所有服务。

#### 完整示例：前后端分离应用

```yaml
# docker-compose.yml
version: '3.8'

services:
  # 前端服务
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      target: production
    ports:
      - "80:80"
    depends_on:
      - backend
    networks:
      - app-network
    restart: unless-stopped

  # 后端 API 服务
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - DATABASE_URL=postgresql://postgres:password@db:5432/myapp
      - REDIS_URL=redis://redis:6379
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
    networks:
      - app-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # PostgreSQL 数据库
  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=myapp
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    networks:
      - app-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  # Redis 缓存
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis-data:/data
    networks:
      - app-network
    restart: unless-stopped

networks:
  app-network:
    driver: bridge

volumes:
  postgres-data:
  redis-data:
```

#### 常用命令

```bash
# 启动所有服务（后台运行）
docker compose up -d

# 查看服务状态
docker compose ps

# 查看日志
docker compose logs
docker compose logs -f backend  # 实时追踪特定服务

# 重新构建并启动
docker compose up -d --build

# 停止所有服务
docker compose down

# 停止并删除数据卷
docker compose down -v

# 扩展服务（运行多个实例）
docker compose up -d --scale backend=3
```

### 2.5 实战案例：部署一个完整的 Web 应用

#### 项目结构

```
my-webapp/
├── backend/
│   ├── Dockerfile
│   ├── package.json
│   └── src/
│       └── server.js
├── frontend/
│   ├── Dockerfile
│   ├── nginx.conf
│   └── src/
│       └── ...
├── docker-compose.yml
└── .env
```

#### 后端 Dockerfile

```dockerfile
# backend/Dockerfile
FROM node:18-alpine

WORKDIR /app

# 安装 dumb-init（正确处理信号）
RUN apk add --no-cache dumb-init

COPY package*.json ./
RUN npm ci --only=production && npm cache clean --force

COPY src/ ./src/

# 创建非 root 用户
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nodejs -u 1001

USER nodejs

EXPOSE 3000

ENV NODE_ENV=production

ENTRYPOINT ["dumb-init", "--"]
CMD ["node", "src/server.js"]
```

#### 构建和推送镜像

```bash
# 构建镜像
docker build -t my-webapp-backend:v1.0 ./backend

# 本地测试运行
docker run -d -p 3000:3000 --name backend-test my-webapp-backend:v1.0

# 测试通过后打标签推送到仓库
docker tag my-webapp-backend:v1.0 registry.example.com/my-webapp-backend:v1.0
docker push registry.example.com/my-webapp-backend:v1.0
```

---

## 三、Kubernetes 实战进阶

### 3.1 核心概念解析

#### Pod（最小部署单元）

Pod 是 Kubernetes 中最小的可部署单元，一个 Pod 可以包含一个或多个紧密关联的容器。

```yaml
# pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: my-app
  labels:
    app: my-app
    tier: frontend
spec:
  containers:
  - name: app
    image: nginx:1.25-alpine
    ports:
    - containerPort: 80
    resources:
      requests:
        memory: "64Mi"
        cpu: "50m"
      limits:
        memory: "128Mi"
        cpu: "100m"
    livenessProbe:
      httpGet:
        path: /
        port: 80
      initialDelaySeconds: 10
      periodSeconds: 10
    readinessProbe:
      httpGet:
        path: /
        port: 80
      initialDelaySeconds: 5
      periodSeconds: 5
```

#### Deployment（控制器）

Deployment 管理 Pod 的副本数量，提供滚动更新和回滚能力。

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: my-app
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1        # 滚动更新时最多超出副本数
      maxUnavailable: 0  # 滚动更新时最多不可用副本数
  template:
    metadata:
      labels:
        app: my-app
    spec:
      containers:
      - name: app
        image: my-app:v1.0
        ports:
        - containerPort: 3000
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        env:
        - name: NODE_ENV
          value: "production"
        - name: DB_HOST
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: db-host
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: db-password
        livenessProbe:
          httpGet:
            path: /health
            port: 3000
          initialDelaySeconds: 15
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 3000
          initialDelaySeconds: 5
          periodSeconds: 5
```

#### Service（服务发现）

Service 为 Pod 提供稳定的访问入口。

```yaml
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: my-app-service
spec:
  selector:
    app: my-app
  ports:
  - port: 80        # Service 端口
    targetPort: 3000 # Pod 端口
    protocol: TCP
  type: ClusterIP  # 内部访问
---
# NodePort 类型（可从集群外部访问）
apiVersion: v1
kind: Service
metadata:
  name: my-app-nodeport
spec:
  selector:
    app: my-app
  ports:
  - port: 80
    targetPort: 3000
    nodePort: 30080  # 范围: 30000-32767
  type: NodePort
```

#### ConfigMap 和 Secret（配置管理）

```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  db-host: "postgres-service"
  db-port: "5432"
  cache-ttl: "3600"
  app.properties: |
    feature.flag.a=true
    feature.flag.b=false
---
# secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
type: Opaque
stringData:
  db-password: "your-secure-password"
  api-key: "your-api-key"
  tls.crt: |
    -----BEGIN CERTIFICATE-----
    ...
    -----END CERTIFICATE-----
```

#### Ingress（入站流量管理）

```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: my-app-ingress
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - api.example.com
    secretName: api-tls-secret
  rules:
  - host: api.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: my-app-service
            port:
              number: 80
```

### 3.2 本地开发环境搭建

#### 使用 Kind (Kubernetes in Docker)

```bash
# 安装 kind
curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind

# 创建集群
kind create cluster --name my-cluster

# 查看集群
kubectl cluster-info --context kind-my-cluster

# 加载本地镜像到集群（无需推送仓库）
kind load docker-image my-app:v1.0 --name my-cluster

# 删除集群
kind delete cluster --name my-cluster
```

#### 使用 Minikube

```bash
# 安装 minikube
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube

# 启动集群
minikube start --cpus=4 --memory=8192

# 启用插件
minikube addons enable ingress
minikube addons enable metrics-server
minikube addons enable dashboard

# 访问 Dashboard
minikube dashboard

# 停止/删除集群
minikube stop
minikube delete
```

### 3.3 部署应用实践

```bash
# 创建命名空间
kubectl create namespace myapp

# 应用配置
kubectl apply -f configmap.yaml -n myapp
kubectl apply -f secret.yaml -n myapp

# 部署应用
kubectl apply -f deployment.yaml -n myapp
kubectl apply -f service.yaml -n myapp
kubectl apply -f ingress.yaml -n myapp

# 查看部署状态
kubectl get all -n myapp

# 查看 Pod 详情
kubectl describe pod <pod-name> -n myapp

# 查看日志
kubectl logs -f deployment/my-app -n myapp

# 进入容器
kubectl exec -it <pod-name> -n myapp -- /bin/sh

# 端口转发（本地调试）
kubectl port-forward svc/my-app-service 8080:80 -n myapp
```

### 3.4 自动扩缩容（HPA）

```yaml
# hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: my-app-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: my-app
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

```bash
# 应用 HPA
kubectl apply -f hpa.yaml -n myapp

# 查看 HPA 状态
kubectl get hpa -n myapp
```

---

## 四、生产级最佳实践

### 4.1 镜像安全与优化

#### 安全检查清单

| 项目 | 要求 | 检查方法 |
|------|------|----------|
| 基础镜像 | 使用官方镜像，指定版本标签 | `docker images` 检查 |
| 镜像扫描 | 扫描漏洞 | `docker scout cves my-app:v1.0` |
| 非 root 运行 | 容器使用非特权用户 | Dockerfile 中设置 USER |
| 最小化镜像 | 仅包含必要组件 | 使用 alpine/distroless |
| 敏感信息 | 不在镜像中存储密钥 | 使用 Secret/ConfigMap |

#### 镜像优化技巧

```dockerfile
# 优化示例
# 1. 使用最小化基础镜像
FROM gcr.io/distroless/nodejs18-debian11

# 2. 多阶段构建
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build

# 3. 最终镜像仅包含必要文件
FROM gcr.io/distroless/nodejs18-debian11
COPY --from=builder /app/dist /app
COPY --from=builder /app/node_modules /app/node_modules
CMD ["server.js"]
```

### 4.2 资源限制与配额

```yaml
# namespace 资源配额
apiVersion: v1
kind: ResourceQuota
metadata:
  name: app-quota
  namespace: myapp
spec:
  hard:
    requests.cpu: "10"
    requests.memory: 20Gi
    limits.cpu: "20"
    limits.memory: 40Gi
    pods: "50"
    services: "10"
---
# Pod 的限制范围（LimitRange）
apiVersion: v1
kind: LimitRange
metadata:
  name: app-limits
  namespace: myapp
spec:
  limits:
  - type: Container
    default:
      cpu: "500m"
      memory: "512Mi"
    defaultRequest:
      cpu: "100m"
      memory: "128Mi"
    max:
      cpu: "2"
      memory: "2Gi"
    min:
      cpu: "50m"
      memory: "64Mi"
```

### 4.3 日志与监控

#### 日志架构

```
┌─────────┐     ┌──────────┐     ┌─────────────┐
│  Pods   │────▶│ Fluentd  │────▶│ Elasticsearch│
└─────────┘     │/Fluentbit│     └─────────────┘
                └──────────┘            │
                                        ▼
                                  ┌──────────┐
                                  │  Kibana  │
                                  └──────────┘
```

#### Prometheus + Grafana 监控

```yaml
# Prometheus ServiceMonitor 示例
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: my-app-monitor
  namespace: monitoring
spec:
  selector:
    matchLabels:
      app: my-app
  endpoints:
  - port: metrics
    interval: 30s
    path: /metrics
```

---

## 五、常见问题排查

### 5.1 镜像构建问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 构建超时 | 网络问题或镜像过大 | 使用国内镜像源，优化 Dockerfile |
| 依赖安装失败 | 网络或源不可用 | 更换 npm/pip 源，使用缓存 |
| 权限错误 | COPY 的文件权限问题 | 在 Dockerfile 中设置正确权限 |

```bash
# 调试构建过程
docker build --progress=plain --no-cache -t my-app:v1.0 .

# 查看镜像层
docker history my-app:v1.0
```

### 5.2 容器启动失败

```bash
# 查看 Pod 状态
kubectl get pods -n myapp
kubectl describe pod <pod-name> -n myapp

# 查看容器日志
kubectl logs <pod-name> -n myapp
kubectl logs <pod-name> -c <container-name> -n myapp  # 多容器场景

# 查看事件
kubectl get events -n myapp --sort-by='.lastTimestamp'
```

**常见状态说明**：

| 状态 | 说明 | 排查方向 |
|------|------|----------|
| `ImagePullBackOff` | 镜像拉取失败 | 检查镜像名、仓库认证、网络 |
| `CrashLoopBackOff` | 容器反复崩溃 | 查看日志，检查启动命令 |
| `Pending` | 无法调度 | 检查资源请求、节点状态 |
| `OOMKilled` | 内存超限 | 增加内存限制或优化代码 |

### 5.3 网络与存储问题

```bash
# 测试服务连通性
kubectl run test --image=busybox --rm -it --restart=Never -- nslookup my-app-service.myapp.svc.cluster.local

# 查看服务端点
kubectl get endpoints my-app-service -n myapp

# 查看 PVC 状态
kubectl get pvc -n myapp
kubectl describe pvc <pvc-name> -n myapp
```

---

## 六、总结

本文从容器化基础概念出发，系统讲解了 Docker 和 Kubernetes 的核心知识和实战技巧：

**核心要点回顾**：

1. **Docker** 解决应用打包和单机运行问题，核心概念是镜像、容器、仓库
2. **Kubernetes** 解决大规模容器编排问题，核心概念是 Pod、Deployment、Service
3. **生产实践** 关注镜像安全、资源限制、日志监控、自动扩缩容
4. **问题排查** 掌握 `kubectl describe`、`kubectl logs`、`docker logs` 等关键命令

**学习路径建议**：

```
Docker 基础 → Docker Compose → Kubernetes 核心概念 → 本地实践 → 生产部署
```

**下一步学习方向**：

- Helm 包管理
- GitOps（ArgoCD）
- 服务网格（Istio）
- 云原生安全

---

> 如果本文对你有帮助，欢迎点赞收藏！有问题欢迎在评论区讨论。