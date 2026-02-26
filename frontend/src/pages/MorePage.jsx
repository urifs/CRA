import { Link, useNavigate } from "react-router-dom";
import { 
  DollarSign,
  Clock,
  Bell,
  Package,
  Tags,
  ClipboardList,
  LogOut,
  ChevronRight,
  User
} from "lucide-react";

export default function MorePage() {
  const navigate = useNavigate();
  const user = JSON.parse(localStorage.getItem("user") || "{}");

  const menuItems = [
    { path: "/gerenciamento/balance", icon: DollarSign, label: "Balanço", description: "Custos e despesas" },
    { path: "/gerenciamento/usage", icon: Clock, label: "Tempo de Uso", description: "Registrar horas" },
    { path: "/gerenciamento/horimetro", icon: Clock, label: "Horímetro", description: "Horas das máquinas" },
    { path: "/gerenciamento/notifications", icon: Bell, label: "Notificações", description: "Alertas do sistema" },
    { path: "/gerenciamento/stock", icon: Package, label: "Estoque", description: "Controle de peças" },
    { path: "/gerenciamento/categories", icon: Tags, label: "Categorias", description: "Tipos de máquinas" },
    { path: "/gerenciamento/audit", icon: ClipboardList, label: "Auditoria", description: "Histórico de alterações" },
  ];

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    navigate("/login");
  };

  return (
    <div className="space-y-6 animate-fade-in pb-4" data-testid="more-page">
      {/* User Info */}
      <div className="bg-white rounded-xl p-4 shadow-sm">
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 bg-black rounded-full flex items-center justify-center">
            <User className="text-white" size={24} />
          </div>
          <div>
            <h2 className="font-bold text-lg text-black">{user.name || "Usuário"}</h2>
            <p className="text-gray-500 text-sm">{user.email || ""}</p>
          </div>
        </div>
      </div>

      {/* Menu Items */}
      <div className="bg-white rounded-xl shadow-sm overflow-hidden">
        {menuItems.map((item, index) => (
          <Link
            key={item.path}
            to={item.path}
            className={`flex items-center gap-4 p-4 touch-feedback ${
              index < menuItems.length - 1 ? "border-b border-gray-100" : ""
            }`}
            data-testid={`more-menu-${item.path.replace("/", "")}`}
          >
            <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
              <item.icon className="text-gray-600" size={20} />
            </div>
            <div className="flex-1">
              <p className="font-medium text-black">{item.label}</p>
              <p className="text-sm text-gray-500">{item.description}</p>
            </div>
            <ChevronRight className="text-gray-400" size={20} />
          </Link>
        ))}
      </div>

      {/* Logout */}
      <div className="bg-white rounded-xl shadow-sm overflow-hidden">
        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-4 p-4 touch-feedback text-left"
          data-testid="logout-btn-mobile"
        >
          <div className="w-10 h-10 bg-red-100 rounded-lg flex items-center justify-center">
            <LogOut className="text-red-600" size={20} />
          </div>
          <div className="flex-1">
            <p className="font-medium text-red-600">Sair</p>
            <p className="text-sm text-gray-500">Encerrar sessão</p>
          </div>
        </button>
      </div>

      {/* App Info */}
      <div className="text-center py-4">
        <p className="text-sm text-gray-400">Sistema de Gerenciamento v1.0</p>
        <p className="text-xs text-gray-300 mt-1">Sistema de Gerenciamento de Manutenção</p>
      </div>
    </div>
  );
}
