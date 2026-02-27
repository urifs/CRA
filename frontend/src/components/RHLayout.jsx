import { useState, useEffect } from "react";
import { Outlet, NavLink, useNavigate, useLocation } from "react-router-dom";
import { useAuth, API } from "@/App";
import axios from "axios";
import { 
  LayoutDashboard, 
  Users,
  Clock,
  DollarSign,
  Calendar,
  HardHat,
  Bell,
  Calculator,
  LogOut, 
  Menu, 
  X,
  ArrowLeft,
  MoreHorizontal,
  UserPlus,
  FileText
} from "lucide-react";
import ChatbotWidget from "@/components/ChatbotWidget";
import TasksInbox from "@/components/TasksInbox";

export const RHLayout = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(window.innerWidth < 768);
  const [notifCount, setNotifCount] = useState({ total: 0, urgentes: 0 });

  useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth < 768);
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  useEffect(() => {
    fetchNotifCount();
    const interval = setInterval(fetchNotifCount, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  const fetchNotifCount = async () => {
    try {
      const response = await axios.get(`${API}/rh/notificacoes/contagem`);
      setNotifCount(response.data);
    } catch (error) {
      console.error("Erro ao carregar contagem de notificações:", error);
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
    { path: "/rh/dashboard", icon: LayoutDashboard, label: "Dashboard" },
    { path: "/rh/funcionarios", icon: Users, label: "Funcionários" },
    { path: "/rh/ponto", icon: Clock, label: "Ponto Eletrônico" },
    { path: "/rh/folha-pagamento", icon: DollarSign, label: "Folha de Pagamento" },
    { path: "/rh/ferias", icon: Calendar, label: "Férias e Escalas" },
    { path: "/rh/epi", icon: HardHat, label: "Gestão de EPI/EPC" },
    { path: "/rh/custos", icon: Calculator, label: "Gestão de Custos" },
    { path: "/rh/exportar", icon: FileDown, label: "Exportação" },
  ];

  const mobileNavItems = [
    { path: "/rh/dashboard", icon: LayoutDashboard, label: "Início" },
    { path: "/rh/funcionarios", icon: Users, label: "Funcionários" },
    { path: "/rh/ponto", icon: Clock, label: "Ponto" },
    { path: "/rh/notificacoes", icon: Bell, label: "Alertas", badge: notifCount.total },
    { path: "/rh/more", icon: MoreHorizontal, label: "Mais" },
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
            <Users className="text-[#10B981]" size={24} />
            <span className="font-heading font-bold">RH</span>
          </div>
          <div className="flex items-center gap-1">
            <TasksInbox system="rh" accentColor="#10B981" />
            <button
              data-testid="rh-mobile-notif-btn"
              className="p-2 hover:bg-gray-900 rounded-lg relative"
              onClick={() => navigate("/rh/notificacoes")}
            >
              <Bell size={22} />
              {notifCount.total > 0 && (
                <span className={`absolute -top-1 -right-1 min-w-[18px] h-[18px] flex items-center justify-center text-xs font-bold rounded-full ${notifCount.urgentes > 0 ? 'bg-[#E31A1A]' : 'bg-[#10B981]'} text-white`}>
                  {notifCount.total > 99 ? '99+' : notifCount.total}
                </span>
              )}
            </button>
            <button
              data-testid="rh-mobile-menu-btn"
              className="p-2 hover:bg-gray-900 rounded-lg"
              onClick={() => setSidebarOpen(!sidebarOpen)}
            >
              {sidebarOpen ? <X size={24} /> : <Menu size={24} />}
            </button>
          </div>
        </div>
      </header>

      {/* Sidebar */}
      <aside
        className={`admin-sidebar transition-transform duration-300 ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"
        }`}
        style={{ paddingTop: 'env(safe-area-inset-top)' }}
      >
        {/* Back button */}
        <button
          onClick={handleBackToSelect}
          className="w-full flex items-center gap-2 px-4 py-3 text-gray-400 hover:bg-gray-900 transition-colors border-b border-gray-800"
          data-testid="back-to-select"
        >
          <ArrowLeft size={18} />
          <span className="text-sm">Trocar Sistema</span>
        </button>

        {/* Logo */}
        <div className="p-5 border-b border-gray-800" style={{ flexShrink: 0 }}>
          <div className="flex items-center justify-between">
            <h1 className="font-heading text-xl font-black tracking-tight text-white flex items-center gap-2">
              <Users className="text-[#10B981]" size={28} />
              <span>RH</span>
            </h1>
            <div className="hidden md:block">
              <TasksInbox system="rh" accentColor="#10B981" />
            </div>
          </div>
          <p className="text-xs text-gray-400 mt-1">Recursos Humanos</p>
        </div>

        {/* Navigation - Scrollable */}
        <div className="sidebar-nav py-2">
          {/* Notification link at top of sidebar */}
          <NavLink
            to="/rh/notificacoes"
            onClick={() => setSidebarOpen(false)}
            className={({ isActive }) =>
              `admin-sidebar-link ${isActive ? "active" : ""} ${notifCount.urgentes > 0 ? "text-[#10B981]" : ""}`
            }
            data-testid="rh-nav-notificacoes"
          >
            <Bell size={20} />
            <span className="flex-1">Notificações</span>
            {notifCount.total > 0 && (
              <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${notifCount.urgentes > 0 ? 'bg-[#E31A1A]' : 'bg-[#10B981]'} text-white`}>
                {notifCount.total}
              </span>
            )}
          </NavLink>

          <div className="border-b border-gray-800 my-2" />

          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              onClick={() => setSidebarOpen(false)}
              className={({ isActive }) =>
                `admin-sidebar-link ${isActive ? "active" : ""}`
              }
              data-testid={`rh-nav-${item.path.split('/').pop()}`}
            >
              <item.icon size={20} />
              <span className="flex-1">{item.label}</span>
            </NavLink>
          ))}
        </div>

        {/* User info */}
        <div className="p-3 border-t border-gray-800" style={{ flexShrink: 0 }}>
          <div className="flex items-center justify-between">
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-white truncate" data-testid="rh-user-name">
                {user?.name}
              </p>
              <p className="text-xs text-gray-400 truncate">{user?.email}</p>
            </div>
            <button
              data-testid="rh-logout-btn"
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
        className="admin-main-content md:pt-0"
        style={{ paddingTop: 'calc(56px + env(safe-area-inset-top))' }}
      >
        <div className="p-4 md:p-8 pb-24 md:pb-8">
          <Outlet />
        </div>
      </main>

      {/* Mobile bottom navigation */}
      <nav className="admin-mobile-nav" data-testid="rh-mobile-bottom-nav">
        {mobileNavItems.map((item) => {
          const isActive = location.pathname === item.path || 
            (item.path === "/rh/more" && ["/rh/folha-pagamento", "/rh/ferias", "/rh/epi", "/rh/custos"].includes(location.pathname));
          
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={`mobile-nav-item no-select ${isActive ? "active" : ""}`}
              style={{ "--accent-color": "#10B981" }}
              data-testid={`rh-mobile-nav-${item.path.split('/').pop()}`}
            >
              <div className="relative">
                <item.icon size={22} />
                {item.badge > 0 && (
                  <span className="absolute -top-2 -right-2 min-w-[16px] h-[16px] flex items-center justify-center text-[10px] font-bold rounded-full bg-[#E31A1A] text-white">
                    {item.badge > 99 ? '99+' : item.badge}
                  </span>
                )}
              </div>
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>

      {/* Chatbot Widget */}
      <ChatbotWidget module="rh" accentColor="#10B981" />
    </div>
  );
};

export default RHLayout;
