# Salon Analytics Data Upload Guide

This guide explains how to upload your Blazer salon data to the nBrain platform to populate the database and enable analytics.

## Prerequisites

1. **Active nBrain Account**: You need login credentials for the platform
2. **Data Files**: The following CSV files from the `blazer/` directory:
   - `Emp List Active as of 1.1.24-7.31.25.csv` - Employee/staff data
   - `Staff Performance_Utilization - All Salons 2024.csv` - 2024 performance metrics
   - `Staff Performance_Utilization - All Salons 2025 072725.csv` - 2025 performance metrics

## Upload Methods

### Method 1: Using the Web Interface (Recommended)

1. **Login to nBrain**: https://nbrain-frontend.onrender.com
2. **Navigate to Salon Analytics**: Click on the Salon Analytics menu item
3. **Upload Files**:
   - Click "Upload Staff Data" button
   - Select `Emp List Active as of 1.1.24-7.31.25.csv`
   - Wait for confirmation message
   - Click "Upload Performance" button
   - Upload both performance CSV files (2024 and 2025)

### Method 2: Using the Shell Script

1. **Get your API token**:
   ```bash
   # Login to get token
   curl -X POST https://nbrain-backend.onrender.com/auth/login \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=YOUR_EMAIL&password=YOUR_PASSWORD"
   ```

2. **Set the token**:
   ```bash
   export API_TOKEN='your-token-from-response'
   ```

3. **Run the upload script**:
   ```bash
   ./upload_salon_data.sh
   ```

### Method 3: Using the Python Script

1. **Install dependencies**:
   ```bash
   pip install requests
   ```

2. **Run the script**:
   ```bash
   python upload_salon_data.py
   ```

3. **Enter credentials when prompted**

## Data File Formats

### Employee List CSV
Required columns:
- `PAYROLL LAST NAME`
- `PAYROLL FIRST NAME`
- `PREFERRED FIRST NAME`
- `JOB TITLE`
- `HOME DEPARTMENT`
- `POSITION STATUS`
- `HIRE DATE`
- `REHIRE DATE` (optional)
- `TERMINATION DATE` (optional)

### Performance CSV
Required columns:
- `Location name`
- `Staff Name`
- `Hours Booked`
- `Hours Scheduled`
- `Utilization %`
- `Prebooked %`
- `Self-booked %`
- `Appointment Count`
- `Service Count`
- `Service Sales`
- `Service Sales per Appointment`
- `Tip Sales`
- `New Client Count`
- `Returning Client Count`
- `Gross Sales`
- `Net Sales`

## After Upload

Once data is uploaded successfully, you can:

1. **View Dashboard Metrics**:
   - Total revenue
   - Average utilization
   - Active staff count
   - New clients

2. **Use AI Assistant**:
   - Ask questions like:
     - "What is our current capacity utilization?"
     - "Which stylists have the highest prebooking rates?"
     - "Show me optimal scheduling for location X"
     - "Predict success for new hires"

3. **Access Analytics**:
   - **Performance Trends**: View revenue and utilization over time
   - **Staff Analytics**: Individual performance metrics
   - **Capacity Analysis**: Identify over/understaffing
   - **Predictions**: AI-powered success predictions for staff

## Troubleshooting

### Common Issues

1. **Authentication Failed**:
   - Ensure your credentials are correct
   - Check if your account has the necessary permissions

2. **File Upload Errors**:
   - Verify CSV format matches requirements
   - Check file encoding (should be UTF-8)
   - Ensure no special characters in headers

3. **Data Not Showing**:
   - Refresh the dashboard after upload
   - Check the upload response for any warnings
   - Verify date formats (MM/DD/YYYY expected)

### Support

For additional help:
- Check the API response messages for specific errors
- Contact support with the error details
- Review the upload logs in the response

## API Endpoints Reference

- **Staff Upload**: `POST /api/salon/upload/staff`
- **Performance Upload**: `POST /api/salon/upload/performance`
- **Dashboard Overview**: `GET /api/salon/dashboard/overview`
- **Analytics Query**: `POST /api/salon/analytics/query`

## Best Practices

1. **Upload Order**: Always upload staff data before performance data
2. **Regular Updates**: Upload new performance data monthly
3. **Data Validation**: Review upload results for any warnings
4. **Backup**: Keep original CSV files as backup

## Security Notes

- API tokens expire after 24 hours
- Use HTTPS for all API calls
- Don't share or commit tokens to version control
- Store credentials securely 