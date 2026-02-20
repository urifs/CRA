import { useState, useEffect } from "react";
import { Outlet, NavLink, useNavigate, useLocation } from "react-router-dom";
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
  ClipboardList,
  MoreHorizontal
} from "lucide-react";
import { Button } from "@/components/ui/button";

export const Layout = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [notificationCount, setNotificationCount] = useState(0);
  const [isMobile, setIsMobile] = useState(window.innerWidth < 768);

  useEffect(() => {
    fetchNotificationCount();
    const interval = setInterval(fetchNotificationCount, 60000);
    
    const handleResize = () => {
      setIsMobile(window.innerWidth < 768);
    };
    window.addEventListener('resize', handleResize);
    
    return () => {
      clearInterval(interval);
      window.removeEventListener('resize', handleResize);
    };
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
    { path: "/audit", icon: ClipboardList, label: "Auditoria" },
  ];

  // Mobile bottom navigation items
  const mobileNavItems = [
    { path: "/dashboard", icon: LayoutDashboard, label: "Início" },
    { path: "/obras", icon: HardHat, label: "Obras" },
    { path: "/machines", icon: Truck, label: "Máquinas" },
    { path: "/maintenances", icon: Wrench, label: "Manutenções" },
    { path: "/more", icon: MoreHorizontal, label: "Mais" },
  ];

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Mobile header */}
      <header 
        className="fixed top-0 left-0 right-0 z-40 md:hidden bg-slate-900 text-white"
        style={{ paddingTop: 'env(safe-area-inset-top)' }}
      >
        <div className="flex items-center justify-between px-4 py-3">
          <div className="flex items-center gap-2">
            <Construction className="text-orange-500" size={24} />
            <span className="font-heading font-bold">CRA Construtora</span>
          </div>
          <button
            data-testid="mobile-menu-btn"
            className="p-2 hover:bg-slate-800 rounded-lg"
            onClick={() => setSidebarOpen(!sidebarOpen)}
          >
            {sidebarOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>
      </header>

      {/* Sidebar - Hidden on mobile, always visible on desktop */}
      <aside
        className={`sidebar transition-transform duration-300 ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"
        }`}
        style={{ paddingTop: 'env(safe-area-inset-top)' }}
      >
        {/* Logo - Fixed at top */}
        <div className="p-5 border-b border-slate-700" style={{ flexShrink: 0 }}>
          <h1 className="font-heading text-xl font-black tracking-tight text-white flex items-center gap-2">
            <Construction className="text-orange-500" size={28} />
            <span>CRA Construtora</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">Sistema de Manutenção</p>
        </div>

        {/* Navigation - Scrollable */}
        <nav className="py-2" style={{ flex: 1, minHeight: 0, overflowY: 'auto', overflowX: 'hidden' }}>
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

        {/* Quick action - Fixed at bottom */}
        <div className="px-4 py-3 border-t border-slate-700" style={{ flexShrink: 0 }}>
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

        {/* User info - Fixed at bottom */}
        <div className="p-3 border-t border-slate-700" style={{ flexShrink: 0 }}>
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

      {/* Backdrop for mobile sidebar */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 md:hidden"
          style={{ zIndex: 55 }}
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Main content */}
      <main 
        className="main-content md:pt-0"
        style={{ paddingTop: 'calc(56px + env(safe-area-inset-top))' }}
      >
        <div className="p-4 md:p-8 pb-24 md:pb-8">
          <Outlet />
        </div>
      </main>

      {/* Mobile bottom navigation */}
      <nav className="mobile-nav" data-testid="mobile-bottom-nav">
        {mobileNavItems.map((item) => {
          const isActive = location.pathname === item.path || 
            (item.path === "/more" && ["/balance", "/usage", "/notifications", "/stock", "/categories", "/audit"].includes(location.pathname));
          
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={`mobile-nav-item no-select ${isActive ? "active" : ""}`}
              data-testid={`mobile-nav-${item.path.replace("/", "")}`}
            >
              <item.icon size={22} />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>

      {/* Floating action button for mobile */}
      {isMobile && location.pathname !== "/maintenances/new" && (
        <button
          onClick={() => navigate("/maintenances/new")}
          className="fab bg-orange-500 hover:bg-orange-600 text-white flex items-center justify-center shadow-lg"
          data-testid="fab-new-maintenance"
          style={{ bottom: 'calc(80px + env(safe-area-inset-bottom))' }}
        >
          <Plus size={28} />
        </button>
      )}
    </div>
  );
};

export default Layout;
