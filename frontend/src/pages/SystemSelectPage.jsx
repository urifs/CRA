import { useNavigate } from "react-router-dom";
import { useAuth } from "@/App";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { 
  Building2,
  Truck,
  Wrench,
  DollarSign,
  FileText,
  Package,
  Users,
  ArrowRight,
  Shield,
  Lock,
  HardHat,
  LogOut,
  FolderOpen,
  Upload,
  HardDrive,
  Clock,
  Calculator
} from "lucide-react";

export default function SystemSelectPage() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  // Verificar permissões baseado no role do usuário
  const userRole = user?.role || "gerenciamento";
  
  // Roles com acesso total (admin e programador)
  const hasFullAccess = ["admin", "programador"].includes(userRole);
  
  const canAccessGerenciamento = hasFullAccess || ["gerenciamento", "ambos", "gerenciamento_rh"].includes(userRole);
  const canAccessAdministrativo = hasFullAccess || ["administrativo", "ambos", "administrativo_rh"].includes(userRole);
  const canAccessRH = hasFullAccess || ["rh", "ambos_rh", "gerenciamento_rh", "administrativo_rh"].includes(userRole);
  const canAccessArmazenamento = hasFullAccess || ["ambos", "gerenciamento", "administrativo", "rh", "ambos_rh", "gerenciamento_rh", "administrativo_rh"].includes(userRole);
  const canAccessAdminPanel = hasFullAccess;

  const handleLogout = () => {
    logout();
    navigate("/login");
    toast.success("Logout realizado com sucesso!");
  };

  const systems = [
    {
      id: "gerenciamento",
      title: "Gerenciamento",
      description: "Sistema de manutenção de máquinas, obras e estoque de peças",
      icon: HardHat,
      useLogo: true,
      color: "bg-[#E31A1A]",
      hoverColor: "hover:border-[#E31A1A]",
      textColor: "text-[#E31A1A]",
      path: "/gerenciamento/dashboard",
      hasAccess: canAccessGerenciamento,
      features: [
        { icon: Truck, label: "Máquinas" },
        { icon: Wrench, label: "Manutenções" },
        { icon: Package, label: "Estoque" },
      ]
    },
    {
      id: "administrativo",
      title: "Administrativo",
      description: "Sistema financeiro, notas fiscais, fornecedores e ordens de serviço",
      icon: Building2,
      useLogo: false,
      color: "bg-[#D4A000]",
      hoverColor: "hover:border-[#D4A000]",
      textColor: "text-[#D4A000]",
      path: "/administrativo/dashboard",
      hasAccess: canAccessAdministrativo,
      features: [
        { icon: DollarSign, label: "Financeiro" },
        { icon: FileText, label: "NF-e" },
        { icon: Users, label: "Fornecedores" },
      ]
    },
    {
      id: "rh",
      title: "RH",
      description: "Recursos Humanos, ponto eletrônico, folha de pagamento e EPIs",
      icon: Users,
      useLogo: false,
      color: "bg-[#10B981]",
      hoverColor: "hover:border-[#10B981]",
      textColor: "text-[#10B981]",
      path: "/rh/chat",
      hasAccess: canAccessRH,
      features: [
        { icon: Users, label: "Funcionários" },
        { icon: Clock, label: "Ponto" },
        { icon: HardHat, label: "EPIs" },
      ]
    },
    {
      id: "armazenamento",
      title: "Armazenamento",
      description: "Sistema de arquivos e documentos da empresa",
      icon: HardDrive,
      useLogo: false,
      color: "bg-blue-600",
      hoverColor: "hover:border-blue-600",
      textColor: "text-blue-600",
      path: "/armazenamento",
      hasAccess: canAccessArmazenamento,
      features: [
        { icon: FolderOpen, label: "Pastas" },
        { icon: Upload, label: "Upload" },
        { icon: FileText, label: "Documentos" },
      ]
    },
    {
      id: "painel-admin",
      title: "Painel Admin",
      description: "Configurações globais, usuários, permissões e gestão da plataforma",
      icon: Shield,
      useLogo: false,
      color: "bg-green-600",
      hoverColor: "hover:border-green-500",
      textColor: "text-green-500",
      path: "/painel-admin",
      hasAccess: canAccessAdminPanel,
      restrictedLabel: "Apenas administradores",
      features: [
        { icon: Users, label: "Usuários" },
        { icon: Shield, label: "Permissões" },
        { icon: Calculator, label: "Configurações" },
      ]
    }
  ];

  const getRoleBadge = () => {
    const roleInfo = {
      gerenciamento: { label: "Gerenciamento", color: "bg-[#E31A1A]" },
      administrativo: { label: "Administrativo", color: "bg-[#D4A000] text-black" },
      rh: { label: "RH", color: "bg-[#10B981]" },
      ambos: { label: "Ger + Admin", color: "bg-purple-500" },
      ambos_rh: { label: "Ger + Admin + RH", color: "bg-purple-600" },
      gerenciamento_rh: { label: "Ger + RH", color: "bg-pink-500" },
      administrativo_rh: { label: "Admin + RH", color: "bg-orange-500" },
      admin: { label: "Administrador", color: "bg-green-500" }
    };
    const info = roleInfo[userRole] || roleInfo.gerenciamento;
    return <Badge className={`${info.color} text-xs`}>{info.label}</Badge>;
  };

  return (
    <div 
      className="min-h-screen bg-black flex items-center justify-center p-3 sm:p-4"
      style={{ paddingTop: 'env(safe-area-inset-top)', paddingBottom: 'env(safe-area-inset-bottom)' }}
    >
      {/* Background pattern - same as login page */}
      <div className="absolute inset-0 opacity-5">
        <div className="absolute inset-0" style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='1'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`
        }} />
      </div>

      <div className="w-full max-w-6xl relative z-10">
        {/* Header */}
        <div className="text-center mb-4 sm:mb-8">
          <div className="flex items-center justify-center gap-2 sm:gap-3 mb-3 sm:mb-4">
            <img src="/logo.png" alt="Gerenciamento" className="w-10 h-10 sm:w-12 sm:h-12 object-contain" />
            <h1 className="text-2xl sm:text-3xl md:text-4xl font-heading font-black text-white">
              Gerenciamento
            </h1>
          </div>
          <div className="text-gray-400 text-sm sm:text-base flex flex-wrap items-center justify-center gap-2">
            <span>Olá, <span className="text-white font-medium">{user?.name}</span>!</span>
            {getRoleBadge()}
          </div>
          <p className="text-gray-500 text-xs sm:text-sm mt-2">
            Selecione o sistema que deseja acessar:
          </p>
        </div>

        {/* System Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-3 sm:gap-4 px-1">
          {systems.map((system) => (
            <Card
              key={system.id}
              className={`bg-gray-900 border-2 border-gray-800 ${system.hasAccess ? system.hoverColor + ' cursor-pointer hover:shadow-xl hover:-translate-y-1' : 'opacity-50 cursor-not-allowed'} transition-all duration-300`}
              onClick={() => {
                if (system.hasAccess) {
                  navigate(system.path);
                } else if (system.restrictedLabel) {
                  toast.error(`Acesso negado. ${system.restrictedLabel}.`);
                }
              }}
              data-testid={`system-${system.id}`}
            >
              <CardContent className="p-4">
                {/* Icon and Title */}
                <div className="flex items-start gap-3 mb-3">
                  <div className={`w-12 h-12 ${system.color} rounded-xl flex items-center justify-center flex-shrink-0 ${!system.hasAccess && 'grayscale'}`}>
                    {system.useLogo ? (
                      <img src="/logo.png" alt="Logo" className="w-8 h-8 object-contain" />
                    ) : (
                      <system.icon className={system.id === "administrativo" && system.hasAccess ? "text-black" : "text-white"} size={24} />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h2 className="text-lg sm:text-xl font-bold text-white">{system.title}</h2>
                      {!system.hasAccess && (
                        <Lock size={14} className="text-gray-500 flex-shrink-0" />
                      )}
                    </div>
                    <p className="text-xs sm:text-sm text-gray-400 line-clamp-2">{system.description}</p>
                  </div>
                </div>

                {/* Features */}
                <div className="flex flex-wrap items-center gap-2 sm:gap-4 mb-3 sm:mb-4 pt-3 sm:pt-4 border-t border-gray-700">
                  {system.features.map((feature, index) => (
                    <div key={index} className="flex items-center gap-1 sm:gap-2 text-gray-300">
                      <feature.icon size={14} className="text-gray-400" />
                      <span className="text-xs sm:text-sm">{feature.label}</span>
                    </div>
                  ))}
                </div>

                {/* Action */}
                <div className={`flex items-center justify-end gap-2 text-xs sm:text-sm font-medium ${system.hasAccess ? system.textColor : 'text-gray-600'}`}>
                  {system.hasAccess ? (
                    <>
                      <span>Acessar</span>
                      <ArrowRight size={16} />
                    </>
                  ) : (
                    <>
                      <Lock size={12} />
                      <span>Sem acesso</span>
                    </>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Logout Button */}
        <div className="mt-6 sm:mt-8 flex justify-center pb-4 sm:pb-8">
          <Button
            variant="ghost"
            size="sm"
            className="text-gray-400 hover:text-white hover:bg-gray-800 active:bg-gray-700 min-h-[44px] px-4 sm:px-6 text-xs sm:text-sm"
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              handleLogout();
            }}
            data-testid="logout-btn"
          >
            <LogOut size={16} className="mr-1 sm:mr-2" />
            Sair da conta
          </Button>
        </div>

        {/* Footer */}
        <p className="text-center text-gray-500 text-xs sm:text-sm mt-4 sm:mt-6">
          Gerenciamento © 2026
        </p>
      </div>
    </div>
  );
}
