import csv
import os
import math
from datetime import datetime, timedelta
from models import Food, Meal, MealItem
from app import db

def get_food_data_from_csv():
    """Read food data from CSV file"""
    food_data = []
    csv_path = os.path.join(os.path.dirname(__file__), 'food_data.csv')
    
    if os.path.exists(csv_path):
        with open(csv_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                food_data.append(row)
    
    return food_data

def search_food_in_csv(query, lang='en'):
    """Search for food items in the CSV file based on a query"""
    results = []
    csv_path = os.path.join(os.path.dirname(__file__), 'food_data.csv')
    
    if not os.path.exists(csv_path):
        return results
    
    with open(csv_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            # Check name in English
            if query.lower() in row['Dish Name'].lower():
                results.append(row)
            # Check name in the specified language if available
            elif lang != 'en' and f'name_{lang}' in row and row[f'name_{lang}'] and query.lower() in row[f'name_{lang}'].lower():
                results.append(row)
    
    return results

def import_foods_from_csv():
    """Import foods from CSV into the database"""
    food_data = get_food_data_from_csv()
    count = 0
    
    for item in food_data:
        try:
            # Check if food already exists by name
            if 'Dish Name' not in item or not item['Dish Name']:
                continue
                
            existing_food = Food.query.filter_by(name=item['Dish Name']).first()
            if not existing_food:
                # Safe conversion of values with defaults if missing or invalid
                try:
                    calories = float(item.get('Calories (kcal)', 0)) if item.get('Calories (kcal)') else 0
                except (ValueError, TypeError):
                    calories = 0
                    
                try:
                    protein = float(item.get('Protein (g)', 0)) if item.get('Protein (g)') else 0
                except (ValueError, TypeError):
                    protein = 0
                    
                try:
                    carbs = float(item.get('Carbohydrate (g)', 0)) if item.get('Carbohydrate (g)') else 0
                except (ValueError, TypeError):
                    carbs = 0
                    
                try:
                    fat = float(item.get('Fats (g)', 0)) if item.get('Fats (g)') else 0
                except (ValueError, TypeError):
                    fat = 0
                    
                try:
                    fiber = float(item.get('Fibre (g)', 0)) if item.get('Fibre (g)') else 0
                except (ValueError, TypeError):
                    fiber = 0
                
                food = Food(
                    name=item['Dish Name'],
                    calories=calories,
                    protein=protein,
                    carbs=carbs,
                    fat=fat,
                    fiber=fiber,
                    category='other',  # Default category
                    is_custom=False
                )
                
                # Add multilingual names if available
                for lang in ['hi', 'kn', 'ta', 'te', 'mr', 'gu']:
                    lang_key = f'name_{lang}'
                    if lang_key in item and item[lang_key]:
                        setattr(food, lang_key, item[lang_key])
                
                db.session.add(food)
                count += 1
        except Exception as e:
            print(f"Error importing food item: {str(e)}")
    
    db.session.commit()
    return count

def calculate_bmi(weight, height):
    """Calculate BMI from weight (kg) and height (cm)"""
    if not weight or not height or height == 0:
        return 0
    
    # Convert height from cm to m
    height_m = height / 100
    
    # BMI formula: weight(kg) / height(m)^2
    bmi = weight / (height_m * height_m)
    return round(bmi, 1)

def get_bmi_category(bmi):
    """Return BMI category based on BMI value"""
    if bmi < 18.5:
        return "Underweight"
    elif bmi < 25:
        return "Normal weight"
    elif bmi < 30:
        return "Overweight"
    else:
        return "Obese"

def calculate_daily_calorie_needs(weight, height, age, gender, activity_level, health_goal):
    """Calculate daily calorie needs using Mifflin-St Jeor Equation"""
    # Convert height from cm to m
    height_m = height / 100
    
    # Base BMR calculation (Mifflin-St Jeor)
    if gender.lower() == 'male':
        bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5
    else:  # female or other
        bmr = (10 * weight) + (6.25 * height) - (5 * age) - 161
    
    # Apply activity multiplier
    activity_multipliers = {
        'sedentary': 1.2,        # Little or no exercise
        'light': 1.375,          # Light exercise 1-3 days/week
        'moderate': 1.55,        # Moderate exercise 3-5 days/week
        'active': 1.725,         # Hard exercise 6-7 days/week
        'very active': 1.9       # Very hard exercise & physical job
    }
    
    multiplier = activity_multipliers.get(activity_level.lower(), 1.2)
    daily_calories = bmr * multiplier
    
    # Adjust for health goal
    if health_goal.lower() == 'weight loss':
        daily_calories -= 500  # Create a deficit
    elif health_goal.lower() == 'gain':
        daily_calories += 500  # Create a surplus
    
    return int(daily_calories)

def get_daily_meals(user_id, date=None):
    """Get all meals logged by a user on a specific date"""
    if date is None:
        date = datetime.utcnow().date()
    
    meals = Meal.query.filter_by(
        user_id=user_id,
        date=date
    ).order_by(Meal.time).all()
    
    return meals

def calculate_daily_nutrition(meals):
    """Calculate total nutrition from a list of meal logs"""
    total = {
        'calories': 0,
        'protein': 0,
        'carbs': 0,
        'fat': 0
    }
    
    for meal in meals:
        # Check if meal is a dictionary or object
        if isinstance(meal, dict):
            meal_nutrition = meal
        else:
            try:
                # Try to call the function
                meal_nutrition = meal.total_nutrition()
            except (AttributeError, TypeError):
                # If it fails, try to access it as an attribute
                meal_nutrition = getattr(meal, 'total_nutrition', {})
                if callable(meal_nutrition):
                    meal_nutrition = meal_nutrition()
                elif not isinstance(meal_nutrition, dict):
                    meal_nutrition = {}
        
        total['calories'] += meal_nutrition.get('calories', 0)
        total['protein'] += meal_nutrition.get('protein', 0)
        total['carbs'] += meal_nutrition.get('carbs', 0)
        total['fat'] += meal_nutrition.get('fat', 0)
    
    return total

def get_weekly_nutrition_data(user_id):
    """Get nutrition data for the past 7 days for charts"""
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=6)  # 7 days including today
    
    dates = []
    calories = []
    protein = []
    carbs = []
    fat = []
    
    # Get user profile for targets
    from models import UserProfile
    profile = UserProfile.query.filter_by(user_id=user_id).first()
    target_calories = profile.target_calories if profile else 2000
    target_protein = profile.target_protein if profile else 125
    target_carbs = profile.target_carbs if profile else 250
    target_fat = profile.target_fat if profile else 55
    
    # Get data for each day
    current_date = start_date
    while current_date <= end_date:
        dates.append(current_date.isoformat())
        
        daily_meals = get_daily_meals(user_id, current_date)
        daily_nutrition = calculate_daily_nutrition(daily_meals)
        
        calories.append(daily_nutrition['calories'])
        protein.append(daily_nutrition['protein'])
        carbs.append(daily_nutrition['carbs'])
        fat.append(daily_nutrition['fat'])
        
        current_date += timedelta(days=1)
    
    return {
        'dates': dates,
        'calories': calories,
        'protein': protein,
        'carbs': carbs,
        'fat': fat,
        'target_calories': target_calories,
        'target_protein': target_protein,
        'target_carbs': target_carbs,
        'target_fat': target_fat
    }

def get_meal_type_distribution(user_id, date=None):
    """Get distribution of calories by meal type for a specific day"""
    if date is None:
        date = datetime.utcnow().date()
    
    distribution = {
        'breakfast': 0,
        'lunch': 0,
        'dinner': 0,
        'snack': 0
    }
    
    meals = get_daily_meals(user_id, date)
    
    for meal in meals:
        if not hasattr(meal, 'meal_type') or meal.meal_type not in distribution:
            continue
            
        try:
            # Try to get nutrition info
            if hasattr(meal, 'total_nutrition'):
                if callable(meal.total_nutrition):
                    nutrition = meal.total_nutrition()
                else:
                    nutrition = meal.total_nutrition
            else:
                nutrition = {'calories': 0}
                
            distribution[meal.meal_type] += nutrition.get('calories', 0)
        except Exception as e:
            # Log error but continue processing
            print(f"Error getting meal nutrition: {str(e)}")
            continue
    
    return distribution