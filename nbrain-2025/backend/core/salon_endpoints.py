from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Query
from typing import Dict, Any, List, Optional
from datetime import datetime, date
import json

from .auth import get_current_active_user
from .database import SessionLocal, get_db, User
from .salon_handler import SalonAnalyticsHandler
from .salon_models import (
    SalonLocation, SalonStaff, StaffPerformance, 
    SalonClient, SalonAppointment, StaffPrediction
)
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

router = APIRouter(prefix="/api/salon", tags=["salon"])
salon_handler = SalonAnalyticsHandler()

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "module": "salon_analytics"}

@router.post("/upload/staff")
async def upload_staff_data(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user)
):
    """Upload employee list CSV file"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted")
    
    content = await file.read()
    result = salon_handler.ingest_staff_data(content.decode())
    
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['error'])
    
    return result

@router.post("/upload/performance")
async def upload_performance_data(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user)
):
    """Upload staff performance CSV file"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted")
    
    content = await file.read()
    result = salon_handler.ingest_performance_data(content.decode())
    
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['error'])
    
    return result

@router.post("/upload/transactions")
async def upload_transaction_data(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user)
):
    """Upload detailed line item transaction CSV file"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted")
    
    content = await file.read()
    result = salon_handler.ingest_transaction_data(content.decode())
    
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['error'])
    
    return result

@router.post("/upload/timeclock")
async def upload_time_clock_data(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user)
):
    """Upload time clock CSV file"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted")
    
    content = await file.read()
    result = salon_handler.ingest_time_clock_data(content.decode())
    
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['error'])
    
    return result

@router.post("/upload/schedules")
async def upload_schedule_data(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user)
):
    """Upload schedule records CSV file"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted")
    
    content = await file.read()
    result = salon_handler.ingest_schedule_data(content.decode())
    
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['error'])
    
    return result

@router.post("/analytics/query")
async def process_analytics_query(
    query: Dict[str, str],
    current_user: User = Depends(get_current_active_user)
):
    """Process natural language analytics queries"""
    user_query = query.get('query', '')
    if not user_query:
        raise HTTPException(status_code=400, detail="Query is required")
    
    result = await salon_handler.process_analytics_query(user_query, current_user.id)
    return result

@router.get("/analytics/capacity")
async def get_capacity_utilization(
    location_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user)
):
    """Get capacity utilization analysis"""
    result = salon_handler.analyze_capacity_utilization(location_id)
    
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['error'])
    
    return result

@router.get("/analytics/prebooking")
async def get_prebooking_impact(
    current_user: User = Depends(get_current_active_user)
):
    """Get prebooking impact analysis"""
    result = salon_handler.analyze_prebooking_impact()
    
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['error'])
    
    return result

@router.get("/analytics/scheduling/{location_id}")
async def get_optimal_scheduling(
    location_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """Get optimal scheduling analysis for a location"""
    result = salon_handler.get_optimal_scheduling(location_id)
    
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['error'])
    
    return result

@router.post("/predict/staff/{staff_id}")
async def predict_staff_success(
    staff_id: int,
    weeks: int = 6,
    current_user: User = Depends(get_current_active_user)
):
    """Predict staff success based on early performance"""
    result = salon_handler.predict_staff_success(staff_id, weeks)
    
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['error'])
    
    return result

@router.get("/locations")
async def get_locations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all salon locations"""
    locations = db.query(SalonLocation).filter_by(is_active=True).all()
    return [{
        "id": loc.id,
        "name": loc.name,
        "code": loc.code
    } for loc in locations]

