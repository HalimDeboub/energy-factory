import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Label } from "../components/ui/label";
import { Input } from "../components/ui/input";
import { Switch } from "../components/ui/switch";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { 
  Database, Globe, FileText, Plus, Save, 
  Wifi, Cpu, Layers, Activity, Search, 
  Trash2, ArrowRight, Settings2, ShieldCheck,
  Server, Link2, Info, HardDrive, Zap, Map, Key, Upload
} from "lucide-react"; 
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "../components/ui/dialog"; 
import { useState, useEffect } from "react"; 
import { toast } from "react-hot-toast";

// Universal internal schema fields (matches backend UNIVERSAL_SCHEMA)
const UNIVERSAL_FIELDS = [
  { key: "consumption_mw",         label: "Total Consumption",    unit: "MW" },
  { key: "solar_mw",               label: "Solar Generation",     unit: "MW" },
  { key: "wind_mw",                label: "Wind Generation",      unit: "MW" },
  { key: "hydro_mw",               label: "Hydro Generation",     unit: "MW" },
  { key: "gas_mw",                 label: "Gas Generation",       unit: "MW" },
  { key: "nuclear_mw",             label: "Nuclear Generation",   unit: "MW" },
  { key: "biomass_mw",             label: "Biomass Generation",   unit: "MW" },
  { key: "storage_mw",             label: "Battery Storage",      unit: "MW" },
  { key: "grid_exchange_mw",       label: "Grid Exchanges",       unit: "MW" },
  { key: "carbon_intensity_g_kwh", label: "CO₂ Intensity",        unit: "g/kWh" },
  { key: "total_production_mw",    label: "Total Production",     unit: "MW" },
  { key: "capacity_mw",            label: "Installed Capacity",   unit: "MW" },
  { key: "availability_pct",       label: "Availability",         unit: "%" },
  { key: "peak_load_mw",           label: "Peak Load",            unit: "MW" },
  { key: "forecast_mw",            label: "Forecast",             unit: "MW" },
];

const SOURCE_TYPES = [
  { id: "rest_api",  label: "REST API",   icon: <Link2 className="size-4" />,   desc: "HTTP/JSON endpoint" },
  { id: "iot",       label: "IoT",        icon: <Wifi className="size-4" />,    desc: "MQTT / sensor feed" },
  { id: "database",  label: "Database",   icon: <Server className="size-4" />,  desc: "SQL / SCADA / InfluxDB" },
  { id: "document",  label: "Document",   icon: <FileText className="size-4" />,desc: "PDF / CSV / reports" },
];

type MappingState = Record<string, string>;

