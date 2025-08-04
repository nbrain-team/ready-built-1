from sqlalchemy import Column, Integer, String, Float, DateTime, Date, Boolean, ForeignKey, JSON, Text, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class SalonLocation(Base):
    """Salon locations"""
    __tablename__ = 'salon_locations'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False, unique=True)
    code = Column(String(50))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    staff_members = relationship("SalonStaff", back_populates="location")
    performance_records = relationship("StaffPerformance", back_populates="location")
    appointments = relationship("SalonAppointment", back_populates="location")

class SalonStaff(Base):
    """Salon staff members"""
    __tablename__ = 'salon_staff'
    
    id = Column(Integer, primary_key=True)
    payroll_last_name = Column(String(100))
    payroll_first_name = Column(String(100))
    preferred_first_name = Column(String(100))
    full_name = Column(String(200), nullable=False)  # For matching with performance data
    job_title = Column(String(100))
    location_id = Column(Integer, ForeignKey('salon_locations.id'))
    department = Column(String(100))
    position_status = Column(String(50))  # Active, Terminated, Leave
    hire_date = Column(Date)
    rehire_date = Column(Date)
    termination_date = Column(Date)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    location = relationship("SalonLocation", back_populates="staff_members")
    performance_records = relationship("StaffPerformance", back_populates="staff")
    appointments = relationship("SalonAppointment", back_populates="staff")
    
    # Indexes
    __table_args__ = (
        Index('idx_salon_staff_name', 'full_name'),
        Index('idx_salon_staff_location', 'location_id'),
        Index('idx_salon_staff_status', 'position_status'),
    )

class StaffPerformance(Base):
    """Staff performance and utilization metrics"""
    __tablename__ = 'staff_performance'
    
    id = Column(Integer, primary_key=True)
    location_id = Column(Integer, ForeignKey('salon_locations.id'))
    staff_id = Column(Integer, ForeignKey('salon_staff.id'))
    period_date = Column(Date, nullable=False)  # Month/Year of the performance
    hours_booked = Column(Float)
    hours_scheduled = Column(Float)
    utilization_percent = Column(Float)
    prebooked_percent = Column(Float)
    self_booked_percent = Column(Float)
    appointment_count = Column(Integer)
    service_count = Column(Integer)
    service_sales = Column(Float)
    service_sales_per_appointment = Column(Float)
    tip_sales = Column(Float)
    order_client_count = Column(Integer)
    service_client_count = Column(Integer)
    new_client_count = Column(Integer)
    returning_client_count = Column(Integer)
    product_quantity_sold = Column(Integer)
    net_retail_product_sales = Column(Float)
    net_package_sales = Column(Float)
    retail_product_client_count = Column(Integer)
    membership_client_count = Column(Integer)
    package_client_count = Column(Integer)
    discount_amount = Column(Float)
    gross_sales = Column(Float)
    net_sales = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    location = relationship("SalonLocation", back_populates="performance_records")
    staff = relationship("SalonStaff", back_populates="performance_records")
    
    # Indexes
    __table_args__ = (
        UniqueConstraint('staff_id', 'period_date', name='uq_staff_performance'),
        Index('idx_staff_performance_date', 'period_date'),
        Index('idx_staff_performance_location', 'location_id'),
        Index('idx_staff_performance_utilization', 'utilization_percent'),
    )

class SalonClient(Base):
    """Salon clients"""
    __tablename__ = 'salon_clients'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    first_visit_date = Column(Date)
    last_visit_date = Column(Date)
    visit_count = Column(Integer, default=0)
    total_spent = Column(Float, default=0)
    is_active = Column(Boolean, default=True)
    client_type = Column(String(50))  # New, Returning, VIP
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    appointments = relationship("SalonAppointment", back_populates="client")
    
    # Indexes
    __table_args__ = (
        Index('idx_salon_clients_name', 'name'),
        Index('idx_salon_clients_type', 'client_type'),
    )

class SalonAppointment(Base):
    """Individual appointment records"""
    __tablename__ = 'salon_appointments'
    
    id = Column(Integer, primary_key=True)
    sale_id = Column(String(100), unique=True)
    location_id = Column(Integer, ForeignKey('salon_locations.id'))
    staff_id = Column(Integer, ForeignKey('salon_staff.id'))
    client_id = Column(Integer, ForeignKey('salon_clients.id'))
    sale_date = Column(DateTime, nullable=False)
    service_name = Column(String(200))
    sale_type = Column(String(50))  # service, gratuity, product
    net_service_sales = Column(Float)
    net_sales = Column(Float)
    is_prebooked = Column(Boolean, default=False)
    is_self_booked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    location = relationship("SalonLocation", back_populates="appointments")
    staff = relationship("SalonStaff", back_populates="appointments")
    client = relationship("SalonClient", back_populates="appointments")
    
    # Indexes
    __table_args__ = (
        Index('idx_salon_appointments_date', 'sale_date'),
        Index('idx_salon_appointments_staff', 'staff_id'),
        Index('idx_salon_appointments_client', 'client_id'),
        Index('idx_salon_appointments_location', 'location_id'),
    )

class StaffPrediction(Base):
    """Predictions for staff success/failure"""
    __tablename__ = 'staff_predictions'
    
    id = Column(Integer, primary_key=True)
    staff_id = Column(Integer, ForeignKey('salon_staff.id'))
    prediction_date = Column(Date, nullable=False)
    weeks_since_hire = Column(Integer)
    predicted_success = Column(Boolean)
    success_probability = Column(Float)
    key_factors = Column(JSON)  # Factors contributing to prediction
    actual_outcome = Column(Boolean)  # For tracking prediction accuracy
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    staff = relationship("SalonStaff")
    
    # Indexes
    __table_args__ = (
        Index('idx_staff_predictions_staff', 'staff_id'),
        Index('idx_staff_predictions_date', 'prediction_date'),
    )

class SalonAnalytics(Base):
    """Aggregated analytics and insights"""
    __tablename__ = 'salon_analytics'
    
    id = Column(Integer, primary_key=True)
    location_id = Column(Integer, ForeignKey('salon_locations.id'))
    metric_type = Column(String(100), nullable=False)  # capacity, growth_potential, scheduling_optimization
    metric_date = Column(Date, nullable=False)
    metric_value = Column(Float)
    metric_data = Column(JSON)  # Detailed data for the metric
    insights = Column(Text)  # AI-generated insights
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    location = relationship("SalonLocation")
    
    # Indexes
    __table_args__ = (
        Index('idx_salon_analytics_type', 'metric_type'),
        Index('idx_salon_analytics_date', 'metric_date'),
        Index('idx_salon_analytics_location', 'location_id'),
    ) 