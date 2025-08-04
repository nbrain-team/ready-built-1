import React, { useState, useEffect } from 'react';
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  TrendingUp, TrendingDown, Users, DollarSign, Clock, 
  Calendar, Upload, MessageSquare, BarChart3, Activity
} from 'lucide-react';
import { salonApiInstance as salonApi } from '@/services/salonApi';
import SalonChat from './SalonChat';

interface DashboardMetrics {
  total_locations: number;
  total_staff: number;
  active_staff: number;
  avg_utilization: number;
  total_revenue: number;
  new_clients: number;
  period?: string;
}

interface PerformanceTrend {
  period: string;
  total_sales: number;
  avg_utilization: number;
  total_appointments: number;
  new_clients: number;
}

interface TopPerformer {
  staff_id: number;
  staff_name: string;
  location: string;
  net_sales: number;
  utilization: number;
  appointments: number;
  prebooking: number;
}

const SalonDashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [trends, setTrends] = useState<PerformanceTrend[]>([]);
  const [topPerformers, setTopPerformers] = useState<TopPerformer[]>([]);
  const [selectedLocation, setSelectedLocation] = useState<string>('all');
  const [selectedMetric, setSelectedMetric] = useState<string>('sales');
  const [loading, setLoading] = useState(true);
  const [uploadProgress, setUploadProgress] = useState<string>('');
  const [showChat, setShowChat] = useState(false);

  useEffect(() => {
    loadDashboardData();
  }, [selectedLocation]);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const [overviewData, trendsData, performersData] = await Promise.all([
        salonApi.getDashboardOverview(),
        salonApi.getPerformanceTrends(selectedLocation === 'all' ? undefined : parseInt(selectedLocation)),
        salonApi.getTopPerformers(selectedMetric)
      ]);

      setMetrics(overviewData);
      setTrends(trendsData.reverse()); // Chronological order
      setTopPerformers(performersData);
    } catch (error) {
      console.error('Error loading dashboard:', error);
    } finally {
      setLoading(false);
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

  const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff7c7c', '#8dd1e1'];

  if (loading) {
    return <div className="flex items-center justify-center h-screen">Loading dashboard...</div>;
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Salon Analytics Dashboard</h1>
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

      {/* Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Revenue</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(metrics?.total_revenue || 0)}</div>
            <p className="text-xs text-muted-foreground">
              {metrics?.period ? `Period: ${new Date(metrics.period).toLocaleDateString()}` : 'Current month'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Utilization</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatPercent(metrics?.avg_utilization || 0)}</div>
            <div className="flex items-center text-xs">
              {(metrics?.avg_utilization || 0) > 0.7 ? (
                <TrendingUp className="h-4 w-4 text-green-500 mr-1" />
              ) : (
                <TrendingDown className="h-4 w-4 text-red-500 mr-1" />
              )}
              {(metrics?.avg_utilization || 0) > 0.7 ? 'High demand' : 'Opportunity to grow'}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Staff</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
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
            <CardTitle className="text-sm font-medium">New Clients</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics?.new_clients || 0}</div>
            <p className="text-xs text-muted-foreground">This month</p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Tabs */}
      <Tabs defaultValue="trends" className="space-y-4">
        <TabsList>
          <TabsTrigger value="trends">Performance Trends</TabsTrigger>
          <TabsTrigger value="staff">Staff Analytics</TabsTrigger>
          <TabsTrigger value="capacity">Capacity Analysis</TabsTrigger>
          <TabsTrigger value="predictions">Predictions</TabsTrigger>
        </TabsList>

        <TabsContent value="trends" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Revenue & Utilization Trends</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={trends}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="period" 
                    tickFormatter={(value) => new Date(value).toLocaleDateString('en-US', { month: 'short', year: '2-digit' })}
                  />
                  <YAxis yAxisId="left" orientation="left" stroke="#8884d8" />
                  <YAxis yAxisId="right" orientation="right" stroke="#82ca9d" />
                  <Tooltip 
                    formatter={(value: any, name: string) => {
                      if (name === 'Revenue') return formatCurrency(value);
                      if (name === 'Utilization') return formatPercent(value);
                      return value;
                    }}
                  />
                  <Legend />
                  <Line yAxisId="left" type="monotone" dataKey="total_sales" stroke="#8884d8" name="Revenue" />
                  <Line yAxisId="right" type="monotone" dataKey="avg_utilization" stroke="#82ca9d" name="Utilization" />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Appointments Trend</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={trends}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="period" 
                      tickFormatter={(value) => new Date(value).toLocaleDateString('en-US', { month: 'short' })}
                    />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="total_appointments" fill="#8884d8" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>New Client Acquisition</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={trends}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="period" 
                      tickFormatter={(value) => new Date(value).toLocaleDateString('en-US', { month: 'short' })}
                    />
                    <YAxis />
                    <Tooltip />
                    <Line type="monotone" dataKey="new_clients" stroke="#82ca9d" strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="staff" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex justify-between items-center">
                <CardTitle>Top Performers</CardTitle>
                <Select value={selectedMetric} onValueChange={setSelectedMetric}>
                  <SelectTrigger className="w-[180px]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="sales">By Sales</SelectItem>
                    <SelectItem value="utilization">By Utilization</SelectItem>
                    <SelectItem value="appointments">By Appointments</SelectItem>
                    <SelectItem value="prebooking">By Prebooking</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {topPerformers.map((performer, index) => (
                  <div key={performer.staff_id} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex items-center gap-4">
                      <div className="text-2xl font-bold text-muted-foreground">
                        #{index + 1}
                      </div>
                      <div>
                        <p className="font-semibold">{performer.staff_name}</p>
                        <p className="text-sm text-muted-foreground">{performer.location}</p>
                      </div>
                    </div>
                    <div className="flex gap-6 text-right">
                      <div>
                        <p className="text-sm text-muted-foreground">Sales</p>
                        <p className="font-semibold">{formatCurrency(performer.net_sales)}</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Utilization</p>
                        <p className="font-semibold">{formatPercent(performer.utilization)}</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Appointments</p>
                        <p className="font-semibold">{performer.appointments}</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Prebooking</p>
                        <p className="font-semibold">{formatPercent(performer.prebooking)}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="capacity">
          <Card>
            <CardHeader>
              <CardTitle>Capacity Utilization Analysis</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8">
                <p className="text-muted-foreground">
                  Click "Analyze Capacity" in the AI Assistant to get detailed capacity insights
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="predictions">
          <Card>
            <CardHeader>
              <CardTitle>Staff Success Predictions</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8">
                <p className="text-muted-foreground">
                  Use the AI Assistant to predict staff success based on early performance indicators
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* AI Chat Sidebar */}
      {showChat && (
        <div className="fixed right-0 top-0 h-screen w-96 bg-background border-l shadow-lg z-50 flex flex-col">
          <div className="flex justify-between items-center p-4 border-b flex-shrink-0">
            <h2 className="text-lg font-semibold">AI Analytics Assistant</h2>
            <Button variant="ghost" size="sm" onClick={() => setShowChat(false)}>
              ×
            </Button>
          </div>
          <div className="flex-1 overflow-hidden">
            <SalonChat />
          </div>
        </div>
      )}
    </div>
  );
};

export default SalonDashboard; 