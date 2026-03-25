from flask import Flask, render_template, request, redirect, flash, session
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from weasyprint import HTML
from flask import make_response
from datetime import datetime

import random
import smtplib
from email.mime.text import MIMEText
import os
import webbrowser
import threading


app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev_key")




# =========================
# MongoDB Connection
# =========================
mongo_uri = os.getenv("MONGO_URI")


if not mongo_uri:
    raise ValueError("❌ MONGO URI NOT FOUND. Please set it in environment variables.")

client = MongoClient(mongo_uri)

db = client["healthcoach"]

users = db["users"]

# =========================
# HOME
# =========================
@app.route("/")
def home():
    return render_template("index.html")

# =========================
# LOGIN
# =========================
@app.route("/login", methods=["GET","POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        user = users.find_one({"email": email})

        if user and check_password_hash(user["password"], password):

            session["user"] = email

            # 🔥 Smart routing
            if "personal" not in user:
                return redirect("/personal")
            elif "body" not in user:
                return redirect("/body")
            elif "activity" not in user:
                return redirect("/activity")
            else:
                return redirect("/dashboard")

        else:
            flash("Invalid email or password", "error")

    return render_template("login.html")

# =========================
# SIGNUP
# =========================
@app.route("/signup", methods=["GET","POST"])
def signup():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        existing_user = users.find_one({"email": email})

        if existing_user:
            flash("Account already exists", "error")
            return redirect("/login")

        hashed_password = generate_password_hash(password)

        users.insert_one({
            "name": name,
            "email": email,
            "password": hashed_password
        })

        flash("Account created successfully", "success")
        return redirect("/login")

    return render_template("signup.html")


# =========================
# PERSONAL DETAILS (UPDATED 🔥)
# =========================
@app.route("/personal", methods=["GET","POST"])
def personal():

    if "user" not in session:
        return redirect("/login")

    user_email = session["user"]
    user = users.find_one({"email": user_email})

    if not user:
        return redirect("/login")

    if request.method == "POST":

        # =========================
        # BASIC VALIDATION
        # =========================
        if not all([
            request.form.get("name"),
            request.form.get("age"),
            request.form.get("dob"),
            request.form.get("gender"),
            request.form.get("medicine")
        ]):
            flash("Please fill all required fields", "error")
            return render_template("personal_details.html", data=request.form)

        # =========================
        # ALLERGIES VALIDATION
        # =========================
        allergies = request.form.getlist("allergies")

        if "None" not in allergies and len(allergies) == 0:
            flash("Please select at least one allergy", "error")
            return render_template("personal_details.html", data=request.form)

        # =========================
        # HEALTH CONDITION VALIDATION
        # =========================
        conditions = request.form.getlist("conditions")

        if len(conditions) == 0:
            flash("Please select at least one health condition", "error")
            return render_template("personal_details.html", data=request.form)

        # =========================
        # MEDICINE VALIDATION
        # =========================
        medicine = request.form.get("medicine")
        medicine_name = request.form.get("medicine_name")

        if medicine == "Yes" and not medicine_name:
            flash("Please enter the name of the medicine you are taking", "error")
            return render_template("personal_details.html", data=request.form)

        # =========================
        # SAVE DATA
        # =========================
        data = {
            "name": request.form.get("name"),
            "age": request.form.get("age"),
            "dob": request.form.get("dob"),
            "gender": request.form.get("gender"),

            "allergies": allergies,
            "allergy_description": request.form.get("allergy_description"),

            "conditions": conditions,
            "condition_description": request.form.get("condition_description"),

            "medicine": medicine,
            "medicine_name": medicine_name
        }

        users.update_one(
            {"email": user_email},
            {"$set": {"personal": data}},
            upsert=True
        )

        return redirect("/body")

    # =========================
    # GET REQUEST (LOAD DATA)
    # =========================
    personal_data = user.get("personal") if user and "personal" in user else None

    return render_template("personal_details.html", data=personal_data)


# =========================
# BODY MEASUREMENTS (FIXED)
# =========================
@app.route("/body", methods=["GET","POST"])
def body():

    if "user" not in session:
        return redirect("/login")

    user_email = session["user"]

    user = users.find_one({"email": user_email})   # 🔥 ADD THIS

    if not user:
        return redirect("/login")

    if request.method == "POST":

        # =========================
        # 1. REQUIRED VALIDATION
        # =========================
        required_fields = [
            "weight", "height", "neck", "chest",
            "arms", "shoulders", "waist", "hip",
            "high_hip", "thighs"
        ]

        for field in required_fields:
            if not request.form.get(field):
                flash("Please fill all body measurements", "error")
                return redirect("/body")


        # =========================
        # 2. BONUS 3 (ADD HERE 🔥)
        # =========================
        try:
            weight = float(request.form.get("weight"))
            height = float(request.form.get("height"))

            if weight < 20 or weight > 300:
                flash("Invalid weight entered", "error")
                return redirect("/body")

            if height < 80 or height > 250:
                flash("Invalid height entered", "error")
                return redirect("/body")

        except:
            flash("Invalid input values", "error")
            return redirect("/body")


        # =========================
        # 3. SAVE DATA
        # =========================
        data = {
            "weight": request.form.get("weight"),
            "height": request.form.get("height"),
            "neck": request.form.get("neck"),
            "chest": request.form.get("chest"),
            "arms": request.form.get("arms"),
            "shoulders": request.form.get("shoulders"),
            "waist": request.form.get("waist"),
            "hip": request.form.get("hip"),
            "high_hip": request.form.get("high_hip"),
            "thighs": request.form.get("thighs")
        }

        users.update_one(
            {"email": user_email},
            {"$set": {"body": data}},
            upsert=True
        )
        

        users.update_one(
            {"email": user_email},
            {
                "$push": {
                    "progress": {
                        "weight": float(request.form.get("weight")),
                        "date": datetime.now()
                    }
                }
            }
        )

        users.update_one(
            {"email": user_email},
            {
                "$push": {
                    "progress_full": {
                        "date": datetime.now(),
                        "weight": float(request.form.get("weight")),
                        "waist": float(request.form.get("waist")),
                        "chest": float(request.form.get("chest")),
                        "hips": float(request.form.get("hip")),
                        "arms": float(request.form.get("arms"))
                    }
                }
            }
        )

        return redirect("/activity")


    # =========================
    # GET REQUEST
    # =========================
    user = users.find_one({"email": user_email})
    body_data = user.get("body") if user and "body" in user else None

    return render_template("body_measurements.html", data=body_data)

# =========================
# ACTIVITY PAGE (FIXED)
# =========================
@app.route("/activity", methods=["GET", "POST"])
def activity():

    # ===== LOGIN CHECK =====
    if "user" not in session:
        return redirect("/login")

    user_email = session["user"]
    user = users.find_one({"email": user_email})

    if not user:
        return redirect("/login")

    # =========================
    # POST REQUEST
    # =========================
    if request.method == "POST":

        activity = request.form.get("activity")
        goal = request.form.get("goal")
        target_weight = request.form.get("target_weight")

        # ===== VALIDATION =====
        valid_activities = ["sedentary", "light", "moderate", "active", "very_active"]
        valid_goals = ["weight_loss", "weight_gain", "muscle_build", "maintain"]

        # Empty check
        if not activity or not goal:
            flash("Please select activity level and goal", "error")
            return redirect("/activity")

        # Value validation
        if activity not in valid_activities:
            flash("Invalid activity selected", "error")
            return redirect("/activity")

        if goal not in valid_goals:
            flash("Invalid goal selected", "error")
            return redirect("/activity")

        # ===== TARGET WEIGHT VALIDATION =====
        if not target_weight:
            flash("Please enter your target weight", "error")
            return redirect("/activity")

        try:
            target_weight = float(target_weight)

            if target_weight < 20 or target_weight > 300:
                flash("Target weight must be between 20–300 kg", "error")
                return redirect("/activity")

        except:
            flash("Invalid target weight", "error")
            return redirect("/activity")

        # ===== SAVE DATA =====
        data = {
            "activity_level": activity,
            "goal": goal,
            "target_weight": target_weight
        }

        users.update_one(
            {"email": user_email},
            {"$set": {"activity": data}},
            upsert=True
        )

        return redirect("/health_calculator")

    # =========================
    # GET REQUEST (NO RE-FETCH NEEDED)
    # =========================
    activity_data = user.get("activity") if "activity" in user else None

    return render_template("activity_goal.html", data=activity_data)

# =========================
# CALCULATIONS (UPDATED 🔥)
# =========================
@app.route("/health_calculator")
def health_calculator():

    # =========================
    # SESSION CHECK
    # =========================
    if "user" not in session:
        return redirect("/login")

    user = users.find_one({"email": session["user"]})
    
    if not user:
        return redirect("/login")

    # =========================
    # GET DATA FROM DB
    # =========================
    personal = user.get("personal", {})
    body = user.get("body", {})
    activity = user.get("activity", {})

    # =========================
    # DATA EXTRACTION
    # =========================
    weight = float(body.get("weight", 0))
    height = float(body.get("height", 0))
    age = int(personal.get("age", 0))
    gender = personal.get("gender", "Male")

    activity_level = activity.get("activity_level", "moderate")
    goal = activity.get("goal", "maintain")

    waist = float(body.get("waist", 0))
    hip = float(body.get("hip", 0))
    chest = float(body.get("chest", 0))

    # =========================
    # SAFE VALIDATION
    # =========================
    if height <= 0 or weight <= 0:
        flash("Invalid body data. Please fill body measurements properly.", "error")
        return redirect("/body")

    height_m = height / 100

    # =========================
    # BMI
    # =========================
    bmi = round(weight / (height_m ** 2), 2)

    if bmi < 18.5:
        bmi_status = "Underweight"
        bmi_color = "#3498db"
    elif bmi < 25:
        bmi_status = "Normal"
        bmi_color = "#2ecc71"
    elif bmi < 30:
        bmi_status = "Overweight"
        bmi_color = "#f39c12"
    else:
        bmi_status = "Obese"
        bmi_color = "#e74c3c"

    # =========================
    # BMR
    # =========================
    if gender == "Male":
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161

    bmr = round(bmr, 2)

    # =========================
    # TDEE
    # =========================
    activity_map = {
        "sedentary": 1.2,
        "light": 1.375,
        "moderate": 1.55,
        "active": 1.725,
        "very_active": 1.9
    }

    tdee = round(bmr * activity_map.get(activity_level, 1.55), 2)

    # =========================
    # CALORIES BASED ON GOAL
    # =========================
    if goal == "weight_loss":
        calories = tdee - 500
    elif goal == "weight_gain":
        calories = tdee + 500
    else:
        calories = tdee

    calories = round(calories, 2)

    # =========================
    # CALORIE STATUS
    # =========================
    if goal == "weight_loss":
        cal_status = "Calorie Deficit"
        cal_color = "#3498db"
    elif goal == "weight_gain":
        cal_status = "Calorie Surplus"
        cal_color = "#e67e22"
    else:
        cal_status = "Maintenance"
        cal_color = "#2ecc71"

    # =========================
    # MACROS
    # =========================
    macros = calculate_macros(calories, goal)

    protein = macros["protein"]
    carbs = macros["carbs"]
    fats = macros["fats"]

    # =========================
    # WATER
    # =========================
    water = round(weight * 0.033, 2)

    # =========================
    # BODY FAT % (NEW 🔥)
    # =========================
    body_fat = round(
        (1.20 * bmi) + (0.23 * age) - (10.8 if gender == "Male" else 0) - 5.4,
        2
    )

    # =========================
    # WAIST TO HIP RATIO (NEW 🔥)
    # =========================
    whr = round(waist / hip, 2) if hip > 0 else 0

    # =========================
    # SMART BODY TYPE (IMPROVED 🔥)
    # =========================
    if body_fat < 18:
        body_type = "Ectomorph"
    elif body_fat < 25:
        body_type = "Mesomorph"
    else:
        body_type = "Endomorph"

    # =========================
    # BODY SHAPE
    # =========================
    if abs(chest - hip) < 5:
        body_shape = "Rectangle"
    elif chest > hip:
        body_shape = "Inverted Triangle"
    else:
        body_shape = "Pear"

    # =========================
    # AI SUGGESTION (PREMIUM 🔥)
    # =========================
    if bmi < 18.5:
        suggestion = "Your body is currently underweight. Focus on a calorie surplus, strength training, and nutrient-dense meals to build healthy mass."
    elif bmi < 25:
        suggestion = "You are in a healthy range. Maintain consistency with balanced nutrition and regular exercise to sustain your fitness."
    elif bmi < 30:
        suggestion = "You are slightly above the ideal range. A structured calorie deficit combined with cardio and strength training will help improve body composition."
    else:
        suggestion = "Your body indicates higher fat accumulation. A disciplined approach with calorie control, regular workouts, and lifestyle changes is recommended."

    users.update_one(
        {"email": session["user"]},
        {"$set": {
            "bmi": bmi,
            "bmr": bmr,
            "tdee": tdee,
            "calories": calories,
            "protein": protein,
            "carbs": carbs,
            "fats": fats,
            "water": water,
            "body_fat": body_fat,
            "whr": whr,
            "body_type": body_type,
            "body_shape": body_shape,
            "suggestion": suggestion
        }}
    )

    # =========================
    # RENDER
    # =========================
    return render_template(
        "health_calculator.html",
        bmi=bmi,
        bmi_status=bmi_status,
        bmi_color=bmi_color,
        bmr=bmr,
        tdee=tdee,
        calories=calories,
        cal_status=cal_status,
        cal_color=cal_color,
        protein=protein,
        carbs=carbs,
        fats=fats,
        water=water,
        body_type=body_type,
        body_shape=body_shape,
        body_fat=body_fat,   # NEW
        whr=whr,             # NEW
        suggestion=suggestion
    )

# =========================
# DIET & EXERCISE FUNCTIONS
# =========================

def split_calories(calories):
    return {
        "Breakfast": round(calories * 0.30),
        "Lunch": round(calories * 0.40),
        "Snack": round(calories * 0.10),
        "Dinner": round(calories * 0.20)
    }

def calculate_macros(calories, goal):

    if goal == "weight_loss":
        protein_ratio = 0.40
        carbs_ratio = 0.30
        fats_ratio = 0.30

    elif goal == "muscle_build":
        protein_ratio = 0.35
        carbs_ratio = 0.45
        fats_ratio = 0.20

    elif goal == "weight_gain":
        protein_ratio = 0.25
        carbs_ratio = 0.50
        fats_ratio = 0.25

    else:  # maintain
        protein_ratio = 0.30
        carbs_ratio = 0.40
        fats_ratio = 0.30

    return {
        "protein": round((calories * protein_ratio) / 4),
        "carbs": round((calories * carbs_ratio) / 4),
        "fats": round((calories * fats_ratio) / 9)
    }

def filter_foods(food_list, allergies, conditions):

    filtered = []

    for food in food_list:
        tags = food.get("tags", [])

        # =========================
        # ALLERGIES
        # =========================
        if "Dairy" in allergies and "dairy" in tags:
            continue

        if "Peanuts" in allergies and "peanut" in tags:
            continue

        if "Seafood" in allergies and "seafood" in tags:
            continue

        # =========================
        # HEALTH CONDITIONS
        # =========================
        if "Diabetes" in conditions:
            # allow safe + medium foods
            if "high_sugar" in tags:
                continue

        if "Blood Pressure" in conditions:
            if "high_sodium" in tags:
                continue

        # =========================
        # KEEP FOOD
        # =========================
        filtered.append(food)

    # fallback (IMPORTANT)
    return filtered if filtered else food_list

# =========================
# FOOD DATABASE (FIXED 🔥)
# =========================
FOOD_DB = {

# ================= VEG INDIAN =================
"veg_indian": [

# Breakfast
{"name":"Oats Upma","type":"breakfast","cal":250,"protein":8,"carbs":40,"fats":6,"tags":["veg","low_gi","high_fiber","diabetes_safe"]},
{"name":"Vegetable Poha","type":"breakfast","cal":300,"protein":6,"carbs":50,"fats":8,"tags":["veg","high_carb"]},
{"name":"Besan Chilla","type":"breakfast","cal":280,"protein":12,"carbs":30,"fats":10,"tags":["veg","high_protein","low_gi"]},
{"name":"Idli + Sambar","type":"breakfast","cal":320,"protein":10,"carbs":55,"fats":5,"tags":["veg","light","low_sodium","low_gi"]},
{"name":"Vegetable Dalia","type":"breakfast","cal":270,"protein":9,"carbs":45,"fats":6,"tags":["veg","low_gi","high_fiber","diabetes_safe"]},
{"name":"Whole Wheat Pita + Hummus","type":"breakfast","cal":300,"protein":10,"carbs":40,"fats":10,"tags":["veg","high_fiber","low_gi"]},

# Lunch
{"name":"Dal + Roti","type":"lunch","cal":450,"protein":18,"carbs":60,"fats":10,"tags":["veg","high_fiber","complex_carbs","diabetes_safe"]},
{"name":"Rajma + Rice","type":"lunch","cal":500,"protein":20,"carbs":70,"fats":12,"tags":["veg","high_fiber","complex_carbs"]},
{"name":"Chole + Roti","type":"lunch","cal":520,"protein":18,"carbs":75,"fats":15,"tags":["veg","high_fiber"]},
{"name":"Paneer Sabzi","type":"lunch","cal":400,"protein":22,"carbs":30,"fats":18,"tags":["veg","dairy","high_protein"]},
{"name":"Vegetable Pulao","type":"lunch","cal":450,"protein":12,"carbs":65,"fats":12,"tags":["veg","high_carb"]},

# Snack
{"name":"Fruits Bowl","type":"snack","cal":150,"protein":2,"carbs":35,"fats":1,"tags":["veg","high_fiber","low_sugar","diabetes_safe"]},
{"name":"Roasted Chana","type":"snack","cal":180,"protein":10,"carbs":25,"fats":3,"tags":["veg","high_protein","high_fiber"]},
{"name":"Peanut Chaat","type":"snack","cal":200,"protein":8,"carbs":20,"fats":10,"tags":["veg","peanut"]},
{"name":"Buttermilk","type":"snack","cal":120,"protein":5,"carbs":10,"fats":5,"tags":["veg","dairy","light"]},

# Dinner
{"name":"Vegetable Khichdi","type":"dinner","cal":350,"protein":12,"carbs":50,"fats":8,"tags":["veg","light","low_sodium","low_gi"]},
{"name":"Mix Veg Curry + Roti","type":"dinner","cal":400,"protein":15,"carbs":50,"fats":12,"tags":["veg","high_fiber"]},
{"name":"Palak Paneer","type":"dinner","cal":420,"protein":20,"carbs":20,"fats":22,"tags":["veg","dairy","high_protein"]},
{"name":"Lauki Sabzi + Roti","type":"dinner","cal":320,"protein":10,"carbs":40,"fats":8,"tags":["veg","weight_loss","light"]},
],


# ================= NONVEG INDIAN =================
"nonveg_indian": [

# Breakfast
{"name":"Egg Bhurji","type":"breakfast","cal":280,"protein":18,"carbs":5,"fats":20,"tags":["egg","high_protein","low_carb","diabetes_safe"]},
{"name":"Boiled Eggs + Toast","type":"breakfast","cal":300,"protein":20,"carbs":25,"fats":12,"tags":["egg","high_protein"]},
{"name":"Chicken Sandwich","type":"breakfast","cal":350,"protein":22,"carbs":30,"fats":12,"tags":["nonveg","high_protein"]},
{"name":"Egg Omelette + Roti","type":"breakfast","cal":320,"protein":20,"carbs":20,"fats":18,"tags":["egg","high_protein"]},
{"name":"Chicken Sausage + Toast","type":"breakfast","cal":350,"protein":22,"carbs":25,"fats":18,"tags":["nonveg","high_protein"]},

# Lunch
{"name":"Chicken Curry + Rice","type":"lunch","cal":550,"protein":35,"carbs":60,"fats":15,"tags":["nonveg","high_protein"]},
{"name":"Fish Curry + Rice","type":"lunch","cal":520,"protein":32,"carbs":60,"fats":14,"tags":["seafood","high_protein"]},
{"name":"Egg Curry + Roti","type":"lunch","cal":480,"protein":25,"carbs":40,"fats":18,"tags":["egg","high_protein"]},
{"name":"Grilled Chicken + Brown Rice","type":"lunch","cal":520,"protein":35,"carbs":55,"fats":14,"tags":["nonveg","weight_loss","high_protein"]},
{"name":"Mutton Curry + Roti","type":"lunch","cal":600,"protein":30,"carbs":40,"fats":30,"tags":["red_meat"]},
{"name":"Fish Tikka + Rice","type":"lunch","cal":500,"protein":32,"carbs":45,"fats":18,"tags":["seafood","high_protein"]},
{"name":"Chicken Biryani (controlled portion)","type":"lunch","cal":600,"protein":28,"carbs":65,"fats":22,"tags":["nonveg","high_carb"]},

# Snack
{"name":"Boiled Eggs","type":"snack","cal":140,"protein":12,"carbs":1,"fats":10,"tags":["egg","high_protein"]},
{"name":"Chicken Soup","type":"snack","cal":180,"protein":15,"carbs":5,"fats":8,"tags":["nonveg","light","low_sodium","low_gi"]},
{"name":"Chicken Tikka","type":"snack","cal":250,"protein":28,"carbs":5,"fats":12,"tags":["nonveg","high_protein"]},
{"name":"Fish Soup","type":"snack","cal":180,"protein":15,"carbs":5,"fats":8,"tags":["seafood","light","low_sodium"]},

# Dinner
{"name":"Grilled Chicken","type":"dinner","cal":400,"protein":35,"carbs":10,"fats":15,"tags":["nonveg","high_protein","low_carb","low_sodium","diabetes_safe"]},
{"name":"Fish Fry","type":"dinner","cal":450,"protein":30,"carbs":5,"fats":25,"tags":["seafood"]},
{"name":"Chicken Stir Fry","type":"dinner","cal":420,"protein":32,"carbs":15,"fats":18,"tags":["nonveg","high_protein","low_carb"]},
{"name":"Mutton Stew","type":"dinner","cal":480,"protein":28,"carbs":15,"fats":28,"tags":["red_meat"]},
{"name":"Grilled Fish + Veggies","type":"dinner","cal":420,"protein":32,"carbs":10,"fats":20,"tags":["seafood","weight_loss","low_sodium","diabetes_safe"]},
{"name":"Chicken Curry + Roti","type":"dinner","cal":450,"protein":30,"carbs":35,"fats":18,"tags":["nonveg","high_protein"]},
],


# ================= VEG MEDITERRANEAN =================
"veg_mediterranean": [

# Breakfast
{"name":"Greek Yogurt + Nuts","type":"breakfast","cal":300,"protein":15,"carbs":20,"fats":15,"tags":["veg","dairy","healthy_fat"]},
{"name":"Avocado Toast","type":"breakfast","cal":320,"protein":8,"carbs":30,"fats":18,"tags":["veg","healthy_fat"]},
{"name":"Fruit Smoothie","type":"breakfast","cal":280,"protein":6,"carbs":50,"fats":5,"tags":["veg","high_carb"]},

# Lunch
{"name":"Quinoa Salad","type":"lunch","cal":400,"protein":15,"carbs":50,"fats":12,"tags":["veg","low_gi","high_fiber","diabetes_safe"]},
{"name":"Mediterranean Veg Wrap","type":"lunch","cal":420,"protein":12,"carbs":50,"fats":15,"tags":["veg","high_fiber"]},
{"name":"Lentil Soup","type":"lunch","cal":350,"protein":18,"carbs":40,"fats":8,"tags":["veg","low_gi","high_fiber","low_sodium","diabetes_safe"]},
{"name":"Mediterranean Couscous","type":"lunch","cal":420,"protein":12,"carbs":60,"fats":12,"tags":["veg","high_carb"]},
{"name":"Chickpea Salad","type":"lunch","cal":380,"protein":15,"carbs":50,"fats":10,"tags":["veg","high_fiber","low_gi"]},

# Snack
{"name":"Hummus + Veggies","type":"snack","cal":200,"protein":8,"carbs":20,"fats":10,"tags":["veg","high_fiber"]},
{"name":"Mixed Nuts","type":"snack","cal":250,"protein":6,"carbs":10,"fats":20,"tags":["veg","healthy_fat"]},
{"name":"Olive Oil Veg Salad","type":"snack","cal":200,"protein":5,"carbs":10,"fats":15,"tags":["veg","healthy_fat"]},

# Dinner
{"name":"Grilled Vegetables","type":"dinner","cal":300,"protein":10,"carbs":40,"fats":10,"tags":["veg","light","low_sodium"]},
{"name":"Falafel + Salad","type":"dinner","cal":420,"protein":15,"carbs":45,"fats":18,"tags":["veg","high_fiber"]},
{"name":"Stuffed Bell Peppers","type":"dinner","cal":350,"protein":10,"carbs":40,"fats":12,"tags":["veg","light"]},
{"name":"Zucchini Noodles","type":"dinner","cal":280,"protein":8,"carbs":30,"fats":10,"tags":["veg","weight_loss","low_carb"]},
],


# ================= NONVEG MEDITERRANEAN =================
"nonveg_mediterranean": [

# Breakfast
{"name":"Omelette + Avocado","type":"breakfast","cal":350,"protein":20,"carbs":10,"fats":22,"tags":["egg","high_protein","healthy_fat"]},
{"name":"Egg Wrap","type":"breakfast","cal":320,"protein":18,"carbs":25,"fats":14,"tags":["egg","high_protein"]},
{"name":"Egg White Omelette","type":"breakfast","cal":250,"protein":22,"carbs":5,"fats":10,"tags":["egg","high_protein","weight_loss"]},

# Lunch
{"name":"Grilled Chicken Salad","type":"lunch","cal":450,"protein":35,"carbs":20,"fats":15,"tags":["nonveg","high_protein","weight_loss"]},
{"name":"Tuna Salad","type":"lunch","cal":400,"protein":30,"carbs":15,"fats":18,"tags":["seafood","high_protein","low_gi"]},
{"name":"Grilled Fish Salad","type":"lunch","cal":420,"protein":32,"carbs":15,"fats":18,"tags":["seafood","weight_loss","low_gi"]},
{"name":"Chicken Shawarma Bowl","type":"lunch","cal":500,"protein":35,"carbs":40,"fats":18,"tags":["nonveg","high_protein"]},
{"name":"Lamb Kebabs + Salad","type":"lunch","cal":550,"protein":30,"carbs":20,"fats":30,"tags":["red_meat"]},

# Snack
{"name":"Tuna Sandwich","type":"snack","cal":300,"protein":20,"carbs":30,"fats":10,"tags":["seafood","high_protein"]},
{"name":"Greek Yogurt","type":"snack","cal":200,"protein":12,"carbs":10,"fats":8,"tags":["dairy"]},
{"name":"Boiled Egg + Olive Oil","type":"snack","cal":200,"protein":12,"carbs":2,"fats":15,"tags":["egg","healthy_fat"]},

# Dinner
{"name":"Salmon + Veggies","type":"dinner","cal":500,"protein":40,"carbs":10,"fats":25,"tags":["seafood","high_protein","healthy_fat","diabetes_safe"]},
{"name":"Grilled Chicken","type":"dinner","cal":420,"protein":35,"carbs":10,"fats":15,"tags":["nonveg","high_protein","low_carb"]},
{"name":"Grilled Salmon + Quinoa","type":"dinner","cal":520,"protein":40,"carbs":30,"fats":22,"tags":["seafood","high_protein"]},
{"name":"Chicken Skewers","type":"dinner","cal":400,"protein":35,"carbs":10,"fats":15,"tags":["nonveg","high_protein"]},
{"name":"Lamb Stew","type":"dinner","cal":500,"protein":30,"carbs":15,"fats":30,"tags":["red_meat"]},
]

}

def generate_day_meal(food_pool, calories):

    split = split_calories(calories)
    meals = {}

    for meal in ["Breakfast", "Lunch", "Snack", "Dinner"]:

        options = [f for f in food_pool if f["type"] == meal.lower()]

        if not options:
            continue

        if not options:
            continue  # skip instead of crash

        food = random.choice(options)

        cal = split[meal]

        # scale food nutrition to match calories
        factor = cal / food["cal"]

        protein = round(food["protein"] * factor)
        carbs = round(food["carbs"] * factor)
        fats = round(food["fats"] * factor)

        meals[meal] = {
            "name": food["name"],
            "calories": cal,
            "protein": protein,
            "carbs": carbs,
            "fats": fats
        }

    return meals

def generate_week_meals(food_pool, calories):

    days = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

    weekly = {}
    used_foods = set()

    for day in days:

        split = split_calories(calories)
        daily = {}

        for meal in ["Breakfast","Lunch","Snack","Dinner"]:

            options = [f for f in food_pool if f["type"] == meal.lower()]

            # avoid repetition
            options = [f for f in food_pool if f["type"] == meal.lower()]

            # remove used foods
            filtered_options = [f for f in options if f["name"] not in used_foods]

            # fallback if empty
            if not filtered_options:
                filtered_options = options

            # 🔥 FINAL SAFETY (IMPORTANT)
            if not filtered_options:
                filtered_options = food_pool   # 🔥 FIX

            food = random.choice(filtered_options)
            used_foods.add(food["name"])

            cal = split[meal]

            factor = cal / food["cal"]

            protein = round(food["protein"] * factor)
            carbs = round(food["carbs"] * factor)
            fats = round(food["fats"] * factor)

            daily[meal] = {
                "name": food["name"],
                "calories": cal,
                "protein": protein,
                "carbs": carbs,
                "fats": fats
            }

        weekly[day] = daily

    return weekly

# =========================
# ADVANCED EXERCISE SYSTEM 🔥
# =========================
def generate_exercise(goal, duration):

    # 10+ exercises per category
    base = {
        "weight_loss": [
            "Running", "Cycling", "Jump Rope", "HIIT", "Burpees",
            "Mountain Climbers", "Jump Squats", "Plank", "High Knees", "Box Jumps"
        ],
        "muscle_build": [
            "Push-ups", "Squats", "Deadlift", "Pull-ups", "Bench Press",
            "Lunges", "Bicep Curls", "Tricep Dips", "Shoulder Press", "Leg Press"
        ],
        "maintain": [
            "Yoga", "Walking", "Stretching", "Light Jogging", "Pilates",
            "Core Workout", "Bodyweight Squats", "Wall Sit", "Arm Circles", "Step-ups"
        ]
    }

    pool = base.get(goal, base["maintain"])

    days = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

    if duration == "week":
        plan = {}

        for day in days:
            # 3 different exercises each day
            plan[day] = random.sample(pool, 3)

        return plan

    else:
        return random.sample(pool, 4)

# =========================
# ADVANCED FOOD RESTRICTION SYSTEM 🔥
# =========================
def get_restricted_foods(user, calories):

    personal = user.get("personal", {})
    body = user.get("body", {})
    activity = user.get("activity", {})

    allergies = personal.get("allergies", [])
    conditions = personal.get("conditions", [])
    goal = activity.get("goal", "maintain")

    weight = float(body.get("weight", 0))
    height = float(body.get("height", 0))
    age = int(personal.get("age", 0))

    # BMI
    height_m = height / 100 if height > 0 else 1
    bmi = weight / (height_m ** 2)

    restricted = []

    # =========================
    # ALLERGIES 🚫
    # =========================
    if "Peanuts" in allergies:
        restricted.append("Peanuts and peanut-based products")

    if "Dairy" in allergies:
        restricted.append("Milk, paneer, cheese and dairy products")

    # =========================
    # HEALTH CONDITIONS 🧬
    # =========================
    if "Diabetes" in conditions:
        restricted.append("Sugary foods, sweets, desserts, sweetened drinks")

    if "Blood Pressure" in conditions:
        restricted.append("High sodium foods, pickles, packaged snacks")

    if "Thyroid" in conditions:
        restricted.append("Excess soy products and processed foods")

    # =========================
    # BMI BASED ⚖️
    # =========================
    if bmi >= 25:
        restricted.append("Fried foods, junk food, high-fat fast foods")

    if bmi < 18.5:
        restricted.append("Low-calorie restrictive diets (focus on nutrient-dense foods instead)")

    # =========================
    # GOAL BASED 🎯
    # =========================
    if goal == "weight_loss":
        restricted.append("High-calorie junk food, sugary snacks, soft drinks")

    if goal == "muscle_build":
        restricted.append("Highly processed junk food with low protein")

    # =========================
    # ALWAYS INCLUDE (GENERAL HEALTH)
    # =========================
    restricted.append("Excess alcohol and highly processed foods")

    # Remove duplicates
    restricted = list(set(restricted))

    return restricted

def calculate_calories(user):

    personal = user.get("personal", {})
    body = user.get("body", {})
    activity = user.get("activity", {})

    weight = float(body.get("weight", 0))
    height = float(body.get("height", 0))
    age = int(personal.get("age", 0))
    gender = personal.get("gender", "Male")

    activity_level = activity.get("activity_level", "moderate")
    goal = activity.get("goal", "maintain")

    # BMR
    if gender == "Male":
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161

    # Activity
    activity_map = {
        "sedentary": 1.2,
        "light": 1.375,
        "moderate": 1.55,
        "active": 1.725,
        "very_active": 1.9
    }

    tdee = bmr * activity_map.get(activity_level, 1.55)

    # Goal adjustment
    if goal == "weight_loss":
        calories = tdee - 500
    elif goal == "weight_gain":
        calories = tdee + 500
    else:
        calories = tdee

    return round(calories)


# =========================
# PLAN (DIET + EXERCISE)
# =========================
@app.route("/plan", methods=["GET", "POST"])
def plan():

    if "user" not in session:
        return redirect("/login")

    user = users.find_one({"email": session["user"]})

    # ✅ ADD THIS RIGHT HERE
    if not user:
        return redirect("/login")

    if request.method == "POST":

        diet_type = request.form.get("diet_type")
        cuisine = request.form.get("cuisine")

        key = f"{diet_type}_{cuisine}"


        diet_duration = request.form.get("diet_duration")
        exercise_duration = request.form.get("exercise_duration")

        # 1. GET USER DATA FIRST
        personal = user.get("personal", {})
        activity = user.get("activity", {})

        allergies = personal.get("allergies", [])
        conditions = personal.get("conditions", [])
        goal = activity.get("goal", "maintain")

        # 2. GET FOOD
        food_pool = FOOD_DB.get(key, FOOD_DB["veg_indian"])

        # 3. FILTER FOOD (NOW WORKS PERFECTLY)
        filtered_foods = filter_foods(food_pool, allergies, conditions)

        # 🔥 fallback safety
        if not filtered_foods:
            filtered_foods = food_pool

        # 🔥 USE REAL CALORIES FROM AI PAGE
    
        
        
        calories = calculate_calories(user)   # ✅ CORRECT

        # DIET
        if diet_duration == "week":
            meals = generate_week_meals(filtered_foods, calories)
        else:
            meals = generate_day_meal(filtered_foods, calories)

        # EXERCISE
        exercise_plan = generate_exercise(goal, exercise_duration)

        # RESTRICTED FOODS
        restricted_foods = get_restricted_foods(user, calories)

        # =========================
        # SMART SUMMARY TEXT
        # =========================
        summary = f"""
        This plan is created based on your goal of {goal.replace('_',' ')} and your daily calorie requirement of {calories} kcal.
        The diet is structured with balanced macros and portion control, while the exercise routine is designed to match your activity level and improve overall fitness.
        """

        macros = calculate_macros(calories, goal)
        

        # =========================
        # ADD THIS (TIPS LOGIC 🔥)
        # =========================
        tips = []

        personal = user.get("personal", {})
        body = user.get("body", {})
        activity = user.get("activity", {})

        goal = activity.get("goal")
        conditions = personal.get("conditions", [])
        weight = float(body.get("weight", 0))

        # GOAL BASED
        if goal == "weight_loss":
            tips += [
                "Avoid fried and sugary foods",
                "Walk at least 30–45 minutes daily",
                "Eat more fiber-rich foods",
                "Drink more water"
            ]

        elif goal == "weight_gain":
            tips += [
                "Increase calorie intake",
                "Eat every 3–4 hours",
                "Include protein-rich foods",
                "Add nuts and dairy"
            ]

        elif goal == "muscle_build":
            tips += [
                "Focus on strength training",
                "Eat high protein diet",
                "Sleep properly",
                "Stay consistent"
            ]

        else:
            tips += [
                "Maintain balanced diet",
                "Exercise regularly",
                "Stay hydrated"
            ]

        # CONDITION BASED
        if "Diabetes" in conditions:
            tips.append("Avoid sugar and refined carbs")

        if "Blood Pressure" in conditions:
            tips.append("Reduce salt intake")

        if "PCOS" in conditions:
            tips.append("Eat low GI foods")

        if "Cholesterol" in conditions:
            tips.append("Avoid fried food")

        # GENERAL
        if weight > 90:
            tips.append("Focus on gradual fat loss")

        if weight < 45:
            tips.append("Increase healthy calorie intake")

        # REMOVE DUPLICATES
        tips = list(set(tips))

        users.update_one(
            {"email": session["user"]},
            {"$set": {
                "meals": meals,
                "exercise_plan": exercise_plan,
                "tips": tips,
                "summary": summary,
                "diet_type": request.form.get("diet_type"),
                "cuisine": request.form.get("cuisine")
            }}
        )

        # 🔥 STORE TEMP DATA IN SESSION
        session["plan_data"] = {
            "meals": meals,
            "exercise_plan": exercise_plan,
            "calories": calories,
            "diet_duration": diet_duration,
            "exercise_duration": exercise_duration,
            "restricted_foods": restricted_foods,
            "tips": tips,
            "summary": summary,
            "macros": macros,
            "goal": goal
        }

        session["show_plan"] = True   # 🔥 FLAG

        return redirect("/plan")

    plan_data = session.get("plan_data")
    show_plan = session.get("show_plan")
    from_report = request.args.get("from")

    # ✅ CASE 1: Coming from report → show result
    if from_report == "report" and plan_data:
        return render_template(
            "plan.html",
            **plan_data,
            show_result=True
        )

    # ✅ CASE 2: After generate → show once
    if plan_data and show_plan:
        session["show_plan"] = False   # 🔥 reset

        return render_template(
            "plan.html",
            **plan_data,
            show_result=True
        )

    # ❌ CASE 3: Refresh → CLEAR EVERYTHING
    session.pop("plan_data", None)

    return render_template("plan.html", show_result=False)


# =========================
# REPORT ROUTE
# =========================
@app.route("/report")
def report():

    if "user" not in session:
        return redirect("/login")

    user = users.find_one({"email": session["user"]})

    return render_template("report.html",
        personal=user.get("personal"),
        body=user.get("body"),
        activity=user.get("activity"),

        bmi=user.get("bmi"),
        bmr=user.get("bmr"),
        tdee=user.get("tdee"),
        calories=user.get("calories"),
        protein=user.get("protein"),
        carbs=user.get("carbs"),
        fats=user.get("fats"),
        water=user.get("water"),
        body_fat=user.get("body_fat"),
        whr=user.get("whr"),
        body_type=user.get("body_type"),
        body_shape=user.get("body_shape"),
        suggestion=user.get("suggestion"),

        meals=user.get("meals"),
        exercise=user.get("exercise_plan"),
        tips=user.get("tips")
    )

# =========================
# PDF ROUTE
# =========================
@app.route("/download_report")
def download_report():

    if "user" not in session:
        return redirect("/login")

    user = users.find_one({"email": session["user"]})

    html = render_template("report.html",
        personal=user.get("personal"),
        body=user.get("body"),
        activity=user.get("activity"),

        bmi=user.get("bmi"),
        bmr=user.get("bmr"),
        tdee=user.get("tdee"),
        calories=user.get("calories"),
        protein=user.get("protein"),
        carbs=user.get("carbs"),
        fats=user.get("fats"),
        water=user.get("water"),
        body_fat=user.get("body_fat"),
        whr=user.get("whr"),
        body_type=user.get("body_type"),
        body_shape=user.get("body_shape"),
        suggestion=user.get("suggestion"),

        meals=user.get("meals"),
        exercise=user.get("exercise_plan"),
        tips=user.get("tips")
    )

    pdf = HTML(string=html).write_pdf()

    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=Health_Report.pdf'

    return response

@app.route("/dashboard")
def dashboard():

    if "user" not in session:
        return redirect("/login")

    user = users.find_one({"email": session["user"]})

    # ===== PROGRESS DATA =====
    progress = user.get("progress", [])
    progress_full = user.get("progress_full", [])

    weights = [p["weight"] for p in progress]
    dates = [p["date"].strftime("%d %b") for p in progress]

    # ===== BODY DATA =====
    waist = [p.get("waist", 0) for p in progress_full]
    chest = [p.get("chest", 0) for p in progress_full]
    hips = [p.get("hips", 0) for p in progress_full]
    arms = [p.get("arms", 0) for p in progress_full]

    # ===== GOAL PROGRESS =====
    start = weights[0] if weights else 0
    current = weights[-1] if weights else 0
    target = user.get("activity", {}).get("target_weight", 0)
    goal = user.get("activity", {}).get("goal", "")

    percent = 0

    if start and target:
        if goal == "weight_loss":
            total = start - target
            done = start - current
        else:
            total = target - start
            done = current - start

        if total > 0:
            percent = int((done / total) * 100)
            percent = max(0, min(percent, 100))
 
    journal_entries = user.get("journal", [])

    return render_template(
        "dashboard.html",
        user=user,
        weights=weights,
        dates=dates,
        waist=waist,
        chest=chest,
        hips=hips,
        arms=arms,
        percent=percent,
        start=start,
        current=current,
        target=target,
        journal_entries=journal_entries
    )



@app.route("/journal", methods=["POST"])
def journal():

    # ===== LOGIN CHECK =====
    if "user" not in session:
        return redirect("/login")

    user_email = session["user"]

    # ===== GET ENTRY =====
    entry_text = request.form.get("entry")

    if entry_text:

        users.update_one(
            {"email": user_email},
            {
                "$push": {
                    "journal": {
                        "text": entry_text,
                        "date": datetime.now()
                    }
                }
            }
        )

    return redirect("/dashboard")

@app.route("/delete_entry/<int:index>")
def delete_entry(index):

    if "user" not in session:
        return redirect("/login")

    user = users.find_one({"email": session["user"]})

    journal = user.get("journal", [])

    if 0 <= index < len(journal):
        journal.pop(index)

        users.update_one(
            {"email": session["user"]},
            {"$set": {"journal": journal}}
        )

    return redirect("/dashboard")


@app.route("/download_progress")
def download_progress():

    # ===== LOGIN CHECK =====
    if "user" not in session:
        return redirect("/login")

    # ===== GET USER DATA =====
    user = users.find_one({"email": session["user"]})

    if not user:
        return redirect("/login")

    # ===== GET PROGRESS DATA =====
    progress = user.get("progress_full", [])

    # ===== GENERATE HTML =====
    html = render_template(
        "progress_pdf.html",
        progress=progress,
        user=user
    )

    # ===== CREATE PDF =====
    pdf = HTML(string=html).write_pdf()

    # ===== SEND RESPONSE =====
    response = make_response(pdf)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = "attachment; filename=progress_report.pdf"

    return response



# =========================
# FORGOT PASSWORD
# =========================
@app.route("/forgot", methods=["GET","POST"])
def forgot():

    if request.method == "POST":

        email = request.form["email"]
        user = users.find_one({"email": email})

        if user:

            otp = str(random.randint(100000, 999999))

            session["reset_email"] = email
            session["otp"] = otp

            try:

                sender_email = os.getenv("EMAIL_USER")
                app_password = os.getenv("EMAIL_PASS")

                
                
                msg = MIMEText(f"Your OTP is {otp}")
                msg["Subject"] = "HealthCoach OTP"
                msg["From"] = sender_email
                msg["To"] = email

                server = smtplib.SMTP("smtp-relay.brevo.com", 587)
                server.starttls()
                server.login(sender_email, app_password)
                server.send_message(msg)
                server.quit()

                flash("OTP sent to your email", "success")
                return redirect("/verify")

            except Exception as e:
                print("Email Error:", e)
                flash(f"Error sending email: {e}")

        else:
            flash("Email not found", "error")

    return render_template("forgot.html")

# =========================
# VERIFY OTP
# =========================
@app.route("/verify", methods=["GET","POST"])
def verify():

    if request.method == "POST":

        if request.form["otp"] == session.get("otp"):
            flash("OTP verified successfully", "success")
            return redirect("/reset")
        else:
            flash("Invalid OTP", "error")

    return render_template("verify.html")

# =========================
# RESET PASSWORD
# =========================
@app.route("/reset", methods=["GET","POST"])
def reset():

    if "reset_email" not in session:
        return redirect("/forgot")

    if request.method == "POST":

        hashed_password = generate_password_hash(request.form["password"])

        users.update_one(
            {"email": session["reset_email"]},
            {"$set": {"password": hashed_password}}
        )

        session.clear()

        flash("Password updated successfully", "success")
        return redirect("/login")

    return render_template("reset.html")

# =========================
# LOGOUT
# =========================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# =========================
# RUN
# =========================

def open_browser():
    webbrowser.open("http://127.0.0.1:5000")

if __name__ == "__main__":
    threading.Timer(1, open_browser).start()
    port = int(os.environ.get("PORT", 10000))

    app.run(host="0.0.0.0", port=port)