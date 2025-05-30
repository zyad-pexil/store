"""
مسارات لوحة تحكم المدير لمتجر سوقي الإلكتروني
يتضمن مسارات إدارة المنتجات والطلبات والمستخدمين
"""

from flask import Blueprint, render_template, redirect, url_for, request, flash, session, jsonify
from src.models import db, User, Product, Category, ProductImage, Order, OrderItem, OrderStatusHistory, Review
from src.routes.auth import admin_required
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from flask_wtf.csrf import CSRFProtect

# إنشاء مخطط المسارات
admin_bp = Blueprint('admin', __name__)

# الصفحة الرئيسية للوحة التحكم
@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """
    لوحة تحكم المدير الرئيسية
    """
    # إحصائيات سريعة
    total_products = Product.query.count()
    total_orders = Order.query.count()
    pending_orders = Order.query.filter_by(status='processing').count()
    total_customers = User.query.filter_by(role='customer').count()
    
    # آخر الطلبات
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html', 
                          total_products=total_products,
                          total_orders=total_orders,
                          pending_orders=pending_orders,
                          total_customers=total_customers,
                          recent_orders=recent_orders)

# إدارة المنتجات
@admin_bp.route('/products')
@admin_required
def products():
    """
    عرض قائمة المنتجات
    """
    products = Product.query.all()
    return render_template('admin/products/index.html', products=products)

@admin_bp.route('/products/create', methods=['GET', 'POST'])
@admin_required
def create_product():
    """
    إنشاء منتج جديد
    """
    categories = Category.query.all()
    
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            description = request.form.get('description')
            price = request.form.get('price')
            stock_quantity = request.form.get('stock_quantity')
            category_id = request.form.get('category_id')
            
            # التحقق من البيانات
            if not name or not price or not category_id:
                flash('يرجى ملء جميع الحقول المطلوبة', 'danger')
                return render_template('admin/products/create.html', categories=categories)
            
            # إنشاء منتج جديد
            new_product = Product(
                name=name,
                description=description,
                price=float(price),
                stock_quantity=int(stock_quantity) if stock_quantity else 0,
                category_id=int(category_id),
                created_by=session.get('user_id')
            )
            
            db.session.add(new_product)
            db.session.commit()
            
            # معالجة الصور
            if 'product_images' in request.files:
                images = request.files.getlist('product_images')
                upload_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src', 'static', 'uploads', 'products')
                
                # التأكد من وجود المجلد
                os.makedirs(upload_dir, exist_ok=True)
                
                for i, image in enumerate(images):
                    if image and image.filename:
                        # تأمين اسم الملف
                        filename = secure_filename(image.filename)
                        # إضافة طابع زمني لتجنب تكرار الأسماء
                        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                        unique_filename = f"{timestamp}_{filename}"
                        
                        # حفظ الصورة
                        image_path = os.path.join(upload_dir, unique_filename)
                        image.save(image_path)
                        
                        # إنشاء سجل للصورة
                        product_image = ProductImage(
                            product_id=new_product.id,
                            image_path=f"/static/uploads/products/{unique_filename}",
                            is_primary=(i == 0)  # الصورة الأولى هي الرئيسية
                        )
                        db.session.add(product_image)
                
                db.session.commit()
            
            flash('تم إضافة المنتج بنجاح', 'success')
            return redirect(url_for('admin.products'))
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء إضافة المنتج: {str(e)}', 'danger')
            return render_template('admin/products/create.html', categories=categories)
    
    return render_template('admin/products/create.html', categories=categories)

@admin_bp.route('/products/<int:product_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_product(product_id):
    """
    تعديل منتج موجود
    """
    product = Product.query.get_or_404(product_id)
    categories = Category.query.all()
    
    if request.method == 'POST':
        try:
            product.name = request.form.get('name')
            product.description = request.form.get('description')
            product.price = float(request.form.get('price'))
            product.stock_quantity = int(request.form.get('stock_quantity', 0))
            product.category_id = int(request.form.get('category_id'))
            product.is_active = 'is_active' in request.form
            
            db.session.commit()
            
            # معالجة الصور الجديدة
            if 'product_images' in request.files:
                images = request.files.getlist('product_images')
                upload_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src', 'static', 'uploads', 'products')
                
                # التأكد من وجود المجلد
                os.makedirs(upload_dir, exist_ok=True)
                
                for image in images:
                    if image and image.filename:
                        # تأمين اسم الملف
                        filename = secure_filename(image.filename)
                        # إضافة طابع زمني لتجنب تكرار الأسماء
                        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                        unique_filename = f"{timestamp}_{filename}"
                        
                        # حفظ الصورة
                        image_path = os.path.join(upload_dir, unique_filename)
                        image.save(image_path)
                        
                        # إنشاء سجل للصورة
                        product_image = ProductImage(
                            product_id=product.id,
                            image_path=f"/static/uploads/products/{unique_filename}",
                            is_primary=False
                        )
                        db.session.add(product_image)
                
                db.session.commit()
            
            flash('تم تحديث المنتج بنجاح', 'success')
            return redirect(url_for('admin.products'))
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء تحديث المنتج: {str(e)}', 'danger')
            return render_template('admin/products/edit.html', product=product, categories=categories)
    
    return render_template('admin/products/edit.html', product=product, categories=categories)

@admin_bp.route('/products/<int:product_id>/delete', methods=['POST'])
@admin_required
def delete_product(product_id):
    """
    حذف منتج
    """
    try:
        product = Product.query.get_or_404(product_id)
        
        # حذف صور المنتج
        for image in product.images:
            # حذف الملف الفعلي إذا كان موجوداً
            image_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), image.image_path.lstrip('/'))
            if os.path.exists(image_path):
                os.remove(image_path)
        
        db.session.delete(product)
        db.session.commit()
        
        flash('تم حذف المنتج بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء حذف المنتج: {str(e)}', 'danger')
    
    return redirect(url_for('admin.products'))

