import { useState, useEffect } from "react";
import { Outlet, NavLink, useNavigate, useLocation } from "react-router-dom";
import { useAuth, API } from "@/App";
import axios from "axios";
import { 
  LayoutDashboard, 
  DollarSign,
  TrendingUp,
  TrendingDown,
  FileText,
  Users,
  Package,
  ClipboardList,
  LogOut, 
  Menu, 
  X,
  Building2,
  ArrowLeft,
  MoreHorizontal,
  Bell,
  Truck,
  CreditCard,
  FileDown
} from "lucide-react";
import { Button } from "@/components/ui/button";
import ChatbotWidget from "@/components/ChatbotWidget";
import TasksInbox from "@/components/TasksInbox";

export const AdminLayout = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(window.innerWidth < 768);
  const [notifCount, setNotifCount] = useState({ total: 0, vencidas: 0 });

  useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth < 768);
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  useEffect(() => {
    fetchNotifCount();
    // Atualizar a cada 5 minutos
    const interval = setInterval(fetchNotifCount, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  const fetchNotifCount = async () => {
    try {
      const response = await axios.get(`${API}/admin/notificacoes/contagem?prazo_dias=7`);
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
    { path: "/administrativo/dashboard", icon: LayoutDashboard, label: "Dashboard" },
    { path: "/administrativo/a-pagar", icon: TrendingDown, label: "A Pagar" },
    { path: "/administrativo/a-receber", icon: TrendingUp, label: "A Receber" },
    { path: "/administrativo/alugueis", icon: Truck, label: "Aluguéis Máquinas" },
    { path: "/administrativo/imoveis", icon: Building2, label: "Imóveis" },
    { path: "/administrativo/plano-contas", icon: DollarSign, label: "Plano de Contas" },
    { path: "/administrativo/centro-custo", icon: Building2, label: "Centro de Custo" },
    { path: "/administrativo/formas-pagamento", icon: CreditCard, label: "Formas Pagamento" },
    { path: "/administrativo/contas-bancarias", icon: Building2, label: "Contas Bancárias" },
    { path: "/administrativo/cadastros", icon: Users, label: "Cadastros" },
    { path: "/administrativo/produtos", icon: Package, label: "Produtos" },
    { path: "/administrativo/ordens-servico", icon: ClipboardList, label: "Ordens de Serviço" },
    { path: "/administrativo/exportar", icon: FileDown, label: "Exportação" },
  ];

  const mobileNavItems = [
    { path: "/administrativo/dashboard", icon: LayoutDashboard, label: "Início" },
    { path: "/administrativo/a-pagar", icon: TrendingDown, label: "A Pagar" },
    { path: "/administrativo/a-receber", icon: TrendingUp, label: "A Receber" },
    { path: "/administrativo/notificacoes", icon: Bell, label: "Alertas", badge: notifCount.total },
    { path: "/administrativo/more", icon: MoreHorizontal, label: "Mais" },
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
            <Building2 className="text-[#D4A000]" size={24} />
            <span className="font-heading font-bold">Administrativo</span>
          </div>
          <div className="flex items-center gap-1">
            {/* Tasks inbox */}
            <TasksInbox system="administrativo" accentColor="#D4A000" />
            {/* Notification bell for mobile header */}
            <button
              data-testid="admin-mobile-notif-btn"
              className="p-2 hover:bg-gray-900 rounded-lg relative"
              onClick={() => navigate("/administrativo/notificacoes")}
            >
              <Bell size={22} />
              {notifCount.total > 0 && (
                <span className={`absolute -top-1 -right-1 min-w-[18px] h-[18px] flex items-center justify-center text-xs font-bold rounded-full ${notifCount.vencidas > 0 ? 'bg-[#E31A1A]' : 'bg-[#D4A000] text-black'} text-white`}>
                  {notifCount.total > 99 ? '99+' : notifCount.total}
                </span>
              )}
            </button>
            <button
              data-testid="admin-mobile-menu-btn"
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
              <Building2 className="text-[#D4A000]" size={28} />
              <span>Administrativo</span>
            </h1>
            <div className="hidden md:block">
              <TasksInbox system="administrativo" accentColor="#D4A000" />
            </div>
          </div>
          <p className="text-xs text-gray-400 mt-1">Sistema Financeiro</p>
        </div>

        {/* Navigation - Scrollable */}
        <div className="sidebar-nav py-2">
          {/* Notification link at top of sidebar */}
          <NavLink
            to="/administrativo/notificacoes"
            onClick={() => setSidebarOpen(false)}
            className={({ isActive }) =>
              `admin-sidebar-link ${isActive ? "active" : ""} ${notifCount.vencidas > 0 ? "text-[#D4A000]" : ""}`
            }
            data-testid="admin-nav-notificacoes"
          >
            <Bell size={20} />
            <span className="flex-1">Notificações</span>
            {notifCount.total > 0 && (
              <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${notifCount.vencidas > 0 ? 'bg-[#E31A1A]' : 'bg-[#D4A000] text-black'} text-white`}>
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
              data-testid={`admin-nav-${item.path.split('/').pop()}`}
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
              <p className="text-sm font-medium text-white truncate" data-testid="admin-user-name">
                {user?.name}
              </p>
              <p className="text-xs text-gray-400 truncate">{user?.email}</p>
            </div>
            <button
              data-testid="admin-logout-btn"
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
      <nav className="admin-mobile-nav" data-testid="admin-mobile-bottom-nav">
        {mobileNavItems.map((item) => {
          const isActive = location.pathname === item.path || 
            (item.path === "/administrativo/more" && ["/administrativo/plano-contas", "/administrativo/cadastros", "/administrativo/produtos", "/administrativo/ordens-servico", "/administrativo/alugueis", "/administrativo/centro-custo", "/administrativo/formas-pagamento"].includes(location.pathname));
          
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={`mobile-nav-item no-select ${isActive ? "active" : ""}`}
              data-testid={`admin-mobile-nav-${item.path.split('/').pop()}`}
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
      <ChatbotWidget module="administrativo" accentColor="#D4A000" />
    </div>
  );
};

export default AdminLayout;
