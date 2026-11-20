from flask import Flask, jsonify, render_template
import numpy as np
from sklearn.cluster import KMeans
from sklearn.linear_model import LinearRegression
from datetime import datetime, timedelta
import random

app = Flask(__name__)

# ============================================================
# MALL ZONES CONFIGURATION
# ============================================================

ZONES = {
    "Zone A": {"type": "Retail", "base_energy": 120, "base_staff": 8},
    "Zone B": {"type": "Retail", "base_energy": 100, "base_staff": 6},
    "Zone C": {"type": "Retail", "base_energy": 90, "base_staff": 5},
    "Food Court": {"type": "Dining", "base_energy": 150, "base_staff": 12},
    "Entertainment": {"type": "Leisure", "base_energy": 200, "base_staff": 10}
}

# Current state (simulated real-time data)
zone_data = {}
historical_data = []  # For ML analysis

customer_transactions = []  # Individual-level simulated behaviour

# ============================================================
# SMART PARKING SYSTEM CONFIGURATION
# ============================================================

PARKING_CONFIG = {
    "total_slots": 500,
    "base_price_per_hour": 20,  # ₹20/hour base rate
    "zones": ["Ground Floor", "First Floor", "Second Floor", "VIP"]
}

# Parking state (simulated IoT sensor data)
parking_data = {
    "total_slots": 500,
    "occupied_slots": 350,
    "available_slots": 150,
    "occupancy_percent": 70.0,
    "average_duration": 120,  # minutes
    "entry_rate": 5,  # vehicles per minute
    "exit_rate": 3,  # vehicles per minute
    "waiting_time": 0,  # minutes
    "current_price": 20
}

parking_history = []  # For prediction

# ============================================================
# CAMERA STATUS MONITORING SYSTEM (IoT Health)
# ============================================================

# Camera configuration
CAMERAS = [
    {"id": "cam_001", "name": "Main Entrance Camera", "location": "Main Entrance", "type": "Surveillance"},
    {"id": "cam_002", "name": "Food Court Camera", "location": "Food Court", "type": "Monitoring"},
    {"id": "cam_003", "name": "Parking Entry Camera", "location": "Parking Entry", "type": "ANPR"},
    {"id": "cam_004", "name": "Parking Exit Camera", "location": "Parking Exit", "type": "ANPR"},
    {"id": "cam_005", "name": "Zone A Camera", "location": "Zone A", "type": "Surveillance"},
    {"id": "cam_006", "name": "Zone B Camera", "location": "Zone B", "type": "Surveillance"},
    {"id": "cam_007", "name": "Zone C Camera", "location": "Zone C", "type": "Monitoring"},
    {"id": "cam_008", "name": "Entertainment Zone Camera", "location": "Entertainment", "type": "Surveillance"}
]

# Camera state tracking
camera_status = {}
HEARTBEAT_THRESHOLD = 60  # seconds - if no heartbeat for 60s, camera is offline

def initialize_cameras():
    """Initialize all cameras as active"""
    now = datetime.now()
    for camera in CAMERAS:
        camera_status[camera["id"]] = {
            "name": camera["name"],
            "location": camera["location"],
            "type": camera["type"],
            "status": "active",  # active, offline, error
            "last_heartbeat": now,
            "uptime_percent": 99.5
        }

def simulate_camera_heartbeat():
    """Simulate camera heartbeat and random failures"""
    now = datetime.now()
    
    for camera_id, status in camera_status.items():
        # Randomly simulate failures (5% chance per update)
        if random.random() < 0.05:
            # Camera failure
            if status["status"] == "active":
                # Randomly choose offline or error
                status["status"] = "offline" if random.random() < 0.7 else "error"
                status["last_heartbeat"] = now - timedelta(seconds=random.randint(60, 300))
        else:
            # Normal operation - update heartbeat
            if status["status"] == "active":
                status["last_heartbeat"] = now
                status["uptime_percent"] = max(95.0, status["uptime_percent"] + random.uniform(-0.1, 0.1))
            elif status["status"] in ["offline", "error"]:
                # Random recovery (20% chance)
                if random.random() < 0.20:
                    status["status"] = "active"
                    status["last_heartbeat"] = now
                    status["uptime_percent"] = 98.0
        
        # Check if camera should be marked offline based on heartbeat
        time_since_heartbeat = (now - status["last_heartbeat"]).total_seconds()
        if time_since_heartbeat > HEARTBEAT_THRESHOLD and status["status"] == "active":
            status["status"] = "offline"