# إدارة الطلبات
@admin_bp.route('/orders')
@admin_required
def orders():
    """
    عرض قائمة الطلبات
    """
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template('admin/orders/index.html', orders=orders)

@admin_bp.route('/orders/<int:order_id>')
@admin_required
def show_order(order_id):
    """
    عرض تفاصيل طلب محدد
    """
    order = Order.query.get_or_404(order_id)
    return render_template('admin/orders/show.html', order=order)

@admin_bp.route('/orders/<int:order_id>/edit', methods=['GET'])
@admin_required
def edit_order(order_id):
    """
    تعديل حالة طلب
    """
    order = Order.query.get_or_404(order_id)
    return render_template('admin/orders/edit.html', order=order)

@admin_bp.route('/orders/<int:order_id>/update-status', methods=['POST'])
@admin_required
def update_order_status(order_id):
    """
    تحديث حالة الطلب
    """
    try:
        order = Order.query.get_or_404(order_id)
        new_status = request.form.get('new_status')
        payment_status = request.form.get('payment_status')
        tracking_number = request.form.get('tracking_number')
        notes = request.form.get('notes', '')
        notify_customer = 'notify_customer' in request.form
        
        if not new_status or new_status not in ['pending', 'processing', 'shipped', 'delivered', 'cancelled']:
            flash('حالة الطلب غير صالحة', 'danger')
            return redirect(url_for('admin.edit_order', order_id=order_id))
        
        # تحديث حالة الطلب
        order.status = new_status
        order.payment_status = payment_status
        order.tracking_number = tracking_number
        
        # إضافة سجل لتحديث الحالة
        status_update = OrderStatusHistory(
            order_id=order.id,
            status=new_status,
            notes=notes,
            updated_by=session.get('user_id')
        )
        
        db.session.add(status_update)
        db.session.commit()
        
        # إرسال إشعار للعميل إذا تم تحديد ذلك
        if notify_customer:
            # هنا يمكن إضافة كود لإرسال إشعار للعميل
            pass
        
        flash('تم تحديث حالة الطلب بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء تحديث حالة الطلب: {str(e)}', 'danger')
    
    return redirect(url_for('admin.show_order', order_id=order_id))

# إدارة الفئات
@admin_bp.route('/categories')
@admin_required
def categories():
    """
    عرض قائمة الفئات
    """
    categories = Category.query.all()
    return render_template('admin/categories/index.html', categories=categories)

@admin_bp.route('/categories/create', methods=['GET', 'POST'])
@admin_required
def create_category():
    """
    إنشاء فئة جديدة
    """
    parent_categories = Category.query.all()
    
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            description = request.form.get('description')
            parent_id = request.form.get('parent_id')
            
            if not name:
                flash('يرجى إدخال اسم الفئة', 'danger')
                return render_template('admin/categories/create.html', parent_categories=parent_categories)
            
            new_category = Category(
                name=name,
                description=description,
                parent_id=int(parent_id) if parent_id else None
            )
            
            db.session.add(new_category)
            db.session.commit()
            
            # معالجة صورة الفئة
            if 'category_image' in request.files:
                image = request.files['category_image']
                if image and image.filename:
                    # تأمين اسم الملف
                    filename = secure_filename(image.filename)
                    # إضافة طابع زمني لتجنب تكرار الأسماء
                    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                    unique_filename = f"{timestamp}_{filename}"
                    
                    # إنشاء مجلد الصور إذا لم يكن موجوداً
                    upload_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src', 'static', 'uploads', 'categories')
                    os.makedirs(upload_dir, exist_ok=True)
                    
                    # حفظ الصورة
                    image_path = os.path.join(upload_dir, unique_filename)
                    image.save(image_path)
                    
                    # تحديث مسار الصورة في الفئة
                    new_category.image_path = f"/static/uploads/categories/{unique_filename}"
                    db.session.commit()
            
            flash('تم إضافة الفئة بنجاح', 'success')
            return redirect(url_for('admin.categories'))
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء إضافة الفئة: {str(e)}', 'danger')
            return render_template('admin/categories/create.html', parent_categories=parent_categories)
    
    return render_template('admin/categories/create.html', parent_categories=parent_categories)

