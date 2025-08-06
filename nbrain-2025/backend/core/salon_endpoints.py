from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Query
from typing import Dict, Any, List, Optional
from datetime import datetime, date
import json
import math

from .auth import get_current_active_user
from .database import SessionLocal, get_db, User
from .salon_handler import SalonAnalyticsHandler
from .salon_models import (
    SalonLocation, SalonStaff, StaffPerformance, 
    SalonClient, SalonAppointment, StaffPrediction,
    SalonTransaction  # Added this import
)
from .salon_ai_assistant import salon_ai_assistant  # Add new AI assistant
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

router = APIRouter(prefix="/api/salon", tags=["salon"])
salon_handler = SalonAnalyticsHandler()

def sanitize_float_value(value: Any) -> Any:
    """Ensure float values are JSON-compliant (no NaN, infinity)"""
    if value is None:
        return None
    elif isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return 0.0
        return value
    elif isinstance(value, int):
        # Ensure integers don't overflow
        if value > 2**53 or value < -(2**53):
            return float(value)
        return value
    elif isinstance(value, dict):
        return {k: sanitize_float_value(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [sanitize_float_value(item) for item in value]
    elif isinstance(value, tuple):
        return tuple(sanitize_float_value(item) for item in value)
    return value

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
    # Temporarily removed for demo: current_user: User = Depends(get_current_active_user)
):
    """Process natural language analytics queries using AI assistant"""
    user_query = query.get('query', '')
    if not user_query:
        raise HTTPException(status_code=400, detail="Query is required")
    
    # Use the new AI assistant for all queries
    result = await salon_ai_assistant.process_query(user_query, "demo_user")
    
    # Ensure JSON serializable
    return sanitize_float_value(result)

@router.get("/analytics/capacity")
async def get_capacity_utilization(
    location_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user)
):
    """Get capacity utilization analysis"""
    result = salon_handler.analyze_capacity_utilization(location_id)
    
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['error'])
    
    # Sanitize the result before returning
    return sanitize_float_value(result)

@router.get("/analytics/prebooking")
async def get_prebooking_impact(
    current_user: User = Depends(get_current_active_user)
):
    """Get prebooking impact analysis"""
    result = salon_handler.analyze_prebooking_impact()
    
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['error'])
    
    # Sanitize the result before returning
    return sanitize_float_value(result)

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
    from sqlalchemy import and_
    from datetime import datetime, timedelta
    
    # Get January 2025 data from salon_transactions
    start_date = date(2025, 1, 1)
    end_date = date(2025, 1, 31)
    
    # Get transaction-based metrics
    total_transactions = db.query(func.count(SalonTransaction.id)).filter(
        and_(
            SalonTransaction.sale_date >= start_date,
            SalonTransaction.sale_date <= end_date
        )
    ).scalar() or 0
    
    total_revenue = db.query(func.sum(SalonTransaction.net_sales)).filter(
        and_(
            SalonTransaction.sale_date >= start_date,
            SalonTransaction.sale_date <= end_date
        )
    ).scalar() or 0
    
    unique_clients = db.query(func.count(func.distinct(SalonTransaction.client_name))).filter(
        and_(
            SalonTransaction.sale_date >= start_date,
            SalonTransaction.sale_date <= end_date,
            SalonTransaction.client_name.isnot(None)
        )
    ).scalar() or 0
    
    # Get location and staff counts
    total_locations = db.query(SalonLocation).filter_by(is_active=True).count()
    total_staff = db.query(SalonStaff).count()
    active_staff = db.query(SalonStaff).filter_by(position_status='A - Active').count()
    
    # Calculate daily average
    days_in_month = 30
    avg_daily_revenue = total_revenue / days_in_month if total_revenue else 0
    
    return sanitize_float_value({
        "total_locations": total_locations,
        "total_staff": total_staff,
        "active_staff": active_staff,
        "total_transactions": total_transactions,
        "total_revenue": float(total_revenue),
        "unique_clients": unique_clients,
        "avg_daily_revenue": float(avg_daily_revenue),
        "period": "January 2025"
    })

