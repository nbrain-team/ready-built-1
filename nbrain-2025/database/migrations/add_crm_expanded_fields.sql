-- Add expanded CRM opportunity fields

-- Opportunity type field
ALTER TABLE crm_opportunities 
ADD COLUMN IF NOT EXISTS opportunity_type VARCHAR(50);

-- Owner field
ALTER TABLE crm_opportunities 
ADD COLUMN IF NOT EXISTS owner VARCHAR(255);

-- Sales pipeline field
ALTER TABLE crm_opportunities 
ADD COLUMN IF NOT EXISTS sales_pipeline VARCHAR(50);

-- Stage field
ALTER TABLE crm_opportunities 
ADD COLUMN IF NOT EXISTS stage VARCHAR(50);

-- Estimated close date field
ALTER TABLE crm_opportunities 
ADD COLUMN IF NOT EXISTS est_close_date VARCHAR(50);

-- Actual close date field
ALTER TABLE crm_opportunities 
ADD COLUMN IF NOT EXISTS close_date VARCHAR(50);

-- Engagement type field
ALTER TABLE crm_opportunities 
ADD COLUMN IF NOT EXISTS engagement_type VARCHAR(50);

-- Win likelihood field
ALTER TABLE crm_opportunities 
ADD COLUMN IF NOT EXISTS win_likelihood VARCHAR(10);

-- Forecast category field
ALTER TABLE crm_opportunities 
ADD COLUMN IF NOT EXISTS forecast_category VARCHAR(50);

-- Add indexes for better performance
CREATE INDEX IF NOT EXISTS idx_crm_opportunity_type ON crm_opportunities(opportunity_type);
CREATE INDEX IF NOT EXISTS idx_crm_owner ON crm_opportunities(owner);
CREATE INDEX IF NOT EXISTS idx_crm_sales_pipeline ON crm_opportunities(sales_pipeline);
CREATE INDEX IF NOT EXISTS idx_crm_stage ON crm_opportunities(stage);
CREATE INDEX IF NOT EXISTS idx_crm_close_dates ON crm_opportunities(est_close_date, close_date); 