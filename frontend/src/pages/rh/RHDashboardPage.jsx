import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { API } from "@/App";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { 
  Users, Clock, DollarSign, Calendar, HardHat, AlertTriangle,
  TrendingUp, TrendingDown, UserPlus, Gift, AlertCircle, CheckCircle
} from "lucide-react";
import { toast } from "sonner";

export default function RHDashboardPage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    total_funcionarios: 0,
    funcionarios_ativos: 0,
    funcionarios_ferias: 0,
    funcionarios_afastados: 0,
    total_folha: 0,
    aniversariantes_mes: [],
    alertas_ferias: [],
    alertas_epi: [],
    ponto_hoje: { presentes: 0, ausentes: 0, atrasados: 0 }
  });

  useEffect(() => {
    fetchDashboardStats();
  }, []);

  const fetchDashboardStats = async () => {
    try {
      const response = await axios.get(`${API}/rh/dashboard`);
      setStats(response.data);
    } catch (error) {
      console.error("Erro ao carregar dashboard:", error);
      // Set default values if API fails
      setStats({
        total_funcionarios: 0,
        funcionarios_ativos: 0,
        funcionarios_ferias: 0,
        funcionarios_afastados: 0,
        total_folha: 0,
        aniversariantes_mes: [],
        alertas_ferias: [],
        alertas_epi: [],
        ponto_hoje: { presentes: 0, ausentes: 0, atrasados: 0 }
      });
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat("pt-BR", {
      style: "currency",
      currency: "BRL"
    }).format(value || 0);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="spinner w-12 h-12"></div>
      </div>
    );
  }

  return (
    <div data-testid="rh-dashboard-page">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Dashboard RH</h1>
          <p className="text-gray-500 mt-1">Visão geral dos recursos humanos</p>
        </div>
        <Button 
          onClick={() => navigate("/rh/funcionarios")} 
          className="bg-[#10B981] hover:bg-[#059669]"
          data-testid="btn-novo-funcionario"
        >
          <UserPlus size={18} className="mr-2" />
          Novo Funcionário
        </Button>
      </div>

      {/* Cards de estatísticas */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <Card className="cursor-pointer hover:shadow-lg transition-shadow" onClick={() => navigate("/rh/funcionarios")}>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-lg bg-[#10B981]/10 flex items-center justify-center">
                <Users className="text-[#10B981]" size={24} />
              </div>
              <div>
                <p className="text-sm text-gray-500">Total Funcionários</p>
                <p className="text-2xl font-bold">{stats.total_funcionarios}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="cursor-pointer hover:shadow-lg transition-shadow" onClick={() => navigate("/rh/ponto")}>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-lg bg-blue-100 flex items-center justify-center">
                <Clock className="text-blue-600" size={24} />
              </div>
              <div>
                <p className="text-sm text-gray-500">Presentes Hoje</p>
                <p className="text-2xl font-bold">{stats.ponto_hoje.presentes}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="cursor-pointer hover:shadow-lg transition-shadow" onClick={() => navigate("/rh/folha-pagamento")}>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-lg bg-yellow-100 flex items-center justify-center">
                <DollarSign className="text-yellow-600" size={24} />
              </div>
              <div>
                <p className="text-sm text-gray-500">Folha Mensal</p>
                <p className="text-xl font-bold">{formatCurrency(stats.total_folha)}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="cursor-pointer hover:shadow-lg transition-shadow" onClick={() => navigate("/rh/ferias")}>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-lg bg-purple-100 flex items-center justify-center">
                <Calendar className="text-purple-600" size={24} />
              </div>
              <div>
                <p className="text-sm text-gray-500">Em Férias</p>
                <p className="text-2xl font-bold">{stats.funcionarios_ferias}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Grid de informações */}
      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Ponto de Hoje */}
        <Card>
          <CardContent className="p-4">
            <h3 className="font-semibold text-lg mb-4 flex items-center gap-2">
              <Clock size={20} className="text-blue-600" />
              Ponto de Hoje
            </h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                <div className="flex items-center gap-2">
                  <CheckCircle size={18} className="text-green-600" />
                  <span>Presentes</span>
                </div>
                <span className="font-bold text-green-600">{stats.ponto_hoje.presentes}</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-red-50 rounded-lg">
                <div className="flex items-center gap-2">
                  <AlertCircle size={18} className="text-red-600" />
                  <span>Ausentes</span>
                </div>
                <span className="font-bold text-red-600">{stats.ponto_hoje.ausentes}</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-yellow-50 rounded-lg">
                <div className="flex items-center gap-2">
                  <AlertTriangle size={18} className="text-yellow-600" />
                  <span>Atrasados</span>
                </div>
                <span className="font-bold text-yellow-600">{stats.ponto_hoje.atrasados}</span>
              </div>
            </div>
            <Button 
              variant="outline" 
              className="w-full mt-4"
              onClick={() => navigate("/rh/ponto")}
            >
              Ver Detalhes
            </Button>
          </CardContent>
        </Card>

        {/* Aniversariantes do Mês */}
        <Card>
          <CardContent className="p-4">
            <h3 className="font-semibold text-lg mb-4 flex items-center gap-2">
              <Gift size={20} className="text-pink-600" />
              Aniversariantes do Mês
            </h3>
            {stats.aniversariantes_mes.length > 0 ? (
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {stats.aniversariantes_mes.map((func, idx) => (
                  <div key={idx} className="flex items-center justify-between p-2 bg-pink-50 rounded-lg">
                    <span className="font-medium">{func.nome}</span>
                    <span className="text-sm text-gray-500">{func.data_nascimento_formatada}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-center py-4">Nenhum aniversariante este mês</p>
            )}
          </CardContent>
        </Card>

        {/* Alertas de Férias */}
        <Card>
          <CardContent className="p-4">
            <h3 className="font-semibold text-lg mb-4 flex items-center gap-2">
              <Calendar size={20} className="text-orange-600" />
              Alertas de Férias
            </h3>
            {stats.alertas_ferias.length > 0 ? (
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {stats.alertas_ferias.map((alerta, idx) => (
                  <div key={idx} className="flex items-center justify-between p-2 bg-orange-50 rounded-lg">
                    <span className="font-medium text-sm">{alerta.nome}</span>
                    <span className="text-xs text-orange-600">{alerta.mensagem}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-center py-4">Nenhum alerta de férias</p>
            )}
            <Button 
              variant="outline" 
              className="w-full mt-4"
              onClick={() => navigate("/rh/ferias")}
            >
              Ver Calendário
            </Button>
          </CardContent>
        </Card>

        {/* Alertas de EPI */}
        <Card>
          <CardContent className="p-4">
            <h3 className="font-semibold text-lg mb-4 flex items-center gap-2">
              <HardHat size={20} className="text-red-600" />
              Alertas de EPI
            </h3>
            {stats.alertas_epi.length > 0 ? (
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {stats.alertas_epi.map((alerta, idx) => (
                  <div key={idx} className="p-2 bg-red-50 rounded-lg">
                    <p className="font-medium text-sm">{alerta.funcionario}</p>
                    <p className="text-xs text-red-600">{alerta.epi} - Vence em {alerta.dias_restantes} dias</p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-center py-4">Nenhum EPI próximo do vencimento</p>
            )}
            <Button 
              variant="outline" 
              className="w-full mt-4"
              onClick={() => navigate("/rh/epi")}
            >
              Ver Gestão de EPI
            </Button>
          </CardContent>
        </Card>

        {/* Resumo Financeiro */}
        <Card className="md:col-span-2">
          <CardContent className="p-4">
            <h3 className="font-semibold text-lg mb-4 flex items-center gap-2">
              <DollarSign size={20} className="text-green-600" />
              Resumo Financeiro RH
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="p-3 bg-gray-50 rounded-lg text-center">
                <p className="text-sm text-gray-500">Salários</p>
                <p className="text-lg font-bold text-gray-700">{formatCurrency(stats.total_folha * 0.6)}</p>
              </div>
              <div className="p-3 bg-gray-50 rounded-lg text-center">
                <p className="text-sm text-gray-500">Encargos</p>
                <p className="text-lg font-bold text-gray-700">{formatCurrency(stats.total_folha * 0.25)}</p>
              </div>
              <div className="p-3 bg-gray-50 rounded-lg text-center">
                <p className="text-sm text-gray-500">Benefícios</p>
                <p className="text-lg font-bold text-gray-700">{formatCurrency(stats.total_folha * 0.1)}</p>
              </div>
              <div className="p-3 bg-gray-50 rounded-lg text-center">
                <p className="text-sm text-gray-500">EPIs</p>
                <p className="text-lg font-bold text-gray-700">{formatCurrency(stats.total_folha * 0.05)}</p>
              </div>
            </div>
            <Button 
              variant="outline" 
              className="w-full mt-4"
              onClick={() => navigate("/rh/custos")}
            >
              Ver Gestão de Custos
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
