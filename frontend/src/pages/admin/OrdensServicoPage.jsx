import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "@/App";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { 
  Plus, 
  Search, 
  ClipboardList,
  Calendar,
  User,
  CheckCircle2,
  Clock,
  AlertCircle,
  Edit,
  Trash2,
  TrendingDown,
  TrendingUp,
  Minus
} from "lucide-react";
import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

export default function OrdensServicoPage() {
  const [ordens, setOrdens] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("todas");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingOrdem, setEditingOrdem] = useState(null);
  const [formData, setFormData] = useState({
    numero_contrato: "",
    cliente_nome: "",
    cliente_fantasia: "",
    obra: "",
    descricao: "",
    data_abertura: new Date().toISOString().split("T")[0],
    data_previsao_entrega: "",
    valor_total: "",
    valor_antecipado: "",
    tipo_financeiro: "nenhum",
    observacoes: ""
  });

  useEffect(() => {
    fetchOrdens();
  }, []);

  const fetchOrdens = async () => {
    try {
      const response = await axios.get(`${API}/admin/ordens-servico`);
      setOrdens(response.data);
    } catch (error) {
      console.error("Erro ao carregar ordens:", error);
      toast.error("Erro ao carregar ordens de serviço");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const dataToSend = {
        ...formData,
        valor_total: parseFloat(formData.valor_total) || 0,
        valor_antecipado: parseFloat(formData.valor_antecipado) || 0
      };
      
      if (editingOrdem) {
        await axios.put(`${API}/admin/ordens-servico/${editingOrdem.id}`, dataToSend);
        toast.success("Ordem de serviço atualizada!");
      } else {
        await axios.post(`${API}/admin/ordens-servico`, dataToSend);
        toast.success("Ordem de serviço criada!");
      }
      fetchOrdens();
      closeModal();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao salvar ordem");
    }
  };

  const handleUpdateStatus = async (id, status) => {
    try {
      await axios.patch(`${API}/admin/ordens-servico/${id}/status`, { status });
      toast.success("Status atualizado!");
      fetchOrdens();
    } catch (error) {
      toast.error("Erro ao atualizar status");
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Deseja realmente excluir esta ordem de serviço?")) return;
    try {
      await axios.delete(`${API}/admin/ordens-servico/${id}`);
      toast.success("Ordem excluída!");
      fetchOrdens();
    } catch (error) {
      toast.error("Erro ao excluir ordem");
    }
  };

  const openModal = (ordem = null) => {
    if (ordem) {
      setEditingOrdem(ordem);
      setFormData({
        numero_contrato: ordem.numero_contrato || "",
        cliente_nome: ordem.cliente_nome || "",
        cliente_fantasia: ordem.cliente_fantasia || "",
        obra: ordem.obra || "",
        descricao: ordem.descricao || "",
        data_abertura: ordem.data_abertura?.split("T")[0] || "",
        data_previsao_entrega: ordem.data_previsao_entrega?.split("T")[0] || "",
        valor_total: ordem.valor_total?.toString() || "",
        valor_antecipado: ordem.valor_antecipado?.toString() || "",
        tipo_financeiro: ordem.tipo_financeiro || "nenhum",
        observacoes: ordem.observacoes || ""
      });
    } else {
      setEditingOrdem(null);
      setFormData({
        numero_contrato: "",
        cliente_nome: "",
        cliente_fantasia: "",
        obra: "",
        descricao: "",
        data_abertura: new Date().toISOString().split("T")[0],
        data_previsao_entrega: "",
        valor_total: "",
        valor_antecipado: "",
        tipo_financeiro: "nenhum",
        observacoes: ""
      });
    }
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setEditingOrdem(null);
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(value || 0);
  };

  const getStatusInfo = (status) => {
    switch (status) {
      case "em_aberto":
        return { label: "Aberta", color: "bg-blue-100 text-[#FFC232]", icon: Clock };
      case "em_andamento":
        return { label: "Em Andamento", color: "bg-orange-100 text-[#E31A1A]", icon: AlertCircle };
      case "concluida":
        return { label: "Concluída", color: "bg-green-100 text-green-700", icon: CheckCircle2 };
      case "cancelada":
        return { label: "Cancelada", color: "bg-red-100 text-red-700", icon: AlertCircle };
      default:
        return { label: "Aberta", color: "bg-blue-100 text-[#FFC232]", icon: Clock };
    }
  };

  const getTipoFinanceiroInfo = (tipo) => {
    switch (tipo) {
      case "a_pagar":
        return { label: "A Pagar", color: "bg-red-50 text-red-600", icon: TrendingDown };
      case "a_receber":
        return { label: "A Receber", color: "bg-green-50 text-green-600", icon: TrendingUp };
      default:
        return { label: "-", color: "bg-slate-50 text-slate-400", icon: Minus };
    }
  };

  const filteredOrdens = ordens.filter(ordem => {
    const matchSearch = ordem.numero?.toString().includes(search) ||
                       ordem.cliente_nome?.toLowerCase().includes(search.toLowerCase()) ||
                       ordem.cliente_fantasia?.toLowerCase().includes(search.toLowerCase()) ||
                       ordem.descricao?.toLowerCase().includes(search.toLowerCase()) ||
                       ordem.obra?.toLowerCase().includes(search.toLowerCase());
    
    if (filter === "todas") return matchSearch;
    return matchSearch && ordem.status === filter;
  });

  // Totais
  const totalOS = filteredOrdens.length;
  const totalAPagar = filteredOrdens.filter(o => o.tipo_financeiro === "a_pagar").reduce((s, o) => s + (o.valor_total || 0), 0);
  const totalAReceber = filteredOrdens.filter(o => o.tipo_financeiro === "a_receber").reduce((s, o) => s + (o.valor_total || 0), 0);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="spinner w-12 h-12"></div>
      </div>
    );
  }

  return (
    <div data-testid="ordens-servico-page">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Ordens de Serviço</h1>
          <p className="text-slate-500 mt-1">Gerenciamento de OS</p>
        </div>
        <Button onClick={() => openModal()} className="bg-[#FFC232] hover:bg-[#FFC232]" data-testid="new-os-btn">
          <Plus size={18} className="mr-2" />
          Nova OS
        </Button>
      </div>

      {/* Resumo */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <Card className="stat-card">
          <CardContent className="p-4 flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
              <ClipboardList className="text-[#FFC232]" size={20} />
            </div>
            <div>
              <p className="text-xs text-slate-500">Total OS</p>
              <p className="text-lg font-bold text-[#FFC232]">{totalOS}</p>
            </div>
          </CardContent>
        </Card>
        <Card className="stat-card">
          <CardContent className="p-4 flex items-center gap-3">
            <div className="w-10 h-10 bg-red-100 rounded-lg flex items-center justify-center">
              <TrendingDown className="text-red-600" size={20} />
            </div>
            <div>
              <p className="text-xs text-slate-500">Total A Pagar</p>
              <p className="text-lg font-bold text-red-600">{formatCurrency(totalAPagar)}</p>
            </div>
          </CardContent>
        </Card>
        <Card className="stat-card">
          <CardContent className="p-4 flex items-center gap-3">
            <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
              <TrendingUp className="text-green-600" size={20} />
            </div>
            <div>
              <p className="text-xs text-slate-500">Total A Receber</p>
              <p className="text-lg font-bold text-green-600">{formatCurrency(totalAReceber)}</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <div className="flex flex-col md:flex-row gap-4 mb-6">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400" size={20} />
          <Input
            placeholder="Buscar por número, cliente, obra ou descrição..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-10"
            data-testid="search-os"
          />
        </div>
        <div className="flex gap-2 overflow-x-auto pb-2 md:pb-0">
          {[
            { value: "todas", label: "Todas" },
            { value: "em_aberto", label: "Abertas" },
            { value: "em_andamento", label: "Em Andamento" },
            { value: "concluida", label: "Concluídas" }
          ].map((f) => (
            <Button
              key={f.value}
              variant={filter === f.value ? "default" : "outline"}
              onClick={() => setFilter(f.value)}
              className={filter === f.value ? "bg-[#FFC232]" : ""}
              size="sm"
            >
              {f.label}
            </Button>
          ))}
        </div>
      </div>

      {/* Lista */}
      {filteredOrdens.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-slate-400">
            <ClipboardList className="mx-auto mb-4" size={48} />
            <p className="font-medium">Nenhuma ordem encontrada</p>
            <p className="text-sm">Crie uma nova ordem de serviço</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {filteredOrdens.map((ordem) => {
            const statusInfo = getStatusInfo(ordem.status);
            const StatusIcon = statusInfo.icon;
            const tipoInfo = getTipoFinanceiroInfo(ordem.tipo_financeiro);
            const TipoIcon = tipoInfo.icon;
            return (
              <Card key={ordem.id} className="hover:shadow-md transition-shadow" data-testid={`os-${ordem.id}`}>
                <CardContent className="p-4">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1 flex-wrap">
                        <span className="font-bold text-[#FFC232]">OS-{ordem.numero}</span>
                        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${statusInfo.color}`}>
                          <StatusIcon className="inline mr-1" size={12} />
                          {statusInfo.label}
                        </span>
                        {ordem.tipo_financeiro && ordem.tipo_financeiro !== "nenhum" && (
                          <span className={`px-2 py-0.5 rounded text-xs font-medium ${tipoInfo.color}`}>
                            <TipoIcon className="inline mr-1" size={12} />
                            {tipoInfo.label}
                          </span>
                        )}
                      </div>
                      <h3 className="font-medium text-slate-900 truncate">{ordem.descricao || "Sem descrição"}</h3>
                      {(ordem.cliente_nome || ordem.cliente_fantasia) && (
                        <p className="text-sm text-slate-500 flex items-center gap-1">
                          <User size={14} />
                          {ordem.cliente_fantasia || ordem.cliente_nome}
                        </p>
                      )}
                      {ordem.obra && (
                        <p className="text-sm text-slate-500">Obra: {ordem.obra}</p>
                      )}
                      <p className="text-sm text-slate-500 flex items-center gap-1">
                        <Calendar size={14} />
                        Abertura: {new Date(ordem.data_abertura).toLocaleDateString('pt-BR')}
                        {ordem.data_previsao_entrega && ` | Previsão: ${new Date(ordem.data_previsao_entrega).toLocaleDateString('pt-BR')}`}
                      </p>
                    </div>
                    <div className="text-right">
                      {ordem.valor_total > 0 && (
                        <p className="text-lg font-bold text-slate-900">{formatCurrency(ordem.valor_total)}</p>
                      )}
                      {ordem.valor_restante > 0 && ordem.valor_antecipado > 0 && (
                        <p className="text-xs text-slate-500">Restante: {formatCurrency(ordem.valor_restante)}</p>
                      )}
                      <div className="flex gap-1 mt-2">
                        {ordem.status === "em_aberto" && (
                          <Button
                            size="sm"
                            variant="outline"
                            className="text-[#E31A1A]"
                            onClick={() => handleUpdateStatus(ordem.id, "em_andamento")}
                            title="Iniciar"
                          >
                            <Clock size={16} />
                          </Button>
                        )}
                        {ordem.status === "em_andamento" && (
                          <Button
                            size="sm"
                            variant="outline"
                            className="text-green-600"
                            onClick={() => handleUpdateStatus(ordem.id, "concluida")}
                            title="Concluir"
                          >
                            <CheckCircle2 size={16} />
                          </Button>
                        )}
                        <Button size="sm" variant="outline" onClick={() => openModal(ordem)}>
                          <Edit size={16} />
                        </Button>
                        <Button 
                          size="sm" 
                          variant="outline" 
                          className="text-red-600 hover:bg-red-50"
                          onClick={() => handleDelete(ordem.id)}
                        >
                          <Trash2 size={16} />
                        </Button>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Modal */}
      <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{editingOrdem ? "Editar Ordem de Serviço" : "Nova Ordem de Serviço"}</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="form-label">Nº Contrato</label>
                <Input
                  value={formData.numero_contrato}
                  onChange={(e) => setFormData({...formData, numero_contrato: e.target.value})}
                  placeholder="Ex: CONT-2024-001"
                />
              </div>
              <div>
                <label className="form-label">Tipo Financeiro *</label>
                <Select value={formData.tipo_financeiro} onValueChange={(value) => setFormData({...formData, tipo_financeiro: value})}>
                  <SelectTrigger className="w-full h-11">
                    <SelectValue placeholder="Selecione o tipo" />
                  </SelectTrigger>
                  <SelectContent className="z-[9999]">
                    <SelectItem value="nenhum">Nenhum</SelectItem>
                    <SelectItem value="a_pagar">A Pagar (Despesa)</SelectItem>
                    <SelectItem value="a_receber">A Receber (Receita)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="form-label">Cliente (Razão Social)</label>
                <Input
                  value={formData.cliente_nome}
                  onChange={(e) => setFormData({...formData, cliente_nome: e.target.value})}
                  placeholder="Nome do cliente"
                />
              </div>
              <div>
                <label className="form-label">Cliente (Nome Fantasia)</label>
                <Input
                  value={formData.cliente_fantasia}
                  onChange={(e) => setFormData({...formData, cliente_fantasia: e.target.value})}
                  placeholder="Nome fantasia"
                />
              </div>
            </div>
            <div>
              <label className="form-label">Obra/Projeto</label>
              <Input
                value={formData.obra}
                onChange={(e) => setFormData({...formData, obra: e.target.value})}
                placeholder="Nome da obra ou projeto"
              />
            </div>
            <div>
              <label className="form-label">Descrição do Serviço *</label>
              <Input
                value={formData.descricao}
                onChange={(e) => setFormData({...formData, descricao: e.target.value})}
                placeholder="Descreva o serviço a ser realizado"
                required
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="form-label">Data de Abertura</label>
                <Input
                  type="date"
                  value={formData.data_abertura}
                  onChange={(e) => setFormData({...formData, data_abertura: e.target.value})}
                />
              </div>
              <div>
                <label className="form-label">Previsão de Entrega</label>
                <Input
                  type="date"
                  value={formData.data_previsao_entrega}
                  onChange={(e) => setFormData({...formData, data_previsao_entrega: e.target.value})}
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="form-label">Valor Total</label>
                <Input
                  type="number"
                  step="0.01"
                  value={formData.valor_total}
                  onChange={(e) => setFormData({...formData, valor_total: e.target.value})}
                  placeholder="0,00"
                />
              </div>
              <div>
                <label className="form-label">Valor Antecipado</label>
                <Input
                  type="number"
                  step="0.01"
                  value={formData.valor_antecipado}
                  onChange={(e) => setFormData({...formData, valor_antecipado: e.target.value})}
                  placeholder="0,00"
                />
              </div>
            </div>
            <div>
              <label className="form-label">Observações</label>
              <Input
                value={formData.observacoes}
                onChange={(e) => setFormData({...formData, observacoes: e.target.value})}
                placeholder="Observações adicionais"
              />
            </div>
            <div className="flex gap-3 pt-2">
              <Button type="button" variant="outline" onClick={closeModal} className="flex-1">
                Cancelar
              </Button>
              <Button type="submit" className="flex-1 bg-[#FFC232] hover:bg-[#FFC232]">
                {editingOrdem ? "Atualizar" : "Criar OS"}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