@router.get("/dashboard/performance-trends")
async def get_performance_trends(
    location_id: Optional[int] = Query(None),
    months: int = Query(6, ge=1, le=24),
    db: Session = Depends(get_db)
    # Temporarily removed for demo: current_user: dict = Depends(get_current_active_user)
):
    """Get performance trends over time from transactions"""
    from sqlalchemy import and_, extract
    
    # Get daily trends for January 2025
    query = db.query(
        SalonTransaction.sale_date,
        func.count(SalonTransaction.id).label('transaction_count'),
        func.sum(SalonTransaction.net_sales).label('total_sales'),
        func.sum(SalonTransaction.net_service_sales).label('service_sales'),
        func.count(func.distinct(SalonTransaction.client_name)).label('unique_clients')
    ).filter(
        SalonTransaction.sale_date >= date(2025, 1, 1)
    ).group_by(SalonTransaction.sale_date)
    
    if location_id:
        query = query.filter(SalonTransaction.location_id == location_id)
    
    query = query.order_by(SalonTransaction.sale_date)
    trends = query.all()
    
    result = []
    for trend in trends:
        result.append({
            "period": trend.sale_date.isoformat(),
            "transaction_count": int(trend.transaction_count or 0),
            "total_sales": float(trend.total_sales or 0),
            "service_sales": float(trend.service_sales or 0) if trend.service_sales else 0,
            "unique_clients": int(trend.unique_clients or 0)
        })
    
    return sanitize_float_value(result)

