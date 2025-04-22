from flask import render_template, redirect, url_for, flash, request, session, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.urls import urlsplit
from werkzeug.utils import secure_filename
from flask_babel import gettext as _
import datetime
import os
import time

from app import app, db, babel
from models import User, UserProfile, Meal, MealLog
from forms import (
    LoginForm, RegistrationForm, UserProfileForm, 
    LogMealForm, MealSearchForm, AdminMealForm
)
from utils import (
    calculate_bmi, calculate_daily_calorie_needs, get_bmi_category,
    get_daily_meals, calculate_daily_nutrition, get_weekly_nutrition_data,
    get_meal_type_distribution, get_food_data_from_csv
)

# Language selection
@app.route('/set_language/<lang>')
def set_language(lang):
    session['language'] = lang
    # If user is logged in, update their preference
    if current_user.is_authenticated and current_user.profile:
        current_user.profile.preferred_language = lang
        db.session.commit()
    # Redirect back to the page they came from
    next_page = request.args.get('next') or request.referrer or url_for('index')
    return redirect(next_page)

# Home page
@app.route('/')
def index():
    return render_template('index.html', title=_('Welcome to SmartCafé'))

# User Authentication
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash(_('Invalid email or password'), 'danger')
            return redirect(url_for('login'))
        
        login_user(user, remember=form.remember_me.data)
        
        # Set language preference
        if user.profile and user.profile.preferred_language:
            session['language'] = user.profile.preferred_language
        
        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('dashboard')
        return redirect(next_page)
    
    return render_template('login.html', title=_('Sign In'), form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        
        flash(_('Congratulations, you are now registered! Please complete your profile.'), 'success')
        login_user(user)
        return redirect(url_for('profile'))
    
    return render_template('signup.html', title=_('Register'), form=form)

# User Profile
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    # Check if user has a profile, create one if not
    if not current_user.profile:
        profile = UserProfile(user_id=current_user.id)
        db.session.add(profile)
        db.session.commit()
    
    form = UserProfileForm(obj=current_user.profile)
    
    if form.validate_on_submit():
        form.populate_obj(current_user.profile)
        
        # Calculate BMI and daily calorie needs
        current_user.profile.calculate_bmi()
        current_user.profile.calculate_daily_calorie_needs()
        
        # Update language preference
        session['language'] = form.preferred_language.data
        
        db.session.commit()
        flash(_('Your profile has been updated!'), 'success')
        return redirect(url_for('dashboard'))
    
    # Pre-populate form with current data
    if request.method == 'GET' and current_user.profile:
        form.age.data = current_user.profile.age
        form.gender.data = current_user.profile.gender
        form.weight.data = current_user.profile.weight
        form.height.data = current_user.profile.height
        form.activity_level.data = current_user.profile.activity_level
        form.health_goal.data = current_user.profile.health_goal
        form.preferred_language.data = current_user.profile.preferred_language
    
    bmi = None
    bmi_category = None
    if current_user.profile and current_user.profile.bmi:
        bmi = current_user.profile.bmi
        bmi_category = get_bmi_category(bmi)
    
    return render_template('profile.html', title=_('Your Profile'), 
                          form=form, bmi=bmi, bmi_category=bmi_category)

# Dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    # Check if profile is complete
    if not current_user.profile or not current_user.profile.age:
        flash(_('Please complete your profile first.'), 'info')
        return redirect(url_for('profile'))
    
    # Get today's date and meals
    today = datetime.datetime.now().date()
    meals = get_daily_meals(current_user.id, today)
    
    # Calculate daily nutrition totals
    nutrition = calculate_daily_nutrition(meals)
    
    # Get weekly data for charts
    weekly_data = get_weekly_nutrition_data(current_user.id)
    
    # Get meal type distribution
    meal_distribution = get_meal_type_distribution(current_user.id, today)
    
    return render_template('dashboard.html', title=_('Dashboard'),
                          profile=current_user.profile,
                          meals=meals,
                          nutrition=nutrition,
                          weekly_data=weekly_data,
                          meal_distribution=meal_distribution,
                          today=today.strftime('%Y-%m-%d'))

# Cafeteria Menu
@app.route('/menu')
@login_required
def menu():
    # Get food data from CSV
    csv_food_data = get_food_data_from_csv()
    
    # Get meals from database
    cafeteria_items = Meal.query.filter_by(is_cafeteria_item=True).all()
    
    return render_template('menu.html', title=_('Cafeteria Menu'),
                          meals=cafeteria_items,
                          csv_food_data=csv_food_data)

# Log CSV Meal (API endpoint)
@app.route('/log-meal-csv', methods=['POST'])
@login_required
def log_meal_csv():
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Create a new meal log
        meal_log = MealLog(
            user_id=current_user.id,
            custom_meal_name=request.form.get('custom_meal_name'),
            custom_meal_calories=float(request.form.get('custom_meal_calories')),
            custom_meal_proteins=float(request.form.get('custom_meal_proteins')),
            custom_meal_carbs=float(request.form.get('custom_meal_carbs')),
            custom_meal_fats=float(request.form.get('custom_meal_fats')),
            portion_size=request.form.get('portion_size', 'medium'),
            meal_type=request.form.get('meal_type', 'snack'),
            meal_time=datetime.datetime.now()
        )
        
        db.session.add(meal_log)
        db.session.commit()
        
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'message': 'Invalid request'})

