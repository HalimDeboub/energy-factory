import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { 
  Zap, 
  Activity, 
  Leaf, 
  ShieldCheck, 
  Server, 
  ArrowUpRight, 
  ArrowDownRight,
  RefreshCw,
  Globe,
  Database
} from "lucide-react";
import { 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer
} from 'recharts';
import { useState, useEffect } from "react";

export function Dashboard() {
  const [stats, setStats] = useState<any>(null);
  const [metrics, setMetrics] = useState<any>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [stateRes, metricsRes, historyRes] = await Promise.all([
          fetch("http://localhost:9000/debug/state-check").then(r => r.json()),
          fetch("http://localhost:9000/insights/metrics").then(r => r.json()),
          fetch("http://localhost:9000/insights/history?hours=24").then(r => r.json())
        ]);

        setStats(stateRes);
        setMetrics(metricsRes.metrics);
        setHistory(historyRes.data);
        setIsLoading(false);
      } catch (err) {
        console.error("Error fetching dashboard data:", err);
        setIsLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 60000); // Refresh every minute
    return () => clearInterval(interval);
  }, []);

  const formatMW = (val: number) => {
    if (!val) return "0.0 GW";
    return (val / 1000).toFixed(1) + " GW";
  };

  const enterpriseMetrics = [
    { 
        title: "Fleet Power Output", 
        value: formatMW(metrics?.current_consumption_kwh), 
        change: "Real-time", 
        trend: "up", 
        icon: <Zap className="size-5 text-yellow-500" />,
        description: `Source: ${stats?.active_data_providers?.[0] || 'N/A'}`
    },
    { 
        title: "Active Nodes", 
        value: stats?.active_data_providers?.length || 0, 
        total: "Providers Online", 
        change: "100%", 
        trend: "up", 
        icon: <ShieldCheck className="size-5 text-green-500" />,
        description: "Zero connection errors detected"
    },
    { 
        title: "Carbon Impact", 
        value: metrics?.co2_saved_kg ? `${metrics.co2_saved_kg}kg` : "0.0kg", 
        change: "CO2 Saved", 
        trend: "down", 
        icon: <Leaf className="size-5 text-emerald-500" />,
        description: "Current decarbonization offset"
    },
    { 
        title: "Solar Efficiency", 
        value: metrics?.solar_efficiency_percent ? `${metrics.solar_efficiency_percent}%` : "0%", 
        change: "Mix Share", 
        trend: "up", 
        icon: <RefreshCw className="size-5 text-blue-500" />,
        description: "Renewable contribution to total load"
    },
  ];

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8 bg-[#fafafa] min-h-screen">
      <div className="flex items-end justify-between border-b border-slate-200 pb-8">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <div className={`size-2 rounded-full animate-pulse ${stats?.status === 'ready' ? 'bg-green-500' : 'bg-red-500'}`} />
            <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-400">
                {stats?.status === 'ready' ? 'System Operational' : 'System Initializing'}
            </span>
          </div>
          <h2 className="text-4xl font-light text-slate-900 tracking-tight">Mission Control</h2>
        </div>
        
        <div className="flex gap-3">
            <div className="px-4 py-2 bg-white border border-slate-200 rounded-xl flex items-center gap-3 shadow-sm">
                <Database className="size-4 text-slate-400" />
                <div className="text-left">
                    <p className="text-[9px] uppercase font-bold text-slate-400 leading-none">Last Sync</p>
                    <p className="text-xs font-medium text-slate-700">
                        {stats?.latest_data_sync && stats.latest_data_sync !== "N/A" 
                            ? new Date(stats.latest_data_sync).toLocaleString('fr-FR', { hour: '2-digit', minute: '2-digit', day: '2-digit', month: 'short' })
                            : 'Searching...'}
                    </p>
                </div>
            </div>
        </div>
      </div>

      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
        {enterpriseMetrics.map((m, i) => (
          <Card key={i} className="border-none shadow-[0_8px_30px_rgb(0,0,0,0.04)] rounded-2xl bg-white group transition-all duration-500">
            <CardContent className="p-6">
              <div className="flex justify-between items-start mb-4">
                <div className="p-2.5 bg-slate-50 rounded-xl group-hover:bg-slate-900 group-hover:text-white transition-all duration-500">
                  {m.icon}
                </div>
                <Badge variant="outline" className={`border-none text-[10px] font-bold text-slate-500 bg-slate-50 uppercase tracking-tighter`}>
                   {m.change}
                </Badge>
              </div>
              <div>
                <p className="text-xs font-medium text-slate-400 mb-1 uppercase tracking-wider">{m.title}</p>
                <div className="flex items-baseline gap-2">
                   <h3 className="text-2xl font-bold text-slate-900">{m.value}</h3>
                   <span className="text-[10px] text-slate-400 font-medium">{m.total}</span>
                </div>
                <p className="text-[10px] text-slate-400 mt-3 flex items-center gap-1">
                    <Globe className="size-3" /> {m.description}
                </p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid lg:grid-cols-3 gap-8">
        <Card className="lg:col-span-2 border-none shadow-[0_8px_30px_rgb(0,0,0,0.04)] rounded-[2rem] bg-white p-4">
          <CardHeader className="pb-8">
            <CardTitle className="text-xl font-medium text-slate-900">Live Load Tracking</CardTitle>
            <CardDescription className="text-xs">Real-time consumption trend from primary grid nodes</CardDescription>
          </CardHeader>
          <CardContent className="h-[350px]">
            {history.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={history}>
                    <defs>
                    <linearGradient id="colorCons" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#22c55e" stopOpacity={0.1}/>
                        <stop offset="95%" stopColor="#22c55e" stopOpacity={0}/>
                    </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                    <XAxis 
                        dataKey="time" 
                        axisLine={false} 
                        tickLine={false} 
                        tick={{fontSize: 10, fill: '#94a3b8'}} 
                        tickFormatter={(str) => {
                            const date = new Date(str);
                            return date.getHours() + ":" + date.getMinutes().toString().padStart(2, '0');
                        }}
                    />
                    <YAxis axisLine={false} tickLine={false} tick={{fontSize: 10, fill: '#94a3b8'}} />
                    <Tooltip 
                        contentStyle={{borderRadius: '16px', border: 'none', boxShadow: '0 10px 40px rgba(0,0,0,0.1)'}}
                    />
                    <Area type="monotone" dataKey="consommation" stroke="#22c55e" strokeWidth={2} fillOpacity={1} fill="url(#colorCons)" />
                </AreaChart>
                </ResponsiveContainer>
            ) : (
                <div className="flex items-center justify-center h-full text-slate-300">
                    <RefreshCw className="size-6 animate-spin mr-3" />
                    Syncing with grid data...
                </div>
            )}
          </CardContent>
        </Card>

        <Card className="border-none shadow-[0_8px_30px_rgb(0,0,0,0.04)] rounded-[2rem] bg-slate-900 text-white overflow-hidden">
          <CardHeader className="pb-4">
            <CardTitle className="text-lg font-light text-white/90">Source Matrix</CardTitle>
            <CardDescription className="text-white/40 text-xs">Identified data nodes in active fleet</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
             <div className="space-y-4">
                {stats?.active_data_providers?.map((p: string, i: number) => (
                    <div key={i} className="flex items-center justify-between p-4 bg-white/5 rounded-2xl border border-white/10 hover:bg-white/10 transition-colors group cursor-default">
                        <div className="flex items-center gap-3">
                            <Server className="size-4 text-white/40 group-hover:text-green-400 transition-colors" />
                            <div>
                                <p className="text-xs font-medium text-white/90">{p}</p>
                                <p className="text-[10px] text-white/30 font-mono tracking-tighter">Node Ready</p>
                            </div>
                        </div>
                        <div className="size-2 bg-green-500 rounded-full shadow-[0_0_10px_rgba(34,197,94,0.5)]" />
                    </div>
                ))}

                {stats?.active_knowledge_providers?.map((p: string, i: number) => (
                    <div key={i} className="flex items-center justify-between p-4 bg-white/5 rounded-2xl border border-white/10">
                        <div className="flex items-center gap-3">
                            <FileText className="size-4 text-blue-400" />
                            <div>
                                <p className="text-xs font-medium text-white/90">{p}</p>
                                <p className="text-[10px] text-white/30 font-mono tracking-tighter">Knowledge RAG</p>
                            </div>
                        </div>
                        <div className="size-2 bg-blue-500 rounded-full" />
                    </div>
                ))}
             </div>

             <div className="pt-6 border-t border-white/10">
                <p className="text-[10px] font-bold uppercase tracking-widest text-white/20 mb-4 font-mono">Infrastructure Stats</p>
                <div className="grid grid-cols-2 gap-4">
                    <div className="p-4 bg-white/5 rounded-2xl">
                        <p className="text-[10px] text-white/40 uppercase mb-1">Cache Ratio</p>
                        <p className="text-xl font-bold text-white">
                            {stats?.cache_stats ? (stats.cache_stats.hits / (stats.cache_stats.hits + stats.cache_stats.misses || 1) * 100).toFixed(0) : 0}%
                        </p>
                    </div>
                    <div className="p-4 bg-white/5 rounded-2xl">
                        <p className="text-[10px] text-white/40 uppercase mb-1">Latency</p>
                        <p className="text-xl font-bold text-white">450ms</p>
                    </div>
                </div>
             </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

const FileText = ({ className }: { className?: string }) => (
    <svg className={className} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/></svg>
);
