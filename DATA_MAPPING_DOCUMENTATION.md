# Salon Analytics Platform - Data Mapping Documentation

## Executive Summary
This document outlines how we process and map salon data from various CSV imports into our analytics platform. We've identified key relationships between different data sources to provide comprehensive insights into salon operations, staff performance, and client behavior.

---

## 1. Data Sources Overview

### Currently Imported Documents

#### 1.1 **Employee List (Staff Master Data)**
- **File**: `employee_list.csv`
- **Purpose**: Core staff directory containing all employee information
- **Key Fields**:
  - `Employee ID` - Unique identifier for each staff member
  - `Full Name` - Staff member's complete name
  - `Job Title` - Role/position in the salon
  - `Location` - Which salon location they work at
  - `Hire Date` - When they started employment
  - `Position Status` - Active/Inactive/On Leave
  - `Email` - Contact information

#### 1.2 **Detailed Line Item Transactions**
- **File**: `detailed_line_item_transactions.csv`
- **Purpose**: Granular transaction-level data for every service and product sale
- **Key Fields**:
  - `Sale ID` - Unique transaction identifier
  - `Sale Date` - When the transaction occurred
  - `Location ID` - Which salon location
  - `Staff ID` - Which staff member performed the service
  - `Client Name` - Customer identifier
  - `Service/Product Name` - What was sold
  - `Sale Type` - Service vs Product classification
  - `Net Sales` - Revenue amount
  - `Net Service Sales` - Service-specific revenue

#### 1.3 **Staff Performance Summary**
- **File**: `staff_performance.csv`
- **Purpose**: Aggregated performance metrics by staff member and period
- **Key Fields**:
  - `Staff ID` - Links to Employee List
  - `Period Date` - Performance measurement period
  - `Location ID` - Performance location
  - `Net Sales` - Total revenue generated
  - `Appointment Count` - Number of appointments
  - `Utilization Percent` - Time efficiency
  - `Prebooked Percent` - Client retention metric
  - `Unique Clients` - Client diversity

#### 1.4 **Time Clock Records**
- **File**: `time_clock.csv`
- **Purpose**: Track actual hours worked by staff
- **Key Fields**:
  - `Staff ID` - Links to Employee List
  - `Clock In/Out Times` - Actual work hours
  - `Date` - Work date
  - `Total Hours` - Hours worked

#### 1.5 **Schedule Records**
- **File**: `schedules.csv`
- **Purpose**: Planned staff schedules
- **Key Fields**:
  - `Staff ID` - Links to Employee List
  - `Scheduled Start/End` - Planned work hours
  - `Date` - Schedule date
  - `Location` - Work location

---

## 2. Data Relationships & Mapping

### 2.1 Primary Key Relationships

```
Employee List (Staff Master)
    ├── Staff ID (Primary Key)
    │
    ├──> Transactions (via Staff ID)
    │    └── Links each sale to performing stylist
    │
    ├──> Staff Performance (via Staff ID)
    │    └── Aggregated metrics per staff member
    │
    ├──> Time Clock (via Staff ID)
    │    └── Actual hours worked
    │
    └──> Schedules (via Staff ID)
         └── Planned work schedule
```

### 2.2 Location Relationships

```
Location (Salon Branches)
    ├── Location ID/Name
    │
    ├──> Employee List (via Location)
    │    └── Staff assigned to location
    │
    ├──> Transactions (via Location ID)
    │    └── Sales at each location
    │
    └──> Staff Performance (via Location ID)
         └── Performance by location
```

### 2.3 Client Relationships

```
Client (from Transactions)
    ├── Client Name (Identifier)
    │
    ├──> Transaction History
    │    ├── Services purchased
    │    ├── Products purchased
    │    ├── Frequency of visits
    │    └── Preferred stylists
    │
    └──> Calculated Metrics
         ├── Total lifetime value
         ├── Visit frequency
         └── Service preferences
```

---

## 3. Data Processing Logic

### 3.1 Transaction Processing
1. **Import**: Raw transaction CSV data
2. **Validation**: Check for valid Staff IDs, Location IDs
3. **Enrichment**: Link to staff names, location names
4. **Aggregation**: Calculate daily/weekly/monthly summaries
5. **Storage**: Store in `salon_transactions` table

### 3.2 Performance Calculation
1. **Revenue Metrics**: Sum net sales by staff/period
2. **Productivity**: Calculate services per hour worked
3. **Client Metrics**: Count unique clients per staff
4. **Efficiency**: Compare actual hours (time clock) vs scheduled hours
5. **Utilization**: Billable hours / Total hours worked

### 3.3 Predictive Analytics
- **New Staff Success**: Analyze first 4-6 weeks performance patterns
- **Client Retention**: Track prebooking rates and return visits
- **Optimal Scheduling**: Compare performance by day/time patterns

---

## 4. Current Analytics Capabilities

