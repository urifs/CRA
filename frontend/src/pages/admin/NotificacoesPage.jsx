import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "@/App";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { 
  Bell, AlertTriangle, Clock, CheckCircle2, DollarSign, 
  TrendingDown, TrendingUp, ClipboardList, Truck, Calendar,
  Filter, ChevronRight, Search, X
} from "lucide-react";
import { useNavigate } from "react-router-dom";

const tipoIcons = {
  conta_pagar: { icon: TrendingDown, color: "text-red-600", bg: "bg-red-100", label: "Conta a Pagar" },
  conta_receber: { icon: TrendingUp, color: "text-green-600", bg: "bg-green-100", label: "Conta a Receber" },
  ordem_servico: { icon: ClipboardList, color: "text-[#D4A000]", bg: "bg-blue-100", label: "Ordem de Serviço" },
  aluguel: { icon: Truck, color: "text-purple-600", bg: "bg-purple-100", label: "Aluguel" }
};

const urgenciaInfo = {
  alta: { color: "bg-red-500", textColor: "text-red-700", label: "Urgente" },
  media: { color: "bg-[#E31A1A]", textColor: "text-[#E31A1A]", label: "Atenção" },
  baixa: { color: "bg-[#D4A000]", textColor: "text-[#D4A000]", label: "Em breve" }
};

