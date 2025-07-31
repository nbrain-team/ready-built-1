-- Fix CRM status field confusion
-- The status field should be Active/Closed/Dead
-- The deal_status field should have the sales stage values

-- First, let's see what we have
SELECT DISTINCT status FROM crm_opportunities;

-- Update records where status has deal stage values
UPDATE crm_opportunities 
SET 
    deal_status = status,  -- Move the sales stage to deal_status
    status = 'Active'      -- Set all to Active (you can manually update Closed ones later)
WHERE status IN ('Cold Lead', 'Warm Lead', 'Intro Email', 'Intro', 'Discovery', 
                 'Presentation', 'Proposal', 'Closed', 'Dead');

-- For any records where status is already 'Closed' or 'Dead', keep them
UPDATE crm_opportunities 
SET status = 'Closed'
WHERE deal_status = 'Closed' AND status = 'Active';

UPDATE crm_opportunities 
SET status = 'Dead'
WHERE deal_status = 'Dead' AND status = 'Active';

-- Verify the fix
SELECT 
    COUNT(*) as total,
    COUNT(CASE WHEN status = 'Active' THEN 1 END) as active_count,
    COUNT(CASE WHEN status = 'Closed' THEN 1 END) as closed_count,
    COUNT(CASE WHEN status = 'Dead' THEN 1 END) as dead_count
FROM crm_opportunities; 