def get_camera_health_summary():
    """Get overall camera system health"""
    active_count = sum(1 for s in camera_status.values() if s["status"] == "active")
    offline_count = sum(1 for s in camera_status.values() if s["status"] == "offline")
    error_count = sum(1 for s in camera_status.values() if s["status"] == "error")
    total_count = len(camera_status)
    
    if offline_count == 0 and error_count == 0:
        summary = "All cameras operational"
        status_level = "healthy"
    elif offline_count + error_count <= 2:
        summary = f"{offline_count + error_count} camera(s) offline - attention required"
        status_level = "warning"
    else:
        summary = f"{offline_count + error_count} cameras offline - critical issue"
        status_level = "critical"
    
    return {
        "summary": summary,
        "status_level": status_level,
        "active": active_count,
        "offline": offline_count,
        "error": error_count,
        "total": total_count,
        "health_percent": round((active_count / total_count) * 100, 1)
    }

# Initialize cameras on startup
initialize_cameras()

# ============================================================
# EVENT-AWARE SYSTEM (Movies, Events, Festivals)
# ============================================================

# Simulated event schedule
EVENTS = [
    {"type": "movie", "name": "Action Movie", "start": "14:00", "end": "16:15", "audience": 200},
    {"type": "movie", "name": "Comedy Movie", "start": "18:00", "end": "20:00", "audience": 180},
    {"type": "movie", "name": "Thriller Movie", "start": "20:30", "end": "22:45", "audience": 220},
    {"type": "event", "name": "Weekend Sale", "start": "10:00", "end": "22:00", "audience": 500, "days": [5, 6]},  # Sat, Sun
    {"type": "festival", "name": "Festival Day", "start": "09:00", "end": "23:00", "audience": 800, "date": None}  # Can be set
]

def get_upcoming_events():
    """Get events happening in the next 2 hours"""
    now = datetime.now()
    upcoming = []
    
    for event in EVENTS:
        start_time = datetime.strptime(event["start"], "%H:%M").time()
        end_time = datetime.strptime(event["end"], "%H:%M").time()
        current_time = now.time()
        
        # Check if event is happening now or soon
        if start_time <= current_time <= end_time:
            # Event is happening now
            event_start = datetime.combine(now.date(), start_time)
            event_end = datetime.combine(now.date(), end_time)
            if event_end > now:
                upcoming.append({
                    "event": event,
                    "type": "current",
                    "time_until_end": (event_end - now).total_seconds() / 60
                })
        elif start_time > current_time:
            # Event is upcoming
            event_start = datetime.combine(now.date(), start_time)
            time_until = (event_start - now).total_seconds() / 60
            if time_until <= 120:  # Next 2 hours
                upcoming.append({
                    "event": event,
                    "type": "upcoming",
                    "time_until": time_until
                })
    
    return upcoming

def predict_exit_rush():
    """Predict exit rush based on movie end times and events"""
    now = datetime.now()
    predictions = []
    
    for event in EVENTS:
        if event["type"] == "movie":
            end_time = datetime.strptime(event["end"], "%H:%M").time()
            event_end = datetime.combine(now.date(), end_time)
            
            # Check if movie ending in next 30 minutes
            time_diff = (event_end - now).total_seconds() / 60
            if 0 <= time_diff <= 30:
                expected_exits = int(event.get("audience", 200) * 0.7)  # 70% have cars
                predictions.append({
                    "event": event["name"],
                    "time": event["end"],
                    "expected_exits": expected_exits,
                    "minutes_until": int(time_diff),
                    "message": f"High exit traffic expected at {event['end']} due to {event['name']} ending"
                })
    
    return predictions

# ============================================================
# DATA SIMULATION ENGINE
# ============================================================

def generate_realistic_footfall(zone_name, hour):
    """Generate realistic customer footfall based on zone type and time"""
    base_patterns = {
        "Zone A": {"peak": [11, 12, 13, 18, 19, 20], "base": 50, "peak_mult": 2.5},
        "Zone B": {"peak": [12, 13, 14, 19, 20], "base": 40, "peak_mult": 2.2},
        "Zone C": {"peak": [10, 11, 15, 16, 17], "base": 35, "peak_mult": 2.0},
        "Food Court": {"peak": [12, 13, 14, 19, 20, 21], "base": 80, "peak_mult": 3.0},
        "Entertainment": {"peak": [18, 19, 20, 21, 22], "base": 60, "peak_mult": 2.8}
    }
    
    pattern = base_patterns.get(zone_name, {"peak": [], "base": 50, "peak_mult": 2.0})
    is_peak = hour in pattern["peak"]
    multiplier = pattern["peak_mult"] if is_peak else 1.0
    
    # Add randomness
    footfall = int(pattern["base"] * multiplier * random.uniform(0.8, 1.2))
    return max(10, footfall)

def calculate_energy_usage(footfall, base_energy):
    """Calculate energy usage based on footfall"""
    # More people = more AC, lighting, escalators
    usage = base_energy * (1 + footfall / 200)
    return round(usage, 1)

