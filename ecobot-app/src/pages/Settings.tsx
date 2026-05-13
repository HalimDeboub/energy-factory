import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Label } from "../components/ui/label";
import { Input } from "../components/ui/input";
import { Switch } from "../components/ui/switch";
import { Button } from "../components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Badge } from "../components/ui/badge";
import { 
  Database, Globe, FileText, Plus, Save, 
  Wifi, Cpu, Layers, Activity, Search, 
  Trash2, ArrowRight, Settings2, ShieldCheck,
  Server, Link2, Info
} from "lucide-react"; 
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "../components/ui/dialog"; 
import { useState, useEffect } from "react"; 

export function Settings() {
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [sources, setSources] = useState<{data_sources: any[], knowledge_sources: any[]}>({data_sources: [], knowledge_sources: []});
  const [newSource, setNewSource] = useState({ 
    id: "", name: "", type: "rest_api", url: "", topic: "", connection_string: "", metrics: "" 
  });

  useEffect(() => {
    fetch("http://localhost:9000/sources")
      .then(res => res.json())
      .then(data => setSources(data))
      .catch(err => console.error("Error fetching sources:", err));
  }, []);

  const handleAddSource = async () => {
    try {
      const payload = {
        ...newSource,
        id: newSource.name.toLowerCase().replace(/ /g, "_"),
        metrics: newSource.metrics.split(",").map(m => m.trim()).filter(m => m),
        enabled: true
      };

      const response = await fetch("http://localhost:9000/sources", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        setIsDialogOpen(false);
        window.location.reload(); 
      }
    } catch (error) {
      console.error("Failed to add source:", error);
    }
  };

  const getSourceIcon = (type: string) => {
    switch (type) {
      case "rest_api": return <Link2 className="size-4" />;
      case "iot": return <Wifi className="size-4" />;
      case "database": return <Server className="size-4" />;
      default: return <Activity className="size-4" />;
    }
  };

  return (
    <div className="p-10 max-w-7xl mx-auto space-y-12 bg-[#fafafa] min-h-screen">
      {/* Header Section */}
      <div className="flex items-end justify-between border-b border-slate-200 pb-8">
        <div>
          <Badge variant="outline" className="mb-3 text-[10px] uppercase tracking-widest border-slate-300 text-slate-500 rounded-full px-3">
            Core Engine v2.4
          </Badge>
          <h2 className="text-4xl font-light text-slate-900 tracking-tight">Intelligence Sources</h2>
          <p className="text-slate-500 mt-2 font-light max-w-md">Connect and configure the primary data nodes that feed the EcoBot RAG framework.</p>
        </div>
        
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button className="bg-slate-900 hover:bg-slate-800 text-white rounded-full px-6 transition-all duration-300">
              <Plus className="size-4 mr-2" /> Connect Source
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-md border-none shadow-2xl rounded-3xl p-8 bg-white/95 backdrop-blur-xl">
            <DialogHeader className="space-y-1">
              <DialogTitle className="text-2xl font-light">New Connection</DialogTitle>
              <DialogDescription className="text-slate-400 font-light text-sm">
                Integrate a new energy data stream into your network.
              </DialogDescription>
            </DialogHeader>
            
            <div className="space-y-6 py-6">
              <div className="space-y-3">
                <Label className="text-xs uppercase tracking-widest text-slate-400 font-bold">Source Class</Label>
                <div className="grid grid-cols-3 gap-3">
                  {[
                    {id: "rest_api", label: "API", icon: <Link2 />},
                    {id: "iot", label: "IoT", icon: <Wifi />},
                    {id: "database", label: "DB", icon: <Server />}
                  ].map(t => (
                    <button 
                      key={t.id}
                      onClick={() => setNewSource({...newSource, type: t.id})}
                      className={`py-4 rounded-2xl flex flex-col items-center gap-2 transition-all duration-300 ${newSource.type === t.id ? 'bg-slate-900 text-white' : 'bg-slate-50 text-slate-400 hover:bg-slate-100'}`}
                    >
                      <span className="size-5">{t.icon}</span>
                      <span className="text-[10px] font-medium tracking-wider">{t.label}</span>
                    </button>
                  ))}
                </div>
              </div>

              <div className="space-y-4">
                <div className="space-y-1.5">
                  <Label htmlFor="s-name" className="text-xs text-slate-400 ml-1">Friendly Name</Label>
                  <Input id="s-name" placeholder="e.g. Regional Power Grid" className="bg-slate-50 border-none rounded-xl h-11 focus:ring-1 focus:ring-slate-200"
                         onChange={(e) => setNewSource({...newSource, name: e.target.value})} />
                </div>

                {newSource.type === "rest_api" && (
                  <div className="space-y-1.5 animate-in fade-in zoom-in-95 duration-300">
                    <Label htmlFor="s-url" className="text-xs text-slate-400 ml-1">Base Endpoint</Label>
                    <Input id="s-url" placeholder="https://api.grid.io/v2" className="bg-slate-50 border-none rounded-xl h-11 focus:ring-1 focus:ring-slate-200"
                           onChange={(e) => setNewSource({...newSource, url: e.target.value})} />
                  </div>
                )}

                {newSource.type === "iot" && (
                  <div className="space-y-1.5 animate-in fade-in zoom-in-95 duration-300">
                    <Label htmlFor="s-topic" className="text-xs text-slate-400 ml-1">Stream Identifier / Topic</Label>
                    <Input id="s-topic" placeholder="grid/telemetry/main_transformer" className="bg-slate-50 border-none rounded-xl h-11 focus:ring-1 focus:ring-slate-200"
                           onChange={(e) => setNewSource({...newSource, topic: e.target.value})} />
                  </div>
                )}

                {newSource.type === "database" && (
                  <div className="space-y-1.5 animate-in fade-in zoom-in-95 duration-300">
                    <Label htmlFor="s-conn" className="text-xs text-slate-400 ml-1">Secure Connection String</Label>
                    <Input id="s-conn" placeholder="postgresql://***:***@host.com" className="bg-slate-50 border-none rounded-xl h-11 focus:ring-1 focus:ring-slate-200"
                           onChange={(e) => setNewSource({...newSource, connection_string: e.target.value})} />
                </div>
                )}

                <div className="space-y-1.5">
                  <Label htmlFor="s-metrics" className="text-xs text-slate-400 ml-1">Observability Metrics</Label>
                  <Input id="s-metrics" placeholder="voltage, kw, current" className="bg-slate-50 border-none rounded-xl h-11 focus:ring-1 focus:ring-slate-200"
                         onChange={(e) => setNewSource({...newSource, metrics: e.target.value})} />
                </div>
              </div>
            </div>

            <DialogFooter>
              <Button onClick={handleAddSource} className="w-full bg-slate-900 hover:bg-slate-800 h-12 text-sm rounded-xl transition-all">
                <Save className="size-4 mr-2" /> Deploy Connection
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* Source Cards Grid */}
      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
        {sources.data_sources.map((source) => (
          <div key={source.id} className="group relative bg-white border border-slate-100 rounded-[2rem] p-7 transition-all duration-500 hover:shadow-[0_20px_50px_rgba(0,0,0,0.04)] hover:-translate-y-1">
            <div className="flex items-center justify-between mb-8">
              <div className="flex items-center gap-3">
                <div className="size-10 bg-slate-50 rounded-2xl flex items-center justify-center text-slate-400 group-hover:bg-slate-900 group-hover:text-white transition-all duration-500">
                  {getSourceIcon(source.type)}
                </div>
                <div>
                   <span className="text-[10px] uppercase tracking-widest text-slate-400 font-bold block">{source.type.replace("_", " ")}</span>
                   <h3 className="text-lg font-medium text-slate-900 leading-tight">{source.name}</h3>
                </div>
              </div>
              <Switch defaultChecked={source.enabled} className="data-[state=checked]:bg-green-500" />
            </div>

            <div className="space-y-4">
              <div className="bg-slate-50/50 rounded-2xl p-4 border border-slate-50">
                <div className="text-[10px] text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                   <Settings2 className="size-3" /> Configured Metrics
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {source.metrics?.map((m: string) => (
                    <span key={m} className="px-2 py-0.5 bg-white border border-slate-100 text-slate-500 text-[10px] rounded-md font-medium">
                      {m}
                    </span>
                  ))}
                  {(!source.metrics || source.metrics.length === 0) && <span className="text-[10px] text-slate-300 italic">No specific metrics</span>}
                </div>
              </div>

              <div className="flex items-center justify-between pt-2">
                 <div className="flex items-center gap-2">
                    <div className={`size-1.5 rounded-full ${source.enabled ? 'bg-green-500 animate-pulse' : 'bg-slate-300'}`} />
                    <span className="text-[11px] text-slate-500 font-medium">{source.enabled ? 'Online' : 'Disconnected'}</span>
                 </div>
                 <div className="flex items-center gap-3">
                   <button className="text-slate-300 hover:text-slate-900 transition-colors">
                      <Info className="size-4" />
                   </button>
                   <button className="text-slate-300 hover:text-red-500 transition-colors">
                      <Trash2 className="size-4" />
                   </button>
                 </div>
              </div>
            </div>
          </div>
        ))}

        {/* Knowledge Sources - Same Aesthetic */}
        {sources.knowledge_sources.map((ks) => (
          <div key={ks.id} className="group relative bg-slate-900 border border-slate-800 rounded-[2rem] p-7 transition-all duration-500 hover:shadow-[0_20px_50px_rgba(0,0,0,0.2)] hover:-translate-y-1">
             <div className="flex items-center justify-between mb-8">
              <div className="flex items-center gap-3">
                <div className="size-10 bg-slate-800 rounded-2xl flex items-center justify-center text-white/50 group-hover:bg-white group-hover:text-slate-900 transition-all duration-500">
                  <FileText className="size-4" />
                </div>
                <div>
                   <span className="text-[10px] uppercase tracking-widest text-white/30 font-bold block">Knowledge RAG</span>
                   <h3 className="text-lg font-medium text-white leading-tight">{ks.name}</h3>
                </div>
              </div>
              <Switch defaultChecked={ks.enabled} className="data-[state=checked]:bg-blue-500 border-slate-700" />
            </div>

            <div className="space-y-4">
              <div className="bg-white/5 rounded-2xl p-4 border border-white/5">
                <div className="text-[10px] text-white/30 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                   <Search className="size-3" /> Directory Path
                </div>
                <p className="text-[11px] text-white/60 font-mono truncate">{ks.path}</p>
              </div>

              <div className="flex items-center justify-between pt-2">
                 <div className="flex items-center gap-2">
                    <ShieldCheck className="size-4 text-blue-400" />
                    <span className="text-[11px] text-white/50 font-medium">Indexing Secured</span>
                 </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
