import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, LineChart, Line } from "recharts";
import { Download, Calendar, FileText, Sparkles, TrendingUp, Zap, Clock } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { useState, useEffect } from "react";
import { toast } from "react-hot-toast";

export function Reports() {
  const [aiSummary, setAiSummary] = useState<string>("");
  const [history, setHistory] = useState<any[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      const token = localStorage.getItem("token");
      if (!token) {
        toast.error("Session expired. Please log in again.");
        return;
      }

      const headers = {
        "Authorization": `Bearer ${token}`
      };

      // Fetch historical data for charts
      try {
        console.log("📊 Reports: Fetching 7-day history...");
        const res = await fetch("http://localhost:9000/insights/history?hours=168", { headers });
        
        if (res.status === 401) {
          toast.error("Authentication failed. Please re-login.");
          return;
        }

        const data = await res.json();
        if (data && data.data) {
            setHistory(data.data);
        }
      } catch (err) {
        console.error("Error fetching history:", err);
      }

      // Initial AI Summary
      generateAISummary();
    };

    fetchData();
  }, []);

  const generateAISummary = async () => {
    const token = localStorage.getItem("token");
    if (!token) return;

    setIsGenerating(true);
    const headers = {
      "Authorization": `Bearer ${token}`
    };

    try {
      console.log("🤖 Reports: Generating AI Strategic Summary...");
      const res = await fetch("http://localhost:9000/reports/ai-summary", { headers });
      
      if (!res.ok) {
          if (res.status === 401) throw new Error("Unauthorized");
          throw new Error("Server error during synthesis");
      }
      
      const data = await res.json();
      setAiSummary(data.summary);
    } catch (err: any) {
      console.error("Error generating AI summary:", err);
      setAiSummary("Failed to generate strategic analysis. Please verify AI agent status.");
      if (err.message === "Unauthorized") {
          toast.error("Session invalid. Re-login required.");
      } else {
          toast.error("Intelligence Agent unreachable.");
      }
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8 bg-[#fafafa] min-h-screen">
      {/* Header Area */}
      <div className="flex items-end justify-between border-b border-emerald-100 pb-8">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-emerald-600">
                Strategic Intelligence
            </span>
          </div>
          <h2 className="text-4xl font-light text-slate-700 tracking-tight">Executive Reports</h2>
        </div>
        
        <div className="flex gap-3">
            <Button variant="outline" className="rounded-xl border-emerald-100 bg-white shadow-sm hover:bg-emerald-50 text-emerald-600">
                <Calendar className="size-4 mr-2" />
                Select Period
            </Button>
            <Button className="rounded-xl bg-emerald-600 text-white shadow-lg shadow-emerald-100 hover:bg-emerald-700 transition-all border-none">
                <Download className="size-4 mr-2" />
                Export PDF
            </Button>
        </div>
      </div>

      <div className="grid lg:grid-cols-3 gap-8">
        {/* Left Column: AI Strategic Summary */}
        <div className="lg:col-span-1 space-y-8">
            <Card className="border-none shadow-[0_8px_30px_rgb(16,185,129,0.05)] rounded-[2.5rem] bg-emerald-950 text-white overflow-hidden">
                <CardHeader className="pb-4">
                    <div className="flex items-center justify-between">
                        <Badge className="bg-emerald-500/20 text-emerald-300 border-none px-3 py-1 rounded-full text-[10px] font-bold tracking-widest uppercase">
                            AI Analysis
                        </Badge>
                        <Sparkles className={`size-4 text-emerald-400 ${isGenerating ? 'animate-pulse' : ''}`} />
                    </div>
                    <CardTitle className="text-2xl font-light mt-4">EcoBot Intelligence</CardTitle>
                    <CardDescription className="text-white/40 text-xs">Autonomous cross-provider synthesis</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                    <div className="min-h-[300px] text-sm leading-relaxed text-white/80 font-light">
                        {isGenerating ? (
                            <div className="space-y-4 animate-pulse">
                                <div className="h-4 bg-white/10 rounded w-3/4" />
                                <div className="h-4 bg-white/10 rounded w-full" />
                                <div className="h-4 bg-white/10 rounded w-5/6" />
                                <div className="h-4 bg-white/10 rounded w-2/3" />
                                <div className="h-4 bg-white/10 rounded w-full" />
                            </div>
                        ) : (
                            <p className="whitespace-pre-wrap">{aiSummary || "Select generate to start AI analysis..."}</p>
                        )}
                    </div>
                    
                    <Button 
                        onClick={generateAISummary}
                        disabled={isGenerating}
                        className="w-full rounded-2xl bg-white/10 hover:bg-white/20 border border-white/10 py-6 transition-all text-white"
                    >
                        {isGenerating ? "Synthesizing Data..." : "Re-generate Analysis"}
                    </Button>
                </CardContent>
            </Card>

            <Card className="border-none shadow-[0_8px_30px_rgb(0,0,0,0.02)] rounded-[2rem] bg-white p-2">
                <CardHeader>
                    <CardTitle className="text-sm font-medium text-slate-700">Network Efficiency</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="flex items-center justify-between p-4 bg-emerald-50/30 rounded-2xl border border-emerald-50">
                        <div className="flex items-center gap-3">
                            <TrendingUp className="size-4 text-emerald-600" />
                            <span className="text-xs font-medium text-slate-600">Grid Stability</span>
                        </div>
                        <span className="text-xs font-bold text-emerald-700">99.98%</span>
                    </div>
                    <div className="flex items-center justify-between p-4 bg-emerald-50/30 rounded-2xl border border-emerald-50">
                        <div className="flex items-center gap-3">
                            <Zap className="size-4 text-emerald-500" />
                            <span className="text-xs font-medium text-slate-600">Peak Load Index</span>
                        </div>
                        <span className="text-xs font-bold text-emerald-700">High</span>
                    </div>
                </CardContent>
            </Card>
        </div>

        {/* Right Column: Historical Trends & Data */}
        <div className="lg:col-span-2 space-y-8">
            <Card className="border-none shadow-[0_8px_30px_rgb(0,0,0,0.02)] rounded-[2.5rem] bg-white p-6">
                <CardHeader className="flex flex-row items-center justify-between pb-8">
                    <div>
                        <CardTitle className="text-xl font-medium text-slate-700">7-Day Generation Mix</CardTitle>
                        <CardDescription className="text-xs text-slate-400">Aggregate production by source (MW)</CardDescription>
                    </div>
                    <div className="flex items-center gap-2">
                        <Badge variant="outline" className="bg-emerald-50 text-emerald-700 border-none font-bold uppercase text-[9px] tracking-wider">
                            Real Data Synchronized
                        </Badge>
                    </div>
                </CardHeader>
                <CardContent className="h-[400px]">
                    {history && history.length > 0 ? (
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={history.slice(-24)}>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                                <XAxis 
                                    dataKey="time" 
                                    axisLine={false} 
                                    tickLine={false} 
                                    tick={{fontSize: 9, fill: '#94a3b8'}}
                                    tickFormatter={(str) => {
                                        const d = new Date(str);
                                        return d.getHours() + "h";
                                    }}
                                />
                                <YAxis axisLine={false} tickLine={false} tick={{fontSize: 9, fill: '#94a3b8'}} />
                                <Tooltip 
                                    contentStyle={{borderRadius: '16px', border: 'none', boxShadow: '0 10px 40px rgba(16,185,129,0.1)'}}
                                />
                                <Legend wrapperStyle={{fontSize: '10px', paddingTop: '20px'}} />
                                <Bar dataKey="nuclear_mw" fill="#10b981" name="Nuclear" radius={[4, 4, 0, 0]} fillOpacity={0.8} />
                                <Bar dataKey="solar_mw" fill="#34d399" name="Solar" radius={[4, 4, 0, 0]} fillOpacity={0.6} />
                                <Bar dataKey="wind_mw" fill="#059669" name="Wind" radius={[4, 4, 0, 0]} fillOpacity={0.4} />
                            </BarChart>
                        </ResponsiveContainer>
                    ) : (
                        <div className="flex items-center justify-center h-full text-emerald-100 font-light italic">
                            Synthesizing historical generation mix...
                        </div>
                    )}
                </CardContent>
            </Card>

            <div className="grid grid-cols-2 gap-6">
                 <Card className="border-none shadow-[0_8px_30px_rgb(0,0,0,0.02)] rounded-[2rem] bg-white p-6">
                    <CardHeader className="p-0 pb-4">
                        <div className="flex items-center gap-3 text-emerald-600/40 mb-2">
                            <Clock className="size-4" />
                            <span className="text-[10px] font-bold uppercase tracking-widest">Temporal Analysis</span>
                        </div>
                        <CardTitle className="text-lg font-medium text-slate-700">Off-Peak Advantage</CardTitle>
                    </CardHeader>
                    <CardContent className="p-0">
                        <p className="text-sm text-slate-400 font-light leading-relaxed">
                            Current trends suggest shifting 15% of heavy industrial load to the 02:00-05:00 window 
                            could reduce carbon intensity by up to 22g/kWh.
                        </p>
                    </CardContent>
                 </Card>

                 <Card className="border-none shadow-[0_8px_30px_rgb(0,0,0,0.02)] rounded-[2rem] bg-white p-6">
                    <CardHeader className="p-0 pb-4">
                        <div className="flex items-center gap-3 text-emerald-600/40 mb-2">
                            <TrendingUp className="size-4" />
                            <span className="text-[10px] font-bold uppercase tracking-widest">Grid Forecasting</span>
                        </div>
                        <CardTitle className="text-lg font-medium text-slate-700">Weekly Forecast</CardTitle>
                    </CardHeader>
                    <CardContent className="p-0">
                        <p className="text-sm text-slate-400 font-light leading-relaxed">
                            Solar yield is projected to increase by 8% this week due to high pressure systems over the 
                            southern fleet clusters.
                        </p>
                    </CardContent>
                 </Card>
            </div>
        </div>
      </div>
    </div>
  );
}
