"""
SrBoy Security & Optimization Algorithms
Advanced security, fraud prevention, and optimization algorithms for the SrBoy delivery platform.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
import math
from geopy.distance import geodesic
import asyncio
from enum import Enum

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class SecurityAnalyzer:
    """Advanced security analysis and fraud detection algorithms"""
    
    def __init__(self):
        self.risk_thresholds = {
            "carousel_pattern": 0.3,  # 30% acceptance rate threshold
            "speed_anomaly": 80,      # km/h threshold
            "time_anomaly": 2.0,      # Standard deviations
            "identity_match": 0.85    # Face recognition threshold
        }
    
    def analyze_behavioral_risk(self, motoboy_data: Dict) -> Dict:
        """
        Comprehensive behavioral risk analysis for motoboys
        Returns risk score and detailed analysis
        """
        risk_factors = []
        risk_score = 0.0
        
        # 1. Carousel Pattern Analysis
        carousel_risk = self._analyze_carousel_pattern(motoboy_data)
        risk_factors.append(carousel_risk)
        risk_score += carousel_risk["score"]
        
        # 2. Speed Anomaly Detection
        speed_risk = self._analyze_speed_patterns(motoboy_data)
        risk_factors.append(speed_risk)
        risk_score += speed_risk["score"]
        
        # 3. Time Pattern Analysis
        time_risk = self._analyze_time_patterns(motoboy_data)
        risk_factors.append(time_risk)
        risk_score += time_risk["score"]
        
        # 4. Location Consistency
        location_risk = self._analyze_location_consistency(motoboy_data)
        risk_factors.append(location_risk)
        risk_score += location_risk["score"]
        
        # Normalize risk score (0-100)
        final_risk_score = min(risk_score * 25, 100)
        
        # Determine risk level
        if final_risk_score <= 25:
            risk_level = RiskLevel.LOW
        elif final_risk_score <= 50:
            risk_level = RiskLevel.MEDIUM
        elif final_risk_score <= 75:
            risk_level = RiskLevel.HIGH
        else:
            risk_level = RiskLevel.CRITICAL
        
        return {
            "motoboy_id": motoboy_data.get("id"),
            "risk_score": round(final_risk_score, 2),
            "risk_level": risk_level.value,
            "risk_factors": risk_factors,
            "analysis_timestamp": datetime.now().isoformat(),
            "requires_manual_review": risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL],
            "recommended_actions": self._get_recommended_actions(risk_level)
        }
    
    def _analyze_carousel_pattern(self, motoboy_data: Dict) -> Dict:
        """Detect excessive acceptance/cancellation patterns"""
        deliveries = motoboy_data.get("delivery_history", [])
        if len(deliveries) < 10:  # Not enough data
            return {"factor": "carousel_pattern", "score": 0.0, "details": "Insufficient data"}
        
        recent_deliveries = deliveries[-30:]  # Last 30 deliveries
        cancelled_count = sum(1 for d in recent_deliveries if d.get("status") == "cancelled")
        acceptance_rate = (len(recent_deliveries) - cancelled_count) / len(recent_deliveries)
        
        if acceptance_rate < self.risk_thresholds["carousel_pattern"]:
            score = 1.0
            details = f"Low acceptance rate: {acceptance_rate:.2%}"
        else:
            score = 0.0
            details = f"Normal acceptance rate: {acceptance_rate:.2%}"
        
        return {
            "factor": "carousel_pattern",
            "score": score,
            "details": details,
            "acceptance_rate": acceptance_rate
        }
    
    def _analyze_speed_patterns(self, motoboy_data: Dict) -> Dict:
        """Detect abnormal speed patterns indicating GPS spoofing"""
        location_history = motoboy_data.get("location_history", [])
        if len(location_history) < 5:
            return {"factor": "speed_anomaly", "score": 0.0, "details": "Insufficient location data"}
        
        speeds = []
        for i in range(1, len(location_history)):
            prev_loc = location_history[i-1]
            curr_loc = location_history[i]
            
            # Calculate speed between two points
            distance = geodesic(
                (prev_loc["lat"], prev_loc["lng"]),
                (curr_loc["lat"], curr_loc["lng"])
            ).kilometers
            
            time_diff = (
                datetime.fromisoformat(curr_loc["timestamp"]) - 
                datetime.fromisoformat(prev_loc["timestamp"])
            ).total_seconds() / 3600  # Convert to hours
            
            if time_diff > 0:
                speed = distance / time_diff
                speeds.append(speed)
        
        if not speeds:
            return {"factor": "speed_anomaly", "score": 0.0, "details": "No speed data"}
        
        max_speed = max(speeds)
        avg_speed = sum(speeds) / len(speeds)
        
        if max_speed > self.risk_thresholds["speed_anomaly"]:
            score = min(max_speed / 100, 1.0)  # Normalize to 0-1
            details = f"Abnormal max speed: {max_speed:.1f} km/h"
        else:
            score = 0.0
            details = f"Normal speed patterns (max: {max_speed:.1f} km/h)"
        
        return {
            "factor": "speed_anomaly",
            "score": score,
            "details": details,
            "max_speed": max_speed,
            "avg_speed": avg_speed
        }
    
    def _analyze_time_patterns(self, motoboy_data: Dict) -> Dict:
        """Analyze delivery time patterns for anomalies"""
        deliveries = motoboy_data.get("delivery_history", [])
        completed_deliveries = [d for d in deliveries if d.get("status") == "delivered"]
        
        if len(completed_deliveries) < 5:
            return {"factor": "time_anomaly", "score": 0.0, "details": "Insufficient completed deliveries"}
        
        delivery_times = []
        for delivery in completed_deliveries:
            if delivery.get("pickup_confirmed_at") and delivery.get("delivered_at"):
                pickup_time = datetime.fromisoformat(delivery["pickup_confirmed_at"])
                delivery_time = datetime.fromisoformat(delivery["delivered_at"])
                duration = (delivery_time - pickup_time).total_seconds() / 60  # Minutes
                delivery_times.append(duration)
        
        if not delivery_times:
            return {"factor": "time_anomaly", "score": 0.0, "details": "No timing data"}
        
        avg_time = np.mean(delivery_times)
        std_time = np.std(delivery_times)
        
        # Check for anomalously short or long deliveries
        anomalous_deliveries = [
            t for t in delivery_times 
            if abs(t - avg_time) > (self.risk_thresholds["time_anomaly"] * std_time)
        ]
        
        anomaly_rate = len(anomalous_deliveries) / len(delivery_times)
        
        if anomaly_rate > 0.2:  # More than 20% anomalous
            score = anomaly_rate
            details = f"High anomaly rate: {anomaly_rate:.2%}"
        else:
            score = 0.0
            details = f"Normal delivery times (avg: {avg_time:.1f}min)"
        
        return {
            "factor": "time_anomaly",
            "score": score,
            "details": details,
            "avg_delivery_time": avg_time,
            "anomaly_rate": anomaly_rate
        }
    
    def _analyze_location_consistency(self, motoboy_data: Dict) -> Dict:
        """Check for location consistency and impossible movements"""
        location_history = motoboy_data.get("location_history", [])
        base_city = motoboy_data.get("base_city")
        
        if len(location_history) < 3:
            return {"factor": "location_consistency", "score": 0.0, "details": "Insufficient location data"}
        
        # Check for impossible jumps in location
        impossible_jumps = 0
        total_movements = 0
        
        city_boundaries = self._get_city_boundaries(base_city)
        out_of_bounds_count = 0
        
        for i in range(1, len(location_history)):
            prev_loc = location_history[i-1]
            curr_loc = location_history[i]
            
            # Check distance and time for impossible movement
            distance = geodesic(
                (prev_loc["lat"], prev_loc["lng"]),
                (curr_loc["lat"], curr_loc["lng"])
            ).kilometers
            
            time_diff = (
                datetime.fromisoformat(curr_loc["timestamp"]) - 
                datetime.fromisoformat(prev_loc["timestamp"])
            ).total_seconds() / 3600
            
            if time_diff > 0:
                required_speed = distance / time_diff
                if required_speed > 150:  # Impossible for motorcycle
                    impossible_jumps += 1
                total_movements += 1
            
            # Check if location is within city boundaries
            if not self._is_within_city_boundaries(curr_loc, city_boundaries):
                out_of_bounds_count += 1
        
        if total_movements == 0:
            return {"factor": "location_consistency", "score": 0.0, "details": "No movement data"}
        
        jump_rate = impossible_jumps / total_movements
        out_of_bounds_rate = out_of_bounds_count / len(location_history)
        
        total_inconsistency = jump_rate + out_of_bounds_rate
        
        if total_inconsistency > 0.1:
            score = min(total_inconsistency, 1.0)
            details = f"Location inconsistencies detected: {total_inconsistency:.2%}"
        else:
            score = 0.0
            details = "Location patterns consistent"
        
        return {
            "factor": "location_consistency",
            "score": score,
            "details": details,
            "impossible_jumps": impossible_jumps,
            "out_of_bounds_rate": out_of_bounds_rate
        }
    
    def _get_recommended_actions(self, risk_level: RiskLevel) -> List[str]:
        """Get recommended actions based on risk level"""
        actions = {
            RiskLevel.LOW: ["Continue monitoring"],
            RiskLevel.MEDIUM: [
                "Increase monitoring frequency",
                "Request identity verification within 7 days"
            ],
            RiskLevel.HIGH: [
                "Immediate identity verification required",
                "Limit to maximum 5 deliveries per day",
                "Manual review of next 10 deliveries"
            ],
            RiskLevel.CRITICAL: [
                "Immediate account suspension",
                "Manual investigation required",
                "Contact motoboy for explanation",
                "Consider permanent ban if fraud confirmed"
            ]
        }
        return actions.get(risk_level, [])
    
    def _get_city_boundaries(self, city: str) -> Dict:
        """Get approximate boundaries for served cities"""
        boundaries = {
            "São Roque": {"lat_min": -23.6, "lat_max": -23.5, "lng_min": -47.2, "lng_max": -47.1},
            "Mairinque": {"lat_min": -23.6, "lat_max": -23.5, "lng_min": -47.2, "lng_max": -47.1},
            "Araçariguama": {"lat_min": -23.5, "lat_max": -23.4, "lng_min": -47.1, "lng_max": -47.0},
            "Alumínio": {"lat_min": -23.6, "lat_max": -23.5, "lng_min": -47.3, "lng_max": -47.2},
            "Ibiúna": {"lat_min": -23.7, "lat_max": -23.6, "lng_min": -47.3, "lng_max": -47.2}
        }
        return boundaries.get(city, {})
    
    def _is_within_city_boundaries(self, location: Dict, boundaries: Dict) -> bool:
        """Check if location is within city boundaries"""
        if not boundaries:
            return True  # If no boundaries defined, assume valid
        
        lat, lng = location["lat"], location["lng"]
        return (
            boundaries["lat_min"] <= lat <= boundaries["lat_max"] and
            boundaries["lng_min"] <= lng <= boundaries["lng_max"]
        )


class IdentityVerifier:
    """Real-time identity verification system"""
    
    def __init__(self):
        self.verification_intervals = {
            "new_user": 7,      # 7 days for new users
            "regular": 30,      # 30 days for regular users
            "high_risk": 1,     # Daily for high-risk users
            "before_payout": 0  # Before high-value payouts
        }
    
    def requires_verification(self, motoboy_data: Dict) -> bool:
        """Check if motoboy requires identity verification"""
        last_verification = motoboy_data.get("last_identity_verification")
        risk_level = motoboy_data.get("risk_level", "low")
        account_age_days = self._calculate_account_age(motoboy_data.get("created_at"))
        pending_payout = motoboy_data.get("wallet_balance", 0)
        
        # New users
        if account_age_days <= 7 and not last_verification:
            return True
        
        # High-risk users
        if risk_level in ["high", "critical"]:
            if not last_verification or self._days_since_verification(last_verification) >= 1:
                return True
        
        # Regular verification cycle
        if not last_verification or self._days_since_verification(last_verification) >= 30:
            return True
        
        # Before high-value payouts
        if pending_payout > 500:  # R$ 500+
            if not last_verification or self._days_since_verification(last_verification) >= 7:
                return True
        
        return False
    
    def simulate_face_verification(self, motoboy_id: str, new_selfie_data: str) -> Dict:
        """Simulate facial recognition verification (would use real API in production)"""
        # In production, this would use Google Vision AI or Azure Face API
        # For demo purposes, we'll simulate the verification
        
        confidence_score = np.random.uniform(0.7, 0.95)  # Simulate confidence
        is_match = confidence_score >= self.risk_thresholds.get("identity_match", 0.85)
        
        return {
            "motoboy_id": motoboy_id,
            "verification_result": "match" if is_match else "no_match",
            "confidence_score": round(confidence_score, 3),
            "timestamp": datetime.now().isoformat(),
            "requires_manual_review": confidence_score < 0.9,
            "verification_method": "facial_recognition"
        }
    
    def verify_data_consistency(self, motoboy_data: Dict) -> Dict:
        """Cross-reference and validate data consistency"""
        inconsistencies = []
        
        # Check name consistency
        google_name = motoboy_data.get("google_profile", {}).get("name", "")
        profile_name = motoboy_data.get("name", "")
        cnh_name = motoboy_data.get("cnh_name", "")  # Would be extracted from CNH OCR
        
        if google_name and profile_name:
            name_similarity = self._calculate_name_similarity(google_name, profile_name)
            if name_similarity < 0.8:
                inconsistencies.append({
                    "type": "name_mismatch",
                    "details": f"Google name vs Profile name similarity: {name_similarity:.2f}",
                    "severity": "medium"
                })
        
        # Check CNH data consistency
        if cnh_name and profile_name:
            cnh_similarity = self._calculate_name_similarity(cnh_name, profile_name)
            if cnh_similarity < 0.9:
                inconsistencies.append({
                    "type": "cnh_name_mismatch", 
                    "details": f"CNH name vs Profile name similarity: {cnh_similarity:.2f}",
                    "severity": "high"
                })
        
        # Check bank account name
        bank_name = motoboy_data.get("bank_info", {}).get("account_holder", "")
        if bank_name and profile_name:
            bank_similarity = self._calculate_name_similarity(bank_name, profile_name)
            if bank_similarity < 0.8:
                inconsistencies.append({
                    "type": "bank_name_mismatch",
                    "details": f"Bank account vs Profile name similarity: {bank_similarity:.2f}",
                    "severity": "high"
                })
        
        consistency_score = max(0, 100 - (len(inconsistencies) * 25))
        
        return {
            "motoboy_id": motoboy_data.get("id"),
            "consistency_score": consistency_score,
            "inconsistencies": inconsistencies,
            "requires_manual_review": len(inconsistencies) > 0,
            "verification_timestamp": datetime.now().isoformat()
        }
    
    def _calculate_account_age(self, created_at: str) -> int:
        """Calculate account age in days"""
        if not created_at:
            return 0
        creation_date = datetime.fromisoformat(created_at)
        return (datetime.now() - creation_date).days
    
    def _days_since_verification(self, last_verification: str) -> int:
        """Calculate days since last verification"""
        verification_date = datetime.fromisoformat(last_verification)
        return (datetime.now() - verification_date).days
    
    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two names"""
        # Simple similarity calculation (in production, use more sophisticated algorithms)
        name1_clean = name1.lower().strip()
        name2_clean = name2.lower().strip()
        
        if name1_clean == name2_clean:
            return 1.0
        
        # Calculate Jaccard similarity of words
        words1 = set(name1_clean.split())
        words2 = set(name2_clean.split())
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0


