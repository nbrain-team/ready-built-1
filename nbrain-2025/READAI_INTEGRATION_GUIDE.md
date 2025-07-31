# Read.ai Integration Guide

This guide explains how to set up the Read.ai webhook integration with nBrain to automatically import meeting transcripts and insights.

## Overview

The Read.ai integration allows you to:
- Automatically receive meeting transcripts via webhooks
- Extract action items and sync them to Oracle
- Associate meetings with clients automatically
- Search through meeting content
- Generate insights from meeting data

## Setup Instructions

### Step 1: Generate Webhook Credentials

1. Log into nBrain platform
2. Navigate to Settings or Integrations page
3. Click on "Read.ai Integration"
4. Click "Generate Webhook Secret"
5. Save the provided:
   - **Webhook URL**: `https://your-app.onrender.com/webhooks/readai`
   - **Webhook Secret**: A secure token for verifying webhooks

### Step 2: Configure Read.ai

1. Log into your Read.ai account
2. Go to Settings > Integrations > Webhooks
3. Add a new webhook with:
   - **URL**: The webhook URL from Step 1
   - **Secret**: The webhook secret from Step 1
   - **Events**: Select all meeting-related events:
     - Meeting completed
     - Transcript ready
     - Summary generated
     - Action items extracted

### Step 3: Test the Integration

1. Have a meeting with Read.ai enabled
2. After the meeting ends, Read.ai will send the transcript to nBrain
3. Check the integration status in nBrain to confirm receipt

## Webhook Data Flow

```
Read.ai Meeting → Webhook → nBrain Processing:
├── Store meeting transcript and metadata
├── Associate with client (if email domains match)
├── Create Oracle action items
├── Generate insights
└── Make searchable in platform
```

## Features

### Automatic Client Association

The system automatically associates meetings with clients by:
1. Checking participant email domains against client domains
2. Matching participant emails with client sync email addresses
3. Matching with primary contact emails

### Oracle Integration

Meeting data automatically syncs to Oracle:
- Action items become Oracle tasks
- Meeting summaries become insights
- Key discussion points are highlighted

### Search Capabilities

You can search meetings through:
- Oracle unified search
- Client portal meeting history
- Direct Read.ai meeting search endpoint

## API Endpoints

### Webhook Endpoint (for Read.ai)
```
POST /webhooks/readai
Headers:
  X-Readai-Signature: <webhook signature>
Body: JSON webhook payload
```

### User Endpoints

#### Get Integration Status
```
GET /readai/integration-status
Authorization: Bearer <token>
```

#### Generate Webhook Secret
```
POST /readai/generate-webhook-secret
Authorization: Bearer <token>
```

#### List Meetings
```
GET /readai/meetings?limit=20&client_id=<optional>
Authorization: Bearer <token>
```

#### Get Meeting Details
```
GET /readai/meetings/{meeting_id}
Authorization: Bearer <token>
```

#### Search Meetings
```
POST /readai/search
Authorization: Bearer <token>
Body: {
  "query": "search terms",
  "client_id": "optional client filter"
}
```

## Webhook Payload Format

Read.ai should send webhooks in this general format:
```json
{
  "event_type": "meeting.completed",
  "meeting_id": "unique-meeting-id",
  "user_email": "user@example.com",
  "title": "Sales Call with ACME Corp",
  "meeting_url": "https://zoom.us/j/123456",
  "platform": "Zoom",
  "start_time": "2024-01-15T10:00:00Z",
  "end_time": "2024-01-15T11:00:00Z",
  "duration_minutes": 60,
  "participants": [
    {"email": "host@company.com", "name": "John Host"},
    {"email": "client@acme.com", "name": "Jane Client"}
  ],
  "transcript": "Full meeting transcript...",
  "summary": "Meeting summary...",
  "key_points": [
    "Discussed Q1 roadmap",
    "Agreed on pricing structure"
  ],
  "action_items": [
    {
      "title": "Send proposal by Friday",
      "assignee": "host@company.com",
      "due_date": "2024-01-19"
    }
  ],
  "sentiment_score": 0.8,
  "engagement_score": 0.9
}
```

## Security

- Webhook signatures are verified using HMAC-SHA256
- User association is done via email matching
- All data is stored encrypted at rest
- Webhook secrets should be rotated periodically

## Troubleshooting

### Webhooks Not Arriving
1. Check webhook URL is correct
2. Verify webhook secret matches
3. Check Read.ai webhook logs for errors
4. Ensure your app is publicly accessible

### Meetings Not Associated with Clients
1. Verify client email domains are set correctly
2. Add participant emails to client sync addresses
3. Check meeting participants include client emails

### Action Items Not Created
1. Ensure Read.ai is extracting action items
2. Check Oracle integration is active
3. Verify user has Oracle connected

## Environment Variables

Add to your `.env` or Render environment:
```
APP_BASE_URL=https://your-app.onrender.com
```

## Database Migration

Run the migration to create Read.ai tables:
```sql
-- Run: database/migrations/create_readai_tables.sql
```

## Support

For issues:
1. Check webhook logs in Read.ai dashboard
2. Review nBrain logs for processing errors
3. Verify integration status in nBrain
4. Contact support with webhook ID and timestamp 