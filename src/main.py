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
# استخدام DATABASE_URL من متغيرات البيئة إذا كان موجوداً، وإلا استخدم SQLite
database_url = os.environ.get("DATABASE_URL")
if database_url and database_url.startswith("postgres://"):
    # Render قد يوفر رابط يبدأ بـ postgres:// بدلاً من postgresql://
    database_url = database_url.replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = database_url or "sqlite:///../instance/sooqi.db" # تعديل مسار SQLite
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

# مسار خاص لتهيئة قاعدة البيانات (يستخدم مرة واحدة فقط)
@app.route('/setup-database')
def setup_database():
    try:
        # إنشاء جداول قاعدة البيانات
        db.create_all()
        
        # إنشاء مستخدم مدير افتراضي إذا لم يكن موجوداً
        admin = User.query.filter_by(email='admin@sooqi.com').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@sooqi.com',
                password='admin123',  # في الإنتاج، يجب استخدام كلمة مرور أكثر تعقيداً
                full_name='مدير النظام',
                role='admin',
                is_active=True
            )
            db.session.add(admin)
            db.session.commit()
            return 'تم إنشاء قاعدة البيانات وإضافة المستخدم المدير بنجاح!'
        else:
            return 'قاعدة البيانات موجودة بالفعل والمستخدم المدير موجود!'
    except Exception as e:
        return f'حدث خطأ أثناء إعداد قاعدة البيانات: {str(e)}'

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
