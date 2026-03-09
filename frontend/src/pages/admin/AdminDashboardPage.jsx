import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "@/App";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { 
  DollarSign, 
  TrendingUp, 
  TrendingDown,
  FileText,
  Users,
  Package,
  ClipboardList,
  AlertCircle,
  Calendar,
  CheckCircle2,
  Clock,
  Wallet,
  BadgeDollarSign,
  Search,
  Filter,
  AlertTriangle,
  XCircle
} from "lucide-react";

export default function AdminDashboardPage() {
  const [data, setData] = useState({
    stats: { totalPagar: 0, totalReceber: 0, saldoPrevisto: 0, contasVencidas: 0 },
    aPagar: { total: 0, mes: 0, ano: 0, vencidas: 0, osValor: 0 },
    aReceber: { total: 0, mes: 0, ano: 0, vencidas: 0, osValor: 0 },
    quitados: { pagar: { total: 0, mes: 0, ano: 0 }, receber: { total: 0, mes: 0, ano: 0 } },
    contasProximas: [],
    vencidas: { pagar: { quantidade: 0, valor: 0, lista: [] }, receber: { quantidade: 0, valor: 0, lista: [] }, totalQuantidade: 0, totalValor: 0 }
  });
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("resumo");
  
  // Filters
  const [searchTerm, setSearchTerm] = useState("");
  const [filterCentroCusto, setFilterCentroCusto] = useState("");
  const [filterPlanoContas, setFilterPlanoContas] = useState("");
  const [filterStatus, setFilterStatus] = useState("");
  
  // Data for filters
  const [centrosCusto, setCentrosCusto] = useState([]);
  const [planosContas, setPlanosContas] = useState([]);
  const [contasPagar, setContasPagar] = useState([]);
  const [contasReceber, setContasReceber] = useState([]);

  useEffect(() => {
    fetchDashboardData();
    fetchFilterData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const response = await axios.get(`${API}/admin/dashboard`);
      setData(response.data);
    } catch (error) {
      console.error("Erro ao carregar dashboard:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchFilterData = async () => {
    try {
      const [ccRes, pcRes, cpRes, crRes] = await Promise.all([
        axios.get(`${API}/admin/centros-custo`),
        axios.get(`${API}/admin/plano-contas`),
        axios.get(`${API}/admin/contas-pagar`),
        axios.get(`${API}/admin/contas-receber`)
      ]);
      setCentrosCusto(ccRes.data);
      setPlanosContas(pcRes.data);
      setContasPagar(cpRes.data);
      setContasReceber(crRes.data);
    } catch (error) {
      console.error("Erro ao carregar dados de filtro:", error);
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

  const { stats, aPagar, aReceber, quitados, contasProximas, vencidas } = data;

  // Componente de filtros reutilizável
  const FilterBar = () => (
    <Card className="mb-6">
      <CardContent className="p-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
            <Input
              placeholder="Buscar por descrição..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-9"
            />
          </div>
          <Select value={filterCentroCusto} onValueChange={setFilterCentroCusto}>
            <SelectTrigger>
              <SelectValue placeholder="Centro de Custo" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todos</SelectItem>
              {centrosCusto.map(cc => (
                <SelectItem key={cc.id} value={cc.id}>{cc.nome}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={filterPlanoContas} onValueChange={setFilterPlanoContas}>
            <SelectTrigger>
              <SelectValue placeholder="Plano de Contas" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todos</SelectItem>
              {planosContas.map(pc => (
                <SelectItem key={pc.id} value={pc.id}>{pc.nome}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={filterStatus} onValueChange={setFilterStatus}>
            <SelectTrigger>
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todos</SelectItem>
              <SelectItem value="pendente">Pendente</SelectItem>
              <SelectItem value="vencido">Vencido</SelectItem>
              <SelectItem value="pago">Pago/Recebido</SelectItem>
            </SelectContent>
          </Select>
          <Button className="bg-[#D4A000] hover:bg-[#b38900] text-black">
            <Search size={16} className="mr-2" />
            Buscar
          </Button>
        </div>
      </CardContent>
    </Card>
  );

  return (
    <div data-testid="admin-dashboard">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Dashboard Financeiro</h1>
          <p className="text-gray-500 mt-1">Visão geral financeira e operacional</p>
        </div>
      </div>

      {/* Tabs principais */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="mb-6">
        <TabsList className="grid grid-cols-5 w-full max-w-3xl">
          <TabsTrigger value="resumo" className="flex items-center gap-2">
            <Wallet size={16} />
            Resumo
          </TabsTrigger>
          <TabsTrigger value="vencidas" className="flex items-center gap-2" data-testid="tab-vencidas">
            <AlertTriangle size={16} />
            Vencidas
            {(vencidas?.totalQuantidade > 0) && (
              <span className="bg-red-600 text-white text-xs px-1.5 py-0.5 rounded-full animate-pulse">{vencidas.totalQuantidade}</span>
            )}
          </TabsTrigger>
          <TabsTrigger value="pagar" className="flex items-center gap-2">
            <TrendingDown size={16} />
            A Pagar
            {aPagar.vencidas > 0 && (
              <span className="bg-red-500 text-white text-xs px-1.5 py-0.5 rounded-full">{aPagar.vencidas}</span>
            )}
          </TabsTrigger>
          <TabsTrigger value="receber" className="flex items-center gap-2">
            <TrendingUp size={16} />
            A Receber
            {aReceber.vencidas > 0 && (
              <span className="bg-[#E31A1A] text-white text-xs px-1.5 py-0.5 rounded-full">{aReceber.vencidas}</span>
            )}
          </TabsTrigger>
          <TabsTrigger value="quitados" className="flex items-center gap-2">
            <CheckCircle2 size={16} />
            Quitados
          </TabsTrigger>
        </TabsList>

        {/* Tab: Resumo */}
        <TabsContent value="resumo" className="mt-6">
          {/* Filters */}
          <FilterBar />
          
          {/* Financial Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            <Card className="stat-card border-l-4 border-l-red-500">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">Total a Pagar</p>
                    <p className="text-2xl font-bold text-red-600 mt-1">{formatCurrency(stats.totalPagar)}</p>
                    <p className="text-xs text-gray-400 mt-1">+ {formatCurrency(aPagar.osValor)} em OS</p>
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
                    <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">Total a Receber</p>
                    <p className="text-2xl font-bold text-green-600 mt-1">{formatCurrency(stats.totalReceber)}</p>
                    <p className="text-xs text-gray-400 mt-1">+ {formatCurrency(aReceber.osValor)} em OS</p>
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
                    <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">Saldo Previsto</p>
                    <p className={`text-2xl font-bold mt-1 ${stats.saldoPrevisto >= 0 ? 'text-[#D4A000]' : 'text-red-600'}`}>
                      {formatCurrency(stats.saldoPrevisto)}
                    </p>
                  </div>
                  <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                    <DollarSign className="text-[#D4A000]" size={24} />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="stat-card border-l-4 border-l-orange-500">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">Contas Vencidas</p>
                    <p className="text-2xl font-bold text-[#E31A1A] mt-1">{stats.contasVencidas}</p>
                  </div>
                  <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center">
                    <AlertCircle className="text-[#E31A1A]" size={24} />
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Secondary Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            <Card className="stat-card">
              <CardContent className="p-4 flex items-center gap-3">
                <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
                  <FileText className="text-gray-600" size={20} />
                </div>
                <div>
                  <p className="text-xs text-gray-500">NF-e Emitidas</p>
                  <p className="text-lg font-bold text-black">{stats.notasEmitidas || 0}</p>
                </div>
              </CardContent>
            </Card>

            <Card className="stat-card">
              <CardContent className="p-4 flex items-center gap-3">
                <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
                  <Users className="text-gray-600" size={20} />
                </div>
                <div>
                  <p className="text-xs text-gray-500">Fornecedores</p>
                  <p className="text-lg font-bold text-black">{stats.fornecedores || 0}</p>
                </div>
              </CardContent>
            </Card>

            <Card className="stat-card">
              <CardContent className="p-4 flex items-center gap-3">
                <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
                  <Package className="text-gray-600" size={20} />
                </div>
                <div>
                  <p className="text-xs text-gray-500">Produtos</p>
                  <p className="text-lg font-bold text-black">{stats.produtos || 0}</p>
                </div>
              </CardContent>
            </Card>

            <Card className="stat-card">
              <CardContent className="p-4 flex items-center gap-3">
                <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
                  <ClipboardList className="text-gray-600" size={20} />
                </div>
                <div>
                  <p className="text-xs text-gray-500">OS Abertas</p>
                  <p className="text-lg font-bold text-black">{stats.ordensAbertas || 0}</p>
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
                <div className="text-center py-8 text-gray-400">
                  <Calendar className="mx-auto mb-2" size={32} />
                  <p>Nenhuma conta próxima ao vencimento</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {contasProximas.map((conta, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-white rounded-lg">
                      <div className="flex items-center gap-3">
                        <div className={`w-2 h-2 rounded-full ${conta.tipo === 'pagar' ? 'bg-red-500' : 'bg-green-500'}`} />
                        <div>
                          <p className="font-medium text-black">{conta.descricao}</p>
                          <p className="text-xs text-gray-500">
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
        </TabsContent>

        {/* Tab: Vencidas */}
        <TabsContent value="vencidas" className="mt-6" data-testid="tab-content-vencidas">
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <Card className="border-l-4 border-l-red-600 bg-red-50">
              <CardContent className="p-6">
                <div className="flex justify-between items-start">
                  <div>
                    <p className="text-sm text-gray-600 font-medium">Total Vencido</p>
                    <p className="text-3xl font-bold text-red-700 mt-1">{formatCurrency(vencidas?.totalValor || 0)}</p>
                    <p className="text-sm text-red-600 mt-2">
                      {vencidas?.totalQuantidade || 0} conta(s) vencida(s)
                    </p>
                  </div>
                  <div className="w-14 h-14 bg-red-200 rounded-full flex items-center justify-center">
                    <AlertTriangle className="text-red-700" size={28} />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="border-l-4 border-l-red-500">
              <CardContent className="p-6">
                <div className="flex justify-between items-start">
                  <div>
                    <p className="text-sm text-gray-500">A Pagar Vencido</p>
                    <p className="text-2xl font-bold text-red-600 mt-1">{formatCurrency(vencidas?.pagar?.valor || 0)}</p>
                    <p className="text-xs text-gray-400 mt-1">{vencidas?.pagar?.quantidade || 0} conta(s)</p>
                  </div>
                  <div className="w-12 h-12 bg-red-100 rounded-lg flex items-center justify-center">
                    <TrendingDown className="text-red-600" size={24} />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="border-l-4 border-l-orange-500">
              <CardContent className="p-6">
                <div className="flex justify-between items-start">
                  <div>
                    <p className="text-sm text-gray-500">A Receber Vencido</p>
                    <p className="text-2xl font-bold text-orange-600 mt-1">{formatCurrency(vencidas?.receber?.valor || 0)}</p>
                    <p className="text-xs text-gray-400 mt-1">{vencidas?.receber?.quantidade || 0} conta(s)</p>
                  </div>
                  <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center">
                    <TrendingUp className="text-orange-600" size={24} />
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Listas de Contas Vencidas */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Contas a Pagar Vencidas */}
            <Card>
              <CardHeader className="border-b bg-red-50">
                <CardTitle className="flex items-center gap-2 text-red-700">
                  <XCircle size={20} />
                  <span>Contas a Pagar Vencidas</span>
                  {vencidas?.pagar?.quantidade > 0 && (
                    <span className="bg-red-600 text-white text-xs px-2 py-0.5 rounded-full ml-auto">
                      {vencidas.pagar.quantidade}
                    </span>
                  )}
                </CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                {(!vencidas?.pagar?.lista || vencidas.pagar.lista.length === 0) ? (
                  <div className="text-center py-12 text-gray-400">
                    <CheckCircle2 className="mx-auto mb-3 text-green-500" size={40} />
                    <p className="font-medium text-green-600">Nenhuma conta a pagar vencida!</p>
                    <p className="text-sm mt-1">Suas contas estão em dia.</p>
                  </div>
                ) : (
                  <div className="max-h-[400px] overflow-y-auto">
                    {vencidas.pagar.lista.map((conta, index) => {
                      const diasVencido = Math.floor((new Date() - new Date(conta.data_vencimento)) / (1000 * 60 * 60 * 24));
                      return (
                        <div 
                          key={conta.id || index} 
                          className="p-4 border-b last:border-b-0 hover:bg-red-50 transition-colors"
                          data-testid={`conta-pagar-vencida-${index}`}
                        >
                          <div className="flex justify-between items-start">
                            <div className="flex-1">
                              <p className="font-medium text-gray-900">{conta.descricao || 'Sem descrição'}</p>
                              <div className="flex flex-wrap gap-2 mt-1 text-xs">
                                {conta.fornecedor_nome && (
                                  <span className="bg-gray-100 px-2 py-0.5 rounded text-gray-600">
                                    {conta.fornecedor_nome}
                                  </span>
                                )}
                                {conta.centro_custo_nome && (
                                  <span className="bg-blue-50 px-2 py-0.5 rounded text-blue-600">
                                    {conta.centro_custo_nome}
                                  </span>
                                )}
                              </div>
                              <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
                                <span className="flex items-center gap-1">
                                  <Calendar size={12} />
                                  Venceu: {new Date(conta.data_vencimento).toLocaleDateString('pt-BR')}
                                </span>
                                <span className="bg-red-100 text-red-700 px-2 py-0.5 rounded font-medium">
                                  {diasVencido} dia(s) atraso
                                </span>
                              </div>
                            </div>
                            <div className="text-right">
                              <p className="text-lg font-bold text-red-600">
                                {formatCurrency(conta.valor_final || conta.valor)}
                              </p>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Contas a Receber Vencidas */}
            <Card>
              <CardHeader className="border-b bg-orange-50">
                <CardTitle className="flex items-center gap-2 text-orange-700">
                  <Clock size={20} />
                  <span>Contas a Receber Vencidas</span>
                  {vencidas?.receber?.quantidade > 0 && (
                    <span className="bg-orange-600 text-white text-xs px-2 py-0.5 rounded-full ml-auto">
                      {vencidas.receber.quantidade}
                    </span>
                  )}
                </CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                {(!vencidas?.receber?.lista || vencidas.receber.lista.length === 0) ? (
                  <div className="text-center py-12 text-gray-400">
                    <CheckCircle2 className="mx-auto mb-3 text-green-500" size={40} />
                    <p className="font-medium text-green-600">Nenhuma conta a receber vencida!</p>
                    <p className="text-sm mt-1">Seus recebimentos estão em dia.</p>
                  </div>
                ) : (
                  <div className="max-h-[400px] overflow-y-auto">
                    {vencidas.receber.lista.map((conta, index) => {
                      const diasVencido = Math.floor((new Date() - new Date(conta.data_vencimento)) / (1000 * 60 * 60 * 24));
                      return (
                        <div 
                          key={conta.id || index} 
                          className="p-4 border-b last:border-b-0 hover:bg-orange-50 transition-colors"
                          data-testid={`conta-receber-vencida-${index}`}
                        >
                          <div className="flex justify-between items-start">
                            <div className="flex-1">
                              <p className="font-medium text-gray-900">{conta.descricao || 'Sem descrição'}</p>
                              <div className="flex flex-wrap gap-2 mt-1 text-xs">
                                {conta.cliente_nome && (
                                  <span className="bg-gray-100 px-2 py-0.5 rounded text-gray-600">
                                    {conta.cliente_nome}
                                  </span>
                                )}
                                {conta.centro_custo_nome && (
                                  <span className="bg-blue-50 px-2 py-0.5 rounded text-blue-600">
                                    {conta.centro_custo_nome}
                                  </span>
                                )}
                              </div>
                              <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
                                <span className="flex items-center gap-1">
                                  <Calendar size={12} />
                                  Venceu: {new Date(conta.data_vencimento).toLocaleDateString('pt-BR')}
                                </span>
                                <span className="bg-orange-100 text-orange-700 px-2 py-0.5 rounded font-medium">
                                  {diasVencido} dia(s) atraso
                                </span>
                              </div>
                            </div>
                            <div className="text-right">
                              <p className="text-lg font-bold text-orange-600">
                                {formatCurrency(conta.valor_final || conta.valor)}
                              </p>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Tab: A Pagar */}
        <TabsContent value="pagar" className="mt-6">
          {/* Filters */}
          <FilterBar />
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <Card className="border-l-4 border-l-red-400">
              <CardContent className="p-6">
                <div className="flex justify-between items-start">
                  <div>
                    <p className="text-sm text-gray-500">Este Mês</p>
                    <p className="text-2xl font-bold text-red-600">{formatCurrency(aPagar.mes)}</p>
                  </div>
                  <span className="bg-red-100 text-red-700 text-xs font-medium px-2 py-1 rounded">MÊS</span>
                </div>
              </CardContent>
            </Card>
            <Card className="border-l-4 border-l-red-500">
              <CardContent className="p-6">
                <div className="flex justify-between items-start">
                  <div>
                    <p className="text-sm text-gray-500">Este Ano</p>
                    <p className="text-2xl font-bold text-red-600">{formatCurrency(aPagar.ano)}</p>
                  </div>
                  <span className="bg-red-100 text-red-700 text-xs font-medium px-2 py-1 rounded">ANO</span>
                </div>
              </CardContent>
            </Card>
            <Card className="border-l-4 border-l-red-600">
              <CardContent className="p-6">
                <div className="flex justify-between items-start">
                  <div>
                    <p className="text-sm text-gray-500">Total Geral</p>
                    <p className="text-2xl font-bold text-red-600">{formatCurrency(aPagar.total)}</p>
                  </div>
                  <span className="bg-red-100 text-red-700 text-xs font-medium px-2 py-1 rounded">GERAL</span>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Lista de Contas */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-lg">Contas a Pagar</CardTitle>
            </CardHeader>
            <CardContent>
              {contasPagar.filter(c => {
                if (searchTerm && !c.descricao?.toLowerCase().includes(searchTerm.toLowerCase())) return false;
                if (filterCentroCusto && filterCentroCusto !== "all" && c.centro_custo_id !== filterCentroCusto) return false;
                if (filterPlanoContas && filterPlanoContas !== "all" && c.plano_contas_id !== filterPlanoContas) return false;
                if (filterStatus === "vencido" && c.data_vencimento >= new Date().toISOString().split("T")[0]) return false;
                if (filterStatus === "pendente" && (c.status === "pago" || c.data_vencimento < new Date().toISOString().split("T")[0])) return false;
                if (filterStatus === "pago" && c.status !== "pago") return false;
                return c.status !== "pago";
              }).length === 0 ? (
                <p className="text-gray-500 text-center py-8">Nenhuma conta encontrada</p>
              ) : (
                <div className="space-y-2 max-h-[400px] overflow-y-auto">
                  {contasPagar.filter(c => {
                    if (searchTerm && !c.descricao?.toLowerCase().includes(searchTerm.toLowerCase())) return false;
                    if (filterCentroCusto && filterCentroCusto !== "all" && c.centro_custo_id !== filterCentroCusto) return false;
                    if (filterPlanoContas && filterPlanoContas !== "all" && c.plano_contas_id !== filterPlanoContas) return false;
                    if (filterStatus === "vencido" && c.data_vencimento >= new Date().toISOString().split("T")[0]) return false;
                    if (filterStatus === "pendente" && (c.status === "pago" || c.data_vencimento < new Date().toISOString().split("T")[0])) return false;
                    if (filterStatus === "pago" && c.status !== "pago") return false;
                    return c.status !== "pago";
                  }).map(conta => {
                    const isVencida = conta.data_vencimento < new Date().toISOString().split("T")[0];
                    return (
                      <div key={conta.id} className={`p-3 rounded-lg flex justify-between items-center ${isVencida ? 'bg-red-50 border border-red-200' : 'bg-gray-50'}`}>
                        <div className="flex items-center gap-3">
                          <div className={`w-2 h-2 rounded-full ${isVencida ? 'bg-red-500' : 'bg-yellow-500'}`} />
                          <div>
                            <p className="font-medium text-black text-sm">{conta.descricao}</p>
                            <p className="text-xs text-gray-500">
                              {conta.fornecedor_nome && <span className="mr-2">{conta.fornecedor_nome}</span>}
                              Venc: {new Date(conta.data_vencimento).toLocaleDateString('pt-BR')}
                              {conta.centro_custo_nome && <span className="ml-2 text-blue-600">• {conta.centro_custo_nome}</span>}
                            </p>
                          </div>
                        </div>
                        <span className="font-bold text-red-600">{formatCurrency(conta.valor)}</span>
                      </div>
                    );
                  })}
                </div>
              )}
            </CardContent>
          </Card>

          <div className="grid grid-cols-2 gap-4 mt-6">
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <AlertCircle className="text-[#E31A1A]" size={24} />
                  <div>
                    <p className="text-sm text-gray-500">Contas Vencidas</p>
                    <p className="text-xl font-bold text-[#E31A1A]">{aPagar.vencidas}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <ClipboardList className="text-[#D4A000]" size={24} />
                  <div>
                    <p className="text-sm text-gray-500">Valor em OS (a pagar)</p>
                    <p className="text-xl font-bold text-[#D4A000]">{formatCurrency(aPagar.osValor)}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Tab: A Receber */}
        <TabsContent value="receber" className="mt-6">
          {/* Filters */}
          <FilterBar />
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <Card className="border-l-4 border-l-green-400">
              <CardContent className="p-6">
                <div className="flex justify-between items-start">
                  <div>
                    <p className="text-sm text-gray-500">Este Mês</p>
                    <p className="text-2xl font-bold text-green-600">{formatCurrency(aReceber.mes)}</p>
                  </div>
                  <span className="bg-green-100 text-green-700 text-xs font-medium px-2 py-1 rounded">MÊS</span>
                </div>
              </CardContent>
            </Card>
            <Card className="border-l-4 border-l-green-500">
              <CardContent className="p-6">
                <div className="flex justify-between items-start">
                  <div>
                    <p className="text-sm text-gray-500">Este Ano</p>
                    <p className="text-2xl font-bold text-green-600">{formatCurrency(aReceber.ano)}</p>
                  </div>
                  <span className="bg-green-100 text-green-700 text-xs font-medium px-2 py-1 rounded">ANO</span>
                </div>
              </CardContent>
            </Card>
            <Card className="border-l-4 border-l-green-600">
              <CardContent className="p-6">
                <div className="flex justify-between items-start">
                  <div>
                    <p className="text-sm text-gray-500">Total Geral</p>
                    <p className="text-2xl font-bold text-green-600">{formatCurrency(aReceber.total)}</p>
                  </div>
                  <span className="bg-green-100 text-green-700 text-xs font-medium px-2 py-1 rounded">GERAL</span>
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <AlertCircle className="text-[#E31A1A]" size={24} />
                  <div>
                    <p className="text-sm text-gray-500">Contas Vencidas</p>
                    <p className="text-xl font-bold text-[#E31A1A]">{aReceber.vencidas}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <ClipboardList className="text-[#D4A000]" size={24} />
                  <div>
                    <p className="text-sm text-gray-500">Valor em OS (a receber)</p>
                    <p className="text-xl font-bold text-[#D4A000]">{formatCurrency(aReceber.osValor)}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Tab: Quitados */}
        <TabsContent value="quitados" className="mt-6">
          {/* Filters */}
          <FilterBar />
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Pagos */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-red-600">
                  <TrendingDown size={20} />
                  Pagos (Despesas)
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between items-center p-3 bg-red-50 rounded-lg">
                    <span className="text-gray-600">Este Mês</span>
                    <span className="font-bold text-red-600">{formatCurrency(quitados.pagar?.mes)}</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-red-50 rounded-lg">
                    <span className="text-gray-600">Este Ano</span>
                    <span className="font-bold text-red-600">{formatCurrency(quitados.pagar?.ano)}</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-red-100 rounded-lg">
                    <span className="font-medium text-gray-700">Total Geral</span>
                    <span className="font-bold text-red-700">{formatCurrency(quitados.pagar?.total)}</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Recebidos */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-green-600">
                  <TrendingUp size={20} />
                  Recebidos (Receitas)
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between items-center p-3 bg-green-50 rounded-lg">
                    <span className="text-gray-600">Este Mês</span>
                    <span className="font-bold text-green-600">{formatCurrency(quitados.receber?.mes)}</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-green-50 rounded-lg">
                    <span className="text-gray-600">Este Ano</span>
                    <span className="font-bold text-green-600">{formatCurrency(quitados.receber?.ano)}</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-green-100 rounded-lg">
                    <span className="font-medium text-gray-700">Total Geral</span>
                    <span className="font-bold text-green-700">{formatCurrency(quitados.receber?.total)}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Saldo Líquido */}
          <Card className="mt-6">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <BadgeDollarSign className="text-[#D4A000]" size={32} />
                  <div>
                    <p className="text-sm text-gray-500">Saldo Líquido (Recebido - Pago)</p>
                    <p className={`text-3xl font-bold ${(quitados.receber?.total - quitados.pagar?.total) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {formatCurrency((quitados.receber?.total || 0) - (quitados.pagar?.total || 0))}
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
