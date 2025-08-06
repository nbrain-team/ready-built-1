import React, { useState, useEffect } from 'react';
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  AreaChart, Area, ComposedChart
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { 
  TrendingUp, Users, DollarSign, ShoppingCart, Clock, 
  Calendar, Search, Download, Filter, ChevronDown,
  Activity, UserCheck, Package, Star, Target, AlertCircle
} from 'lucide-react';
import { salonApi } from '@/services/salonApi';
import SalonChat from './SalonChat';

// Date range presets
const DATE_RANGES = {
  'today': { label: 'Today', days: 0 },
  'yesterday': { label: 'Yesterday', days: 1 },
  'last7': { label: 'Last 7 days', days: 7 },
  'last30': { label: 'Last 30 days', days: 30 },
  'thisMonth': { label: 'This month', days: -1 },
  'lastMonth': { label: 'Last month', days: -2 },
  'custom': { label: 'Custom range', days: 0 }
};

const SalonDashboard = () => {
  // State management
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedMetric, setSelectedMetric] = useState('revenue'); // For clickable cards
  const [dateRange, setDateRange] = useState('last30');
  const [customStartDate, setCustomStartDate] = useState('');
  const [customEndDate, setCustomEndDate] = useState('');
  const [showDatePicker, setShowDatePicker] = useState(false);
  
  // Data states with proper types
  const [dashboardData, setDashboardData] = useState<{
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
      total_clients?: number;
      new_clients?: number;
      returning_clients?: number;
      vip_clients?: number;
      avg_client_value?: number;
    };
    transactions: Array<{
      id: number;
      sale_id: string;
      sale_date: string;
      location: string;
      staff_name: string;
      client_name: string;
      service_name: string;
      sale_type: string;
      net_service_sales: number;
      net_sales: number;
    }>;
  }>({
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
    clientInsights: {},
    transactions: []
  });

  const [filters, setFilters] = useState({
    location: '',
    staff: '',
    service: '',
    search: ''
  });

  // Calculate date range
  const getDateRange = () => {
    let endDate = new Date();
    let startDate = new Date();
    
    if (dateRange === 'custom') {
      return {
        start: customStartDate || new Date().toISOString().split('T')[0],
        end: customEndDate || new Date().toISOString().split('T')[0]
      };
    }
    
    const preset = DATE_RANGES[dateRange as keyof typeof DATE_RANGES];
    if (preset.days === 0) { // Today
      startDate = new Date();
    } else if (preset.days === 1) { // Yesterday
      startDate.setDate(startDate.getDate() - 1);
      endDate.setDate(endDate.getDate() - 1);
    } else if (preset.days === -1) { // This month
      startDate.setDate(1);
    } else if (preset.days === -2) { // Last month
      startDate = new Date(endDate.getFullYear(), endDate.getMonth() - 1, 1);
      endDate = new Date(endDate.getFullYear(), endDate.getMonth(), 0);
    } else {
      startDate.setDate(startDate.getDate() - preset.days);
    }
    
    return {
      start: startDate.toISOString().split('T')[0],
      end: endDate.toISOString().split('T')[0]
    };
  };

  // Fetch data with date range
  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const { start, end } = getDateRange();
      
      const [overview, trends, topPerformers, serviceBreakdown, clientInsights] = await Promise.all([
        salonApi.getDashboardOverview(start, end),
        salonApi.getPerformanceTrends(start, end),
        salonApi.getTopPerformers('sales'),
        salonApi.getServiceBreakdown(),
        salonApi.getClientInsights()
      ]);

      setDashboardData({
        overview: overview.data || overview,
        trends: trends.data || trends,
        topPerformers: topPerformers.data || topPerformers,
        serviceBreakdown: serviceBreakdown.data || serviceBreakdown,
        clientInsights: clientInsights.data || clientInsights,
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
  }, [dateRange, customStartDate, customEndDate]);

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
             day.product_count,
      label: selectedMetric === 'revenue' ? `$${(day.revenue || 0).toLocaleString()}` :
             selectedMetric === 'ticket' ? `$${(day.average_ticket || 0).toFixed(2)}` :
             (day[selectedMetric === 'transactions' ? 'transaction_count' :
                  selectedMetric === 'clients' ? 'unique_clients' :
                  selectedMetric === 'services' ? 'service_count' :
                  'product_count'] || 0).toLocaleString()
    }));
  };

  // Metric card configuration
  const metricCards = [
    {
      id: 'revenue',
      title: 'Total Revenue',
      value: `$${(dashboardData.overview.totalRevenue || 0).toLocaleString()}`,
      icon: DollarSign,
      color: 'text-green-600',
      bgColor: 'bg-green-50 hover:bg-green-100',
      description: 'Total sales revenue'
    },
    {
      id: 'transactions',
      title: 'Transactions',
      value: (dashboardData.overview.totalTransactions || 0).toLocaleString(),
      icon: ShoppingCart,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50 hover:bg-blue-100',
      description: 'Total number of transactions'
    },
    {
      id: 'clients',
      title: 'Unique Clients',
      value: (dashboardData.overview.uniqueClients || 0).toLocaleString(),
      icon: Users,
      color: 'text-purple-600',
      bgColor: 'bg-purple-50 hover:bg-purple-100',
      description: 'Individual customers served'
    },
    {
      id: 'ticket',
      title: 'Average Ticket',
      value: `$${(dashboardData.overview.averageTicket || 0).toFixed(2)}`,
      icon: TrendingUp,
      color: 'text-orange-600',
      bgColor: 'bg-orange-50 hover:bg-orange-100',
      description: 'Average transaction value'
    },
    {
      id: 'services',
      title: 'Services Sold',
      value: (dashboardData.overview.totalServices || 0).toLocaleString(),
      icon: Activity,
      color: 'text-indigo-600',
      bgColor: 'bg-indigo-50 hover:bg-indigo-100',
      description: 'Total services performed'
    },
    {
      id: 'products',
      title: 'Products Sold',
      value: (dashboardData.overview.totalProducts || 0).toLocaleString(),
      icon: Package,
      color: 'text-pink-600',
      bgColor: 'bg-pink-50 hover:bg-pink-100',
      description: 'Total products sold'
    }
  ];

  // Helper functions
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', { 
      style: 'currency', 
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff7c7c', '#8dd1e1', '#d084d0', '#ffb347', '#87ceeb'];

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
    <div className="p-6 space-y-6">
      {/* Header with Date Range Selector */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Salon Analytics Dashboard</h1>
          <p className="text-gray-600 mt-1">Real-time insights into your salon performance</p>
        </div>
        
        {/* Date Range Selector */}
        <div className="flex items-center gap-2">
          <Calendar className="h-5 w-5 text-gray-500" />
          <Select value={dateRange} onValueChange={setDateRange}>
            <SelectTrigger className="w-[180px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {Object.entries(DATE_RANGES).map(([key, value]) => (
                <SelectItem key={key} value={key}>
                  {value.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          
          {dateRange === 'custom' && (
            <div className="flex gap-2">
              <Input
                type="date"
                value={customStartDate}
                onChange={(e) => setCustomStartDate(e.target.value)}
                className="w-[140px]"
              />
              <span className="self-center">to</span>
              <Input
                type="date"
                value={customEndDate}
                onChange={(e) => setCustomEndDate(e.target.value)}
                className="w-[140px]"
              />
            </div>
          )}
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
            <Card 
              key={metric.id}
              className={`cursor-pointer transition-all transform hover:scale-105 ${metric.bgColor} ${
                isSelected ? 'ring-2 ring-offset-2 ring-blue-500' : ''
              }`}
              onClick={() => setSelectedMetric(metric.id)}
            >
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <Icon className={`h-8 w-8 ${metric.color}`} />
                  {isSelected && (
                    <Badge className="bg-blue-500 text-white">Selected</Badge>
                  )}
                </div>
                <p className="text-2xl font-bold mt-2">{metric.value}</p>
                <p className="text-sm text-gray-600">{metric.title}</p>
                <p className="text-xs text-gray-500 mt-1">{metric.description}</p>
              </CardContent>
            </Card>
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
              {DATE_RANGES[dateRange]?.label || 'Custom Range'}
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
              <YAxis />
              <Tooltip 
                content={({ active, payload }) => {
                  if (active && payload && payload[0]) {
                    return (
                      <div className="bg-white p-2 border rounded shadow">
                        <p className="font-semibold">{payload[0].payload.date}</p>
                        <p className="text-blue-600">{payload[0].payload.label}</p>
                      </div>
                    );
                  }
                  return null;
                }}
              />
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
      <Tabs defaultValue="performance" className="space-y-4">
        <TabsList className="grid w-full grid-cols-6">
          <TabsTrigger value="performance">Performance</TabsTrigger>
          <TabsTrigger value="staff">Staff</TabsTrigger>
          <TabsTrigger value="services">Services</TabsTrigger>
          <TabsTrigger value="clients">Clients</TabsTrigger>
          <TabsTrigger value="transactions">Transactions</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
        </TabsList>

        <TabsContent value="performance" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>January 2025 Daily Performance</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <ComposedChart data={dashboardData.trends}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="period" 
                    tickFormatter={(value) => new Date(value).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                  />
                  <YAxis yAxisId="left" orientation="left" stroke="#8884d8" />
                  <YAxis yAxisId="right" orientation="right" stroke="#82ca9d" />
                  <Tooltip 
                    formatter={(value: any, name: string) => {
                      if (name.includes('Revenue') || name.includes('Sales')) return formatCurrency(value);
                      return value.toLocaleString();
                    }}
                  />
                  <Legend />
                  <Bar yAxisId="left" dataKey="transaction_count" fill="#8884d8" name="Transactions" />
                  <Line yAxisId="right" type="monotone" dataKey="total_sales" stroke="#82ca9d" name="Revenue" strokeWidth={2} />
                  <Line yAxisId="left" type="monotone" dataKey="unique_clients" stroke="#ffc658" name="Unique Clients" strokeWidth={2} />
                </ComposedChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="staff" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex justify-between items-center">
                <CardTitle>Top Performing Staff</CardTitle>
                <Select value={selectedMetric} onValueChange={setSelectedMetric}>
                  <SelectTrigger className="w-[180px]">
                    <SelectValue placeholder="Select metric" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="sales">Revenue</SelectItem>
                    <SelectItem value="transactions">Transactions</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Staff Name</TableHead>
                    <TableHead>Location</TableHead>
                    <TableHead className="text-right">Revenue</TableHead>
                    <TableHead className="text-right">Transactions</TableHead>
                    <TableHead className="text-right">Clients</TableHead>
                    <TableHead className="text-right">Avg Ticket</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {dashboardData.topPerformers.map((performer) => (
                    <TableRow key={performer.staff_id}>
                      <TableCell className="font-medium">{performer.staff_name}</TableCell>
                      <TableCell>{performer.location}</TableCell>
                      <TableCell className="text-right">{formatCurrency(performer.net_sales)}</TableCell>
                      <TableCell className="text-right">{performer.transactions}</TableCell>
                      <TableCell className="text-right">{performer.unique_clients}</TableCell>
                      <TableCell className="text-right">{formatCurrency(performer.avg_ticket)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="services" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Service Performance Breakdown</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div>
                  <h3 className="text-sm font-medium mb-4">Revenue by Service</h3>
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={dashboardData.serviceBreakdown.slice(0, 8)}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={(entry) => `${entry.service_name.substring(0, 15)}...`}
                        outerRadius={80}
                        fill="#8884d8"
                        dataKey="revenue"
                      >
                        {dashboardData.serviceBreakdown.slice(0, 8).map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip formatter={(value) => formatCurrency(value as number)} />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
                <div>
                  <h3 className="text-sm font-medium mb-4">Top Services</h3>
                  <div className="space-y-2">
                    {dashboardData.serviceBreakdown.slice(0, 10).map((service, index) => (
                      <div key={index} className="flex justify-between items-center p-2 rounded-lg bg-gray-50">
                        <div className="flex-1">
                          <p className="text-sm font-medium">{service.service_name}</p>
                          <p className="text-xs text-muted-foreground">{service.count} services</p>
                        </div>
                        <div className="text-right">
                          <p className="text-sm font-bold">{formatCurrency(service.revenue)}</p>
                          <p className="text-xs text-muted-foreground">Avg: {formatCurrency(service.avg_price)}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="clients" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Client Analytics</CardTitle>
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
                      <p className="text-xs text-green-700">{((dashboardData.clientInsights.new_clients / dashboardData.clientInsights.total_clients) * 100).toFixed(1)}% of total</p>
                    </div>
                    <div className="p-4 rounded-lg bg-purple-50">
                      <p className="text-sm font-medium text-purple-900">VIP Clients (5+ visits)</p>
                      <p className="text-2xl font-bold text-purple-900">{dashboardData.clientInsights.vip_clients?.toLocaleString()}</p>
                      <p className="text-xs text-purple-700">{((dashboardData.clientInsights.vip_clients / dashboardData.clientInsights.total_clients) * 100).toFixed(1)}% of total</p>
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
                      <p className="text-xs text-muted-foreground">{((dashboardData.clientInsights.returning_clients / dashboardData.clientInsights.total_clients) * 100).toFixed(1)}% retention rate</p>
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
              <div className="flex justify-between items-center">
                <CardTitle>Transaction Search</CardTitle>
                <div className="flex gap-2">
                  <Input
                    placeholder="Search by client, service, or ID..."
                    value={filters.search}
                    onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
                    className="w-[300px]"
                  />
                  <Button onClick={searchTransactions}>
                    <Search className="h-4 w-4 mr-2" />
                    Search
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Date</TableHead>
                    <TableHead>Sale ID</TableHead>
                    <TableHead>Client</TableHead>
                    <TableHead>Service</TableHead>
                    <TableHead>Staff</TableHead>
                    <TableHead>Location</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead className="text-right">Amount</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {dashboardData.transactions.map((transaction) => (
                    <TableRow key={transaction.id}>
                      <TableCell>{new Date(transaction.sale_date).toLocaleDateString()}</TableCell>
                      <TableCell className="font-mono text-xs">{transaction.sale_id}</TableCell>
                      <TableCell>{transaction.client_name}</TableCell>
                      <TableCell>{transaction.service_name}</TableCell>
                      <TableCell>{transaction.staff_name}</TableCell>
                      <TableCell>{transaction.location}</TableCell>
                      <TableCell>
                        <Badge variant={transaction.sale_type === 'service' ? 'default' : 'secondary'}>
                          {transaction.sale_type}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right font-medium">
                        {formatCurrency(transaction.net_sales)}
                      </TableCell>
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
                <CardTitle>Revenue Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={dashboardData.trends}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="period" 
                      tickFormatter={(value) => new Date(value).getDate().toString()}
                    />
                    <YAxis />
                    <Tooltip formatter={(value) => formatCurrency(value as number)} />
                    <Area type="monotone" dataKey="total_sales" stroke="#8884d8" fill="#8884d8" fillOpacity={0.6} />
                    <Area type="monotone" dataKey="service_sales" stroke="#82ca9d" fill="#82ca9d" fillOpacity={0.6} />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Daily Transaction Volume</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={dashboardData.trends}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="period" 
                      tickFormatter={(value) => new Date(value).getDate().toString()}
                    />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="transaction_count" fill="#ffc658" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>

      {/* Chat Assistant */}
      {/* The SalonChat component was removed from imports, so this block will be removed */}
    </div>
  );
};

export default SalonDashboard; 