# Log Meal
@app.route('/log-meal', methods=['GET', 'POST'])
@login_required
def log_meal():
    form = LogMealForm()
    search_form = MealSearchForm()
    
    # Get meal_id from query parameter if available
    meal_id = request.args.get('meal_id', None)
    
    # Handle pre-filled data from CSV food items
    if request.method == 'GET':
        custom_meal_name = request.args.get('custom_meal_name')
        if custom_meal_name:
            form.custom_meal_name.data = custom_meal_name
            form.custom_meal_calories.data = float(request.args.get('custom_meal_calories', 0))
            form.custom_meal_carbs.data = float(request.args.get('custom_meal_carbs', 0))
            form.custom_meal_proteins.data = float(request.args.get('custom_meal_proteins', 0))
            form.custom_meal_fats.data = float(request.args.get('custom_meal_fats', 0))
    
    if meal_id:
        meal = Meal.query.get(meal_id)
        if meal:
            form.meal_id.data = meal_id
    
    if form.validate_on_submit():
        meal_log = MealLog(user_id=current_user.id)
        
        # Check if logging an existing meal or custom meal
        if form.meal_id.data:
            meal_log.meal_id = form.meal_id.data
        else:
            meal_log.custom_meal_name = form.custom_meal_name.data
            meal_log.custom_meal_calories = form.custom_meal_calories.data
            meal_log.custom_meal_proteins = form.custom_meal_proteins.data
            meal_log.custom_meal_carbs = form.custom_meal_carbs.data
            meal_log.custom_meal_fats = form.custom_meal_fats.data
        
        meal_log.portion_size = form.portion_size.data
        meal_log.meal_type = form.meal_type.data
        meal_log.notes = form.notes.data
        meal_log.meal_time = datetime.datetime.now()
        
        # Handle meal image upload if provided
        if form.meal_image.data:
            try:
                # Save the image
                filename = secure_filename(f"meal_{current_user.id}_{int(time.time())}.jpg")
                image_path = os.path.join(app.config.get('UPLOAD_FOLDER', 'static/uploads'), filename)
                
                # Ensure upload directory exists
                os.makedirs(os.path.dirname(image_path), exist_ok=True)
                
                # Save the file
                form.meal_image.data.save(image_path)
                
                # Save path to database
                meal_log.image_path = os.path.join('uploads', filename)
            except Exception as e:
                app.logger.error(f"Error saving meal image: {str(e)}")
                # Continue without image if there's an error
                flash(_('Failed to save meal image, but meal was logged.'), 'warning')
        
        db.session.add(meal_log)
        db.session.commit()
        
        flash(_('Meal logged successfully!'), 'success')
        return redirect(url_for('dashboard'))
    
    # Handle meal search
    search_results = []
    csv_search_results = []
    
    if search_form.validate_on_submit():
        search_term = search_form.search_term.data
        if search_term:
            search_term = search_term.lower()
        else:
            search_term = ""
        lang = session.get('language', 'en')
        
        # Search in database meals
        if lang == 'en':
            search_results = Meal.query.filter(Meal.name_en.contains(search_term)).all()
        elif lang == 'hi':
            search_results = Meal.query.filter(
                (Meal.name_hi.contains(search_term)) | (Meal.name_en.contains(search_term))
            ).all()
        elif lang == 'kn':
            search_results = Meal.query.filter(
                (Meal.name_kn.contains(search_term)) | (Meal.name_en.contains(search_term))
            ).all()
        elif lang == 'ta':
            search_results = Meal.query.filter(
                (Meal.name_ta.contains(search_term)) | (Meal.name_en.contains(search_term))
            ).all()
        elif lang == 'te':
            search_results = Meal.query.filter(
                (Meal.name_te.contains(search_term)) | (Meal.name_en.contains(search_term))
            ).all()
        elif lang == 'mr':
            search_results = Meal.query.filter(
                (Meal.name_mr.contains(search_term)) | (Meal.name_en.contains(search_term))
            ).all()
        elif lang == 'gu':
            search_results = Meal.query.filter(
                (Meal.name_gu.contains(search_term)) | (Meal.name_en.contains(search_term))
            ).all()
            
        # Search in CSV food data
        csv_food_data = get_food_data_from_csv()
        for item in csv_food_data:
            if search_term in item['Dish Name'].lower():
                csv_search_results.append(item)
    
    return render_template('log_meal.html', title=_('Log a Meal'),
                          form=form, search_form=search_form,
                          search_results=search_results,
                          csv_search_results=csv_search_results,
                          selected_meal_id=meal_id)

