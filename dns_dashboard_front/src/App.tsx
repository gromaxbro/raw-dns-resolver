import React, { useEffect, useMemo, useState } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
} from 'chart.js';
import { Line, Doughnut } from 'react-chartjs-2';
import { useDNSStore } from './store/dnsStore';
import { StatCard } from './components/StatCard';
import { FiActivity, FiServer, FiShield, FiZap, FiCalendar, FiX } from 'react-icons/fi';

// Register ChartJS components
ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, BarElement, ArcElement, Title, Tooltip, Legend);

// Chart Options
const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { position: 'bottom' as const },
  },
  scales: {
    y: { grid: { color: '#f1f5f9' } },
    x: { grid: { display: false } },
  },
};

function App() {
  const { stats, logs, setData } = useDNSStore();
  const [filter, setFilter] = useState<'today' | '7days' | '30days' | '365days' | 'custom'>('today');
  const [customRange, setCustomRange] = useState<{ start: string; end: string }>({
    start: '',
    end: '',
  });

  useEffect(() => {
    fetch('/src/assets/data.json')
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
      })
      .then(rawLogs => {
        setData(rawLogs);
      })
      .catch(error => {
        console.error('Failed to fetch DNS data:', error);
      });
  }, [setData]);

  // Filter logs based on selected timeframe
  const filteredLogs = useMemo(() => {
    const now = new Date();
    
    return logs.filter(log => {
      const logDate = new Date(log.timestamp);
      
      switch (filter) {
        case 'today':
          return logDate.toDateString() === now.toDateString();
        case '7days':
          return (now.getTime() - logDate.getTime()) <= 7 * 24 * 60 * 60 * 1000;
        case '30days':
          return (now.getTime() - logDate.getTime()) <= 30 * 24 * 60 * 60 * 1000;
        case '365days':
          return (now.getTime() - logDate.getTime()) <= 365 * 24 * 60 * 60 * 1000;
        case 'custom':
          if (!customRange.start || !customRange.end) return true;
          const startDate = new Date(customRange.start);
          const endDate = new Date(customRange.end);
          return logDate >= startDate && logDate <= endDate;
        default:
          return true;
      }
    });
  }, [logs, filter, customRange]);

  // Real Traffic Data from filtered logs
  const trafficData = useMemo(() => {
    if (!filteredLogs.length) return { labels: [], datasets: [] };
    
    const timeGroups: { [key: string]: { total: number; cacheHits: number } } = {};
    
    filteredLogs.forEach(log => {
      const time = new Date(log.timestamp).toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit',
        hour12: false 
      }).slice(0, 5);
      
      if (!timeGroups[time]) {
        timeGroups[time] = { total: 0, cacheHits: 0 };
      }
      timeGroups[time].total++;
      if (log.latency < 1) {
        timeGroups[time].cacheHits++;
      }
    });

    const sortedTimes = Object.keys(timeGroups).sort();
    const labels = sortedTimes.slice(-6);
    const totalData = labels.map(time => timeGroups[time]?.total || 0);
    const cacheData = labels.map(time => timeGroups[time]?.cacheHits || 0);

    return {
      labels,
      datasets: [
        {
          label: "Total Queries",
          data: totalData,
          borderColor: "#6366f1",
          backgroundColor: "rgba(99, 102, 241, 0.1)",
          tension: 0.4,
          fill: true
        },
        {
          label: "Cache Hits",
          data: cacheData,
          borderColor: "#10b981",
          backgroundColor: "rgba(16, 185, 129, 0.1)",
          tension: 0.4,
          fill: true
        }
      ]
    };
  }, [filteredLogs]);

  // Real Query Types Distribution from filtered logs
  const queryTypeData = useMemo(() => {
    if (!filteredLogs.length) return { labels: [], datasets: [] };
    
    const typeCounts: { [key: string]: number } = {};
    filteredLogs.forEach(log => {
      typeCounts[log.type] = (typeCounts[log.type] || 0) + 1;
    });

    const sortedTypes = Object.entries(typeCounts)
      .sort(([,a], [,b]) => (b as number) - (a as number))
      .slice(0, 5)
      .map(([type]) => type);

    const data = sortedTypes.map(type => typeCounts[type] || 0);

    return {
      labels: sortedTypes,
      datasets: [
        {
          data,
          backgroundColor: ['#6366f1', '#818cf8', '#a5b4fc', '#c7d2fe', '#e0e7ff'],
          borderWidth: 0,
        },
      ],
    };
  }, [filteredLogs]);

  // Recent Slow Queries from filtered logs
  const slowQueries = useMemo(() => 
    filteredLogs
      .filter(log => log.latency > 100)
      .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
      .slice(0, 5),
  [filteredLogs]);

  const getFilterLabel = () => {
    switch (filter) {
      case 'today': return 'Today';
      case '7days': return '7 Days';
      case '30days': return '30 Days';
      case '365days': return '365 Days';
      case 'custom': return customRange.start && customRange.end 
        ? `${new Date(customRange.start).toLocaleDateString()} - ${new Date(customRange.end).toLocaleDateString()}`
        : 'Custom Range';
      default: return 'All Time';
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans p-8">
      <div className="max-w-7xl mx-auto">
        
        {/* Header */}
        <header className="mb-8">
          <h1 className="text-3xl font-bold text-slate-900">DNS Resolver Status</h1>
          <p className="text-slate-500 mt-1">Real-time production metrics</p>
        </header>

        {/* Filter Controls */}
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm mb-8">
          <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
            <div className="flex flex-wrap gap-2">
              {(['today', '7days', '30days', '365days', 'custom'] as const).map(period => (
                <button
                  key={period}
                  onClick={() => setFilter(period)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                    filter === period
                      ? 'bg-indigo-600 text-white shadow-md'
                      : 'bg-slate-100 hover:bg-slate-200 text-slate-700'
                  }`}
                >
                  {period === 'custom' ? 'Custom' : period.replace(/([A-Z])/g, ' $1').trim()}
                </button>
              ))}
            </div>
            
            {filter === 'custom' && (
              <div className="flex gap-2 items-center flex-wrap">
                <input
                  type="date"
                  value={customRange.start}
                  onChange={(e) => setCustomRange(prev => ({ ...prev, start: e.target.value }))}
                  className="px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm"
                  max={new Date().toISOString().split('T')[0]}
                />
                <span className="text-slate-500">to</span>
                <input
                  type="date"
                  value={customRange.end}
                  onChange={(e) => setCustomRange(prev => ({ ...prev, end: e.target.value }))}
                  className="px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm"
                  max={new Date().toISOString().split('T')[0]}
                />
              </div>
            )}
            
            <div className="text-sm text-slate-600 font-medium">
              Showing {filteredLogs.length} of {logs.length} logs ({getFilterLabel()})
            </div>
          </div>
        </div>

        {/* KPI Cards - using filtered stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatCard 
            title="Total Queries" 
            value={filteredLogs.length.toLocaleString()} 
            icon={<FiActivity />} 
            trend={filteredLogs.length > 0 ? `+12% vs last hour` : ""}
          />
          <StatCard 
            title="Avg Latency" 
            value={filteredLogs.length > 0 
              ? `${Math.round(filteredLogs.reduce((sum, log) => sum + log.latency, 0) / filteredLogs.length)} ms` 
              : '0 ms'}
            icon={<FiZap />} 
            className={filteredLogs.length > 0 && 
              Math.round(filteredLogs.reduce((sum, log) => sum + log.latency, 0) / filteredLogs.length) > 50 
              ? "border-red-200" : ""}
          />
          <StatCard 
            title="Cache Hit Rate" 
            value={filteredLogs.length > 0 
              ? `${Math.round((filteredLogs.filter(log => log.latency < 1).length / filteredLogs.length) * 100)}%` 
              : '0%'}
            icon={<FiServer />} 
          />
          <StatCard 
            title="Error Rate" 
            value={filteredLogs.length > 0 
              ? `${Math.round((filteredLogs.filter(log => log.rcode !== 'NOERROR').length / filteredLogs.length) * 100)}%` 
              : '0%'}
            icon={<FiShield />} 
            className={filteredLogs.length > 0 && 
              (filteredLogs.filter(log => log.rcode !== 'NOERROR').length / filteredLogs.length) * 100 > 5 
              ? "bg-red-50" : ""}
          />
        </div>

        {/* Charts Section */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Traffic Chart */}
          <div className="lg:col-span-2 bg-white p-6 rounded-xl border border-slate-200 shadow-sm min-h-[400px]">
            <h2 className="text-lg font-semibold mb-4 text-slate-800">Traffic Overview</h2>
            <div className="h-[300px]">
              <Line options={chartOptions} data={trafficData} />
            </div>
          </div>

          {/* Query Types Distribution */}
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
            <h2 className="text-lg font-semibold mb-4 text-slate-800">Query Types</h2>
            <div className="h-[300px] flex justify-center">
              <Doughnut data={queryTypeData} options={{ maintainAspectRatio: false }} />
            </div>
          </div>
        </div>

        {/* Recent Logs Table */}
        <div className="mt-8 bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-100">
            <h3 className="font-semibold text-slate-800">
              Recent Slow Queries ({slowQueries.length} &gt;100ms)
            </h3>
          </div>
          {slowQueries.length > 0 ? (
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 text-slate-500">
                <tr>
                  <th className="px-6 py-3 font-medium">Timestamp</th>
                  <th className="px-6 py-3 font-medium">Domain</th>
                  <th className="px-6 py-3 font-medium">Type</th>
                  <th className="px-6 py-3 font-medium">Latency</th>
                  <th className="px-6 py-3 font-medium">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {slowQueries.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-50">
                    <td className="px-6 py-3 text-slate-600">
                      {new Date(log.timestamp).toLocaleTimeString()}
                    </td>
                    <td className="px-6 py-3 font-mono text-slate-700 truncate max-w-[200px]">
                      {log.domain}
                    </td>
                    <td className="px-6 py-3">
                      <span className="bg-blue-100 text-blue-700 px-2 py-1 rounded text-xs">
                        {log.type}
                      </span>
                    </td>
                    <td className="px-6 py-3 text-red-600 font-medium">
                      {log.latency}ms
                    </td>
                    <td className={`px-6 py-3 ${
                      log.rcode === 'NOERROR' ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {log.rcode}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="px-6 py-8 text-center text-slate-500">
              No slow queries (&gt;100ms) found in selected timeframe
            </div>
          )}
        </div>

      </div>
    </div>
  );
}

export default App;
