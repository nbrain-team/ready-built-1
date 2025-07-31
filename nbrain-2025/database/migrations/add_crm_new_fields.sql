-- Add new fields to CRM opportunities table

-- Lead status field
ALTER TABLE crm_opportunities 
ADD COLUMN IF NOT EXISTS lead_status VARCHAR(50);

-- Job title field
ALTER TABLE crm_opportunities 
ADD COLUMN IF NOT EXISTS job_title VARCHAR(255);

-- Company address field
ALTER TABLE crm_opportunities 
ADD COLUMN IF NOT EXISTS company_address TEXT;

-- Update existing opportunities to have a default lead status
UPDATE crm_opportunities 
SET lead_status = 'New Lead' 
WHERE lead_status IS NULL;

-- Add indexes for better performance
CREATE INDEX IF NOT EXISTS idx_crm_lead_status ON crm_opportunities(lead_status);
CREATE INDEX IF NOT EXISTS idx_crm_job_title ON crm_opportunities(job_title); 