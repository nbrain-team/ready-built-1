import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc
import io
import csv
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import joblib
import os
import google.generativeai as genai
import logging

from .database import SessionLocal
from .salon_models import (
    SalonLocation, SalonStaff, StaffPerformance, SalonClient,
    SalonAppointment, StaffPrediction, SalonAnalytics, SalonTransaction, SalonTimeClockEntry, SalonScheduleRecord
)

logger = logging.getLogger(__name__)

class SalonAnalyticsHandler:
    def __init__(self):
        # Configure Gemini
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            self.gemini_model = genai.GenerativeModel('gemini-1.5-pro')
        else:
            logger.warning("GEMINI_API_KEY not found. AI features will be limited.")
            self.gemini_model = None
            
        self.model_path = "models/staff_success_predictor.pkl"
        self.scaler_path = "models/staff_scaler.pkl"
        
    def ingest_staff_data(self, file_content: str) -> Dict[str, Any]:
        """Ingest employee list CSV data"""
        db = SessionLocal()
        try:
            df = pd.read_csv(io.StringIO(file_content))
            
            locations_created = 0
            staff_created = 0
            staff_updated = 0
            
            for _, row in df.iterrows():
                # Extract location from department
                dept = row.get('HOME DEPARTMENT', '')
                location_name = dept.split(' - ')[-1] if ' - ' in dept else dept
                
                # Get or create location
                location = db.query(SalonLocation).filter_by(name=location_name).first()
                if not location and location_name:
                    location = SalonLocation(
                        name=location_name,
                        code=dept.split(' - ')[0] if ' - ' in dept else None
                    )
                    db.add(location)
                    db.flush()
                    locations_created += 1
                
                # Create full name for matching
                first_name = row.get('PREFERRED FIRST NAME') or row.get('PAYROLL FIRST NAME', '')
                last_name = row.get('PAYROLL LAST NAME', '')
                full_name = f"{first_name} {last_name}".strip()
                
                # Check if staff exists
                staff = db.query(SalonStaff).filter_by(full_name=full_name).first()
                
                if staff:
                    # Update existing staff
                    staff.position_status = row.get('POSITION STATUS', 'A')
                    staff.termination_date = pd.to_datetime(row.get('TERMINATION DATE'), errors='coerce')
                    staff_updated += 1
                else:
                    # Create new staff
                    staff = SalonStaff(
                        payroll_last_name=last_name,
                        payroll_first_name=row.get('PAYROLL FIRST NAME', ''),
                        preferred_first_name=row.get('PREFERRED FIRST NAME', ''),
                        full_name=full_name,
                        job_title=row.get('JOB TITLE', ''),
                        location_id=location.id if location else None,
                        department=row.get('HOME DEPARTMENT', ''),
                        position_status=row.get('POSITION STATUS', 'A'),
                        hire_date=pd.to_datetime(row.get('HIRE DATE'), errors='coerce'),
                        rehire_date=pd.to_datetime(row.get('REHIRE DATE'), errors='coerce'),
                        termination_date=pd.to_datetime(row.get('TERMINATION DATE'), errors='coerce')
                    )
                    db.add(staff)
                    staff_created += 1
            
            db.commit()
            
            return {
                "success": True,
                "locations_created": locations_created,
                "staff_created": staff_created,
                "staff_updated": staff_updated
            }
            
        except Exception as e:
            db.rollback()
            return {"success": False, "error": str(e)}
        finally:
            db.close()
    
    def ingest_performance_data(self, file_content: str) -> Dict[str, Any]:
        """Ingest staff performance CSV data"""
        db = SessionLocal()
        try:
            df = pd.read_csv(io.StringIO(file_content))
            
            # Extract year from filename or use current year
            year = datetime.now().year
            month = datetime.now().month
            period_date = date(year, month, 1)
            
            records_created = 0
            records_updated = 0
            
            for _, row in df.iterrows():
                location_name = row.get('Location name', '')
                staff_name = row.get('Staff Name', '')
                
                # Skip summary rows
                if location_name == 'All' or staff_name == 'All' or pd.isna(staff_name) or staff_name == '':
                    continue
                
                # Get location
                location = db.query(SalonLocation).filter_by(name=location_name).first()
                if not location:
                    location = SalonLocation(name=location_name)
                    db.add(location)
                    db.flush()
                
                # Get or create staff
                staff = db.query(SalonStaff).filter_by(full_name=staff_name).first()
                if not staff:
                    staff = SalonStaff(
                        full_name=staff_name,
                        location_id=location.id
                    )
                    db.add(staff)
                    db.flush()
                
                # Check if performance record exists
                perf = db.query(StaffPerformance).filter_by(
                    staff_id=staff.id,
                    period_date=period_date
                ).first()
                
                if perf:
                    records_updated += 1
                else:
                    perf = StaffPerformance(
                        staff_id=staff.id,
                        location_id=location.id,
                        period_date=period_date
                    )
                    records_created += 1
                
                # Update performance data
                perf.hours_booked = float(row.get('Hours Booked', 0) or 0)
                perf.hours_scheduled = float(row.get('Hours Scheduled', 0) or 0)
                perf.utilization_percent = float(row.get('Utilization %', 0) or 0)
                perf.prebooked_percent = float(row.get('Prebooked %', 0) or 0)
                perf.self_booked_percent = float(row.get('Self-booked %', 0) or 0)
                perf.appointment_count = int(row.get('Appointment Count', 0) or 0)
                perf.service_count = int(row.get('Service Count', 0) or 0)
                perf.service_sales = float(row.get('Service Sales', 0) or 0)
                perf.service_sales_per_appointment = float(row.get('Service Sales per Appointment', 0) or 0)
                perf.tip_sales = float(row.get('Tip Sales', 0) or 0)
                perf.new_client_count = int(row.get('New Client Count', 0) or 0)
                perf.returning_client_count = int(row.get('Returning Client Count', 0) or 0)
                perf.gross_sales = float(row.get('Gross Sales', 0) or 0)
                perf.net_sales = float(row.get('Net Sales', 0) or 0)
                
                if not perf.id:
                    db.add(perf)
            
            db.commit()
            
            return {
                "success": True,
                "records_created": records_created,
                "records_updated": records_updated
            }
            
        except Exception as e:
            db.rollback()
            return {"success": False, "error": str(e)}
        finally:
            db.close()
    
    def ingest_transaction_data(self, file_content: str) -> Dict[str, Any]:
        """Ingest detailed line item transaction data"""
        db = SessionLocal()
        try:
            df = pd.read_csv(io.StringIO(file_content))
            
            # Skip summary rows
            df = df[df['Sale id'] != 'All']
            
            records_created = 0
            records_skipped = 0
            
            for _, row in df.iterrows():
                sale_id = row.get('Sale id')
                if pd.isna(sale_id):
                    continue
                
                # Check if transaction exists
                existing = db.query(SalonTransaction).filter_by(sale_id=sale_id).first()
                if existing:
                    records_skipped += 1
                    continue
                
                # Get location
                location_name = row.get('Location Name', '')
                location = db.query(SalonLocation).filter_by(name=location_name).first()
                if not location and location_name:
                    location = SalonLocation(name=location_name)
                    db.add(location)
                    db.flush()
                
                # Get staff by name
                staff_name = row.get('Staff Name', '')
                staff = None
                if staff_name and not pd.isna(staff_name):
                    staff = db.query(SalonStaff).filter_by(full_name=staff_name).first()
                
                # Create transaction
                transaction = SalonTransaction(
                    sale_id=sale_id,
                    location_id=location.id if location else None,
                    sale_date=pd.to_datetime(row.get('Sale Date'), errors='coerce'),
                    client_name=row.get('Client Name'),
                    staff_id=staff.id if staff else None,
                    service_name=row.get('Service Name'),
                    sale_type=row.get('Sale Type'),
                    net_service_sales=float(row.get('Net Service Sales', 0) or 0),
                    net_sales=float(row.get('Net Sales', 0) or 0)
                )
                db.add(transaction)
                records_created += 1
            
            db.commit()
            
            return {
                "success": True,
                "records_created": records_created,
                "records_skipped": records_skipped
            }
            
        except Exception as e:
            db.rollback()
            return {"success": False, "error": str(e)}
        finally:
            db.close()
    
    def ingest_time_clock_data(self, file_content: str) -> Dict[str, Any]:
        """Ingest time clock data"""
        db = SessionLocal()
        try:
            df = pd.read_csv(io.StringIO(file_content))
            
            # Skip summary rows
            df = df[df['Timecard id'] != 'All']
            
            records_created = 0
            records_skipped = 0
            
            for _, row in df.iterrows():
                timecard_id = row.get('Timecard id')
                if pd.isna(timecard_id):
                    continue
                
                # Check if entry exists
                existing = db.query(SalonTimeClockEntry).filter_by(timecard_id=timecard_id).first()
                if existing:
                    records_skipped += 1
                    continue
                
                # Get staff by name
                staff_name = row.get('Staff Name', '')
                staff = db.query(SalonStaff).filter_by(full_name=staff_name).first()
                if not staff and staff_name:
                    # Create staff if not exists
                    staff = SalonStaff(full_name=staff_name)
                    db.add(staff)
                    db.flush()
                
                # Get location
                location_name = row.get('Location Name', '')
                location = db.query(SalonLocation).filter_by(name=location_name).first()
                if not location and location_name:
                    location = SalonLocation(name=location_name)
                    db.add(location)
                    db.flush()
                
                # Parse dates
                clock_date = pd.to_datetime(row.get('Date '), errors='coerce')
                clock_in = pd.to_datetime(row.get('In At'), errors='coerce')
                clock_out = pd.to_datetime(row.get('Out At'), errors='coerce')
                
                # Create time clock entry
                entry = SalonTimeClockEntry(
                    timecard_id=timecard_id,
                    staff_id=staff.id if staff else None,
                    location_id=location.id if location else None,
                    clock_date=clock_date,
                    clock_in=clock_in,
                    clock_out=clock_out,
                    reason=row.get('Reason '),
                    hours_clocked=float(row.get('Hours Clocked', 0) or 0),
                    minutes_clocked=float(row.get('Minutes Clocked', 0) or 0),
                    staff_role=row.get('Staff Role Name')
                )
                db.add(entry)
                records_created += 1
            
            db.commit()
            
            return {
                "success": True,
                "records_created": records_created,
                "records_skipped": records_skipped
            }
            
        except Exception as e:
            db.rollback()
            return {"success": False, "error": str(e)}
        finally:
            db.close()
    
    def ingest_schedule_data(self, file_content: str) -> Dict[str, Any]:
        """Ingest schedule records data"""
        db = SessionLocal()
        try:
            df = pd.read_csv(io.StringIO(file_content))
            
            records_created = 0
            records_skipped = 0
            
            for _, row in df.iterrows():
                schedule_id = row.get('ScheduleRecord id')
                if pd.isna(schedule_id):
                    continue
                
                # Check if schedule exists
                existing = db.query(SalonScheduleRecord).filter_by(schedule_record_id=schedule_id).first()
                if existing:
                    records_skipped += 1
                    continue
                
                # Get staff and location by ID (these are UUIDs in the data)
                staff_id_str = row.get('Staff Id')
                location_id_str = row.get('Location Id')
                
                # For now, we'll skip matching by UUID and create placeholder records
                # In a real scenario, you'd need to map these UUIDs to your staff/location records
                
                # Parse date and times
                schedule_date = pd.to_datetime(row.get('Start On'), errors='coerce')
                start_time = pd.to_datetime(f"{row.get('Start On')} {row.get('Start At')}", errors='coerce')
                end_time = pd.to_datetime(f"{row.get('Start On')} {row.get('End At')}", errors='coerce')
                
                # Create schedule record
                schedule = SalonScheduleRecord(
                    schedule_record_id=schedule_id,
                    schedule_date=schedule_date,
                    start_time=start_time,
                    end_time=end_time
                )
                db.add(schedule)
                records_created += 1
            
            db.commit()
            
            return {
                "success": True,
                "records_created": records_created,
                "records_skipped": records_skipped,
                "note": "Staff/Location mapping by UUID not implemented yet"
            }
            
        except Exception as e:
            db.rollback()
            return {"success": False, "error": str(e)}
        finally:
            db.close()
    
    def predict_staff_success(self, staff_id: int, weeks: int = 6) -> Dict[str, Any]:
        """Predict staff success based on first N weeks of performance"""
        db = SessionLocal()
        try:
            staff = db.query(SalonStaff).filter_by(id=staff_id).first()
            if not staff:
                return {"success": False, "error": "Staff not found"}
            
            # Get performance data for first N weeks
            start_date = staff.hire_date
            end_date = start_date + timedelta(weeks=weeks)
            
            performance_data = db.query(StaffPerformance).filter(
                and_(
                    StaffPerformance.staff_id == staff_id,
                    StaffPerformance.period_date >= start_date,
                    StaffPerformance.period_date <= end_date
                )
            ).all()
            
            if not performance_data:
                return {"success": False, "error": "No performance data available"}
            
            # Calculate features for prediction
            features = self._calculate_prediction_features(performance_data)
            
            # Make prediction
            prediction, probability, factors = self._predict_success(features)
            
            # Store prediction
            pred_record = StaffPrediction(
                staff_id=staff_id,
                prediction_date=date.today(),
                weeks_since_hire=weeks,
                predicted_success=prediction,
                success_probability=probability,
                key_factors=factors
            )
            db.add(pred_record)
            db.commit()
            
            return {
                "success": True,
                "predicted_success": prediction,
                "success_probability": probability,
                "key_factors": factors,
                "recommendation": self._generate_recommendation(prediction, factors)
            }
            
        except Exception as e:
            db.rollback()
            return {"success": False, "error": str(e)}
        finally:
            db.close()
    
    def analyze_capacity_utilization(self, location_id: Optional[int] = None) -> Dict[str, Any]:
        """Analyze salon capacity utilization"""
        db = SessionLocal()
        try:
            query = db.query(StaffPerformance)
            if location_id:
                query = query.filter(StaffPerformance.location_id == location_id)
            
            # Get latest month's data
            latest_date = query.order_by(desc(StaffPerformance.period_date)).first().period_date
            current_data = query.filter(StaffPerformance.period_date == latest_date).all()
            
            total_booked = sum(p.hours_booked for p in current_data)
            total_scheduled = sum(p.hours_scheduled for p in current_data)
            overall_utilization = (total_booked / total_scheduled * 100) if total_scheduled > 0 else 0
            
            # Determine staffing status
            if overall_utilization > 85:
                status = "understaffed"
                recommendation = "Consider hiring additional stylists to meet demand"
            elif overall_utilization < 60:
                status = "overstaffed"
                recommendation = "Optimize scheduling or increase marketing to boost bookings"
            else:
                status = "optimal"
                recommendation = "Capacity utilization is at optimal levels"
            
            # Calculate by stylist
            stylist_utilization = []
            for perf in current_data:
                if perf.hours_scheduled > 0:
                    stylist_utilization.append({
                        "staff_id": perf.staff_id,
                        "staff_name": perf.staff.full_name,
                        "utilization": perf.utilization_percent,
                        "hours_booked": perf.hours_booked,
                        "hours_scheduled": perf.hours_scheduled
                    })
            
            # Sort by utilization
            stylist_utilization.sort(key=lambda x: x['utilization'], reverse=True)
            
            return {
                "success": True,
                "overall_utilization": overall_utilization,
                "status": status,
                "recommendation": recommendation,
                "total_hours_booked": total_booked,
                "total_hours_scheduled": total_scheduled,
                "stylist_breakdown": stylist_utilization[:10],  # Top 10
                "analysis_date": latest_date.isoformat()
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            db.close()
    
    def analyze_prebooking_impact(self) -> Dict[str, Any]:
        """Analyze the impact of prebooking on client frequency"""
        db = SessionLocal()
        try:
            # Get performance data with prebooking info
            perf_data = db.query(StaffPerformance).filter(
                StaffPerformance.appointment_count > 0
            ).all()
            
            # Calculate averages
            high_prebook = [p for p in perf_data if p.prebooked_percent > 0.3]
            low_prebook = [p for p in perf_data if p.prebooked_percent <= 0.3]
            
            high_prebook_metrics = {
                "avg_appointments": np.mean([p.appointment_count for p in high_prebook]),
                "avg_client_count": np.mean([p.service_client_count for p in high_prebook]),
                "avg_sales": np.mean([p.net_sales for p in high_prebook]),
                "avg_returning_clients": np.mean([p.returning_client_count for p in high_prebook])
            }
            
            low_prebook_metrics = {
                "avg_appointments": np.mean([p.appointment_count for p in low_prebook]),
                "avg_client_count": np.mean([p.service_client_count for p in low_prebook]),
                "avg_sales": np.mean([p.net_sales for p in low_prebook]),
                "avg_returning_clients": np.mean([p.returning_client_count for p in low_prebook])
            }
            
            # Calculate impact
            appointment_increase = ((high_prebook_metrics['avg_appointments'] - low_prebook_metrics['avg_appointments']) 
                                  / low_prebook_metrics['avg_appointments'] * 100)
            sales_increase = ((high_prebook_metrics['avg_sales'] - low_prebook_metrics['avg_sales']) 
                            / low_prebook_metrics['avg_sales'] * 100)
            
            return {
                "success": True,
                "prebooking_impact": {
                    "appointment_increase_percent": appointment_increase,
                    "sales_increase_percent": sales_increase,
                    "high_prebook_stylists": len(high_prebook),
                    "low_prebook_stylists": len(low_prebook)
                },
                "high_prebook_metrics": high_prebook_metrics,
                "low_prebook_metrics": low_prebook_metrics,
                "recommendation": f"Stylists with >30% prebooking see {appointment_increase:.1f}% more appointments and {sales_increase:.1f}% higher sales"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            db.close()
    
    def get_optimal_scheduling(self, location_id: int) -> Dict[str, Any]:
        """Determine optimal scheduling for a location"""
        db = SessionLocal()
        try:
            # Get all performance data for location
            perf_data = db.query(StaffPerformance).filter(
                StaffPerformance.location_id == location_id
            ).all()
            
            if not perf_data:
                return {"success": False, "error": "No performance data for location"}
            
            # Group by utilization ranges
            utilization_ranges = {
                "0-40%": [],
                "40-60%": [],
                "60-80%": [],
                "80-100%": []
            }
            
            for perf in perf_data:
                if perf.utilization_percent <= 0.4:
                    utilization_ranges["0-40%"].append(perf)
                elif perf.utilization_percent <= 0.6:
                    utilization_ranges["40-60%"].append(perf)
                elif perf.utilization_percent <= 0.8:
                    utilization_ranges["60-80%"].append(perf)
                else:
                    utilization_ranges["80-100%"].append(perf)
            
            # Calculate optimal hours
            optimal_performers = utilization_ranges["60-80%"] + utilization_ranges["80-100%"]
            if optimal_performers:
                avg_optimal_hours = np.mean([p.hours_scheduled for p in optimal_performers])
                avg_optimal_sales = np.mean([p.net_sales for p in optimal_performers])
            else:
                avg_optimal_hours = 35  # Default
                avg_optimal_sales = 0
            
            # Generate recommendations
            recommendations = []
            for range_name, performers in utilization_ranges.items():
                if range_name == "0-40%" and performers:
                    recommendations.append(f"{len(performers)} stylists are underutilized - consider reducing their hours or increasing marketing")
                elif range_name == "80-100%" and len(performers) > len(perf_data) * 0.3:
                    recommendations.append("Many stylists are at capacity - consider hiring additional staff")
            
            return {
                "success": True,
                "optimal_hours_per_week": avg_optimal_hours,
                "current_utilization_distribution": {
                    k: len(v) for k, v in utilization_ranges.items()
                },
                "recommendations": recommendations,
                "projected_revenue_at_optimal": avg_optimal_sales * len(perf_data)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            db.close()
    
    def _calculate_prediction_features(self, performance_data: List[StaffPerformance]) -> np.ndarray:
        """Calculate features for success prediction"""
        features = []
        
        # Average metrics
        features.append(np.mean([p.utilization_percent for p in performance_data]))
        features.append(np.mean([p.prebooked_percent for p in performance_data]))
        features.append(np.mean([p.appointment_count for p in performance_data]))
        features.append(np.mean([p.service_sales_per_appointment for p in performance_data]))
        features.append(np.mean([p.new_client_count for p in performance_data]))
        
        # Growth trends
        if len(performance_data) > 1:
            sales_growth = (performance_data[-1].net_sales - performance_data[0].net_sales) / performance_data[0].net_sales
            client_growth = (performance_data[-1].service_client_count - performance_data[0].service_client_count) / max(performance_data[0].service_client_count, 1)
        else:
            sales_growth = 0
            client_growth = 0
        
        features.append(sales_growth)
        features.append(client_growth)
        
        return np.array(features).reshape(1, -1)
    
    def _predict_success(self, features: np.ndarray) -> Tuple[bool, float, Dict]:
        """Make success prediction using ML model or heuristics"""
        # For now, use heuristics until we have enough training data
        utilization = features[0][0]
        prebook_rate = features[0][1]
        avg_appointments = features[0][2]
        sales_per_appointment = features[0][3]
        
        score = 0
        factors = {}
        
        # Utilization factor
        if utilization > 0.7:
            score += 30
            factors["utilization"] = "High utilization indicates good demand"
        elif utilization > 0.5:
            score += 20
            factors["utilization"] = "Moderate utilization"
        else:
            score += 5
            factors["utilization"] = "Low utilization is concerning"
        
        # Prebooking factor
        if prebook_rate > 0.25:
            score += 25
            factors["prebooking"] = "Strong prebooking rate"
        elif prebook_rate > 0.15:
            score += 15
            factors["prebooking"] = "Average prebooking"
        else:
            score += 5
            factors["prebooking"] = "Low prebooking needs improvement"
        
        # Sales performance
        if sales_per_appointment > 50:
            score += 25
            factors["sales"] = "Excellent sales per appointment"
        elif sales_per_appointment > 40:
            score += 15
            factors["sales"] = "Good sales performance"
        else:
            score += 5
            factors["sales"] = "Sales performance needs improvement"
        
        # Growth trend
        if features[0][5] > 0.1:  # Sales growth
            score += 20
            factors["growth"] = "Positive growth trajectory"
        
        probability = score / 100
        success = probability > 0.6
        
        return success, probability, factors
    
    def _generate_recommendation(self, predicted_success: bool, factors: Dict) -> str:
        """Generate recommendation based on prediction"""
        if predicted_success:
            return "This stylist shows strong potential for success. Focus on maintaining their momentum and providing growth opportunities."
        else:
            weaknesses = []
            if "Low utilization" in str(factors.values()):
                weaknesses.append("increasing bookings through marketing")
            if "Low prebooking" in str(factors.values()):
                weaknesses.append("improving prebooking practices")
            if "Sales performance needs improvement" in str(factors.values()):
                weaknesses.append("upselling and service recommendations")
            
            return f"This stylist may need additional support. Focus on: {', '.join(weaknesses)}"
    
    async def process_analytics_query(self, query: str, user_id: str) -> Dict[str, Any]:
        """Process natural language analytics queries"""
        # Map query to appropriate analytics function
        query_lower = query.lower()
        
        if "predict" in query_lower and "success" in query_lower:
            # Extract staff name or ID from query
            return {
                "response": "To predict staff success, please provide the staff member's name or ID.",
                "action_needed": "staff_selection"
            }
        
        elif "capacity" in query_lower or "utilization" in query_lower:
            result = self.analyze_capacity_utilization()
            if result['success']:
                response = f"Current capacity utilization is {result['overall_utilization']:.1f}%. "
                response += f"The salon is {result['status']}. {result['recommendation']}"
                return {
                    "response": response,
                    "data": result
                }
        
        elif "prebooking" in query_lower and "frequency" in query_lower:
            result = self.analyze_prebooking_impact()
            if result['success']:
                response = f"Prebooking has a significant impact on client frequency. "
                response += result['recommendation']
                return {
                    "response": response,
                    "data": result
                }
        
        elif "optimal" in query_lower and ("hours" in query_lower or "scheduling" in query_lower):
            # Would need location context
            return {
                "response": "To determine optimal scheduling, please specify the salon location.",
                "action_needed": "location_selection"
            }
        
        else:
            # Use Gemini for general analytics questions
            prompt = f"""
            You are a salon analytics expert. Answer this question based on salon performance data:
            {query}
            
            Provide actionable insights and specific recommendations.
            """
            
            if self.gemini_model:
                try:
                    response = self.gemini_model.generate_content(prompt)
                    return {
                        "response": response.text,
                        "data": None
                    }
                except Exception as e:
                    logger.error(f"Error generating Gemini response: {e}")
                    return {
                        "response": "Sorry, I encountered an error generating a response.",
                        "data": None
                    }
            else:
                return {
                    "response": "Sorry, AI features are currently unavailable.",
                    "data": None
                } 