@router.get("/dashboard/top-performers")
async def get_top_performers(
    metric: str = Query("sales", regex="^(sales|utilization|appointments|prebooking|transactions)$"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
    # Temporarily removed for demo: current_user: dict = Depends(get_current_active_user)
):
    """Get top performing staff by various metrics"""
    from sqlalchemy import and_
    
    # Get top performers from transaction data for January 2025
    if metric in ["sales", "transactions"]:
        query = db.query(
            SalonTransaction.staff_id,
            SalonStaff.full_name,
            SalonLocation.name.label('location_name'),
            func.count(SalonTransaction.id).label('transaction_count'),
            func.sum(SalonTransaction.net_sales).label('total_sales'),
            func.count(func.distinct(SalonTransaction.client_name)).label('unique_clients')
        ).join(
            SalonStaff, SalonTransaction.staff_id == SalonStaff.id
        ).join(
            SalonLocation, SalonTransaction.location_id == SalonLocation.id
        ).filter(
            and_(
                SalonTransaction.sale_date >= date(2025, 1, 1),
                SalonTransaction.sale_date <= date(2025, 1, 31)
            )
        ).group_by(
            SalonTransaction.staff_id,
            SalonStaff.full_name,
            SalonLocation.name
        )
        
        if metric == "sales":
            query = query.order_by(desc(func.sum(SalonTransaction.net_sales)))
        else:
            query = query.order_by(desc(func.count(SalonTransaction.id)))
        
        performers = query.limit(limit).all()
        
        result = []
        for p in performers:
            result.append({
                "staff_id": p.staff_id,
                "staff_name": p.full_name,
                "location": p.location_name,
                "net_sales": float(p.total_sales or 0),
                "transactions": int(p.transaction_count or 0),
                "unique_clients": int(p.unique_clients or 0),
                "avg_ticket": float(p.total_sales / p.transaction_count) if p.transaction_count else 0
            })
        
        return sanitize_float_value(result)
    
    # Fall back to performance table for other metrics
    latest_perf = db.query(func.max(StaffPerformance.period_date)).scalar()
    
    if not latest_perf:
        return []
    
    from sqlalchemy.orm import joinedload
    
    query = db.query(StaffPerformance).options(
        joinedload(StaffPerformance.staff),
        joinedload(StaffPerformance.location)
    ).filter(
        StaffPerformance.period_date == latest_perf
    )
    
    if metric == "utilization":
        query = query.order_by(desc(StaffPerformance.utilization_percent))
    elif metric == "appointments":
        query = query.order_by(desc(StaffPerformance.appointment_count))
    elif metric == "prebooking":
        query = query.order_by(desc(StaffPerformance.prebooked_percent))
    
    performers = query.limit(limit).all()
    
    result = []
    for p in performers:
        utilization = float(p.utilization_percent or 0)
        prebooking = float(p.prebooked_percent or 0)
        
        import math
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
    
    return sanitize_float_value(result)

@router.get("/debug/check-data")
async def debug_check_data(
    db: Session = Depends(get_db)
):
    """Debug endpoint to check for problematic data"""
    import logging
    logger = logging.getLogger(__name__)
    
    # Check for NaN or infinity values in the database
    problematic_records = []
    
    # Check StaffPerformance records
    performances = db.query(StaffPerformance).limit(10).all()
    for p in performances:
        issues = []
        if p.utilization_percent is not None:
            if isinstance(p.utilization_percent, float):
                if math.isnan(p.utilization_percent):
                    issues.append("utilization_percent is NaN")
                elif math.isinf(p.utilization_percent):
                    issues.append("utilization_percent is infinity")
        
        if p.prebooked_percent is not None:
            if isinstance(p.prebooked_percent, float):
                if math.isnan(p.prebooked_percent):
                    issues.append("prebooked_percent is NaN")
                elif math.isinf(p.prebooked_percent):
                    issues.append("prebooked_percent is infinity")
        
        if p.net_sales is not None:
            if isinstance(p.net_sales, float):
                if math.isnan(p.net_sales):
                    issues.append("net_sales is NaN")
                elif math.isinf(p.net_sales):
                    issues.append("net_sales is infinity")
        
        if issues:
            problematic_records.append({
                "id": p.id,
                "staff_id": p.staff_id,
                "period_date": p.period_date.isoformat() if p.period_date else None,
                "issues": issues
            })
    
    return {
        "total_performance_records": db.query(StaffPerformance).count(),
        "problematic_records": problematic_records,
        "sample_utilization_values": [
            p.utilization_percent for p in performances[:5]
        ]
    }

@router.get("/transactions/search")
async def search_transactions(
    search: Optional[str] = Query(None),
    location_id: Optional[int] = Query(None),
    staff_id: Optional[int] = Query(None),
    sale_type: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Search and filter transactions with all available fields"""
    from sqlalchemy import and_, or_
    
    query = db.query(SalonTransaction).join(
        SalonLocation, SalonTransaction.location_id == SalonLocation.id, isouter=True
    ).join(
        SalonStaff, SalonTransaction.staff_id == SalonStaff.id, isouter=True
    )
    
    filters = []
    
    if search:
        search_term = f"%{search}%"
        filters.append(or_(
            SalonTransaction.client_name.ilike(search_term),
            SalonTransaction.service_name.ilike(search_term),
            SalonTransaction.sale_id.ilike(search_term)
        ))
    
    if location_id:
        filters.append(SalonTransaction.location_id == location_id)
    
    if staff_id:
        filters.append(SalonTransaction.staff_id == staff_id)
    
    if sale_type:
        filters.append(SalonTransaction.sale_type == sale_type)
    
    if start_date:
        filters.append(SalonTransaction.sale_date >= start_date)
    
    if end_date:
        filters.append(SalonTransaction.sale_date <= end_date)
    
    if filters:
        query = query.filter(and_(*filters))
    
    # Get total count
    total = query.count()
    
    # Get paginated results
    transactions = query.order_by(desc(SalonTransaction.sale_date)).limit(limit).offset(offset).all()
    
    results = []
    for t in transactions:
        results.append({
            "id": t.id,
            "sale_id": t.sale_id,
            "sale_date": t.sale_date.isoformat(),
            "location": t.location.name if t.location else None,
            "staff_name": t.staff.full_name if t.staff else None,
            "client_name": t.client_name,
            "service_name": t.service_name,
            "sale_type": t.sale_type,
            "net_service_sales": float(t.net_service_sales or 0),
            "net_sales": float(t.net_sales or 0)
        })
    
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "results": results
    }

@router.get("/analytics/service-breakdown")
async def get_service_breakdown(
    location_id: Optional[int] = Query(None),
    start_date: Optional[date] = Query(date(2025, 1, 1)),
    end_date: Optional[date] = Query(date(2025, 1, 31)),
    db: Session = Depends(get_db)
):
    """Get service breakdown analytics"""
    from sqlalchemy import and_
    
    query = db.query(
        SalonTransaction.service_name,
        func.count(SalonTransaction.id).label('count'),
        func.sum(SalonTransaction.net_sales).label('revenue'),
        func.avg(SalonTransaction.net_sales).label('avg_price')
    ).filter(
        and_(
            SalonTransaction.sale_date >= start_date,
            SalonTransaction.sale_date <= end_date,
            SalonTransaction.service_name.isnot(None)
        )
    ).group_by(SalonTransaction.service_name)
    
    if location_id:
        query = query.filter(SalonTransaction.location_id == location_id)
    
    services = query.order_by(desc(func.sum(SalonTransaction.net_sales))).limit(20).all()
    
    result = []
    for s in services:
        if s.service_name and s.service_name != 'NaN':
            result.append({
                "service_name": s.service_name,
                "count": int(s.count),
                "revenue": float(s.revenue or 0),
                "avg_price": float(s.avg_price or 0)
            })
    
    return sanitize_float_value(result)

@router.get("/analytics/client-insights")
async def get_client_insights(
    location_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """Get client analytics and insights"""
    from sqlalchemy import and_, func
    
    # Get client frequency distribution
    client_visits = db.query(
        SalonTransaction.client_name,
        func.count(SalonTransaction.id).label('visit_count'),
        func.sum(SalonTransaction.net_sales).label('total_spent')
    ).filter(
        and_(
            SalonTransaction.sale_date >= date(2025, 1, 1),
            SalonTransaction.sale_date <= date(2025, 1, 31),
            SalonTransaction.client_name.isnot(None)
        )
    ).group_by(SalonTransaction.client_name)
    
    if location_id:
        client_visits = client_visits.filter(SalonTransaction.location_id == location_id)
    
    client_visits = client_visits.all()
    
    # Categorize clients
    new_clients = 0
    returning_clients = 0
    vip_clients = 0  # 5+ visits
    total_client_revenue = 0
    
    for client in client_visits:
        if client.visit_count == 1:
            new_clients += 1
        elif client.visit_count >= 5:
            vip_clients += 1
            returning_clients += 1
        else:
            returning_clients += 1
        total_client_revenue += client.total_spent or 0
    
    avg_client_value = total_client_revenue / len(client_visits) if client_visits else 0
    
    return sanitize_float_value({
        "total_clients": len(client_visits),
        "new_clients": new_clients,
        "returning_clients": returning_clients,
        "vip_clients": vip_clients,
        "avg_client_value": float(avg_client_value),
        "total_revenue": float(total_client_revenue)
    })

@router.get("/analytics/daily-summary")
async def get_daily_summary(
    target_date: Optional[date] = Query(None),
    db: Session = Depends(get_db)
):
    """Get detailed daily summary"""
    from sqlalchemy import and_
    
    if not target_date:
        # Get the latest date with data
        target_date = db.query(func.max(SalonTransaction.sale_date)).scalar()
    
    if not target_date:
        return {"error": "No data available"}
    
    # Get all transactions for the day
    transactions = db.query(SalonTransaction).filter(
        SalonTransaction.sale_date == target_date
    ).all()
    
    # Calculate summaries
    by_location = {}
    by_service_type = {}
    by_staff = {}
    
    for t in transactions:
        # By location
        loc_name = t.location.name if t.location else "Unknown"
        if loc_name not in by_location:
            by_location[loc_name] = {"count": 0, "revenue": 0}
        by_location[loc_name]["count"] += 1
        by_location[loc_name]["revenue"] += t.net_sales or 0
        
        # By service type
        service_type = t.sale_type or "Unknown"
        if service_type not in by_service_type:
            by_service_type[service_type] = {"count": 0, "revenue": 0}
        by_service_type[service_type]["count"] += 1
        by_service_type[service_type]["revenue"] += t.net_sales or 0
        
        # By staff
        if t.staff:
            staff_name = t.staff.full_name
            if staff_name not in by_staff:
                by_staff[staff_name] = {"count": 0, "revenue": 0}
            by_staff[staff_name]["count"] += 1
            by_staff[staff_name]["revenue"] += t.net_sales or 0
    
    return sanitize_float_value({
        "date": target_date.isoformat(),
        "total_transactions": len(transactions),
        "total_revenue": float(sum(t.net_sales or 0 for t in transactions)),
        "unique_clients": len(set(t.client_name for t in transactions if t.client_name)),
        "by_location": by_location,
        "by_service_type": by_service_type,
        "top_staff": dict(sorted(by_staff.items(), key=lambda x: x[1]["revenue"], reverse=True)[:10])
    })

def setup_salon_endpoints(app):
    """Setup salon endpoints in the main app"""
    app.include_router(router) 