def calculate_staff_needed(footfall, base_staff):
    """Calculate staff requirement based on footfall"""
    # More people = need more staff
    needed = base_staff + int(footfall / 30)
    return needed

def calculate_dwell_time(zone_name, footfall):
    """Calculate average dwell time in minutes"""
    dwell_times = {
        "Zone A": 45,
        "Zone B": 40,
        "Zone C": 35,
        "Food Court": 60,
        "Entertainment": 90
    }
    base = dwell_times.get(zone_name, 45)
    # Slight variation based on crowd
    return round(base * random.uniform(0.9, 1.1), 1)

def simulate_real_time_data():
    """Generate current real-time data for all zones"""
    current_hour = datetime.now().hour
    current_data = {}
    
    for zone_name, zone_config in ZONES.items():
        footfall = generate_realistic_footfall(zone_name, current_hour)
        energy = calculate_energy_usage(footfall, zone_config["base_energy"])
        staff_needed = calculate_staff_needed(footfall, zone_config["base_staff"])
        staff_current = zone_config["base_staff"]  # Current staff allocation
        dwell_time = calculate_dwell_time(zone_name, footfall)
        
        current_data[zone_name] = {
            "footfall": footfall,
            "energy_usage": energy,
            "staff_needed": staff_needed,
            "staff_current": staff_current,
            "dwell_time": dwell_time,
            "timestamp": datetime.now().isoformat()
        }
    
    zone_data.update(current_data)
    
    # Store historical data (last 24 hours simulation)
    historical_data.append({
        "timestamp": datetime.now(),
        "zones": current_data.copy()
    })
    
    # Keep only last 24 hours of data
    if len(historical_data) > 24:
        historical_data.pop(0)
    
    return current_data

# ============================================================
# CUSTOMER-LEVEL SIMULATION & ANALYTICS
# ============================================================

PRODUCT_CATALOG = [
    "Electronics",
    "Clothing",
    "Footwear",
    "Groceries",
    "Cosmetics",
    "Toys",
    "Home Decor",
    "Cinema Tickets",
    "Food Court Meal",
    "Accessories"
]


def simulate_customer_transactions(num_customers=60):
    """Simulate individual customer transaction/behaviour records"""
    global customer_transactions
    customer_transactions = []
    
    for i in range(num_customers):
        customer_id = f"C{i+1:03d}"
        
        # Behavioural archetypes to create natural clusters
        r = random.random()
        if r < 0.3:
            # Loyal spender: visits frequently, stays long, spends high
            visit_frequency = random.randint(8, 15)
            dwell_time = random.uniform(60, 120)
            total_spent = random.uniform(3000, 8000)
        elif r < 0.7:
            # Regular shopper: moderate frequency, dwell and spend
            visit_frequency = random.randint(3, 7)
            dwell_time = random.uniform(30, 60)
            total_spent = random.uniform(800, 2500)
        else:
            # Quick / low-intent visitor: short dwell, low spend
            visit_frequency = random.randint(1, 3)
            dwell_time = random.uniform(10, 30)
            total_spent = random.uniform(0, 800)
        
        num_items = random.randint(1, 4)
        items = random.sample(PRODUCT_CATALOG, num_items)
        
        customer_transactions.append({
            "customer_id": customer_id,
            "items": items,
            "total_spent": round(total_spent, 2),
            "visit_frequency": visit_frequency,
            "dwell_time": round(dwell_time, 1)
        })


def segment_customers_kmeans():
    """Cluster customers into behavioural segments using K-Means"""
    if len(customer_transactions) < 3:
        return {"segments": {}, "assignments": []}
    
    features = []
    for tx in customer_transactions:
        features.append([
            tx["total_spent"],
            tx["visit_frequency"],
            tx["dwell_time"]
        ])
    
    X = np.array(features, dtype=float)
    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X)
    centers = kmeans.cluster_centers_
    
    # Map clusters to business-friendly labels
    indices = list(range(3))
    by_spend = sorted(indices, key=lambda idx: centers[idx][0], reverse=True)
    by_dwell = sorted(indices, key=lambda idx: centers[idx][2])
    
    high_spend_idx = by_spend[0]
    low_dwell_idx = by_dwell[0]
    
    label_map = {}
    label_map[high_spend_idx] = "Loyal Spenders"
    label_map[low_dwell_idx] = "Quick Buyers"
    
    for idx in indices:
        if idx not in label_map:
            label_map[idx] = "Window Shoppers"
    
    segments_summary = {}
    assignments = []
    
    for i, tx in enumerate(customer_transactions):
        seg_name = label_map[labels[i]]
        assignment = {
            **tx,
            "segment": seg_name
        }
        assignments.append(assignment)
        
        if seg_name not in segments_summary:
            segments_summary[seg_name] = {
                "count": 0,
                "total_spent": 0.0,
                "total_dwell": 0.0,
                "total_frequency": 0
            }
        
        agg = segments_summary[seg_name]
        agg["count"] += 1
        agg["total_spent"] += tx["total_spent"]
        agg["total_dwell"] += tx["dwell_time"]
        agg["total_frequency"] += tx["visit_frequency"]
    
    for seg_name, agg in segments_summary.items():
        count = agg["count"]
        agg["avg_spent"] = round(agg["total_spent"] / count, 1)
        agg["avg_dwell"] = round(agg["total_dwell"] / count, 1)
        agg["avg_frequency"] = round(agg["total_frequency"] / count, 1)
        del agg["total_spent"]
        del agg["total_dwell"]
        del agg["total_frequency"]
    
    return {
        "segments": segments_summary,
        "assignments": assignments
    }


