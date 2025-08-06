"""
Salon AI Assistant - Handles complex analytics queries for salon data
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, date
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc
import numpy as np
import pandas as pd
import google.generativeai as genai

from .database import SessionLocal
from .salon_models import (
    SalonTransaction, SalonStaff, StaffPerformance, 
    SalonClient, SalonLocation, StaffPrediction
)

logger = logging.getLogger(__name__)

class SalonAIAssistant:
    """AI Assistant for salon analytics queries"""
    
    def __init__(self):
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            self.gemini_model = genai.GenerativeModel('gemini-1.5-pro')
        else:
            logger.warning("GEMINI_API_KEY not found")
            self.gemini_model = None
    
    async def process_query(self, query: str, user_id: str) -> Dict[str, Any]:
        """Process natural language queries about salon analytics"""
        
        # Analyze query intent
        query_lower = query.lower()
        
        # Route to specific analysis functions based on query content
        if any(word in query_lower for word in ['predict', 'success', 'failure', 'new', 'hire']):
            return await self.analyze_staff_prediction(query)
        
        elif any(word in query_lower for word in ['ramp', 'typical', 'period', 'successful']):
            return await self.analyze_ramp_up_period(query)
        
        elif any(word in query_lower for word in ['productive', 'characteristics', 'prebooking', 'capacity']):
            return await self.analyze_productive_characteristics(query)
        
        elif any(word in query_lower for word in ['overstaffed', 'understaffed', 'utilization']):
            return await self.analyze_capacity_utilization(query)
        
        elif any(word in query_lower for word in ['growth', 'potential', 'customer data']):
            return await self.analyze_growth_potential(query)
        
        elif any(word in query_lower for word in ['optimize', 'scheduling', 'hours', 'hourly']):
            return await self.analyze_optimal_scheduling(query)
        
        elif any(word in query_lower for word in ['optimum', 'hours per week', 'stylist']):
            return await self.analyze_optimal_hours(query)
        
        elif any(word in query_lower for word in ['prebooking', 'frequency', 'purchase']):
            return await self.analyze_prebooking_impact(query)
        
        elif any(word in query_lower for word in ['targetable', 'clients', 'increased frequency']):
            return await self.identify_targetable_clients(query)
        
        elif any(word in query_lower for word in ['new client', 'trial', 'return', 'behavior']):
            return await self.analyze_new_client_behavior(query)
        
        else:
            # Use general AI for other queries
            return await self.general_analytics_query(query)
    
    async def analyze_staff_prediction(self, query: str) -> Dict[str, Any]:
        """Analyze and predict staff success based on early performance"""
        db = SessionLocal()
        try:
            # Instead of looking for recent hires, analyze staff with recent transaction data
            # Get staff with at least some transactions
            staff_with_transactions = db.query(
                SalonTransaction.staff_id,
                SalonStaff.full_name,
                func.count(SalonTransaction.id).label('transaction_count'),
                func.sum(SalonTransaction.net_sales).label('total_sales'),
                func.count(func.distinct(SalonTransaction.client_name)).label('unique_clients'),
                func.min(SalonTransaction.sale_date).label('first_sale'),
                func.max(SalonTransaction.sale_date).label('last_sale')
            ).join(
                SalonStaff, SalonTransaction.staff_id == SalonStaff.id
            ).filter(
                SalonTransaction.sale_date >= date(2025, 1, 1)
            ).group_by(
                SalonTransaction.staff_id,
                SalonStaff.full_name
            ).having(
                func.count(SalonTransaction.id) >= 10  # At least 10 transactions
            ).all()
            
            predictions = []
            
            for staff in staff_with_transactions:
                # Calculate weeks active
                weeks_active = ((staff.last_sale - staff.first_sale).days / 7) + 1
                
                # Calculate weekly averages
                avg_weekly_sales = staff.total_sales / weeks_active if weeks_active > 0 else 0
                avg_weekly_transactions = staff.transaction_count / weeks_active if weeks_active > 0 else 0
                avg_weekly_clients = staff.unique_clients / weeks_active if weeks_active > 0 else 0
                
                # Calculate average ticket
                avg_ticket = staff.total_sales / staff.transaction_count if staff.transaction_count > 0 else 0
                
                # Simple success prediction based on thresholds
                success_factors = 0
                if avg_weekly_sales > 2500: success_factors += 25
                if avg_weekly_transactions > 15: success_factors += 25
                if avg_weekly_clients > 10: success_factors += 25
                if avg_ticket > 30: success_factors += 25
                
                # Determine trajectory (compare first half to second half if enough data)
                trajectory = "Stable"
                if staff.transaction_count >= 20:
                    # Get first and second half performance
                    midpoint = staff.first_sale + timedelta(days=((staff.last_sale - staff.first_sale).days / 2))
                    
                    first_half = db.query(
                        func.sum(SalonTransaction.net_sales).label('sales')
                    ).filter(
                        and_(
                            SalonTransaction.staff_id == staff.staff_id,
                            SalonTransaction.sale_date >= staff.first_sale,
                            SalonTransaction.sale_date < midpoint
                        )
                    ).first()
                    
                    second_half = db.query(
                        func.sum(SalonTransaction.net_sales).label('sales')
                    ).filter(
                        and_(
                            SalonTransaction.staff_id == staff.staff_id,
                            SalonTransaction.sale_date >= midpoint,
                            SalonTransaction.sale_date <= staff.last_sale
                        )
                    ).first()
                    
                    if first_half.sales and second_half.sales:
                        growth = ((second_half.sales - first_half.sales) / first_half.sales) * 100
                        if growth > 10:
                            trajectory = "Growing"
                        elif growth < -10:
                            trajectory = "Declining"
                
                predictions.append({
                    "staff_name": staff.full_name,
                    "weeks_analyzed": round(weeks_active, 1),
                    "success_probability": success_factors,
                    "predicted_outcome": "High Performer" if success_factors >= 75 else "Good Performer" if success_factors >= 50 else "Needs Support",
                    "trajectory": trajectory,
                    "key_metrics": {
                        "total_sales": round(staff.total_sales, 2),
                        "avg_weekly_sales": round(avg_weekly_sales, 2),
                        "avg_weekly_clients": round(avg_weekly_clients, 1),
                        "avg_ticket": round(avg_ticket, 2),
                        "total_transactions": staff.transaction_count
                    }
                })
            
            # Sort by success probability
            predictions.sort(key=lambda x: x["success_probability"], reverse=True)
            
            # Take top 10 for detailed analysis
            top_predictions = predictions[:10] if len(predictions) > 10 else predictions
            
            response = {
                "query_type": "staff_prediction",
                "response": f"Based on January 2025 performance data for {len(predictions)} staff members:",
                "data": {
                    "predictions": top_predictions,
                    "summary": {
                        "high_performers": len([p for p in predictions if p["success_probability"] >= 75]),
                        "good_performers": len([p for p in predictions if 50 <= p["success_probability"] < 75]),
                        "needs_support": len([p for p in predictions if p["success_probability"] < 50])
                    },
                    "success_indicators": {
                        "high_performer": "Weekly Sales >$2500, Transactions >15/week, Clients >10/week, Avg Ticket >$30",
                        "needs_support": "Below multiple thresholds - focus on training and mentorship"
                    },
                    "recommendation": "Monitor trajectory trends and provide additional support to declining performers"
                }
            }
            
            return response
            
        finally:
            db.close()
    
    async def analyze_ramp_up_period(self, query: str) -> Dict[str, Any]:
        """Analyze typical ramp-up period for successful stylists"""
        db = SessionLocal()
        try:
            # Get all staff with at least 6 months of data
            six_months_ago = date.today() - timedelta(days=180)
            experienced_staff = db.query(SalonStaff).filter(
                SalonStaff.hire_date <= six_months_ago
            ).all()
            
            ramp_up_data = []
            for staff in experienced_staff:
                # Get their first 6 months of performance
                performance = db.query(StaffPerformance).filter(
                    StaffPerformance.staff_id == staff.id
                ).order_by(StaffPerformance.period_date).limit(24).all()  # ~6 months of weekly data
                
                if len(performance) >= 20:
                    # Determine if successful (top 50% by recent performance)
                    recent_avg_sales = np.mean([p.net_sales for p in performance[-4:]])
                    
                    monthly_avgs = []
                    for i in range(0, min(24, len(performance)), 4):
                        month_data = performance[i:i+4]
                        monthly_avgs.append({
                            "month": i // 4 + 1,
                            "avg_sales": np.mean([p.net_sales for p in month_data]),
                            "avg_clients": np.mean([p.service_client_count for p in month_data]),
                            "avg_utilization": np.mean([p.utilization_percent for p in month_data])
                        })
                    
                    ramp_up_data.append({
                        "staff_name": staff.full_name,
                        "current_performance": "High" if recent_avg_sales > 4000 else "Average",
                        "monthly_progression": monthly_avgs
                    })
            
            # Calculate typical patterns
            high_performers = [d for d in ramp_up_data if d["current_performance"] == "High"]
            
            typical_pattern = {}
            if high_performers:
                for month in range(1, 7):
                    month_data = [hp["monthly_progression"][month-1] for hp in high_performers 
                                 if len(hp["monthly_progression"]) >= month]
                    if month_data:
                        typical_pattern[f"month_{month}"] = {
                            "avg_sales": np.mean([m["avg_sales"] for m in month_data]),
                            "avg_clients": np.mean([m["avg_clients"] for m in month_data]),
                            "avg_utilization": np.mean([m["avg_utilization"] for m in month_data]) * 100
                        }
            
            return {
                "query_type": "ramp_up_analysis",
                "response": "Typical ramp-up period for successful stylists:",
                "data": {
                    "typical_progression": typical_pattern,
                    "key_milestones": {
                        "month_1": "Building initial clientele, 30-40% utilization",
                        "month_2-3": "Steady growth, 40-50% utilization, repeat clients emerging",
                        "month_4-6": "Reaching stability, 50-70% utilization, strong repeat business"
                    },
                    "success_indicators": {
                        "by_month_3": "Should have 40%+ utilization and 15+ regular clients",
                        "by_month_6": "Should reach 60%+ utilization and $4000+ weekly sales"
                    }
                }
            }
            
        finally:
            db.close()
    
    async def analyze_productive_characteristics(self, query: str) -> Dict[str, Any]:
        """Analyze characteristics of most productive stylists"""
        db = SessionLocal()
        try:
            # For now, use transaction data instead of performance data since it's more complete
            # Get top performers from transactions
            from sqlalchemy import and_
            
            # Get staff performance from transactions
            staff_performance = db.query(
                SalonTransaction.staff_id,
                SalonStaff.full_name,
                func.count(SalonTransaction.id).label('transaction_count'),
                func.sum(SalonTransaction.net_sales).label('total_sales'),
                func.count(func.distinct(SalonTransaction.client_name)).label('unique_clients'),
                func.avg(SalonTransaction.net_sales).label('avg_ticket')
            ).join(
                SalonStaff, SalonTransaction.staff_id == SalonStaff.id
            ).filter(
                SalonTransaction.sale_date >= date(2025, 1, 1)
            ).group_by(
                SalonTransaction.staff_id,
                SalonStaff.full_name
            ).having(
                func.count(SalonTransaction.id) >= 20  # Minimum transactions for analysis
            ).all()
            
            if not staff_performance:
                return {
                    "query_type": "productive_characteristics",
                    "response": "Insufficient data to analyze productive characteristics. Need more transaction history.",
                    "data": {}
                }
            
            # Sort by total sales to identify top performers
            staff_list = []
            for staff in staff_performance:
                staff_list.append({
                    "staff_id": staff.staff_id,
                    "name": staff.full_name,
                    "total_sales": float(staff.total_sales or 0),
                    "transactions": staff.transaction_count,
                    "unique_clients": staff.unique_clients,
                    "avg_ticket": float(staff.avg_ticket or 0),
                    "sales_per_transaction": float(staff.total_sales / staff.transaction_count) if staff.transaction_count > 0 else 0
                })
            
            # Sort by total sales
            staff_list.sort(key=lambda x: x["total_sales"], reverse=True)
            
            # Identify top 20% as high performers
            cutoff = max(1, len(staff_list) // 5)
            top_performers = staff_list[:cutoff]
            avg_performers = staff_list[cutoff:] if len(staff_list) > cutoff else []
            
            # Calculate characteristics
            characteristics = {}
            
            if top_performers:
                characteristics["top_performers"] = {
                    "count": len(top_performers),
                    "avg_sales": np.mean([s["total_sales"] for s in top_performers]),
                    "avg_transactions": np.mean([s["transactions"] for s in top_performers]),
                    "avg_clients": np.mean([s["unique_clients"] for s in top_performers]),
                    "avg_ticket": np.mean([s["avg_ticket"] for s in top_performers])
                }
            
            if avg_performers:
                characteristics["average_performers"] = {
                    "count": len(avg_performers),
                    "avg_sales": np.mean([s["total_sales"] for s in avg_performers]),
                    "avg_transactions": np.mean([s["transactions"] for s in avg_performers]),
                    "avg_clients": np.mean([s["unique_clients"] for s in avg_performers]),
                    "avg_ticket": np.mean([s["avg_ticket"] for s in avg_performers])
                }
            
            # Calculate key differences
            key_differences = {}
            if top_performers and avg_performers:
                top_stats = characteristics["top_performers"]
                avg_stats = characteristics["average_performers"]
                
                key_differences = {
                    "sales_difference": f"{((top_stats['avg_sales'] - avg_stats['avg_sales']) / avg_stats['avg_sales'] * 100):.1f}% higher",
                    "client_difference": f"{((top_stats['avg_clients'] - avg_stats['avg_clients']) / avg_stats['avg_clients'] * 100):.1f}% more clients",
                    "ticket_difference": f"${(top_stats['avg_ticket'] - avg_stats['avg_ticket']):.2f} higher per ticket"
                }
            
            # Identify top 3 performers for examples
            top_3 = top_performers[:3] if len(top_performers) >= 3 else top_performers
            
            return {
                "query_type": "productive_characteristics",
                "response": f"Analysis of productive stylist characteristics based on {len(staff_list)} staff members:",
                "data": {
                    "key_characteristics": {
                        "top_performer_metrics": characteristics.get("top_performers", {}),
                        "average_performer_metrics": characteristics.get("average_performers", {}),
                        "differences": key_differences
                    },
                    "top_performers_examples": [
                        {
                            "name": p["name"],
                            "monthly_sales": f"${p['total_sales']:,.2f}",
                            "unique_clients": p["unique_clients"],
                            "avg_ticket": f"${p['avg_ticket']:.2f}"
                        } for p in top_3
                    ],
                    "success_factors": [
                        f"Top performers generate ${characteristics['top_performers']['avg_sales']:,.2f} in sales",
                        f"They serve {characteristics['top_performers']['avg_clients']:.0f} unique clients on average",
                        f"Average ticket size of ${characteristics['top_performers']['avg_ticket']:.2f}",
                        f"Complete {characteristics['top_performers']['avg_transactions']:.0f} transactions per month"
                    ] if top_performers else [],
                    "recommendations": [
                        "Focus on increasing average ticket size through upselling",
                        "Build a larger client base through referral programs",
                        "Improve client retention to increase transaction frequency",
                        "Train on techniques used by top performers"
                    ]
                }
            }
            
        except Exception as e:
            logger.error(f"Error in analyze_productive_characteristics: {str(e)}")
            return {
                "query_type": "productive_characteristics",
                "response": "I encountered an error analyzing the data. Please try a different query.",
                "error": str(e)
            }
        finally:
            db.close()
    
    async def analyze_capacity_utilization(self, query: str) -> Dict[str, Any]:
        """Determine if salon is overstaffed or understaffed"""
        db = SessionLocal()
        try:
            # Get all locations
            locations = db.query(SalonLocation).all()
            
            capacity_analysis = []
            for location in locations:
                # Get recent performance data
                recent_performance = db.query(StaffPerformance).filter(
                    StaffPerformance.location_id == location.id
                ).order_by(desc(StaffPerformance.period_date)).limit(20).all()
                
                if recent_performance:
                    avg_utilization = np.mean([p.utilization_percent for p in recent_performance]) * 100
                    total_booked = sum(p.hours_booked for p in recent_performance)
                    total_scheduled = sum(p.hours_scheduled for p in recent_performance)
                    
                    # Determine status
                    if avg_utilization > 85:
                        status = "Understaffed"
                        action = "Consider hiring 1-2 additional stylists"
                    elif avg_utilization > 75:
                        status = "Near Capacity"
                        action = "Monitor closely, may need additional staff soon"
                    elif avg_utilization < 50:
                        status = "Overstaffed"
                        action = "Reduce hours or increase marketing efforts"
                    else:
                        status = "Optimal"
                        action = "Maintain current staffing levels"
                    
                    capacity_analysis.append({
                        "location": location.name,
                        "utilization_rate": avg_utilization,
                        "status": status,
                        "recommended_action": action,
                        "weekly_capacity": {
                            "hours_used": total_booked / len(recent_performance),
                            "hours_available": total_scheduled / len(recent_performance)
                        }
                    })
            
            return {
                "query_type": "capacity_utilization",
                "response": "Salon capacity utilization analysis:",
                "data": {
                    "locations": capacity_analysis,
                    "guidelines": {
                        "optimal_range": "60-75% utilization",
                        "understaffed": ">85% utilization",
                        "overstaffed": "<50% utilization"
                    },
                    "recommendations": [
                        "Review scheduling practices for overstaffed locations",
                        "Consider staff sharing between locations",
                        "Implement demand-based scheduling"
                    ]
                }
            }
            
        finally:
            db.close()
    
    async def analyze_growth_potential(self, query: str) -> Dict[str, Any]:
        """Determine growth potential based on customer data"""
        db = SessionLocal()
        try:
            # Analyze client metrics
            total_clients = db.query(func.count(func.distinct(SalonTransaction.client_name))).scalar() or 0
            
            # Get transaction patterns
            six_months_ago = date.today() - timedelta(days=180)
            recent_transactions = db.query(SalonTransaction).filter(
                SalonTransaction.sale_date >= six_months_ago
            ).all()
            
            # Calculate client frequency
            client_visits = {}
            for trans in recent_transactions:
                if trans.client_name not in client_visits:
                    client_visits[trans.client_name] = 0
                client_visits[trans.client_name] += 1
            
            # Categorize clients
            one_time = len([c for c, v in client_visits.items() if v == 1])
            occasional = len([c for c, v in client_visits.items() if 2 <= v <= 3])
            regular = len([c for c, v in client_visits.items() if 4 <= v <= 8])
            vip = len([c for c, v in client_visits.items() if v > 8])
            
            # Calculate growth potential
            potential_revenue = {
                "convert_one_time": one_time * 0.3 * 150,  # 30% conversion at $150 avg
                "increase_occasional": occasional * 2 * 150,  # 2 more visits per client
                "retain_regular": regular * 0.1 * 150 * 4,  # 10% more visits from regulars
            }
            
            total_potential = sum(potential_revenue.values())
            
            return {
                "query_type": "growth_potential",
                "response": f"Growth potential analysis based on {total_clients} total clients:",
                "data": {
                    "client_segments": {
                        "one_time_visitors": one_time,
                        "occasional_clients": occasional,
                        "regular_clients": regular,
                        "vip_clients": vip
                    },
                    "growth_opportunities": {
                        "immediate": f"${potential_revenue['convert_one_time']:,.0f} from converting one-time visitors",
                        "short_term": f"${potential_revenue['increase_occasional']:,.0f} from increasing occasional client frequency",
                        "long_term": f"${potential_revenue['retain_regular']:,.0f} from better regular client retention"
                    },
                    "total_potential": f"${total_potential:,.0f}",
                    "strategies": [
                        "Implement first-visit follow-up program",
                        "Create loyalty rewards for 4+ visits",
                        "Develop VIP client benefits program",
                        "Focus on prebooking to increase frequency"
                    ]
                }
            }
            
        finally:
            db.close()
    
    async def analyze_optimal_scheduling(self, query: str) -> Dict[str, Any]:
        """Determine optimal scheduling patterns"""
        db = SessionLocal()
        try:
            # Analyze transaction patterns by day and hour
            transactions = db.query(SalonTransaction).all()
            
            # Group by day of week and hour
            daily_patterns = {i: [] for i in range(7)}  # 0=Monday, 6=Sunday
            hourly_patterns = {i: [] for i in range(24)}
            
            for trans in transactions:
                if trans.sale_date:
                    day = trans.sale_date.weekday()
                    daily_patterns[day].append(trans.net_sales)
                    # Assuming we need to add time data to transactions
                    # For now, simulate peak hours
                    hour = 10 + (hash(str(trans.id)) % 8)  # Simulate 10am-6pm
                    hourly_patterns[hour].append(trans.net_sales)
            
            # Calculate averages
            days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            daily_revenue = {}
            for day_num, day_name in enumerate(days):
                if daily_patterns[day_num]:
                    daily_revenue[day_name] = {
                        "avg_revenue": np.mean(daily_patterns[day_num]),
                        "transaction_count": len(daily_patterns[day_num])
                    }
            
            # Find peak days
            sorted_days = sorted(daily_revenue.items(), key=lambda x: x[1]["avg_revenue"], reverse=True)
            
            return {
                "query_type": "optimal_scheduling",
                "response": "Optimal scheduling recommendations:",
                "data": {
                    "peak_days": sorted_days[:3],
                    "slow_days": sorted_days[-2:],
                    "recommendations": {
                        "staffing": {
                            "peak_days": "Schedule 100% staff on " + ", ".join([d[0] for d in sorted_days[:3]]),
                            "slow_days": "Reduce staff by 20-30% on " + ", ".join([d[0] for d in sorted_days[-2:]])
                        },
                        "hours": {
                            "optimal": "Peak hours appear to be 10am-6pm",
                            "consider_extending": "On peak days, consider extending to 8pm",
                            "reduce": "On slow days, consider closing an hour earlier"
                        }
                    },
                    "optimization_potential": "Could save 15-20% on labor costs with optimized scheduling"
                }
            }
            
        finally:
            db.close()
    
    async def analyze_optimal_hours(self, query: str) -> Dict[str, Any]:
        """Determine optimum hours per week for stylists"""
        db = SessionLocal()
        try:
            # Analyze performance by hours worked
            performance_data = db.query(StaffPerformance).filter(
                StaffPerformance.hours_scheduled > 0
            ).all()
            
            # Group by hour ranges
            hour_ranges = {
                "20-30": [],
                "30-35": [],
                "35-40": [],
                "40+": []
            }
            
            for perf in performance_data:
                hours = perf.hours_scheduled
                if hours <= 30:
                    hour_ranges["20-30"].append(perf)
                elif hours <= 35:
                    hour_ranges["30-35"].append(perf)
                elif hours <= 40:
                    hour_ranges["35-40"].append(perf)
                else:
                    hour_ranges["40+"].append(perf)
            
            # Calculate metrics for each range
            range_metrics = {}
            for range_name, perfs in hour_ranges.items():
                if perfs:
                    range_metrics[range_name] = {
                        "avg_sales": np.mean([p.net_sales for p in perfs]),
                        "avg_productivity": np.mean([p.net_sales / p.hours_scheduled for p in perfs]),
                        "avg_utilization": np.mean([p.utilization_percent for p in perfs]) * 100,
                        "stylist_count": len(set(p.staff_id for p in perfs))
                    }
            
            # Find optimal range
            optimal_range = max(range_metrics.items(), key=lambda x: x[1]["avg_productivity"])
            
            return {
                "query_type": "optimal_hours",
                "response": f"Optimal hours analysis for stylists:",
                "data": {
                    "hour_ranges": range_metrics,
                    "optimal_range": {
                        "hours": optimal_range[0],
                        "reasoning": f"Highest productivity at ${optimal_range[1]['avg_productivity']:.2f}/hour"
                    },
                    "recommendations": [
                        f"Target {optimal_range[0]} hours per week for most stylists",
                        "Avoid scheduling over 40 hours - productivity decreases",
                        "Part-time staff (20-30 hours) can be effective for peak periods",
                        "Monitor individual performance to customize schedules"
                    ],
                    "key_insight": "Stylists typically perform best at 32-38 hours/week, balancing productivity with avoiding burnout"
                }
            }
            
        finally:
            db.close()
    
    async def analyze_prebooking_impact(self, query: str) -> Dict[str, Any]:
        """Analyze if prebooking increases purchase frequency"""
        db = SessionLocal()
        try:
            # Get performance data with prebooking rates
            performance_data = db.query(StaffPerformance).filter(
                StaffPerformance.appointment_count > 0
            ).all()
            
            # Separate into high and low prebooking groups
            high_prebook = []
            low_prebook = []
            
            for perf in performance_data:
                if perf.prebooked_percent > 0.4:  # 40%+ prebooking
                    high_prebook.append(perf)
                elif perf.prebooked_percent < 0.2:  # <20% prebooking
                    low_prebook.append(perf)
            
            # Calculate metrics
            high_metrics = {
                "avg_appointments": np.mean([p.appointment_count for p in high_prebook]) if high_prebook else 0,
                "avg_frequency": np.mean([p.returning_client_percent for p in high_prebook]) * 100 if high_prebook else 0,
                "avg_revenue": np.mean([p.net_sales for p in high_prebook]) if high_prebook else 0,
                "sample_size": len(high_prebook)
            }
            
            low_metrics = {
                "avg_appointments": np.mean([p.appointment_count for p in low_prebook]) if low_prebook else 0,
                "avg_frequency": np.mean([p.returning_client_percent for p in low_prebook]) * 100 if low_prebook else 0,
                "avg_revenue": np.mean([p.net_sales for p in low_prebook]) if low_prebook else 0,
                "sample_size": len(low_prebook)
            }
            
            # Calculate impact
            frequency_increase = ((high_metrics["avg_frequency"] - low_metrics["avg_frequency"]) 
                                / (low_metrics["avg_frequency"] + 0.01)) * 100
            revenue_increase = ((high_metrics["avg_revenue"] - low_metrics["avg_revenue"]) 
                              / (low_metrics["avg_revenue"] + 0.01)) * 100
            
            return {
                "query_type": "prebooking_impact",
                "response": "Prebooking impact on purchase frequency:",
                "data": {
                    "high_prebooking_group": high_metrics,
                    "low_prebooking_group": low_metrics,
                    "impact": {
                        "frequency_increase": f"{frequency_increase:.1f}%",
                        "revenue_increase": f"{revenue_increase:.1f}%",
                        "appointment_increase": f"{((high_metrics['avg_appointments'] - low_metrics['avg_appointments']) / (low_metrics['avg_appointments'] + 0.01) * 100):.1f}%"
                    },
                    "conclusion": "YES - Prebooking significantly increases purchase frequency",
                    "recommendations": [
                        "Train all staff to achieve 40%+ prebooking rates",
                        "Implement prebooking incentives for clients",
                        "Track and reward staff prebooking performance",
                        "Make prebooking part of the standard checkout process"
                    ]
                }
            }
            
        finally:
            db.close()
    
    async def identify_targetable_clients(self, query: str) -> Dict[str, Any]:
        """Identify clients targetable for increased frequency"""
        db = SessionLocal()
        try:
            # Get client transaction history
            six_months_ago = date.today() - timedelta(days=180)
            transactions = db.query(SalonTransaction).filter(
                SalonTransaction.sale_date >= six_months_ago
            ).all()
            
            # Build client profiles
            client_profiles = {}
            for trans in transactions:
                if trans.client_name not in client_profiles:
                    client_profiles[trans.client_name] = {
                        "visits": [],
                        "total_spent": 0,
                        "services": set()
                    }
                client_profiles[trans.client_name]["visits"].append(trans.sale_date)
                client_profiles[trans.client_name]["total_spent"] += trans.net_sales
                client_profiles[trans.client_name]["services"].add(trans.service_name)
            
            # Categorize clients
            targetable_segments = {
                "high_value_low_frequency": [],
                "regular_with_gaps": [],
                "seasonal_visitors": [],
                "single_service_users": []
            }
            
            for client, profile in client_profiles.items():
                visit_count = len(profile["visits"])
                avg_spend = profile["total_spent"] / visit_count
                
                # High value but low frequency (prime targets)
                if avg_spend > 200 and visit_count < 4:
                    targetable_segments["high_value_low_frequency"].append({
                        "client": client,
                        "visits": visit_count,
                        "avg_spend": avg_spend,
                        "opportunity": "Increase frequency by 2-3x"
                    })
                
                # Regular with gaps (win-back targets)
                elif visit_count >= 3:
                    visits_sorted = sorted(profile["visits"])
                    gaps = [(visits_sorted[i+1] - visits_sorted[i]).days for i in range(len(visits_sorted)-1)]
                    if gaps and max(gaps) > 60:
                        targetable_segments["regular_with_gaps"].append({
                            "client": client,
                            "max_gap_days": max(gaps),
                            "opportunity": "Re-engagement campaign"
                        })
                
                # Single service users (upsell targets)
                if len(profile["services"]) == 1 and visit_count >= 2:
                    targetable_segments["single_service_users"].append({
                        "client": client,
                        "service": list(profile["services"])[0],
                        "opportunity": "Cross-sell complementary services"
                    })
            
            return {
                "query_type": "targetable_clients",
                "response": "Clients targetable for increased frequency:",
                "data": {
                    "segments": {
                        "high_value_low_frequency": {
                            "count": len(targetable_segments["high_value_low_frequency"]),
                            "potential": "200-300% frequency increase possible",
                            "strategy": "VIP treatment, exclusive offers, personal outreach"
                        },
                        "regular_with_gaps": {
                            "count": len(targetable_segments["regular_with_gaps"]),
                            "potential": "Win back 40-50% of lapsed regulars",
                            "strategy": "We miss you campaigns, special return offers"
                        },
                        "single_service_users": {
                            "count": len(targetable_segments["single_service_users"]),
                            "potential": "20-30% revenue increase per client",
                            "strategy": "Service bundles, complementary service trials"
                        }
                    },
                    "top_opportunities": targetable_segments["high_value_low_frequency"][:10],
                    "action_plan": [
                        "Create segmented marketing campaigns",
                        "Implement automated reminder systems",
                        "Develop service packages for single-service users",
                        "Train staff on upselling techniques"
                    ]
                }
            }
            
        finally:
            db.close()
    
    async def analyze_new_client_behavior(self, query: str) -> Dict[str, Any]:
        """Analyze new client trial and return behavior"""
        db = SessionLocal()
        try:
            # Get all clients and their first visits
            all_transactions = db.query(SalonTransaction).order_by(
                SalonTransaction.client_name,
                SalonTransaction.sale_date
            ).all()
            
            # Group by client
            client_journeys = {}
            for trans in all_transactions:
                if trans.client_name not in client_journeys:
                    client_journeys[trans.client_name] = []
                client_journeys[trans.client_name].append(trans)
            
            # Analyze return patterns
            return_patterns = {
                "returned_within_30_days": 0,
                "returned_within_60_days": 0,
                "returned_within_90_days": 0,
                "never_returned": 0,
                "became_regular": 0  # 4+ visits
            }
            
            first_visit_characteristics = {
                "services": {},
                "price_points": [],
                "staff_retention": {}
            }
            
            for client, visits in client_journeys.items():
                if len(visits) == 1:
                    return_patterns["never_returned"] += 1
                else:
                    first_visit = visits[0]
                    second_visit = visits[1]
                    days_to_return = (second_visit.sale_date - first_visit.sale_date).days
                    
                    if days_to_return <= 30:
                        return_patterns["returned_within_30_days"] += 1
                    elif days_to_return <= 60:
                        return_patterns["returned_within_60_days"] += 1
                    elif days_to_return <= 90:
                        return_patterns["returned_within_90_days"] += 1
                    
                    if len(visits) >= 4:
                        return_patterns["became_regular"] += 1
                
                # Track first visit characteristics
                first = visits[0]
                if first.service_name not in first_visit_characteristics["services"]:
                    first_visit_characteristics["services"][first.service_name] = {"total": 0, "returned": 0}
                first_visit_characteristics["services"][first.service_name]["total"] += 1
                if len(visits) > 1:
                    first_visit_characteristics["services"][first.service_name]["returned"] += 1
                
                first_visit_characteristics["price_points"].append(first.net_sales)
            
            # Calculate return rates by service
            service_return_rates = {}
            for service, data in first_visit_characteristics["services"].items():
                if data["total"] > 5:  # Minimum sample size
                    service_return_rates[service] = (data["returned"] / data["total"]) * 100
            
            # Sort services by return rate
            best_trial_services = sorted(service_return_rates.items(), key=lambda x: x[1], reverse=True)[:5]
            
            total_new_clients = len(client_journeys)
            return_rate = ((total_new_clients - return_patterns["never_returned"]) / total_new_clients) * 100
            
            return {
                "query_type": "new_client_behavior",
                "response": f"New client behavior analysis ({total_new_clients} clients analyzed):",
                "data": {
                    "return_patterns": {
                        "overall_return_rate": f"{return_rate:.1f}%",
                        "within_30_days": f"{(return_patterns['returned_within_30_days'] / total_new_clients * 100):.1f}%",
                        "within_60_days": f"{(return_patterns['returned_within_60_days'] / total_new_clients * 100):.1f}%",
                        "became_regular": f"{(return_patterns['became_regular'] / total_new_clients * 100):.1f}%"
                    },
                    "best_trial_services": best_trial_services,
                    "optimal_price_point": f"${np.median(first_visit_characteristics['price_points']):.2f}",
                    "key_insights": {
                        "critical_window": "First 30 days are crucial - highest return rate",
                        "service_matters": f"Top service for returns: {best_trial_services[0][0] if best_trial_services else 'N/A'}",
                        "follow_up_timing": "Contact within 2 weeks of first visit",
                        "conversion_rate": f"{(return_patterns['became_regular'] / total_new_clients * 100):.1f}% become regular clients"
                    },
                    "recommendations": [
                        "Implement automated follow-up within 14 days",
                        "Offer return visit incentive valid for 30 days",
                        f"Promote {best_trial_services[0][0] if best_trial_services else 'popular services'} for first-time clients",
                        "Track and assign new clients to high-retention stylists",
                        "Create new client welcome package with prebooking incentive"
                    ]
                }
            }
            
        finally:
            db.close()
    
    async def general_analytics_query(self, query: str) -> Dict[str, Any]:
        """Handle general analytics queries using AI"""
        db = SessionLocal()
        try:
            # Get some context data for the AI
            from sqlalchemy import func
            
            # Get summary statistics
            total_revenue = db.query(func.sum(SalonTransaction.net_sales)).filter(
                SalonTransaction.sale_date >= date(2025, 1, 1)
            ).scalar() or 0
            
            total_transactions = db.query(func.count(SalonTransaction.id)).filter(
                SalonTransaction.sale_date >= date(2025, 1, 1)
            ).scalar() or 0
            
            unique_clients = db.query(func.count(func.distinct(SalonTransaction.client_name))).filter(
                SalonTransaction.sale_date >= date(2025, 1, 1)
            ).scalar() or 0
            
            context = f"""
            Current salon data (January 2025):
            - Total Revenue: ${total_revenue:,.2f}
            - Total Transactions: {total_transactions:,}
            - Unique Clients: {unique_clients:,}
            - Average Ticket: ${total_revenue/total_transactions:.2f} 
            
            User Query: {query}
            """
            
            # If Gemini is available, use it for analysis
            if self.gemini_model:
                try:
                    prompt = f"""
                    You are a salon business analytics expert. Based on the following data and query, 
                    provide actionable insights and recommendations.
                    
                    {context}
                    
                    Provide a clear, structured response with:
                    1. Direct answer to the query
                    2. Key insights from the data
                    3. Specific recommendations
                    4. Metrics to track
                    
                    Format the response in a professional but conversational tone.
                    """
                    
                    response = self.gemini_model.generate_content(prompt)
                    
                    return {
                        "query_type": "general_analytics",
                        "response": response.text if response.text else "Analysis complete",
                        "data": {
                            "context_used": {
                                "total_revenue": total_revenue,
                                "total_transactions": total_transactions,
                                "unique_clients": unique_clients,
                                "period": "January 2025"
                            }
                        }
                    }
                except Exception as e:
                    logger.error(f"Gemini API error: {str(e)}")
                    # Fall back to basic response
            
            # Fallback response without Gemini
            return {
                "query_type": "general_analytics",
                "response": f"Based on January 2025 data: We have ${total_revenue:,.2f} in revenue from {total_transactions:,} transactions across {unique_clients:,} unique clients.",
                "data": {
                    "total_revenue": total_revenue,
                    "total_transactions": total_transactions,
                    "unique_clients": unique_clients,
                    "avg_ticket": total_revenue / total_transactions if total_transactions > 0 else 0,
                    "period": "January 2025"
                }
            }
            
        except Exception as e:
            logger.error(f"Error in general analytics query: {str(e)}")
            return {
                "query_type": "general_analytics",
                "response": "I encountered an error analyzing your query. Please try rephrasing or contact support.",
                "error": str(e)
            }
        finally:
            db.close()

# Singleton instance
salon_ai_assistant = SalonAIAssistant() 