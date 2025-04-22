from flask import render_template, flash, redirect, url_for, request, jsonify, g
from flask_login import login_user, logout_user, current_user, login_required
from urllib.parse import urlparse
from flask_babel import _, get_locale

from app import app, db, babel
from models import User, UserProfile, Food, Meal, MealItem, Achievement, UserAchievement
from utils import (
    calculate_bmi, get_bmi_category, calculate_daily_calorie_needs,
    get_daily_meals, calculate_daily_nutrition, get_weekly_nutrition_data,
    search_food_in_csv, import_foods_from_csv, get_food_data_from_csv,
    get_meal_type_distribution
)

import json
import os
from datetime import datetime, date, timedelta
from werkzeug.utils import secure_filename

# Function to get the current locale
def get_app_locale():
    if current_user.is_authenticated:
        return current_user.locale
    return request.accept_languages.best_match(['en', 'es', 'hi', 'kn', 'ta', 'te', 'mr', 'gu'])

@app.before_request
def before_request():
    g.locale = str(get_locale())

@app.context_processor
def inject_locale():
    return dict(locale=g.locale)

@app.template_filter('attr_list')
def attr_list_filter(obj):
    """Returns a list of attributes available on an object"""
    return [attr for attr in dir(obj) if not attr.startswith('_')]

