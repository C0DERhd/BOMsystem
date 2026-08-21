# BOM管理系统部署指南

## 环境要求

### 开发环境
- Python 3.8+
- Node.js 16+
- MySQL 8.0+
- Redis (可选)

### 生产环境
- Docker & Docker Compose
- 或者 Linux服务器 + Nginx

## 快速开始

### 1. 本地开发部署

#### Windows系统
```bash
# 双击运行启动脚本
start.bat
```

#### Linux/MacOS系统
```bash
# 执行启动脚本
chmod +x start.sh
./start.sh
```

### 2. Docker部署

```bash
# 克隆代码
git clone <repository>
cd BOMsystem

# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 3. 简化部署（推荐）

我们提供了一个简化版的部署配置文件 `simple-deploy.yml`，它包含了完整的环境（MySQL、Redis、后端、前端），
适合快速部署和测试：

```bash
# 使用简化配置启动
docker-compose -f simple-deploy.yml up -d
```

这将启动一个包含MySQL数据库、Redis缓存、后端API和前端界面的完整环境。

### 3. 手动部署

#### 后端部署

```bash
# 进入后端目录
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/MacOS
# 或
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件配置数据库连接等

# 初始化数据库
python init_db.py

# 启动后端服务
python run.py
```

#### 前端部署

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 开发模式启动
npm start

# 或者构建生产版本
npm run build
# 将build目录部署到Web服务器
```

## 配置说明

### 后端配置 (backend/.env)

```bash
# Flask配置
FLASK_CONFIG=production
FLASK_DEBUG=False

# 数据库配置
DATABASE_URL=mysql+pymysql://username:password@localhost/bom_prod
VISIRAY_DATABASE_URL=mysql+pymysql://username:password@localhost/visiray

# Redis配置 (可选)
REDIS_URL=redis://localhost:6379/0

# 安全密钥 (生产环境必须修改)
SECRET_KEY=your-secret-key-change-in-production
JWT_SECRET_KEY=jwt-secret-string-change-in-production

# SSO配置 (可选)
SSO_ENABLED=false
OAUTH_CLIENT_ID=your-oauth-client-id
OAUTH_CLIENT_SECRET=your-oauth-client-secret
```

### 前端配置

在前端构建时，可以通过环境变量配置API地址：

```bash
# 生产环境API地址
REACT_APP_API_BASE_URL=https://api.yourdomain.com/api
```

## Nginx配置示例

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    
    # 前端静态文件
    location / {
        root /path/to/frontend/build;
        index index.html;
        try_files $uri $uri/ /index.html;
    }
    
    # API代理
    location /api {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

## 数据库备份

```bash
# 备份数据库
mysqldump -u username -p bom_prod > backup.sql

# 恢复数据库
mysql -u username -p bom_prod < backup.sql
```

## 系统监控

### 日志位置
- 后端日志: `backend/logs/`
- 前端日志: 浏览器控制台
- Nginx日志: `/var/log/nginx/`

### 健康检查
- 后端健康检查: `GET /api/health`
- 前端访问: `http://localhost:3000`

## 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查数据库服务是否启动
   - 验证数据库连接字符串
   - 确认用户权限

2. **前端无法连接后端**
   - 检查后端服务是否运行在5000端口
   - 验证前端代理配置
   - 检查防火墙设置

3. **权限错误**
   - 确认用户角色和权限配置
   - 检查JWT token是否有效

### 日志查看

```bash
# 查看后端日志
tail -f backend/logs/bom_system.log

# 查看Docker日志
docker-compose logs -f backend
docker-compose logs -f frontend
```

## 性能优化

### 数据库优化
- 创建适当的索引
- 定期清理日志表
- 配置数据库连接池

### 前端优化
- 启用Gzip压缩
- 配置CDN
- 使用生产构建

### 缓存配置
- 启用Redis缓存
- 配置浏览器缓存
- 使用HTTP缓存头

## 安全建议

1. **修改默认密码**: 更改默认管理员密码
2. **HTTPS配置**: 生产环境使用HTTPS
3. **防火墙设置**: 限制数据库端口访问
4. **定期备份**: 设置自动数据库备份
5. **更新依赖**: 定期更新系统依赖包

## 技术支持

如有问题，请查看：
- 系统日志文件
- GitHub Issues
- 项目文档

默认管理员账号: `admin` / `admin123`