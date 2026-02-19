import { useState } from "react";
import { Outlet, NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "@/App";
import { 
  LayoutDashboard, 
  Truck, 
  Wrench, 
  Tags, 
  LogOut, 
  Menu, 
  X,
  Plus,
  Package
} from "lucide-react";
import { Button } from "@/components/ui/button";

export const Layout = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const navItems = [
    { path: "/dashboard", icon: LayoutDashboard, label: "Dashboard" },
    { path: "/machines", icon: Truck, label: "Máquinas" },
    { path: "/maintenances", icon: Wrench, label: "Manutenções" },
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
            <Truck className="text-orange-500" size={28} />
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
              <span>{item.label}</span>
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
