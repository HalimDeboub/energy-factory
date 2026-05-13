import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, LineChart, Line } from "recharts";
import { Download, Calendar, FileText, Sparkles, TrendingUp, Zap, Clock } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { useState, useEffect } from "react";

export function Reports() {
  const [aiSummary, setAiSummary] = useState<string>("");
  const [history, setHistory] = useState<any[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);

  useEffect(() => {
    // Fetch historical data for charts
    fetch("http://localhost:9000/insights/history?hours=168") // Last 7 days
      .then(r => r.json())
      .then(data => setHistory(data.data))
      .catch(err => console.error("Error fetching history:", err));

    // Initial AI Summary
    generateAISummary();
  }, []);

  const generateAISummary = async () => {
    setIsGenerating(true);
    try {
      const res = await fetch("http://localhost:9000/reports/ai-summary");
      const data = await res.json();
      setAiSummary(data.summary);
    } catch (err) {
      console.error("Error generating AI summary:", err);
      setAiSummary("Failed to generate strategic analysis. Please verify AI agent status.");
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8 bg-[#fafafa] min-h-screen">
      {/* Header Area */}
      <div className="flex items-end justify-between border-b border-slate-200 pb-8">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-400">
                Strategic Intelligence
            </span>
          </div>
          <h2 className="text-4xl font-light text-slate-900 tracking-tight">Executive Reports</h2>
        </div>
        
        <div className="flex gap-3">
            <Button variant="outline" className="rounded-xl border-slate-200 bg-white shadow-sm hover:bg-slate-50">
                <Calendar className="size-4 mr-2 text-slate-500" />
                Select Period
            </Button>
            <Button className="rounded-xl bg-slate-900 text-white shadow-lg shadow-slate-200 hover:bg-slate-800 transition-all">
                <Download className="size-4 mr-2" />
                Export PDF
            </Button>
        </div>
      </div>

      <div className="grid lg:grid-cols-3 gap-8">
        {/* Left Column: AI Strategic Summary */}
        <div className="lg:col-span-1 space-y-8">
            <Card className="border-none shadow-[0_8px_30px_rgb(0,0,0,0.04)] rounded-[2rem] bg-gradient-to-br from-slate-900 to-slate-800 text-white overflow-hidden">
                <CardHeader className="pb-4">
                    <div className="flex items-center justify-between">
                        <Badge className="bg-blue-500/20 text-blue-300 border-none px-3 py-1 rounded-full text-[10px] font-bold tracking-widest uppercase">
                            AI Analysis
                        </Badge>
                        <Sparkles className={`size-4 text-blue-400 ${isGenerating ? 'animate-pulse' : ''}`} />
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
                        className="w-full rounded-2xl bg-white/10 hover:bg-white/20 border border-white/10 py-6 transition-all"
                    >
                        {isGenerating ? "Synthesizing Data..." : "Re-generate Analysis"}
                    </Button>
                </CardContent>
            </Card>

            <Card className="border-none shadow-[0_8px_30px_rgb(0,0,0,0.04)] rounded-[2rem] bg-white p-2">
                <CardHeader>
                    <CardTitle className="text-sm font-medium">Network Efficiency</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="flex items-center justify-between p-4 bg-slate-50 rounded-2xl">
                        <div className="flex items-center gap-3">
                            <TrendingUp className="size-4 text-green-500" />
                            <span className="text-xs font-medium text-slate-600">Grid Stability</span>
                        </div>
                        <span className="text-xs font-bold text-slate-900">99.98%</span>
                    </div>
                    <div className="flex items-center justify-between p-4 bg-slate-50 rounded-2xl">
                        <div className="flex items-center gap-3">
                            <Zap className="size-4 text-yellow-500" />
                            <span className="text-xs font-medium text-slate-600">Peak Load Index</span>
                        </div>
                        <span className="text-xs font-bold text-slate-900">High</span>
                    </div>
                </CardContent>
            </Card>
        </div>

        {/* Right Column: Historical Trends & Data */}
        <div className="lg:col-span-2 space-y-8">
            <Card className="border-none shadow-[0_8px_30px_rgb(0,0,0,0.04)] rounded-[2rem] bg-white p-6">
                <CardHeader className="flex flex-row items-center justify-between pb-8">
                    <div>
                        <CardTitle className="text-xl font-medium">7-Day Generation Mix</CardTitle>
                        <CardDescription className="text-xs">Aggregate production by source (MW)</CardDescription>
                    </div>
                    <div className="flex items-center gap-2">
                        <Badge variant="outline" className="bg-emerald-50 text-emerald-700 border-none font-bold uppercase text-[9px] tracking-wider">
                            Real Data Synchronized
                        </Badge>
                    </div>
                </CardHeader>
                <CardContent className="h-[400px]">
                    <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={history.slice(-24)}> {/* Show last 24 records for clarity */}
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
                                contentStyle={{borderRadius: '16px', border: 'none', boxShadow: '0 10px 40px rgba(0,0,0,0.1)'}}
                            />
                            <Legend wrapperStyle={{fontSize: '10px', paddingTop: '20px'}} />
                            <Bar dataKey="nucleaire" fill="#6366f1" name="Nuclear" radius={[4, 4, 0, 0]} />
                            <Bar dataKey="solaire" fill="#fbbf24" name="Solar" radius={[4, 4, 0, 0]} />
                            <Bar dataKey="eolien" fill="#10b981" name="Wind" radius={[4, 4, 0, 0]} />
                        </BarChart>
                    </ResponsiveContainer>
                </CardContent>
            </Card>

            <div className="grid grid-cols-2 gap-6">
                 <Card className="border-none shadow-[0_8px_30px_rgb(0,0,0,0.04)] rounded-[2rem] bg-white p-6">
                    <CardHeader className="p-0 pb-4">
                        <div className="flex items-center gap-3 text-slate-400 mb-2">
                            <Clock className="size-4" />
                            <span className="text-[10px] font-bold uppercase tracking-widest">Temporal Analysis</span>
                        </div>
                        <CardTitle className="text-lg font-medium">Off-Peak Advantage</CardTitle>
                    </CardHeader>
                    <CardContent className="p-0">
                        <p className="text-sm text-slate-500 font-light leading-relaxed">
                            Current trends suggest shifting 15% of heavy industrial load to the 02:00-05:00 window 
                            could reduce carbon intensity by up to 22g/kWh.
                        </p>
                    </CardContent>
                 </Card>

                 <Card className="border-none shadow-[0_8px_30px_rgb(0,0,0,0.04)] rounded-[2rem] bg-white p-6">
                    <CardHeader className="p-0 pb-4">
                        <div className="flex items-center gap-3 text-slate-400 mb-2">
                            <TrendingUp className="size-4" />
                            <span className="text-[10px] font-bold uppercase tracking-widest">Grid Forecasting</span>
                        </div>
                        <CardTitle className="text-lg font-medium">Weekly Forecast</CardTitle>
                    </CardHeader>
                    <CardContent className="p-0">
                        <p className="text-sm text-slate-500 font-light leading-relaxed">
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