Based on the mapped data, we can provide:

### 4.1 Staff Analytics
- Individual performance tracking
- Success prediction for new hires
- Optimal scheduling recommendations
- Top performer identification
- Productivity trends

### 4.2 Client Analytics
- Client segmentation (new/returning/VIP)
- Service preferences
- Visit frequency patterns
- Revenue per client
- Retention analysis

### 4.3 Business Intelligence
- Revenue trends by location/service/staff
- Capacity utilization
- Service mix analysis
- Peak hour identification
- Comparative location performance

---

## 5. Recommended Additional Data Sources

### 5.1 **Critical Missing Data** (High Priority)

#### Client Master File
- **Purpose**: Complete client profiles
- **Needed Fields**:
  - Unique Client ID (currently using names which may have duplicates)
  - Phone/Email for contact
  - First visit date
  - Birthday (for targeted marketing)
  - Preferred services/products
  - Client source (walk-in, referral, online)

#### Appointment Book Data
- **Purpose**: Understand booking patterns and no-shows
- **Needed Fields**:
  - Appointment ID
  - Booking date/time vs actual service date/time
  - Service requested vs service delivered
  - No-show/cancellation data
  - Online vs phone vs walk-in bookings
  - Wait list data

#### Product Inventory
- **Purpose**: Track retail performance and inventory turns
- **Needed Fields**:
  - Product SKUs
  - Cost of goods sold
  - Current inventory levels
  - Reorder points
  - Supplier information

### 5.2 **Enhanced Analytics Data** (Medium Priority)

#### Marketing Campaign Data
- **Purpose**: ROI on marketing efforts
- **Needed Fields**:
  - Campaign dates and types
  - Promotional codes used
  - New client acquisition source
  - Campaign costs
  - Response rates

#### Staff Training/Certification Records
- **Purpose**: Correlate skills with performance
- **Needed Fields**:
  - Certifications held
  - Training completed
  - Specializations
  - Years of experience
  - Education level

#### Client Feedback/Reviews
- **Purpose**: Quality metrics beyond revenue
- **Needed Fields**:
  - Service ratings
  - Staff ratings
  - NPS scores
  - Review text
  - Complaint/compliment data

### 5.3 **Advanced Insights Data** (Future Enhancement)

#### Point of Sale (POS) Details
- **Purpose**: Complete transaction context
- **Needed Fields**:
  - Payment methods
  - Tips data
  - Discounts applied
  - Transaction time (start/end)
  - Service add-ons

#### Chemical Service Records
- **Purpose**: Track color formulas and chemical usage
- **Needed Fields**:
  - Color formulas used
  - Chemical costs
  - Processing times
  - Allergy information
  - Retouch schedules

#### Competitive Intelligence
- **Purpose**: Market positioning
- **Needed Fields**:
  - Competitor pricing
  - Market service rates
  - Industry benchmarks
  - Local demographic data

---

## 6. Data Quality Observations

### Current Strengths
- Transaction data is comprehensive with good date coverage
- Staff IDs are consistent across files
- Revenue data appears complete

### Areas for Improvement
1. **Client Identification**: Using names may cause duplicate client issues
2. **Service Standardization**: Service names should be standardized (e.g., "Haircut" vs "Hair Cut")
3. **Missing Values**: Some transactions lack client names
4. **Time Zone**: Ensure all dates/times are in consistent timezone
5. **Historical Data**: Would benefit from 12+ months of historical data for seasonality analysis

---

## 7. Implementation Recommendations

### Immediate Actions
1. Implement unique client ID system
2. Standardize service/product naming conventions
3. Add appointment booking data import
4. Include client contact information

### Short-term (1-3 months)
1. Integrate marketing campaign tracking
2. Add inventory management data
3. Implement client feedback collection
4. Enhance staff profile data

### Long-term (3-6 months)
1. Real-time POS integration
2. Automated competitive intelligence
3. Predictive inventory management
4. Advanced client lifetime value modeling

---

## 8. Expected Outcomes

With the recommended additional data, the platform will be able to:

1. **Predict Client Behavior**
   - When clients are likely to return
   - Risk of client churn
   - Upsell opportunities

2. **Optimize Operations**
   - Ideal staff-to-demand ratios
   - Inventory optimization
   - Service pricing optimization

3. **Enhance Marketing**
   - Targeted campaign effectiveness
   - ROI on promotional activities
   - Client acquisition cost analysis

4. **Improve Staff Management**
   - Better success prediction
   - Training need identification
   - Performance-based scheduling

5. **Strategic Planning**
   - Market expansion opportunities
   - Service mix optimization
   - Competitive positioning

---

## Contact & Questions

For any questions about this data mapping or to discuss additional data integration:
- Platform Team: [Your Contact]
- Technical Lead: [Your Contact]
- Data Questions: [Your Email]

*Document Version: 1.0*  
*Last Updated: January 2025* 