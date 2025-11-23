import { create } from 'zustand';

export interface DNSLog {
  id: string;
  timestamp: string;
  domain: string;
  type: string;
  rcode: string;
  latency: number;
}

interface DNSState {
  logs: DNSLog[];
  stats: {
    totalQueries: number;
    avgLatency: number;
    cacheHitRate: number;
    errorRate: number;
  };
  isLoading: boolean;
  setData: (rawLogs: any[]) => void;
}

export const useDNSStore = create<DNSState>((set) => ({
  logs: [],
  stats: { totalQueries: 0, avgLatency: 0, cacheHitRate: 0, errorRate: 0 },
  isLoading: false,
  
  setData: (rawLogs: any[]) => {
    // Transform raw data to DNSLog format
    const logs: DNSLog[] = rawLogs.map((item) => ({
      id: item.id,
      timestamp: item.timestamp,
      domain: item.domain,
      type: item.query_type,
      rcode: item.rcode,
      latency: item.latency_ms,
    }));

    // Calculate stats
    const totalQueries = logs.length;
    const latencies = logs.map(log => log.latency).filter(latency => latency !== null && latency !== undefined);
    const avgLatency = latencies.length > 0 ? Math.round(sum(latencies) / latencies.length) : 0;
    const cacheHits = rawLogs.filter(item => item.cached).length;
    const cacheHitRate = totalQueries > 0 ? Math.round((cacheHits / totalQueries) * 100 * 10) / 10 : 0;
    const errors = logs.filter(log => log.rcode !== 'NOERROR').length;
    const errorRate = totalQueries > 0 ? Math.round((errors / totalQueries) * 100 * 10) / 10 : 0;

    const stats = {
      totalQueries,
      avgLatency,
      cacheHitRate,
      errorRate,
    };

    set({ logs, stats });
  },
}));

// Helper function for sum
function sum(numbers: number[]): number {
  return numbers.reduce((acc, curr) => acc + curr, 0);
}
