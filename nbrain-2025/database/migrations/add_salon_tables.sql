-- Salon Analytics Tables Migration

-- Salon Locations
CREATE TABLE IF NOT EXISTS salon_locations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL UNIQUE,
    code VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_salon_locations_name ON salon_locations(name);

-- Salon Staff
CREATE TABLE IF NOT EXISTS salon_staff (
    id SERIAL PRIMARY KEY,
    payroll_last_name VARCHAR(100),
    payroll_first_name VARCHAR(100),
    preferred_first_name VARCHAR(100),
    full_name VARCHAR(200) NOT NULL,
    job_title VARCHAR(100),
    location_id INTEGER REFERENCES salon_locations(id),
    department VARCHAR(100),
    position_status VARCHAR(50),
    hire_date DATE,
    rehire_date DATE,
    termination_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_salon_staff_name ON salon_staff(full_name);
CREATE INDEX idx_salon_staff_location ON salon_staff(location_id);
CREATE INDEX idx_salon_staff_status ON salon_staff(position_status);

-- Staff Performance
CREATE TABLE IF NOT EXISTS staff_performance (
    id SERIAL PRIMARY KEY,
    location_id INTEGER REFERENCES salon_locations(id),
    staff_id INTEGER REFERENCES salon_staff(id),
    period_date DATE NOT NULL,
    hours_booked FLOAT,
    hours_scheduled FLOAT,
    utilization_percent FLOAT,
    prebooked_percent FLOAT,
    self_booked_percent FLOAT,
    appointment_count INTEGER,
    service_count INTEGER,
    service_sales FLOAT,
    service_sales_per_appointment FLOAT,
    tip_sales FLOAT,
    order_client_count INTEGER,
    service_client_count INTEGER,
    new_client_count INTEGER,
    returning_client_count INTEGER,
    product_quantity_sold INTEGER,
    net_retail_product_sales FLOAT,
    net_package_sales FLOAT,
    retail_product_client_count INTEGER,
    membership_client_count INTEGER,
    package_client_count INTEGER,
    discount_amount FLOAT,
    gross_sales FLOAT,
    net_sales FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_staff_performance UNIQUE (staff_id, period_date)
);

CREATE INDEX idx_staff_performance_date ON staff_performance(period_date);
CREATE INDEX idx_staff_performance_location ON staff_performance(location_id);
CREATE INDEX idx_staff_performance_utilization ON staff_performance(utilization_percent);

-- Salon Clients
CREATE TABLE IF NOT EXISTS salon_clients (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    first_visit_date DATE,
    last_visit_date DATE,
    visit_count INTEGER DEFAULT 0,
    total_spent FLOAT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    client_type VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_salon_clients_name ON salon_clients(name);
CREATE INDEX idx_salon_clients_type ON salon_clients(client_type);

-- Salon Appointments
CREATE TABLE IF NOT EXISTS salon_appointments (
    id SERIAL PRIMARY KEY,
    sale_id VARCHAR(100) UNIQUE,
    location_id INTEGER REFERENCES salon_locations(id),
    staff_id INTEGER REFERENCES salon_staff(id),
    client_id INTEGER REFERENCES salon_clients(id),
    sale_date TIMESTAMP NOT NULL,
    service_name VARCHAR(200),
    sale_type VARCHAR(50),
    net_service_sales FLOAT,
    net_sales FLOAT,
    is_prebooked BOOLEAN DEFAULT FALSE,
    is_self_booked BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_salon_appointments_date ON salon_appointments(sale_date);
CREATE INDEX idx_salon_appointments_staff ON salon_appointments(staff_id);
CREATE INDEX idx_salon_appointments_client ON salon_appointments(client_id);
CREATE INDEX idx_salon_appointments_location ON salon_appointments(location_id);

-- Staff Predictions
CREATE TABLE IF NOT EXISTS staff_predictions (
    id SERIAL PRIMARY KEY,
    staff_id INTEGER REFERENCES salon_staff(id),
    prediction_date DATE NOT NULL,
    weeks_since_hire INTEGER,
    predicted_success BOOLEAN,
    success_probability FLOAT,
    key_factors JSONB,
    actual_outcome BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_staff_predictions_staff ON staff_predictions(staff_id);
CREATE INDEX idx_staff_predictions_date ON staff_predictions(prediction_date);

-- Salon Analytics
CREATE TABLE IF NOT EXISTS salon_analytics (
    id SERIAL PRIMARY KEY,
    location_id INTEGER REFERENCES salon_locations(id),
    metric_type VARCHAR(100) NOT NULL,
    metric_date DATE NOT NULL,
    metric_value FLOAT,
    metric_data JSONB,
    insights TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_salon_analytics_type ON salon_analytics(metric_type);
CREATE INDEX idx_salon_analytics_date ON salon_analytics(metric_date);
CREATE INDEX idx_salon_analytics_location ON salon_analytics(location_id); 