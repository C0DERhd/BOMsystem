-- 创建数据库
CREATE DATABASE IF NOT EXISTS bom_prod CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS visiray CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 创建用户并授权 (使用符合密码策略的密码)
CREATE USER IF NOT EXISTS 'zhanchao_wang'@'%' IDENTIFIED BY 'Visiray88!!';
GRANT ALL PRIVILEGES ON bom_prod.* TO 'zhanchao_wang'@'%';
GRANT ALL PRIVILEGES ON visiray.* TO 'zhanchao_wang'@'%';

-- 创建管理员用户
CREATE USER IF NOT EXISTS 'admin'@'%' IDENTIFIED BY 'Visiray88!!';
GRANT ALL PRIVILEGES ON bom_prod.* TO 'admin'@'%';
GRANT ALL PRIVILEGES ON visiray.* TO 'admin'@'%';

-- 刷新权限
FLUSH PRIVILEGES;

-- 使用数据库
USE bom_prod;

-- 显示创建结果
SHOW DATABASES LIKE 'bom_prod';
SHOW DATABASES LIKE 'visiray';
SELECT User, Host FROM mysql.user WHERE User IN ('zhanchao_wang', 'admin');