# CI/CD 流水线搭建：从代码提交到自动部署

> 一篇涵盖 CI/CD 核心概念、主流工具选型和实战配置的完整指南，帮助你构建高效的自动化交付流程。

---

## 目录

- [一、CI/CD 概述](#一cicd-概述)
- [二、工具选型与架构设计](#二工具选型与架构设计)
- [三、GitLab CI/CD 实战](#三gitlab-cicd-实战)
- [四、Jenkins Pipeline 实战](#四jenkins-pipeline-实战)
- [五、GitHub Actions 实战](#五github-actions-实战)
- [六、高级实践](#六高级实践)
- [七、总结](#七总结)

---

## 一、CI/CD 概述

### 1.1 什么是 CI/CD

**CI（持续集成 - Continuous Integration）**：开发人员频繁地将代码合并到主干，每次合并都自动触发构建和测试。

**CD（持续交付/部署 - Continuous Delivery/Deployment）**：
- **持续交付**：代码经过测试后，可随时部署到生产环境（需手动触发）
- **持续部署**：代码通过测试后，自动部署到生产环境（全自动）

```
┌─────────────────────────────────────────────────────────────────┐
│                        CI/CD 流程图                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐ │
│  │ 代码提交  │───▶│ 自动构建  │───▶│ 自动测试  │───▶│ 代码检查  │ │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘ │
│       │                                                   │    │
│       │              CI（持续集成）                        │    │
│       └───────────────────────────────────────────────────┘    │
│                                                   │              │
│                                                   ▼              │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐ │
│  │ 部署测试  │───▶│ 部署预发  │───▶│ 部署生产  │───▶│ 监控告警  │ │
│  │ 环境     │    │ 环境     │    │ 环境     │    │          │ │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘ │
│       │              │                │                         │
│       │              CD（持续交付/部署）│                         │
│       └──────────────┴────────────────┘                         │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 CI/CD 的价值

| 维度 | 传统方式 | CI/CD 方式 |
|------|----------|------------|
| **发布频率** | 月度/季度 | 每天/每周多次 |
| **发布风险** | 大变更，高风险 | 小变更，低风险 |
| **问题定位** | 困难，排查时间长 | 快速定位，快速修复 |
| **团队效率** | 手动操作，等待时间长 | 自动化，即时反馈 |
| **回滚成本** | 高，需要手动恢复 | 低，一键回滚 |

### 1.3 CI/CD 核心要素

```
┌─────────────────────────────────────────────────────────────────┐
│                     CI/CD 核心要素                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  版本控制          构建系统          测试自动化                   │
│  ┌─────────┐      ┌─────────┐      ┌─────────┐                │
│  │ Git     │      │ Maven   │      │ JUnit   │                │
│  │ GitLab  │      │ Gradle  │      │ Jest    │                │
│  │ GitHub  │      │ npm     │      │ Pytest  │                │
│  └─────────┘      └─────────┘      └─────────┘                │
│                                                                 │
│  制品管理          环境管理          监控告警                     │
│  ┌─────────┐      ┌─────────┐      ┌─────────┐                │
│  │ Nexus   │      │ Docker  │      │ Grafana │                │
│  │ Harbor  │      │ K8s     │      │ PagerDuty│               │
│  │ ECR     │      │ Ansible │      │ 钉钉/企微│               │
│  └─────────┘      └─────────┘      └─────────┘                │
└─────────────────────────────────────────────────────────────────┘
```

---

## 二、工具选型与架构设计

### 2.1 主流 CI/CD 工具对比

| 工具 | 特点 | 适用场景 |
|------|------|----------|
| **GitLab CI/CD** | 内置于 GitLab，配置简单，Docker 原生支持 | 中小型团队，GitLab 用户 |
| **Jenkins** | 插件丰富，生态成熟，高度可定制 | 大型企业，复杂流水线 |
| **GitHub Actions** | 云原生，配置简单，市场丰富 | GitHub 用户，开源项目 |
| **ArgoCD** | GitOps 模式，K8s 原生 | 云原生项目，K8s 部署 |
| **Tekton** | 云原生，声明式配置 | K8s 环境，高度定制需求 |

### 2.2 架构设计原则

#### 分支策略

```
┌─────────────────────────────────────────────────────────────────┐
│                     Git Flow 分支策略                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  main (生产分支)                                                │
│    │                                                           │
│    │───── merge ─────▶ hotfix/xxx ────── merge ─────▶          │
│    │                         │                                 │
│    │                         │                                 │
│  release/x.x (发布分支)                                       │
│    │                         │                                 │
│    │◀──── merge ─────────────┘                                 │
│    │                                                           │
│  develop (开发分支)                                             │
│    │                                                           │
│    │◀──── merge ────────────────────────                       │
│    │                              │                            │
│    │──── merge ───▶ feature/xxx ───┘                           │
│    │                                                           │
│                                                                 │
│  简化版（推荐小型团队）：                                         │
│  main ──── feature/xxx ──── main ──── 部署                      │
│  （主干开发模式，通过 PR 触发 CI/CD）                             │
└─────────────────────────────────────────────────────────────────┘
```

#### 环境规划

| 环境 | 用途 | 部署时机 | 数据 |
|------|------|----------|------|
| **开发环境（DEV）** | 开发联调 | 每次提交 | 模拟数据 |
| **测试环境（TEST）** | QA 测试 | 合并到 develop | 测试数据 |
| **预发环境（STAGING）** | 上线前验证 | 合并到 release/main | 类生产数据 |
| **生产环境（PROD）** | 真实用户 | 打标签/合并到 main | 真实数据 |

---

## 三、GitLab CI/CD 实战

### 3.1 基础概念

GitLab CI/CD 使用 `.gitlab-ci.yml` 文件定义流水线，核心概念：

| 概念 | 说明 |
|------|------|
| **Pipeline** | 完整的 CI/CD 流程，包含多个 Stage |
| **Stage** | 阶段，如 build、test、deploy |
| **Job** | 具体任务，属于某个 Stage |
| **Runner** | 执行 Job 的代理程序 |

### 3.2 完整流水线配置

```yaml
# .gitlab-ci.yml

# 定义阶段
stages:
  - lint
  - build
  - test
  - security
  - deploy-dev
  - deploy-staging
  - deploy-prod

# 全局变量
variables:
  MAVEN_OPTS: "-Dmaven.repo.local=.m2/repository"
  DOCKER_REGISTRY: "registry.example.com"
  IMAGE_NAME: "${DOCKER_REGISTRY}/myapp"
  SONAR_HOST: "https://sonar.example.com"

# 缓存配置
cache:
  key: "${CI_JOB_NAME}"
  paths:
    - .m2/repository/
    - node_modules/

# ============ Lint 阶段 ============
lint:
  stage: lint
  image: node:18-alpine
  script:
    - npm ci
    - npm run lint
  only:
    - merge_requests
    - main
    - develop

# ============ Build 阶段 ============
build:
  stage: build
  image: maven:3.9-eclipse-temurin-17
  script:
    - mvn clean package -DskipTests
    - ls -la target/
  artifacts:
    paths:
      - target/*.jar
    expire_in: 1 hour
  only:
    - merge_requests
    - main
    - develop

# 构建Docker镜像
build-image:
  stage: build
  image: docker:24
  services:
    - docker:24-dind
  variables:
    DOCKER_TLS_CERTDIR: "/certs"
  before_script:
    - docker login -u "$CI_REGISTRY_USER" -p "$CI_REGISTRY_PASSWORD" $DOCKER_REGISTRY
  script:
    - docker build -t $IMAGE_NAME:$CI_COMMIT_SHORT_SHA .
    - docker push $IMAGE_NAME:$CI_COMMIT_SHORT_SHA
    # 如果是 main 分支，同时打 latest 标签
    - |
      if [ "$CI_COMMIT_BRANCH" == "main" ]; then
        docker tag $IMAGE_NAME:$CI_COMMIT_SHORT_SHA $IMAGE_NAME:latest
        docker push $IMAGE_NAME:latest
      fi
  only:
    - main
    - develop

# ============ Test 阶段 ============
unit-test:
  stage: test
  image: maven:3.9-eclipse-temurin-17
  script:
    - mvn test
  artifacts:
    reports:
      junit:
        - target/surefire-reports/TEST-*.xml
    coverage: '/Total.*?([0-9]{1,3})%/'
  only:
    - merge_requests
    - main
    - develop

integration-test:
  stage: test
  image: maven:3.9-eclipse-temurin-17
  services:
    - name: postgres:15-alpine
      alias: db
    - name: redis:7-alpine
      alias: redis
  variables:
    POSTGRES_DB: testdb
    POSTGRES_USER: test
    POSTGRES_PASSWORD: test
    SPRING_DATASOURCE_URL: jdbc:postgresql://db:5432/testdb
    SPRING_REDIS_HOST: redis
  script:
    - mvn verify -P integration-test
  artifacts:
    reports:
      junit:
        - target/failsafe-reports/TEST-*.xml
  only:
    - merge_requests
    - main

# ============ Security 阶段 ============
sonarqube-check:
  stage: security
  image: maven:3.9-eclipse-temurin-17
  variables:
    SONAR_USER_HOME: "${CI_PROJECT_DIR}/.sonar"
    GIT_DEPTH: "0"
  cache:
    key: "${CI_JOB_NAME}"
    paths:
      - .sonar/cache
  script:
    - mvn verify sonar:sonar -Dsonar.projectKey=myapp -Dsonar.host.url=$SONAR_HOST
  allow_failure: true
  only:
    - merge_requests
    - main

dependency-check:
  stage: security
  image: maven:3.9-eclipse-temurin-17
  script:
    - mvn org.owasp:dependency-check-maven:check
  artifacts:
    reports:
      dependency_scanning: target/dependency-check-report.json
  allow_failure: true
  only:
    - main
    - develop

# ============ Deploy 阶段 ============
deploy-dev:
  stage: deploy-dev
  image: bitnami/kubectl:latest
  variables:
    KUBE_NAMESPACE: dev
  script:
    - kubectl config use-context dev-cluster
    - kubectl set image deployment/myapp myapp=$IMAGE_NAME:$CI_COMMIT_SHORT_SHA -n $KUBE_NAMESPACE
    - kubectl rollout status deployment/myapp -n $KUBE_NAMESPACE --timeout=300s
  environment:
    name: development
    url: https://dev.example.com
  only:
    - develop

deploy-staging:
  stage: deploy-staging
  image: bitnami/kubectl:latest
  variables:
    KUBE_NAMESPACE: staging
  script:
    - kubectl config use-context staging-cluster
    - kubectl set image deployment/myapp myapp=$IMAGE_NAME:$CI_COMMIT_SHORT_SHA -n $KUBE_NAMESPACE
    - kubectl rollout status deployment/myapp -n $KUBE_NAMESPACE --timeout=300s
  environment:
    name: staging
    url: https://staging.example.com
  when: manual  # 手动触发
  only:
    - main

deploy-prod:
  stage: deploy-prod
  image: bitnami/kubectl:latest
  variables:
    KUBE_NAMESPACE: prod
  script:
    - kubectl config use-context prod-cluster
    # 先部署到金丝雀（10%流量）
    - kubectl patch deployment myapp-canary -n $KUBE_NAMESPACE -p '{"spec":{"template":{"spec":{"containers":[{"name":"myapp","image":"'$IMAGE_NAME:$CI_COMMIT_SHORT_SHA'"}]}}}}'
    - sleep 300  # 观察5分钟
    # 全量部署
    - kubectl set image deployment/myapp myapp=$IMAGE_NAME:$CI_COMMIT_SHORT_SHA -n $KUBE_NAMESPACE
    - kubectl rollout status deployment/myapp -n $KUBE_NAMESPACE --timeout=600s
  environment:
    name: production
    url: https://www.example.com
  when: manual
  only:
    - main
  except:
    - merge_requests
```

### 3.3 Runner 配置

```bash
# 安装 GitLab Runner (Linux)
curl -L https://packages.gitlab.com/install/repositories/runner/gitlab-runner/script.rpm.sh | sudo bash
sudo yum install gitlab-runner

# 注册 Runner
sudo gitlab-runner register
# 输入 GitLab URL: https://gitlab.example.com
# 输入注册 Token:（从 GitLab 项目设置获取）
# 输入描述: my-runner
# 输入标签: docker,linux
# 选择执行器: docker
# 默认镜像: alpine:latest

# 启动 Runner
sudo gitlab-runner start

# 查看状态
sudo gitlab-runner status
```

---

## 四、Jenkins Pipeline 实战

### 4.1 Jenkins 架构

```
┌─────────────────────────────────────────────────────────────────┐
│                      Jenkins 架构示意                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│                    ┌─────────────────┐                          │
│                    │  Jenkins Master │                          │
│                    │   - 调度任务      │                          │
│                    │   - 分发构建      │                          │
│                    │   - Web UI       │                          │
│                    └────────┬────────┘                          │
│                             │                                   │
│              ┌──────────────┼──────────────┐                    │
│              │              │              │                    │
│              ▼              ▼              ▼                    │
│        ┌──────────┐  ┌──────────┐  ┌──────────┐                │
│        │ Agent 1  │  │ Agent 2  │  │ Agent 3  │                │
│        │ (Docker) │  │ (K8s)    │  │ (Linux)  │                │
│        └──────────┘  └──────────┘  └──────────┘                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Declarative Pipeline 完整示例

```groovy
// Jenkinsfile

pipeline {
    agent {
        kubernetes {
            yaml '''
apiVersion: v1
kind: Pod
metadata:
  labels:
    pipeline: ci-cd
spec:
  containers:
  - name: maven
    image: maven:3.9-eclipse-temurin-17
    command:
    - cat
    tty: true
    volumeMounts:
    - name: maven-cache
      mountPath: /root/.m2/repository
  - name: docker
    image: docker:24
    command:
    - cat
    tty: true
    volumeMounts:
    - name: docker-sock
      mountPath: /var/run/docker.sock
  - name: kubectl
    image: bitnami/kubectl:latest
    command:
    - cat
    tty: true
  volumes:
  - name: maven-cache
    persistentVolumeClaim:
      claimName: maven-cache-pvc
  - name: docker-sock
    hostPath:
      path: /var/run/docker.sock
'''
        }
    }

    environment {
        DOCKER_REGISTRY = 'registry.example.com'
        IMAGE_NAME = "${DOCKER_REGISTRY}/myapp"
        SONAR_HOST = 'https://sonar.example.com'
    }

    options {
        timeout(time: 30, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '20'))
        disableConcurrentBuilds()
        timestamps()
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                script {
                    env.GIT_COMMIT_SHORT = sh(
                        script: 'git rev-parse --short HEAD',
                        returnStdout: true
                    ).trim()
                }
                echo "Building commit: ${env.GIT_COMMIT_SHORT}"
            }
        }

        stage('Lint') {
            steps {
                container('maven') {
                    sh 'mvn checkstyle:check'
                }
            }
        }

        stage('Build') {
            steps {
                container('maven') {
                    sh 'mvn clean package -DskipTests'
                }
                archiveArtifacts artifacts: 'target/*.jar', fingerprint: true
            }
        }

        stage('Test') {
            parallel {
                stage('Unit Tests') {
                    steps {
                        container('maven') {
                            sh 'mvn test'
                        }
                    }
                    post {
                        always {
                            junit 'target/surefire-reports/**/*.xml'
                        }
                    }
                }
                stage('Integration Tests') {
                    steps {
                        container('maven') {
                            sh 'mvn verify -P integration-test'
                        }
                    }
                    post {
                        always {
                            junit 'target/failsafe-reports/**/*.xml'
                        }
                    }
                }
            }
        }

        stage('SonarQube Analysis') {
            steps {
                container('maven') {
                    withCredentials([string(credentialsId: 'sonar-token', variable: 'SONAR_TOKEN')]) {
                        sh """
                            mvn sonar:sonar \\
                                -Dsonar.host.url=${SONAR_HOST} \\
                                -Dsonar.login=${SONAR_TOKEN} \\
                                -Dsonar.projectKey=myapp
                        """
                    }
                }
            }
        }

        stage('Security Scan') {
            steps {
                container('maven') {
                    sh 'mvn org.owasp:dependency-check-maven:check'
                }
            }
            post {
                always {
                    publishHTML([
                        allowMissing: true,
                        alwaysLinkToLastBuild: true,
                        keepAll: true,
                        reportDir: 'target',
                        reportFiles: 'dependency-check-report.html',
                        reportName: 'Dependency Check'
                    ])
                }
            }
        }

        stage('Build & Push Image') {
            when {
                anyOf {
                    branch 'main'
                    branch 'develop'
                }
            }
            steps {
                container('docker') {
                    withCredentials([usernamePassword(
                        credentialsId: 'docker-registry',
                        usernameVariable: 'REGISTRY_USER',
                        passwordVariable: 'REGISTRY_PASS'
                    )]) {
                        sh """
                            docker login -u ${REGISTRY_USER} -p ${REGISTRY_PASS} ${DOCKER_REGISTRY}
                            docker build -t ${IMAGE_NAME}:${env.GIT_COMMIT_SHORT} .
                            docker push ${IMAGE_NAME}:${env.GIT_COMMIT_SHORT}
                        """
                    }
                }
            }
        }

        stage('Deploy to Dev') {
            when {
                branch 'develop'
            }
            steps {
                container('kubectl') {
                    sh """
                        kubectl config use-context dev-cluster
                        kubectl set image deployment/myapp myapp=${IMAGE_NAME}:${env.GIT_COMMIT_SHORT} -n dev
                        kubectl rollout status deployment/myapp -n dev --timeout=300s
                    """
                }
            }
        }

        stage('Deploy to Staging') {
            when {
                branch 'main'
            }
            steps {
                input message: 'Deploy to Staging?', ok: 'Deploy'
                container('kubectl') {
                    sh """
                        kubectl config use-context staging-cluster
                        kubectl set image deployment/myapp myapp=${IMAGE_NAME}:${env.GIT_COMMIT_SHORT} -n staging
                        kubectl rollout status deployment/myapp -n staging --timeout=300s
                    """
                }
            }
        }

        stage('Deploy to Production') {
            when {
                branch 'main'
            }
            steps {
                input message: 'Deploy to Production?', ok: 'Deploy'
                container('kubectl') {
                    sh """
                        kubectl config use-context prod-cluster
                        kubectl set image deployment/myapp myapp=${IMAGE_NAME}:${env.GIT_COMMIT_SHORT} -n prod
                        kubectl rollout status deployment/myapp -n prod --timeout=600s
                    """
                }
            }
        }
    }

    post {
        success {
            echo 'Pipeline succeeded!'
        }
        failure {
            echo 'Pipeline failed!'
        }
        always {
            cleanWs()
        }
    }
}
```

### 4.3 常用 Jenkins 插件

| 插件 | 用途 |
|------|------|
| **Git** | Git 仓库集成 |
| **Pipeline** | 声明式流水线支持 |
| **Docker Pipeline** | Docker 操作支持 |
| **Kubernetes** | K8s 动态 Agent |
| **SonarQube Scanner** | 代码质量扫描 |
| **Credentials Binding** | 安全凭证管理 |
| **Blue Ocean** | 现代化 UI |
| **Build Timestamp** | 构建时间戳 |

---

## 五、GitHub Actions 实战

### 5.1 基础概念

GitHub Actions 使用 YAML 文件定义工作流，存放在 `.github/workflows/` 目录。

| 概念 | 说明 |
|------|------|
| **Workflow** | 工作流，一个 YAML 文件 |
| **Event** | 触发事件，如 push、pull_request |
| **Job** | 任务，包含多个 Step |
| **Step** | 步骤，执行具体操作 |
| **Action** | 可复用的操作单元 |
| **Runner** | 执行任务的虚拟机 |

### 5.2 完整工作流配置

```yaml
# .github/workflows/ci-cd.yml

