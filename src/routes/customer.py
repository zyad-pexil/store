"""
مسارات واجهة العميل لمتجر سوقي الإلكتروني
يتضمن مسارات عرض المنتجات، سلة التسوق، الطلبات، والتقييمات
"""

from flask import Blueprint, render_template, redirect, url_for, request, flash, session, jsonify
from src.models import db, User, Product, Category, ProductImage, CartItem, Order, OrderItem, Address, Review
from src.routes.auth import login_required, customer_required
from werkzeug.utils import secure_filename
import os
from datetime import datetime

# إنشاء مخطط المسارات
customer_bp = Blueprint('customer', __name__)

# الصفحة الرئيسية للعميل
@customer_bp.route('/dashboard')
@customer_required
def dashboard():
    """
    لوحة تحكم العميل الرئيسية
    """
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    
    # آخر الطلبات للعميل
    recent_orders = Order.query.filter_by(user_id=user_id).order_by(Order.created_at.desc()).limit(5).all()
    
    # عدد العناصر في سلة التسوق
    cart_count = CartItem.query.filter_by(user_id=user_id).count()
    
    return render_template('customer/dashboard.html', 
                          user=user,
                          recent_orders=recent_orders,
                          cart_count=cart_count)

# عرض المنتجات
@customer_bp.route('/products')
def products():
    """
    عرض قائمة المنتجات
    """
    # البحث والتصفية
    search_query = request.args.get('search', '')
    category_id = request.args.get('category', '')
    sort_by = request.args.get('sort_by', 'newest')
    
    # بناء الاستعلام
    query = Product.query.filter(Product.is_active == True)
    
    # تطبيق البحث
    if search_query:
        query = query.filter(Product.name.ilike(f'%{search_query}%') | 
                            Product.description.ilike(f'%{search_query}%'))
    
    # تطبيق التصفية حسب الفئة
    if category_id and category_id.isdigit():
        query = query.filter(Product.category_id == int(category_id))
    
    # تطبيق الترتيب
    if sort_by == 'price_low':
        query = query.order_by(Product.price.asc())
    elif sort_by == 'price_high':
        query = query.order_by(Product.price.desc())
    else:  # 'newest' هو الافتراضي
        query = query.order_by(Product.created_at.desc())
    
    # تنفيذ الاستعلام
    products = query.all()
    
    # الحصول على جميع الفئات للتصفية
    categories = Category.query.all()
    
    return render_template('customer/products/index.html', 
                          products=products,
                          categories=categories,
                          search_query=search_query,
                          category_id=category_id,
                          sort_by=sort_by)

# إضافة مسار عرض المنتجات حسب الفئة
@customer_bp.route('/category/<int:category_id>/products')
def category_products(category_id):
    """
    عرض المنتجات حسب الفئة
    """
    category = Category.query.get_or_404(category_id)
    
    # البحث والتصفية
    search_query = request.args.get('search', '')
    sort_by = request.args.get('sort_by', 'newest')
    
    # بناء الاستعلام
    query = Product.query.filter(Product.category_id == category_id, Product.is_active == True)
    
    # تطبيق البحث
    if search_query:
        query = query.filter(Product.name.ilike(f'%{search_query}%') | 
                            Product.description.ilike(f'%{search_query}%'))
    
    # تطبيق الترتيب
    if sort_by == 'price_low':
        query = query.order_by(Product.price.asc())
    elif sort_by == 'price_high':
        query = query.order_by(Product.price.desc())
    else:  # 'newest' هو الافتراضي
        query = query.order_by(Product.created_at.desc())
    
    # تنفيذ الاستعلام
    products = query.all()
    
    # الحصول على جميع الفئات للتصفية
    categories = Category.query.all()
    
    return render_template('customer/products/category.html', 
                          products=products,
                          categories=categories,
                          current_category=category,
                          search_query=search_query,
                          sort_by=sort_by)

@customer_bp.route('/products/<int:product_id>')
def product_details(product_id):
    """
    عرض تفاصيل منتج محدد
    """
    product = Product.query.get_or_404(product_id)
    
    # الحصول على التقييمات المعتمدة فقط
    reviews = Review.query.filter_by(product_id=product_id, is_approved=True).all()
    
    # حساب متوسط التقييم
    avg_rating = 0
    if reviews:
        avg_rating = sum(review.rating for review in reviews) / len(reviews)
    
    # منتجات مشابهة (من نفس الفئة)
    similar_products = Product.query.filter(
        Product.category_id == product.category_id,
        Product.id != product.id,
        Product.is_active == True
    ).limit(4).all()
    
    return render_template('customer/products/details.html', 
                          product=product,
                          reviews=reviews,
                          avg_rating=avg_rating,
                          similar_products=similar_products)

