# phpMyAdmin 创建数据库和用户指南

## 登录 phpMyAdmin

1. 打开浏览器，访问 phpMyAdmin 地址
2. 使用以下凭据登录：
   - 用户名: `root`
   - 密码: `Visiray88!!`

## 创建数据库

1. 登录后，在左侧数据库列表上方点击"新建"
2. 在"数据库名"字段中输入: `bom_prod`
3. 选择字符集为: `utf8mb4`
4. 选择排序规则为: `utf8mb4_unicode_ci`
5. 点击"创建"

## 创建用户并授权

1. 点击顶部导航栏的"账户"或"用户账户"
2. 点击"添加用户账户"
3. 填写以下信息：
   - 用户名: `zhanchao_wang`
   - 主机: `%` (表示允许从任何主机连接)
   - 密码: `Visiray88`
   - 确认密码: `Visiray88`
4. 在"全局权限"部分，选择"全部权限"
5. 点击"执行"

## 验证创建结果

1. 在左侧数据库列表中确认 `bom_prod` 数据库已创建
2. 点击"账户"或"用户账户"，确认用户 `zhanchao_wang` 已创建
3. 刷新权限：
   - 点击"SQL"标签
   - 输入以下命令并执行：
     ```sql
     FLUSH PRIVILEGES;
     ```

## 使用 SQL 脚本创建（推荐）

您也可以直接执行 SQL 脚本来完成所有操作：

1. 点击顶部导航栏的"SQL"
2. 复制并粘贴以下 SQL 脚本：
   ```sql
   -- 创建数据库
   CREATE DATABASE IF NOT EXISTS bom_prod CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   
   -- 创建用户并授权
   CREATE USER IF NOT EXISTS 'zhanchao_wang'@'%' IDENTIFIED BY 'Visiray88';
   GRANT ALL PRIVILEGES ON bom_prod.* TO 'zhanchao_wang'@'%';
   
   -- 刷新权限
   FLUSH PRIVILEGES;
   
   -- 显示创建结果
   SHOW DATABASES LIKE 'bom_prod';
   SELECT User, Host FROM mysql.user WHERE User = 'zhanchao_wang';
   ```
3. 点击"执行"

完成以上步骤后，您就可以进行下一步的部署操作了。