class RouteOptimizer:
    """Advanced route optimization algorithms"""
    
    def __init__(self):
        self.traffic_api_key = "demo_key"  # Would use real API key in production
    
    def optimize_multiple_deliveries(self, deliveries: List[Dict], motoboy_location: Dict) -> Dict:
        """Optimize route for multiple deliveries"""
        if not deliveries:
            return {"optimized_route": [], "total_distance": 0, "estimated_time": 0}
        
        # Create route points (motoboy -> pickups -> deliveries)
        route_points = [motoboy_location]
        
        # Add pickup points
        for delivery in deliveries:
            route_points.append({
                "type": "pickup",
                "delivery_id": delivery["id"],
                "location": delivery["pickup_address"],
                "priority": delivery.get("priority_score", 0)
            })
        
        # Add delivery points
        for delivery in deliveries:
            route_points.append({
                "type": "delivery",
                "delivery_id": delivery["id"],
                "location": delivery["delivery_address"],
                "priority": delivery.get("priority_score", 0)
            })
        
        # Optimize route using modified TSP algorithm
        optimized_sequence = self._solve_vehicle_routing(route_points)
        
        # Calculate total distance and time
        total_distance = 0
        estimated_time = 0
        
        for i in range(1, len(optimized_sequence)):
            prev_point = optimized_sequence[i-1]
            curr_point = optimized_sequence[i]
            
            distance = geodesic(
                (prev_point["location"]["lat"], prev_point["location"]["lng"]),
                (curr_point["location"]["lat"], curr_point["location"]["lng"])
            ).kilometers
            
            total_distance += distance
            estimated_time += self._estimate_segment_time(distance, prev_point, curr_point)
        
        return {
            "optimized_route": optimized_sequence,
            "total_distance": round(total_distance, 2),
            "estimated_time": round(estimated_time, 0),
            "fuel_savings": self._calculate_fuel_savings(deliveries, optimized_sequence),
            "optimization_score": self._calculate_optimization_score(deliveries, optimized_sequence)
        }
    
    def _solve_vehicle_routing(self, points: List[Dict]) -> List[Dict]:
        """Solve vehicle routing problem with pickup/delivery constraints"""
        # Simplified VRP solution (in production, use OR-Tools or similar)
        
        # Separate pickups and deliveries
        pickups = [p for p in points if p.get("type") == "pickup"]
        deliveries = [p for p in points if p.get("type") == "delivery"]
        start_point = [p for p in points if p.get("type") != "pickup" and p.get("type") != "delivery"][0]
        
        # Sort by priority and proximity
        pickups_sorted = sorted(pickups, key=lambda x: (-x["priority"], 
                               geodesic((start_point["lat"], start_point["lng"]), 
                                      (x["location"]["lat"], x["location"]["lng"])).kilometers))
        
        # Create optimized sequence: pickup -> delivery for each order
        optimized_route = [start_point]
        
        for pickup in pickups_sorted:
            optimized_route.append(pickup)
            # Find corresponding delivery
            delivery = next(d for d in deliveries if d["delivery_id"] == pickup["delivery_id"])
            optimized_route.append(delivery)
        
        return optimized_route
    
    def _estimate_segment_time(self, distance: float, from_point: Dict, to_point: Dict) -> float:
        """Estimate time for route segment considering traffic"""
        base_time = distance / 30 * 60  # 30 km/h average speed, result in minutes
        
        # Add traffic multiplier based on time of day
        current_hour = datetime.now().hour
        if 7 <= current_hour <= 9 or 17 <= current_hour <= 19:  # Rush hours
            traffic_multiplier = 1.5
        elif 11 <= current_hour <= 14:  # Lunch hours
            traffic_multiplier = 1.2
        else:
            traffic_multiplier = 1.0
        
        return base_time * traffic_multiplier
    
    def _calculate_fuel_savings(self, original_deliveries: List[Dict], optimized_route: List[Dict]) -> Dict:
        """Calculate fuel savings from route optimization"""
        # Calculate original route distance (simple pickup -> delivery for each)
        original_distance = 0
        for delivery in original_deliveries:
            pickup_to_delivery = geodesic(
                (delivery["pickup_address"]["lat"], delivery["pickup_address"]["lng"]),
                (delivery["delivery_address"]["lat"], delivery["delivery_address"]["lng"])
            ).kilometers
            original_distance += pickup_to_delivery * 2  # Round trip assumption
        
        # Calculate optimized route distance
        optimized_distance = 0
        for i in range(1, len(optimized_route)):
            segment_distance = geodesic(
                (optimized_route[i-1]["location"]["lat"], optimized_route[i-1]["location"]["lng"]),
                (optimized_route[i]["location"]["lat"], optimized_route[i]["location"]["lng"])
            ).kilometers
            optimized_distance += segment_distance
        
        distance_saved = max(0, original_distance - optimized_distance)
        fuel_price_per_km = 0.15  # R$ 0.15 per km (approximate)
        money_saved = distance_saved * fuel_price_per_km
        
        return {
            "distance_saved_km": round(distance_saved, 2),
            "money_saved": round(money_saved, 2),
            "efficiency_improvement": round((distance_saved / original_distance) * 100, 1) if original_distance > 0 else 0
        }
    
    def _calculate_optimization_score(self, original_deliveries: List[Dict], optimized_route: List[Dict]) -> float:
        """Calculate overall optimization score (0-100)"""
        # Consider factors: distance efficiency, time efficiency, priority handling
        fuel_savings = self._calculate_fuel_savings(original_deliveries, optimized_route)
        efficiency = fuel_savings["efficiency_improvement"]
        
        # Priority score (higher priority orders handled first)
        priority_score = 0
        route_deliveries = [r for r in optimized_route if r.get("type") == "delivery"]
        for i, delivery in enumerate(route_deliveries):
            priority_weight = delivery.get("priority", 0) / 10
            position_penalty = i * 0.1  # Earlier is better
            priority_score += max(0, priority_weight - position_penalty)
        
        # Combine scores
        final_score = (efficiency * 0.7) + (priority_score * 0.3)
        return min(100, max(0, final_score))


