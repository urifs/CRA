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
  DollarSign,
  MoreHorizontal,
  ArrowLeft,
  HardHat,
  FileDown
} from "lucide-react";
import { Button } from "@/components/ui/button";
import ChatbotWidget from "@/components/ChatbotWidget";
import TasksInbox from "@/components/TasksInbox";

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

  const handleBackToSelect = () => {
    navigate("/select-system");
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
    { path: "/exportar", icon: FileDown, label: "Exportação" },
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
    <div className="min-h-screen bg-white">
      {/* Mobile header */}
      <header 
        className="fixed top-0 left-0 right-0 z-40 md:hidden bg-black text-white"
        style={{ paddingTop: 'env(safe-area-inset-top)' }}
      >
        <div className="flex items-center justify-between px-4 py-3">
          <div className="flex items-center gap-2">
            <img src="/logo.png" alt="Logo" className="w-8 h-8 object-contain" />
            <span className="font-heading font-bold">Gerenciamento</span>
          </div>
          <div className="flex items-center gap-1">
            <TasksInbox system="gerenciamento" accentColor="#E31A1A" />
            <button
              data-testid="mobile-menu-btn"
              className="p-2 hover:bg-gray-900 rounded-lg"
              onClick={() => setSidebarOpen(!sidebarOpen)}
            >
              {sidebarOpen ? <X size={24} /> : <Menu size={24} />}
            </button>
          </div>
        </div>
      </header>

      {/* Sidebar - Hidden on mobile, always visible on desktop */}
      <aside
        className={`sidebar transition-transform duration-300 ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"
        }`}
        style={{ paddingTop: 'env(safe-area-inset-top)' }}
      >
        {/* Back to system select button */}
        <button
          onClick={handleBackToSelect}
          className="w-full flex items-center gap-2 px-4 py-3 text-gray-400 hover:bg-gray-900 transition-colors border-b border-gray-800"
          data-testid="back-to-select"
        >
          <ArrowLeft size={18} />
          <span className="text-sm">Trocar Sistema</span>
        </button>

        {/* Logo - Fixed at top */}
        <div className="p-5 border-b border-gray-800" style={{ flexShrink: 0 }}>
          <div className="flex items-center justify-between">
            <h1 className="font-heading text-xl font-black tracking-tight text-white flex items-center gap-2">
              <img src="/logo.png" alt="CRA" className="w-8 h-8 object-contain" />
              <span>CRA Construtora</span>
            </h1>
            <div className="hidden md:block">
              <TasksInbox system="gerenciamento" accentColor="#E31A1A" />
            </div>
          </div>
          <p className="text-xs text-gray-400 mt-1">Gerenciamento</p>
        </div>

        {/* Navigation - Scrollable */}
        <div className="sidebar-nav py-2">
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
                  className="bg-[#E31A1A] text-white text-xs font-bold px-2 py-0.5 rounded-full min-w-[20px] text-center"
                  data-testid="notification-badge"
                >
                  {item.badge > 99 ? "99+" : item.badge}
                </span>
              )}
            </NavLink>
          ))}
        </div>

        {/* Quick action - Fixed at bottom */}
        <div className="px-4 py-3 border-t border-gray-800" style={{ flexShrink: 0 }}>
          <Button
            data-testid="new-maintenance-btn"
            className="w-full bg-[#E31A1A] hover:bg-red-700 text-white font-bold"
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
        <div className="p-3 border-t border-gray-800" style={{ flexShrink: 0 }}>
          <div className="flex items-center justify-between">
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-white truncate" data-testid="user-name">
                {user?.name}
              </p>
              <p className="text-xs text-gray-400 truncate">{user?.email}</p>
            </div>
            <button
              data-testid="logout-btn"
              onClick={handleLogout}
              className="ml-2 p-2 text-gray-400 hover:text-white hover:bg-gray-900 rounded-md transition-colors"
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
            (item.path === "/more" && ["/balance", "/usage", "/notifications", "/stock", "/categories"].includes(location.pathname));
          
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
          className="fab bg-[#E31A1A] hover:bg-red-700 text-white flex items-center justify-center shadow-lg"
          data-testid="fab-new-maintenance"
          style={{ bottom: 'calc(90px + env(safe-area-inset-bottom))' }}
        >
          <Plus size={28} />
        </button>
      )}

      {/* Chatbot Widget - positioned to the left of FAB on mobile */}
      <ChatbotWidget 
        module="gerenciamento" 
        accentColor="#E31A1A" 
        hasFab={isMobile && location.pathname !== "/maintenances/new"}
      />
    </div>
  );
};

export default Layout;
