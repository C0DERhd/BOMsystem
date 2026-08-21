# Docker 网络连接问题解决方案

当在部署时遇到 "Get https://registry-1.docker.io/v2/: proxyconnect tcp: dial tcp: lookup registry-1.docker.io" 错误时，可以采用以下几种解决方案：

## 解决方案 1: 配置 Docker daemon 使用镜像加速器（推荐）

### 方法 A: 使用国内镜像源

1. 在群晖 NAS 上打开 Docker 套件
2. 进入"设置" -> "注册表"
3. 添加以下镜像加速器：
   - https://docker.mirrors.ustc.edu.cn
   - https://hub-mirror.c.163.com
   - https://mirror.baidubce.com

### 方法 B: 使用阿里云镜像加速器

1. 访问阿里云容器镜像服务控制台
2. 获取专属加速器地址
3. 在群晖 Docker 设置中配置该地址

## 解决方案 2: 手动拉取镜像

在群晖终端中手动拉取所需的镜像：

```bash
# 拉取后端镜像
docker pull python:3.10-slim

# 拉取前端镜像
docker pull node:18-alpine

# 拉取 Redis 镜像
docker pull redis:7-alpine
```

如果仍然超时，可以尝试使用国内镜像：

```bash
# 使用阿里云镜像
docker pull registry.cn-hangzhou.aliyuncs.com/zhuyali/python:3.10-slim
docker tag registry.cn-hangzhou.aliyuncs.com/zhuyali/python:3.10-slim python:3.10-slim
```

## 解决方案 3: 修改 synology-deploy.yml 文件

我们已经在 [synology-deploy.yml](synology-deploy.yml) 中做了以下优化：

1. 为 pip 配置了国内镜像源：
   ```bash
   pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
   ```

2. 为 npm 配置了国内镜像源：
   ```bash
   npm config set registry https://registry.npmmirror.com
   ```

3. 使用了轻量级的基础镜像以减少下载时间：
   - `python:3.10-slim`
   - `node:18-alpine`
   - `redis:7-alpine`

## 解决方案 4: 网络连接优化

1. 确保群晖 NAS 有稳定的网络连接
2. 检查防火墙设置，确保没有阻止 Docker 的网络访问
3. 如果使用代理，需要在 Docker 设置中配置代理

## 解决方案 5: 重试策略

如果以上方法都不行，可以尝试：

1. 等待一段时间后重试（可能是网络临时问题）
2. 重启 Docker 服务
3. 重启群晖 NAS

## 部署建议

为了提高部署成功率，建议：

1. 在非高峰时段进行部署
2. 确保网络连接稳定
3. 预先拉取所需镜像
4. 使用国内镜像源加速下载

## 镜像列表

本项目需要以下镜像：
- python:3.10-slim（后端）
- node:18-alpine（前端）
- redis:7-alpine（缓存）

这些镜像都比较轻量，应该能较快完成下载。