name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]
  release:
    types: [ published ]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}
  JAVA_VERSION: '17'
  NODE_VERSION: '18'

jobs:
  # ============ Lint Job ============
  lint:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: Install dependencies
        run: cd frontend && npm ci

      - name: Run ESLint
        run: cd frontend && npm run lint

      - name: Run Prettier
        run: cd frontend && npm run format:check

  # ============ Build & Test Job ============
  build-test:
    runs-on: ubuntu-latest
    needs: lint
    
    services:
      postgres:
        image: postgres:15-alpine
        env:
          POSTGRES_DB: testdb
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Setup JDK
        uses: actions/setup-java@v4
        with:
          java-version: ${{ env.JAVA_VERSION }}
          distribution: 'temurin'
          cache: maven

      - name: Cache Maven packages
        uses: actions/cache@v4
        with:
          path: ~/.m2/repository
          key: ${{ runner.os }}-maven-${{ hashFiles('**/pom.xml') }}
          restore-keys: |
            ${{ runner.os }}-maven-

      - name: Build with Maven
        run: mvn clean package -DskipTests

      - name: Run unit tests
        run: mvn test

      - name: Run integration tests
        run: mvn verify -P integration-test
        env:
          SPRING_DATASOURCE_URL: jdbc:postgresql://localhost:5432/testdb
          SPRING_DATASOURCE_USERNAME: test
          SPRING_DATASOURCE_PASSWORD: test
          SPRING_REDIS_HOST: localhost

      - name: Upload test reports
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: test-reports
          path: |
            target/surefire-reports/
            target/failsafe-reports/

      - name: SonarQube Scan
        uses: sonarsource/sonarqube-scan-action@master
        env:
          SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
          SONAR_HOST: ${{ secrets.SONAR_HOST }}

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v4
        with:
          files: ./target/jacoco/jacoco.xml
          fail_ci_if_error: false

  # ============ Security Scan Job ============
  security:
    runs-on: ubuntu-latest
    needs: build-test
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          severity: 'CRITICAL,HIGH'
          format: 'sarif'
          output: 'trivy-results.sarif'

      - name: Upload Trivy results to GitHub Security
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: 'trivy-results.sarif'

  # ============ Build Docker Image Job ============
  build-image:
    runs-on: ubuntu-latest
    needs: [build-test, security]
    if: github.event_name == 'push' || github.event_name == 'release'
    permissions:
      contents: read
      packages: write

    outputs:
      image-tag: ${{ steps.meta.outputs.tags }}

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata for Docker
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=sha,prefix=
            type=ref,event=branch
            type=ref,event=pr
            type=semver,pattern={{version}}
            type=raw,value=latest,enable=${{ github.ref == 'refs/heads/main' }}

      - name: Build and push Docker image
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
          platforms: linux/amd64,linux/arm64

  # ============ Deploy to Dev Job ============
  deploy-dev:
    runs-on: ubuntu-latest
    needs: build-image
    if: github.ref == 'refs/heads/develop'
    environment:
      name: development
      url: https://dev.example.com

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up kubectl
        uses: azure/setup-kubectl@v3

      - name: Configure kubeconfig
        run: |
          mkdir -p ~/.kube
          echo "${{ secrets.KUBE_CONFIG_DEV }}" | base64 -d > ~/.kube/config

      - name: Deploy to Dev
        run: |
          kubectl set image deployment/myapp \\
            myapp=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }} \\
            -n dev
          kubectl rollout status deployment/myapp -n dev --timeout=300s

      - name: Wait for deployment
        run: |
          kubectl wait --for=condition=available --timeout=300s deployment/myapp -n dev

      - name: Run smoke tests
        run: |
          curl -f https://dev.example.com/health || exit 1

  # ============ Deploy to Staging Job ============
  deploy-staging:
    runs-on: ubuntu-latest
    needs: build-image
    if: github.ref == 'refs/heads/main'
    environment:
      name: staging
      url: https://staging.example.com

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up kubectl
        uses: azure/setup-kubectl@v3

      - name: Configure kubeconfig
        run: |
          mkdir -p ~/.kube
          echo "${{ secrets.KUBE_CONFIG_STAGING }}" | base64 -d > ~/.kube/config

      - name: Deploy to Staging
        run: |
          kubectl set image deployment/myapp \\
            myapp=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }} \\
            -n staging
          kubectl rollout status deployment/myapp -n staging --timeout=300s

      - name: Run E2E tests
        run: |
          npm ci
          npm run test:e2e -- --env staging
        env:
          TEST_URL: https://staging.example.com

  # ============ Deploy to Production Job ============
  deploy-prod:
    runs-on: ubuntu-latest
    needs: [build-image, deploy-staging]
    if: github.event_name == 'release'
    environment:
      name: production
      url: https://www.example.com

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up kubectl
        uses: azure/setup-kubectl@v3

      - name: Configure kubeconfig
        run: |
          mkdir -p ~/.kube
          echo "${{ secrets.KUBE_CONFIG_PROD }}" | base64 -d > ~/.kube/config

      - name: Blue-Green Deployment
        run: |
          # 部署到 Green 环境
          kubectl set image deployment/myapp-green \\
            myapp=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }} \\
            -n prod
          kubectl rollout status deployment/myapp-green -n prod --timeout=600s
          
          # 等待 Green 就绪
          kubectl wait --for=condition=available --timeout=300s deployment/myapp-green -n prod
          
          # 切换流量到 Green
          kubectl patch service myapp -n prod -p '{"spec":{"selector":{"version":"green"}}}'
          
          # 观察一段时间后，删除 Blue
          sleep 300
          kubectl scale deployment myapp-blue -n prod --replicas=0

      - name: Notify deployment
        uses: 8398a7/action-slack@v3
        with:
          status: success
          text: |
            Production deployed!
            Version: ${{ github.event.release.tag_name }}
            Commit: ${{ github.sha }}
          webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

