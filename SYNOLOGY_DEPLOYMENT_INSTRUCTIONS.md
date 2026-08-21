# 群晖 NAS Container Manager 部署说明

## 部署前准备

1. 确保已在 phpMyAdmin 中创建了数据库和用户：
   - 数据库: `bom_prod`
   - 用户名: `zhanchao_wang`
   - 密码: `Visiray88`

2. 确保 Windows 系统上的 MySQL 服务正在运行
   - 用户名: `root`
   - 密码: `Visiray88!!`
   - 地址: `localhost:3306`

## 部署步骤

1. 将整个项目文件夹上传到群晖 NAS

2. 打开 Container Manager，选择"项目" -> "新建"

3. 选择包含 `synology-deploy.yml` 文件的目录

4. 项目名称设置为 "bom-system"

5. 点击"运行"启动容器

6. 等待容器启动完成后，初始化数据库：
   - 进入 `bom_backend` 容器终端
   - 执行以下命令：
     ```bash
     cd /app
     export FLASK_APP=run.py
     flask init-db
     flask create-admin
     ```

7. 访问系统：
   - 前端: `http://your-nas-ip`
   - 默认账户: admin / admin123

## 配置说明

- Redis 端口映射为 6380:6379，避免端口冲突
- 后端服务运行在 5000 端口
- 前端服务运行在 80 端口
- 数据持久化路径:
  - Redis 数据: /docker/redis/data
  - 上传文件: /docker/backend/uploads