class DemandPredictor:
    """Predictive demand analysis and heat map generation"""
    
    def __init__(self):
        self.historical_data = []
        self.city_zones = self._initialize_city_zones()
    
    def generate_demand_heatmap(self, city: str, target_datetime: datetime = None) -> Dict:
        """Generate predictive demand heatmap for a city"""
        if not target_datetime:
            target_datetime = datetime.now() + timedelta(hours=1)
        
        zones = self.city_zones.get(city, [])
        heatmap_data = []
        
        for zone in zones:
            predicted_demand = self._predict_zone_demand(city, zone, target_datetime)
            heatmap_data.append({
                "zone_id": zone["id"],
                "zone_name": zone["name"],
                "center_lat": zone["center"]["lat"],
                "center_lng": zone["center"]["lng"],
                "radius_km": zone["radius"],
                "predicted_demand": predicted_demand["demand_score"],
                "confidence": predicted_demand["confidence"],
                "peak_hours": predicted_demand["peak_hours"],
                "demand_factors": predicted_demand["factors"]
            })
        
        # Sort by demand score
        heatmap_data.sort(key=lambda x: x["predicted_demand"], reverse=True)
        
        return {
            "city": city,
            "prediction_datetime": target_datetime.isoformat(),
            "zones": heatmap_data,
            "top_zones": heatmap_data[:3],  # Top 3 demand zones
            "overall_demand": self._calculate_city_demand(heatmap_data),
            "recommendations": self._generate_positioning_recommendations(heatmap_data)
        }
    
    def _predict_zone_demand(self, city: str, zone: Dict, target_datetime: datetime) -> Dict:
        """Predict demand for a specific zone"""
        # Simulate demand prediction based on multiple factors
        base_demand = np.random.uniform(0.3, 0.8)
        
        # Time-based factors
        hour = target_datetime.hour
        day_of_week = target_datetime.weekday()
        
        # Hour multipliers
        hour_multipliers = {
            (7, 9): 1.5,    # Morning rush
            (11, 14): 1.8,  # Lunch time
            (17, 20): 1.6,  # Evening rush
            (20, 22): 1.2   # Dinner time
        }
        
        hour_multiplier = 1.0
        for (start_hour, end_hour), multiplier in hour_multipliers.items():
            if start_hour <= hour <= end_hour:
                hour_multiplier = multiplier
                break
        
        # Day of week multiplier
        if day_of_week < 5:  # Weekdays
            day_multiplier = 1.2
        elif day_of_week == 5:  # Friday
            day_multiplier = 1.4
        else:  # Weekend
            day_multiplier = 0.8
        
        # Zone-specific factors
        zone_type = zone.get("type", "residential")
        zone_multipliers = {
            "commercial": 1.5,
            "business_district": 1.8,
            "residential": 1.0,
            "industrial": 0.7
        }
        
        zone_multiplier = zone_multipliers.get(zone_type, 1.0)
        
        # Weather factor (simulated)
        weather_multiplier = np.random.uniform(0.8, 1.3)
        
        # Calculate final demand
        final_demand = base_demand * hour_multiplier * day_multiplier * zone_multiplier * weather_multiplier
        final_demand = min(1.0, final_demand)  # Cap at 1.0
        
        # Calculate confidence based on historical data availability
        confidence = np.random.uniform(0.7, 0.95)
        
        return {
            "demand_score": round(final_demand, 3),
            "confidence": round(confidence, 3),
            "peak_hours": self._get_zone_peak_hours(zone_type),
            "factors": {
                "hour_multiplier": hour_multiplier,
                "day_multiplier": day_multiplier,
                "zone_multiplier": zone_multiplier,
                "weather_impact": weather_multiplier
            }
        }
    
    def _initialize_city_zones(self) -> Dict:
        """Initialize zones for each city"""
        return {
            "São Roque": [
                {"id": "sr_center", "name": "Centro", "center": {"lat": -23.5320, "lng": -47.1360}, "radius": 2, "type": "commercial"},
                {"id": "sr_industrial", "name": "Zona Industrial", "center": {"lat": -23.5250, "lng": -47.1300}, "radius": 3, "type": "industrial"},
                {"id": "sr_residential", "name": "Zona Residencial", "center": {"lat": -23.5400, "lng": -47.1400}, "radius": 2.5, "type": "residential"}
            ],
            "Mairinque": [
                {"id": "mq_center", "name": "Centro", "center": {"lat": -23.5450, "lng": -47.1680}, "radius": 2, "type": "commercial"},
                {"id": "mq_residential", "name": "Bairros", "center": {"lat": -23.5500, "lng": -47.1750}, "radius": 3, "type": "residential"}
            ],
            "Araçariguama": [
                {"id": "ar_center", "name": "Centro", "center": {"lat": -23.4420, "lng": -47.0610}, "radius": 1.5, "type": "commercial"},
                {"id": "ar_residential", "name": "Residencial", "center": {"lat": -23.4400, "lng": -47.0580}, "radius": 2, "type": "residential"}
            ],
            "Alumínio": [
                {"id": "al_center", "name": "Centro", "center": {"lat": -23.5340, "lng": -47.2590}, "radius": 1.8, "type": "commercial"},
                {"id": "al_industrial", "name": "Industrial", "center": {"lat": -23.5300, "lng": -47.2550}, "radius": 2.5, "type": "industrial"}
            ],
            "Ibiúna": [
                {"id": "ib_center", "name": "Centro", "center": {"lat": -23.6560, "lng": -47.2230}, "radius": 2, "type": "commercial"},
                {"id": "ib_rural", "name": "Zona Rural", "center": {"lat": -23.6600, "lng": -47.2300}, "radius": 4, "type": "residential"}
            ]
        }
    
    def _get_zone_peak_hours(self, zone_type: str) -> List[str]:
        """Get peak hours for different zone types"""
        peak_hours = {
            "commercial": ["08:00-10:00", "12:00-14:00", "18:00-20:00"],
            "business_district": ["08:00-09:00", "12:00-13:00", "17:00-19:00"],
            "residential": ["11:00-13:00", "18:00-21:00"],
            "industrial": ["07:00-08:00", "12:00-13:00", "17:00-18:00"]
        }
        return peak_hours.get(zone_type, ["12:00-14:00"])
    
    def _calculate_city_demand(self, zones: List[Dict]) -> Dict:
        """Calculate overall city demand"""
        total_demand = sum(zone["predicted_demand"] for zone in zones)
        avg_demand = total_demand / len(zones) if zones else 0
        
        demand_level = "low"
        if avg_demand >= 0.7:
            demand_level = "high"
        elif avg_demand >= 0.4:
            demand_level = "medium"
        
        return {
            "level": demand_level,
            "score": round(avg_demand, 3),
            "total_zones": len(zones),
            "high_demand_zones": len([z for z in zones if z["predicted_demand"] >= 0.6])
        }
    
    def _generate_positioning_recommendations(self, zones: List[Dict]) -> List[str]:
        """Generate positioning recommendations for motoboys"""
        recommendations = []
        
        top_zone = zones[0] if zones else None
        if top_zone:
            recommendations.append(f"Posicione-se próximo a {top_zone['zone_name']} (demanda: {top_zone['predicted_demand']:.1%})")
        
        high_demand_zones = [z for z in zones if z["predicted_demand"] >= 0.6]
        if len(high_demand_zones) > 1:
            recommendations.append(f"Áreas de alta demanda: {', '.join(z['zone_name'] for z in high_demand_zones[:3])}")
        
        if zones:
            avg_confidence = sum(z["confidence"] for z in zones) / len(zones)
            if avg_confidence >= 0.8:
                recommendations.append("Predição confiável - boa oportunidade de ganhos")
            else:
                recommendations.append("Predição moderada - monitore mudanças na demanda")
        
        return recommendations


