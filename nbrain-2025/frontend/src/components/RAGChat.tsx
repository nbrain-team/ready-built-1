import React, { useState, useEffect, useRef } from 'react';
import { Send, Database, TrendingUp, Calendar, Download, Upload } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { ragApi } from '../services/ragApi';

interface Message {
  id: string;
  query: string;
  response: string;
  timestamp: string;
  drillDowns?: DrillDown[];
}

interface DrillDown {
  label: string;
  action: string;
  context: any;
}

interface DataSource {
  id: number;
  name: string;
  display_name: string;
  description: string;
  entry_count: number;
}

export const RAGChat: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string>('');
  const [dataSources, setDataSources] = useState<DataSource[]>([]);
  const [selectedSources, setSelectedSources] = useState<string[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { user } = useAuth();

  useEffect(() => {
    // Generate session ID
    setSessionId(`rag-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`);
    
    // Load data sources
    loadDataSources();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadDataSources = async () => {
    try {
      const sources = await ragApi.getDataSources();
      setDataSources(sources);
    } catch (error) {
      console.error('Failed to load data sources:', error);
    }
  };

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage = input;
    setInput('');
    setLoading(true);

    // Add user message to chat
    const tempId = Date.now().toString();
    setMessages(prev => [...prev, {
      id: tempId,
      query: userMessage,
      response: '',
      timestamp: new Date().toISOString()
    }]);

    try {
      const response = await ragApi.sendChatMessage({
        query: userMessage,
        session_id: sessionId,
        context: {
          sources: selectedSources,
          date_range: {
            start: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
            end: new Date().toISOString()
          }
        }
      });

      // Update message with response
      setMessages(prev => prev.map(msg => 
        msg.id === tempId 
          ? {
              ...msg,
              response: response.response,
              drillDowns: response.drill_downs
            }
          : msg
      ));
    } catch (error) {
      console.error('Chat error:', error);
      setMessages(prev => prev.map(msg => 
        msg.id === tempId 
          ? {
              ...msg,
              response: 'Sorry, I encountered an error processing your request.'
            }
          : msg
      ));
    } finally {
      setLoading(false);
    }
  };

  const handleDrillDown = async (drillDown: DrillDown) => {
    const query = `${drillDown.label} based on the previous data`;
    setInput(query);
    handleSend();
  };

  const handleSourceToggle = (sourceName: string) => {
    setSelectedSources(prev => 
      prev.includes(sourceName)
        ? prev.filter(s => s !== sourceName)
        : [...prev, sourceName]
    );
  };

  return (
    <div className="flex h-full">
      {/* Sidebar - Data Sources */}
      <div className="w-64 bg-gray-50 p-4 border-r">
        <h3 className="font-semibold text-gray-700 mb-4 flex items-center">
          <Database className="w-4 h-4 mr-2" />
          Data Sources
        </h3>
        <div className="space-y-2">
          {dataSources.map(source => (
            <label
              key={source.id}
              className="flex items-center p-2 rounded hover:bg-gray-100 cursor-pointer"
            >
              <input
                type="checkbox"
                checked={selectedSources.includes(source.name)}
                onChange={() => handleSourceToggle(source.name)}
                className="mr-2"
              />
              <div className="flex-1">
                <div className="text-sm font-medium">{source.display_name}</div>
                <div className="text-xs text-gray-500">
                  {source.entry_count.toLocaleString()} entries
                </div>
              </div>
            </label>
          ))}
        </div>

        <div className="mt-6">
          <button className="w-full flex items-center justify-center p-2 bg-blue-600 text-white rounded hover:bg-blue-700">
            <Upload className="w-4 h-4 mr-2" />
            Upload Data
          </button>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 ? (
            <div className="text-center text-gray-500 mt-8">
              <Database className="w-12 h-12 mx-auto mb-4 text-gray-300" />
              <p className="text-lg font-medium">Ask questions about your data</p>
              <p className="text-sm mt-2">
                Select data sources and start exploring insights
              </p>
            </div>
          ) : (
            messages.map(message => (
              <div key={message.id} className="space-y-2">
                {/* User Query */}
                <div className="flex justify-end">
                  <div className="bg-blue-600 text-white p-3 rounded-lg max-w-2xl">
                    {message.query}
                  </div>
                </div>

                {/* AI Response */}
                {message.response && (
                  <div className="flex justify-start">
                    <div className="bg-gray-100 p-3 rounded-lg max-w-2xl">
                      <div className="prose prose-sm">
                        {message.response}
                      </div>

                      {/* Drill-down buttons */}
                      {message.drillDowns && message.drillDowns.length > 0 && (
                        <div className="mt-3 flex flex-wrap gap-2">
                          {message.drillDowns.map((drill, idx) => (
                            <button
                              key={idx}
                              onClick={() => handleDrillDown(drill)}
                              className="flex items-center px-3 py-1 bg-white border border-gray-300 rounded-full text-sm hover:bg-gray-50"
                            >
                              {drill.action === 'trend_analysis' && (
                                <TrendingUp className="w-3 h-3 mr-1" />
                              )}
                              {drill.action === 'period_comparison' && (
                                <Calendar className="w-3 h-3 mr-1" />
                              )}
                              {drill.label}
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ))
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="border-t p-4">
          <div className="flex items-center space-x-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSend()}
              placeholder="Ask about your data..."
              className="flex-1 p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={loading}
            />
            <button
              onClick={handleSend}
              disabled={loading || !input.trim()}
              className="p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}; 