# سلة التسوق
@customer_bp.route('/cart')
@customer_required
def cart():
    """
    عرض سلة التسوق
    """
    user_id = session.get('user_id')
    cart_items = CartItem.query.filter_by(user_id=user_id).all()
    
    # حساب المجموع
    total = sum(item.product.price * item.quantity for item in cart_items)
    
    return render_template('customer/cart.html', 
                          cart_items=cart_items,
                          total=total)

@customer_bp.route('/cart/add/<int:product_id>', methods=['POST'])
@customer_required
def add_to_cart(product_id):
    """
    إضافة منتج إلى سلة التسوق
    """
    user_id = session.get('user_id')
    product = Product.query.get_or_404(product_id)
    
    # التحقق من توفر المنتج
    if not product.is_active:
        flash('هذا المنتج غير متوفر حالياً', 'danger')
        return redirect(url_for('customer.product_details', product_id=product_id))
    
    quantity = int(request.form.get('quantity', 1))
    
    # التحقق من الكمية المطلوبة
    if quantity <= 0:
        flash('يجب أن تكون الكمية أكبر من صفر', 'danger')
        return redirect(url_for('customer.product_details', product_id=product_id))
    
    if quantity > product.stock_quantity:
        flash(f'الكمية المطلوبة غير متوفرة. المتاح حالياً: {product.stock_quantity}', 'danger')
        return redirect(url_for('customer.product_details', product_id=product_id))
    
    # التحقق مما إذا كان المنتج موجوداً بالفعل في السلة
    cart_item = CartItem.query.filter_by(user_id=user_id, product_id=product_id).first()
    
    if cart_item:
        # تحديث الكمية
        cart_item.quantity += quantity
        if cart_item.quantity > product.stock_quantity:
            cart_item.quantity = product.stock_quantity
            flash(f'تم تحديث الكمية إلى الحد الأقصى المتاح: {product.stock_quantity}', 'warning')
    else:
        # إضافة منتج جديد إلى السلة
        cart_item = CartItem(
            user_id=user_id,
            product_id=product_id,
            quantity=quantity
        )
        db.session.add(cart_item)
    
    db.session.commit()
    
    flash('تمت إضافة المنتج إلى سلة التسوق', 'success')
    return redirect(url_for('customer.cart'))

@customer_bp.route('/cart/update/<int:cart_item_id>', methods=['POST'])
@customer_required
def update_cart(cart_item_id):
    """
    تحديث كمية منتج في سلة التسوق
    """
    user_id = session.get('user_id')
    cart_item = CartItem.query.filter_by(id=cart_item_id, user_id=user_id).first_or_404()
    
    quantity = int(request.form.get('quantity', 1))
    
    # التحقق من الكمية المطلوبة
    if quantity <= 0:
        # حذف العنصر من السلة
        db.session.delete(cart_item)
        db.session.commit()
        flash('تم حذف المنتج من سلة التسوق', 'info')
    else:
        # التحقق من توفر الكمية
        if quantity > cart_item.product.stock_quantity:
            quantity = cart_item.product.stock_quantity
            flash(f'تم تحديث الكمية إلى الحد الأقصى المتاح: {cart_item.product.stock_quantity}', 'warning')
        
        # تحديث الكمية
        cart_item.quantity = quantity
        db.session.commit()
        flash('تم تحديث سلة التسوق', 'success')
    
    return redirect(url_for('customer.cart'))

@customer_bp.route('/cart/remove/<int:cart_item_id>', methods=['POST'])
@customer_required
def remove_from_cart(cart_item_id):
    """
    حذف منتج من سلة التسوق
    """
    user_id = session.get('user_id')
    cart_item = CartItem.query.filter_by(id=cart_item_id, user_id=user_id).first_or_404()
    
    db.session.delete(cart_item)
    db.session.commit()
    
    flash('تم حذف المنتج من سلة التسوق', 'success')
    return redirect(url_for('customer.cart'))

