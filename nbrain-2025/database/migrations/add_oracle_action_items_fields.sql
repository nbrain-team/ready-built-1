-- Add fields for deletion tracking and task conversion to oracle_action_items table

-- Add deleted flag
ALTER TABLE oracle_action_items 
ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN DEFAULT FALSE;

-- Add deletion metadata
ALTER TABLE oracle_action_items 
ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE;

-- Add task conversion tracking
ALTER TABLE oracle_action_items 
ADD COLUMN IF NOT EXISTS task_created BOOLEAN DEFAULT FALSE;

-- Add task ID reference
ALTER TABLE oracle_action_items 
ADD COLUMN IF NOT EXISTS task_id VARCHAR(255);

-- Add index for deleted items
CREATE INDEX IF NOT EXISTS idx_oracle_action_items_deleted 
ON oracle_action_items(user_id, is_deleted);

-- Add index for task conversion
CREATE INDEX IF NOT EXISTS idx_oracle_action_items_task_created 
ON oracle_action_items(user_id, task_created); 