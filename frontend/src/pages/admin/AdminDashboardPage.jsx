import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "@/App";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { 
  DollarSign, 
  TrendingUp, 
  TrendingDown,
  FileText,
  Users,
  Package,
  ClipboardList,
  AlertCircle,
  Calendar
} from "lucide-react";

export default function AdminDashboardPage() {
  const [stats, setStats] = useState({
    totalPagar: 0,
    totalReceber: 0,
    saldoPrevisto: 0,
    contasVencidas: 0,
    notasEmitidas: 0,
    fornecedores: 0,
    produtos: 0,
    ordensAbertas: 0
  });
  const [contasProximas, setContasProximas] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const response = await axios.get(`${API}/admin/dashboard`);
      setStats(response.data.stats);
      setContasProximas(response.data.contasProximas || []);
    } catch (error) {
      console.error("Erro ao carregar dashboard:", error);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
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
    <div data-testid="admin-dashboard">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Dashboard Administrativo</h1>
          <p className="text-slate-500 mt-1">Visão geral financeira e operacional</p>
        </div>
      </div>

      {/* Financial Summary */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <Card className="stat-card border-l-4 border-l-red-500">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-500 uppercase tracking-wide">
                  Total a Pagar
                </p>
                <p className="text-2xl font-bold text-red-600 mt-1">
                  {formatCurrency(stats.totalPagar)}
                </p>
              </div>
              <div className="w-12 h-12 bg-red-100 rounded-lg flex items-center justify-center">
                <TrendingDown className="text-red-600" size={24} />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="stat-card border-l-4 border-l-green-500">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-500 uppercase tracking-wide">
                  Total a Receber
                </p>
                <p className="text-2xl font-bold text-green-600 mt-1">
                  {formatCurrency(stats.totalReceber)}
                </p>
              </div>
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                <TrendingUp className="text-green-600" size={24} />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="stat-card border-l-4 border-l-blue-500">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-500 uppercase tracking-wide">
                  Saldo Previsto
                </p>
                <p className={`text-2xl font-bold mt-1 ${stats.saldoPrevisto >= 0 ? 'text-blue-600' : 'text-red-600'}`}>
                  {formatCurrency(stats.saldoPrevisto)}
                </p>
              </div>
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                <DollarSign className="text-blue-600" size={24} />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="stat-card border-l-4 border-l-orange-500">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-500 uppercase tracking-wide">
                  Contas Vencidas
                </p>
                <p className="text-2xl font-bold text-orange-600 mt-1">
                  {stats.contasVencidas}
                </p>
              </div>
              <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center">
                <AlertCircle className="text-orange-600" size={24} />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Secondary Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <Card className="stat-card">
          <CardContent className="p-4 flex items-center gap-3">
            <div className="w-10 h-10 bg-slate-100 rounded-lg flex items-center justify-center">
              <FileText className="text-slate-600" size={20} />
            </div>
            <div>
              <p className="text-xs text-slate-500">NF-e Emitidas</p>
              <p className="text-lg font-bold text-slate-900">{stats.notasEmitidas}</p>
            </div>
          </CardContent>
        </Card>

        <Card className="stat-card">
          <CardContent className="p-4 flex items-center gap-3">
            <div className="w-10 h-10 bg-slate-100 rounded-lg flex items-center justify-center">
              <Users className="text-slate-600" size={20} />
            </div>
            <div>
              <p className="text-xs text-slate-500">Fornecedores</p>
              <p className="text-lg font-bold text-slate-900">{stats.fornecedores}</p>
            </div>
          </CardContent>
        </Card>

        <Card className="stat-card">
          <CardContent className="p-4 flex items-center gap-3">
            <div className="w-10 h-10 bg-slate-100 rounded-lg flex items-center justify-center">
              <Package className="text-slate-600" size={20} />
            </div>
            <div>
              <p className="text-xs text-slate-500">Produtos</p>
              <p className="text-lg font-bold text-slate-900">{stats.produtos}</p>
            </div>
          </CardContent>
        </Card>

        <Card className="stat-card">
          <CardContent className="p-4 flex items-center gap-3">
            <div className="w-10 h-10 bg-slate-100 rounded-lg flex items-center justify-center">
              <ClipboardList className="text-slate-600" size={20} />
            </div>
            <div>
              <p className="text-xs text-slate-500">OS Abertas</p>
              <p className="text-lg font-bold text-slate-900">{stats.ordensAbertas}</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Upcoming bills */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar size={20} />
            <span>Próximos Vencimentos</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {contasProximas.length === 0 ? (
            <div className="text-center py-8 text-slate-400">
              <Calendar className="mx-auto mb-2" size={32} />
              <p>Nenhuma conta próxima ao vencimento</p>
            </div>
          ) : (
            <div className="space-y-3">
              {contasProximas.map((conta, index) => (
                <div 
                  key={index}
                  className="flex items-center justify-between p-3 bg-slate-50 rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    <div className={`w-2 h-2 rounded-full ${conta.tipo === 'pagar' ? 'bg-red-500' : 'bg-green-500'}`} />
                    <div>
                      <p className="font-medium text-slate-900">{conta.descricao}</p>
                      <p className="text-xs text-slate-500">
                        Vencimento: {new Date(conta.vencimento).toLocaleDateString('pt-BR')}
                      </p>
                    </div>
                  </div>
                  <span className={`font-bold ${conta.tipo === 'pagar' ? 'text-red-600' : 'text-green-600'}`}>
                    {formatCurrency(conta.valor)}
                  </span>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