# الطلبات
@customer_bp.route('/checkout', methods=['GET', 'POST'])
@customer_required
def checkout():
    """
    إتمام عملية الشراء
    """
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    
    # الحصول على عناصر السلة
    cart_items = CartItem.query.filter_by(user_id=user_id).all()
    
    if not cart_items:
        flash('سلة التسوق فارغة', 'warning')
        return redirect(url_for('customer.products'))
    
    # حساب المجموع
    total = sum(item.product.price * item.quantity for item in cart_items)
    
    # الحصول على عناوين المستخدم
    addresses = Address.query.filter_by(user_id=user_id).all()
    
    if request.method == 'POST':
        # التحقق من وجود عنوان
        address_id = request.form.get('address_id')
        payment_method = request.form.get('payment_method')
        notes = request.form.get('notes', '')
        
        if not address_id:
            flash('يرجى اختيار عنوان للتوصيل', 'danger')
            return render_template('customer/checkout.html', 
                                  cart_items=cart_items,
                                  total=total,
                                  addresses=addresses)
        
        # إنشاء طلب جديد
        new_order = Order(
            user_id=user_id,
            address_id=int(address_id),
            total_amount=total,
            payment_method=payment_method,
            notes=notes,
            status='processing',
            payment_status='pending'
        )
        
        db.session.add(new_order)
        db.session.flush()  # للحصول على معرف الطلب
        
        # إضافة عناصر الطلب
        for item in cart_items:
            order_item = OrderItem(
                order_id=new_order.id,
                product_id=item.product_id,
                quantity=item.quantity,
                price=item.product.price
            )
            db.session.add(order_item)
            
            # تحديث المخزون
            product = item.product
            product.stock_quantity -= item.quantity
            
            # حذف العنصر من السلة
            db.session.delete(item)
        
        # إضافة سجل لحالة الطلب
        status_update = OrderStatusHistory(
            order_id=new_order.id,
            status='processing',
            notes='تم إنشاء الطلب',
            updated_by=user_id
        )
        db.session.add(status_update)
        
        db.session.commit()
        
        flash('تم إنشاء الطلب بنجاح', 'success')
        return redirect(url_for('customer.view_order', order_id=new_order.id))
    
    return render_template('customer/checkout.html', 
                          cart_items=cart_items,
                          total=total,
                          addresses=addresses)

@customer_bp.route('/orders')
@customer_required
def orders():
    """
    عرض قائمة طلبات المستخدم
    """
    user_id = session.get('user_id')
    orders = Order.query.filter_by(user_id=user_id).order_by(Order.created_at.desc()).all()
    
    return render_template('customer/orders.html', orders=orders)

@customer_bp.route('/orders/<int:order_id>')
@customer_required
def view_order(order_id):
    """
    عرض تفاصيل طلب محدد
    """
    user_id = session.get('user_id')
    order = Order.query.filter_by(id=order_id, user_id=user_id).first_or_404()
    
    return render_template('customer/order_details.html', order=order)

# العناوين
@customer_bp.route('/addresses')
@customer_required
def addresses():
    """
    عرض قائمة عناوين المستخدم
    """
    user_id = session.get('user_id')
    addresses = Address.query.filter_by(user_id=user_id).all()
    
    return render_template('customer/addresses.html', addresses=addresses)

@customer_bp.route('/addresses/create', methods=['GET', 'POST'])
@customer_required
def create_address():
    """
    إضافة عنوان جديد
    """
    user_id = session.get('user_id')
    
    if request.method == 'POST':
        address_line1 = request.form.get('address_line1')
        address_line2 = request.form.get('address_line2', '')
        city = request.form.get('city')
        state = request.form.get('state')
        postal_code = request.form.get('postal_code')
        country = request.form.get('country')
        is_default = 'is_default' in request.form
        
        if not address_line1 or not city or not state or not postal_code or not country:
            flash('يرجى ملء جميع الحقول المطلوبة', 'danger')
            return render_template('customer/address_form.html', action='create')
        
        # إذا كان العنوان الجديد هو الافتراضي، قم بإلغاء تعيين العناوين الأخرى كافتراضية
        if is_default:
            Address.query.filter_by(user_id=user_id, is_default=True).update({'is_default': False})
        
        # إنشاء عنوان جديد
        new_address = Address(
            user_id=user_id,
            address_line1=address_line1,
            address_line2=address_line2,
            city=city,
            state=state,
            postal_code=postal_code,
            country=country,
            is_default=is_default
        )
        
        db.session.add(new_address)
        db.session.commit()
        
        flash('تم إضافة العنوان بنجاح', 'success')
        return redirect(url_for('customer.addresses'))
    
    return render_template('customer/address_form.html', action='create')

@customer_bp.route('/addresses/<int:address_id>/edit', methods=['GET', 'POST'])
@customer_required
def edit_address(address_id):
    """
    تعديل عنوان موجود
    """
    user_id = session.get('user_id')
    address = Address.query.filter_by(id=address_id, user_id=user_id).first_or_404()
    
    if request.method == 'POST':
        address.address_line1 = request.form.get('address_line1')
        address.address_line2 = request.form.get('address_line2', '')
        address.city = request.form.get('city')
        address.state = request.form.get('state')
        address.postal_code = request.form.get('postal_code')
        address.country = request.form.get('country')
        is_default = 'is_default' in request.form
        
        # إذا كان العنوان المعدل هو الافتراضي، قم بإلغاء تعيين العناوين الأخرى كافتراضية
        if is_default and not address.is_default:
            Address.query.filter_by(user_id=user_id, is_default=True).update({'is_default': False})
        
        address.is_default = is_default
        
        db.session.commit()
        
        flash('تم تحديث العنوان بنجاح', 'success')
        return redirect(url_for('customer.addresses'))
    
    return render_template('customer/address_form.html', action='edit', address=address)

