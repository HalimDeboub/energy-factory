import { Outlet, Link, useLocation, useNavigate } from "react-router-dom";
import {
  LayoutDashboard,
  MessageSquare,
  FileText,
  Settings,
  Leaf,
  LogOut,
  User,
  ShieldCheck
} from "lucide-react";
import { HealthCheck } from "./HealthCheck";
import { useEffect } from "react";

export function Layout() {
  const location = useLocation();
  const navigate = useNavigate();

  // Protect the routes
  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token && location.pathname !== "/onboarding") {
      navigate("/onboarding");
    }
  }, [location, navigate]);

  const handleLogout = () => {
    localStorage.removeItem("token");
    navigate("/onboarding");
  };

  const navItems = [
    { path: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
    { path: "/chat", label: "Assistant", icon: MessageSquare },
    { path: "/reports", label: "Executive Reports", icon: FileText },
    { path: "/settings", label: "Orchestration", icon: Settings },
  ];

  return (
    <div className="flex h-screen bg-slate-50 text-slate-600 font-sans antialiased overflow-hidden">
      {/* Premium Sidebar */}
      <aside className="w-72 bg-white border-r border-emerald-100 flex flex-col shadow-[20px_0_40px_rgba(16,185,129,0.02)]">
        <div className="p-8 pb-12">
            <div className="flex items-center gap-3 text-emerald-600 mb-2">
                <div className="p-2 bg-emerald-50 rounded-xl shadow-sm border border-emerald-100">
                    <Leaf className="size-6" />
                </div>
                <h1 className="text-xl font-light tracking-tight text-slate-700">EcoBot <span className="font-bold text-emerald-600">Pro</span></h1>
            </div>
            <p className="text-[10px] uppercase tracking-[0.2em] font-bold text-slate-300 ml-1">Enterprise Edition</p>
        </div>

        <nav className="flex-1 px-4 space-y-1.5">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname.startsWith(item.path);

            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-3 px-5 py-3.5 rounded-2xl transition-all duration-300 group ${
                  isActive
                    ? "bg-emerald-600 text-white shadow-lg shadow-emerald-100"
                    : "text-slate-400 hover:bg-emerald-50 hover:text-emerald-600"
                }`}
              >
                <Icon className={`size-5 transition-transform duration-500 ${isActive ? 'scale-110' : 'group-hover:scale-110'}`} />
                <span className={`text-sm font-medium ${isActive ? 'opacity-100' : 'opacity-80'}`}>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* User / Org Footer */}
        <div className="p-6 mt-auto border-t border-emerald-50 space-y-4">
            <div className="flex items-center gap-3 p-3 bg-slate-50/50 rounded-2xl border border-slate-100">
                <div className="size-8 bg-white border border-emerald-100 rounded-full flex items-center justify-center text-emerald-600 shadow-sm">
                    <User className="size-4" />
                </div>
                <div className="flex-1 min-w-0">
                    <p className="text-xs font-bold text-slate-700 truncate">Stakeholder</p>
                    <div className="flex items-center gap-1">
                        <ShieldCheck className="size-2.5 text-emerald-500" />
                        <span className="text-[9px] text-slate-400 uppercase font-bold tracking-tighter">Verified Account</span>
                    </div>
                </div>
            </div>
            
            <button 
                onClick={handleLogout}
                className="w-full flex items-center justify-center gap-2 py-3 rounded-xl text-xs font-bold text-slate-400 hover:text-red-500 hover:bg-red-50 transition-all duration-300 group"
            >
                <LogOut className="size-4 group-hover:-translate-x-1 transition-transform" /> Sign Out from Partition
            </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-20 bg-white/80 backdrop-blur-md border-b border-emerald-50 px-8 flex items-center justify-between z-10">
            <div className="flex items-center gap-4">
                <div className="flex -space-x-2">
                    <div className="size-6 rounded-full border-2 border-white bg-emerald-100" />
                    <div className="size-6 rounded-full border-2 border-white bg-teal-100" />
                </div>
                <span className="text-[10px] text-slate-400 font-bold uppercase tracking-widest">Active Data Sync • Real Time</span>
            </div>
            <HealthCheck />
        </header>

        <main className="flex-1 overflow-auto bg-[#fafafa]">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
