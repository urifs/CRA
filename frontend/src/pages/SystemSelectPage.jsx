import { useNavigate } from "react-router-dom";
import { useAuth } from "@/App";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { 
  Landmark, 
  Building2,
  Truck,
  Wrench,
  DollarSign,
  FileText,
  Package,
  Users,
  ArrowRight,
  Shield,
  Lock
} from "lucide-react";

export default function SystemSelectPage() {
  const navigate = useNavigate();
  const { user } = useAuth();

  // Verificar permissões baseado no role do usuário
  const userRole = user?.role || "gerenciamento";
  
  const canAccessGerenciamento = ["gerenciamento", "ambos", "admin"].includes(userRole);
  const canAccessAdministrativo = ["administrativo", "ambos", "admin"].includes(userRole);
  const canAccessAdminPanel = userRole === "admin";

  const systems = [
    {
      id: "gerenciamento",
      title: "Gerenciamento Geral",
      description: "Sistema de manutenção de máquinas, obras e estoque de peças",
      icon: Landmark,
      color: "bg-[#E31A1A]",
      hoverColor: "hover:border-[#E31A1A]",
      textColor: "text-[#E31A1A]",
      path: "/dashboard",
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
      color: "bg-[#FFC232]",
      hoverColor: "hover:border-[#FFC232]",
      textColor: "text-[#FFC232]",
      path: "/administrativo/dashboard",
      hasAccess: canAccessAdministrativo,
      features: [
        { icon: DollarSign, label: "Financeiro" },
        { icon: FileText, label: "NF-e" },
        { icon: Users, label: "Fornecedores" },
      ]
    }
  ];

  const getRoleBadge = () => {
    const roleInfo = {
      gerenciamento: { label: "Gerenciamento", color: "bg-[#E31A1A]" },
      administrativo: { label: "Administrativo", color: "bg-[#FFC232] text-black" },
      ambos: { label: "Acesso Duplo", color: "bg-purple-500" },
      admin: { label: "Administrador", color: "bg-green-500" }
    };
    const info = roleInfo[userRole] || roleInfo.gerenciamento;
    return <Badge className={`${info.color} text-xs`}>{info.label}</Badge>;
  };

  return (
    <div 
      className="min-h-screen bg-black flex items-center justify-center p-4"
      style={{ paddingTop: 'env(safe-area-inset-top)', paddingBottom: 'env(safe-area-inset-bottom)' }}
    >
      <div className="w-full max-w-4xl">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-3 mb-4">
            <Landmark className="text-[#E31A1A]" size={40} />
            <h1 className="text-3xl md:text-4xl font-heading font-black text-white">
              CRA Construtora
            </h1>
          </div>
          <p className="text-gray-400">
            Olá, <span className="text-white font-medium">{user?.name}</span>! {getRoleBadge()}
          </p>
          <p className="text-gray-500 text-sm mt-2">
            Selecione o sistema que deseja acessar:
          </p>
        </div>

        {/* System Cards */}
        <div className="grid md:grid-cols-2 gap-6">
          {systems.map((system) => (
            <Card
              key={system.id}
              className={`bg-gray-900 border-2 border-gray-800 ${system.hasAccess ? system.hoverColor + ' cursor-pointer hover:shadow-xl hover:-translate-y-1' : 'opacity-50 cursor-not-allowed'} transition-all duration-300`}
              onClick={() => system.hasAccess && navigate(system.path)}
              data-testid={`system-${system.id}`}
            >
              <CardContent className="p-6">
                {/* Icon and Title */}
                <div className="flex items-start gap-4 mb-4">
                  <div className={`w-14 h-14 ${system.color} rounded-xl flex items-center justify-center flex-shrink-0 ${!system.hasAccess && 'grayscale'}`}>
                    <system.icon className={system.id === "administrativo" && system.hasAccess ? "text-black" : "text-white"} size={28} />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <h2 className="text-xl font-bold text-white">{system.title}</h2>
                      {!system.hasAccess && (
                        <Lock size={16} className="text-gray-500" />
                      )}
                    </div>
                    <p className="text-sm text-gray-400">{system.description}</p>
                  </div>
                </div>

                {/* Features */}
                <div className="flex items-center gap-4 mb-4 pt-4 border-t border-gray-700">
                  {system.features.map((feature, index) => (
                    <div key={index} className="flex items-center gap-2 text-gray-300">
                      <feature.icon size={16} className="text-gray-400" />
                      <span className="text-sm">{feature.label}</span>
                    </div>
                  ))}
                </div>

                {/* Action */}
                <div className={`flex items-center justify-end gap-2 text-sm font-medium ${system.hasAccess ? system.textColor : 'text-gray-600'}`}>
                  {system.hasAccess ? (
                    <>
                      <span>Acessar</span>
                      <ArrowRight size={18} />
                    </>
                  ) : (
                    <>
                      <Lock size={14} />
                      <span>Sem acesso</span>
                    </>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Admin Panel Button - Only for admin users */}
        {canAccessAdminPanel && (
          <div className="mt-8 flex justify-center">
            <Button
              variant="outline"
              className="bg-transparent border-green-700 text-green-500 hover:bg-green-900/30 hover:text-green-400 hover:border-green-600"
              onClick={() => navigate("/painel-admin")}
              data-testid="admin-panel-btn"
            >
              <Shield size={18} className="mr-2" />
              Painel Administrativo
            </Button>
          </div>
        )}

        {/* Footer */}
        <p className="text-center text-gray-500 text-sm mt-8">
          CRA Construtora © 2026 - Sistema de Gestão Empresarial
        </p>
      </div>
    </div>
  );
}