# Admin Routes
@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    if not current_user.is_admin:
        flash(_('You do not have permission to access this page.'), 'danger')
        return redirect(url_for('dashboard'))
    
    form = AdminMealForm()
    
    # Handle edit meal request
    meal_id = request.args.get('edit', None)
    meal = None
    if meal_id:
        meal = Meal.query.get(meal_id)
        if meal and request.method == 'GET':
            # Populate form with meal data
            form.name_en.data = meal.name_en
            form.name_hi.data = meal.name_hi
            form.name_kn.data = meal.name_kn
            form.name_ta.data = meal.name_ta
            form.name_te.data = meal.name_te
            form.name_mr.data = meal.name_mr
            form.name_gu.data = meal.name_gu
            form.calories.data = meal.calories
            form.proteins.data = meal.proteins
            form.carbs.data = meal.carbs
            form.fats.data = meal.fats
            form.fiber.data = meal.fiber
            form.portion_small.data = meal.portion_small
            form.portion_medium.data = meal.portion_medium
            form.portion_large.data = meal.portion_large
            form.is_cafeteria_item.data = meal.is_cafeteria_item
            form.tags.data = meal.tags
            form.image_path.data = meal.image_path
    
    if form.validate_on_submit():
        if meal_id:
            # Update existing meal
            meal.name_en = form.name_en.data
            meal.name_hi = form.name_hi.data
            meal.name_kn = form.name_kn.data
            meal.name_ta = form.name_ta.data
            meal.name_te = form.name_te.data
            meal.name_mr = form.name_mr.data
            meal.name_gu = form.name_gu.data
            meal.calories = form.calories.data
            meal.proteins = form.proteins.data
            meal.carbs = form.carbs.data
            meal.fats = form.fats.data
            meal.fiber = form.fiber.data
            meal.portion_small = form.portion_small.data
            meal.portion_medium = form.portion_medium.data
            meal.portion_large = form.portion_large.data
            meal.is_cafeteria_item = form.is_cafeteria_item.data
            meal.tags = form.tags.data
            meal.image_path = form.image_path.data
            flash(_('Meal updated successfully!'), 'success')
        else:
            # Create new meal
            new_meal = Meal(
                name_en=form.name_en.data,
                name_hi=form.name_hi.data,
                name_kn=form.name_kn.data,
                name_ta=form.name_ta.data,
                name_te=form.name_te.data,
                name_mr=form.name_mr.data,
                name_gu=form.name_gu.data,
                calories=form.calories.data,
                proteins=form.proteins.data,
                carbs=form.carbs.data,
                fats=form.fats.data,
                fiber=form.fiber.data,
                portion_small=form.portion_small.data,
                portion_medium=form.portion_medium.data,
                portion_large=form.portion_large.data,
                is_cafeteria_item=form.is_cafeteria_item.data,
                tags=form.tags.data,
                image_path=form.image_path.data,
                created_by=current_user.id
            )
            db.session.add(new_meal)
            flash(_('New meal added successfully!'), 'success')
        
        db.session.commit()
        return redirect(url_for('admin'))
    
    # Get all meals for the admin view
    meals = Meal.query.order_by(Meal.name_en).all()
    
    return render_template('admin.html', title=_('Admin Panel'),
                          form=form, meals=meals, edit_id=meal_id)

