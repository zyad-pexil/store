"""
تهيئة تطبيق Flask الرئيسي لمتجر سوقي الإلكتروني
يتضمن إعدادات التطبيق وتسجيل المسارات وتهيئة قاعدة البيانات
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))  # DON'T CHANGE THIS !!!

from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
import logging
from logging.handlers import RotatingFileHandler

# إنشاء تطبيق Flask
app = Flask(__name__)

# تكوين التطبيق
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "sooqi_secret_key_2025_default")

# إعدادات قاعدة البيانات لـ PythonAnywhere (MySQL) أو SQLite
pa_mysql_user = os.environ.get("PA_MYSQL_USER")
pa_mysql_password = os.environ.get("PA_MYSQL_PASSWORD")
pa_mysql_host = os.environ.get("PA_MYSQL_HOST")
pa_mysql_db = os.environ.get("PA_MYSQL_DB")

if pa_mysql_user and pa_mysql_password and pa_mysql_host and pa_mysql_db:
    # استخدام MySQL إذا كانت متغيرات البيئة موجودة (لـ PythonAnywhere)
    app.config["SQLALCHEMY_DATABASE_URI"] = f"mysql+pymysql://{pa_mysql_user}:{pa_mysql_password}@{pa_mysql_host}/{pa_mysql_db}"
else:
    # استخدام SQLite كخيار افتراضي (للتشغيل المحلي أو إذا لم يتم تكوين MySQL)
    # تأكد من أن مسار instance صحيح بالنسبة لموقع main.py
    instance_path = os.path.join(os.path.dirname(app.instance_path), "instance")
    if not os.path.exists(instance_path):
        os.makedirs(instance_path)
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(instance_path, 'sooqi.db')}"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = os.path.join(os.path.dirname(__file__), "static", "uploads") # تعديل مسار الرفع
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB max upload size
app.config["DEBUG"] = os.environ.get("FLASK_DEBUG", "False").lower() == "true"

# تهيئة حماية CSRF
csrf = CSRFProtect(app)

# تهيئة قاعدة البيانات
db = SQLAlchemy()
db.init_app(app)

# إعداد التسجيل (Logging)
if not os.path.exists('logs'):
    os.mkdir('logs')

file_handler = RotatingFileHandler('logs/sooqi.log', maxBytes=10240, backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)
app.logger.info('تم بدء تشغيل متجر سوقي')

# استيراد النماذج
from src.models import User, Product, Category, Order, Review

# تسجيل المسارات
from src.routes.auth import auth_bp
from src.routes.admin import admin_bp
from src.routes.customer import customer_bp
from src.routes.api import api_bp

app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(customer_bp, url_prefix='/customer')
app.register_blueprint(api_bp, url_prefix='/api')

# Flask CLI command for database setup
@app.cli.command("setup-db")
def setup_database_command():
    """Creates database tables and default admin user."""
    try:
        # إنشاء مجلد instance إذا لم يكن موجوداً (مهم لـ SQLite)
        # تأكد من أن مسار instance صحيح بالنسبة لموقع main.py
        instance_path = os.path.join(os.path.dirname(app.instance_path), "instance")
        if not os.path.exists(instance_path):
            os.makedirs(instance_path)
            print(f"Created instance folder at: {instance_path}")

        # إنشاء جداول قاعدة البيانات
        with app.app_context(): # Ensure operations are within app context
            db.create_all()
            print("Database tables created successfully!")

            # إنشاء مستخدم مدير افتراضي إذا لم يكن موجوداً
            admin_email = 'admin@sooqi.com'
            admin = User.query.filter_by(email=admin_email).first()
            if not admin:
                admin_password = 'admin123' # Consider prompting or using env var in production
                admin = User(
                    username='admin',
                    email=admin_email,
                    password=admin_password, # Password will be hashed by the model's setter
                    full_name='Admin User',
                    role='admin',
                    is_active=True
                )
                db.session.add(admin)
                db.session.commit()
                print(f"Admin user ({admin_email}) created successfully with default password.")
            else:
                print(f"Admin user ({admin_email}) already exists.")
    except Exception as e:
        db.session.rollback()
        print(f"Error during database setup: {str(e)}")
        sys.exit(1) # Exit with error code

# معالجة الأخطاء
@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    app.logger.error(f'خطأ داخلي في الخادم: {str(error)}')
    return render_template('errors/500.html'), 500

# الصفحة الرئيسية
@app.route('/')
def index():
    try:
        featured_products = Product.query.filter_by(is_featured=True).limit(8).all()
        categories = Category.query.all()
        return render_template('index.html', featured_products=featured_products, categories=categories)
    except Exception as e:
        app.logger.error(f'خطأ في الصفحة الرئيسية: {str(e)}')
        return render_template('index.html', featured_products=[], categories=[])

# تشغيل التطبيق
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
