import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Badge } from "../components/ui/badge";
import { 
  UserPlus, Building2, Zap, ArrowRight, CheckCircle2, 
  ShieldCheck, Globe, Link2, Save, Sparkles, LayoutDashboard
} from "lucide-react";
import { Link } from "react-router-dom";
import { toast } from "react-hot-toast";

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

export function Onboarding() {
  const [step, setStep] = useState(1);
  const [form, setForm] = useState({
    email: "",
    password: "",
    fullName: "",
    companyName: "",
    sector: "Solar",
    firstSourceName: "",
    firstSourceUrl: ""
  });
  const [discoveredFields, setDiscoveredFields] = useState<string[]>([]);
  const [suggestedMapping, setSuggestedMapping] = useState<Record<string, string>>({});
  const [isDiscovering, setIsDiscovering] = useState(false);

  const nextStep = () => setStep(step + 1);
  const prevStep = () => setStep(step - 1);

  const handleDiscover = async () => {
    if (!form.firstSourceUrl) return;
    setIsDiscovering(true);
    try {
      const res = await fetch("http://localhost:9000/sources/discover", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: form.firstSourceUrl })
      });
      const data = await res.json();
      if (data.status === "success") {
        setDiscoveredFields(data.fields);
        setSuggestedMapping(data.suggested_mapping);
        nextStep(); // Move to mapping step
      } else {
        toast.error(data.message || "Failed to discover fields");
      }
    } catch (err) {
      toast.error("Discovery failed. Check URL.");
    } finally {
      setIsDiscovering(false);
    }
  };

  const handleFinalize = async () => {
    try {
      // 1. Register User & Company
      const regRes = await fetch("http://localhost:9000/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            email: form.email,
            password: form.password,
            full_name: form.fullName,
            company_name: form.companyName,
            sector: form.sector
        }),
      });

      if (!regRes.ok) {
          const errData = await regRes.json();
          throw new Error(errData.detail || "Registration failed");
      }
      const { access_token } = await regRes.json();
      localStorage.setItem("token", access_token);
      toast.success("Organization provisioned successfully!");

      // 2. Add First Source with Mappings
      if (form.firstSourceUrl) {
          const sourceRes = await fetch("http://localhost:9000/sources", {
            method: "POST",
            headers: { 
                "Content-Type": "application/json",
                "Authorization": `Bearer ${access_token}`
            },
            body: JSON.stringify({
                id: form.firstSourceName.toLowerCase().replace(/[^a-z0-9]/g, "_") || "initial_source",
                name: form.firstSourceName,
                type: "rest_api",
                url: form.firstSourceUrl,
                enabled: true,
                persist_data: true,
                field_mapping: suggestedMapping
            }),
          });
          if (sourceRes.ok) {
              toast.success("First data node connected with intelligence!");
          }
      }

      setStep(5); // Move to Success Step
    } catch (error: any) {
      console.error("Onboarding failed:", error);
      toast.error(error.message || "Onboarding failed. Please check your network.");
    }
  };

  const renderStep = () => {
    switch(step) {
      case 1:
        return (
          <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="space-y-2 text-center">
              <div className="size-12 bg-emerald-100 text-emerald-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <UserPlus className="size-6" />
              </div>
              <h2 className="text-2xl font-light text-slate-700">Create Personal Account</h2>
              <p className="text-slate-400 text-sm">Join the enterprise energy network.</p>
            </div>
            <div className="space-y-4">
              <div className="space-y-1.5">
                <Label className="text-[10px] uppercase font-bold text-slate-400 ml-1">Full Name</Label>
                <Input 
                    placeholder="Alex Rivier" 
                    className="bg-slate-50 border-none h-11 rounded-xl"
                    value={form.fullName}
                    onChange={e => setForm({...form, fullName: e.target.value})}
                />
              </div>
              <div className="space-y-1.5">
                <Label className="text-[10px] uppercase font-bold text-slate-400 ml-1">Work Email</Label>
                <Input 
                    placeholder="alex@company.energy" 
                    className="bg-slate-50 border-none h-11 rounded-xl"
                    value={form.email}
                    onChange={e => setForm({...form, email: e.target.value})}
                />
              </div>
              <div className="space-y-1.5">
                <Label className="text-[10px] uppercase font-bold text-slate-400 ml-1">Security Key (Password)</Label>
                <Input 
                    type="password" 
                    className="bg-slate-50 border-none h-11 rounded-xl"
                    value={form.password}
                    onChange={e => setForm({...form, password: e.target.value})}
                />
              </div>
            </div>
            <Button onClick={nextStep} className="w-full bg-emerald-600 hover:bg-emerald-700 h-12 rounded-xl text-white shadow-lg shadow-emerald-100">
              Continue to Company Setup <ArrowRight className="size-4 ml-2" />
            </Button>
            <p className="text-center text-xs text-slate-400 mt-4">
                Already have an account? <Link to="/login" className="text-emerald-600 font-bold hover:underline">Log in</Link>
            </p>
          </div>
        );
      case 2:
        return (
          <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-500">
            <div className="space-y-2 text-center">
              <div className="size-12 bg-emerald-100 text-emerald-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <Building2 className="size-6" />
              </div>
              <h2 className="text-2xl font-light text-slate-700">Establish Organization</h2>
              <p className="text-slate-400 text-sm">Define your company profile.</p>
            </div>
            <div className="space-y-4">
              <div className="space-y-1.5">
                <Label className="text-[10px] uppercase font-bold text-slate-400 ml-1">Legal Entity Name</Label>
                <Input 
                    placeholder="GreenGrid Systems" 
                    className="bg-slate-50 border-none h-11 rounded-xl"
                    value={form.companyName}
                    onChange={e => setForm({...form, companyName: e.target.value})}
                />
              </div>
              <div className="space-y-1.5">
                <Label className="text-[10px] uppercase font-bold text-slate-400 ml-1">Energy Sector</Label>
                <select 
                    className="w-full bg-slate-50 border-none h-11 rounded-xl px-3 text-sm text-slate-600 focus:ring-2 focus:ring-emerald-100 outline-none"
                    value={form.sector}
                    onChange={e => setForm({...form, sector: e.target.value})}
                >
                    <option>Solar Generation</option>
                    <option>Wind Farms</option>
                    <option>Grid Operator</option>
                    <option>EV Infrastructure</option>
                </select>
              </div>
            </div>
            <div className="flex gap-3">
                <Button variant="outline" onClick={prevStep} className="flex-1 border-emerald-100 h-12 rounded-xl text-emerald-600">Back</Button>
                <Button onClick={nextStep} className="flex-[2] bg-emerald-600 hover:bg-emerald-700 h-12 rounded-xl text-white shadow-lg shadow-emerald-100">
                  Provision Company <ArrowRight className="size-4 ml-2" />
                </Button>
            </div>
          </div>
        );
      case 3:
        return (
          <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-500">
            <div className="space-y-2 text-center">
              <div className="size-12 bg-emerald-100 text-emerald-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <Link2 className="size-6" />
              </div>
              <h2 className="text-2xl font-light text-slate-700">First Data Node</h2>
              <p className="text-slate-400 text-sm">Connect your initial telemetry stream.</p>
            </div>
            <div className="space-y-4">
              <div className="space-y-1.5">
                <Label className="text-[10px] uppercase font-bold text-slate-400 ml-1">Source Label</Label>
                <Input 
                    placeholder="Main Plant API" 
                    className="bg-slate-50 border-none h-11 rounded-xl"
                    value={form.firstSourceName}
                    onChange={e => setForm({...form, firstSourceName: e.target.value})}
                />
              </div>
              <div className="space-y-1.5">
                <Label className="text-[10px] uppercase font-bold text-slate-400 ml-1">API Endpoint URL</Label>
                <Input 
                    placeholder="https://api.energy.net/v1/telemetry" 
                    className="bg-slate-50 border-none h-11 rounded-xl text-xs font-mono"
                    value={form.firstSourceUrl}
                    onChange={e => setForm({...form, firstSourceUrl: e.target.value})}
                />
              </div>
            </div>
            <div className="flex gap-3">
                <Button variant="outline" onClick={prevStep} className="flex-1 border-emerald-100 h-12 rounded-xl text-emerald-600">Back</Button>
                <Button 
                    onClick={handleDiscover} 
                    disabled={isDiscovering}
                    className="flex-[2] bg-emerald-600 hover:bg-emerald-700 h-12 rounded-xl text-white shadow-lg shadow-emerald-100"
                >
                  {isDiscovering ? "Discovering..." : "Analyze & Map Source"} <Sparkles className="size-4 ml-2" />
                </Button>
            </div>
          </div>
        );
      case 4:
        return (
          <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-500">
            <div className="space-y-2 text-center">
              <div className="size-12 bg-emerald-100 text-emerald-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <Zap className="size-6" />
              </div>
              <h2 className="text-2xl font-light text-slate-700">Intelligent Mapping</h2>
              <p className="text-slate-400 text-sm">Align your source fields to standard metrics.</p>
            </div>
            
            <div className="space-y-4 max-h-[300px] overflow-y-auto pr-2">
                {UNIVERSAL_FIELDS.map((metric) => (
                    <div key={metric.key} className="p-4 bg-slate-50 rounded-2xl border border-slate-100 flex items-center justify-between">
                        <div>
                            <span className="text-[10px] font-bold uppercase text-emerald-600 block">{metric.label}</span>
                            <span className="text-[8px] text-slate-400 font-mono">{metric.key} ({metric.unit})</span>
                        </div>
                        <select 
                            className="bg-white border border-slate-200 rounded-lg text-[10px] px-2 py-1 outline-none"
                            value={suggestedMapping[metric.key] || ""}
                            onChange={(e) => setSuggestedMapping({...suggestedMapping, [metric.key]: e.target.value})}
                        >
                            <option value="">(Ignore)</option>
                            {discoveredFields.map(f => (
                                <option key={f} value={f}>{f}</option>
                            ))}
                        </select>
                    </div>
                ))}
            </div>

            <div className="flex gap-3">
                <Button variant="outline" onClick={prevStep} className="flex-1 border-emerald-100 h-12 rounded-xl text-emerald-600">Back</Button>
                <Button onClick={handleFinalize} className="flex-[2] bg-emerald-600 hover:bg-emerald-700 h-12 rounded-xl text-white shadow-lg shadow-emerald-100">
                  Finalize Setup <ArrowRight className="size-4 ml-2" />
                </Button>
            </div>
          </div>
        );
      case 5:
        return (
          <div className="space-y-8 text-center animate-in zoom-in duration-500">
            <div className="size-20 bg-emerald-500 text-white rounded-full flex items-center justify-center mx-auto shadow-xl shadow-emerald-200">
                <CheckCircle2 className="size-10" />
            </div>
            <div className="space-y-2">
                <h2 className="text-3xl font-light text-slate-700">System Ready</h2>
                <p className="text-slate-400">Your enterprise partition is successfully provisioned.</p>
            </div>
            
            <div className="bg-emerald-50 rounded-3xl p-6 border border-emerald-100 text-left">
                <div className="flex items-center gap-3 mb-4">
                    <ShieldCheck className="size-5 text-emerald-600" />
                    <span className="text-xs font-bold uppercase tracking-widest text-emerald-700">Security Certificate</span>
                </div>
                <div className="space-y-2">
                    <div className="flex justify-between text-[10px]">
                        <span className="text-emerald-600/60 uppercase">Organization</span>
                        <span className="font-bold text-emerald-900">{form.companyName}</span>
                    </div>
                    <div className="flex justify-between text-[10px]">
                        <span className="text-emerald-600/60 uppercase">Identity</span>
                        <span className="font-bold text-emerald-900">{form.email}</span>
                    </div>
                    <div className="flex justify-between text-[10px]">
                        <span className="text-emerald-600/60 uppercase">First Node</span>
                        <span className="font-bold text-emerald-900">{form.firstSourceName}</span>
                    </div>
                </div>
            </div>

            <Button 
                onClick={() => window.location.href = '/dashboard'}
                className="w-full bg-emerald-600 hover:bg-emerald-700 h-14 rounded-2xl text-white shadow-xl shadow-emerald-100 text-lg font-light"
            >
                Launch Mission Control <LayoutDashboard className="size-5 ml-2" />
            </Button>
          </div>
        )
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-6 relative overflow-hidden">
      {/* Dynamic Background Elements */}
      <div className="absolute top-0 right-0 size-[500px] bg-emerald-100/30 rounded-full blur-[120px] -mr-64 -mt-64" />
      <div className="absolute bottom-0 left-0 size-[500px] bg-teal-100/20 rounded-full blur-[120px] -ml-64 -mb-64" />

      <Card className="max-w-lg w-full border-none shadow-[0_32px_64px_rgba(16,185,129,0.08)] rounded-[3rem] bg-white/80 backdrop-blur-xl p-4">
        <div className="p-8">
            <div className="flex justify-between mb-12">
                {[1, 2, 3, 4, 5].map(s => (
                    <div key={s} className="flex items-center gap-2">
                        <div className={`size-2.5 rounded-full transition-all duration-500 ${step >= s ? 'bg-emerald-500 w-8' : 'bg-slate-200'}`} />
                    </div>
                ))}
            </div>

            {renderStep()}

            {step < 4 && (
                <p className="text-center text-[10px] text-slate-300 mt-8 uppercase tracking-[0.2em] font-bold">
                    Enterprise Onboarding v3.0
                </p>
            )}
        </div>
      </Card>
    </div>
  );
}
