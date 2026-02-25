import { useState, useEffect } from "react";
import axios from "axios";
import { API, useAuth } from "@/App";
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
  Plus, Search, CreditCard, Calendar, CheckCircle2, AlertCircle, Clock, Edit, Trash2, X, Filter, Paperclip
} from "lucide-react";
import { toast } from "sonner";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import AttachmentsSection from "@/components/AttachmentsSection";

const formasPagamento = [
  { value: "dinheiro", label: "Dinheiro" },
  { value: "pix", label: "PIX" },
  { value: "cartao_debito", label: "Cartão Débito" },
  { value: "cartao_credito", label: "Cartão Crédito" },
  { value: "boleto", label: "Boleto" },
  { value: "cheque", label: "Cheque" },
  { value: "transferencia", label: "Transferência" },
  { value: "deposito", label: "Depósito" },
];

export default function ContasPagarPage() {
  const { token } = useAuth();
  const [contas, setContas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [filterStatus, setFilterStatus] = useState("");
  const [filterVencimento, setFilterVencimento] = useState("");
  const [filterFormaPag, setFilterFormaPag] = useState("");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingConta, setEditingConta] = useState(null);
  const [planoContas, setPlanoContas] = useState([]);
  const [subcontas, setSubcontas] = useState([]);
  const [centrosCusto, setCentrosCusto] = useState([]);
  const [formasPagamentoDB, setFormasPagamentoDB] = useState([]);
  const [cadastros, setCadastros] = useState([]);
  
  const [formData, setFormData] = useState({
    fornecedor_nome: "", documento: "", numero_doc: "", descricao: "",
    valor: "", valor_desconto: "0", valor_juros: "0", valor_multa: "0",
    data_emissao: "", data_vencimento: "",
    plano_conta_id: "", plano_conta_nome: "", 
    subconta_id: "", subconta_nome: "",
    centro_custo: "",
    forma_pagamento: "boleto", conta_movimento: "", observacoes: ""
  });

  useEffect(() => { fetchContas(); fetchPlanoContas(); fetchCentrosCusto(); fetchFormasPagamento(); fetchCadastros(); }, [filterStatus, filterVencimento, filterFormaPag]);

  const fetchContas = async () => {
    try {
      let url = `${API}/admin/contas-pagar`;
      const params = new URLSearchParams();
      if (filterStatus) params.append("status", filterStatus);
      if (filterVencimento) params.append("vencimento", filterVencimento);
      if (filterFormaPag) params.append("forma_pagamento", filterFormaPag);
      if (params.toString()) url += `?${params.toString()}`;
      const response = await axios.get(url);
      setContas(response.data);
    } catch (error) { toast.error("Erro ao carregar contas"); }
    finally { setLoading(false); }
  };

  const fetchPlanoContas = async () => {
    try {
      const response = await axios.get(`${API}/admin/plano-contas`);
      // Separar contas principais (nível 1) e subcontas (nível 2)
      const todas = response.data;
      setPlanoContas(todas.filter(p => p.nivel === 1));
      setSubcontas(todas.filter(p => p.nivel === 2));
    } catch (error) { console.error(error); }
  };
  
  // Filtrar subcontas pelo plano de contas selecionado
  const subcontasFiltradas = formData.plano_conta_id 
    ? subcontas.filter(s => s.pai_id === formData.plano_conta_id)
    : [];

  const fetchCentrosCusto = async () => {
    try {
      const response = await axios.get(`${API}/admin/centros-custo`);
      setCentrosCusto(response.data);
    } catch (error) { console.error(error); }
  };

  const fetchFormasPagamento = async () => {
    try {
      const response = await axios.get(`${API}/admin/formas-pagamento?ativo=true`);
      setFormasPagamentoDB(response.data);
    } catch (error) { console.error(error); }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const dataToSend = {
        ...formData,
        valor: parseFloat(formData.valor) || 0,
        valor_desconto: parseFloat(formData.valor_desconto) || 0,
        valor_juros: parseFloat(formData.valor_juros) || 0,
        valor_multa: parseFloat(formData.valor_multa) || 0,
      };
      if (editingConta) {
        await axios.put(`${API}/admin/contas-pagar/${editingConta.id}`, dataToSend);
        toast.success("Conta atualizada!");
      } else {
        await axios.post(`${API}/admin/contas-pagar`, dataToSend);
        toast.success("Conta cadastrada!");
      }
      fetchContas(); closeModal();
    } catch (error) { toast.error(error.response?.data?.detail || "Erro ao salvar"); }
  };

  const handleQuitar = async (id) => {
    try {
      await axios.patch(`${API}/admin/contas-pagar/${id}/quitar`);
      toast.success("Conta quitada!"); fetchContas();
    } catch (error) { toast.error("Erro ao quitar"); }
  };

  const handleCancelar = async (id) => {
    if (!window.confirm("Cancelar esta conta?")) return;
    try {
      await axios.patch(`${API}/admin/contas-pagar/${id}/cancelar`);
      toast.success("Conta cancelada!"); fetchContas();
    } catch (error) { toast.error("Erro ao cancelar"); }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Excluir esta conta?")) return;
    try {
      await axios.delete(`${API}/admin/contas-pagar/${id}`);
      toast.success("Conta excluída!"); fetchContas();
    } catch (error) { toast.error("Erro ao excluir"); }
  };

  const openModal = (conta = null) => {
    if (conta) {
      setEditingConta(conta);
      setFormData({
        fornecedor_nome: conta.fornecedor_nome || "",
        documento: conta.documento || "",
        numero_doc: conta.numero_doc || "",
        descricao: conta.descricao || "",
        valor: conta.valor?.toString() || "",
        valor_desconto: conta.valor_desconto?.toString() || "0",
        valor_juros: conta.valor_juros?.toString() || "0",
        valor_multa: conta.valor_multa?.toString() || "0",
        data_emissao: conta.data_emissao || "",
        data_vencimento: conta.data_vencimento || "",
        plano_conta_id: conta.plano_conta_id || "",
        plano_conta_nome: conta.plano_conta_nome || "",
        subconta_id: conta.subconta_id || "",
        subconta_nome: conta.subconta_nome || "",
        centro_custo: conta.centro_custo || "",
        forma_pagamento: conta.forma_pagamento || "boleto",
        conta_movimento: conta.conta_movimento || "",
        observacoes: conta.observacoes || ""
      });
    } else {
      setEditingConta(null);
      setFormData({
        fornecedor_nome: "", documento: "", numero_doc: "", descricao: "",
        valor: "", valor_desconto: "0", valor_juros: "0", valor_multa: "0",
        data_emissao: new Date().toISOString().split("T")[0], data_vencimento: "",
        plano_conta_id: "", plano_conta_nome: "", 
        subconta_id: "", subconta_nome: "",
        centro_custo: "",
        forma_pagamento: "boleto", conta_movimento: "", observacoes: ""
      });
    }
    setIsModalOpen(true);
  };

  const closeModal = () => { setIsModalOpen(false); setEditingConta(null); };

  const formatCurrency = (v) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(v || 0);

  const getStatusInfo = (conta) => {
    if (conta.status === "quitada") return { label: "Quitada", color: "bg-green-100 text-green-700", icon: CheckCircle2 };
    if (conta.status === "cancelada") return { label: "Cancelada", color: "bg-gray-100 text-gray-700", icon: X };
    const hoje = new Date().toISOString().split("T")[0];
    if (conta.data_vencimento < hoje) return { label: "Vencida", color: "bg-red-100 text-red-700", icon: AlertCircle };
    if (conta.data_vencimento === hoje) return { label: "Vence Hoje", color: "bg-orange-100 text-[#E31A1A]", icon: Clock };
    return { label: "Em Aberto", color: "bg-blue-100 text-[#D4A000]", icon: Calendar };
  };

  const filteredContas = contas.filter(c => {
    const matchSearch = c.descricao?.toLowerCase().includes(search.toLowerCase()) ||
      c.fornecedor_nome?.toLowerCase().includes(search.toLowerCase()) ||
      c.documento?.toLowerCase().includes(search.toLowerCase());
    
    if (!matchSearch) return false;
    if (filterStatus && filterStatus !== "all" && c.status !== filterStatus) return false;
    if (filterFormaPag && filterFormaPag !== "all" && c.forma_pagamento !== filterFormaPag) return false;
    
    const hoje = new Date().toISOString().split("T")[0];
    if (filterVencimento === "vencidas" && (c.status !== "em_aberto" || c.data_vencimento >= hoje)) return false;
    if (filterVencimento === "hoje" && c.data_vencimento !== hoje) return false;
    if (filterVencimento === "a_vencer" && (c.status !== "em_aberto" || c.data_vencimento <= hoje)) return false;
    
    return true;
  });

  // Totais
  const totalEmAberto = filteredContas.filter(c => c.status === "em_aberto").reduce((s, c) => s + (c.valor_final || c.valor || 0), 0);
  const totalVencidas = filteredContas.filter(c => c.status === "em_aberto" && c.data_vencimento < new Date().toISOString().split("T")[0]).reduce((s, c) => s + (c.valor_final || c.valor || 0), 0);
  const totalRegistros = filteredContas.length;

  if (loading) return <div className="flex items-center justify-center min-h-[400px]"><div className="spinner w-12 h-12"></div></div>;

  return (
    <div data-testid="contas-pagar-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Contas a Pagar</h1>
          <p className="text-gray-500 mt-1">Gestão de despesas e pagamentos</p>
        </div>
        <Button onClick={() => openModal()} className="bg-red-600 hover:bg-red-700"><Plus size={18} className="mr-2" />Nova Conta</Button>
      </div>

      {/* Resumo */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <Card className="border-l-4 border-l-blue-500"><CardContent className="p-4">
          <p className="text-sm text-gray-500">Total Em Aberto</p>
          <p className="text-xl font-bold text-[#D4A000]">{formatCurrency(totalEmAberto)}</p>
        </CardContent></Card>
        <Card className="border-l-4 border-l-red-500"><CardContent className="p-4">
          <p className="text-sm text-gray-500">Total Vencidas</p>
          <p className="text-xl font-bold text-red-600">{formatCurrency(totalVencidas)}</p>
        </CardContent></Card>
        <Card className="border-l-4 border-l-slate-500"><CardContent className="p-4">
          <p className="text-sm text-gray-500">Registros</p>
          <p className="text-xl font-bold text-gray-600">{totalRegistros}</p>
        </CardContent></Card>
      </div>

      {/* Filtros */}
      <div className="grid grid-cols-1 md:grid-cols-6 gap-4 mb-6">
        <div className="relative md:col-span-2">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
          <Input placeholder="Buscar..." value={search} onChange={(e) => setSearch(e.target.value)} className="pl-10" />
        </div>
        <Select value={filterStatus} onValueChange={setFilterStatus}>
          <SelectTrigger className="h-11"><SelectValue placeholder="Todos Status" /></SelectTrigger>
          <SelectContent className="z-[9999]">
            <SelectItem value="all">Todos Status</SelectItem>
            <SelectItem value="em_aberto">Em Aberto</SelectItem>
            <SelectItem value="quitada">Quitadas</SelectItem>
            <SelectItem value="cancelada">Canceladas</SelectItem>
          </SelectContent>
        </Select>
        <Select value={filterVencimento} onValueChange={setFilterVencimento}>
          <SelectTrigger className="h-11"><SelectValue placeholder="Vencimento" /></SelectTrigger>
          <SelectContent className="z-[9999]">
            <SelectItem value="all">Todos</SelectItem>
            <SelectItem value="vencidas">Vencidas</SelectItem>
            <SelectItem value="hoje">Hoje</SelectItem>
            <SelectItem value="a_vencer">A Vencer</SelectItem>
          </SelectContent>
        </Select>
        <Select value={filterFormaPag} onValueChange={setFilterFormaPag}>
          <SelectTrigger className="h-11"><SelectValue placeholder="Forma Pagamento" /></SelectTrigger>
          <SelectContent className="z-[9999]">
            <SelectItem value="all">Todas Formas</SelectItem>
            {formasPagamento.map(f => <SelectItem key={f.value} value={f.value}>{f.label}</SelectItem>)}
          </SelectContent>
        </Select>
        <Button className="h-11 bg-[#D4A000] hover:bg-[#b38900] text-black">
          <Search size={16} className="mr-2" />
          Buscar
        </Button>
      </div>

      {/* Tabela */}
      {filteredContas.length === 0 ? (
        <Card><CardContent className="py-12 text-center text-gray-400"><CreditCard className="mx-auto mb-4" size={48} /><p>Nenhuma conta encontrada</p></CardContent></Card>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full border-collapse bg-white rounded-lg overflow-hidden shadow text-sm">
            <thead className="bg-gray-100">
              <tr>
                <th className="text-left p-3 font-medium text-gray-600">Núm.</th>
                <th className="text-left p-3 font-medium text-gray-600">Fornecedor</th>
                <th className="text-left p-3 font-medium text-gray-600">Descrição</th>
                <th className="text-left p-3 font-medium text-gray-600">Documento</th>
                <th className="text-left p-3 font-medium text-gray-600">Emissão</th>
                <th className="text-left p-3 font-medium text-gray-600">Vencimento</th>
                <th className="text-right p-3 font-medium text-gray-600">Valor R$</th>
                <th className="text-left p-3 font-medium text-gray-600">Forma Pag.</th>
                <th className="text-left p-3 font-medium text-gray-600">Status</th>
                <th className="text-center p-3 font-medium text-gray-600">Ações</th>
              </tr>
            </thead>
            <tbody>
              {filteredContas.map((c) => {
                const status = getStatusInfo(c);
                const StatusIcon = status.icon;
                return (
                  <tr 
                    key={c.id} 
                    className="border-t hover:bg-gray-50 cursor-pointer transition-colors"
                    onClick={() => openModal(c)}
                  >
                    <td className="p-3 font-mono">{c.numero}</td>
                    <td className="p-3">{c.fornecedor_nome || "-"}</td>
                    <td className="p-3 max-w-[200px] truncate">{c.descricao}</td>
                    <td className="p-3">{c.documento || "-"}</td>
                    <td className="p-3">{c.data_emissao ? new Date(c.data_emissao).toLocaleDateString('pt-BR') : "-"}</td>
                    <td className="p-3">{new Date(c.data_vencimento).toLocaleDateString('pt-BR')}</td>
                    <td className="p-3 text-right font-medium text-red-600">{formatCurrency(c.valor_final || c.valor)}</td>
                    <td className="p-3 text-xs">{formasPagamentoDB.find(f => f.nome?.toLowerCase() === c.forma_pagamento?.toLowerCase())?.nome || formasPagamento.find(f => f.value === c.forma_pagamento)?.label || c.forma_pagamento}</td>
                    <td className="p-3"><span className={`px-2 py-1 rounded text-xs ${status.color}`}><StatusIcon className="inline mr-1" size={12} />{status.label}</span></td>
                    <td className="p-3 text-center" onClick={(e) => e.stopPropagation()}>
                      <div className="flex justify-center gap-1">
                        {c.status === "em_aberto" && <Button size="sm" variant="outline" className="text-green-600" onClick={() => handleQuitar(c.id)} title="Quitar"><CheckCircle2 size={14} /></Button>}
                        <Button size="sm" variant="outline" onClick={() => openModal(c)}><Edit size={14} /></Button>
                        {c.status === "em_aberto" && <Button size="sm" variant="outline" className="text-[#E31A1A]" onClick={() => handleCancelar(c.id)} title="Cancelar"><X size={14} /></Button>}
                        <Button size="sm" variant="outline" className="text-red-600" onClick={() => handleDelete(c.id)}><Trash2 size={14} /></Button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Modal */}
      <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader><DialogTitle>{editingConta ? "Editar Conta a Pagar" : "Nova Conta a Pagar"}</DialogTitle></DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-3 gap-4">
              <div className="col-span-2">
                <label className="form-label">Fornecedor</label>
                <Input value={formData.fornecedor_nome} onChange={(e) => setFormData({...formData, fornecedor_nome: e.target.value})} />
              </div>
              <div>
                <label className="form-label">Forma de Pagamento</label>
                <Select value={formData.forma_pagamento} onValueChange={(value) => setFormData({...formData, forma_pagamento: value})}>
                  <SelectTrigger className="w-full h-11"><SelectValue placeholder="Selecione..." /></SelectTrigger>
                  <SelectContent className="z-[9999]">
                    {/* Formas padrão */}
                    {formasPagamento.map(f => <SelectItem key={f.value} value={f.value}>{f.label}</SelectItem>)}
                    {/* Formas cadastradas (que não estejam nas padrão) */}
                    {formasPagamentoDB
                      .filter(f => !formasPagamento.some(fp => fp.value.toLowerCase() === f.nome?.toLowerCase() || fp.label.toLowerCase() === f.nome?.toLowerCase()))
                      .map(f => <SelectItem key={f.id} value={f.nome}>{f.nome}</SelectItem>)
                    }
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="grid grid-cols-3 gap-4">
              <div><label className="form-label">Documento (NF)</label><Input value={formData.documento} onChange={(e) => setFormData({...formData, documento: e.target.value})} /></div>
              <div><label className="form-label">Nº Doc.</label><Input value={formData.numero_doc} onChange={(e) => setFormData({...formData, numero_doc: e.target.value})} /></div>
              <div><label className="form-label">Conta Movimento</label><Input value={formData.conta_movimento} onChange={(e) => setFormData({...formData, conta_movimento: e.target.value})} /></div>
            </div>
            <div>
              <label className="form-label">Descrição *</label>
              <Input value={formData.descricao} onChange={(e) => setFormData({...formData, descricao: e.target.value})} required />
            </div>
            <div className="grid grid-cols-4 gap-4">
              <div><label className="form-label">Valor *</label><Input type="number" step="0.01" value={formData.valor} onChange={(e) => setFormData({...formData, valor: e.target.value})} required /></div>
              <div><label className="form-label">Desconto</label><Input type="number" step="0.01" value={formData.valor_desconto} onChange={(e) => setFormData({...formData, valor_desconto: e.target.value})} /></div>
              <div><label className="form-label">Juros</label><Input type="number" step="0.01" value={formData.valor_juros} onChange={(e) => setFormData({...formData, valor_juros: e.target.value})} /></div>
              <div><label className="form-label">Multa</label><Input type="number" step="0.01" value={formData.valor_multa} onChange={(e) => setFormData({...formData, valor_multa: e.target.value})} /></div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div><label className="form-label">Data Emissão</label><Input type="date" value={formData.data_emissao} onChange={(e) => setFormData({...formData, data_emissao: e.target.value})} /></div>
              <div><label className="form-label">Data Vencimento *</label><Input type="date" value={formData.data_vencimento} onChange={(e) => setFormData({...formData, data_vencimento: e.target.value})} required /></div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="form-label">Plano de Contas</label>
                <Select value={formData.plano_conta_id || "none"} onValueChange={(value) => {
                  if (value === "none") {
                    setFormData({...formData, plano_conta_id: "", plano_conta_nome: "", subconta_id: "", subconta_nome: ""});
                  } else {
                    const pc = planoContas.find(p => p.id === value);
                    setFormData({...formData, plano_conta_id: value, plano_conta_nome: pc?.nome || "", subconta_id: "", subconta_nome: ""});
                  }
                }}>
                  <SelectTrigger className="w-full h-11"><SelectValue placeholder="Selecione o tipo de conta..." /></SelectTrigger>
                  <SelectContent className="z-[9999]">
                    <SelectItem value="none">Nenhum</SelectItem>
                    {planoContas.map(p => <SelectItem key={p.id} value={p.id}>{p.codigo ? `${p.codigo} - ` : ""}{p.nome}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="form-label">Subconta</label>
                <Select 
                  value={formData.subconta_id || "none"} 
                  onValueChange={(value) => {
                    if (value === "none") {
                      setFormData({...formData, subconta_id: "", subconta_nome: ""});
                    } else {
                      const sc = subcontasFiltradas.find(s => s.id === value);
                      setFormData({...formData, subconta_id: value, subconta_nome: sc?.nome || ""});
                    }
                  }}
                  disabled={!formData.plano_conta_id}
                >
                  <SelectTrigger className="w-full h-11"><SelectValue placeholder={formData.plano_conta_id ? "Selecione a subconta..." : "Selecione um plano primeiro"} /></SelectTrigger>
                  <SelectContent className="z-[9999]">
                    <SelectItem value="none">Nenhum</SelectItem>
                    {subcontasFiltradas.map(s => <SelectItem key={s.id} value={s.id}>{s.codigo ? `${s.codigo} - ` : ""}{s.nome}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="form-label">Centro de Custo</label>
                <Select value={formData.centro_custo || "none"} onValueChange={(value) => setFormData({...formData, centro_custo: value === "none" ? "" : value})}>
                  <SelectTrigger className="w-full h-11"><SelectValue placeholder="Selecione..." /></SelectTrigger>
                  <SelectContent className="z-[9999]">
                    <SelectItem value="none">Nenhum</SelectItem>
                    {centrosCusto.map(c => <SelectItem key={c.id} value={c.nome}>{c.nome}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <div><label className="form-label">Observações</label><Input value={formData.observacoes} onChange={(e) => setFormData({...formData, observacoes: e.target.value})} /></div>
            </div>
            
            {/* Seção de Anexos */}
            {editingConta && (
              <div className="border-t pt-4 mt-2">
                <AttachmentsSection 
                  entityType="contas_pagar" 
                  entityId={editingConta.id}
                  accentColor="#D4A000"
                />
              </div>
            )}

            <div className="flex gap-3 pt-4">
              <Button type="button" variant="outline" onClick={closeModal} className="flex-1">Cancelar</Button>
              <Button type="submit" className="flex-1 bg-red-600 hover:bg-red-700">{editingConta ? "Atualizar" : "Cadastrar"}</Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