@router.get("/staff")
async def get_staff(
    location_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get staff members with optional filters"""
    query = db.query(SalonStaff)
    
    if location_id:
        query = query.filter(SalonStaff.location_id == location_id)
    
    if status:
        query = query.filter(SalonStaff.position_status == status)
    
    staff = query.all()
    return [{
        "id": s.id,
        "name": s.full_name,
        "job_title": s.job_title,
        "location_id": s.location_id,
        "status": s.position_status,
        "hire_date": s.hire_date.isoformat() if s.hire_date else None
    } for s in staff]

@router.get("/dashboard/overview")
async def get_dashboard_overview(
    db: Session = Depends(get_db)
    # Temporarily removed for demo: current_user: dict = Depends(get_current_active_user)
):
    """Get overview data for dashboard"""
    # Get latest performance date
    latest_perf = db.query(func.max(StaffPerformance.period_date)).scalar()
    
    if not latest_perf:
        return {
            "total_locations": 0,
            "total_staff": 0,
            "active_staff": 0,
            "avg_utilization": 0,
            "total_revenue": 0,
            "new_clients": 0
        }
    
    # Get current month data
    current_data = db.query(StaffPerformance).filter(
        StaffPerformance.period_date == latest_perf
    ).all()
    
    # Calculate metrics
    total_locations = db.query(SalonLocation).count()
    total_staff = db.query(SalonStaff).count()
    active_staff = db.query(SalonStaff).filter_by(position_status='A').count()
    
    if current_data:
        # Handle division by zero and ensure JSON-compliant values
        utilization_values = [p.utilization_percent for p in current_data if p.utilization_percent is not None]
        avg_utilization = sum(utilization_values) / len(utilization_values) if utilization_values else 0.0
        
        total_revenue = sum(p.net_sales or 0 for p in current_data)
        new_clients = sum(p.new_client_count or 0 for p in current_data)
    else:
        avg_utilization = 0.0
        total_revenue = 0.0
        new_clients = 0
    
    # Ensure all values are JSON-compliant (no infinity or NaN)
    import math
    if math.isnan(avg_utilization) or math.isinf(avg_utilization):
        avg_utilization = 0.0
    
    return {
        "total_locations": total_locations,
        "total_staff": total_staff,
        "active_staff": active_staff,
        "avg_utilization": float(avg_utilization),  # Ensure it's a proper float
        "total_revenue": float(total_revenue),
        "new_clients": int(new_clients),
        "period": latest_perf.isoformat() if latest_perf else None
    }

@router.get("/dashboard/performance-trends")
async def get_performance_trends(
    location_id: Optional[int] = Query(None),
    months: int = Query(6, ge=1, le=24),
    db: Session = Depends(get_db)
    # Temporarily removed for demo: current_user: dict = Depends(get_current_active_user)
):
    """Get performance trends over time"""
    import math
    
    query = db.query(
        StaffPerformance.period_date,
        func.sum(StaffPerformance.net_sales).label('total_sales'),
        func.avg(StaffPerformance.utilization_percent).label('avg_utilization'),
        func.sum(StaffPerformance.appointment_count).label('total_appointments'),
        func.sum(StaffPerformance.new_client_count).label('new_clients')
    ).group_by(StaffPerformance.period_date)
    
    if location_id:
        query = query.filter(StaffPerformance.location_id == location_id)
    
    query = query.order_by(desc(StaffPerformance.period_date)).limit(months)
    
    trends = query.all()
    
    result = []
    for trend in trends:
        avg_util = float(trend.avg_utilization or 0)
        if math.isnan(avg_util) or math.isinf(avg_util):
            avg_util = 0.0
            
        result.append({
            "period": trend.period_date.isoformat(),
            "total_sales": float(trend.total_sales or 0),
            "avg_utilization": avg_util,
            "total_appointments": int(trend.total_appointments or 0),
            "new_clients": int(trend.new_clients or 0)
        })
    
    return result

@router.get("/dashboard/top-performers")
async def get_top_performers(
    metric: str = Query("sales", regex="^(sales|utilization|appointments|prebooking)$"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
    # Temporarily removed for demo: current_user: dict = Depends(get_current_active_user)
):
    """Get top performing staff by various metrics"""
    import math
    
    # Get latest performance date
    latest_perf = db.query(func.max(StaffPerformance.period_date)).scalar()
    
    if not latest_perf:
        return []
    
    # Join with staff and location tables to ensure relationships are loaded
    from sqlalchemy.orm import joinedload
    
    query = db.query(StaffPerformance).options(
        joinedload(StaffPerformance.staff),
        joinedload(StaffPerformance.location)
    ).filter(
        StaffPerformance.period_date == latest_perf
    )
    
    # Sort by requested metric
    if metric == "sales":
        query = query.order_by(desc(StaffPerformance.net_sales))
    elif metric == "utilization":
        query = query.order_by(desc(StaffPerformance.utilization_percent))
    elif metric == "appointments":
        query = query.order_by(desc(StaffPerformance.appointment_count))
    elif metric == "prebooking":
        query = query.order_by(desc(StaffPerformance.prebooked_percent))
    
    performers = query.limit(limit).all()
    
    result = []
    for p in performers:
        # Ensure all float values are JSON-compliant
        utilization = float(p.utilization_percent or 0)
        prebooking = float(p.prebooked_percent or 0)
        
        if math.isnan(utilization) or math.isinf(utilization):
            utilization = 0.0
        if math.isnan(prebooking) or math.isinf(prebooking):
            prebooking = 0.0
            
        result.append({
            "staff_id": p.staff_id,
            "staff_name": p.staff.full_name if p.staff else "Unknown",
            "location": p.location.name if p.location else "Unknown",
            "net_sales": float(p.net_sales or 0),
            "utilization": utilization,
            "appointments": int(p.appointment_count or 0),
            "prebooking": prebooking
        })
    
    return result

def setup_salon_endpoints(app):
    """Setup salon endpoints in the main app"""
    app.include_router(router) 