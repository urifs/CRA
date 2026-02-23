import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "@/App";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
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
  Eye
} from "lucide-react";
import { toast } from "sonner";
import { useNavigate } from "react-router-dom";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

export default function OrdensServicoPage() {
  const navigate = useNavigate();
  const [ordens, setOrdens] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("todas");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingOrdem, setEditingOrdem] = useState(null);
  const [formData, setFormData] = useState({
    numero: "",
    cliente: "",
    descricao: "",
    data_abertura: new Date().toISOString().split("T")[0],
    data_previsao: "",
    valor_total: "",
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
      if (editingOrdem) {
        await axios.put(`${API}/admin/ordens-servico/${editingOrdem.id}`, formData);
        toast.success("Ordem de serviço atualizada!");
      } else {
        await axios.post(`${API}/admin/ordens-servico`, formData);
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
        numero: ordem.numero || "",
        cliente: ordem.cliente || "",
        descricao: ordem.descricao || "",
        data_abertura: ordem.data_abertura?.split("T")[0] || "",
        data_previsao: ordem.data_previsao?.split("T")[0] || "",
        valor_total: ordem.valor_total?.toString() || "",
        observacoes: ordem.observacoes || ""
      });
    } else {
      setEditingOrdem(null);
      const nextNumber = `OS-${Date.now().toString().slice(-6)}`;
      setFormData({
        numero: nextNumber,
        cliente: "",
        descricao: "",
        data_abertura: new Date().toISOString().split("T")[0],
        data_previsao: "",
        valor_total: "",
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
      case "aberta":
        return { label: "Aberta", color: "bg-blue-100 text-blue-700", icon: Clock };
      case "em_andamento":
        return { label: "Em Andamento", color: "bg-orange-100 text-orange-700", icon: AlertCircle };
      case "concluida":
        return { label: "Concluída", color: "bg-green-100 text-green-700", icon: CheckCircle2 };
      case "cancelada":
        return { label: "Cancelada", color: "bg-red-100 text-red-700", icon: AlertCircle };
      default:
        return { label: "Aberta", color: "bg-blue-100 text-blue-700", icon: Clock };
    }
  };

  const filteredOrdens = ordens.filter(ordem => {
    const matchSearch = ordem.numero?.toLowerCase().includes(search.toLowerCase()) ||
                       ordem.cliente?.toLowerCase().includes(search.toLowerCase()) ||
                       ordem.descricao?.toLowerCase().includes(search.toLowerCase());
    
    if (filter === "todas") return matchSearch;
    return matchSearch && ordem.status === filter;
  });

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
        <Button onClick={() => openModal()} className="bg-blue-600 hover:bg-blue-700" data-testid="new-os-btn">
          <Plus size={18} className="mr-2" />
          Nova OS
        </Button>
      </div>

      {/* Filters */}
      <div className="flex flex-col md:flex-row gap-4 mb-6">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400" size={20} />
          <Input
            placeholder="Buscar por número, cliente ou descrição..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-10"
            data-testid="search-os"
          />
        </div>
        <div className="flex gap-2 overflow-x-auto pb-2 md:pb-0">
          {[
            { value: "todas", label: "Todas" },
            { value: "aberta", label: "Abertas" },
            { value: "em_andamento", label: "Em Andamento" },
            { value: "concluida", label: "Concluídas" }
          ].map((f) => (
            <Button
              key={f.value}
              variant={filter === f.value ? "default" : "outline"}
              onClick={() => setFilter(f.value)}
              className={filter === f.value ? "bg-blue-600" : ""}
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
            return (
              <Card key={ordem.id} className="hover:shadow-md transition-shadow" data-testid={`os-${ordem.id}`}>
                <CardContent className="p-4">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-bold text-blue-600">{ordem.numero}</span>
                        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${statusInfo.color}`}>
                          <StatusIcon className="inline mr-1" size={12} />
                          {statusInfo.label}
                        </span>
                      </div>
                      <h3 className="font-medium text-slate-900 truncate">{ordem.descricao || "Sem descrição"}</h3>
                      {ordem.cliente && (
                        <p className="text-sm text-slate-500 flex items-center gap-1">
                          <User size={14} />
                          {ordem.cliente}
                        </p>
                      )}
                      <p className="text-sm text-slate-500 flex items-center gap-1">
                        <Calendar size={14} />
                        Abertura: {new Date(ordem.data_abertura).toLocaleDateString('pt-BR')}
                        {ordem.data_previsao && ` | Previsão: ${new Date(ordem.data_previsao).toLocaleDateString('pt-BR')}`}
                      </p>
                    </div>
                    <div className="text-right">
                      {ordem.valor_total > 0 && (
                        <p className="text-lg font-bold text-slate-900">{formatCurrency(ordem.valor_total)}</p>
                      )}
                      <div className="flex gap-1 mt-2">
                        {ordem.status === "aberta" && (
                          <Button
                            size="sm"
                            variant="outline"
                            className="text-orange-600"
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
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>{editingOrdem ? "Editar Ordem de Serviço" : "Nova Ordem de Serviço"}</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="form-label">Número da OS *</label>
                <Input
                  value={formData.numero}
                  onChange={(e) => setFormData({...formData, numero: e.target.value})}
                  placeholder="OS-000000"
                  required
                  data-testid="input-numero-os"
                />
              </div>
              <div>
                <label className="form-label">Cliente</label>
                <Input
                  value={formData.cliente}
                  onChange={(e) => setFormData({...formData, cliente: e.target.value})}
                  placeholder="Nome do cliente"
                  data-testid="input-cliente-os"
                />
              </div>
              <div className="col-span-2">
                <label className="form-label">Descrição do Serviço *</label>
                <Input
                  value={formData.descricao}
                  onChange={(e) => setFormData({...formData, descricao: e.target.value})}
                  placeholder="Descreva o serviço a ser realizado"
                  required
                  data-testid="input-descricao-os"
                />
              </div>
              <div>
                <label className="form-label">Data de Abertura</label>
                <Input
                  type="date"
                  value={formData.data_abertura}
                  onChange={(e) => setFormData({...formData, data_abertura: e.target.value})}
                  data-testid="input-data-abertura"
                />
              </div>
              <div>
                <label className="form-label">Previsão de Entrega</label>
                <Input
                  type="date"
                  value={formData.data_previsao}
                  onChange={(e) => setFormData({...formData, data_previsao: e.target.value})}
                  data-testid="input-data-previsao"
                />
              </div>
              <div className="col-span-2">
                <label className="form-label">Valor Total</label>
                <Input
                  type="number"
                  step="0.01"
                  value={formData.valor_total}
                  onChange={(e) => setFormData({...formData, valor_total: e.target.value})}
                  placeholder="0,00"
                  data-testid="input-valor-os"
                />
              </div>
              <div className="col-span-2">
                <label className="form-label">Observações</label>
                <Input
                  value={formData.observacoes}
                  onChange={(e) => setFormData({...formData, observacoes: e.target.value})}
                  placeholder="Observações adicionais"
                  data-testid="input-obs-os"
                />
              </div>
            </div>
            <div className="flex gap-3 pt-2">
              <Button type="button" variant="outline" onClick={closeModal} className="flex-1">
                Cancelar
              </Button>
              <Button type="submit" className="flex-1 bg-blue-600 hover:bg-blue-700" data-testid="submit-os">
                {editingOrdem ? "Atualizar" : "Criar OS"}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
