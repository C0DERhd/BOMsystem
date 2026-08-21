# BOM管理Web系统

一个基于Python Flask和React的企业级BOM（物料清单）管理系统。

## 功能特性

- 🏗️ **多层级BOM管理**: 支持复杂的产品结构树形管理
- 🔢 **12位智能编码**: 标准化物料编码自动生成和验证
- 👥 **双重认证支持**: 本地账户和SSO单点登录
- 📊 **成本分析**: 基于BOM的成本计算和分析
- 📦 **库存管控**: 物料库存状态实时监控
- 🏢 **供应商管理**: 供应商信息和报价管理
- 🔐 **权限管理**: 基于角色的访问控制

## 技术栈

### 后端
- Python Flask
- SQLAlchemy ORM
- Flask-JWT-Extended
- Flask-Login
- MySQL 8.0
- Redis

### 前端
- React 18
- TypeScript
- Ant Design
- Redux Toolkit
- React Router

## 12位物料编码规则

| 位数范围 | 含义 | 编码范围 | 说明 |
|---------|------|----------|------|
| 1~2位 | 零部件大类 | 01~04 | 01=定制件，02=外购件 |
| 3位 | 定制/外购标识 | 0~9 | 0=定制件，5=外购件 |
| 4~5位 | 部件类别 | 20~39 | 机械件编码 |
| 6~7位 | 分类号 | 00~99 | 材料、传动、紧固件等分类 |
| 8~11位 | 零件顺序号 | 0000~9999 | 唯一流水号 |
| 12位 | 版本号 | 0~9 | 版本迭代 |

### 编码示例
- 定制机械件: `010200050123`**0**
- 外购机械件: `025203504560`**0**

## 快速开始

### 一键启动（推荐）

**Windows:**
```bash
# 双击运行或命令行执行
start.bat
```

**Linux/MacOS:**
```bash
chmod +x start.sh
./start.sh
```

### Docker部署
```bash
docker-compose up -d
```

### 简化部署（推荐）

我们提供了一个简化版的部署配置文件 [simple-deploy.yml](simple-deploy.yml)，它包含了完整的环境（MySQL、Redis、后端、前端），
适合快速部署和测试：

```bash
docker-compose -f simple-deploy.yml up -d
```

这将启动一个包含MySQL数据库、Redis缓存、后端API和前端界面的完整环境。

### 群晖 NAS 部署

1. 在 phpMyAdmin 中执行以下 SQL 创建数据库和用户：
   ```sql
   -- 创建数据库
   CREATE DATABASE IF NOT EXISTS bom_prod CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   
   -- 创建用户并授权
   CREATE USER IF NOT EXISTS 'zhanchao_wang'@'%' IDENTIFIED BY 'Visiray88!!';
   GRANT ALL PRIVILEGES ON bom_prod.* TO 'zhanchao_wang'@'%';
   
   -- 刷新权限
   FLUSH PRIVILEGES;
   ```

2. 确保 Windows 系统上的 MySQL 服务正在运行
   - 用户名: `root`
   - 密码: `Visiray88!!`
   - 地址: `localhost:3306`

3. 将整个项目文件夹上传到群晖 NAS

4. 打开 Container Manager，选择"项目" -> "新建"

5. 选择包含 `synology-deploy.yml` 文件的目录

6. 项目名称设置为 "bom-system"

7. 点击"运行"启动容器

8. 等待容器启动完成后，初始化数据库：
   - 进入 `bom_backend` 容器终端
   - 执行以下命令：
     ```bash
     cd /app
     export FLASK_APP=run.py
     flask init-db
     flask create-admin
     ```

9. 访问系统：
   - 前端: `http://your-nas-ip`
   - 默认账户: admin / admin123

如果遇到 Docker 网络连接问题，请参考 [DOCKER_NETWORK_SOLUTION.md](DOCKER_NETWORK_SOLUTION.md) 文件。

### 手动启动

**后端启动:**
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/MacOS
pip install -r requirements.txt
cp .env.example .env  # 配置数据库连接
python init_db.py     # 初始化数据库
python run.py
```

**前端启动:**
```bash
cd frontend
npm install
npm start
```

**访问系统:**
- 前端地址: http://localhost:3000
- 后端API: http://localhost:5000
- 默认账号: admin / admin123

## 项目结构

```
BOMsystem/
├── backend/                # Flask后端
│   ├── app/                # Flask应用
│   │   ├── models/         # 数据模型
│   │   ├── auth/           # 认证模块
│   │   ├── api/            # API端点
│   │   ├── services/       # 业务服务层
│   │   └── utils/          # 工具类
│   ├── migrations/         # 数据库迁移
│   ├── tests/              # 测试文件
│   ├── requirements.txt    # Python依赖
│   ├── run.py              # 应用启动文件
│   ├── init_db.py          # 数据库初始化
│   └── config.py           # 配置文件
├── frontend/               # React前端
│   ├── src/                # 源代码
│   │   ├── components/     # React组件
│   │   ├── pages/          # 页面组件
│   │   ├── store/          # Redux状态管理
│   │   ├── services/       # API服务
│   │   ├── types/          # TypeScript类型
│   │   └── utils/          # 工具函数
│   ├── public/             # 静态资源
│   └── package.json        # Node.js依赖
├── docs/                   # 项目文档
├── start.bat               # Windows启动脚本
├── start.sh                # Linux/MacOS启动脚本
├── docker-compose.yml      # Docker编排
└── README.md               # 项目说明
```

## 主要功能模块

### 🔢 12位智能编码系统
- 自动生成和验证物料编码
- 支持定制件/外购件分类
- 多层级编码结构设计
- 版本号管理和迭代

### 🏢 BOM管理
- 多层级BOM树形结构管理
- BOM版本控制和对比
- 成本自动计算和分析
- BOM导入导出功能

### 📦 物料主数据管理
- 物料基础信息管理
- 物料分类和属性管理
- 库存状态实时监控
- 替代物料管理

### 🏦 供应商管理
- 供应商基础信息管理
- 价格和报价管理
- 供应商评估和等级管理
- 采购周期和交期管理

### 🔐 权限管理系统
- 基于角色的访问控制(RBAC)
- 细粒度权限控制
- SSO单点登录支持
- 用户和角色管理

### 📈 报表和分析
- BOM成本分析报表
- 物料使用情况统计
- 供应商绩效评估
- 库存状态分析

## 系统特色

✅ **企业级架构**: 基于MVC模式，支持高并发访问  
✅ **响应式设计**: 适配桌面和移动端设备  
✅ **多语言支持**: 中英文界面切换  
✅ **数据安全**: 支持HTTPS、数据加密和备份  
✅ **扩展性**: 模块化设计，支持功能扩展  
✅ **部署灵活**: 支持Docker、云部署和群晖NAS等多种方式