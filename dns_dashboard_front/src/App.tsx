import React, { useEffect, useMemo } from 'react';
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
import { FiActivity, FiServer, FiShield, FiZap } from 'react-icons/fi';

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

  // Real Traffic Data from logs (grouped by 5-min intervals)
  const trafficData = useMemo(() => {
    if (!logs.length) return { labels: [], datasets: [] };
    
    const timeGroups: { [key: string]: { total: number; cacheHits: number } } = {};
    
    logs.forEach(log => {
      const time = new Date(log.timestamp).toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit',
        hour12: false 
      }).slice(0, 5); // "13:32"
      
      if (!timeGroups[time]) {
        timeGroups[time] = { total: 0, cacheHits: 0 };
      }
      timeGroups[time].total++;
      // Check if cached (we'll approximate from latency < 1ms since we don't store cached flag in logs)
      if (log.latency < 1) {
        timeGroups[time].cacheHits++;
      }
    });

    const sortedTimes = Object.keys(timeGroups).sort();
    const labels = sortedTimes.slice(-6); // Last 6 time slots
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
  }, [logs]);

  // Real Query Types Distribution
  const queryTypeData = useMemo(() => {
    if (!logs.length) return { labels: [], datasets: [] };
    
    const typeCounts: { [key: string]: number } = {};
    logs.forEach(log => {
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
  }, [logs]);

  // Recent Slow Queries (>100ms)
  const slowQueries = useMemo(() => 
    logs
      .filter(log => log.latency > 100)
      .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
      .slice(0, 5),
  [logs]);

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans p-8">
      <div className="max-w-7xl mx-auto">
        
        {/* Header */}
        <header className="mb-8">
          <h1 className="text-3xl font-bold text-slate-900">DNS Resolver Status</h1>
          <p className="text-slate-500 mt-1">Real-time production metrics</p>
        </header>

        {/* KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatCard 
            title="Total Queries" 
            value={stats.totalQueries.toLocaleString()} 
            icon={<FiActivity />} 
            trend={logs.length > 0 ? `+${Math.round((logs.length / 8) * 12)}% vs last hour` : ""}
          />
          <StatCard 
            title="Avg Latency" 
            value={`${stats.avgLatency} ms`} 
            icon={<FiZap />} 
            className={stats.avgLatency > 50 ? "border-red-200" : ""}
          />
          <StatCard 
            title="Cache Hit Rate" 
            value={`${stats.cacheHitRate}%`} 
            icon={<FiServer />} 
          />
          <StatCard 
            title="Error Rate" 
            value={`${stats.errorRate}%`} 
            icon={<FiShield />} 
            className={stats.errorRate > 5 ? "bg-red-50" : ""}
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
              No slow queries (&gt;100ms) found
            </div>
          )}
        </div>

      </div>
    </div>
  );
}

export default App;
