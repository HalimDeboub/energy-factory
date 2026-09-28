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
  Database,
  Wind,
  Sun,
  Flame,
  Battery,
  FileText
} from "lucide-react";
import { 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  Legend
} from 'recharts';
import { useState, useEffect } from "react";
import { toast } from "react-hot-toast";

export function Dashboard() {
  const [stats, setStats] = useState<any>(null);
  const [metrics, setMetrics] = useState<any>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      const token = localStorage.getItem("token");
      const headers = {
        "Authorization": `Bearer ${token}`
      };

      try {
        const [stateRes, metricsRes, historyRes] = await Promise.all([
          fetch("http://localhost:9000/debug/state-check", { headers }).then(r => r.json()),
          fetch("http://localhost:9000/insights/metrics", { headers }).then(r => r.json()),
          fetch("http://localhost:9000/insights/history?hours=24", { headers }).then(r => r.json())
        ]);

        if (stateRes) setStats(stateRes);
        if (metricsRes && metricsRes.metrics) setMetrics(metricsRes.metrics);
        if (historyRes && historyRes.data) setHistory(historyRes.data);
        
        setIsLoading(false);
      } catch (err) {
        console.error("Error fetching dashboard data:", err);
        toast.error("Dashboard sync failed. Reconnecting...");
        setIsLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 60000); // Refresh every minute
    return () => clearInterval(interval);
  }, []);

  const formatMW = (val: number) => {
    if (val === undefined || val === null) return "0.0 MW";
    if (val >= 1000) return (val / 1000).toFixed(1) + " GW";
    return val.toFixed(1) + " MW";
  };

  const enterpriseMetrics = [
    { 
        title: "Current Demand", 
        value: formatMW(metrics?.current_consumption_kwh), 
        change: "Total Load", 
        trend: "up", 
        icon: <Zap className="size-5 text-yellow-500" />,
        description: `Active Source: ${stats?.active_data_providers?.[0] || 'None'}`
    },
    { 
        title: "Decarbonization", 
        value: metrics?.co2_saved_kg ? `${metrics.co2_saved_kg}kg` : "0.0kg", 
        change: "CO2 Saved", 
        trend: "down", 
        icon: <Leaf className="size-5 text-emerald-500" />,
        description: "Carbon intensity offset vs baseline"
    },
    { 
        title: "Clean Energy Mix", 
        value: metrics?.solar_efficiency_percent ? `${metrics.solar_efficiency_percent}%` : "0%", 
        change: "Green Share", 
        trend: "up", 
        icon: <RefreshCw className="size-5 text-blue-500" />,
        description: "Renewable contribution to current load"
    },
    { 
        title: "Infrastructure", 
        value: stats?.active_data_providers?.length || 0, 
        total: "Nodes Online", 
        change: "Operational", 
        trend: "up", 
        icon: <ShieldCheck className="size-5 text-emerald-500" />,
        description: `${stats?.active_knowledge_providers?.length || 0} Knowledge RAGs connected`
    },
  ];

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8 bg-[#fafafa] min-h-screen">
      {/* Header */}
      <div className="flex items-end justify-between border-b border-slate-200 pb-8">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <div className={`size-2 rounded-full animate-pulse ${stats?.status === 'ready' ? 'bg-green-500' : 'bg-red-500'}`} />
            <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-400">
                {stats?.status === 'ready' ? 'System Operational' : 'System Initializing'}
            </span>
          </div>
          <h2 className="text-4xl font-light text-slate-900 tracking-tight">Energy Intelligence</h2>
        </div>
        
        <div className="flex gap-3">
            <div className="px-4 py-2 bg-white border border-slate-200 rounded-xl flex items-center gap-3 shadow-sm">
                <Database className="size-4 text-slate-400" />
                <div className="text-left">
                    <p className="text-[9px] uppercase font-bold text-slate-400 leading-none">Last Data Sync</p>
                    <p className="text-xs font-medium text-slate-700">
                        {stats?.latest_data_sync && stats.latest_data_sync !== "N/A" 
                            ? new Date(stats.latest_data_sync).toLocaleString('fr-FR', { hour: '2-digit', minute: '2-digit', day: '2-digit', month: 'short' })
                            : 'Scanning...'}
                    </p>
                </div>
            </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
        {enterpriseMetrics.map((m, i) => (
          <Card key={i} className="border-none shadow-[0_8px_30px_rgb(0,0,0,0.02)] rounded-2xl bg-white group transition-all duration-500 hover:shadow-lg">
            <CardContent className="p-6">
              <div className="flex justify-between items-start mb-4">
                <div className="p-2.5 bg-emerald-50 rounded-xl group-hover:bg-emerald-600 group-hover:text-white transition-all duration-500 text-emerald-600">
                  {m.icon}
                </div>
                <Badge variant="outline" className="border-none text-[10px] font-bold text-emerald-600 bg-emerald-50 uppercase tracking-tighter">
                   {m.change}
                </Badge>
              </div>
              <div>
                <p className="text-xs font-medium text-slate-400 mb-1 uppercase tracking-wider">{m.title}</p>
                <div className="flex items-baseline gap-2">
                   <h3 className="text-2xl font-bold text-slate-700">{m.value}</h3>
                   {m.total && <span className="text-[10px] text-slate-400 font-medium">{m.total}</span>}
                </div>
                <p className="text-[10px] text-slate-400 mt-3 flex items-center gap-1">
                    <Globe className="size-3 text-emerald-400" /> {m.description}
                </p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid lg:grid-cols-3 gap-8">
        {/* Main Chart */}
        <Card className="lg:col-span-2 border-none shadow-[0_8px_30px_rgb(0,0,0,0.02)] rounded-[2rem] bg-white p-4">
          <CardHeader className="pb-8">
            <CardTitle className="text-xl font-medium text-slate-700">Energy Generation & Demand</CardTitle>
            <CardDescription className="text-xs text-slate-400">Real-time mapping across all connected data nodes (24h period)</CardDescription>
          </CardHeader>
          <CardContent className="h-[400px]">
            {history && history.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={history}>
                    <defs>
                      <linearGradient id="colorCons" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#10b981" stopOpacity={0.1}/>
                          <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                      </linearGradient>
                      <linearGradient id="colorSolar" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#fbbf24" stopOpacity={0.1}/>
                          <stop offset="95%" stopColor="#fbbf24" stopOpacity={0}/>
                      </linearGradient>
                      <linearGradient id="colorWind" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.1}/>
                          <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
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
                    <YAxis axisLine={false} tickLine={false} tick={{fontSize: 10, fill: '#94a3b8'}} unit=" MW" />
                    <Tooltip 
                        contentStyle={{borderRadius: '16px', border: 'none', boxShadow: '0 10px 40px rgba(0,0,0,0.05)', backgroundColor: 'rgba(255,255,255,0.95)'}}
                    />
                    <Legend verticalAlign="top" height={36} iconType="circle" wrapperStyle={{fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em'}} />
                    <Area type="monotone" name="Demand" dataKey="consumption_mw" stroke="#10b981" strokeWidth={3} fillOpacity={1} fill="url(#colorCons)" />
                    <Area type="monotone" name="Solar" dataKey="solar_mw" stroke="#fbbf24" strokeWidth={2} fillOpacity={1} fill="url(#colorSolar)" />
                    <Area type="monotone" name="Wind" dataKey="wind_mw" stroke="#3b82f6" strokeWidth={2} fillOpacity={1} fill="url(#colorWind)" />
                    <Area type="monotone" name="Gas" dataKey="gas_mw" stroke="#94a3b8" strokeWidth={1} fillOpacity={0} />
                </AreaChart>
                </ResponsiveContainer>
            ) : (
                <div className="flex items-center justify-center h-full text-emerald-100 font-light">
                    <RefreshCw className="size-6 animate-spin mr-3 text-emerald-400" />
                    Analyzing grid telemetry...
                </div>
            )}
          </CardContent>
        </Card>

        {/* Source Matrix */}
        <Card className="border-none shadow-[0_8px_30px_rgb(16,185,129,0.05)] rounded-[2rem] bg-emerald-950 text-white overflow-hidden">
          <CardHeader className="pb-4">
            <CardTitle className="text-lg font-light text-white/90">Source Matrix</CardTitle>
            <CardDescription className="text-white/40 text-xs">Identified infrastructure nodes</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
             <div className="space-y-4 max-h-[300px] overflow-y-auto pr-1">
                {stats?.active_data_providers?.map((p: string, i: number) => (
                    <div key={i} className="flex items-center justify-between p-4 bg-white/5 rounded-2xl border border-white/5 hover:bg-white/10 transition-colors group cursor-default">
                        <div className="flex items-center gap-3">
                            <Server className="size-4 text-emerald-400/60 group-hover:text-emerald-400 transition-colors" />
                            <div>
                                <p className="text-xs font-medium text-white/90">{p}</p>
                                <p className="text-[10px] text-white/20 font-mono tracking-tighter uppercase">Data Stream Active</p>
                            </div>
                        </div>
                        <div className="size-2 bg-emerald-500 rounded-full shadow-[0_0_10px_rgba(16,185,129,0.5)]" />
                    </div>
                ))}

                {stats?.active_knowledge_providers?.map((p: string, i: number) => (
                    <div key={i} className="flex items-center justify-between p-4 bg-white/5 rounded-2xl border border-white/5 hover:bg-white/10 transition-colors group cursor-default">
                        <div className="flex items-center gap-3">
                            <FileText className="size-4 text-teal-400 group-hover:text-teal-300" />
                            <div>
                                <p className="text-xs font-medium text-white/90">{p}</p>
                                <p className="text-[10px] text-white/20 font-mono tracking-tighter uppercase">Knowledge RAG Indexed</p>
                            </div>
                        </div>
                        <div className="size-2 bg-teal-500 rounded-full" />
                    </div>
                ))}
             </div>

             <div className="pt-6 border-t border-white/5">
                <p className="text-[10px] font-bold uppercase tracking-widest text-white/20 mb-4 font-mono">Real-time Performance</p>
                <div className="grid grid-cols-2 gap-4">
                    <div className="p-4 bg-white/5 rounded-2xl">
                        <p className="text-[10px] text-white/30 uppercase mb-1">RAG Context Size</p>
                        <p className="text-xl font-bold text-white">4.2k tokens</p>
                    </div>
                    <div className="p-4 bg-white/5 rounded-2xl">
                        <p className="text-[10px] text-white/30 uppercase mb-1">Inference Latency</p>
                        <p className="text-xl font-bold text-white">1.2s</p>
                    </div>
                </div>
             </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

