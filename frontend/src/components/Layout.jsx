import { useState, useEffect } from "react";
import { Outlet, NavLink, useNavigate } from "react-router-dom";
import { useAuth, API } from "@/App";
import axios from "axios";
import { 
  LayoutDashboard, 
  Truck, 
  Wrench, 
  Tags, 
  LogOut, 
  Menu, 
  X,
  Plus,
  Package,
  Clock,
  Bell,
  Construction,
  DollarSign,
  HardHat,
  ClipboardList
} from "lucide-react";
import { Button } from "@/components/ui/button";

export const Layout = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [notificationCount, setNotificationCount] = useState(0);

  useEffect(() => {
    fetchNotificationCount();
    // Refresh count every 60 seconds
    const interval = setInterval(fetchNotificationCount, 60000);
    return () => clearInterval(interval);
  }, []);

  const fetchNotificationCount = async () => {
    try {
      const response = await axios.get(`${API}/notifications`);
      setNotificationCount(response.data.length);
    } catch (error) {
      // Silently fail
    }
  };

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const navItems = [
    { path: "/dashboard", icon: LayoutDashboard, label: "Dashboard" },
    { path: "/obras", icon: HardHat, label: "Plano de Obras" },
    { path: "/machines", icon: Truck, label: "Máquinas" },
    { path: "/maintenances", icon: Wrench, label: "Manutenções" },
    { path: "/balance", icon: DollarSign, label: "Balanço" },
    { path: "/usage", icon: Clock, label: "Tempo de Uso" },
    { path: "/notifications", icon: Bell, label: "Notificações", badge: notificationCount },
    { path: "/stock", icon: Package, label: "Estoque" },
    { path: "/categories", icon: Tags, label: "Categorias" },
  ];

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Mobile menu button */}
      <button
        data-testid="mobile-menu-btn"
        className="fixed top-4 left-4 z-50 md:hidden bg-slate-900 text-white p-2 rounded-md"
        onClick={() => setSidebarOpen(!sidebarOpen)}
      >
        {sidebarOpen ? <X size={24} /> : <Menu size={24} />}
      </button>

      {/* Sidebar */}
      <aside
        className={`sidebar transition-transform duration-300 ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"
        }`}
      >
        {/* Logo */}
        <div className="p-6 border-b border-slate-700">
          <h1 className="font-heading text-xl font-black tracking-tight text-white flex items-center gap-2">
            <Construction className="text-orange-500" size={28} />
            <span>CRA Construtora</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">Sistema de Manutenção</p>
        </div>

        {/* Navigation */}
        <nav className="py-4">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              onClick={() => setSidebarOpen(false)}
              className={({ isActive }) =>
                `sidebar-link ${isActive ? "active" : ""}`
              }
              data-testid={`nav-${item.path.slice(1)}`}
            >
              <item.icon size={20} />
              <span className="flex-1">{item.label}</span>
              {item.badge > 0 && (
                <span 
                  className="bg-orange-500 text-white text-xs font-bold px-2 py-0.5 rounded-full min-w-[20px] text-center"
                  data-testid="notification-badge"
                >
                  {item.badge > 99 ? "99+" : item.badge}
                </span>
              )}
            </NavLink>
          ))}
        </nav>

        {/* Quick action */}
        <div className="px-4 py-4 border-t border-slate-700">
          <Button
            data-testid="new-maintenance-btn"
            className="w-full bg-orange-500 hover:bg-orange-600 text-white font-bold"
            onClick={() => {
              navigate("/maintenances/new");
              setSidebarOpen(false);
            }}
          >
            <Plus size={18} className="mr-2" />
            Nova Manutenção
          </Button>
        </div>

        {/* User info */}
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-slate-700">
          <div className="flex items-center justify-between">
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-white truncate" data-testid="user-name">
                {user?.name}
              </p>
              <p className="text-xs text-slate-400 truncate">{user?.email}</p>
            </div>
            <button
              data-testid="logout-btn"
              onClick={handleLogout}
              className="ml-2 p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-md transition-colors"
              title="Sair"
            >
              <LogOut size={20} />
            </button>
          </div>
        </div>
      </aside>

      {/* Backdrop for mobile */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Main content */}
      <main className="main-content">
        <div className="p-4 md:p-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
};

export default Layout;
