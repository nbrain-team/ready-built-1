import React, { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { 
  Send, Bot, User, TrendingUp, Users, Clock, 
  DollarSign, AlertCircle, BarChart3 
} from 'lucide-react';
import { salonApi } from '@/services/salonApi';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  data?: any;
}

interface QuickAction {
  label: string;
  query: string;
  icon: React.ReactNode;
}

const SalonChat: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: `Hi! I'm your Salon Analytics Assistant. I can help you with:
      
• Predicting staff success based on early performance
• Analyzing capacity utilization and staffing needs
• Understanding prebooking impact on revenue
• Optimizing scheduling and hours
• Identifying growth opportunities

What would you like to know?`,
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const scrollAreaRef = useRef<HTMLDivElement>(null);

  const quickActions: QuickAction[] = [
    {
      label: 'Analyze Capacity',
      query: 'What is our current capacity utilization? Are we over or understaffed?',
      icon: <BarChart3 className="h-4 w-4" />
    },
    {
      label: 'Prebooking Impact',
      query: 'Does prebooking increase frequency of purchase?',
      icon: <TrendingUp className="h-4 w-4" />
    },
    {
      label: 'Optimal Hours',
      query: 'What is the optimum number of hours per week for a stylist?',
      icon: <Clock className="h-4 w-4" />
    },
    {
      label: 'Growth Potential',
      query: 'How can we determine the growth potential of our salon?',
      icon: <DollarSign className="h-4 w-4" />
    }
  ];

  useEffect(() => {
    // Scroll to bottom when new messages are added
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await salonApi.processAnalyticsQuery(input);
      
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.response,
        timestamp: new Date(),
        data: response.data
      };

      setMessages(prev => [...prev, assistantMessage]);

      // If there's data, render it appropriately
      if (response.data && response.data.success) {
        renderAnalyticsData(response.data);
      }
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your request. Please try again.',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const renderAnalyticsData = (data: any) => {
    // This would render specific visualizations based on the data type
    // For now, we'll just log it
    console.log('Analytics data:', data);
  };

  const handleQuickAction = (query: string) => {
    setInput(query);
    handleSend();
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('en-US', { 
      hour: 'numeric', 
      minute: '2-digit',
      hour12: true 
    });
  };

  return (
    <div className="flex flex-col h-full">
      <ScrollArea className="flex-1 p-4" ref={scrollAreaRef}>
        <div className="space-y-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex gap-3 ${
                message.role === 'user' ? 'justify-end' : 'justify-start'
              }`}
            >
              {message.role === 'assistant' && (
                <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                  <Bot className="h-5 w-5 text-primary" />
                </div>
              )}
              
              <div className={`max-w-[80%] ${message.role === 'user' ? 'order-first' : ''}`}>
                <Card className={`p-3 ${
                  message.role === 'user' 
                    ? 'bg-primary text-primary-foreground' 
                    : 'bg-muted'
                }`}>
                  <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                  
                  {message.data && (
                    <div className="mt-3 pt-3 border-t">
                      {/* Render specific data visualizations here */}
                      {message.data.overall_utilization !== undefined && (
                        <div className="space-y-2">
                          <div className="flex justify-between">
                            <span>Utilization:</span>
                            <span className="font-semibold">
                              {(message.data.overall_utilization).toFixed(1)}%
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span>Status:</span>
                            <span className={`font-semibold capitalize ${
                              message.data.status === 'optimal' ? 'text-green-600' :
                              message.data.status === 'understaffed' ? 'text-red-600' :
                              'text-yellow-600'
                            }`}>
                              {message.data.status}
                            </span>
                          </div>
                        </div>
                      )}
                      
                      {message.data.prebooking_impact && (
                        <div className="space-y-2">
                          <div className="flex justify-between">
                            <span>Appointment Increase:</span>
                            <span className="font-semibold text-green-600">
                              +{message.data.prebooking_impact.appointment_increase_percent.toFixed(1)}%
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span>Sales Increase:</span>
                            <span className="font-semibold text-green-600">
                              +{message.data.prebooking_impact.sales_increase_percent.toFixed(1)}%
                            </span>
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </Card>
                <p className="text-xs text-muted-foreground mt-1">
                  {formatTime(message.timestamp)}
                </p>
              </div>
              
              {message.role === 'user' && (
                <div className="w-8 h-8 rounded-full bg-secondary flex items-center justify-center">
                  <User className="h-5 w-5" />
                </div>
              )}
            </div>
          ))}
          
          {loading && (
            <div className="flex gap-3 justify-start">
              <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                <Bot className="h-5 w-5 text-primary" />
              </div>
              <Card className="p-3 bg-muted">
                <div className="flex gap-1">
                  <div className="w-2 h-2 bg-primary rounded-full animate-bounce" />
                  <div className="w-2 h-2 bg-primary rounded-full animate-bounce delay-100" />
                  <div className="w-2 h-2 bg-primary rounded-full animate-bounce delay-200" />
                </div>
              </Card>
            </div>
          )}
        </div>
      </ScrollArea>

      {/* Quick Actions */}
      <div className="p-4 border-t">
        <div className="mb-3">
          <p className="text-xs text-muted-foreground mb-2">Quick Actions:</p>
          <div className="grid grid-cols-2 gap-2">
            {quickActions.map((action) => (
              <Button
                key={action.label}
                variant="outline"
                size="sm"
                onClick={() => handleQuickAction(action.query)}
                className="justify-start"
              >
                {action.icon}
                <span className="ml-2 text-xs">{action.label}</span>
              </Button>
            ))}
          </div>
        </div>

        {/* Input */}
        <div className="flex gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Ask about your salon analytics..."
            disabled={loading}
          />
          <Button 
            onClick={handleSend} 
            disabled={!input.trim() || loading}
            size="icon"
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
};

export default SalonChat; 