# API endpoint for getting meal data
@app.route('/api/meal/<int:meal_id>')
@login_required
def get_meal_data(meal_id):
    meal = Meal.query.get_or_404(meal_id)
    lang = session.get('language', 'en')
    
    return jsonify({
        'id': meal.id,
        'name': meal.get_name(lang),
        'calories': meal.calories,
        'proteins': meal.proteins,
        'carbs': meal.carbs,
        'fats': meal.fats,
        'fiber': meal.fiber,
        'portion_small': meal.portion_small,
        'portion_medium': meal.portion_medium,
        'portion_large': meal.portion_large,
        'image_path': meal.image_path
    })

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

# Seed some initial data (for development)
@app.route('/seed', methods=['GET'])
def seed_data():
    # Only accessible in development
    if app.config.get('ENV', 'production') != 'development':
        return redirect(url_for('index'))
    
    # Create admin user if it doesn't exist
    admin = User.query.filter_by(email='admin@smartcafe.com').first()
    if not admin:
        admin = User(username='admin', email='admin@smartcafe.com', is_admin=True)
        admin.set_password('adminpass')
        db.session.add(admin)
        
        # Create admin profile
        admin_profile = UserProfile(
            user_id=1,
            age=30,
            gender='male',
            weight=70,
            height=175,
            activity_level='moderate',
            health_goal='maintenance',
            preferred_language='en'
        )
        db.session.add(admin_profile)
    
    # Add some sample meals if they don't exist
    meals = [
        {
            'name_en': 'Chicken Biryani',
            'name_hi': 'चिकन बिरयानी',
            'calories': 250,
            'proteins': 15,
            'carbs': 30,
            'fats': 8,
            'fiber': 2,
            'portion_small': 150,
            'portion_medium': 300,
            'portion_large': 450,
            'is_cafeteria_item': True,
            'tags': 'rice,chicken,spicy,indian',
            'image_path': 'https://source.unsplash.com/random/300x200/?biryani'
        },
        {
            'name_en': 'Veggie Salad',
            'name_hi': 'सब्जी सलाद',
            'calories': 120,
            'proteins': 3,
            'carbs': 10,
            'fats': 7,
            'fiber': 5,
            'portion_small': 100,
            'portion_medium': 200,
            'portion_large': 300,
            'is_cafeteria_item': True,
            'tags': 'salad,vegetarian,healthy,low-calorie',
            'image_path': 'https://source.unsplash.com/random/300x200/?salad'
        },
        {
            'name_en': 'Masala Dosa',
            'name_hi': 'मसाला डोसा',
            'name_kn': 'ಮಸಾಲ ದೋಸೆ',
            'calories': 180,
            'proteins': 5,
            'carbs': 25,
            'fats': 6,
            'fiber': 3,
            'portion_small': 120,
            'portion_medium': 240,
            'portion_large': 360,
            'is_cafeteria_item': True,
            'tags': 'breakfast,south-indian,vegetarian',
            'image_path': 'https://source.unsplash.com/random/300x200/?dosa'
        }
    ]
    
    for meal_data in meals:
        meal = Meal.query.filter_by(name_en=meal_data['name_en']).first()
        if not meal:
            meal = Meal(**meal_data)
            db.session.add(meal)
    
    db.session.commit()
    flash(_('Sample data has been seeded successfully!'), 'success')
    return redirect(url_for('index'))

# Add current_year to all templates
@app.context_processor
def inject_current_year():
    return {'current_year': datetime.datetime.now().year}