export function Settings() {
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [sources, setSources] = useState<{data_sources: any[], knowledge_sources: any[]}>({data_sources: [], knowledge_sources: []});
  const [newSource, setNewSource] = useState({
    id: "",
    name: "",
    type: "rest_api",
    url: "",
    connection_string: "",
    topic: "",
    metrics: "",
    persist_data: false,
    api_key: "",
    api_key_header: "Authorization",
    mapping: {} as MappingState,
  });

  const [discoveredFields, setDiscoveredFields] = useState<string[]>([]);
  const [isDiscovering, setIsDiscovering] = useState(false);
  const [showMapping, setShowMapping] = useState(false);

  const handleDiscover = async () => {
    if (!newSource.url) return;
    setIsDiscovering(true);
    try {
      const headers: Record<string,string> = {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${localStorage.getItem('token')}`
      };
      const res = await fetch("http://localhost:9000/sources/discover", {
        method: "POST",
        headers,
        body: JSON.stringify({ url: newSource.url, api_key: newSource.api_key, api_key_header: newSource.api_key_header })
      });
      const data = await res.json();
      if (data.status === "success") {
        setDiscoveredFields(data.fields);
        setShowMapping(true);
        toast.success(`Discovered ${data.fields.length} fields`);
      } else {
        toast.error(data.message || "Discovery failed");
      }
    } catch (e) {
      toast.error("Discovery service unreachable");
    } finally {
      setIsDiscovering(false);
    }
  };

  const fetchSources = async () => {
    try {
      const res = await fetch("http://localhost:9000/sources", {
        headers: { "Authorization": `Bearer ${localStorage.getItem('token')}` }
      });
      const data = await res.json();
      if (data && !data.detail) setSources(data);
    } catch (err) {
      console.error("Error fetching sources:", err);
    }
  };

  useEffect(() => { fetchSources(); }, []);

  const [healthStatus, setHealthStatus] = useState<Record<string, 'online' | 'offline' | 'testing'>>({});

  const handleTestConnection = async (sourceId: string) => {
    setHealthStatus(prev => ({ ...prev, [sourceId]: 'testing' }));
    try {
      const res = await fetch(`http://localhost:9000/sources/${sourceId}/test`, {
        method: "POST",
        headers: { "Authorization": `Bearer ${localStorage.getItem('token')}` }
      });
      const data = await res.json();
      if (data.status === "success" || data.connected === true) {
        setHealthStatus(prev => ({ ...prev, [sourceId]: 'online' }));
        toast.success(`${sourceId} connection verified`);
      } else {
        setHealthStatus(prev => ({ ...prev, [sourceId]: 'offline' }));
        toast.error(`${sourceId} connection failed: ${data.message || 'Unknown error'}`);
      }
    } catch (e) {
      setHealthStatus(prev => ({ ...prev, [sourceId]: 'offline' }));
      toast.error("Network error during test");
    }
  };

  const handleDeleteSource = async (sourceId: string) => {
    if (!window.confirm(`Are you sure you want to remove ${sourceId}?`)) return;
    
    try {
      const res = await fetch(`http://localhost:9000/sources/${sourceId}`, {
        method: "DELETE",
        headers: { "Authorization": `Bearer ${localStorage.getItem('token')}` }
      });
      if (res.ok) {
        toast.success("Source removed successfully");
        fetchSources();
      } else {
        toast.error("Failed to remove source");
      }
    } catch (e) {
      toast.error("Network error during deletion");
    }
  };

  const handleAddSource = async () => {
    try {
      const payload = {
        ...newSource,
        id: newSource.name.toLowerCase().replace(/ /g, "_"),
        metrics: newSource.metrics.split(",").map(m => m.trim()).filter(m => m),
        field_mapping: newSource.mapping,
        enabled: true,
        ...(newSource.api_key ? {
          headers: { [newSource.api_key_header]: newSource.api_key_header === "Authorization" ? `Bearer ${newSource.api_key}` : newSource.api_key }
        } : {})
      };

      const response = await fetch("http://localhost:9000/sources", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        setIsDialogOpen(false);
        setDiscoveredFields([]);
        setShowMapping(false);
        toast.success("Source provisioned successfully");
        fetchSources();
      } else {
        toast.error("Failed to provision source");
      }
    } catch (error) {
      toast.error("Network error while provisioning");
    }
  };

  const getSourceIcon = (type: string) => {
    const t = SOURCE_TYPES.find(s => s.id === type);
    return t?.icon || <Activity className="size-4" />;
  };

  const isApiType = newSource.type === "rest_api" || newSource.type === "iot";
  const isDbType = newSource.type === "database";
  const isDocType = newSource.type === "document";

  return (
    <div className="p-10 max-w-7xl mx-auto space-y-12 bg-[#fafafa] min-h-screen">
      {/* Header */}
      <div className="flex items-end justify-between border-b border-emerald-100 pb-8">
        <div>
          <Badge variant="outline" className="mb-3 text-[10px] uppercase tracking-widest border-emerald-200 text-emerald-600 rounded-full px-3 bg-emerald-50">
            Universal Energy Platform
          </Badge>
          <h2 className="text-4xl font-light text-slate-700 tracking-tight">Data Sources</h2>
          <p className="text-slate-400 mt-2 font-light max-w-md">
            Connect any energy data source. Map external fields to the universal schema for intelligent analysis.
          </p>
        </div>

        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button className="bg-emerald-600 hover:bg-emerald-700 text-white rounded-full px-6 shadow-lg shadow-emerald-200">
              <Plus className="size-4 mr-2" /> Connect Source
            </Button>
          </DialogTrigger>

          <DialogContent className="max-w-2xl border-none shadow-2xl rounded-[2.5rem] p-8 bg-white/95 backdrop-blur-xl max-h-[90vh] overflow-y-auto">
            <DialogHeader className="space-y-1">
              <DialogTitle className="text-2xl font-light text-slate-700">New Data Source</DialogTitle>
              <DialogDescription className="text-slate-400 font-light text-sm">
                Connect any API, database, or document. Map fields to the universal energy schema.
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-6 py-4">

              {/* Source Type */}
              <div className="space-y-2">
                <Label className="text-[10px] uppercase tracking-widest text-emerald-600 font-bold">Source Type</Label>
                <div className="grid grid-cols-4 gap-2">
                  {SOURCE_TYPES.map(t => (
                    <button
                      key={t.id}
                      onClick={() => setNewSource({...newSource, type: t.id})}
                      className={`py-3 rounded-2xl flex flex-col items-center gap-1.5 transition-all duration-300 ${newSource.type === t.id ? 'bg-emerald-600 text-white shadow-md' : 'bg-emerald-50/50 text-emerald-600/40 hover:bg-emerald-50'}`}
                    >
                      <span className="size-4">{t.icon}</span>
                      <span className="text-[9px] font-bold tracking-wider">{t.label}</span>
                      <span className="text-[8px] opacity-60 hidden sm:block">{t.desc}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Name */}
              <div className="space-y-1.5">
                <Label className="text-[10px] text-slate-400 uppercase font-bold ml-1">Source Name</Label>
                <Input placeholder="e.g. Tlemcen Solar Farm" className="bg-slate-50 border-none rounded-xl h-11"
                  onChange={(e) => setNewSource({...newSource, name: e.target.value})} />
              </div>

              {/* API / IoT fields */}
              {isApiType && (
                <>
                  <div className="space-y-1.5">
                    <Label className="text-[10px] text-slate-400 uppercase font-bold ml-1">Endpoint URL</Label>
                    <div className="flex gap-2">
                      <Input placeholder="http://127.0.0.1:9001/api/sources/combined" className="bg-slate-50 border-none rounded-xl h-11 flex-1 text-xs font-mono"
                        onChange={(e) => setNewSource({...newSource, url: e.target.value})} />
                      <Button onClick={handleDiscover} disabled={isDiscovering}
                        className="bg-emerald-50 text-emerald-600 hover:bg-emerald-100 rounded-xl px-4 border-none shadow-none text-[10px] font-bold uppercase">
                        {isDiscovering ? "Scanning..." : "Scan Fields"}
                      </Button>
                    </div>
                  </div>

                  {/* API Key */}
                  <div className="p-4 bg-slate-50 rounded-2xl space-y-3">
                    <Label className="text-[10px] uppercase tracking-widest text-slate-500 font-bold flex items-center gap-2">
                      <Key className="size-3" /> API Authentication (optional)
                    </Label>
                    <div className="grid grid-cols-2 gap-3">
                      <div className="space-y-1">
                        <Label className="text-[9px] text-slate-400 uppercase">Header Name</Label>
                        <Input placeholder="Authorization" defaultValue="Authorization" className="bg-white border-none rounded-lg h-9 text-xs"
                          onChange={(e) => setNewSource({...newSource, api_key_header: e.target.value})} />
                      </div>
                      <div className="space-y-1">
                        <Label className="text-[9px] text-slate-400 uppercase">API Key / Token</Label>
                        <Input type="password" placeholder="sk-..." className="bg-white border-none rounded-lg h-9 text-xs"
                          onChange={(e) => setNewSource({...newSource, api_key: e.target.value})} />
                      </div>
                    </div>
                    <p className="text-[9px] text-slate-400">Leave blank for public APIs. Key stored securely in sources config.</p>
                  </div>
                </>
              )}

              {/* Database fields */}
              {isDbType && (
                <div className="space-y-3">
                  <div className="space-y-1.5">
                    <Label className="text-[10px] text-slate-400 uppercase font-bold ml-1">Connection String</Label>
                    <Input placeholder="postgresql://user:pass@host:5432/scada_db  or  sqlite:///data.db" className="bg-slate-50 border-none rounded-xl h-11 text-xs font-mono"
                      onChange={(e) => setNewSource({...newSource, connection_string: e.target.value})} />
                  </div>
                  <div className="space-y-1.5">
                    <Label className="text-[10px] text-slate-400 uppercase font-bold ml-1">Table / Query</Label>
                    <Input placeholder="e.g. grid_readings  or  SELECT * FROM telemetry WHERE ..." className="bg-slate-50 border-none rounded-xl h-11 text-xs font-mono"
                      onChange={(e) => setNewSource({...newSource, url: e.target.value})} />
                  </div>
                  <p className="text-[10px] text-slate-400 ml-1">Supports: PostgreSQL, MySQL, SQLite, InfluxDB, TimescaleDB</p>
                </div>
              )}

              {/* Document fields */}
              {isDocType && (
                <div className="space-y-3">
                  <div className="space-y-1.5">
                    <Label className="text-[10px] text-slate-400 uppercase font-bold ml-1">Document Path or URL</Label>
                    <Input placeholder="/path/to/energy-report.pdf  or  https://..." className="bg-slate-50 border-none rounded-xl h-11 text-xs font-mono"
                      onChange={(e) => setNewSource({...newSource, url: e.target.value})} />
                  </div>
                  <p className="text-[10px] text-slate-400 ml-1">Supports: PDF, CSV, DOCX, TXT. Document will be indexed into the vector knowledge base.</p>
                </div>
              )}

              {/* Discovered fields */}
              {discoveredFields.length > 0 && (
                <div className="p-4 bg-emerald-50/30 rounded-2xl border border-emerald-100 animate-in fade-in">
                  <Label className="text-[9px] uppercase tracking-widest text-emerald-600 font-bold mb-2 block">
                    Detected Fields ({discoveredFields.length}) — click to copy
                  </Label>
                  <div className="flex flex-wrap gap-1.5">
                    {discoveredFields.map(f => (
                      <Badge key={f} variant="outline" className="bg-white border-emerald-100 text-emerald-700 cursor-pointer hover:bg-emerald-600 hover:text-white transition-colors text-[10px]"
                        onClick={() => { navigator.clipboard.writeText(f); toast.success(`Copied "${f}"`); }}>
                        {f}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

              {/* Persist toggle */}
              {!isDocType && (
                <div className="flex items-center justify-between p-4 bg-emerald-50/30 rounded-2xl border border-emerald-100">
                  <div>
                    <p className="text-xs font-bold text-emerald-700">Data Persistence</p>
                    <p className="text-[10px] text-emerald-600/60">ON = store in DB for history & trends. OFF = live-only context.</p>
                  </div>
                  <Switch checked={newSource.persist_data}
                    onCheckedChange={(val) => setNewSource({...newSource, persist_data: val})} />
                </div>
              )}

              {/* Universal Field Mapping */}
              {(isApiType || isDbType) && (
                <div className="space-y-3">
                  <Label className="text-[10px] uppercase tracking-widest text-emerald-600 font-bold flex items-center gap-2">
                    <Map className="size-3" /> Field Mapping → Universal Schema
                  </Label>
                  <p className="text-[10px] text-slate-400">
                    Map your source's field names to the universal internal schema. Leave blank to skip a field.
                  </p>
                  <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
                    {UNIVERSAL_FIELDS.map(field => (
                      <div key={field.key} className="flex items-center gap-3 bg-slate-50 rounded-xl px-3 py-2">
                        <div className="flex-1 min-w-0">
                          <span className="text-[10px] font-bold text-emerald-700 block">{field.label}</span>
                          <span className="text-[9px] text-slate-400 font-mono">{field.key} ({field.unit})</span>
                        </div>
                        <ArrowRight className="size-3 text-slate-300 flex-shrink-0" />
                        <Input
                          placeholder={discoveredFields[0] || "your_field_name"}
                          className="bg-white border-none rounded-lg h-8 text-[10px] font-mono w-40 flex-shrink-0"
                          value={newSource.mapping[field.key] || ""}
                          onChange={(e) => setNewSource({
                            ...newSource,
                            mapping: { ...newSource.mapping, [field.key]: e.target.value }
                          })}
                        />
                      </div>
                    ))}
                  </div>
                </div>
              )}

            </div>

            <DialogFooter className="pt-4">
              <Button onClick={handleAddSource} className="w-full bg-emerald-600 hover:bg-emerald-700 h-12 text-sm rounded-2xl shadow-lg shadow-emerald-100">
                <Save className="size-4 mr-2" /> Activate Data Node
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* Source Cards */}
      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
        {sources.data_sources.length === 0 && (
            <div className="lg:col-span-3 py-20 text-center space-y-4 bg-white rounded-[3rem] border border-dashed border-emerald-100">
                <div className="size-16 bg-emerald-50 rounded-full flex items-center justify-center mx-auto text-emerald-400">
                    <Globe className="size-8" />
                </div>
                <div>
                    <h3 className="text-lg font-medium text-slate-600">No active data nodes</h3>
                    <p className="text-sm text-slate-400 font-light">Connect your first SCADA, API or IoT stream to begin analysis.</p>
                </div>
                <Button variant="outline" className="rounded-full border-emerald-200 text-emerald-600 px-8" onClick={() => setIsDialogOpen(true)}>
                    Provision New Node
                </Button>
            </div>
        )}
        {sources.data_sources.map((source) => (
          <div key={source.id} className="group relative bg-white border border-emerald-50 rounded-[2.5rem] p-7 transition-all duration-500 hover:shadow-[0_20px_50px_rgba(16,185,129,0.05)] hover:-translate-y-1">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <div className="size-10 bg-emerald-50 rounded-2xl flex items-center justify-center text-emerald-600 group-hover:bg-emerald-600 group-hover:text-white transition-all duration-500">
                  {getSourceIcon(source.type)}
                </div>
                <div>
                  <span className="text-[9px] uppercase tracking-widest text-emerald-600/40 font-bold block">
                    {SOURCE_TYPES.find(t => t.id === source.type)?.label || source.type}
                  </span>
                  <h3 className="text-lg font-medium text-slate-700 leading-tight">{source.name}</h3>
                </div>
              </div>
              <Switch defaultChecked={source.enabled} className="data-[state=checked]:bg-emerald-500" />
            </div>

            <div className="space-y-4">
              {/* Field Mappings */}
              <div className="bg-emerald-50/20 rounded-2xl p-4 border border-emerald-50/50">
                <div className="flex items-center justify-between mb-3">
                  <div className="text-[9px] text-emerald-600/50 uppercase tracking-wider flex items-center gap-1.5 font-bold">
                    <Settings2 className="size-3" /> Field Mapping
                  </div>
                  <div className="flex gap-1">
                    {source.persist_data && <Badge className="bg-emerald-600 text-[8px] h-4 rounded-md">Stored</Badge>}
                    {source.headers && <Badge className="bg-slate-600 text-[8px] h-4 rounded-md flex items-center gap-1"><Key className="size-2" />Auth</Badge>}
                  </div>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {Object.entries(source.field_mapping || {}).map(([internal, external]) => (
                    <span key={internal} className="px-2 py-0.5 bg-white border border-emerald-50 text-emerald-700 text-[9px] rounded-md font-mono">
                      {external} → {internal}
                    </span>
                  ))}
                  {(!source.field_mapping || Object.keys(source.field_mapping).length === 0) && (
                    <span className="text-[10px] text-slate-300 italic">No field mapping (using raw field names)</span>
                  )}
                </div>
              </div>

              <div className="flex items-center justify-between pt-2">
                <div className="flex items-center gap-2">
                  <div className={`size-1.5 rounded-full ${
                    healthStatus[source.id] === 'online' ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]' : 
                    healthStatus[source.id] === 'offline' ? 'bg-red-500' : 
                    healthStatus[source.id] === 'testing' ? 'bg-yellow-500 animate-pulse' :
                    source.enabled ? 'bg-emerald-500 animate-pulse' : 'bg-slate-200'
                  }`} />
                  <span className="text-[11px] text-slate-400 font-medium capitalize">
                    {healthStatus[source.id] || (source.enabled ? 'Active' : 'Paused')}
                  </span>
                </div>
                <div className="flex items-center gap-3">
                  <button 
                    onClick={() => handleTestConnection(source.id)}
                    disabled={healthStatus[source.id] === 'testing'}
                    className="text-slate-200 hover:text-emerald-600 transition-colors disabled:opacity-50"
                  >
                    <HardDrive className={`size-4 ${healthStatus[source.id] === 'testing' ? 'animate-spin' : ''}`} />
                  </button>
                  <button 
                    onClick={() => handleDeleteSource(source.id)}
                    className="text-slate-200 hover:text-red-400 transition-colors"
                  >
                    <Trash2 className="size-4" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        ))}

        {/* Knowledge/Document Sources */}
        {sources.knowledge_sources.map((ks) => (
          <div key={ks.id} className="group relative bg-teal-50/10 border border-teal-100/50 rounded-[2.5rem] p-7 transition-all duration-500 hover:shadow-[0_20px_50px_rgba(20,184,166,0.05)] hover:-translate-y-1">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <div className="size-10 bg-white rounded-2xl flex items-center justify-center text-teal-500 group-hover:bg-teal-500 group-hover:text-white transition-all duration-500 shadow-sm">
                  <FileText className="size-4" />
                </div>
                <div>
                  <span className="text-[9px] uppercase tracking-widest text-teal-600/40 font-bold block">Document / RAG</span>
                  <h3 className="text-lg font-medium text-slate-700 leading-tight">{ks.name}</h3>
                </div>
              </div>
              <Switch defaultChecked={ks.enabled} className="data-[state=checked]:bg-teal-500" />
            </div>
            <div className="bg-white rounded-2xl p-4 border border-teal-50/50">
              <div className="text-[9px] text-teal-600/50 uppercase tracking-wider mb-2 flex items-center gap-1.5 font-bold">
                <Search className="size-3" /> Indexed Path
              </div>
              <p className="text-[10px] text-slate-400 font-mono truncate">{ks.path}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

