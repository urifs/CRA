import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "@/App";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { 
  Plus, Search, Truck, Calendar, User, MapPin, CheckCircle2, Clock, XCircle,
  Edit, Trash2, DollarSign, Phone
} from "lucide-react";
import { toast } from "sonner";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";

const tiposPeriodo = [
  { value: "hora", label: "Por Hora" },
  { value: "diaria", label: "Diária" },
  { value: "semanal", label: "Semanal" },
  { value: "quinzenal", label: "Quinzenal" },
  { value: "mensal", label: "Mensal" },
  { value: "semestral", label: "Semestral" },
  { value: "anual", label: "Anual" },
  { value: "outro", label: "Outro (especificar)" }
];

export default function AlugueisPage() {
  const [alugueis, setAlugueis] = useState([]);
  const [maquinas, setMaquinas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("todos");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingAluguel, setEditingAluguel] = useState(null);
  const [formData, setFormData] = useState({
    maquina_id: "",
    maquina_nome: "",
    maquina_placa: "",
    cliente_nome: "",
    cliente_telefone: "",
    cliente_documento: "",
    tipo_periodo: "diaria",
    periodo_especificado: "",
    data_entrega: new Date().toISOString().split("T")[0],
    data_vencimento: "",
    valor: "",
    valor_caucao: "",
    local_entrega: "",
    observacoes: "",
    gerar_conta_receber: true
  });

  useEffect(() => {
    fetchAlugueis();
    fetchMaquinas();
  }, []);

  const fetchAlugueis = async () => {
    try {
      const response = await axios.get(`${API}/admin/alugueis`);
      setAlugueis(response.data);
    } catch (error) {
      toast.error("Erro ao carregar aluguéis");
    } finally {
      setLoading(false);
    }
  };

  const fetchMaquinas = async () => {
    try {
      const response = await axios.get(`${API}/admin/maquinas-disponiveis`);
      setMaquinas(response.data);
    } catch (error) {
      console.error("Erro ao carregar máquinas:", error);
    }
  };

  const handleMaquinaChange = (maquinaId) => {
    const maquina = maquinas.find(m => m.id === maquinaId);
    if (maquina) {
      setFormData({
        ...formData,
        maquina_id: maquina.id,
        maquina_nome: maquina.name,
        maquina_placa: maquina.plate || ""
      });
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const dataToSend = {
        ...formData,
        valor: parseFloat(formData.valor) || 0,
        valor_caucao: parseFloat(formData.valor_caucao) || 0
      };

      if (editingAluguel) {
        await axios.put(`${API}/admin/alugueis/${editingAluguel.id}`, dataToSend);
        toast.success("Aluguel atualizado!");
      } else {
        await axios.post(`${API}/admin/alugueis`, dataToSend);
        toast.success("Aluguel registrado!");
      }
      fetchAlugueis();
      closeModal();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao salvar aluguel");
    }
  };

  const handleUpdateStatus = async (id, status, data_devolucao = null) => {
    try {
      await axios.patch(`${API}/admin/alugueis/${id}/status`, { 
        status,
        data_devolucao: data_devolucao || new Date().toISOString().split("T")[0]
      });
      toast.success(`Aluguel ${status === "finalizado" ? "finalizado" : "atualizado"}!`);
      fetchAlugueis();
    } catch (error) {
      toast.error("Erro ao atualizar status");
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Excluir este aluguel? A conta a receber associada também será excluída.")) return;
    try {
      await axios.delete(`${API}/admin/alugueis/${id}`);
      toast.success("Aluguel excluído!");
      fetchAlugueis();
    } catch (error) {
      toast.error("Erro ao excluir aluguel");
    }
  };

  const openModal = (aluguel = null) => {
    if (aluguel) {
      setEditingAluguel(aluguel);
      setFormData({
        maquina_id: aluguel.maquina_id || "",
        maquina_nome: aluguel.maquina_nome || "",
        maquina_placa: aluguel.maquina_placa || "",
        cliente_nome: aluguel.cliente_nome || "",
        cliente_telefone: aluguel.cliente_telefone || "",
        cliente_documento: aluguel.cliente_documento || "",
        tipo_periodo: aluguel.tipo_periodo || "diaria",
        periodo_especificado: aluguel.periodo_especificado || "",
        data_entrega: aluguel.data_entrega?.split("T")[0] || "",
        data_vencimento: aluguel.data_vencimento?.split("T")[0] || "",
        valor: aluguel.valor?.toString() || "",
        valor_caucao: aluguel.valor_caucao?.toString() || "",
        local_entrega: aluguel.local_entrega || "",
        observacoes: aluguel.observacoes || "",
        gerar_conta_receber: false
      });
    } else {
      setEditingAluguel(null);
      setFormData({
        maquina_id: "",
        maquina_nome: "",
        maquina_placa: "",
        cliente_nome: "",
        cliente_telefone: "",
        cliente_documento: "",
        tipo_periodo: "diaria",
        periodo_especificado: "",
        data_entrega: new Date().toISOString().split("T")[0],
        data_vencimento: "",
        valor: "",
        valor_caucao: "",
        local_entrega: "",
        observacoes: "",
        gerar_conta_receber: true
      });
    }
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setEditingAluguel(null);
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value || 0);
  };

  const getStatusInfo = (status) => {
    switch (status) {
      case "ativo": return { label: "Ativo", color: "bg-green-100 text-green-700", icon: Clock };
      case "finalizado": return { label: "Finalizado", color: "bg-blue-100 text-blue-700", icon: CheckCircle2 };
      case "cancelado": return { label: "Cancelado", color: "bg-red-100 text-red-700", icon: XCircle };
      default: return { label: status, color: "bg-slate-100 text-slate-700", icon: Clock };
    }
  };

  const getPeriodoLabel = (tipo, especificado) => {
    if (tipo === "outro" && especificado) return especificado;
    return tiposPeriodo.find(t => t.value === tipo)?.label || tipo;
  };

  const filteredAlugueis = alugueis.filter(a => {
    const matchSearch = 
      a.numero?.toString().includes(search) ||
      a.cliente_nome?.toLowerCase().includes(search.toLowerCase()) ||
      a.maquina_nome?.toLowerCase().includes(search.toLowerCase()) ||
      a.maquina_placa?.toLowerCase().includes(search.toLowerCase());
    
    if (filter === "todos") return matchSearch;
    return matchSearch && a.status === filter;
  });

  // Totais
  const totalAtivos = alugueis.filter(a => a.status === "ativo").length;
  const valorTotalAtivos = alugueis.filter(a => a.status === "ativo").reduce((s, a) => s + (a.valor || 0), 0);

  if (loading) {
    return <div className="flex items-center justify-center min-h-[400px]"><div className="spinner w-12 h-12"></div></div>;
  }

  return (
    <div data-testid="alugueis-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Aluguéis de Máquinas</h1>
          <p className="text-slate-500 mt-1">Controle de locação de equipamentos</p>
        </div>
        <Button onClick={() => openModal()} className="bg-blue-600 hover:bg-blue-700" data-testid="new-aluguel-btn">
          <Plus size={18} className="mr-2" />Novo Aluguel
        </Button>
      </div>

      {/* Resumo */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-6">
        <Card className="stat-card">
          <CardContent className="p-4 flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
              <Truck className="text-blue-600" size={20} />
            </div>
            <div>
              <p className="text-xs text-slate-500">Total de Aluguéis</p>
              <p className="text-lg font-bold text-blue-600">{alugueis.length}</p>
            </div>
          </CardContent>
        </Card>
        <Card className="stat-card">
          <CardContent className="p-4 flex items-center gap-3">
            <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
              <Clock className="text-green-600" size={20} />
            </div>
            <div>
              <p className="text-xs text-slate-500">Ativos</p>
              <p className="text-lg font-bold text-green-600">{totalAtivos}</p>
            </div>
          </CardContent>
        </Card>
        <Card className="stat-card">
          <CardContent className="p-4 flex items-center gap-3">
            <div className="w-10 h-10 bg-emerald-100 rounded-lg flex items-center justify-center">
              <DollarSign className="text-emerald-600" size={20} />
            </div>
            <div>
              <p className="text-xs text-slate-500">Valor Ativos</p>
              <p className="text-lg font-bold text-emerald-600">{formatCurrency(valorTotalAtivos)}</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filtros */}
      <div className="flex flex-col md:flex-row gap-4 mb-6">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400" size={20} />
          <Input 
            placeholder="Buscar por número, cliente ou máquina..." 
            value={search} 
            onChange={(e) => setSearch(e.target.value)} 
            className="pl-10" 
          />
        </div>
        <div className="flex gap-2 overflow-x-auto pb-2 md:pb-0">
          {[
            { value: "todos", label: "Todos" },
            { value: "ativo", label: "Ativos" },
            { value: "finalizado", label: "Finalizados" },
            { value: "cancelado", label: "Cancelados" }
          ].map(f => (
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
      {filteredAlugueis.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-slate-400">
            <Truck className="mx-auto mb-4" size={48} />
            <p>Nenhum aluguel encontrado</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {filteredAlugueis.map(aluguel => {
            const statusInfo = getStatusInfo(aluguel.status);
            const StatusIcon = statusInfo.icon;
            const isVencido = aluguel.status === "ativo" && aluguel.data_vencimento < new Date().toISOString().split("T")[0];
            
            return (
              <Card key={aluguel.id} className={`hover:shadow-md transition-shadow ${isVencido ? 'border-l-4 border-l-red-500' : ''}`} data-testid={`aluguel-${aluguel.id}`}>
                <CardContent className="p-4">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1 flex-wrap">
                        <span className="font-bold text-blue-600">#{aluguel.numero}</span>
                        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${statusInfo.color}`}>
                          <StatusIcon className="inline mr-1" size={12} />{statusInfo.label}
                        </span>
                        <span className="px-2 py-0.5 rounded text-xs bg-slate-100 text-slate-600">
                          {getPeriodoLabel(aluguel.tipo_periodo, aluguel.periodo_especificado)}
                        </span>
                        {isVencido && (
                          <span className="px-2 py-0.5 rounded text-xs bg-red-100 text-red-700 font-medium">VENCIDO</span>
                        )}
                      </div>
                      <h3 className="font-medium text-slate-900 flex items-center gap-2">
                        <Truck size={16} className="text-slate-400" />
                        {aluguel.maquina_nome}
                        {aluguel.maquina_placa && <span className="text-xs text-slate-500">({aluguel.maquina_placa})</span>}
                      </h3>
                      <p className="text-sm text-slate-500 flex items-center gap-1">
                        <User size={14} />{aluguel.cliente_nome}
                        {aluguel.cliente_telefone && (
                          <span className="flex items-center gap-1 ml-2">
                            <Phone size={12} />{aluguel.cliente_telefone}
                          </span>
                        )}
                      </p>
                      {aluguel.local_entrega && (
                        <p className="text-sm text-slate-500 flex items-center gap-1">
                          <MapPin size={14} />{aluguel.local_entrega}
                        </p>
                      )}
                      <p className="text-sm text-slate-500 flex items-center gap-1">
                        <Calendar size={14} />
                        Entrega: {new Date(aluguel.data_entrega).toLocaleDateString('pt-BR')} | 
                        Vencimento: {new Date(aluguel.data_vencimento).toLocaleDateString('pt-BR')}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-lg font-bold text-slate-900">{formatCurrency(aluguel.valor)}</p>
                      {aluguel.valor_caucao > 0 && (
                        <p className="text-xs text-slate-500">Caução: {formatCurrency(aluguel.valor_caucao)}</p>
                      )}
                      <div className="flex gap-1 mt-2 justify-end">
                        {aluguel.status === "ativo" && (
                          <Button
                            size="sm"
                            variant="outline"
                            className="text-green-600"
                            onClick={() => handleUpdateStatus(aluguel.id, "finalizado")}
                            title="Finalizar"
                          >
                            <CheckCircle2 size={16} />
                          </Button>
                        )}
                        <Button size="sm" variant="outline" onClick={() => openModal(aluguel)}>
                          <Edit size={16} />
                        </Button>
                        <Button size="sm" variant="outline" className="text-red-600" onClick={() => handleDelete(aluguel.id)}>
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
            <DialogTitle>{editingAluguel ? "Editar Aluguel" : "Novo Aluguel"}</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Máquina */}
            <div>
              <label className="form-label">Máquina *</label>
              <select 
                className="form-select" 
                value={formData.maquina_id} 
                onChange={(e) => handleMaquinaChange(e.target.value)}
                required
              >
                <option value="">Selecione uma máquina</option>
                {maquinas.map(m => (
                  <option key={m.id} value={m.id}>
                    {m.name} {m.plate ? `(${m.plate})` : ''} - {m.category_name || 'Sem categoria'}
                  </option>
                ))}
              </select>
              {maquinas.length === 0 && (
                <p className="text-xs text-orange-600 mt-1">
                  Nenhuma máquina cadastrada. Cadastre máquinas no módulo de Gerenciamento Geral.
                </p>
              )}
            </div>

            {/* Cliente */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="form-label">Cliente/Locatário *</label>
                <Input 
                  value={formData.cliente_nome} 
                  onChange={(e) => setFormData({...formData, cliente_nome: e.target.value})} 
                  placeholder="Nome do cliente" 
                  required 
                />
              </div>
              <div>
                <label className="form-label">Telefone</label>
                <Input 
                  value={formData.cliente_telefone} 
                  onChange={(e) => setFormData({...formData, cliente_telefone: e.target.value})} 
                  placeholder="(00) 00000-0000" 
                />
              </div>
            </div>

            <div>
              <label className="form-label">CPF/CNPJ</label>
              <Input 
                value={formData.cliente_documento} 
                onChange={(e) => setFormData({...formData, cliente_documento: e.target.value})} 
                placeholder="Documento do cliente" 
              />
            </div>

            {/* Período */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="form-label">Tipo de Período *</label>
                <select 
                  className="form-select" 
                  value={formData.tipo_periodo} 
                  onChange={(e) => setFormData({...formData, tipo_periodo: e.target.value})}
                >
                  {tiposPeriodo.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
                </select>
              </div>
              {formData.tipo_periodo === "outro" && (
                <div>
                  <label className="form-label">Especificar Período *</label>
                  <Input 
                    value={formData.periodo_especificado} 
                    onChange={(e) => setFormData({...formData, periodo_especificado: e.target.value})} 
                    placeholder="Ex: 45 dias" 
                    required={formData.tipo_periodo === "outro"}
                  />
                </div>
              )}
            </div>

            {/* Datas */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="form-label">Data de Entrega *</label>
                <Input 
                  type="date" 
                  value={formData.data_entrega} 
                  onChange={(e) => setFormData({...formData, data_entrega: e.target.value})} 
                  required 
                />
              </div>
              <div>
                <label className="form-label">Data de Vencimento *</label>
                <Input 
                  type="date" 
                  value={formData.data_vencimento} 
                  onChange={(e) => setFormData({...formData, data_vencimento: e.target.value})} 
                  required 
                />
              </div>
            </div>

            {/* Valores */}
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
                />
              </div>
              <div>
                <label className="form-label">Valor Caução</label>
                <Input 
                  type="number" 
                  step="0.01" 
                  value={formData.valor_caucao} 
                  onChange={(e) => setFormData({...formData, valor_caucao: e.target.value})} 
                  placeholder="0,00" 
                />
              </div>
            </div>

            {/* Local */}
            <div>
              <label className="form-label">Local de Entrega</label>
              <Input 
                value={formData.local_entrega} 
                onChange={(e) => setFormData({...formData, local_entrega: e.target.value})} 
                placeholder="Endereço ou local de entrega" 
              />
            </div>

            {/* Observações */}
            <div>
              <label className="form-label">Observações</label>
              <Input 
                value={formData.observacoes} 
                onChange={(e) => setFormData({...formData, observacoes: e.target.value})} 
                placeholder="Observações adicionais" 
              />
            </div>

            {/* Gerar conta a receber */}
            {!editingAluguel && (
              <div className="flex items-center gap-2 p-3 bg-blue-50 rounded-lg">
                <input 
                  type="checkbox" 
                  id="gerar_conta" 
                  checked={formData.gerar_conta_receber} 
                  onChange={(e) => setFormData({...formData, gerar_conta_receber: e.target.checked})} 
                  className="w-4 h-4" 
                />
                <label htmlFor="gerar_conta" className="text-sm text-blue-700">
                  Gerar automaticamente uma conta a receber para este aluguel
                </label>
              </div>
            )}

            <div className="flex gap-3 pt-2">
              <Button type="button" variant="outline" onClick={closeModal} className="flex-1">Cancelar</Button>
              <Button type="submit" className="flex-1 bg-blue-600 hover:bg-blue-700">
                {editingAluguel ? "Atualizar" : "Registrar Aluguel"}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
