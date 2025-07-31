-- Check CRM records on Render database

-- 1. Count total CRM opportunities
SELECT COUNT(*) as total_records FROM crm_opportunities;

-- 2. Show first 10 records with key fields
SELECT 
    id,
    client_opportunity as company,
    lead_status,
    deal_status,
    stage,
    contact_name,
    status,
    created_at
FROM crm_opportunities 
ORDER BY created_at DESC 
LIMIT 10;

-- 3. Check for records with missing required fields
SELECT COUNT(*) as missing_required_fields
FROM crm_opportunities 
WHERE status IS NULL OR client_opportunity IS NULL;

-- 4. If you find records with NULL status, fix them:
-- UPDATE crm_opportunities SET status = 'Active' WHERE status IS NULL;

-- 5. Check all columns in the table
SELECT column_name, data_type, is_nullable
FROM information_schema.columns 
WHERE table_name = 'crm_opportunities'
ORDER BY ordinal_position;

-- 6. Check if there are any records from before today (to verify old data exists)
SELECT 
    COUNT(*) as old_records,
    MIN(created_at) as oldest_record,
    MAX(created_at) as newest_record
FROM crm_opportunities
WHERE created_at < CURRENT_DATE; 