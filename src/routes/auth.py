"""
مسارات المصادقة لمتجر سوقي الإلكتروني
يتضمن مسارات تسجيل الدخول، التسجيل، وتسجيل الخروج
"""

from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from src.models import db, User
from functools import wraps

# إنشاء مخطط المسارات
auth_bp = Blueprint('auth', __name__)

# وظائف المساعدة للتحقق من الصلاحيات

def login_required(f):
    """
    مُزين للتحقق من تسجيل دخول المستخدم
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('يرجى تسجيل الدخول للوصول إلى هذه الصفحة', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """
    مُزين للتحقق من صلاحيات المدير
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('يرجى تسجيل الدخول للوصول إلى هذه الصفحة', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        
        user = User.query.get(session['user_id'])
        if not user or not user.is_admin():
            flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'danger')
            return redirect(url_for('index'))
        
        return f(*args, **kwargs)
    return decorated_function

def customer_required(f):
    """
    مُزين للتحقق من صلاحيات العميل
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('يرجى تسجيل الدخول للوصول إلى هذه الصفحة', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        
        user = User.query.get(session['user_id'])
        if not user or not user.is_customer():
            flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'danger')
            return redirect(url_for('index'))
        
        return f(*args, **kwargs)
    return decorated_function

# مسارات المصادقة

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    صفحة تسجيل الدخول
    """
    # التحقق إذا كان المستخدم مسجل دخوله بالفعل
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user:
            if user.is_admin():
                return redirect(url_for('admin.dashboard'))
            else:
                return redirect(url_for('customer.dashboard'))
    
    # معالجة نموذج تسجيل الدخول
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # التحقق من البيانات
        if not email or not password:
            flash('يرجى إدخال البريد الإلكتروني وكلمة المرور', 'danger')
            return render_template('auth/login.html')
        
        # البحث عن المستخدم في قاعدة البيانات
        user = User.query.filter_by(email=email).first()
        
        # التحقق من وجود المستخدم وصحة كلمة المرور
        if not user or not user.verify_password(password):
            flash('البريد الإلكتروني أو كلمة المرور غير صحيحة', 'danger')
            return render_template('auth/login.html')
        
        # تسجيل الدخول بنجاح
        session['user_id'] = user.id
        session['username'] = user.username
        session['role'] = user.role
        
        # توجيه المستخدم حسب دوره
        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)
        elif user.is_admin():
            return redirect(url_for('admin.dashboard'))
        else:
            return redirect(url_for('customer.dashboard'))
    
    # عرض صفحة تسجيل الدخول
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    صفحة التسجيل الجديد
    """
    # التحقق إذا كان المستخدم مسجل دخوله بالفعل
    if 'user_id' in session:
        return redirect(url_for('index'))
    
    # معالجة نموذج التسجيل
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        phone = request.form.get('phone')
        
        # تعيين دور المستخدم دائمًا كعميل
        role = 'customer'
        
        # التحقق من البيانات
        if not username or not email or not password or not confirm_password:
            flash('يرجى ملء جميع الحقول المطلوبة', 'danger')
            return render_template('auth/register.html')
        
        if password != confirm_password:
            flash('كلمات المرور غير متطابقة', 'danger')
            return render_template('auth/register.html')
        
        # التحقق من عدم وجود مستخدم بنفس اسم المستخدم أو البريد الإلكتروني
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            flash('اسم المستخدم أو البريد الإلكتروني مستخدم بالفعل', 'danger')
            return render_template('auth/register.html')
        
        # إنشاء مستخدم جديد
        new_user = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            role=role  # دائمًا 'customer'
        )
        new_user.password = password  # سيتم تشفيرها تلقائياً
        
        # حفظ المستخدم في قاعدة البيانات
        db.session.add(new_user)
        db.session.commit()
        
        flash('تم التسجيل بنجاح! يمكنك الآن تسجيل الدخول', 'success')
        return redirect(url_for('auth.login'))
    
    # عرض صفحة التسجيل
    return render_template('auth/register.html')

@auth_bp.route('/logout')
def logout():
    """
    تسجيل الخروج
    """
    # مسح بيانات الجلسة
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('role', None)
    
    flash('تم تسجيل الخروج بنجاح', 'info')
    return redirect(url_for('index'))

@auth_bp.route('/profile')
@login_required
def profile():
    """
    صفحة الملف الشخصي
    """
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        flash('حدث خطأ في الجلسة، يرجى تسجيل الدخول مرة أخرى', 'warning')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/profile.html', user=user)

@auth_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """
    صفحة تعديل الملف الشخصي
    """
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        flash('حدث خطأ في الجلسة، يرجى تسجيل الدخول مرة أخرى', 'warning')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        # تحديث بيانات المستخدم
        user.first_name = request.form.get('first_name', user.first_name)
        user.last_name = request.form.get('last_name', user.last_name)
        user.phone = request.form.get('phone', user.phone)
        
        # تحديث كلمة المرور إذا تم توفيرها
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if current_password and new_password and confirm_password:
            if not user.verify_password(current_password):
                flash('كلمة المرور الحالية غير صحيحة', 'danger')
                return render_template('auth/edit_profile.html', user=user)
            
            if new_password != confirm_password:
                flash('كلمات المرور الجديدة غير متطابقة', 'danger')
                return render_template('auth/edit_profile.html', user=user)
            
            user.password = new_password  # سيتم تشفيرها تلقائياً
        
        # حفظ التغييرات
        db.session.commit()
        
        flash('تم تحديث الملف الشخصي بنجاح', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/edit_profile.html', user=user)
