# Google Docs Integration Setup Guide

This guide explains how to set up Google Docs integration for the nBrain platform.

## Overview

The Google Docs integration allows the system to:
- Create professional agent specification documents
- Generate content documents (blog posts, meeting notes, etc.)
- Save documents to Google Drive
- Share documents with appropriate permissions

## Prerequisites

1. A Google Cloud Platform (GCP) account
2. A project in GCP with billing enabled
3. Admin access to enable APIs

## Setup Steps

### 1. Create a Service Account

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Select your project or create a new one
3. Navigate to **IAM & Admin** > **Service Accounts**
4. Click **Create Service Account**
5. Fill in the details:
   - Service account name: `nbrain-docs-service`
   - Service account ID: (auto-generated)
   - Description: "Service account for nBrain Google Docs integration"
6. Click **Create and Continue**

### 2. Grant Permissions

Grant the following roles to the service account:
- **Google Docs API Editor**
- **Google Drive API Editor**

Click **Continue** and then **Done**.

### 3. Create Service Account Key

1. Click on the created service account
2. Go to the **Keys** tab
3. Click **Add Key** > **Create New Key**
4. Choose **JSON** format
5. Click **Create** - a JSON file will be downloaded

### 4. Enable Required APIs

In the Google Cloud Console:
1. Go to **APIs & Services** > **Library**
2. Search for and enable:
   - **Google Docs API**
   - **Google Drive API**

### 5. Configure Environment Variables

You have two options for configuring the credentials:

#### Option A: JSON String (Recommended for cloud deployments)

1. Open the downloaded JSON file
2. Copy the entire contents
3. Set the environment variable:
   ```bash
   GOOGLE_SERVICE_ACCOUNT_JSON='<paste-json-contents-here>'
   ```

#### Option B: File Path (For local development)

1. Place the JSON file in your backend directory
2. Set the environment variable:
   ```bash
   GOOGLE_SERVICE_ACCOUNT_PATH='/path/to/service-account-key.json'
   ```

### 6. For Render.com Deployment

1. Go to your Render dashboard
2. Select your backend service
3. Go to **Environment** tab
4. Add a new environment variable:
   - Key: `GOOGLE_SERVICE_ACCOUNT_JSON`
   - Value: (paste the entire JSON content)
5. Save and deploy

## Troubleshooting

### Common Issues

1. **"Google Docs service not configured" error**
   - Verify environment variables are set correctly
   - Check that the JSON is valid (no extra quotes or escaping)
   - Ensure the service account has proper permissions

2. **"Failed to create Google Doc" error**
   - Check that Google Docs API and Drive API are enabled
   - Verify the service account has Editor permissions
   - Check application logs for detailed error messages

3. **Documents created but not accessible**
   - The service account creates documents in its own Drive
   - Documents are automatically shared with "anyone with link" permission
   - You may need to transfer ownership or adjust sharing settings

## Security Best Practices

1. **Never commit service account keys to version control**
2. **Use environment variables for production deployments**
3. **Regularly rotate service account keys**
4. **Grant minimum required permissions**
5. **Monitor service account usage in GCP**

## Alternative: OAuth2 Flow

For user-specific document creation (documents owned by the user), you can implement OAuth2 flow instead of service accounts. This requires:
- Setting up OAuth2 consent screen
- Creating OAuth2 credentials
- Implementing the authorization flow in the application

Contact the development team if you need user-specific document ownership.

## Support

If you encounter issues:
1. Check the application logs for detailed error messages
2. Verify all setup steps were completed
3. Ensure APIs are enabled and billing is active
4. Contact your system administrator for assistance 