'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  ChartBarIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  UserGroupIcon,
  ComputerDesktopIcon,
  ChatBubbleLeftRightIcon,
  DocumentTextIcon,
  EyeIcon,
  HeartIcon,
} from '@heroicons/react/24/outline';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { useQuery } from '@tanstack/react-query';
import apiService, { queryKeys } from '../services/api';
import {
  SystemMetrics,
  SystemHealth,
  UrgencyLevel,
  URGENCY_COLORS,
  ChatMessage,
} from '../types/medical';
import Layout from '../components/Layout';

// Mock data for demonstration
const mockHourlyData = [
  { hour: '00:00', cases: 2, critical: 0, high: 1, medium: 1, low: 0 },
  { hour: '01:00', cases: 1, critical: 0, high: 0, medium: 1, low: 0 },
  { hour: '02:00', cases: 3, critical: 1, high: 1, medium: 1, low: 0 },
  { hour: '03:00', cases: 2, critical: 0, high: 1, medium: 0, low: 1 },
  { hour: '04:00', cases: 4, critical: 1, high: 2, medium: 1, low: 0 },
  { hour: '05:00', cases: 6, critical: 2, high: 2, medium: 1, low: 1 },
  { hour: '06:00', cases: 8, critical: 3, high: 3, medium: 2, low: 0 },
  { hour: '07:00', cases: 12, critical: 4, high: 4, medium: 3, low: 1 },
  { hour: '08:00', cases: 15, critical: 5, high: 6, medium: 3, low: 1 },
  { hour: '09:00', cases: 18, critical: 6, high: 7, medium: 4, low: 1 },
  { hour: '10:00', cases: 22, critical: 8, high: 8, medium: 4, low: 2 },
  { hour: '11:00', cases: 25, critical: 9, high: 10, medium: 4, low: 2 },
];

const urgencyDistribution = [
  { name: 'Critical', value: 15, color: '#ef4444' },
  { name: 'High', value: 35, color: '#f97316' },
  { name: 'Medium', value: 30, color: '#f59e0b' },
  { name: 'Low', value: 20, color: '#10b981' },
];

const processingTimeData = [
  { agent: 'Vision Bot', time: 2.3, requests: 45 },
  { agent: 'Text Bot', time: 1.8, requests: 67 },
  { agent: 'Chief Bot', time: 3.1, requests: 89 },
];

