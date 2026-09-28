import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { ShieldCheck, Lock, User, ArrowRight, Leaf } from "lucide-react";
import { useNavigate, Link } from "react-router-dom";
import { toast } from "react-hot-toast";

export function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async () => {
    setIsLoading(true);
    try {
      const res = await fetch("http://localhost:9000/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      if (res.ok) {
        const { access_token } = await res.json();
        localStorage.setItem("token", access_token);
        toast.success("Welcome back, Stakeholder!");
        navigate("/dashboard");
      } else {
        const errData = await res.json();
        toast.error(errData.detail || "Invalid credentials.");
      }
    } catch (error) {
      console.error("Login failed", error);
      toast.error("System unreachable. Verify backend status.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-6 relative overflow-hidden">
      {/* Dynamic Background Elements */}
      <div className="absolute top-0 right-0 size-[500px] bg-emerald-100/30 rounded-full blur-[120px] -mr-64 -mt-64" />
      <div className="absolute bottom-0 left-0 size-[500px] bg-teal-100/20 rounded-full blur-[120px] -ml-64 -mb-64" />

      <Card className="max-w-md w-full border-none shadow-[0_32px_64px_rgba(16,185,129,0.08)] rounded-[3rem] bg-white/80 backdrop-blur-xl p-4">
        <div className="p-8">
            <div className="space-y-2 text-center mb-10">
              <div className="size-14 bg-emerald-600 text-white rounded-[1.5rem] flex items-center justify-center mx-auto mb-6 shadow-lg shadow-emerald-100">
                <Leaf className="size-8" />
              </div>
              <h2 className="text-3xl font-light text-slate-700">Stakeholder Login</h2>
              <p className="text-slate-400 text-sm">Secure access to your energy partition.</p>
            </div>
            
            <div className="space-y-5">
              <div className="space-y-1.5">
                <Label className="text-[10px] uppercase font-bold text-slate-400 ml-1">Work Email</Label>
                <div className="relative">
                    <User className="absolute left-4 top-3.5 size-4 text-emerald-600/40" />
                    <Input 
                        placeholder="alex@company.energy" 
                        className="bg-slate-50 border-none h-12 rounded-2xl pl-12"
                        value={email}
                        onChange={e => setEmail(e.target.value)}
                    />
                </div>
              </div>
              <div className="space-y-1.5">
                <Label className="text-[10px] uppercase font-bold text-slate-400 ml-1">Access Token</Label>
                <div className="relative">
                    <Lock className="absolute left-4 top-3.5 size-4 text-emerald-600/40" />
                    <Input 
                        type="password" 
                        placeholder="••••••••"
                        className="bg-slate-50 border-none h-12 rounded-2xl pl-12"
                        value={password}
                        onChange={e => setPassword(e.target.value)}
                    />
                </div>
              </div>
              
              <Button 
                onClick={handleLogin} 
                disabled={isLoading}
                className="w-full bg-emerald-600 hover:bg-emerald-700 h-14 rounded-2xl text-white shadow-xl shadow-emerald-100 text-lg font-light mt-4"
              >
                {isLoading ? "Authenticating..." : "Enter Workspace"} <ArrowRight className="size-5 ml-2" />
              </Button>
            </div>

            <div className="mt-10 text-center space-y-4">
                <p className="text-xs text-slate-400">
                    New stakeholder? <Link to="/onboarding" className="text-emerald-600 font-bold hover:underline">Onboard Organization</Link>
                </p>
                <div className="flex items-center justify-center gap-2 text-[9px] text-slate-300 font-bold uppercase tracking-widest">
                    <ShieldCheck className="size-3" />
                    End-to-End Encrypted Session
                </div>
            </div>
        </div>
      </Card>
    </div>
  );
}