@customer_bp.route('/addresses/<int:address_id>/delete', methods=['POST'])
@customer_required
def delete_address(address_id):
    """
    حذف عنوان
    """
    user_id = session.get('user_id')
    address = Address.query.filter_by(id=address_id, user_id=user_id).first_or_404()
    
    # التحقق من عدم وجود طلبات مرتبطة بالعنوان
    if address.orders:
        flash('لا يمكن حذف العنوان لأنه مرتبط بطلبات', 'danger')
        return redirect(url_for('customer.addresses'))
    
    db.session.delete(address)
    db.session.commit()
    
    flash('تم حذف العنوان بنجاح', 'success')
    return redirect(url_for('customer.addresses'))

# التقييمات
@customer_bp.route('/reviews')
@customer_required
def reviews():
    """
    عرض تقييمات المستخدم
    """
    user_id = session.get('user_id')
    reviews = Review.query.filter_by(user_id=user_id).all()
    
    return render_template('customer/reviews.html', reviews=reviews)

@customer_bp.route('/products/<int:product_id>/review', methods=['POST'])
@customer_required
def add_review(product_id):
    """
    إضافة تقييم لمنتج
    """
    user_id = session.get('user_id')
    product = Product.query.get_or_404(product_id)
    
    # التحقق مما إذا كان المستخدم قد اشترى المنتج
    has_purchased = OrderItem.query.join(Order).filter(
        Order.user_id == user_id,
        OrderItem.product_id == product_id
    ).first()
    
    if not has_purchased:
        flash('يمكنك فقط تقييم المنتجات التي قمت بشرائها', 'danger')
        return redirect(url_for('customer.product_details', product_id=product_id))
    
    # التحقق مما إذا كان المستخدم قد قام بتقييم المنتج من قبل
    existing_review = Review.query.filter_by(user_id=user_id, product_id=product_id).first()
    
    rating = int(request.form.get('rating', 5))
    comment = request.form.get('comment', '')
    
    if existing_review:
        # تحديث التقييم الموجود
        existing_review.rating = rating
        existing_review.comment = comment
        existing_review.is_approved = False  # إعادة التقييم للمراجعة
        flash('تم تحديث تقييمك بنجاح وسيتم مراجعته', 'success')
    else:
        # إنشاء تقييم جديد
        new_review = Review(
            user_id=user_id,
            product_id=product_id,
            rating=rating,
            comment=comment,
            is_approved=False  # يتطلب موافقة المدير
        )
        db.session.add(new_review)
        flash('تم إضافة تقييمك بنجاح وسيتم مراجعته', 'success')
    
    db.session.commit()
    return redirect(url_for('customer.product_details', product_id=product_id))

@customer_bp.route('/reviews/<int:review_id>/edit', methods=['GET', 'POST'])
@customer_required
def edit_review(review_id):
    """
    تعديل تقييم
    """
    user_id = session.get('user_id')
    review = Review.query.filter_by(id=review_id, user_id=user_id).first_or_404()
    
    if request.method == 'POST':
        review.rating = int(request.form.get('rating', 5))
        review.comment = request.form.get('comment', '')
        review.is_approved = False  # إعادة التقييم للمراجعة
        
        db.session.commit()
        
        flash('تم تحديث التقييم بنجاح وسيتم مراجعته', 'success')
        return redirect(url_for('customer.reviews'))
    
    return render_template('customer/review_form.html', review=review)

@customer_bp.route('/reviews/<int:review_id>/delete', methods=['POST'])
@customer_required
def delete_review(review_id):
    """
    حذف تقييم
    """
    user_id = session.get('user_id')
    review = Review.query.filter_by(id=review_id, user_id=user_id).first_or_404()
    
    db.session.delete(review)
    db.session.commit()
    
    flash('تم حذف التقييم بنجاح', 'success')
    return redirect(url_for('customer.reviews'))

# الإشعارات
@customer_bp.route('/notifications')
@customer_required
def notifications():
    """
    عرض إشعارات المستخدم
    """
    user_id = session.get('user_id')
    notifications = Notification.query.filter_by(user_id=user_id).order_by(Notification.created_at.desc()).all()
    
    return render_template('customer/notifications.html', notifications=notifications)

# المفضلة
@customer_bp.route('/wishlist')
@customer_required
def wishlist():
    """
    عرض قائمة المفضلة
    """
    user_id = session.get('user_id')
    # تنفيذ هذا المسار حسب نموذج المفضلة في قاعدة البيانات
    
    return render_template('customer/wishlist.html')