export default function NotificacoesPage() {
  const [data, setData] = useState({ resumo: {}, notificacoes: [], prazo_dias: 7 });
  const [loading, setLoading] = useState(true);
  const [prazoDias, setPrazoDias] = useState(7);
  const [filterTipo, setFilterTipo] = useState("todos");
  const [filterUrgencia, setFilterUrgencia] = useState("todas");
  const [searchTerm, setSearchTerm] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    fetchNotificacoes();
  }, [prazoDias]);

  const fetchNotificacoes = async () => {
    try {
      const response = await axios.get(`${API}/admin/notificacoes?prazo_dias=${prazoDias}`);
      setData(response.data);
    } catch (error) {
      console.error("Erro ao carregar notificações:", error);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value) => {
    if (!value) return "";
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value);
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return "";
    return new Date(dateStr).toLocaleDateString('pt-BR');
  };

  const getDaysUntil = (dateStr) => {
    if (!dateStr) return null;
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const target = new Date(dateStr);
    const diff = Math.ceil((target - today) / (1000 * 60 * 60 * 24));
    return diff;
  };

  const getDaysLabel = (days) => {
    if (days === null) return "";
    if (days < 0) return `${Math.abs(days)} dia${Math.abs(days) !== 1 ? 's' : ''} atrás`;
    if (days === 0) return "Hoje";
    if (days === 1) return "Amanhã";
    return `Em ${days} dias`;
  };

  const filteredNotificacoes = data.notificacoes.filter(n => {
    if (filterTipo !== "todos" && n.tipo !== filterTipo) return false;
    if (filterUrgencia !== "todas" && n.urgencia !== filterUrgencia) return false;
    if (searchTerm && !n.descricao.toLowerCase().includes(searchTerm.toLowerCase()) &&
        !(n.nome_relacionado || "").toLowerCase().includes(searchTerm.toLowerCase())) return false;
    return true;
  });

  const { resumo } = data;

  if (loading) {
    return <div className="flex items-center justify-center min-h-[400px]"><div className="spinner w-12 h-12"></div></div>;
  }

  return (
    <div data-testid="notificacoes-page">
      <div className="page-header">
        <div>
          <h1 className="page-title flex items-center gap-2">
            <Bell className="text-[#E31A1A]" />
            Central de Notificações
          </h1>
          <p className="text-gray-500 mt-1">Acompanhe vencimentos e prazos importantes</p>
        </div>
      </div>

      {/* Search Bar */}
      <div className="relative max-w-md mb-6">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
        <Input
          type="text"
          placeholder="Pesquisar notificações..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="pl-10 pr-10 h-10 bg-white border-gray-200"
          data-testid="search-notificacoes"
        />
        {searchTerm && (
          <button
            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
            onClick={() => setSearchTerm("")}
          >
            <X size={16} />
          </button>
        )}
      </div>

      {/* Configuração de prazo */}
      <Card className="mb-6">
        <CardContent className="p-4">
          <div className="flex items-center gap-4 flex-wrap">
            <div className="flex items-center gap-2">
              <Calendar className="text-gray-400" size={20} />
              <span className="text-sm text-gray-600">Mostrar próximos</span>
              <Input 
                type="number" 
                value={prazoDias} 
                onChange={(e) => setPrazoDias(parseInt(e.target.value) || 7)} 
                className="w-20" 
                min="1" 
                max="90"
              />
              <span className="text-sm text-gray-600">dias</span>
            </div>
            <Button variant="outline" size="sm" onClick={fetchNotificacoes}>
              <Filter size={16} className="mr-1" />Atualizar
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Resumo */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
        <Card className="stat-card border-l-4 border-l-red-500">
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <AlertTriangle className="text-red-500" size={20} />
              <div>
                <p className="text-xs text-gray-500">Vencidas</p>
                <p className="text-xl font-bold text-red-600">{resumo.vencidas || 0}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="stat-card">
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <TrendingDown className="text-red-500" size={20} />
              <div>
                <p className="text-xs text-gray-500">A Pagar</p>
                <p className="text-xl font-bold">{resumo.por_tipo?.conta_pagar || 0}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="stat-card">
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <TrendingUp className="text-green-500" size={20} />
              <div>
                <p className="text-xs text-gray-500">A Receber</p>
                <p className="text-xl font-bold">{resumo.por_tipo?.conta_receber || 0}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="stat-card">
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <ClipboardList className="text-[#D4A000]" size={20} />
              <div>
                <p className="text-xs text-gray-500">OS</p>
                <p className="text-xl font-bold">{resumo.por_tipo?.ordem_servico || 0}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="stat-card">
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <Truck className="text-purple-500" size={20} />
              <div>
                <p className="text-xs text-gray-500">Aluguéis</p>
                <p className="text-xl font-bold">{resumo.por_tipo?.aluguel || 0}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filtros */}
      <div className="flex flex-wrap gap-4 mb-6">
        <div className="flex gap-2">
          <span className="text-sm text-gray-500 self-center">Tipo:</span>
          {[
            { value: "todos", label: "Todos" },
            { value: "conta_pagar", label: "A Pagar" },
            { value: "conta_receber", label: "A Receber" },
            { value: "ordem_servico", label: "OS" },
            { value: "aluguel", label: "Aluguéis" }
          ].map(f => (
            <Button 
              key={f.value} 
              variant={filterTipo === f.value ? "default" : "outline"} 
              size="sm"
              onClick={() => setFilterTipo(f.value)}
              className={filterTipo === f.value ? "bg-[#D4A000]" : ""}
            >
              {f.label}
            </Button>
          ))}
        </div>
        <div className="flex gap-2">
          <span className="text-sm text-gray-500 self-center">Urgência:</span>
          {[
            { value: "todas", label: "Todas" },
            { value: "alta", label: "Urgente" },
            { value: "media", label: "Atenção" },
            { value: "baixa", label: "Em breve" }
          ].map(f => (
            <Button 
              key={f.value} 
              variant={filterUrgencia === f.value ? "default" : "outline"} 
              size="sm"
              onClick={() => setFilterUrgencia(f.value)}
              className={filterUrgencia === f.value ? "bg-[#D4A000]" : ""}
            >
              {f.label}
            </Button>
          ))}
        </div>
      </div>

      {/* Lista de notificações */}
      {filteredNotificacoes.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-gray-400">
            <CheckCircle2 className="mx-auto mb-4 text-green-400" size={48} />
            <p className="font-medium">Nenhuma notificação pendente!</p>
            <p className="text-sm">Não há vencimentos nos próximos {prazoDias} dias</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {filteredNotificacoes.map((notif, index) => {
            const tipoInfo = tipoIcons[notif.tipo] || tipoIcons.conta_pagar;
            const TipoIcon = tipoInfo.icon;
            const urgInfo = urgenciaInfo[notif.urgencia] || urgenciaInfo.baixa;
            const daysUntil = getDaysUntil(notif.data);

            return (
              <Card 
                key={`${notif.tipo}-${notif.id}-${index}`} 
                className={`hover:shadow-md transition-shadow cursor-pointer ${notif.vencida ? 'border-l-4 border-l-red-500' : ''}`}
                onClick={() => navigate(notif.link)}
                data-testid={`notif-${notif.tipo}-${notif.id}`}
              >
                <CardContent className="p-4">
                  <div className="flex items-start gap-4">
                    {/* Ícone */}
                    <div className={`w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 ${tipoInfo.bg}`}>
                      <TipoIcon className={tipoInfo.color} size={20} />
                    </div>

                    {/* Conteúdo */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1 flex-wrap">
                        <span className={`px-2 py-0.5 rounded text-xs font-medium ${urgInfo.textColor} bg-opacity-20`} 
                              style={{ backgroundColor: `${urgInfo.color}20` }}>
                          {urgInfo.label}
                        </span>
                        <span className="text-xs text-gray-500">{tipoInfo.label}</span>
                        {notif.vencida && (
                          <span className="px-2 py-0.5 rounded text-xs bg-red-100 text-red-700 font-medium">
                            VENCIDO
                          </span>
                        )}
                      </div>
                      <h3 className="font-medium text-black truncate">{notif.titulo}</h3>
                      {notif.subtitulo && (
                        <p className="text-sm text-gray-500">{notif.subtitulo}</p>
                      )}
                    </div>

                    {/* Valor e Data */}
                    <div className="text-right flex-shrink-0">
                      {notif.valor > 0 && (
                        <p className="font-bold text-black">{formatCurrency(notif.valor)}</p>
                      )}
                      <p className="text-sm text-gray-500">{formatDate(notif.data)}</p>
                      <p className={`text-xs ${notif.vencida ? 'text-red-600 font-medium' : 'text-gray-400'}`}>
                        {getDaysLabel(daysUntil)}
                      </p>
                    </div>

                    {/* Seta */}
                    <ChevronRight className="text-gray-300 flex-shrink-0" size={20} />
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Total */}
      {filteredNotificacoes.length > 0 && (
        <div className="mt-4 text-center text-sm text-gray-500">
          Mostrando {filteredNotificacoes.length} de {data.notificacoes.length} notificações
        </div>
      )}
    </div>
  );
}
