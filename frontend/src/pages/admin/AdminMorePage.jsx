import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "@/App";
import { Card, CardContent } from "@/components/ui/card";
import { 
  DollarSign,
  Users,
  Package,
  ClipboardList,
  ArrowLeft,
  ChevronRight,
  LogOut
} from "lucide-react";

export default function AdminMorePage() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const menuItems = [
    { 
      path: "/admin/plano-contas", 
      icon: DollarSign, 
      label: "Plano de Contas",
      description: "Categorias financeiras"
    },
    { 
      path: "/admin/fornecedores", 
      icon: Users, 
      label: "Fornecedores",
      description: "Cadastro de fornecedores"
    },
    { 
      path: "/admin/produtos", 
      icon: Package, 
      label: "Produtos",
      description: "Cadastro de produtos"
    },
    { 
      path: "/admin/ordens-servico", 
      icon: ClipboardList, 
      label: "Ordens de Serviço",
      description: "Gerenciar OS"
    },
  ];

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <div data-testid="admin-more-page">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Mais Opções</h1>
          <p className="text-slate-500 mt-1">Funcionalidades adicionais</p>
        </div>
      </div>

      {/* Menu items */}
      <div className="space-y-3 mb-8">
        {menuItems.map((item) => (
          <NavLink key={item.path} to={item.path}>
            <Card className="hover:border-blue-500 transition-colors cursor-pointer">
              <CardContent className="p-4 flex items-center gap-4">
                <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                  <item.icon className="text-blue-600" size={24} />
                </div>
                <div className="flex-1">
                  <p className="font-medium text-slate-900">{item.label}</p>
                  <p className="text-sm text-slate-500">{item.description}</p>
                </div>
                <ChevronRight className="text-slate-400" size={20} />
              </CardContent>
            </Card>
          </NavLink>
        ))}
      </div>

      {/* System switch */}
      <Card 
        className="hover:border-orange-500 transition-colors cursor-pointer mb-4"
        onClick={() => navigate("/select-system")}
      >
        <CardContent className="p-4 flex items-center gap-4">
          <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center">
            <ArrowLeft className="text-orange-600" size={24} />
          </div>
          <div className="flex-1">
            <p className="font-medium text-slate-900">Trocar Sistema</p>
            <p className="text-sm text-slate-500">Voltar para seleção de sistemas</p>
          </div>
          <ChevronRight className="text-slate-400" size={20} />
        </CardContent>
      </Card>

      {/* User info and logout */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium text-slate-900">{user?.name}</p>
              <p className="text-sm text-slate-500">{user?.email}</p>
            </div>
            <button
              onClick={handleLogout}
              className="flex items-center gap-2 px-4 py-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
              data-testid="admin-more-logout"
            >
              <LogOut size={20} />
              <span className="font-medium">Sair</span>
            </button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
