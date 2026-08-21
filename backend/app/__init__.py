from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, current_user
from flask_jwt_extended import JWTManager, get_jwt_identity, verify_jwt_in_request
from flask_cors import CORS
from flask_caching import Cache
from sqlalchemy import text

# 加载环境变量
import os
import sys
from dotenv import load_dotenv

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

load_dotenv()
load_dotenv(os.path.join(base_dir, '.env'))

# 确保backend目录在sys.path中，以便导入config模块
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from config import config

# 扩展初始化
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
jwt = JWTManager()
cache = Cache()

def create_app(config_name='default'):
    """应用工厂函数"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # 配置Visiray数据库连接
    visiray_db_url = os.getenv('VISIRAY_DATABASE_URL', 'mysql+pymysql://test:Visiray88!!@192.168.0.2:3306/visiray')
    app.config['SQLALCHEMY_BINDS'] = {
        'visiray': visiray_db_url
    }
    
    # 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    jwt.init_app(app)
    cache.init_app(app)
    
    # CORS配置 - 允许所有来源用于开发环境
    CORS(app, origins=['http://localhost:3000', 'http://localhost:5173', 'http://localhost:5174', 'http://localhost:8000', 'http://localhost:8001', 'http://localhost:8002', 'http://localhost:8003', 'http://127.0.0.1:5173', 'http://127.0.0.1:5174', 'http://127.0.0.1:8000', 'http://127.0.0.1:8001', 'http://127.0.0.1:8002', 'http://127.0.0.1:8003'], 
         supports_credentials=True, allow_headers=['Content-Type', 'Authorization'])
    
    # 登录管理器配置
    login_manager.login_view = 'auth.login'
    login_manager.login_message = '请先登录访问此页面'
    login_manager.login_message_category = 'info'
    
    # 注册蓝图
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    
    from app.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # 注册错误处理器
    @app.errorhandler(404)
    @app.before_request
    def require_admin_for_write_requests():
        if request.method not in {'POST', 'PUT', 'PATCH', 'DELETE'}:
            return None
        if not request.path.startswith('/api/'):
            return None

        allowed_paths = {
            '/api/auth/login',
            '/api/auth/logout',
            '/api/auth/refresh',
            '/api/auth/password/change',
            '/api/visiray/login',
        }
        if request.path in allowed_paths:
            return None

        user = None
        try:
            if current_user.is_authenticated:
                user = current_user
        except Exception:
            user = None

        if user is None:
            try:
                verify_jwt_in_request(optional=True)
                identity = get_jwt_identity()
                user_id = identity.get('user_id') if isinstance(identity, dict) else identity
                if user_id is not None:
                    from app.models.user import User
                    user = User.query.get(int(user_id))
            except Exception:
                user = None

        if user is None or not getattr(user, 'is_active', True):
            return jsonify({'success': False, 'message': '请先登录'}), 401
        if not user.has_role('admin'):
            return jsonify({'success': False, 'message': '普通用户仅可查看，编辑操作仅管理员可用'}), 403

        return None

    @app.errorhandler(404)
    def not_found_error(error):
        return {'error': 'Not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return {'error': 'Internal server error'}, 500
    
    # JWT错误处理
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return {'error': 'Token has expired'}, 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        try:
            current_app.logger.error(f"JWT invalid token: {error}")
        except Exception:
            pass
        return {'error': 'Invalid token'}, 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return {'error': 'Access token required'}, 401

    # 附件上传目录配置（可通过环境变量覆盖）
    app.config['ATTACHMENT_UPLOAD_FOLDER'] = os.getenv(
        'ATTACHMENT_UPLOAD_FOLDER',
        os.path.join(base_dir, 'uploads', 'attachments')
    )

    # 开发环境下确保 Visiray 附件表存在（跨平台，MySQL/SQLite/Postgres 通用 IF NOT EXISTS）
    try:
        with app.app_context():
            engine = db.get_engine(app, bind='visiray')
            with engine.begin() as conn:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS purchase_order_attachments (
                        id INT PRIMARY KEY AUTO_INCREMENT,
                        purchase_order_no VARCHAR(50) NOT NULL,
                        stored_filename VARCHAR(255) NOT NULL,
                        original_filename VARCHAR(255) NOT NULL,
                        content_type VARCHAR(100),
                        file_size BIGINT,
                        uploaded_by BIGINT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS part_number_rule (
                        id INT PRIMARY KEY AUTO_INCREMENT,
                        rule_name VARCHAR(100) NOT NULL,
                        prefix VARCHAR(20) DEFAULT '',
                        config_json TEXT NOT NULL,
                        is_active TINYINT(1) DEFAULT 0,
                        remark VARCHAR(500) NULL,
                        created_by BIGINT NULL,
                        updated_by BIGINT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                    )
                """))
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS contract_number_records (
                        id INT PRIMARY KEY AUTO_INCREMENT,
                        date DATE NOT NULL,
                        seq INT NOT NULL,
                        contract_no VARCHAR(50) NOT NULL UNIQUE,
                        subject VARCHAR(200) NOT NULL,
                        supplier VARCHAR(200) NULL,
                        related_order_no VARCHAR(100) NULL,
                        purchase_content TEXT NULL,
                        quantity DECIMAL(18,4) NULL,
                        amount DECIMAL(18,2) NULL,
                        attachment_file VARCHAR(255) NULL,
                        attachment_name VARCHAR(255) NULL,
                        remark TEXT NULL,
                        created_by VARCHAR(100) NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        INDEX idx_contract_number_date_seq (date, seq),
                        INDEX idx_contract_number_created_at (created_at)
                    )
                """))
                # 确保 part_number 表包含必要字段
                try:
                    cols = conn.execute(text("SHOW COLUMNS FROM part_number")).fetchall()
                    existing = {row[0] for row in cols}
                    if 'part_name' not in existing:
                        conn.execute(text("ALTER TABLE part_number ADD COLUMN part_name VARCHAR(200) NULL"))
                    if 'created_by' not in existing:
                        conn.execute(text("ALTER TABLE part_number ADD COLUMN created_by BIGINT NULL"))
                    if 'created_by_name' not in existing:
                        conn.execute(text("ALTER TABLE part_number ADD COLUMN created_by_name VARCHAR(200) NULL"))
                    if 'unit' not in existing:
                        conn.execute(text("ALTER TABLE part_number ADD COLUMN unit VARCHAR(20) NULL"))
                    if 'standard_cost' not in existing:
                        conn.execute(text("ALTER TABLE part_number ADD COLUMN standard_cost DECIMAL(12,4) DEFAULT 0"))
                except Exception as e:
                    try:
                        app.logger.warning(f"Ensure part_number columns failed: {e}")
                    except Exception:
                        pass
                try:
                    cols = conn.execute(text("SHOW COLUMNS FROM part_number_versions")).fetchall()
                    existing = {row[0] for row in cols}
                    if 'part_id' not in existing:
                        conn.execute(text("ALTER TABLE part_number_versions ADD COLUMN part_id VARCHAR(50) NOT NULL"))
                    if 'version_no' not in existing:
                        conn.execute(text("ALTER TABLE part_number_versions ADD COLUMN version_no VARCHAR(4) NOT NULL"))
                    if 'status' not in existing:
                        conn.execute(text("ALTER TABLE part_number_versions ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'active'"))
                    if 'is_current' not in existing:
                        conn.execute(text("ALTER TABLE part_number_versions ADD COLUMN is_current TINYINT(1) NOT NULL DEFAULT 0"))
                    if 'remark' not in existing:
                        conn.execute(text("ALTER TABLE part_number_versions ADD COLUMN remark VARCHAR(500) NULL"))
                    if 'created_by' not in existing:
                        conn.execute(text("ALTER TABLE part_number_versions ADD COLUMN created_by BIGINT NULL"))
                    if 'created_by_name' not in existing:
                        conn.execute(text("ALTER TABLE part_number_versions ADD COLUMN created_by_name VARCHAR(200) NULL"))
                    if 'created_at' not in existing:
                        conn.execute(text("ALTER TABLE part_number_versions ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP"))
                    if 'updated_at' not in existing:
                        conn.execute(text("ALTER TABLE part_number_versions ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))
                    indexes = conn.execute(text("SHOW INDEX FROM part_number_versions")).fetchall()
                    index_names = {row[2] for row in indexes}
                    if 'ux_part_number_versions_part_version' not in index_names:
                        conn.execute(text("CREATE UNIQUE INDEX ux_part_number_versions_part_version ON part_number_versions (part_id, version_no)"))
                    if 'idx_part_number_versions_part_current' not in index_names:
                        conn.execute(text("CREATE INDEX idx_part_number_versions_part_current ON part_number_versions (part_id, is_current, version_no)"))
                except Exception as e:
                    try:
                        app.logger.warning(f"Ensure part_number_versions columns failed: {e}")
                    except Exception:
                        pass
    except Exception as e:
        try:
            app.logger.warning(str(e))
        except Exception:
            pass
    try:
        with app.app_context():
            engine = db.get_engine(app)
            with engine.begin() as conn:
                try:
                    cols = conn.execute(text("SHOW COLUMNS FROM materials")).fetchall()
                    existing = {row[0] for row in cols}
                    if 'visiray_part_id' not in existing:
                        conn.execute(text("ALTER TABLE materials ADD COLUMN visiray_part_id VARCHAR(50) NULL"))
                    indexes = conn.execute(text("SHOW INDEX FROM materials WHERE Key_name = 'ux_materials_visiray_part_id'")).fetchall()
                    if not indexes:
                        conn.execute(text("CREATE UNIQUE INDEX ux_materials_visiray_part_id ON materials (visiray_part_id)"))
                except Exception as e:
                    try:
                        app.logger.warning(f"Ensure materials visiray_part_id failed: {e}")
                    except Exception:
                        pass
                try:
                    conn.execute(text("""
                        ALTER TABLE boms
                        MODIFY COLUMN status ENUM('draft','active','inactive','obsolete')
                        DEFAULT 'draft'
                    """))
                except Exception as e:
                    try:
                        app.logger.warning(f"Ensure boms status enum failed: {e}")
                    except Exception:
                        pass
                try:
                    cols = conn.execute(text("SHOW COLUMNS FROM boms")).fetchall()
                    existing = {row[0] for row in cols}
                    if 'is_deleted' not in existing:
                        conn.execute(text("ALTER TABLE boms ADD COLUMN is_deleted TINYINT(1) NOT NULL DEFAULT 0"))
                    if 'deleted_at' not in existing:
                        conn.execute(text("ALTER TABLE boms ADD COLUMN deleted_at DATETIME NULL"))
                    if 'deleted_by' not in existing:
                        conn.execute(text("ALTER TABLE boms ADD COLUMN deleted_by BIGINT NULL"))
                except Exception as e:
                    try:
                        app.logger.warning(f"Ensure boms soft delete columns failed: {e}")
                    except Exception:
                        pass
    except Exception as e:
        try:
            app.logger.warning(str(e))
        except Exception:
            pass
    try:
        with app.app_context():
            from app.models.user import Role, Permission
            admin_role = Role.query.filter_by(code='admin').first()
            if admin_role:
                admin_role.permissions = Permission.query.all()
            user_role = Role.query.filter_by(code='user').first()
            if user_role:
                read_permissions = Permission.query.filter(Permission.action == 'read').all()
                user_role.permissions = read_permissions
            bom_admin_role = Role.query.filter_by(code='bom_admin').first()
            if bom_admin_role:
                purchase_perms = Permission.query.filter(
                    Permission.code.in_([
                        'purchase_attachment_read',
                        'purchase_attachment_create',
                        'purchase_attachment_delete',
                        'purchase_attachment_download'
                    ])
                ).all()
                for p in purchase_perms:
                    if p not in bom_admin_role.permissions:
                        bom_admin_role.permissions.append(p)
            db.session.commit()
    except Exception:
        pass
    
    return app
