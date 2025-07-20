'use client';

import React, { useState, useEffect } from 'react';
import { usePathname } from 'next/navigation';
import Link from 'next/link';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Bars3Icon,
  XMarkIcon,
  HomeIcon,
  ChartBarIcon,
  ChatBubbleLeftRightIcon,
  ClipboardDocumentListIcon,
  Cog6ToothIcon,
  HeartIcon,
  BellIcon,
  UserCircleIcon,
  ComputerDesktopIcon,
  EyeIcon,
  DocumentTextIcon,
} from '@heroicons/react/24/outline';
import {
  HeartIcon as HeartIconSolid,
  BellIcon as BellIconSolid,
} from '@heroicons/react/24/solid';
import apiService from '../services/api';
import { SystemHealth, UrgencyLevel } from '../types/medical';

interface LayoutProps {
  children: React.ReactNode;
}

interface NavigationItem {
  name: string;
  href: string;
  icon: React.ComponentType<any>;
  description: string;
  badge?: string;
}

const navigation: NavigationItem[] = [
  {
    name: 'Dashboard',
    href: '/',
    icon: HomeIcon,
    description: 'Overview and quick stats'
  },
  {
    name: 'New Triage',
    href: '/triage',
    icon: ClipboardDocumentListIcon,
    description: 'Submit new triage case'
  },
  {
    name: 'Cases',
    href: '/cases',
    icon: DocumentTextIcon,
    description: 'View all triage cases'
  },
  {
    name: 'AI Chat',
    href: '/chat',
    icon: ChatBubbleLeftRightIcon,
    description: 'Chat with medical AI'
  },
  {
    name: 'Analytics',
    href: '/analytics',
    icon: ChartBarIcon,
    description: 'System performance metrics'
  },
  {
    name: 'Vision Bot',
    href: '/vision',
    icon: EyeIcon,
    description: 'Medical image analysis'
  },
  {
    name: 'System',
    href: '/system',
    icon: ComputerDesktopIcon,
    description: 'System health and settings'
  },
];

const urgencyColors = {
  [UrgencyLevel.LOW]: 'bg-green-500',
  [UrgencyLevel.MEDIUM]: 'bg-yellow-500',
  [UrgencyLevel.HIGH]: 'bg-orange-500',
  [UrgencyLevel.CRITICAL]: 'bg-red-500',
};

export default function Layout({ children }: LayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null);
  const [notifications, setNotifications] = useState<number>(0);
  const [currentTime, setCurrentTime] = useState(new Date());
  const pathname = usePathname();

  // Update current time every minute
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 60000);

    return () => clearInterval(timer);
  }, []);

  // Fetch system health periodically
  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const health = await apiService.getSystemHealth();
        setSystemHealth(health);
      } catch (error) {
        console.error('Failed to fetch system health:', error);
      }
    };

    // Initial fetch
    fetchHealth();

    // Fetch every 30 seconds
    const interval = setInterval(fetchHealth, 30000);

    return () => clearInterval(interval);
  }, []);

  const isSystemHealthy = systemHealth?.status === 'healthy';
  const currentNav = navigation.find(item => item.href === pathname);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Mobile sidebar overlay */}
      <AnimatePresence>
        {sidebarOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-40 lg:hidden"
          >
            <div
              className="fixed inset-0 bg-gray-600 bg-opacity-75"
              onClick={() => setSidebarOpen(false)}
            />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Mobile sidebar */}
      <AnimatePresence>
        {sidebarOpen && (
          <motion.div
            initial={{ x: -320 }}
            animate={{ x: 0 }}
            exit={{ x: -320 }}
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            className="fixed inset-y-0 left-0 z-50 w-80 bg-white shadow-xl lg:hidden"
          >
            <Sidebar
              navigation={navigation}
              currentPath={pathname}
              systemHealth={systemHealth}
              onClose={() => setSidebarOpen(false)}
              isMobile
            />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Desktop sidebar */}
      <div className="hidden lg:fixed lg:inset-y-0 lg:z-40 lg:flex lg:w-80 lg:flex-col">
        <Sidebar
          navigation={navigation}
          currentPath={pathname}
          systemHealth={systemHealth}
        />
      </div>

      {/* Main content */}
      <div className="lg:pl-80">
        {/* Top navigation */}
        <div className="sticky top-0 z-30 flex h-16 shrink-0 items-center gap-x-4 border-b border-gray-200 bg-white px-4 shadow-sm sm:gap-x-6 sm:px-6 lg:px-8">
          {/* Mobile menu button */}
          <button
            type="button"
            className="-m-2.5 p-2.5 text-gray-700 lg:hidden"
            onClick={() => setSidebarOpen(true)}
          >
            <span className="sr-only">Open sidebar</span>
            <Bars3Icon className="h-6 w-6" aria-hidden="true" />
          </button>

          {/* Separator */}
          <div className="h-6 w-px bg-gray-200 lg:hidden" aria-hidden="true" />

          {/* Breadcrumb */}
          <div className="flex flex-1 items-center gap-x-4 self-stretch lg:gap-x-6">
            <div className="flex items-center gap-x-2">
              <HeartIconSolid className="h-6 w-6 text-medical-600" />
              <span className="text-lg font-semibold text-gray-900">
                Medical Triage-BOTS
              </span>
              {currentNav && (
                <>
                  <span className="text-gray-400">/</span>
                  <span className="text-gray-600">{currentNav.name}</span>
                </>
              )}
            </div>

            <div className="ml-auto flex items-center gap-x-4 lg:gap-x-6">
              {/* System status indicator */}
              <div className="flex items-center gap-x-2">
                <div
                  className={`h-2 w-2 rounded-full ${
                    isSystemHealthy ? 'bg-green-500' : 'bg-red-500'
                  }`}
                />
                <span className="text-sm text-gray-600">
                  {isSystemHealthy ? 'System Healthy' : 'System Issues'}
                </span>
              </div>

              {/* Current time */}
              <div className="hidden sm:flex sm:items-center sm:gap-x-2">
                <span className="text-sm text-gray-500">
                  {currentTime.toLocaleTimeString([], {
                    hour: '2-digit',
                    minute: '2-digit'
                  })}
                </span>
              </div>

              {/* Notifications */}
              <button
                type="button"
                className="relative -m-2.5 p-2.5 text-gray-400 hover:text-gray-500"
              >
                <span className="sr-only">View notifications</span>
                {notifications > 0 ? (
                  <BellIconSolid className="h-6 w-6 text-medical-600" />
                ) : (
                  <BellIcon className="h-6 w-6" />
                )}
                {notifications > 0 && (
                  <span className="absolute -top-0.5 -right-0.5 h-4 w-4 rounded-full bg-red-500 text-xs text-white flex items-center justify-center">
                    {notifications > 9 ? '9+' : notifications}
                  </span>
                )}
              </button>

              {/* User menu */}
              <button
                type="button"
                className="-m-1.5 flex items-center p-1.5 text-gray-400 hover:text-gray-500"
              >
                <span className="sr-only">Open user menu</span>
                <UserCircleIcon className="h-8 w-8" />
              </button>
            </div>
          </div>
        </div>

        {/* Main content area */}
        <main className="py-6">
          <div className="px-4 sm:px-6 lg:px-8">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}