export default function Dashboard() {
  const [chatMessage, setChatMessage] = useState('');
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const [isLLMLoading, setIsLLMLoading] = useState(false);

  // Fetch system data
  const { data: systemHealth } = useQuery({
    queryKey: queryKeys.health,
    queryFn: apiService.getSystemHealth,
    refetchInterval: 30000,
  });

  const { data: systemMetrics } = useQuery({
    queryKey: queryKeys.metrics,
    queryFn: apiService.getSystemMetrics,
    refetchInterval: 5000,
  });

  // LLM Chat Integration
  const handleSendMessage = async () => {
    if (!chatMessage.trim()) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: chatMessage,
      timestamp: new Date().toISOString(),
    };

    setChatHistory(prev => [...prev, userMessage]);
    setChatMessage('');
    setIsLLMLoading(true);

    try {
      const response = await apiService.sendChatMessage(chatMessage);
      setChatHistory(prev => [...prev, response]);
    } catch (error) {
      console.error('Chat error:', error);
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your message. Please try again.',
        timestamp: new Date().toISOString(),
      };
      setChatHistory(prev => [...prev, errorMessage]);
    } finally {
      setIsLLMLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <Layout>
      <div className="space-y-6">
        {/* Welcome Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="medical-gradient rounded-xl p-6 text-white"
        >
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold">Medical Triage-BOTS Dashboard</h1>
              <p className="text-medical-100 mt-1">
                AI-powered medical triage system with multi-modal analysis
              </p>
            </div>
            <HeartIcon className="h-12 w-12 text-medical-200" />
          </div>
        </motion.div>

        {/* Quick Stats */}
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard
            title="Total Cases Today"
            value={systemMetrics?.metrics.total_requests || 0}
            change="+12%"
            changeType="positive"
            icon={DocumentTextIcon}
            color="blue"
          />
          <StatCard
            title="Critical Cases"
            value={systemMetrics?.metrics.critical_cases || 0}
            change="+3"
            changeType="negative"
            icon={ExclamationTriangleIcon}
            color="red"
          />
          <StatCard
            title="Avg Processing Time"
            value={`${(systemMetrics?.metrics.average_processing_time || 0).toFixed(1)}s`}
            change="-0.2s"
            changeType="positive"
            icon={ClockIcon}
            color="green"
          />
          <StatCard
            title="Success Rate"
            value={`${((systemMetrics?.metrics.successful_requests || 0) / Math.max(systemMetrics?.metrics.total_requests || 1, 1) * 100).toFixed(1)}%`}
            change="+2.1%"
            changeType="positive"
            icon={CheckCircleIcon}
            color="green"
          />
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          {/* Cases Over Time Chart */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="lg:col-span-2 card"
          >
            <div className="card-header">
              <h3 className="text-lg font-semibold text-gray-900">Cases by Hour</h3>
              <p className="text-sm text-gray-500">Triage cases processed throughout the day</p>
            </div>
            <div className="card-body">
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={mockHourlyData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
                  <XAxis dataKey="hour" stroke="#6b7280" />
                  <YAxis stroke="#6b7280" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'white',
                      border: '1px solid #e5e7eb',
                      borderRadius: '8px',
                      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
                    }}
                  />
                  <Area
                    type="monotone"
                    dataKey="critical"
                    stackId="1"
                    stroke="#ef4444"
                    fill="#ef4444"
                    fillOpacity={0.8}
                  />
                  <Area
                    type="monotone"
                    dataKey="high"
                    stackId="1"
                    stroke="#f97316"
                    fill="#f97316"
                    fillOpacity={0.8}
                  />
                  <Area
                    type="monotone"
                    dataKey="medium"
                    stackId="1"
                    stroke="#f59e0b"
                    fill="#f59e0b"
                    fillOpacity={0.8}
                  />
                  <Area
                    type="monotone"
                    dataKey="low"
                    stackId="1"
                    stroke="#10b981"
                    fill="#10b981"
                    fillOpacity={0.8}
                  />
                  <Legend />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </motion.div>

          {/* Urgency Distribution */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="card"
          >
            <div className="card-header">
              <h3 className="text-lg font-semibold text-gray-900">Urgency Distribution</h3>
              <p className="text-sm text-gray-500">Current case priorities</p>
            </div>
            <div className="card-body">
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie
                    data={urgencyDistribution}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {urgencyDistribution.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </motion.div>
        </div>

        {/* LLM Chat Integration and Processing Times */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          {/* AI Chat Interface */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="card"
          >
            <div className="card-header flex items-center gap-x-3">
              <ChatBubbleLeftRightIcon className="h-6 w-6 text-medical-600" />
              <div>
                <h3 className="text-lg font-semibold text-gray-900">AI Medical Assistant</h3>
                <p className="text-sm text-gray-500">Ask questions about medical cases or system status</p>
              </div>
            </div>
            <div className="card-body">
              {/* Chat History */}
              <div className="h-64 overflow-y-auto mb-4 space-y-3 border border-gray-200 rounded-lg p-3">
                {chatHistory.length === 0 ? (
                  <div className="flex items-center justify-center h-full text-gray-500">
                    <div className="text-center">
                      <ChatBubbleLeftRightIcon className="h-8 w-8 mx-auto mb-2 text-gray-400" />
                      <p className="text-sm">Start a conversation with the AI assistant</p>
                      <p className="text-xs text-gray-400 mt-1">
                        Ask about symptoms, medical data, or system status
                      </p>
                    </div>
                  </div>
                ) : (
                  chatHistory.map((message) => (
                    <div
                      key={message.id}
                      className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                      <div
                        className={`max-w-xs lg:max-w-md px-3 py-2 rounded-lg text-sm ${
                          message.role === 'user'
                            ? 'bg-medical-600 text-white'
                            : 'bg-gray-100 text-gray-900'
                        }`}
                      >
                        <p>{message.content}</p>
                        <p className={`text-xs mt-1 ${
                          message.role === 'user' ? 'text-medical-200' : 'text-gray-500'
                        }`}>
                          {new Date(message.timestamp).toLocaleTimeString()}
                        </p>
                      </div>
                    </div>
                  ))
                )}
                {isLLMLoading && (
                  <div className="flex justify-start">
                    <div className="bg-gray-100 px-3 py-2 rounded-lg">
                      <div className="flex items-center space-x-2">
                        <div className="spinner-sm" />
                        <span className="text-sm text-gray-600">AI is thinking...</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Chat Input */}
              <div className="flex gap-x-2">
                <input
                  type="text"
                  value={chatMessage}
                  onChange={(e) => setChatMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Ask about medical cases, symptoms, or system status..."
                  className="flex-1 form-input text-sm"
                  disabled={isLLMLoading}
                />
                <button
                  onClick={handleSendMessage}
                  disabled={!chatMessage.trim() || isLLMLoading}
                  className="btn-primary px-4 py-2 text-sm disabled:opacity-50"
                >
                  Send
                </button>
              </div>

              {/* Quick Questions */}
              <div className="mt-3 flex flex-wrap gap-2">
                {[
                  'What are the symptoms of diabetes?',
                  'Show me system health',
                  'How many critical cases today?',
                  'Explain triage scoring'
                ].map((question) => (
                  <button
                    key={question}
                    onClick={() => setChatMessage(question)}
                    className="text-xs px-2 py-1 bg-gray-100 hover:bg-gray-200 rounded-full text-gray-700 transition-colors"
                  >
                    {question}
                  </button>
                ))}
              </div>
            </div>
          </motion.div>

          {/* Processing Performance */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="card"
          >
            <div className="card-header">
              <h3 className="text-lg font-semibold text-gray-900">Agent Performance</h3>
              <p className="text-sm text-gray-500">Average processing times by agent</p>
            </div>
            <div className="card-body">
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={processingTimeData} layout="horizontal">
                  <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
                  <XAxis type="number" stroke="#6b7280" />
                  <YAxis dataKey="agent" type="category" stroke="#6b7280" width={80} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'white',
                      border: '1px solid #e5e7eb',
                      borderRadius: '8px',
                      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
                    }}
                  />
                  <Bar dataKey="time" fill="#0ea5e9" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>

              {/* Agent Details */}
              <div className="mt-4 space-y-2">
                {processingTimeData.map((agent) => (
                  <div key={agent.agent} className="flex items-center justify-between py-2 px-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center gap-x-3">
                      {agent.agent === 'Vision Bot' && <EyeIcon className="h-5 w-5 text-purple-600" />}
                      {agent.agent === 'Text Bot' && <DocumentTextIcon className="h-5 w-5 text-blue-600" />}
                      {agent.agent === 'Chief Bot' && <ComputerDesktopIcon className="h-5 w-5 text-green-600" />}
                      <span className="text-sm font-medium text-gray-900">{agent.agent}</span>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-semibold text-gray-900">{agent.time}s</div>
                      <div className="text-xs text-gray-500">{agent.requests} requests</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </motion.div>
        </div>

        {/* Recent Activity */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="card"
        >
          <div className="card-header">
            <h3 className="text-lg font-semibold text-gray-900">Recent Activity</h3>
            <p className="text-sm text-gray-500">Latest triage cases and system events</p>
          </div>
          <div className="card-body">
            <div className="space-y-4">
              {[
                {
                  id: 1,
                  type: 'case',
                  message: 'New critical case submitted - Patient P67890',
                  time: '2 minutes ago',
                  urgency: UrgencyLevel.CRITICAL,
                },
                {
                  id: 2,
                  type: 'system',
                  message: 'Vision Bot completed image analysis for case C123',
                  time: '5 minutes ago',
                  urgency: UrgencyLevel.LOW,
                },
                {
                  id: 3,
                  type: 'case',
                  message: 'High priority case resolved - Patient P12345',
                  time: '8 minutes ago',
                  urgency: UrgencyLevel.HIGH,
                },
                {
                  id: 4,
                  type: 'system',
                  message: 'System health check completed successfully',
                  time: '15 minutes ago',
                  urgency: UrgencyLevel.LOW,
                },
              ].map((activity) => (
                <div key={activity.id} className="flex items-center gap-x-4 p-3 hover:bg-gray-50 rounded-lg transition-colors">
                  <div className={`w-2 h-2 rounded-full ${urgencyColors[activity.urgency]}`} />
                  <div className="flex-1">
                    <p className="text-sm text-gray-900">{activity.message}</p>
                    <p className="text-xs text-gray-500">{activity.time}</p>
                  </div>
                  <div className={`text-xs px-2 py-1 rounded-full ${
                    activity.urgency === UrgencyLevel.CRITICAL
                      ? 'bg-red-100 text-red-800'
                      : activity.urgency === UrgencyLevel.HIGH
                      ? 'bg-orange-100 text-orange-800'
                      : 'bg-gray-100 text-gray-800'
                  }`}>
                    {activity.type}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </motion.div>
      </div>
    </Layout>
  );
}

interface StatCardProps {
  title: string;
  value: string | number;
  change: string;
  changeType: 'positive' | 'negative' | 'neutral';
  icon: React.ComponentType<any>;
  color: 'blue' | 'red' | 'green' | 'yellow';
}

function StatCard({ title, value, change, changeType, icon: Icon, color }: StatCardProps) {
  const colorClasses = {
    blue: 'bg-blue-50 text-blue-600',
    red: 'bg-red-50 text-red-600',
    green: 'bg-green-50 text-green-600',
    yellow: 'bg-yellow-50 text-yellow-600',
  };

  const changeClasses = {
    positive: 'text-green-600',
    negative: 'text-red-600',
    neutral: 'text-gray-600',
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -2 }}
      className="card hover:shadow-lg transition-shadow duration-200"
    >
      <div className="card-body">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-600">{title}</p>
            <p className="text-2xl font-bold text-gray-900">{value}</p>
            <p className={`text-sm font-medium ${changeClasses[changeType]}`}>
              {change} from yesterday
            </p>
          </div>
          <div className={`p-3 rounded-lg ${colorClasses[color]}`}>
            <Icon className="h-6 w-6" />
          </div>
        </div>
      </div>
    </motion.div>
  );
}

const urgencyColors = {
  [UrgencyLevel.CRITICAL]: 'bg-red-500',
  [UrgencyLevel.HIGH]: 'bg-orange-500',
  [UrgencyLevel.MEDIUM]: 'bg-yellow-500',
  [UrgencyLevel.LOW]: 'bg-green-500',
};