def analyze_product_associations(min_support=0.1, min_count=3):
    """Derive frequently co-purchased item pairs for layout optimization"""
    if not customer_transactions:
        return []
    
    pair_counts = {}
    total_tx = len(customer_transactions)
    
    for tx in customer_transactions:
        items = sorted(set(tx["items"]))
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                pair = (items[i], items[j])
                pair_counts[pair] = pair_counts.get(pair, 0) + 1
    
    recommendations = []
    
    for (a, b), count in pair_counts.items():
        support = count / total_tx
        if count >= min_count and support >= min_support:
            recommendations.append({
                "items": [a, b],
                "count": count,
                "support": round(support, 2),
                "recommendation": f"Place {a} and {b} closer together to increase basket size"
            })
    
    recommendations.sort(key=lambda r: r["count"], reverse=True)
    return recommendations


def generate_offer(segment_name):
    """Generate a simple personalized offer based on customer segment"""
    if segment_name == "Loyal Spenders":
        return {
            "title": "Premium Loyalty Reward",
            "message": "Exclusive 15% off on your favourite brands today.",
            "coupon": "LOYAL15"
        }
    if segment_name == "Quick Buyers":
        return {
            "title": "Express Checkout Perk",
            "message": "Get 10% off on quick purchases under 30 minutes.",
            "coupon": "QUICK10"
        }
    if segment_name == "Window Shoppers":
        return {
            "title": "Try & Save Offer",
            "message": "Convert browsing into savings: ₹200 off on bills above ₹1500.",
            "coupon": "TRY200"
        }
    return {
        "title": "Smart Mall Offer",
        "message": "Enjoy special savings across the mall today.",
        "coupon": "MALL5"
    }


