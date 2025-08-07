import React, { useState, useRef, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { 
  Send, Bot, User, TrendingUp, Users, DollarSign, 
  Calendar, Target, Activity, AlertCircle, Sparkles, Loader2
} from 'lucide-react';
import { salonApi } from '@/services/salonApi';
import ReactMarkdown from 'react-markdown';

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
      content: "Hello! I'm your Salon Analytics Assistant. I can help you analyze staff performance, predict success, understand client behavior, and identify growth opportunities. What would you like to know?",
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
      console.log('Sending query to AI:', input);
      const response = await salonApi.processAnalyticsQuery(input);
      console.log('AI Response:', response);
      
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: response.response || response.message || 'I processed your request but received an unexpected response format.',
        data: response.data,
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error: any) {
      console.error('AI Chat Error:', error);
      
      let errorContent = "I apologize, but I encountered an error processing your request.";
      
      if (error.response) {
        // The request was made and the server responded with a status code
        // that falls out of the range of 2xx
        console.error('Error response:', error.response.data);
        console.error('Error status:', error.response.status);
        
        if (error.response.status === 404) {
          errorContent = "I'm having trouble connecting to the analytics service. Please try refreshing the page or contact support if the issue persists.";
        } else if (error.response.status === 500) {
          errorContent = "The server encountered an error processing your request. Please try again with a simpler query.";
        } else if (error.response.status === 429) {
          errorContent = "Too many requests. Please wait a moment before trying again.";
        }
      } else if (error.request) {
        // The request was made but no response was received
        console.error('No response received:', error.request);
        errorContent = "Unable to reach the server. Please check your internet connection and try again.";
      } else {
        // Something happened in setting up the request that triggered an Error
        console.error('Error setting up request:', error.message);
      }
      
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: errorContent,
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

  // Add a function to render markdown content
  const renderMessageContent = (content: string, type: 'user' | 'assistant') => {
    if (type === 'assistant') {
      return (
        <ReactMarkdown 
          className="prose prose-sm max-w-none"
          components={{
            h1: ({children}) => <h1 className="text-lg font-bold mb-2">{children}</h1>,
            h2: ({children}) => <h2 className="text-base font-semibold mb-2">{children}</h2>,
            h3: ({children}) => <h3 className="text-sm font-semibold mb-1">{children}</h3>,
            p: ({children}) => <p className="mb-2">{children}</p>,
            ul: ({children}) => <ul className="list-disc pl-4 mb-2">{children}</ul>,
            ol: ({children}) => <ol className="list-decimal pl-4 mb-2">{children}</ol>,
            li: ({children}) => <li className="mb-1">{children}</li>,
            strong: ({children}) => <strong className="font-semibold">{children}</strong>,
            code: ({children}) => <code className="bg-gray-200 px-1 rounded text-sm">{children}</code>,
            pre: ({children}) => <pre className="bg-gray-200 p-2 rounded overflow-x-auto mb-2">{children}</pre>,
          }}
        >
          {content}
        </ReactMarkdown>
      );
    }
    return content;
  };

  try {
    return (
      <div className="h-full w-full flex flex-col bg-white rounded-lg border border-gray-200">
        {/* Header */}
        <div className="px-4 py-3 border-b border-gray-200 bg-gray-50 rounded-t-lg">
          <div className="flex items-center gap-2">
            <Bot className="h-5 w-5 text-blue-500" />
            <h3 className="font-semibold text-gray-900">Salon AI Analytics Assistant</h3>
          </div>
        </div>
        
        {/* Main Content Area */}
        <div className="flex-1 flex flex-col min-h-0 p-4">
          {/* Sample Questions */}
          <div className="mb-3">
            <p className="text-xs text-gray-500 mb-2">Try asking:</p>
            <div className="flex flex-wrap gap-2">
              {SAMPLE_QUESTIONS.slice(0, 3).map((question, idx) => (
                <Button
                  key={idx}
                  variant="outline"
                  size="sm"
                  onClick={() => handleSampleQuestion(question)}
                  className="text-xs"
                >
                  {question.length > 40 ? question.substring(0, 40) + '...' : question}
                </Button>
              ))}
            </div>
          </div>

          {/* Messages Container with proper scroll */}
          <div className="flex-1 overflow-y-auto min-h-0 mb-4 pr-2">
            <div className="space-y-4">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div className={`max-w-[80%] ${message.type === 'user' ? 'order-2' : 'order-1'}`}>
                    <div className="flex items-start gap-2">
                      {message.type === 'assistant' && (
                        <Bot className="h-6 w-6 text-blue-500 mt-1 flex-shrink-0" />
                      )}
                      <div className="min-w-0 flex-1">
                        <div
                          className={`p-3 rounded-lg ${
                            message.type === 'user'
                              ? 'bg-blue-500 text-white'
                              : 'bg-gray-100 text-gray-900'
                          }`}
                        >
                          {renderMessageContent(message.content, message.type)}
                        </div>
                        {message.data && renderData(message.data)}
                        <div className="text-xs text-gray-500 mt-1">
                          {message.timestamp.toLocaleTimeString()}
                        </div>
                      </div>
                      {message.type === 'user' && (
                        <User className="h-6 w-6 text-gray-500 mt-1 flex-shrink-0" />
                      )}
                    </div>
                  </div>
                </div>
              ))}
              {loading && (
                <div className="flex justify-start">
                  <div className="flex items-start gap-2">
                    <Bot className="h-6 w-6 text-blue-500 mt-1 flex-shrink-0" />
                    <div className="bg-gray-100 text-gray-900 p-3 rounded-lg">
                      <Loader2 className="h-4 w-4 animate-spin" />
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          </div>

          {/* Input Area - Always visible at bottom */}
          <div className="flex gap-2 pt-2 border-t border-gray-200">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSend()}
              placeholder="Ask about staff performance, client behavior, growth opportunities..."
              disabled={loading}
              className="flex-1"
            />
            <Button 
              onClick={handleSend} 
              disabled={loading || !input.trim()} 
              size="sm"
            >
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
    );
  } catch (error) {
    console.error('Error rendering SalonAIChat:', error);
    return (
      <div className="h-full flex items-center justify-center bg-white rounded-lg shadow-sm">
        <div className="text-center p-6">
          <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Unable to Load AI Assistant</h3>
          <p className="text-sm text-gray-600 mb-4">
            There was an error loading the AI assistant. Please refresh the page to try again.
          </p>
          <Button onClick={() => window.location.reload()} variant="outline">
            Refresh Page
          </Button>
        </div>
      </div>
    );
  }
};

export default SalonAIChat; 