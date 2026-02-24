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
  LogOut,
  Building2,
  CreditCard,
  FolderTree,
  Truck,
  Bell
} from "lucide-react";

export default function AdminMorePage() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const menuItems = [
    { 
      path: "/administrativo/alugueis", 
      icon: Truck, 
      label: "Aluguéis",
      description: "Locação de máquinas"
    },
    { 
      path: "/administrativo/notificacoes", 
      icon: Bell, 
      label: "Notificações",
      description: "Alertas e vencimentos"
    },
    { 
      path: "/administrativo/plano-contas", 
      icon: FolderTree, 
      label: "Plano de Contas",
      description: "Categorias financeiras"
    },
    { 
      path: "/administrativo/centro-custo", 
      icon: Building2, 
      label: "Centro de Custo",
      description: "Gerenciar centros de custo"
    },
    { 
      path: "/administrativo/formas-pagamento", 
      icon: CreditCard, 
      label: "Formas de Pagamento",
      description: "Configurar formas de pagamento"
    },
    { 
      path: "/administrativo/cadastros", 
      icon: Users, 
      label: "Cadastros",
      description: "Clientes e fornecedores"
    },
    { 
      path: "/administrativo/produtos", 
      icon: Package, 
      label: "Produtos",
      description: "Cadastro de produtos"
    },
    { 
      path: "/administrativo/ordens-servico", 
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
          <p className="text-gray-500 mt-1">Funcionalidades adicionais</p>
        </div>
      </div>

      {/* Menu items */}
      <div className="space-y-3 mb-8">
        {menuItems.map((item) => (
          <NavLink key={item.path} to={item.path}>
            <Card className="hover:border-[#D4A000] transition-colors cursor-pointer">
              <CardContent className="p-4 flex items-center gap-4">
                <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                  <item.icon className="text-[#D4A000]" size={24} />
                </div>
                <div className="flex-1">
                  <p className="font-medium text-black">{item.label}</p>
                  <p className="text-sm text-gray-500">{item.description}</p>
                </div>
                <ChevronRight className="text-gray-400" size={20} />
              </CardContent>
            </Card>
          </NavLink>
        ))}
      </div>

      {/* System switch */}
      <Card 
        className="hover:border-[#E31A1A] transition-colors cursor-pointer mb-4"
        onClick={() => navigate("/select-system")}
      >
        <CardContent className="p-4 flex items-center gap-4">
          <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center">
            <ArrowLeft className="text-[#E31A1A]" size={24} />
          </div>
          <div className="flex-1">
            <p className="font-medium text-black">Trocar Sistema</p>
            <p className="text-sm text-gray-500">Voltar para seleção de sistemas</p>
          </div>
          <ChevronRight className="text-gray-400" size={20} />
        </CardContent>
      </Card>

      {/* User info and logout */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium text-black">{user?.name}</p>
              <p className="text-sm text-gray-500">{user?.email}</p>
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