---

## 六、高级实践

### 6.1 多环境配置管理

```yaml
# GitLab CI/CD 多环境配置示例

# 配置文件管理
.deploy-template:
  script:
    - kubectl config use-context $KUBE_CONTEXT
    - |
      cat <<EOF | kubectl apply -f -
      apiVersion: v1
      kind: ConfigMap
      metadata:
        name: app-config
        namespace: $KUBE_NAMESPACE
      data:
        DATABASE_URL: $DATABASE_URL
        REDIS_URL: $REDIS_URL
        API_KEY: $API_KEY
      EOF
    - kubectl set image deployment/myapp myapp=$IMAGE:$TAG -n $KUBE_NAMESPACE
    - kubectl rollout status deployment/myapp -n $KUBE_NAMESPACE

deploy-dev:
  extends: .deploy-template
  stage: deploy-dev
  variables:
    KUBE_CONTEXT: dev-cluster
    KUBE_NAMESPACE: dev
    DATABASE_URL: jdbc:postgresql://dev-db:5432/myapp
    REDIS_URL: redis://dev-redis:6379
  environment:
    name: development

deploy-staging:
  extends: .deploy-template
  stage: deploy-staging
  variables:
    KUBE_CONTEXT: staging-cluster
    KUBE_NAMESPACE: staging
  environment:
    name: staging
  when: manual
```