@admin_bp.route('/categories/<int:category_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_category(category_id):
    """
    تعديل فئة موجودة
    """
    category = Category.query.get_or_404(category_id)
    parent_categories = Category.query.filter(Category.id != category_id).all()
    
    if request.method == 'POST':
        try:
            category.name = request.form.get('name')
            category.description = request.form.get('description')
            parent_id = request.form.get('parent_id')
            category.parent_id = int(parent_id) if parent_id else None
            
            db.session.commit()
            
            # معالجة صورة الفئة
            if 'category_image' in request.files:
                image = request.files['category_image']
                if image and image.filename:
                    # تأمين اسم الملف
                    filename = secure_filename(image.filename)
                    # إضافة طابع زمني لتجنب تكرار الأسماء
                    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                    unique_filename = f"{timestamp}_{filename}"
                    
                    # إنشاء مجلد الصور إذا لم يكن موجوداً
                    upload_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src', 'static', 'uploads', 'categories')
                    os.makedirs(upload_dir, exist_ok=True)
                    
                    # حفظ الصورة
                    image_path = os.path.join(upload_dir, unique_filename)
                    image.save(image_path)
                    
                    # تحديث مسار الصورة في الفئة
                    category.image_path = f"/static/uploads/categories/{unique_filename}"
                    db.session.commit()
            
            flash('تم تحديث الفئة بنجاح', 'success')
            return redirect(url_for('admin.categories'))
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء تحديث الفئة: {str(e)}', 'danger')
            return render_template('admin/categories/edit.html', category=category, parent_categories=parent_categories)
    
    return render_template('admin/categories/edit.html', category=category, parent_categories=parent_categories)

@admin_bp.route('/categories/<int:category_id>/delete', methods=['POST'])
@admin_required
def delete_category(category_id):
    """
    حذف فئة
    """
    try:
        category = Category.query.get_or_404(category_id)
        
        # التحقق من عدم وجود منتجات مرتبطة بالفئة
        if category.products:
            flash('لا يمكن حذف الفئة لأنها تحتوي على منتجات', 'danger')
            return redirect(url_for('admin.categories'))
        
        # التحقق من عدم وجود فئات فرعية
        if category.subcategories:
            flash('لا يمكن حذف الفئة لأنها تحتوي على فئات فرعية', 'danger')
            return redirect(url_for('admin.categories'))
        
        db.session.delete(category)
        db.session.commit()
        
        flash('تم حذف الفئة بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء حذف الفئة: {str(e)}', 'danger')
    
    return redirect(url_for('admin.categories'))

# إدارة المستخدمين
@admin_bp.route('/users')
@admin_required
def users():
    """
    عرض قائمة المستخدمين
    """
    users = User.query.all()
    return render_template('admin/users/index.html', users=users)

@admin_bp.route('/users/<int:user_id>')
@admin_required
def view_user(user_id):
    """
    عرض تفاصيل مستخدم محدد
    """
    user = User.query.get_or_404(user_id)
    return render_template('admin/users/show.html', user=user)

# إدارة التقييمات
@admin_bp.route('/reviews')
@admin_required
def reviews():
    """
    عرض قائمة التقييمات
    """
    reviews = Review.query.all()
    return render_template('admin/reviews/index.html', reviews=reviews)

@admin_bp.route('/reviews/<int:review_id>/approve', methods=['POST'])
@admin_required
def approve_review(review_id):
    """
    الموافقة على تقييم
    """
    try:
        review = Review.query.get_or_404(review_id)
        review.is_approved = True
        db.session.commit()
        
        flash('تم الموافقة على التقييم بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء الموافقة على التقييم: {str(e)}', 'danger')
    
    return redirect(url_for('admin.reviews'))

@admin_bp.route('/reviews/<int:review_id>/delete', methods=['POST'])
@admin_required
def delete_review(review_id):
    """
    حذف تقييم
    """
    try:
        review = Review.query.get_or_404(review_id)
        db.session.delete(review)
        db.session.commit()
        
        flash('تم حذف التقييم بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء حذف التقييم: {str(e)}', 'danger')
    
    return redirect(url_for('admin.reviews'))
