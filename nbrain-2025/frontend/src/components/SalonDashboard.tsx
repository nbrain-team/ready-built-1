import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  AreaChart, Area, ComposedChart
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { 
  TrendingUp, Users, DollarSign, ShoppingCart, Clock, 
  Calendar, Search, Download, Filter, ChevronDown,
  Activity, UserCheck, Package, Star, Target, AlertCircle, Sparkles, LogOut
} from 'lucide-react';
import { salonApi } from '@/services/salonApi';
import SalonAIChat from './SalonAIChat';

const SalonDashboard = () => {
  const navigate = useNavigate();
  // State management
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedMetric, setSelectedMetric] = useState('revenue');
  const [dateRangeLabel, setDateRangeLabel] = useState('January 2025');
  const [showAIPanel, setShowAIPanel] = useState(false);
  const [startDate, setStartDate] = useState('2025-01-01');
  const [endDate, setEndDate] = useState('2025-01-31');
  
  // Data states with proper types
  interface DashboardData {
    overview: {
      totalRevenue: number;
      totalTransactions: number;
      uniqueClients: number;
      averageTicket: number;
      totalServices: number;
      totalProducts: number;
    };
    trends: Array<{
      date: string;
      revenue: number;
      transaction_count: number;
      unique_clients: number;
      average_ticket: number;
      service_count: number;
      product_count: number;
    }>;
    topPerformers: Array<{
      staff_id: number;
      staff_name: string;
      location: string;
      net_sales: number;
      transactions: number;
      unique_clients: number;
      avg_ticket: number;
    }>;
    serviceBreakdown: Array<{
      service_name: string;
      count: number;
      revenue: number;
      avg_price: number;
    }>;
    clientInsights: {
      total_clients: number;
      new_clients: number;
      returning_clients: number;
      vip_clients: number;
      avg_client_value: number;
    };
    transactions: Array<any>;
  }

  const [dashboardData, setDashboardData] = useState<DashboardData>({
    overview: {
      totalRevenue: 0,
      totalTransactions: 0,
      uniqueClients: 0,
      averageTicket: 0,
      totalServices: 0,
      totalProducts: 0
    },
    trends: [],
    topPerformers: [],
    serviceBreakdown: [],
    clientInsights: {
      total_clients: 0,
      new_clients: 0,
      returning_clients: 0,
      vip_clients: 0,
      avg_client_value: 0
    },
    transactions: []
  });

  const [searchTerm, setSearchTerm] = useState('');

  // Quick date range buttons
  const setDateRange = (days: number, label: string) => {
    const end = new Date();
    const start = new Date();
    
    if (days === -1) { // This month
      start.setDate(1);
    } else if (days === -2) { // Last month
      start.setMonth(start.getMonth() - 1);
      start.setDate(1);
      end.setDate(0); // Last day of previous month
    } else {
      start.setDate(start.getDate() - days);
    }
    
    setStartDate(start.toISOString().split('T')[0]);
    setEndDate(end.toISOString().split('T')[0]);
    setDateRangeLabel(label);
  };

  // Fetch data with date range
  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      
      const [overview, trends, topPerformers, serviceBreakdown, clientInsights] = await Promise.all([
        salonApi.getDashboardOverview(startDate, endDate),
        salonApi.getPerformanceTrends(startDate, endDate),
        salonApi.getTopPerformers('sales'),
        salonApi.getServiceBreakdown(),
        salonApi.getClientInsights()
      ]);

      console.log('API Response Overview:', overview); // Debug log

      // Map the API response to the expected format
      const mappedOverview = {
        totalRevenue: overview.total_revenue || 0,
        totalTransactions: overview.total_transactions || 0,
        uniqueClients: overview.unique_clients || 0,
        averageTicket: overview.avg_ticket || 0,
        totalServices: overview.service_sales || 0,
        totalProducts: overview.product_sales || 0
      };

      // Map trends data if it exists
      const mappedTrends = (trends || []).map((trend: any) => ({
        date: trend.period || trend.date,
        revenue: trend.total_sales || trend.revenue || 0,
        transaction_count: trend.transaction_count || 0,
        unique_clients: trend.unique_clients || 0,
        average_ticket: trend.total_sales && trend.transaction_count 
          ? trend.total_sales / trend.transaction_count 
          : 0,
        service_count: trend.service_sales || 0,
        product_count: trend.product_sales || 0
      }));

      setDashboardData({
        overview: mappedOverview,
        trends: mappedTrends,
        topPerformers: topPerformers || [],
        serviceBreakdown: serviceBreakdown || [],
        clientInsights: clientInsights || {
          total_clients: 0,
          new_clients: 0,
          returning_clients: 0,
          vip_clients: 0,
          avg_client_value: 0
        },
        transactions: []
      });
      
      setError(null);
    } catch (err) {
      console.error('Error fetching dashboard data:', err);
      setError('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  // Fetch data when date range changes
  useEffect(() => {
    fetchDashboardData();
  }, [startDate, endDate]);

  // Get chart data based on selected metric
  const getChartData = () => {
    if (!dashboardData.trends || dashboardData.trends.length === 0) {
      return [];
    }

    return dashboardData.trends.map(day => ({
      date: new Date(day.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      value: selectedMetric === 'revenue' ? day.revenue :
             selectedMetric === 'transactions' ? day.transaction_count :
             selectedMetric === 'clients' ? day.unique_clients :
             selectedMetric === 'ticket' ? day.average_ticket :
             selectedMetric === 'services' ? day.service_count :
             day.product_count || 0
    }));
  };

  // Helper functions
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', { 
      style: 'currency', 
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value || 0);
  };

  // Custom tooltip formatter for charts
  const customTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 border rounded shadow-lg">
          <p className="font-semibold">{label}</p>
          {payload.map((entry: any, index: number) => {
            const value = entry.name.toLowerCase().includes('revenue') || 
                         entry.name.toLowerCase().includes('sales') ||
                         entry.name.toLowerCase().includes('ticket') ||
                         entry.dataKey === 'revenue' ||
                         entry.dataKey === 'value' && (selectedMetric === 'revenue' || selectedMetric === 'ticket')
                         ? formatCurrency(entry.value)
                         : entry.value?.toLocaleString() || 0;
            return (
              <p key={index} style={{ color: entry.color }}>
                {entry.name}: {value}
              </p>
            );
          })}
        </div>
      );
    }
    return null;
  };

  // Format Y-axis for currency
  const formatYAxis = (value: number) => {
    if (selectedMetric === 'revenue' || selectedMetric === 'ticket') {
      // For large numbers, show abbreviated format
      if (value >= 1000000) {
        return `$${(value / 1000000).toFixed(1)}M`;
      } else if (value >= 1000) {
        return `$${(value / 1000).toFixed(0)}K`;
      }
      return formatCurrency(value);
    }
    return value.toLocaleString();
  };

  // Metric card configuration
  const metricCards = [
    {
      id: 'revenue',
      title: 'Total Revenue',
      value: formatCurrency(dashboardData.overview.totalRevenue || 0),
      icon: DollarSign,
      color: 'text-green-600',
      bgColor: 'bg-green-50'
    },
    {
      id: 'transactions',
      title: 'Transactions',
      value: (dashboardData.overview.totalTransactions || 0).toLocaleString(),
      icon: ShoppingCart,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50'
    },
    {
      id: 'clients',
      title: 'Unique Clients',
      value: (dashboardData.overview.uniqueClients || 0).toLocaleString(),
      icon: Users,
      color: 'text-purple-600',
      bgColor: 'bg-purple-50'
    },
    {
      id: 'ticket',
      title: 'Average Ticket',
      value: formatCurrency(dashboardData.overview.averageTicket || 0),
      icon: TrendingUp,
      color: 'text-orange-600',
      bgColor: 'bg-orange-50'
    },
    {
      id: 'services',
      title: 'Service Sales',
      value: formatCurrency(dashboardData.overview.totalServices || 0),
      icon: Activity,
      color: 'text-indigo-600',
      bgColor: 'bg-indigo-50'
    },
    {
      id: 'products',
      title: 'Product Sales',
      value: formatCurrency(dashboardData.overview.totalProducts || 0),
      icon: Package,
      color: 'text-pink-600',
      bgColor: 'bg-pink-50'
    }
  ];

  const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff7c7c', '#8dd1e1', '#d084d0', '#ffb347', '#87ceeb'];

  const handleLogout = () => {
    sessionStorage.removeItem('salonAuth');
    sessionStorage.removeItem('salonUser');
    navigate('/salon-login');
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading dashboard data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 relative">
      {/* Floating AI Assistant Button */}
      <Button
        onClick={() => setShowAIPanel(true)}
        className="fixed bottom-6 right-6 z-40 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white shadow-lg rounded-full p-4 hover:scale-110 transition-transform"
      >
        <Sparkles className="h-5 w-5 mr-2" />
        AI Assistant
      </Button>

      {/* AI Assistant Slide-out Panel */}
      {showAIPanel && (
        <>
          {/* Backdrop */}
          <div 
            className="fixed inset-0 bg-black bg-opacity-50 z-40"
            onClick={() => setShowAIPanel(false)}
          />
          
          {/* Panel */}
          <div className={`fixed top-0 right-0 h-full w-full md:w-2/3 lg:w-1/2 bg-white shadow-2xl z-50 transform transition-transform duration-300 ${
            showAIPanel ? 'translate-x-0' : 'translate-x-full'
          }`}>
            <div className="h-full flex flex-col">
              {/* Panel Header */}
              <div className="flex items-center justify-between p-4 border-b bg-gradient-to-r from-purple-600 to-pink-600 text-white">
                <div className="flex items-center">
                  <Sparkles className="h-6 w-6 mr-2" />
                  <h2 className="text-xl font-bold">AI Analytics Assistant</h2>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowAIPanel(false)}
                  className="text-white hover:bg-white/20"
                >
                  ✕
                </Button>
              </div>
              
              {/* Chat Component */}
              <div className="flex-1 overflow-hidden">
                <SalonAIChat />
              </div>
            </div>
          </div>
        </>
      )}

      {/* Header with Date Range Selector */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Salon Analytics Dashboard</h1>
          <p className="text-gray-600 mt-1">Real-time insights into your salon performance</p>
        </div>
        
        {/* Date Range Selector and Logout */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Calendar className="h-5 w-5 text-gray-500" />
            <div className="flex gap-2">
              <Button 
                variant="outline" 
                size="sm"
                onClick={() => {
                  setStartDate('2025-01-01');
                  setEndDate('2025-01-31');
                  setDateRangeLabel('January 2025');
                }}
                className={dateRangeLabel === 'January 2025' ? 'bg-blue-100' : ''}
              >
                January 2025
              </Button>
              <Button 
                variant="outline" 
                size="sm"
                onClick={() => setDateRange(0, 'Today')}
              >
                Today
              </Button>
              <Button 
                variant="outline" 
                size="sm"
                onClick={() => setDateRange(7, 'Last 7 days')}
              >
                7 days
              </Button>
              <Button 
                variant="outline" 
                size="sm"
                onClick={() => setDateRange(30, 'Last 30 days')}
              >
                30 days
              </Button>
              <Button 
                variant="outline" 
                size="sm"
                onClick={() => setDateRange(-1, 'This month')}
              >
                This month
              </Button>
            </div>
            <div className="flex gap-2 ml-4">
              <Input
                type="date"
                value={startDate}
                onChange={(e) => {
                  setStartDate(e.target.value);
                  setDateRangeLabel('Custom');
                }}
                className="w-[140px]"
              />
              <span className="self-center">to</span>
              <Input
                type="date"
                value={endDate}
                onChange={(e) => {
                  setEndDate(e.target.value);
                  setDateRangeLabel('Custom');
                }}
                className="w-[140px]"
              />
            </div>
          </div>
          
          {/* Logout Button */}
          <Button
            variant="outline"
            size="sm"
            onClick={handleLogout}
            className="flex items-center gap-2"
          >
            <LogOut className="h-4 w-4" />
            Logout
          </Button>
        </div>
      </div>

      {error && (
        <Alert className="bg-red-50 border-red-200">
          <AlertCircle className="h-4 w-4 text-red-600" />
          <AlertDescription className="text-red-800">{error}</AlertDescription>
        </Alert>
      )}

      {/* Clickable Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        {metricCards.map((metric) => {
          const Icon = metric.icon;
          const isSelected = selectedMetric === metric.id;
          
          return (
            <div 
              key={metric.id}
              onClick={() => setSelectedMetric(metric.id)}
              className={`cursor-pointer transition-all transform hover:scale-105 ${
                isSelected ? 'ring-2 ring-offset-2 ring-blue-500' : ''
              }`}
            >
              <Card className={metric.bgColor}>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <Icon className={`h-8 w-8 ${metric.color}`} />
                    {isSelected && (
                      <Badge className="bg-blue-500 text-white">Selected</Badge>
                    )}
                  </div>
                  <p className="text-2xl font-bold mt-2">{metric.value}</p>
                  <p className="text-sm text-gray-600">{metric.title}</p>
                </CardContent>
              </Card>
            </div>
          );
        })}
      </div>

      {/* Dynamic Chart based on selected metric */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>
              {metricCards.find(m => m.id === selectedMetric)?.title} Trend
            </span>
            <Badge variant="outline">
              {dateRangeLabel}
            </Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={getChartData()}>
              <defs>
                <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.8}/>
                  <stop offset="95%" stopColor="#3B82F6" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis tickFormatter={formatYAxis} />
              <Tooltip content={customTooltip} />
              <Area 
                type="monotone" 
                dataKey="value" 
                stroke="#3B82F6" 
                fillOpacity={1} 
                fill="url(#colorValue)" 
              />
            </AreaChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Rest of the dashboard tabs */}
      <Tabs defaultValue="performance">
        <div className="w-full overflow-x-auto mb-4 border-b">
          <TabsList>
            <TabsTrigger value="performance">Performance</TabsTrigger>
            <TabsTrigger value="staff">Staff</TabsTrigger>
            <TabsTrigger value="services">Services</TabsTrigger>
            <TabsTrigger value="clients">Clients</TabsTrigger>
            <TabsTrigger value="transactions">Transactions</TabsTrigger>
            <TabsTrigger value="analytics">Analytics</TabsTrigger>
            <TabsTrigger value="ai-assistant">
              <Sparkles className="w-4 h-4 mr-2" />
              AI Assistant
            </TabsTrigger>
          </TabsList>
        </div>

        <TabsContent value="performance" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Daily Performance Trends</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <ComposedChart data={dashboardData.trends}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="date" 
                    tickFormatter={(value) => new Date(value).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                  />
                  <YAxis yAxisId="left" />
                  <YAxis yAxisId="right" orientation="right" tickFormatter={(value) => formatCurrency(value)} />
                  <Tooltip content={customTooltip} />
                  <Legend />
                  <Bar yAxisId="left" dataKey="transaction_count" fill="#8884d8" name="Transactions" />
                  <Line yAxisId="right" type="monotone" dataKey="revenue" stroke="#82ca9d" name="Revenue" />
                </ComposedChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="staff" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Top Performing Staff</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Staff Name</TableHead>
                    <TableHead>Location</TableHead>
                    <TableHead>Sales</TableHead>
                    <TableHead>Transactions</TableHead>
                    <TableHead>Clients</TableHead>
                    <TableHead>Avg Ticket</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {dashboardData.topPerformers.map((performer) => (
                    <TableRow key={performer.staff_id}>
                      <TableCell className="font-medium">{performer.staff_name}</TableCell>
                      <TableCell>{performer.location}</TableCell>
                      <TableCell>{formatCurrency(performer.net_sales)}</TableCell>
                      <TableCell>{performer.transactions}</TableCell>
                      <TableCell>{performer.unique_clients}</TableCell>
                      <TableCell>{formatCurrency(performer.avg_ticket)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="services" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Service Revenue Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={dashboardData.serviceBreakdown.slice(0, 8)}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      outerRadius={100}
                      fill="#8884d8"
                      dataKey="revenue"
                      label={(entry) => formatCurrency(entry.revenue)}
                    >
                      {dashboardData.serviceBreakdown.slice(0, 8).map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip content={customTooltip} />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Top Services</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {dashboardData.serviceBreakdown.slice(0, 10).map((service, index) => (
                    <div key={index} className="flex justify-between items-center p-2 rounded-lg bg-gray-50">
                      <div className="flex-1">
                        <p className="font-medium text-sm">{service.service_name}</p>
                        <p className="text-xs text-gray-500">{service.count} services</p>
                      </div>
                      <div className="text-right">
                        <p className="font-bold text-sm">{formatCurrency(service.revenue)}</p>
                        <p className="text-xs text-gray-500">Avg: {formatCurrency(service.avg_price)}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="clients" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Client Insights</CardTitle>
            </CardHeader>
            <CardContent>
              {dashboardData.clientInsights && (
                <div className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="p-4 rounded-lg bg-blue-50">
                      <p className="text-sm font-medium text-blue-900">Total Clients</p>
                      <p className="text-2xl font-bold text-blue-900">{dashboardData.clientInsights.total_clients?.toLocaleString()}</p>
                    </div>
                    <div className="p-4 rounded-lg bg-green-50">
                      <p className="text-sm font-medium text-green-900">New Clients</p>
                      <p className="text-2xl font-bold text-green-900">{dashboardData.clientInsights.new_clients?.toLocaleString()}</p>
                      <p className="text-xs text-green-700">
                        {dashboardData.clientInsights.total_clients > 0 
                          ? `${((dashboardData.clientInsights.new_clients / dashboardData.clientInsights.total_clients) * 100).toFixed(1)}% of total`
                          : '0% of total'}
                      </p>
                    </div>
                    <div className="p-4 rounded-lg bg-purple-50">
                      <p className="text-sm font-medium text-purple-900">VIP Clients (5+ visits)</p>
                      <p className="text-2xl font-bold text-purple-900">{dashboardData.clientInsights.vip_clients?.toLocaleString()}</p>
                      <p className="text-xs text-purple-700">
                        {dashboardData.clientInsights.total_clients > 0
                          ? `${((dashboardData.clientInsights.vip_clients / dashboardData.clientInsights.total_clients) * 100).toFixed(1)}% of total`
                          : '0% of total'}
                      </p>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="p-4 rounded-lg border">
                      <p className="text-sm font-medium">Average Client Value</p>
                      <p className="text-2xl font-bold">{formatCurrency(dashboardData.clientInsights.avg_client_value)}</p>
                    </div>
                    <div className="p-4 rounded-lg border">
                      <p className="text-sm font-medium">Returning Clients</p>
                      <p className="text-2xl font-bold">{dashboardData.clientInsights.returning_clients?.toLocaleString()}</p>
                      <p className="text-xs text-muted-foreground">
                        {dashboardData.clientInsights.total_clients > 0
                          ? `${((dashboardData.clientInsights.returning_clients / dashboardData.clientInsights.total_clients) * 100).toFixed(1)}% retention rate`
                          : '0% retention rate'}
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="transactions" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Transaction Search</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex gap-4 mb-4">
                <Input
                  placeholder="Search by client, service, or ID..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-[300px]"
                />
                <Button onClick={() => {/* TODO: Implement search */}}>
                  <Search className="h-4 w-4 mr-2" />
                  Search
                </Button>
              </div>
              
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Date</TableHead>
                    <TableHead>Client</TableHead>
                    <TableHead>Service</TableHead>
                    <TableHead>Staff</TableHead>
                    <TableHead>Location</TableHead>
                    <TableHead>Amount</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {dashboardData.transactions.map((transaction: any) => (
                    <TableRow key={transaction.id}>
                      <TableCell>{new Date(transaction.sale_date).toLocaleDateString()}</TableCell>
                      <TableCell>{transaction.client_name}</TableCell>
                      <TableCell>{transaction.service_name}</TableCell>
                      <TableCell>{transaction.staff_name}</TableCell>
                      <TableCell>{transaction.location}</TableCell>
                      <TableCell>{formatCurrency(transaction.net_sales)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="analytics" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Revenue Trend</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={dashboardData.trends}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="date" 
                      tickFormatter={(value) => new Date(value).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                    />
                    <YAxis tickFormatter={(value) => formatCurrency(value)} />
                    <Tooltip content={customTooltip} />
                    <Area type="monotone" dataKey="revenue" stroke="#8884d8" fill="#8884d8" />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Transaction Volume</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={dashboardData.trends}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="date" 
                      tickFormatter={(value) => new Date(value).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                    />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="transaction_count" fill="#82ca9d" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="ai-assistant" className="h-[600px]">
          <SalonAIChat />
        </TabsContent>
      </Tabs>

      {/* Chat Assistant */}
      {/* The SalonChat component was removed from imports, so this block will be removed */}
    </div>
  );
};

export default SalonDashboard; 