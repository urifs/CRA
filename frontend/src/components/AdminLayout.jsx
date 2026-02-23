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
  Plus,
  Building2,
  ArrowLeft,
  MoreHorizontal
} from "lucide-react";
import { Button } from "@/components/ui/button";

export const AdminLayout = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(window.innerWidth < 768);

  useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth < 768);
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

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
    { path: "/administrativo/plano-contas", icon: DollarSign, label: "Plano de Contas" },
    { path: "/administrativo/nfe", icon: FileText, label: "NF-e" },
    { path: "/administrativo/cadastros", icon: Users, label: "Cadastros" },
    { path: "/administrativo/produtos", icon: Package, label: "Produtos" },
    { path: "/administrativo/ordens-servico", icon: ClipboardList, label: "Ordens de Serviço" },
  ];

  const mobileNavItems = [
    { path: "/administrativo/dashboard", icon: LayoutDashboard, label: "Início" },
    { path: "/administrativo/a-pagar", icon: TrendingDown, label: "A Pagar" },
    { path: "/administrativo/a-receber", icon: TrendingUp, label: "A Receber" },
    { path: "/administrativo/nfe", icon: FileText, label: "NF-e" },
    { path: "/administrativo/more", icon: MoreHorizontal, label: "Mais" },
  ];

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Mobile header */}
      <header 
        className="fixed top-0 left-0 right-0 z-40 md:hidden bg-blue-900 text-white"
        style={{ paddingTop: 'env(safe-area-inset-top)' }}
      >
        <div className="flex items-center justify-between px-4 py-3">
          <div className="flex items-center gap-2">
            <Building2 className="text-blue-300" size={24} />
            <span className="font-heading font-bold">Administrativo</span>
          </div>
          <button
            data-testid="admin-mobile-menu-btn"
            className="p-2 hover:bg-blue-800 rounded-lg"
            onClick={() => setSidebarOpen(!sidebarOpen)}
          >
            {sidebarOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
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
          className="w-full flex items-center gap-2 px-4 py-3 text-blue-300 hover:bg-blue-800 transition-colors border-b border-blue-800"
          data-testid="back-to-select"
        >
          <ArrowLeft size={18} />
          <span className="text-sm">Trocar Sistema</span>
        </button>

        {/* Logo */}
        <div className="p-5 border-b border-blue-800" style={{ flexShrink: 0 }}>
          <h1 className="font-heading text-xl font-black tracking-tight text-white flex items-center gap-2">
            <Building2 className="text-blue-300" size={28} />
            <span>Administrativo</span>
          </h1>
          <p className="text-xs text-blue-400 mt-1">Sistema Financeiro</p>
        </div>

        {/* Navigation - Scrollable */}
        <div className="sidebar-nav py-2">
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
        <div className="p-3 border-t border-blue-800" style={{ flexShrink: 0 }}>
          <div className="flex items-center justify-between">
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-white truncate" data-testid="admin-user-name">
                {user?.name}
              </p>
              <p className="text-xs text-blue-400 truncate">{user?.email}</p>
            </div>
            <button
              data-testid="admin-logout-btn"
              onClick={handleLogout}
              className="ml-2 p-2 text-blue-400 hover:text-white hover:bg-blue-800 rounded-md transition-colors"
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
            (item.path === "/administrativo/more" && ["/administrativo/plano-contas", "/administrativo/fornecedores", "/administrativo/produtos", "/administrativo/ordens-servico"].includes(location.pathname));
          
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={`mobile-nav-item no-select ${isActive ? "active" : ""}`}
              data-testid={`admin-mobile-nav-${item.path.split('/').pop()}`}
            >
              <item.icon size={22} />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>
    </div>
  );
};

export default AdminLayout;
