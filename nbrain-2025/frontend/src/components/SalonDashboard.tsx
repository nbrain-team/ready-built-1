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
  TrendingUp, TrendingDown, Users, DollarSign, Clock, 
  Calendar, Upload, MessageSquare, BarChart3, Activity,
  Search, Filter, ShoppingBag, Award, Target
} from 'lucide-react';
import { salonApiInstance as salonApi } from '@/services/salonApi';
import SalonChat from './SalonChat';

interface DashboardMetrics {
  total_locations: number;
  total_staff: number;
  active_staff: number;
  total_transactions: number;
  total_revenue: number;
  unique_clients: number;
  avg_daily_revenue: number;
  period?: string;
}

interface PerformanceTrend {
  period: string;
  transaction_count: number;
  total_sales: number;
  service_sales: number;
  unique_clients: number;
}

interface TopPerformer {
  staff_id: number;
  staff_name: string;
  location: string;
  net_sales: number;
  transactions: number;
  unique_clients: number;
  avg_ticket: number;
}

interface ServiceBreakdown {
  service_name: string;
  count: number;
  revenue: number;
  avg_price: number;
}

interface ClientInsights {
  total_clients: number;
  new_clients: number;
  returning_clients: number;
  vip_clients: number;
  avg_client_value: number;
  total_revenue: number;
}

interface Transaction {
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
}

const SalonDashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [trends, setTrends] = useState<PerformanceTrend[]>([]);
  const [topPerformers, setTopPerformers] = useState<TopPerformer[]>([]);
  const [serviceBreakdown, setServiceBreakdown] = useState<ServiceBreakdown[]>([]);
  const [clientInsights, setClientInsights] = useState<ClientInsights | null>(null);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [selectedLocation, setSelectedLocation] = useState<string>('all');
  const [selectedMetric, setSelectedMetric] = useState<string>('sales');
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [uploadProgress, setUploadProgress] = useState<string>('');
  const [showChat, setShowChat] = useState(false);

  useEffect(() => {
    loadDashboardData();
  }, [selectedLocation]);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const [overviewData, trendsData, performersData, servicesData, clientData] = await Promise.all([
        salonApi.getDashboardOverview(),
        salonApi.getPerformanceTrends(selectedLocation === 'all' ? undefined : parseInt(selectedLocation)),
        salonApi.getTopPerformers(selectedMetric),
        salonApi.getServiceBreakdown(selectedLocation === 'all' ? undefined : parseInt(selectedLocation)),
        salonApi.getClientInsights(selectedLocation === 'all' ? undefined : parseInt(selectedLocation))
      ]);

      setMetrics(overviewData);
      setTrends(trendsData);
      setTopPerformers(performersData);
      setServiceBreakdown(servicesData);
      setClientInsights(clientData);
    } catch (error) {
      console.error('Error loading dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  const searchTransactions = async () => {
    try {
      const result = await salonApi.searchTransactions({
        search: searchTerm,
        location_id: selectedLocation === 'all' ? undefined : parseInt(selectedLocation),
        limit: 50
      });
      setTransactions(result.results);
    } catch (error) {
      console.error('Error searching transactions:', error);
    }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>, type: 'staff' | 'performance') => {
    const file = event.target.files?.[0];
    if (!file) return;

    setUploadProgress(`Uploading ${type} data...`);
    try {
      const result = await salonApi.uploadData(file, type);
      setUploadProgress(`Success! ${result.message || 'Data uploaded successfully'}`);
      loadDashboardData(); // Refresh dashboard
    } catch (error) {
      setUploadProgress(`Error: ${error instanceof Error ? error.message : 'Upload failed'}`);
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', { 
      style: 'currency', 
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  const formatPercent = (value: number) => {
    return `${(value * 100).toFixed(1)}%`;
  };

  const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff7c7c', '#8dd1e1', '#d084d0', '#ffb347', '#87ceeb'];

  if (loading) {
    return <div className="flex items-center justify-center h-screen">Loading dashboard...</div>;
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Salon Analytics Dashboard</h1>
          <p className="text-muted-foreground">January 2025 Performance Data</p>
        </div>
        <div className="flex gap-4">
          <Button onClick={() => setShowChat(!showChat)}>
            <MessageSquare className="mr-2 h-4 w-4" />
            AI Assistant
          </Button>
          <div className="flex gap-2">
            <label className="cursor-pointer">
              <input
                type="file"
                accept=".csv"
                onChange={(e) => handleFileUpload(e, 'staff')}
                className="hidden"
              />
              <Button variant="outline">
                <Upload className="mr-2 h-4 w-4" />
                Upload Staff Data
              </Button>
            </label>
            <label className="cursor-pointer">
              <input
                type="file"
                accept=".csv"
                onChange={(e) => handleFileUpload(e, 'performance')}
                className="hidden"
              />
              <Button variant="outline">
                <Upload className="mr-2 h-4 w-4" />
                Upload Performance
              </Button>
            </label>
          </div>
        </div>
      </div>

      {uploadProgress && (
        <Alert>
          <AlertDescription>{uploadProgress}</AlertDescription>
        </Alert>
      )}

      {/* Enhanced Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Revenue</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(metrics?.total_revenue || 0)}</div>
            <p className="text-xs text-muted-foreground">
              {formatCurrency(metrics?.avg_daily_revenue || 0)}/day avg
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Transactions</CardTitle>
            <ShoppingBag className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{(metrics?.total_transactions || 0).toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">
              January 2025
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Unique Clients</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{(metrics?.unique_clients || 0).toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">
              Served this month
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Staff</CardTitle>
            <Award className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics?.active_staff || 0}</div>
            <p className="text-xs text-muted-foreground">
              Out of {metrics?.total_staff || 0} total
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Locations</CardTitle>
            <Target className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics?.total_locations || 0}</div>
            <p className="text-xs text-muted-foreground">Active locations</p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Tabs */}
      <Tabs defaultValue="trends" className="space-y-4">
        <TabsList className="grid w-full grid-cols-6">
          <TabsTrigger value="trends">Daily Trends</TabsTrigger>
          <TabsTrigger value="staff">Top Staff</TabsTrigger>
          <TabsTrigger value="services">Services</TabsTrigger>
          <TabsTrigger value="clients">Client Insights</TabsTrigger>
          <TabsTrigger value="transactions">Transactions</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
        </TabsList>

        <TabsContent value="trends" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>January 2025 Daily Performance</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <ComposedChart data={trends}>
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
                  {topPerformers.map((performer) => (
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
                        data={serviceBreakdown.slice(0, 8)}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={(entry) => `${entry.service_name.substring(0, 15)}...`}
                        outerRadius={80}
                        fill="#8884d8"
                        dataKey="revenue"
                      >
                        {serviceBreakdown.slice(0, 8).map((entry, index) => (
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
                    {serviceBreakdown.slice(0, 10).map((service, index) => (
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
              {clientInsights && (
                <div className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="p-4 rounded-lg bg-blue-50">
                      <p className="text-sm font-medium text-blue-900">Total Clients</p>
                      <p className="text-2xl font-bold text-blue-900">{clientInsights.total_clients.toLocaleString()}</p>
                    </div>
                    <div className="p-4 rounded-lg bg-green-50">
                      <p className="text-sm font-medium text-green-900">New Clients</p>
                      <p className="text-2xl font-bold text-green-900">{clientInsights.new_clients.toLocaleString()}</p>
                      <p className="text-xs text-green-700">{((clientInsights.new_clients / clientInsights.total_clients) * 100).toFixed(1)}% of total</p>
                    </div>
                    <div className="p-4 rounded-lg bg-purple-50">
                      <p className="text-sm font-medium text-purple-900">VIP Clients (5+ visits)</p>
                      <p className="text-2xl font-bold text-purple-900">{clientInsights.vip_clients.toLocaleString()}</p>
                      <p className="text-xs text-purple-700">{((clientInsights.vip_clients / clientInsights.total_clients) * 100).toFixed(1)}% of total</p>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="p-4 rounded-lg border">
                      <p className="text-sm font-medium">Average Client Value</p>
                      <p className="text-2xl font-bold">{formatCurrency(clientInsights.avg_client_value)}</p>
                    </div>
                    <div className="p-4 rounded-lg border">
                      <p className="text-sm font-medium">Returning Clients</p>
                      <p className="text-2xl font-bold">{clientInsights.returning_clients.toLocaleString()}</p>
                      <p className="text-xs text-muted-foreground">{((clientInsights.returning_clients / clientInsights.total_clients) * 100).toFixed(1)}% retention rate</p>
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
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
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
                  {transactions.map((transaction) => (
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
                  <AreaChart data={trends}>
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
                  <BarChart data={trends}>
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
      {showChat && (
        <div className="fixed bottom-4 right-4 w-96 h-[600px] bg-white rounded-lg shadow-xl border">
          <SalonChat onClose={() => setShowChat(false)} />
        </div>
      )}
    </div>
  );
};

export default SalonDashboard; 