class ChatModerator:
    """Intelligent chat moderation system"""
    
    def __init__(self):
        self.profanity_list = self._load_profanity_list()
        self.positive_keywords = self._load_positive_keywords()
        self.warning_keywords = self._load_warning_keywords()
    
    def moderate_message(self, message: str, user_id: str, city: str) -> Dict:
        """Moderate a chat message and determine action"""
        moderation_result = {
            "message_id": f"msg_{datetime.now().timestamp()}",
            "user_id": user_id,
            "city": city,
            "original_message": message,
            "filtered_message": message,
            "action": "approved",
            "confidence": 1.0,
            "flags": [],
            "timestamp": datetime.now().isoformat()
        }
        
        # Check for profanity
        profanity_check = self._check_profanity(message)
        if profanity_check["found"]:
            moderation_result["filtered_message"] = profanity_check["filtered"]
            moderation_result["action"] = "filtered"
            moderation_result["flags"].append("profanity")
            moderation_result["confidence"] = profanity_check["confidence"]
        
        # Check for spam
        spam_check = self._check_spam(message, user_id)
        if spam_check["is_spam"]:
            moderation_result["action"] = "blocked"
            moderation_result["flags"].append("spam")
            moderation_result["confidence"] = min(moderation_result["confidence"], spam_check["confidence"])
        
        # Check for safety concerns
        safety_check = self._check_safety_concerns(message)
        if safety_check["has_concerns"]:
            moderation_result["action"] = "flagged_for_review"
            moderation_result["flags"].extend(safety_check["concerns"])
            moderation_result["confidence"] = min(moderation_result["confidence"], safety_check["confidence"])
        
        # Check for positive content
        positive_check = self._check_positive_content(message)
        if positive_check["is_positive"]:
            moderation_result["flags"].append("helpful")
            moderation_result["confidence"] = max(moderation_result["confidence"], positive_check["confidence"])
        
        return moderation_result
    
    def _check_profanity(self, message: str) -> Dict:
        """Check for profanity and offensive language"""
        message_lower = message.lower()
        found_words = []
        
        for word in self.profanity_list:
            if word in message_lower:
                found_words.append(word)
        
        if found_words:
            # Replace profanity with asterisks
            filtered_message = message
            for word in found_words:
                filtered_message = filtered_message.replace(word, "*" * len(word))
            
            return {
                "found": True,
                "filtered": filtered_message,
                "words": found_words,
                "confidence": 0.9
            }
        
        return {"found": False, "filtered": message, "words": [], "confidence": 1.0}
    
    def _check_spam(self, message: str, user_id: str) -> Dict:
        """Check for spam patterns"""
        # Check message length
        if len(message) > 500:
            return {"is_spam": True, "reason": "too_long", "confidence": 0.8}
        
        # Check for repeated characters
        repeated_chars = sum(1 for i in range(1, len(message)) if message[i] == message[i-1])
        if repeated_chars > len(message) * 0.5:
            return {"is_spam": True, "reason": "repeated_chars", "confidence": 0.7}
        
        # Check for excessive capitalization
        caps_ratio = sum(1 for c in message if c.isupper()) / len(message) if message else 0
        if caps_ratio > 0.7 and len(message) > 10:
            return {"is_spam": True, "reason": "excessive_caps", "confidence": 0.6}
        
        # Check for URLs (basic)
        if "http" in message.lower() or "www." in message.lower():
            return {"is_spam": True, "reason": "contains_url", "confidence": 0.9}
        
        return {"is_spam": False, "reason": None, "confidence": 1.0}
    
    def _check_safety_concerns(self, message: str) -> Dict:
        """Check for safety-related concerns"""
        message_lower = message.lower()
        concerns = []
        confidence = 1.0
        
        # Check for location sharing concerns
        location_keywords = ["endereço", "onde moro", "casa", "rua", "número"]
        if any(keyword in message_lower for keyword in location_keywords):
            concerns.append("location_sharing")
            confidence = 0.7
        
        # Check for emergency situations
        emergency_keywords = ["acidente", "roubo", "assalto", "emergência", "socorro", "polícia"]
        if any(keyword in message_lower for keyword in emergency_keywords):
            concerns.append("emergency")
            confidence = 0.9
        
        # Check for harassment
        harassment_keywords = ["idiota", "burro", "incompetente"]
        if any(keyword in message_lower for keyword in harassment_keywords):
            concerns.append("harassment")
            confidence = 0.8
        
        return {
            "has_concerns": len(concerns) > 0,
            "concerns": concerns,
            "confidence": confidence
        }
    
    def _check_positive_content(self, message: str) -> Dict:
        """Check for positive/helpful content"""
        message_lower = message.lower()
        positive_score = 0
        
        for keyword in self.positive_keywords:
            if keyword in message_lower:
                positive_score += 1
        
        is_positive = positive_score >= 2
        
        return {
            "is_positive": is_positive,
            "score": positive_score,
            "confidence": 0.8 if is_positive else 0.5
        }
    
    def _load_profanity_list(self) -> List[str]:
        """Load profanity word list"""
        return [
            "idiota", "burro", "imbecil", "estúpido", "otário", "babaca",
            "corno", "fdp", "merda", "porra", # Add more as needed
        ]
    
    def _load_positive_keywords(self) -> List[str]:
        """Load positive keyword list"""
        return [
            "obrigado", "valeu", "ajuda", "dica", "informação", "cuidado",
            "atenção", "trânsito", "blitz", "radar", "obras", "devagar",
            "segurança", "beleza", "tranquilo", "sucesso", "parabéns"
        ]
    
    def _load_warning_keywords(self) -> List[str]:
        """Load warning/safety keyword list"""
        return [
            "blitz", "radar", "obras", "acidente", "trânsito parado",
            "chuva forte", "alagamento", "buraco", "perigo"
        ]