def build_customer_insights():
    """End-to-end pipeline for customer insights, layout, and parking hints"""
    simulate_customer_transactions()
    segmentation_result = segment_customers_kmeans()
    layout_recommendations = analyze_product_associations()
    
    segments = segmentation_result["segments"]
    assignments = segmentation_result["assignments"]
    
    # Attach offers to recent transactions
    enriched_transactions = []
    for assignment in assignments:
        offer = generate_offer(assignment["segment"])
        enriched_transactions.append({
            **assignment,
            "offer": offer
        })
    
    # Derive parking strategy from segment mix
    loyal_count = segments.get("Loyal Spenders", {}).get("count", 0)
    quick_count = segments.get("Quick Buyers", {}).get("count", 0)
    
    vip_spots = max(5, loyal_count // 2)
    short_term_spots = max(10, quick_count)
    
    parking_insights = {
        "vip_spots_recommended": vip_spots,
        "short_term_spots_recommended": short_term_spots,
        "message": f"Reserve ~{vip_spots} VIP spots near main entrances for Loyal Spenders "
                   f"and ~{short_term_spots} short-term spots close to exits for Quick Buyers."
    }
    
    # Limit feed size for UI
    recent_feed = sorted(
        enriched_transactions,
        key=lambda t: t["total_spent"],
        reverse=True
    )[:20]
    
    return {
        "segments": segments,
        "layout_recommendations": layout_recommendations,
        "recent_transactions": recent_feed,
        "parking": parking_insights
    }

# ============================================================
# AI/ML MODELS
# ============================================================

def perform_customer_clustering():
    """K-Means clustering to segment customers by behavior"""
    if len(historical_data) < 10:
        return {"clusters": [], "message": "Insufficient data for clustering"}
    
    # Prepare features: [footfall, energy_usage, dwell_time]
    features = []
    zone_names = []
    
    for record in historical_data[-12:]:  # Last 12 hours
        for zone_name, zone_info in record["zones"].items():
            features.append([
                zone_info["footfall"],
                zone_info["energy_usage"],
                zone_info["dwell_time"]
            ])
            zone_names.append(zone_name)
    
    if len(features) < 3:
        return {"clusters": [], "message": "Insufficient data"}
    
    # K-Means clustering (3 clusters: Low, Medium, High traffic)
    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    clusters = kmeans.fit_predict(features)
    
    # Analyze clusters (convert numpy types to native Python for JSON serialization)
    cluster_labels = ["Low Traffic", "Medium Traffic", "High Traffic"]
    cluster_analysis = {}
    
    for i, label in enumerate(cluster_labels):
        cluster_points = [features[j] for j in range(len(features)) if clusters[j] == i]
        if cluster_points:
            avg_footfall = float(np.mean([p[0] for p in cluster_points]))
            cluster_analysis[label] = {
                "avg_footfall": round(avg_footfall, 1),
                "count": len(cluster_points)
            }
    
    return {
        "clusters": cluster_analysis,
        "message": "Customer behavior segmented successfully"
    }

def predict_next_hour_footfall():
    """Predict footfall for next hour using Linear Regression"""
    if len(historical_data) < 6:
        return {}
    
    predictions = {}
    next_hour = (datetime.now().hour + 1) % 24
    
    for zone_name in ZONES.keys():
        # Prepare training data: [hour, previous_footfall] -> next_footfall
        X_train = []
        y_train = []
        
        for i in range(len(historical_data) - 1):
            hour = historical_data[i]["timestamp"].hour
            footfall = historical_data[i]["zones"][zone_name]["footfall"]
            next_footfall = historical_data[i + 1]["zones"][zone_name]["footfall"]
            
            X_train.append([hour, footfall])
            y_train.append(next_footfall)
        
        if len(X_train) < 3:
            predictions[zone_name] = generate_realistic_footfall(zone_name, next_hour)
            continue
        
        # Train model
        model = LinearRegression()
        model.fit(X_train, y_train)
        
        # Predict
        current_footfall = zone_data[zone_name]["footfall"]
        prediction = model.predict([[next_hour, current_footfall]])[0]
        predictions[zone_name] = max(10, int(prediction))
    
    return predictions

# ============================================================
# SMART RESOURCE MANAGEMENT
# ============================================================

def analyze_peak_hours():
    """Identify peak hours from historical data"""
    if len(historical_data) < 6:
        return {"peak_hours": [], "message": "Insufficient data"}
    
    hourly_footfall = {}
    
    for record in historical_data:
        hour = record["timestamp"].hour
        total_footfall = sum(z["footfall"] for z in record["zones"].values())
        
        if hour not in hourly_footfall:
            hourly_footfall[hour] = []
        hourly_footfall[hour].append(total_footfall)
    
    # Calculate average footfall per hour (convert to native float for JSON serialization)
    avg_by_hour = {h: float(np.mean(vals)) for h, vals in hourly_footfall.items()}
    
    if not avg_by_hour:
        return {"peak_hours": [], "message": "No data available"}
    
    threshold = float(np.mean(list(avg_by_hour.values())))
    peak_hours = [int(h) for h, avg in avg_by_hour.items() if avg > threshold * 1.2]
    
    return {
        "peak_hours": sorted(peak_hours),
        "avg_footfall_by_hour": {str(h): round(float(avg), 1) for h, avg in avg_by_hour.items()}
    }

def identify_high_low_traffic_zones():
    """Identify high and low traffic zones"""
    if not zone_data:
        return {"high_traffic": [], "low_traffic": []}
    
    avg_footfall = np.mean([z["footfall"] for z in zone_data.values()])
    
    high_traffic = []
    low_traffic = []
    
    for zone_name, data in zone_data.items():
        if data["footfall"] > avg_footfall * 1.3:
            high_traffic.append(zone_name)
        elif data["footfall"] < avg_footfall * 0.7:
            low_traffic.append(zone_name)
    
    return {"high_traffic": high_traffic, "low_traffic": low_traffic}

# ============================================================
# AI RECOMMENDATION ENGINE
# ============================================================

def generate_recommendations():
    """Generate AI-powered recommendations for resource optimization"""
    recommendations = []
    
    if not zone_data:
        return recommendations
    
    # Analyze traffic zones
    traffic_analysis = identify_high_low_traffic_zones()
    
    # Recommendations for low-traffic zones
    for zone_name in traffic_analysis["low_traffic"]:
        current_energy = zone_data[zone_name]["energy_usage"]
        base_energy = ZONES[zone_name]["base_energy"]
        reduction = int((current_energy - base_energy * 0.7) / current_energy * 100)
        
        if reduction > 10:
            recommendations.append({
                "type": "energy",
                "priority": "medium",
                "zone": zone_name,
                "action": f"Reduce lighting in {zone_name} by {reduction}%",
                "reason": "Low customer footfall detected",
                "savings": f"Estimated savings: {reduction * 2} kWh/hour"
            })
            
            recommendations.append({
                "type": "energy",
                "priority": "medium",
                "zone": zone_name,
                "action": f"Reduce AC in {zone_name} by {reduction}%",
                "reason": "Low customer footfall detected",
                "savings": f"Estimated savings: {reduction * 3} kWh/hour"
            })
    
    # Recommendations for high-traffic zones
    for zone_name in traffic_analysis["high_traffic"]:
        staff_gap = zone_data[zone_name]["staff_needed"] - zone_data[zone_name]["staff_current"]
        
        if staff_gap > 2:
            recommendations.append({
                "type": "staff",
                "priority": "high",
                "zone": zone_name,
                "action": f"Increase staff in {zone_name} by {staff_gap} members",
                "reason": "High customer footfall requires more support",
                "impact": "Improves customer service and reduces wait times"
            })
    
    # Predictions for next hour
    predictions = predict_next_hour_footfall()
    current_hour = datetime.now().hour
    next_hour = (current_hour + 1) % 24
    
    for zone_name, predicted_footfall in predictions.items():
        current_footfall = zone_data[zone_name]["footfall"]
        increase = ((predicted_footfall - current_footfall) / current_footfall * 100) if current_footfall > 0 else 0
        
        if increase > 20:
            recommendations.append({
                "type": "prediction",
                "priority": "high",
                "zone": zone_name,
                "action": f"High crowd predicted in {zone_name} next hour ({next_hour}:00)",
                "reason": f"AI predicts {int(increase)}% increase in footfall",
                "suggestion": "Prepare additional resources and staff"
            })
        elif increase < -20:
            recommendations.append({
                "type": "prediction",
                "priority": "low",
                "zone": zone_name,
                "action": f"Low crowd predicted in {zone_name} next hour ({next_hour}:00)",
                "reason": f"AI predicts {int(abs(increase))}% decrease in footfall",
                "suggestion": "Consider reducing energy consumption"
            })
    
    # Peak hour recommendations
    peak_analysis = analyze_peak_hours()
    current_hour = datetime.now().hour
    
    if current_hour in peak_analysis.get("peak_hours", []):
        recommendations.append({
            "type": "peak_hour",
            "priority": "high",
            "zone": "All Zones",
            "action": "Peak hour detected - Optimize all resources",
            "reason": f"Hour {current_hour}:00 is a peak traffic period",
            "suggestion": "Ensure maximum staff allocation and energy efficiency"
        })
    
    return recommendations

# ============================================================
# SMART PARKING SYSTEM (IoT SIMULATION)
# ============================================================

def simulate_parking_iot():
    """Simulate IoT sensors detecting parking slot status"""
    now = datetime.now()
    hour = now.hour
    
    # Base occupancy varies by time
    base_occupancy = {
        "morning": (8, 12, 0.4),   # 8-12: 40% occupancy
        "afternoon": (12, 18, 0.7),  # 12-18: 70% occupancy
        "evening": (18, 22, 0.85),   # 18-22: 85% occupancy
        "night": (22, 8, 0.3)        # 22-8: 30% occupancy
    }
    
    # Determine time period
    if 8 <= hour < 12:
        target_occ = 0.4
    elif 12 <= hour < 18:
        target_occ = 0.7
    elif 18 <= hour < 22:
        target_occ = 0.85
    else:
        target_occ = 0.3
    
    # Event-based adjustment
    upcoming_events = get_upcoming_events()
    for event_info in upcoming_events:
        if event_info["type"] == "current":
            target_occ = min(0.95, target_occ + 0.1)  # Increase during events
    
    total_slots = parking_data["total_slots"]
    current_occupied = parking_data["occupied_slots"]
    target_occupied = int(target_occ * total_slots)
    
    diff = target_occupied - current_occupied
    adjustment = int(diff * 0.1)
    noise = random.randint(-5, 5)
    net_change = adjustment + noise
    
    max_step = max(5, int(total_slots * 0.05))
    if net_change > max_step:
        net_change = max_step
    elif net_change < -max_step:
        net_change = -max_step
    
    new_occupied = current_occupied + net_change
    new_occupied = max(0, min(new_occupied, total_slots))
    
    if net_change >= 0:
        entry_rate = max(1, net_change)
        exit_rate = random.randint(0, max(1, net_change // 2))
    else:
        exit_rate = max(1, -net_change)
        entry_rate = random.randint(0, max(1, (-net_change) // 2))
    
    parking_data["occupied_slots"] = new_occupied
    parking_data["available_slots"] = total_slots - new_occupied
    parking_data["occupancy_percent"] = round((new_occupied / total_slots) * 100, 1)
    parking_data["entry_rate"] = entry_rate
    parking_data["exit_rate"] = exit_rate
    
    # Calculate waiting time
    if parking_data["available_slots"] == 0:
        # Full parking - estimate wait time
        avg_exit_time = parking_data["average_duration"] / 60  # hours
        exits_per_hour = exit_rate * 60
        if exits_per_hour > 0:
            wait_hours = parking_data["occupied_slots"] / exits_per_hour
            parking_data["waiting_time"] = max(0, int(wait_hours * 60))
        else:
            parking_data["waiting_time"] = 999  # No exits expected
    else:
        parking_data["waiting_time"] = 0
    
    # Store history
    parking_history.append({
        "timestamp": now,
        "occupied": new_occupied,
        "occupancy_percent": parking_data["occupancy_percent"],
        "entry_rate": entry_rate,
        "exit_rate": exit_rate
    })
    
    # Keep last 24 hours
    if len(parking_history) > 144:  # 24 hours * 6 (10-min intervals)
        parking_history.pop(0)
    
    return parking_data

# ============================================================
# AI-DRIVEN DYNAMIC PRICING
# ============================================================

def calculate_dynamic_pricing():
    """AI-based dynamic pricing based on occupancy, events, and predictions"""
    base_price = PARKING_CONFIG["base_price_per_hour"]
    occupancy = parking_data["occupancy_percent"] / 100
    
    # Base pricing multiplier based on occupancy
    if occupancy < 0.4:
        # Low occupancy - discount
        price_multiplier = 0.7
        price_reason = "Low occupancy - Discount pricing"
    elif occupancy < 0.6:
        # Normal occupancy
        price_multiplier = 1.0
        price_reason = "Normal occupancy - Standard pricing"
    elif occupancy < 0.85:
        # High occupancy - slight increase
        price_multiplier = 1.3
        price_reason = "High occupancy - Peak pricing"
    else:
        # Very high occupancy - surge pricing
        price_multiplier = 1.8
        price_reason = "Very high occupancy - Surge pricing"
    
    # Event-based surge pricing
    upcoming_events = get_upcoming_events()
    exit_predictions = predict_exit_rush()
    
    event_surge = 1.0
    if exit_predictions:
        # Movie ending soon - expect rush
        event_surge = 2.0  # Double price
        price_reason = f"Event ending soon - Surge pricing active"
    elif any(e["type"] == "current" for e in upcoming_events):
        # Event happening now
        event_surge = 1.5
        price_reason = "Event in progress - Premium pricing"
    
    # Weekend pricing
    is_weekend = datetime.now().weekday() >= 5  # Sat or Sun
    weekend_multiplier = 1.2 if is_weekend else 1.0
    
    # Final price
    final_price = int(base_price * price_multiplier * event_surge * weekend_multiplier)
    parking_data["current_price"] = final_price
    
    return {
        "price": final_price,
        "base_price": base_price,
        "multiplier": round(price_multiplier * event_surge * weekend_multiplier, 2),
        "reason": price_reason,
        "occupancy": parking_data["occupancy_percent"]
    }

# ============================================================
# PARKING PREDICTION (AI)
# ============================================================

def predict_parking_availability():
    """Predict parking availability for next hour using Linear Regression"""
    if len(parking_history) < 6:
        return {}
    
    # Prepare training data: [hour, current_occupancy] -> next_occupancy
    X_train = []
    y_train = []
    
    for i in range(len(parking_history) - 1):
        hour = parking_history[i]["timestamp"].hour
        occupancy = parking_history[i]["occupancy_percent"]
        next_occupancy = parking_history[i + 1]["occupancy_percent"]
        
        X_train.append([hour, occupancy])
        y_train.append(next_occupancy)
    
    if len(X_train) < 3:
        return {}
    
    # Train model
    model = LinearRegression()
    model.fit(X_train, y_train)
    
    # Predict
    next_hour = (datetime.now().hour + 1) % 24
    current_occupancy = parking_data["occupancy_percent"]
    predicted_occupancy = model.predict([[next_hour, current_occupancy]])[0]
    predicted_occupancy = max(0, min(100, predicted_occupancy))
    
    # Account for events
    upcoming_events = get_upcoming_events()
    for event_info in upcoming_events:
        if event_info["type"] == "upcoming" and event_info["time_until"] <= 60:
            predicted_occupancy = min(100, predicted_occupancy + 15)  # Increase for upcoming event
    
    return {
        "next_hour": next_hour,
        "predicted_occupancy": round(predicted_occupancy, 1),
        "predicted_available": max(0, int(parking_data["total_slots"] * (1 - predicted_occupancy / 100))),
        "trend": "increasing" if predicted_occupancy > current_occupancy else "decreasing"
    }

# ============================================================
# FLASK ROUTES
# ============================================================

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/dashboard-data")
def dashboard_data():
    """Main API endpoint that returns all dashboard data"""
    # Simulate real-time data
    simulate_real_time_data()
    simulate_parking_iot()
    
    # Get AI analysis
    clustering = perform_customer_clustering()
    predictions = predict_next_hour_footfall()
    peak_analysis = analyze_peak_hours()
    traffic_analysis = identify_high_low_traffic_zones()
    
    # Parking AI analysis
    parking_pricing = calculate_dynamic_pricing()
    parking_prediction = predict_parking_availability()
    exit_predictions = predict_exit_rush()
    upcoming_events = get_upcoming_events()
    
    # Customer-level AI (behaviour, segmentation, layout, parking strategy)
    customer_insights = build_customer_insights()
    
    # Camera monitoring
    simulate_camera_heartbeat()
    camera_health = get_camera_health_summary()
    
    # Generate recommendations (including parking)
    recommendations = generate_recommendations()
    
    # Add camera health recommendations
    for camera_id, status in camera_status.items():
        if status["status"] == "offline":
            recommendations.append({
                "type": "camera",
                "priority": "high",
                "zone": status["location"],
                "action": f"{status['name']} offline - monitoring may be affected",
                "reason": f"Camera has been offline for {(datetime.now() - status['last_heartbeat']).total_seconds():.0f} seconds",
                "suggestion": "Check camera connection and power supply"
            })
        elif status["status"] == "error":
            recommendations.append({
                "type": "camera",
                "priority": "high",
                "zone": status["location"],
                "action": f"{status['name']} error detected - requires maintenance",
                "reason": "Camera reporting error status",
                "suggestion": "Schedule maintenance check"
            })
    
    if camera_health["status_level"] == "critical":
        recommendations.append({
            "type": "camera",
            "priority": "high",
            "zone": "System",
            "action": f"Critical: {camera_health['offline'] + camera_health['error']} cameras offline - system health at {camera_health['health_percent']}%",
            "reason": "Multiple camera failures detected",
            "suggestion": "Immediate attention required - check network and power infrastructure"
        })
    
    # Add parking recommendations
    if parking_data["occupancy_percent"] > 90:
        recommendations.append({
            "type": "parking",
            "priority": "high",
            "zone": "Parking",
            "action": f"Parking occupancy {parking_data['occupancy_percent']}% → Enable surge pricing",
            "reason": "Very high occupancy detected",
            "savings": f"Current price: ₹{parking_data['current_price']}/hour"
        })
    
    if parking_data["waiting_time"] > 0:
        recommendations.append({
            "type": "parking",
            "priority": "high",
            "zone": "Parking",
            "action": f"Parking full - Estimated waiting time: {parking_data['waiting_time']} minutes",
            "reason": "No available slots",
            "suggestion": "Consider directing customers to alternative parking"
        })
    
    for exit_pred in exit_predictions:
        recommendations.append({
            "type": "parking",
            "priority": "high",
            "zone": "Parking",
            "action": exit_pred["message"],
            "reason": f"Expected {exit_pred['expected_exits']} vehicles exiting in {exit_pred['minutes_until']} minutes",
            "suggestion": "Prepare for exit rush and adjust pricing"
        })
    
    # Calculate overall statistics (use float() to avoid numpy serialization issues)
    total_footfall = int(sum(z["footfall"] for z in zone_data.values()))
    total_energy = float(sum(z["energy_usage"] for z in zone_data.values()))
    avg_dwell_time = float(np.mean([z["dwell_time"] for z in zone_data.values()]))
    
    return jsonify({
        "zones": zone_data,
        "customer_insights": customer_insights,
        "parking": {
            **parking_data,
            "pricing": parking_pricing,
            "prediction": parking_prediction,
            "exit_predictions": exit_predictions,
            "upcoming_events": upcoming_events
        },
        "statistics": {
            "total_footfall": total_footfall,
            "total_energy_usage": round(total_energy, 1),
            "average_dwell_time": round(avg_dwell_time, 1),
            "current_hour": datetime.now().hour,
            "current_time": datetime.now().strftime("%H:%M:%S")
        },
        "ai_analysis": {
            "clustering": clustering,
            "predictions": predictions,
            "peak_hours": peak_analysis,
            "traffic_zones": traffic_analysis
        },
        "cameras": {
            "health": camera_health,
            "cameras": [
                {
                    "id": cam_id,
                    "name": status["name"],
                    "location": status["location"],
                    "type": status["type"],
                    "status": status["status"],
                    "last_heartbeat": status["last_heartbeat"].strftime("%H:%M:%S"),
                    "uptime_percent": round(status["uptime_percent"], 1)
                }
                for cam_id, status in camera_status.items()
            ]
        },
        "recommendations": recommendations
    })

if __name__ == "__main__":
    # Initialize with some data
    simulate_real_time_data()
    simulate_parking_iot()
    app.run(debug=True, host='0.0.0.0', port=5000)