interface SidebarProps {
  navigation: NavigationItem[];
  currentPath: string;
  systemHealth: SystemHealth | null;
  onClose?: () => void;
  isMobile?: boolean;
}

function Sidebar({ navigation, currentPath, systemHealth, onClose, isMobile }: SidebarProps) {
  return (
    <div className="flex grow flex-col gap-y-5 overflow-y-auto bg-white px-6 pb-4 shadow-xl">
      {/* Header */}
      <div className="flex h-16 shrink-0 items-center justify-between">
        <div className="flex items-center gap-x-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg medical-gradient">
            <HeartIcon className="h-6 w-6 text-white" />
          </div>
          <div>
            <h1 className="text-lg font-semibold text-gray-900">Triage-BOTS</h1>
            <p className="text-xs text-gray-500">Medical AI System</p>
          </div>
        </div>
        {isMobile && onClose && (
          <button
            type="button"
            className="-m-2.5 p-2.5 text-gray-700"
            onClick={onClose}
          >
            <span className="sr-only">Close sidebar</span>
            <XMarkIcon className="h-6 w-6" aria-hidden="true" />
          </button>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex flex-1 flex-col">
        <ul role="list" className="flex flex-1 flex-col gap-y-7">
          <li>
            <ul role="list" className="-mx-2 space-y-1">
              {navigation.map((item) => {
                const isActive = currentPath === item.href;
                return (
                  <li key={item.name}>
                    <Link
                      href={item.href}
                      className={`group flex gap-x-3 rounded-md p-2 text-sm leading-6 font-medium transition-colors ${
                        isActive
                          ? 'bg-medical-50 text-medical-700'
                          : 'text-gray-700 hover:text-medical-700 hover:bg-gray-50'
                      }`}
                      onClick={isMobile ? onClose : undefined}
                    >
                      <item.icon
                        className={`h-6 w-6 shrink-0 transition-colors ${
                          isActive ? 'text-medical-600' : 'text-gray-400 group-hover:text-medical-600'
                        }`}
                        aria-hidden="true"
                      />
                      <div className="flex-1">
                        <div className="flex items-center justify-between">
                          <span>{item.name}</span>
                          {item.badge && (
                            <span className="ml-2 inline-flex items-center rounded-full bg-medical-100 px-2 py-1 text-xs font-medium text-medical-700">
                              {item.badge}
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-gray-500 mt-1">{item.description}</p>
                      </div>
                    </Link>
                  </li>
                );
              })}
            </ul>
          </li>

          {/* System Status */}
          <li className="mt-auto">
            <div className="rounded-lg border border-gray-200 p-4">
              <h3 className="text-sm font-medium text-gray-900 mb-3">System Status</h3>

              {systemHealth ? (
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-gray-600">Overall</span>
                    <div className="flex items-center gap-x-1">
                      <div
                        className={`h-2 w-2 rounded-full ${
                          systemHealth.status === 'healthy' ? 'bg-green-500' : 'bg-red-500'
                        }`}
                      />
                      <span className="text-xs font-medium">
                        {systemHealth.status === 'healthy' ? 'Healthy' : 'Issues'}
                      </span>
                    </div>
                  </div>

                  {systemHealth.components && (
                    <div className="space-y-1">
                      {Object.entries(systemHealth.components).map(([component, status]) => (
                        <div key={component} className="flex items-center justify-between">
                          <span className="text-xs text-gray-500 capitalize">
                            {component.replace('_', ' ')}
                          </span>
                          <div className="flex items-center gap-x-1">
                            <div
                              className={`h-1.5 w-1.5 rounded-full ${
                                status === 'operational' ? 'bg-green-400' : 'bg-red-400'
                              }`}
                            />
                            <span className="text-xs text-gray-600">
                              {status === 'operational' ? 'OK' : 'Error'}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ) : (
                <div className="flex items-center justify-center py-2">
                  <div className="spinner-sm" />
                  <span className="ml-2 text-xs text-gray-500">Checking...</span>
                </div>
              )}
            </div>
          </li>
        </ul>
      </nav>
    </div>
  );
}
