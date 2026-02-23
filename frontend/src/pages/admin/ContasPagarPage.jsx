import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "@/App";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { 
  Plus, 
  Search, 
  Filter,
  CreditCard,
  Calendar,
  CheckCircle2,
  AlertCircle,
  Clock,
  Edit,
  Trash2,
  X
} from "lucide-react";
import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

export default function ContasPagarPage() {
  const [contas, setContas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("todas");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingConta, setEditingConta] = useState(null);
  const [formData, setFormData] = useState({
    descricao: "",
    valor: "",
    vencimento: "",
    fornecedor: "",
    categoria: "",
    observacoes: ""
  });

  useEffect(() => {
    fetchContas();
  }, []);

  const fetchContas = async () => {
    try {
      const response = await axios.get(`${API}/admin/contas-pagar`);
      setContas(response.data);
    } catch (error) {
      console.error("Erro ao carregar contas:", error);
      toast.error("Erro ao carregar contas a pagar");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingConta) {
        await axios.put(`${API}/admin/contas-pagar/${editingConta.id}`, formData);
        toast.success("Conta atualizada com sucesso!");
      } else {
        await axios.post(`${API}/admin/contas-pagar`, formData);
        toast.success("Conta cadastrada com sucesso!");
      }
      fetchContas();
      closeModal();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao salvar conta");
    }
  };

  const handlePagar = async (id) => {
    try {
      await axios.patch(`${API}/admin/contas-pagar/${id}/pagar`);
      toast.success("Conta marcada como paga!");
      fetchContas();
    } catch (error) {
      toast.error("Erro ao marcar conta como paga");
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Deseja realmente excluir esta conta?")) return;
    try {
      await axios.delete(`${API}/admin/contas-pagar/${id}`);
      toast.success("Conta excluída com sucesso!");
      fetchContas();
    } catch (error) {
      toast.error("Erro ao excluir conta");
    }
  };

  const openModal = (conta = null) => {
    if (conta) {
      setEditingConta(conta);
      setFormData({
        descricao: conta.descricao,
        valor: conta.valor.toString(),
        vencimento: conta.vencimento.split("T")[0],
        fornecedor: conta.fornecedor || "",
        categoria: conta.categoria || "",
        observacoes: conta.observacoes || ""
      });
    } else {
      setEditingConta(null);
      setFormData({
        descricao: "",
        valor: "",
        vencimento: "",
        fornecedor: "",
        categoria: "",
        observacoes: ""
      });
    }
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setEditingConta(null);
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(value || 0);
  };

  const getStatus = (conta) => {
    if (conta.pago) return { label: "Pago", color: "bg-green-100 text-green-700", icon: CheckCircle2 };
    const hoje = new Date();
    const vencimento = new Date(conta.vencimento);
    if (vencimento < hoje) return { label: "Vencida", color: "bg-red-100 text-red-700", icon: AlertCircle };
    const diffDays = Math.ceil((vencimento - hoje) / (1000 * 60 * 60 * 24));
    if (diffDays <= 7) return { label: "Próxima", color: "bg-orange-100 text-orange-700", icon: Clock };
    return { label: "Em dia", color: "bg-blue-100 text-blue-700", icon: Calendar };
  };

  const filteredContas = contas.filter(conta => {
    const matchSearch = conta.descricao.toLowerCase().includes(search.toLowerCase()) ||
                       (conta.fornecedor && conta.fornecedor.toLowerCase().includes(search.toLowerCase()));
    
    if (filter === "todas") return matchSearch;
    if (filter === "pendentes") return matchSearch && !conta.pago;
    if (filter === "pagas") return matchSearch && conta.pago;
    if (filter === "vencidas") return matchSearch && !conta.pago && new Date(conta.vencimento) < new Date();
    return matchSearch;
  });

  const totalPendente = filteredContas.filter(c => !c.pago).reduce((sum, c) => sum + c.valor, 0);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="spinner w-12 h-12"></div>
      </div>
    );
  }

  return (
    <div data-testid="contas-pagar-page">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Contas a Pagar</h1>
          <p className="text-slate-500 mt-1">Gerenciamento de despesas</p>
        </div>
        <Button onClick={() => openModal()} className="bg-blue-600 hover:bg-blue-700" data-testid="new-conta-pagar-btn">
          <Plus size={18} className="mr-2" />
          Nova Conta
        </Button>
      </div>

      {/* Summary */}
      <Card className="mb-6 border-l-4 border-l-red-500">
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-500">Total Pendente</p>
              <p className="text-2xl font-bold text-red-600">{formatCurrency(totalPendente)}</p>
            </div>
            <CreditCard className="text-red-500" size={32} />
          </div>
        </CardContent>
      </Card>

      {/* Filters */}
      <div className="flex flex-col md:flex-row gap-4 mb-6">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400" size={20} />
          <Input
            placeholder="Buscar por descrição ou fornecedor..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-10"
            data-testid="search-contas-pagar"
          />
        </div>
        <div className="flex gap-2 overflow-x-auto pb-2 md:pb-0">
          {["todas", "pendentes", "vencidas", "pagas"].map((f) => (
            <Button
              key={f}
              variant={filter === f ? "default" : "outline"}
              onClick={() => setFilter(f)}
              className={filter === f ? "bg-blue-600" : ""}
              size="sm"
            >
              {f.charAt(0).toUpperCase() + f.slice(1)}
            </Button>
          ))}
        </div>
      </div>

      {/* Lista */}
      {filteredContas.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-slate-400">
            <CreditCard className="mx-auto mb-4" size={48} />
            <p className="font-medium">Nenhuma conta encontrada</p>
            <p className="text-sm">Cadastre uma nova conta a pagar</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {filteredContas.map((conta) => {
            const status = getStatus(conta);
            const StatusIcon = status.icon;
            return (
              <Card key={conta.id} className="hover:shadow-md transition-shadow" data-testid={`conta-${conta.id}`}>
                <CardContent className="p-4">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="font-medium text-slate-900 truncate">{conta.descricao}</h3>
                        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${status.color}`}>
                          <StatusIcon className="inline mr-1" size={12} />
                          {status.label}
                        </span>
                      </div>
                      {conta.fornecedor && (
                        <p className="text-sm text-slate-500">Fornecedor: {conta.fornecedor}</p>
                      )}
                      <p className="text-sm text-slate-500">
                        Vencimento: {new Date(conta.vencimento).toLocaleDateString('pt-BR')}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-lg font-bold text-red-600">{formatCurrency(conta.valor)}</p>
                      <div className="flex gap-1 mt-2">
                        {!conta.pago && (
                          <Button
                            size="sm"
                            variant="outline"
                            className="text-green-600 hover:bg-green-50"
                            onClick={() => handlePagar(conta.id)}
                          >
                            <CheckCircle2 size={16} />
                          </Button>
                        )}
                        <Button size="sm" variant="outline" onClick={() => openModal(conta)}>
                          <Edit size={16} />
                        </Button>
                        <Button 
                          size="sm" 
                          variant="outline" 
                          className="text-red-600 hover:bg-red-50"
                          onClick={() => handleDelete(conta.id)}
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
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>{editingConta ? "Editar Conta" : "Nova Conta a Pagar"}</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="form-label">Descrição *</label>
              <Input
                value={formData.descricao}
                onChange={(e) => setFormData({...formData, descricao: e.target.value})}
                placeholder="Ex: Aluguel, Energia, Material..."
                required
                data-testid="input-descricao"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="form-label">Valor *</label>
                <Input
                  type="number"
                  step="0.01"
                  value={formData.valor}
                  onChange={(e) => setFormData({...formData, valor: e.target.value})}
                  placeholder="0,00"
                  required
                  data-testid="input-valor"
                />
              </div>
              <div>
                <label className="form-label">Vencimento *</label>
                <Input
                  type="date"
                  value={formData.vencimento}
                  onChange={(e) => setFormData({...formData, vencimento: e.target.value})}
                  required
                  data-testid="input-vencimento"
                />
              </div>
            </div>
            <div>
              <label className="form-label">Fornecedor</label>
              <Input
                value={formData.fornecedor}
                onChange={(e) => setFormData({...formData, fornecedor: e.target.value})}
                placeholder="Nome do fornecedor"
                data-testid="input-fornecedor"
              />
            </div>
            <div>
              <label className="form-label">Categoria</label>
              <Input
                value={formData.categoria}
                onChange={(e) => setFormData({...formData, categoria: e.target.value})}
                placeholder="Ex: Operacional, Administrativo..."
                data-testid="input-categoria"
              />
            </div>
            <div>
              <label className="form-label">Observações</label>
              <Input
                value={formData.observacoes}
                onChange={(e) => setFormData({...formData, observacoes: e.target.value})}
                placeholder="Observações adicionais"
                data-testid="input-observacoes"
              />
            </div>
            <div className="flex gap-3 pt-2">
              <Button type="button" variant="outline" onClick={closeModal} className="flex-1">
                Cancelar
              </Button>
              <Button type="submit" className="flex-1 bg-blue-600 hover:bg-blue-700" data-testid="submit-conta">
                {editingConta ? "Atualizar" : "Cadastrar"}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
