import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "@/App";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { 
  Bell, Gift, Calendar, HardHat, Clock, AlertTriangle, 
  CheckCircle, Users, FileText, ChevronRight
} from "lucide-react";
import { toast } from "sonner";
import { useNavigate } from "react-router-dom";

export default function RHNotificacoesPage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [notificacoes, setNotificacoes] = useState({
    aniversariantes: [],
    alertas_ferias: [],
    alertas_epi: [],
    alertas_atestados: [],
    inconsistencias_ponto: [],
    funcionarios_sem_ferias: []
  });

  useEffect(() => {
    fetchNotificacoes();
  }, []);

  const fetchNotificacoes = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/rh/notificacoes`);
      setNotificacoes(response.data);
    } catch (error) {
      console.error("Erro ao carregar notificações:", error);
    } finally {
      setLoading(false);
    }
  };

  const totalAlertas = 
    notificacoes.alertas_ferias.length +
    notificacoes.alertas_epi.length +
    notificacoes.alertas_atestados.length +
    notificacoes.inconsistencias_ponto.length +
    notificacoes.funcionarios_sem_ferias.length;

  if (loading) {
    return <div className="flex items-center justify-center min-h-[400px]"><div className="spinner w-12 h-12"></div></div>;
  }

  return (
    <div data-testid="rh-notificacoes-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Notificações RH</h1>
          <p className="text-gray-500 mt-1">Alertas e lembretes importantes</p>
        </div>
        <Button onClick={fetchNotificacoes} variant="outline">
          Atualizar
        </Button>
      </div>

      {/* Resumo */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <Card className="cursor-pointer hover:shadow-lg" onClick={() => document.getElementById('aniversariantes')?.scrollIntoView({ behavior: 'smooth' })}>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="w-12 h-12 rounded-lg bg-pink-100 flex items-center justify-center">
              <Gift className="text-pink-600" size={24} />
            </div>
            <div>
              <p className="text-2xl font-bold text-pink-600">{notificacoes.aniversariantes.length}</p>
              <p className="text-sm text-gray-500">Aniversariantes</p>
            </div>
          </CardContent>
        </Card>

        <Card className="cursor-pointer hover:shadow-lg" onClick={() => document.getElementById('ferias')?.scrollIntoView({ behavior: 'smooth' })}>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="w-12 h-12 rounded-lg bg-orange-100 flex items-center justify-center">
              <Calendar className="text-orange-600" size={24} />
            </div>
            <div>
              <p className="text-2xl font-bold text-orange-600">{notificacoes.alertas_ferias.length + notificacoes.funcionarios_sem_ferias.length}</p>
              <p className="text-sm text-gray-500">Alertas Férias</p>
            </div>
          </CardContent>
        </Card>

        <Card className="cursor-pointer hover:shadow-lg" onClick={() => document.getElementById('epi')?.scrollIntoView({ behavior: 'smooth' })}>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="w-12 h-12 rounded-lg bg-red-100 flex items-center justify-center">
              <HardHat className="text-red-600" size={24} />
            </div>
            <div>
              <p className="text-2xl font-bold text-red-600">{notificacoes.alertas_epi.length}</p>
              <p className="text-sm text-gray-500">EPIs Vencendo</p>
            </div>
          </CardContent>
        </Card>

        <Card className="cursor-pointer hover:shadow-lg" onClick={() => document.getElementById('ponto')?.scrollIntoView({ behavior: 'smooth' })}>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="w-12 h-12 rounded-lg bg-yellow-100 flex items-center justify-center">
              <Clock className="text-yellow-600" size={24} />
            </div>
            <div>
              <p className="text-2xl font-bold text-yellow-600">{notificacoes.inconsistencias_ponto.length}</p>
              <p className="text-sm text-gray-500">Inconsistências</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Aniversariantes do Mês */}
      <Card className="mb-6" id="aniversariantes">
        <CardContent className="p-4">
          <h3 className="font-semibold text-lg mb-4 flex items-center gap-2">
            <Gift className="text-pink-600" size={20} />
            Aniversariantes do Mês
          </h3>
          
          {notificacoes.aniversariantes.length === 0 ? (
            <p className="text-center text-gray-400 py-4">Nenhum aniversariante este mês</p>
          ) : (
            <div className="grid gap-2">
              {notificacoes.aniversariantes.map((func, idx) => (
                <div key={idx} className="flex items-center justify-between p-3 bg-pink-50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-pink-200 rounded-full flex items-center justify-center">
                      🎂
                    </div>
                    <div>
                      <p className="font-medium">{func.nome}</p>
                      <p className="text-sm text-gray-500">{func.cargo}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-bold text-pink-600">{func.data_formatada}</p>
                    {func.idade && <p className="text-sm text-gray-500">{func.idade} anos</p>}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Alertas de Férias */}
      <Card className="mb-6" id="ferias">
        <CardContent className="p-4">
          <h3 className="font-semibold text-lg mb-4 flex items-center gap-2">
            <Calendar className="text-orange-600" size={20} />
            Alertas de Férias
          </h3>
          
          {notificacoes.alertas_ferias.length === 0 && notificacoes.funcionarios_sem_ferias.length === 0 ? (
            <div className="flex items-center gap-2 text-green-600 py-4">
              <CheckCircle size={20} />
              <span>Todos os períodos aquisitivos estão em dia</span>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Vencimento próximo */}
              {notificacoes.alertas_ferias.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-orange-600 mb-2">Período Aquisitivo Vencendo</h4>
                  <div className="grid gap-2">
                    {notificacoes.alertas_ferias.map((alerta, idx) => (
                      <div key={idx} className="flex items-center justify-between p-3 bg-orange-50 rounded-lg">
                        <div>
                          <p className="font-medium">{alerta.nome}</p>
                          <p className="text-sm text-gray-500">{alerta.mensagem}</p>
                        </div>
                        <Button size="sm" variant="outline" onClick={() => navigate('/rh/ferias')}>
                          Agendar
                        </Button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Mais de 1 ano sem férias */}
              {notificacoes.funcionarios_sem_ferias.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-red-600 mb-2 flex items-center gap-1">
                    <AlertTriangle size={14} />
                    Mais de 1 ano sem férias
                  </h4>
                  <div className="grid gap-2">
                    {notificacoes.funcionarios_sem_ferias.map((func, idx) => (
                      <div key={idx} className="flex items-center justify-between p-3 bg-red-50 rounded-lg">
                        <div>
                          <p className="font-medium">{func.nome}</p>
                          <p className="text-sm text-red-600">Última férias: {func.ultima_ferias || 'Nunca tirou férias'}</p>
                        </div>
                        <Button size="sm" className="bg-red-500 hover:bg-red-600" onClick={() => navigate('/rh/ferias')}>
                          Agendar Urgente
                        </Button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Alertas de EPI */}
      <Card className="mb-6" id="epi">
        <CardContent className="p-4">
          <h3 className="font-semibold text-lg mb-4 flex items-center gap-2">
            <HardHat className="text-red-600" size={20} />
            Vencimento de EPIs
          </h3>
          
          {notificacoes.alertas_epi.length === 0 ? (
            <div className="flex items-center gap-2 text-green-600 py-4">
              <CheckCircle size={20} />
              <span>Todos os EPIs estão dentro da validade</span>
            </div>
          ) : (
            <div className="grid gap-2">
              {notificacoes.alertas_epi.map((alerta, idx) => (
                <div key={idx} className="flex items-center justify-between p-3 bg-red-50 rounded-lg">
                  <div>
                    <p className="font-medium">{alerta.funcionario}</p>
                    <p className="text-sm text-red-600">{alerta.epi} - Vence em {alerta.dias_restantes} dias</p>
                  </div>
                  <Button size="sm" variant="outline" className="border-red-500 text-red-500" onClick={() => navigate('/rh/epi')}>
                    Substituir
                  </Button>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Alertas de Atestados */}
      {notificacoes.alertas_atestados.length > 0 && (
        <Card className="mb-6">
          <CardContent className="p-4">
            <h3 className="font-semibold text-lg mb-4 flex items-center gap-2">
              <FileText className="text-blue-600" size={20} />
              Vencimento de Atestados Médicos
            </h3>
            
            <div className="grid gap-2">
              {notificacoes.alertas_atestados.map((alerta, idx) => (
                <div key={idx} className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
                  <div>
                    <p className="font-medium">{alerta.funcionario}</p>
                    <p className="text-sm text-blue-600">{alerta.tipo} - Vence em {alerta.dias_restantes} dias</p>
                  </div>
                  <Button size="sm" variant="outline">
                    Ver
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Inconsistências de Ponto */}
      <Card className="mb-6" id="ponto">
        <CardContent className="p-4">
          <h3 className="font-semibold text-lg mb-4 flex items-center gap-2">
            <Clock className="text-yellow-600" size={20} />
            Inconsistências de Ponto
          </h3>
          
          {notificacoes.inconsistencias_ponto.length === 0 ? (
            <div className="flex items-center gap-2 text-green-600 py-4">
              <CheckCircle size={20} />
              <span>Nenhuma inconsistência de ponto hoje</span>
            </div>
          ) : (
            <div className="grid gap-2">
              {notificacoes.inconsistencias_ponto.map((inc, idx) => (
                <div key={idx} className="flex items-center justify-between p-3 bg-yellow-50 rounded-lg">
                  <div>
                    <p className="font-medium">{inc.funcionario}</p>
                    <p className="text-sm text-yellow-600">{inc.tipo}: {inc.detalhe}</p>
                  </div>
                  <Button size="sm" variant="outline" onClick={() => navigate('/rh/ponto')}>
                    Corrigir
                  </Button>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Sem alertas */}
      {totalAlertas === 0 && (
        <Card className="bg-green-50 border-green-200">
          <CardContent className="p-8 text-center">
            <CheckCircle className="mx-auto text-green-600 mb-4" size={48} />
            <h3 className="text-xl font-bold text-green-700 mb-2">Tudo em ordem!</h3>
            <p className="text-green-600">Não há alertas pendentes no momento.</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
