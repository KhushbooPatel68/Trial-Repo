import datetime
import csv
import os
from collections import defaultdict
from models import MealLog
from flask_babel import gettext as _

def get_food_data_from_csv():
    """Read food data from CSV file"""
    food_data = []
    csv_path = os.path.join('data', 'food_data.csv')
    
    if os.path.exists(csv_path):
        with open(csv_path, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                food_data.append(row)
    
    return food_data

def calculate_bmi(weight, height):
    """Calculate BMI from weight (kg) and height (cm)"""
    if not weight or not height:
        return None
    height_m = height / 100  # Convert cm to m
    bmi = weight / (height_m * height_m)
    return round(bmi, 1)

def calculate_daily_calorie_needs(weight, height, age, gender, activity_level, health_goal):
    """Calculate daily calorie needs using Mifflin-St Jeor Equation"""
    if not all([weight, height, age, gender, activity_level]):
        return None
    
    # Base BMR calculation
    if gender.lower() == 'male':
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161
    
    # Activity level multiplier
    activity_multipliers = {
        'sedentary': 1.2,
        'light': 1.375,
        'moderate': 1.55,
        'active': 1.725,
        'very active': 1.9
    }
    multiplier = activity_multipliers.get(activity_level.lower(), 1.2)
    
    # Calculate TDEE (Total Daily Energy Expenditure)
    tdee = bmr * multiplier
    
    # Adjust based on health goal
    if health_goal.lower() == 'weight loss':
        tdee *= 0.8  # 20% caloric deficit
    elif health_goal.lower() == 'gain':
        tdee *= 1.15  # 15% caloric surplus
    
    return round(tdee)

def get_bmi_category(bmi):
    """Return BMI category based on BMI value"""
    if bmi is None:
        return None
    
    if bmi < 18.5:
        return _('Underweight')
    elif bmi < 25:
        return _('Normal weight')
    elif bmi < 30:
        return _('Overweight')
    else:
        return _('Obese')

def get_daily_meals(user_id, date=None):
    """Get all meals logged by a user on a specific date"""
    if date is None:
        date = datetime.datetime.now().date()
    
    # Convert date to datetime objects for comparison
    start_datetime = datetime.datetime.combine(date, datetime.time.min)
    end_datetime = datetime.datetime.combine(date, datetime.time.max)
    
    return MealLog.query.filter(
        MealLog.user_id == user_id,
        MealLog.meal_time >= start_datetime,
        MealLog.meal_time <= end_datetime
    ).order_by(MealLog.meal_time).all()

def calculate_daily_nutrition(meals):
    """Calculate total nutrition from a list of meal logs"""
    totals = {
        'calories': 0,
        'proteins': 0,
        'carbs': 0,
        'fats': 0
    }
    
    for meal in meals:
        totals['calories'] += meal.get_calories() or 0
        macros = meal.get_macros()
        totals['proteins'] += macros.get('proteins') or 0
        totals['carbs'] += macros.get('carbs') or 0
        totals['fats'] += macros.get('fats') or 0
    
    return totals

def get_weekly_nutrition_data(user_id):
    """Get nutrition data for the past 7 days for charts"""
    end_date = datetime.datetime.now().date()
    start_date = end_date - datetime.timedelta(days=6)
    
    # Initialize data structure
    dates = []
    calories_data = []
    macros_data = {
        'proteins': [],
        'carbs': [],
        'fats': []
    }
    
    current_date = start_date
    while current_date <= end_date:
        dates.append(current_date.strftime('%Y-%m-%d'))
        meals = get_daily_meals(user_id, current_date)
        nutrition = calculate_daily_nutrition(meals)
        
        calories_data.append(nutrition['calories'])
        macros_data['proteins'].append(nutrition['proteins'])
        macros_data['carbs'].append(nutrition['carbs'])
        macros_data['fats'].append(nutrition['fats'])
        
        current_date += datetime.timedelta(days=1)
    
    return {
        'dates': dates,
        'calories': calories_data,
        'macros': macros_data
    }

def get_meal_type_distribution(user_id, date=None):
    """Get distribution of calories by meal type for a specific day"""
    meals = get_daily_meals(user_id, date)
    
    meal_types = defaultdict(int)
    for meal in meals:
        meal_types[meal.meal_type] += meal.get_calories() or 0
    
    return dict(meal_types)
