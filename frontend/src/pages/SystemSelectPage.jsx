import { useNavigate } from "react-router-dom";
import { useAuth } from "@/App";
import { Card, CardContent } from "@/components/ui/card";
import { 
  Construction, 
  Building2,
  Truck,
  Wrench,
  DollarSign,
  FileText,
  Package,
  Users,
  ClipboardList,
  ArrowRight
} from "lucide-react";

export default function SystemSelectPage() {
  const navigate = useNavigate();
  const { user } = useAuth();

  const systems = [
    {
      id: "gerenciamento",
      title: "Gerenciamento Geral",
      description: "Sistema de manutenção de máquinas, obras e estoque de peças",
      icon: Construction,
      color: "bg-orange-500",
      hoverColor: "hover:border-orange-500",
      path: "/gerenciamento/dashboard",
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
      color: "bg-blue-600",
      hoverColor: "hover:border-blue-600",
      path: "/administrativo/dashboard",
      features: [
        { icon: DollarSign, label: "Financeiro" },
        { icon: FileText, label: "NF-e" },
        { icon: Users, label: "Fornecedores" },
      ]
    }
  ];

  return (
    <div 
      className="min-h-screen bg-slate-900 flex items-center justify-center p-4"
      style={{ paddingTop: 'env(safe-area-inset-top)', paddingBottom: 'env(safe-area-inset-bottom)' }}
    >
      <div className="w-full max-w-4xl">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-3 mb-4">
            <Construction className="text-orange-500" size={40} />
            <h1 className="text-3xl md:text-4xl font-heading font-black text-white">
              CRA Construtora
            </h1>
          </div>
          <p className="text-slate-400">
            Olá, <span className="text-white font-medium">{user?.name}</span>! Selecione o sistema que deseja acessar:
          </p>
        </div>

        {/* System Cards */}
        <div className="grid md:grid-cols-2 gap-6">
          {systems.map((system) => (
            <Card
              key={system.id}
              className={`bg-slate-800 border-2 border-slate-700 ${system.hoverColor} cursor-pointer transition-all duration-300 hover:shadow-xl hover:shadow-${system.color}/20 hover:-translate-y-1`}
              onClick={() => navigate(system.path)}
              data-testid={`system-${system.id}`}
            >
              <CardContent className="p-6">
                {/* Icon and Title */}
                <div className="flex items-start gap-4 mb-4">
                  <div className={`w-14 h-14 ${system.color} rounded-xl flex items-center justify-center flex-shrink-0`}>
                    <system.icon className="text-white" size={28} />
                  </div>
                  <div className="flex-1">
                    <h2 className="text-xl font-bold text-white mb-1">{system.title}</h2>
                    <p className="text-sm text-slate-400">{system.description}</p>
                  </div>
                </div>

                {/* Features */}
                <div className="flex items-center gap-4 mb-4 pt-4 border-t border-slate-700">
                  {system.features.map((feature, index) => (
                    <div key={index} className="flex items-center gap-2 text-slate-300">
                      <feature.icon size={16} className="text-slate-400" />
                      <span className="text-sm">{feature.label}</span>
                    </div>
                  ))}
                </div>

                {/* Action */}
                <div className={`flex items-center justify-end gap-2 text-sm font-medium ${system.color.replace('bg-', 'text-')}`}>
                  <span>Acessar</span>
                  <ArrowRight size={18} />
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Footer */}
        <p className="text-center text-slate-500 text-sm mt-8">
          CRA Construtora © 2026 - Sistema de Gestão Empresarial
        </p>
      </div>
    </div>
  );
}