# Integration Functions
def analyze_motoboy_security(motoboy_data: Dict) -> Dict:
    """Main function to analyze motoboy security"""
    analyzer = SecurityAnalyzer()
    verifier = IdentityVerifier()
    
    # Behavioral risk analysis
    risk_analysis = analyzer.analyze_behavioral_risk(motoboy_data)
    
    # Identity verification check
    needs_verification = verifier.requires_verification(motoboy_data)
    
    # Data consistency check
    consistency_check = verifier.verify_data_consistency(motoboy_data)
    
    return {
        "motoboy_id": motoboy_data.get("id"),
        "risk_analysis": risk_analysis,
        "needs_identity_verification": needs_verification,
        "data_consistency": consistency_check,
        "overall_security_score": (
            (100 - risk_analysis["risk_score"]) * 0.4 +
            consistency_check["consistency_score"] * 0.6
        ),
        "analysis_timestamp": datetime.now().isoformat()
    }

def optimize_delivery_routes(deliveries: List[Dict], motoboy_location: Dict) -> Dict:
    """Main function to optimize delivery routes"""
    optimizer = RouteOptimizer()
    return optimizer.optimize_multiple_deliveries(deliveries, motoboy_location)

def predict_demand_for_city(city: str, target_time: datetime = None) -> Dict:
    """Main function to predict demand and generate heatmap"""
    predictor = DemandPredictor()
    return predictor.generate_demand_heatmap(city, target_time)

def moderate_chat_message(message: str, user_id: str, city: str) -> Dict:
    """Main function to moderate chat messages"""
    moderator = ChatModerator()
    return moderator.moderate_message(message, user_id, city)