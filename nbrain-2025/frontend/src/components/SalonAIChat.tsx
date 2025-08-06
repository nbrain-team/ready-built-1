import React, { useState, useRef, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { 
  Send, Bot, User, TrendingUp, Users, DollarSign, 
  Calendar, Target, Activity, AlertCircle, Sparkles
} from 'lucide-react';
import { salonApi } from '@/services/salonApi';

interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  data?: any;
  timestamp: Date;
}

const SAMPLE_QUESTIONS = [
  "Can I predict the success of a newly hired stylist based on 4-6 weeks?",
  "What does the typical ramp up period look like for successful stylists?",
  "What are the most productive stylist characteristics?",
  "When is a salon overstaffed or understaffed?",
  "How do I determine growth potential based on customer data?",
  "How do I optimize scheduling?",
  "What is the optimum number of hours per week for a stylist?",
  "Does prebooking increase frequency of purchase?",
  "Which clients are targetable for increased frequency?",
  "What are the characteristics of new client return behavior?"
];

const SalonAIChat: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      type: 'assistant',
      content: "Hello! I'm your Salon Analytics AI Assistant. I can help you understand your salon's performance, predict staff success, identify growth opportunities, and optimize operations. What would you like to know?",
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
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
        type: 'assistant',
        content: response.response || "I've analyzed your query. Here's what I found:",
        data: response.data,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: "I apologize, but I encountered an error processing your request. Please try again.",
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleSampleQuestion = (question: string) => {
    setInput(question);
  };

  const renderData = (data: any) => {
    if (!data) return null;

    return (
      <div className="mt-4 space-y-4">
        {/* Predictions */}
        {data.predictions && (
          <div className="space-y-2">
            <h4 className="font-semibold text-sm">Staff Predictions:</h4>
            {data.predictions.map((pred: any, idx: number) => (
              <div key={idx} className="p-3 bg-gray-50 rounded-lg">
                <div className="flex justify-between items-center">
                  <span className="font-medium">{pred.staff_name}</span>
                  <Badge className={pred.predicted_outcome === 'Success' ? 'bg-green-500' : 'bg-yellow-500'}>
                    {pred.predicted_outcome}
                  </Badge>
                </div>
                <div className="text-xs text-gray-600 mt-1">
                  Success Probability: {pred.success_probability}%
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Key Characteristics */}
        {data.key_characteristics && (
          <div className="space-y-2">
            <h4 className="font-semibold text-sm">Key Characteristics:</h4>
            <div className="grid grid-cols-2 gap-2">
              {Object.entries(data.key_characteristics).map(([key, value]: [string, any]) => (
                <div key={key} className="p-2 bg-blue-50 rounded">
                  <div className="text-xs text-gray-600">{key.replace(/_/g, ' ').toUpperCase()}</div>
                  <div className="font-semibold">
                    Top: {value.top_performers?.toFixed(1)}%
                  </div>
                  <div className="text-sm">
                    Avg: {value.average_performers?.toFixed(1)}%
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Growth Opportunities */}
        {data.growth_opportunities && (
          <div className="space-y-2">
            <h4 className="font-semibold text-sm">Growth Opportunities:</h4>
            {Object.entries(data.growth_opportunities).map(([key, value]) => (
              <div key={key} className="p-2 bg-green-50 rounded">
                <div className="text-xs text-gray-600">{key.replace(/_/g, ' ').toUpperCase()}</div>
                <div className="font-semibold">{String(value)}</div>
              </div>
            ))}
          </div>
        )}

        {/* Recommendations */}
        {data.recommendations && (
          <div className="space-y-2">
            <h4 className="font-semibold text-sm">Recommendations:</h4>
            <ul className="space-y-1">
              {data.recommendations.map((rec: string, idx: number) => (
                <li key={idx} className="flex items-start">
                  <Sparkles className="h-4 w-4 text-yellow-500 mr-2 mt-0.5 flex-shrink-0" />
                  <span className="text-sm">{rec}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Client Segments */}
        {data.segments && (
          <div className="space-y-2">
            <h4 className="font-semibold text-sm">Client Segments:</h4>
            {Object.entries(data.segments).map(([key, segment]: [string, any]) => (
              <div key={key} className="p-3 bg-purple-50 rounded">
                <div className="font-medium text-sm">{key.replace(/_/g, ' ').toUpperCase()}</div>
                <div className="text-xs text-gray-600">Count: {segment.count}</div>
                <div className="text-xs">Potential: {segment.potential}</div>
              </div>
            ))}
          </div>
        )}

        {/* Capacity Analysis */}
        {data.locations && (
          <div className="space-y-2">
            <h4 className="font-semibold text-sm">Location Capacity:</h4>
            {data.locations.map((loc: any, idx: number) => (
              <div key={idx} className="p-3 bg-orange-50 rounded">
                <div className="flex justify-between items-center">
                  <span className="font-medium">{loc.location}</span>
                  <Badge className={
                    loc.status === 'Understaffed' ? 'bg-red-500' :
                    loc.status === 'Overstaffed' ? 'bg-yellow-500' :
                    'bg-green-500'
                  }>
                    {loc.status}
                  </Badge>
                </div>
                <div className="text-xs text-gray-600 mt-1">
                  Utilization: {loc.utilization_rate?.toFixed(1)}%
                </div>
                <div className="text-xs mt-1">{loc.recommended_action}</div>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2">
          <Bot className="h-5 w-5" />
          Salon AI Analytics Assistant
        </CardTitle>
      </CardHeader>
      
      <CardContent className="flex-1 flex flex-col p-4">
        {/* Sample Questions */}
        <div className="mb-4">
          <p className="text-xs text-gray-600 mb-2">Try asking:</p>
          <div className="flex flex-wrap gap-2">
            {SAMPLE_QUESTIONS.slice(0, 3).map((question, idx) => (
              <Button
                key={idx}
                variant="outline"
                size="sm"
                onClick={() => handleSampleQuestion(question)}
                className="text-xs"
              >
                {question.substring(0, 40)}...
              </Button>
            ))}
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto space-y-4 mb-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div className={`max-w-[80%] ${message.type === 'user' ? 'order-2' : 'order-1'}`}>
                <div className="flex items-start gap-2">
                  {message.type === 'assistant' && (
                    <Bot className="h-6 w-6 text-blue-500 mt-1" />
                  )}
                  <div>
                    <div
                      className={`p-3 rounded-lg ${
                        message.type === 'user'
                          ? 'bg-blue-500 text-white'
                          : 'bg-gray-100 text-gray-900'
                      }`}
                    >
                      {message.content}
                    </div>
                    {message.data && renderData(message.data)}
                    <div className="text-xs text-gray-500 mt-1">
                      {message.timestamp.toLocaleTimeString()}
                    </div>
                  </div>
                  {message.type === 'user' && (
                    <User className="h-6 w-6 text-gray-500 mt-1" />
                  )}
                </div>
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex justify-start">
              <div className="flex items-center gap-2">
                <Bot className="h-6 w-6 text-blue-500" />
                <div className="bg-gray-100 p-3 rounded-lg">
                  <div className="flex gap-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                  </div>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="flex gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Ask about staff performance, client behavior, growth opportunities..."
            disabled={loading}
            className="flex-1"
          />
          <Button onClick={handleSend} disabled={loading || !input.trim()}>
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

export default SalonAIChat; 