@app.route('/')
@app.route('/index')
def index():
    """Home page / dashboard"""
    if current_user.is_authenticated:
        # Get user's daily meals and nutrition
        meals = get_daily_meals(current_user.id)
        daily_nutrition = calculate_daily_nutrition(meals)
        
        # Get weekly nutrition data for charts
        weekly_data = get_weekly_nutrition_data(current_user.id)
        
        return render_template('index.html', 
                             meals=meals, 
                             daily_nutrition=daily_nutrition,
                             weekly_data=json.dumps(weekly_data))
    else:
        return render_template('landing.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login page"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember_me = 'remember_me' in request.form
        
        user = User.query.filter_by(username=username).first()
        
        if user is None or not user.check_password(password):
            flash(_('Invalid username or password'), 'danger')
            return redirect(url_for('login'))
            
        login_user(user, remember=remember_me)
        
        # Redirect to requested page or home
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('index')
            
        return redirect(next_page)
        
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration page"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate form data
        if password != confirm_password:
            flash(_('Passwords do not match'), 'danger')
            return redirect(url_for('register'))
            
        if User.query.filter_by(username=username).first():
            flash(_('Username already exists'), 'danger')
            return redirect(url_for('register'))
            
        if User.query.filter_by(email=email).first():
            flash(_('Email already exists'), 'danger')
            return redirect(url_for('register'))
            
        # Create new user
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        # Create empty user profile
        profile = UserProfile(user_id=user.id)
        db.session.add(profile)
        db.session.commit()
        
        flash(_('Registration successful! Please complete your profile.'), 'success')
        login_user(user)
        return redirect(url_for('profile'))
        
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    """Log out the current user"""
    logout_user()
    return redirect(url_for('index'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile page"""
    profile = UserProfile.query.filter_by(user_id=current_user.id).first_or_404()
    
    if request.method == 'POST':
        # Update profile information
        profile.height = float(request.form.get('height', 0))
        profile.weight = float(request.form.get('weight', 0))
        profile.age = int(request.form.get('age', 0))
        profile.gender = request.form.get('gender')
        profile.activity_level = request.form.get('activity_level')
        
        # Calculate target nutrition values
        if all([profile.height, profile.weight, profile.age, profile.gender, profile.activity_level]):
            # Assume 'maintenance' as default health goal if not specified
            health_goal = request.form.get('health_goal', 'maintenance')
            
            profile.target_calories = calculate_daily_calorie_needs(
                profile.weight, profile.height, profile.age, profile.gender, profile.activity_level, health_goal
            )
            
            # Set macronutrient targets (rough estimates)
            profile.target_protein = int(profile.weight * 1.6)  # ~1.6g per kg body weight
            profile.target_carbs = int(profile.target_calories * 0.5 / 4)  # 50% of calories, 4 cals per gram
            profile.target_fat = int(profile.target_calories * 0.25 / 9)  # 25% of calories, 9 cals per gram
        
        # Update user language preference
        current_user.locale = request.form.get('locale', 'en')
        
        db.session.commit()
        flash(_('Profile updated successfully!'), 'success')
        return redirect(url_for('profile'))
    
    # Calculate BMI if height and weight are available
    bmi = None
    bmi_category = None
    if profile.height and profile.weight:
        bmi = calculate_bmi(profile.weight, profile.height)
        bmi_category = get_bmi_category(bmi)
    
    return render_template('profile.html', profile=profile, bmi=bmi, bmi_category=bmi_category)

@app.route('/menu')
@login_required
def menu():
    """Cafeteria menu page with portion selection"""
    # Import foods from CSV if none exist in the database
    if Food.query.count() < 10:  # Arbitrary small number to check
        import_foods_from_csv()
    
    # Get all foods from database
    foods = Food.query.all()
    
    # Get food data directly from CSV for table display
    csv_food_data = get_food_data_from_csv()
    
    # Group CSV food data into categories
    beverages = []
    main_courses = []
    sides = []
    snacks = []
    
    for item in csv_food_data:
        if 'tea' in item['Dish Name'].lower() or 'coffee' in item['Dish Name'].lower() or 'drink' in item['Dish Name'].lower() or 'juice' in item['Dish Name'].lower() or 'punch' in item['Dish Name'].lower() or 'lemonade' in item['Dish Name'].lower():
            beverages.append(item)
        elif 'rice' in item['Dish Name'].lower() or 'curry' in item['Dish Name'].lower() or 'dal' in item['Dish Name'].lower() or 'meal' in item['Dish Name'].lower():
            main_courses.append(item)
        elif 'bread' in item['Dish Name'].lower() or 'roti' in item['Dish Name'].lower() or 'naan' in item['Dish Name'].lower():
            sides.append(item)
        else:
            snacks.append(item)
    
    return render_template('menu.html', 
                          foods=foods, 
                          csv_food_data=csv_food_data, 
                          beverages=beverages,
                          main_courses=main_courses,
                          sides=sides,
                          snacks=snacks)

@app.route('/custom-entry', methods=['GET', 'POST'])
@login_required
def custom_entry():
    """Custom food entry page"""
    if request.method == 'POST':
        name = request.form.get('name')
        calories = int(request.form.get('calories', 0))
        protein = float(request.form.get('protein', 0))
        carbs = float(request.form.get('carbs', 0))
        fat = float(request.form.get('fat', 0))
        fiber = float(request.form.get('fiber', 0))
        category = request.form.get('category', 'other')
        
        food = Food(
            name=name,
            calories=calories,
            protein=protein,
            carbs=carbs,
            fat=fat,
            fiber=fiber,
            category=category,
            is_custom=True,
            created_by=current_user.id
        )
        
        db.session.add(food)
        db.session.commit()
        
        flash(_('Custom food added successfully!'), 'success')
        return redirect(url_for('menu'))
        
    return render_template('custom_entry.html')

@app.route('/add-meal', methods=['POST'])
@login_required
def add_meal():
    """Add a meal with selected items"""
    food_ids = request.form.getlist('food_id')
    meal_type = request.form.get('meal_type', 'snack')
    
    if not food_ids:
        flash(_('Please select at least one food item'), 'danger')
        return redirect(url_for('menu'))
    
    # Create new meal
    meal = Meal(
        user_id=current_user.id,
        meal_type=meal_type,
        date=datetime.utcnow().date(),
        time=datetime.utcnow().time()
    )
    db.session.add(meal)
    db.session.flush()  # Get meal ID
    
    # Add meal items
    for food_id in food_ids:
        portion_size = request.form.get(f'portion_size_{food_id}', 'medium')
        meal_item = MealItem(
            meal_id=meal.id,
            food_id=int(food_id),
            portion_size=portion_size
        )
        db.session.add(meal_item)
    
    db.session.commit()
    
    # Check for achievements
    check_achievements(current_user.id)
    
    flash(_('Meal added successfully!'), 'success')
    return redirect(url_for('index'))

@app.route('/history')
@login_required
def history():
    """Nutrition history page"""
    # Default to showing the past 7 days
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=6)
    
    # Allow custom date range
    if request.args.get('start_date'):
        start_date = datetime.strptime(request.args.get('start_date'), '%Y-%m-%d').date()
    if request.args.get('end_date'):
        end_date = datetime.strptime(request.args.get('end_date'), '%Y-%m-%d').date()
    
    # Get meals in date range
    meals = Meal.query.filter(
        Meal.user_id == current_user.id,
        Meal.date >= start_date,
        Meal.date <= end_date
    ).order_by(Meal.date.desc(), Meal.time.desc()).all()
    
    # Get nutrition data for charts
    weekly_data = get_weekly_nutrition_data(current_user.id)
    
    return render_template('history.html', 
                         meals=meals,
                         start_date=start_date,
                         end_date=end_date,
                         weekly_data=json.dumps(weekly_data))

@app.route('/nutrition-data')
@login_required
def nutrition_data():
    """API endpoint for nutrition chart data"""
    weekly_data = get_weekly_nutrition_data(current_user.id)
    return jsonify(weekly_data)

@app.route('/log-meal', methods=['GET', 'POST'])
@login_required
def log_meal():
    """Log a meal with details and optional photo"""
    
    if request.method == 'POST':
        # Process the form submission
        meal_name = request.form.get('custom_meal_name')
        calories = float(request.form.get('custom_meal_calories', 0))
        proteins = float(request.form.get('custom_meal_proteins', 0))
        carbs = float(request.form.get('custom_meal_carbs', 0))
        fats = float(request.form.get('custom_meal_fats', 0))
        portion_size = request.form.get('portion_size', 'medium')
        meal_type = request.form.get('meal_type', 'snack')
        notes = request.form.get('notes', '')
        
        # Create a new meal
        meal = Meal(
            user_id=current_user.id,
            date=datetime.utcnow().date(),
            time=datetime.utcnow().time(),
            meal_type=meal_type
        )
        db.session.add(meal)
        db.session.flush()  # Get meal ID
        
        # Check if food already exists
        existing_food = Food.query.filter_by(name=meal_name).first()
        
        if existing_food:
            food = existing_food
        else:
            # Create new food
            food = Food(
                name=meal_name,
                calories=calories,
                protein=proteins,
                carbs=carbs,
                fat=fats,
                is_custom=True,
                created_by=current_user.id
            )
            db.session.add(food)
            db.session.flush()  # Get food ID
        
        # Create meal item
        meal_item = MealItem(
            meal_id=meal.id,
            food_id=food.id,
            portion_size=portion_size
        )
        
        # Handle file upload if provided
        meal_image = request.files.get('meal_image')
        if meal_image and meal_image.filename:
            try:
                # Ensure upload directory exists
                upload_folder = os.path.join('static', 'uploads')
                os.makedirs(upload_folder, exist_ok=True)
                
                # Save the file with a secure filename
                filename = secure_filename(f"meal_{current_user.id}_{int(datetime.utcnow().timestamp())}.jpg")
                filepath = os.path.join(upload_folder, filename)
                meal_image.save(filepath)
                
                # If the meal model has an image_path field, set it
                if hasattr(meal, 'image_path'):
                    meal.image_path = os.path.join('uploads', filename)
            except Exception as e:
                app.logger.error(f"Error saving image: {str(e)}")
                flash(_('Error uploading image, but meal was logged'), 'warning')
        
        # Save changes to database
        db.session.add(meal_item)
        db.session.commit()
        
        # Check for achievements
        check_achievements(current_user.id)
        
        flash(_('Meal logged successfully!'), 'success')
        return redirect(url_for('index'))
    
    # GET request - render the form
    # Handle search queries for foods
    search_term = request.args.get('search_term', '')
    search_results = []
    csv_search_results = []
    
    if search_term:
        # Search in database
        search_results = Food.query.filter(Food.name.ilike(f'%{search_term}%')).all()
        
        # Search in CSV
        csv_search_results = search_food_in_csv(search_term, g.locale)
    
    # Prefill form from query params (from CSV item selection)
    custom_meal_name = request.args.get('custom_meal_name', '')
    custom_meal_calories = request.args.get('custom_meal_calories', 0)
    custom_meal_proteins = request.args.get('custom_meal_proteins', 0)
    custom_meal_carbs = request.args.get('custom_meal_carbs', 0)
    custom_meal_fats = request.args.get('custom_meal_fats', 0)
    
    # Create a dictionary to represent the form data
    form = {
        'custom_meal_name': {'data': custom_meal_name},
        'custom_meal_calories': {'data': custom_meal_calories},
        'custom_meal_proteins': {'data': custom_meal_proteins},
        'custom_meal_carbs': {'data': custom_meal_carbs},
        'custom_meal_fats': {'data': custom_meal_fats},
        'portion_size': {'data': 'medium'},
        'meal_type': {'data': 'lunch'},
        'notes': {'data': ''}
    }
    
    return render_template('log_meal.html',
                          title=_('Log a Meal'),
                          form=form,
                          search_results=search_results,
                          csv_search_results=csv_search_results)

@app.route('/food-search')
@login_required
def food_search():
    """API endpoint for food search"""
    query = request.args.get('q', '')
    
    if not query or len(query) < 2:
        return jsonify([])
    
    # Search in database
    db_results = Food.query.filter(Food.name.ilike(f'%{query}%')).all()
    db_foods = [{
        'id': food.id,
        'name': food.get_name(g.locale),
        'calories': food.calories,
        'protein': food.protein,
        'carbs': food.carbs,
        'fat': food.fat,
        'fiber': food.fiber,
        'category': food.category,
        'source': 'db'
    } for food in db_results]
    
    # Search in CSV
    csv_results = search_food_in_csv(query, g.locale)
    csv_foods = [{
        'name': item['Dish Name'],
        'calories': float(item['Calories (kcal)']),
        'protein': float(item['Protein (g)']),
        'carbs': float(item['Carbohydrate (g)']),
        'fat': float(item['Fats (g)']),
        'fiber': float(item['Fibre (g)']) if item['Fibre (g)'] else 0.0,
        'source': 'csv'
    } for item in csv_results]
    
    # Combine results, prioritizing database entries
    all_results = db_foods + csv_foods
    return jsonify(all_results[:10])  # Limit to 10 results

@app.route('/set-language/<language>')
@login_required
def set_language(language):
    """Set user language preference"""
    supported_languages = ['en', 'es', 'hi', 'kn', 'ta', 'te', 'mr', 'gu']
    
    if language in supported_languages:
        current_user.locale = language
        db.session.commit()
        flash(_('Language updated successfully!'), 'success')
    
    # Redirect back to previous page
    next_page = request.referrer or url_for('index')
    return redirect(next_page)

@app.route('/achievements')
@login_required
def achievements():
    """View user achievements"""
    user_achievements = UserAchievement.query.filter_by(user_id=current_user.id).all()
    earned_ids = [ua.achievement_id for ua in user_achievements]
    
    all_achievements = Achievement.query.all()
    
    return render_template('achievements.html', 
                           user_achievements=user_achievements,
                           all_achievements=all_achievements,
                           earned_ids=earned_ids)

def check_achievements(user_id):
    """Check and award achievements for a user"""
    # Count total meals logged
    meal_count = Meal.query.filter_by(user_id=user_id).count()
    
    # Check for meal counting achievements
    achievements_to_check = [
        {'id': 1, 'name': 'First Meal', 'description': 'Log your first meal', 'requirement': 1},
        {'id': 2, 'name': 'Regular Tracker', 'description': 'Log 10 meals', 'requirement': 10},
        {'id': 3, 'name': 'Committed Tracker', 'description': 'Log 30 meals', 'requirement': 30},
        {'id': 4, 'name': 'Nutrition Master', 'description': 'Log 100 meals', 'requirement': 100}
    ]
    
    for achievement_data in achievements_to_check:
        if meal_count >= achievement_data['requirement']:
            # Check if user already has this achievement
            existing = UserAchievement.query.filter_by(
                user_id=user_id, 
                achievement_id=achievement_data['id']
            ).first()
            
            if not existing:
                # Look up the achievement or create it if it doesn't exist
                achievement = Achievement.query.get(achievement_data['id'])
                if not achievement:
                    achievement = Achievement(
                        id=achievement_data['id'],
                        name=achievement_data['name'],
                        description=achievement_data['description'],
                        icon='fa-utensils',
                        requirement_type='meals_logged',
                        requirement_value=achievement_data['requirement']
                    )
                    db.session.add(achievement)
                
                # Award the achievement
                user_achievement = UserAchievement(
                    user_id=user_id,
                    achievement_id=achievement_data['id']
                )
                db.session.add(user_achievement)
                db.session.commit()
                
                flash(_('Achievement unlocked: %(name)s!', name=achievement_data['name']), 'success')

@app.context_processor
def inject_current_year():
    return {'current_year': datetime.utcnow().year}

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500