### 6.2 GitOps 实践（ArgoCD）

```yaml
# ArgoCD Application 配置示例
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: myapp
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://gitlab.example.com/myapp/k8s-manifests.git
    targetRevision: HEAD
    path: overlays/production
  destination:
    server: https://kubernetes.default.svc
    namespace: production
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
```

### 6.3 通知与告警

```yaml
# GitLab CI/CD 通知配置
deploy-prod:
  stage: deploy-prod
  script:
    - kubectl apply -f k8s/production/
  after_script:
    - |
      if [ $CI_JOB_STATUS == "success" ]; then
        curl -X POST "${SLACK_WEBHOOK}" \\
          -H 'Content-Type: application/json' \\
          -d '{
            "text": "✅ 部署成功",
            "attachments": [{
              "color": "good",
              "fields": [
                {"title": "项目", "value": "'${CI_PROJECT_NAME}'", "short": true},
                {"title": "分支", "value": "'${CI_COMMIT_REF_NAME}'", "short": true},
                {"title": "提交", "value": "'${CI_COMMIT_SHORT_SHA}'", "short": true}
              ]
            }]
          }'
      else
        curl -X POST "${SLACK_WEBHOOK}" \
          -H 'Content-Type: application/json' \
          -d '{
            "text": "❌ 部署失败",
            "attachments": [{
              "color": "danger",
              "fields": [
                {"title": "项目", "value": "'${CI_PROJECT_NAME}'", "short": true},
                {"title": "分支", "value": "'${CI_COMMIT_REF_NAME}'", "short": true},
                {"title": "提交", "value": "'${CI_COMMIT_SHORT_SHA}'", "short": true}
              ]
            }]
          }'
      fi
```

