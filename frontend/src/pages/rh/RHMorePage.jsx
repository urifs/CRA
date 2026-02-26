import { useNavigate } from "react-router-dom";
import { Card, CardContent } from "@/components/ui/card";
import { 
  DollarSign, Calendar, HardHat, Calculator, 
  ChevronRight, FileText
} from "lucide-react";

export default function RHMorePage() {
  const navigate = useNavigate();

  const menuItems = [
    {
      title: "Folha de Pagamento",
      description: "Gestão de salários, benefícios e holerites",
      icon: DollarSign,
      path: "/rh/folha-pagamento",
      color: "bg-green-500"
    },
    {
      title: "Férias e Escalas",
      description: "Calendário de férias e alertas de vencimento",
      icon: Calendar,
      path: "/rh/ferias",
      color: "bg-blue-500"
    },
    {
      title: "Gestão de EPI/EPC",
      description: "Fichas de EPI, mapa de risco e validades",
      icon: HardHat,
      path: "/rh/epi",
      color: "bg-orange-500"
    },
    {
      title: "Gestão de Custos",
      description: "Custo real por funcionário, dissídio e rescisão",
      icon: Calculator,
      path: "/rh/custos",
      color: "bg-purple-500"
    }
  ];

  return (
    <div data-testid="rh-more-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Mais Opções</h1>
          <p className="text-gray-500 mt-1">Acesse todas as funções do sistema RH</p>
        </div>
      </div>

      <div className="grid gap-3">
        {menuItems.map((item) => (
          <Card 
            key={item.path}
            className="cursor-pointer hover:shadow-lg transition-shadow"
            onClick={() => navigate(item.path)}
          >
            <CardContent className="p-4">
              <div className="flex items-center gap-4">
                <div className={`w-12 h-12 ${item.color} rounded-lg flex items-center justify-center`}>
                  <item.icon className="text-white" size={24} />
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold">{item.title}</h3>
                  <p className="text-sm text-gray-500">{item.description}</p>
                </div>
                <ChevronRight className="text-gray-400" size={20} />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