---

## 七、总结

本文系统介绍了 CI/CD 流水线的核心概念和实践方法：

**核心要点回顾**：

1. **CI/CD 概念**：持续集成确保代码质量，持续交付/部署实现自动化发布
2. **工具选型**：GitLab CI/CD 适合 GitLab 用户，Jenkins 适合复杂场景，GitHub Actions 适合开源项目
3. **流水线设计**：按阶段组织（lint → build → test → security → deploy），环境分离（dev → staging → prod）
4. **高级实践**：多环境配置、GitOps、通知告警、蓝绿部署

**最佳实践清单**：

- [ ] 代码提交自动触发构建和测试
- [ ] 代码质量检查（SonarQube、ESLint）
- [ ] 安全扫描（依赖漏洞、SAST）
- [ ] 单元测试 + 集成测试覆盖率报告
- [ ] 镜像构建与推送（多平台支持）
- [ ] 环境隔离与配置管理
- [ ] 生产部署需要人工审批
- [ ] 部署失败自动回滚
- [ ] 完整的通知和告警机制

> CI/CD 是 DevOps 的核心实践，能够显著提升交付效率和质量。从简单的流水线开始，逐步完善和优化。
>
> 如果这篇文章对你有帮助，欢迎点赞收藏！有问题欢迎评论区讨论。</tool_call>}