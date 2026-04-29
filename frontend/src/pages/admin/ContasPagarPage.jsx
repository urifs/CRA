import { useState, useEffect } from "react";
import axios from "axios";
import { API, useAuth } from "@/App";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { MaskedDateInput } from "@/components/MaskedDateInput";
import { Textarea } from "@/components/ui/textarea";
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { 
  Plus, Search, CreditCard, Calendar, CheckCircle2, AlertCircle, Clock, Edit, Trash2, X, Filter, Paperclip, UserPlus, Landmark, History, DollarSign, CircleDot, FileDown, TrendingUp, TrendingDown
} from "lucide-react";
import { toast } from "sonner";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import AttachmentsSection from "@/components/AttachmentsSection";
import CadastroFormModal from "@/components/CadastroFormModal";
import { formatCurrency as formatCurrencyInput, parseCurrency } from "@/utils/masks";

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
  const [valorBusca, setValorBusca] = useState("");
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
  const [frotas, setFrotas] = useState([]);
  const [contasBancarias, setContasBancarias] = useState([]);
  const [showNovoCadastro, setShowNovoCadastro] = useState(false);
  
  // Modal de Quitação
  const [showQuitarModal, setShowQuitarModal] = useState(false);
  const [quitarContaId, setQuitarContaId] = useState(null);
  const [quitarContaInfo, setQuitarContaInfo] = useState(null);
  const [dataPagamento, setDataPagamento] = useState(new Date().toISOString().split("T")[0]);
  const [quitarContaBancaria, setQuitarContaBancaria] = useState("");
  const [valorPagamento, setValorPagamento] = useState("");
  const [tipoPagamento, setTipoPagamento] = useState("total"); // "total" ou "parcial"
  const [observacaoPagamento, setObservacaoPagamento] = useState("");
  const [valorJuros, setValorJuros] = useState("");
  const [valorMulta, setValorMulta] = useState("");
  const [valorDesconto, setValorDesconto] = useState("");
  const [showHistoricoPagamentos, setShowHistoricoPagamentos] = useState(false);
  
  // Estados para parcelamento
  const [isParcelado, setIsParcelado] = useState(false);
  const [totalParcelas, setTotalParcelas] = useState("1");
  const [intervaloDias, setIntervaloDias] = useState("30");
  
  const [formData, setFormData] = useState({
    fornecedor_nome: "", documento: "", numero_doc: "", descricao: "",
    valor: "", valor_desconto: "0", valor_juros: "0", valor_multa: "0",
    data_emissao: "", data_vencimento: "",
    plano_conta_id: "", plano_conta_nome: "", 
    subconta_id: "", subconta_nome: "",
    centro_custo: "",
    frota_id: "", frota_nome: "",
    conta_bancaria_id: "", conta_bancaria_nome: "",
    forma_pagamento: "boleto", conta_movimento: "", observacoes: "",
    numero_parcela: "", total_parcelas: ""
  });

  useEffect(() => { fetchContas(); fetchPlanoContas(); fetchCentrosCusto(); fetchFormasPagamento(); fetchCadastros(); fetchFrotas(); fetchContasBancarias(); }, [filterStatus, filterVencimento, filterFormaPag, valorBusca]);

  const fetchContas = async () => {
    try {
      let url = `${API}/admin/contas-pagar`;
      const params = new URLSearchParams();
      if (filterStatus) params.append("status", filterStatus);
      if (filterVencimento) params.append("vencimento", filterVencimento);
      if (filterFormaPag) params.append("forma_pagamento", filterFormaPag);
      if (valorBusca && !isNaN(parseFloat(valorBusca))) params.append("valor", parseFloat(valorBusca));
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

  const fetchCadastros = async () => {
    try {
      const response = await axios.get(`${API}/admin/cadastros`);
      setCadastros(response.data);
    } catch (error) { console.error(error); }
  };

  const fetchFrotas = async () => {
    try {
      const response = await axios.get(`${API}/fleets`);
      setFrotas(response.data);
    } catch (error) { console.error(error); }
  };

  const fetchContasBancarias = async () => {
    try {
      const response = await axios.get(`${API}/admin/contas-bancarias?ativo=true`);
      setContasBancarias(response.data);
    } catch (error) { console.error(error); }
  };

  const handleNovoCadastroSuccess = (novoCadastro) => {
    // Atualizar o formulário com o nome do novo fornecedor
    setFormData({ ...formData, fornecedor_nome: novoCadastro.nome_razao });
    // Atualizar a lista de cadastros
    fetchCadastros();
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const valorTotal = parseCurrency(formData.valor) || 0;
      
      // Se for parcelado e não for edição
      if (isParcelado && !editingConta && parseInt(totalParcelas) > 1) {
        const numParcelas = parseInt(totalParcelas);
        if (!Number.isFinite(numParcelas) || numParcelas < 2 || numParcelas > 360) {
          toast.error("Número de parcelas deve ser entre 2 e 360");
          return;
        }
        const dataParcelado = {
          fornecedor_id: formData.fornecedor_id,
          fornecedor_nome: formData.fornecedor_nome,
          documento: formData.documento,
          numero_doc: formData.numero_doc,
          descricao: formData.descricao,
          valor_total: valorTotal,
          valor_desconto: parseCurrency(formData.valor_desconto) || 0,
          valor_juros: parseCurrency(formData.valor_juros) || 0,
          valor_multa: parseCurrency(formData.valor_multa) || 0,
          data_emissao: formData.data_emissao,
          data_primeiro_vencimento: formData.data_vencimento,
          total_parcelas: parseInt(totalParcelas),
          intervalo_dias: parseInt(intervaloDias),
          plano_conta_id: formData.plano_conta_id,
          plano_conta_nome: formData.plano_conta_nome,
          subconta_id: formData.subconta_id,
          subconta_nome: formData.subconta_nome,
          centro_custo: formData.centro_custo,
          frota_id: formData.frota_id,
          frota_nome: formData.frota_nome,
          forma_pagamento: formData.forma_pagamento,
          conta_movimento: formData.conta_movimento,
          conta_bancaria_id: formData.conta_bancaria_id,
          conta_bancaria_nome: formData.conta_bancaria_nome,
          observacoes: formData.observacoes
        };
        
        const response = await axios.post(`${API}/admin/contas-pagar/parcelado`, dataParcelado);
        toast.success(`${response.data.parcelas.length} parcelas criadas com sucesso!`);
      } else {
        // Conta única ou edição
        const dataToSend = {
          ...formData,
          valor: valorTotal,
          valor_desconto: parseCurrency(formData.valor_desconto) || 0,
          valor_juros: parseCurrency(formData.valor_juros) || 0,
          valor_multa: parseCurrency(formData.valor_multa) || 0,
          numero_parcela: parseInt(formData.numero_parcela) || 1,
          total_parcelas: parseInt(formData.total_parcelas) || 1,
        };
        
        if (editingConta) {
          await axios.put(`${API}/admin/contas-pagar/${editingConta.id}`, dataToSend);
          toast.success("Conta atualizada!");
        } else {
          await axios.post(`${API}/admin/contas-pagar`, dataToSend);
          toast.success("Conta cadastrada!");
        }
      }
      fetchContas(); closeModal();
    } catch (error) { toast.error(error.response?.data?.detail || "Erro ao salvar"); }
  };

  const openQuitarModal = (conta) => {
    setQuitarContaId(conta.id);
    setQuitarContaInfo(conta);
    setDataPagamento(new Date().toISOString().split("T")[0]);
    setQuitarContaBancaria(conta.conta_bancaria_id || "");
    // Calcular saldo restante
    const valorTotal = conta.valor_final || conta.valor;
    const valorJaPago = conta.valor_pago || 0;
    const saldoRestante = valorTotal - valorJaPago;
    setValorPagamento(formatCurrencyInput(saldoRestante.toFixed(2)));
    setTipoPagamento("total");
    setObservacaoPagamento("");
    setValorJuros("");
    setValorMulta("");
    setValorDesconto("");
    setShowHistoricoPagamentos(false);
    setShowQuitarModal(true);
  };

  const handleQuitar = async () => {
    if (!quitarContaBancaria) {
      toast.error("Selecione a conta bancária");
      return;
    }
    
    const valorTotal = quitarContaInfo.valor_final || quitarContaInfo.valor;
    const valorJaPago = quitarContaInfo.valor_pago || 0;
    const saldoRestante = valorTotal - valorJaPago;
    
    // Se for pagamento parcial, usar o valor informado
    let valorPagar = saldoRestante;
    if (tipoPagamento === "parcial") {
      valorPagar = parseCurrency(valorPagamento);
      if (!valorPagar || valorPagar <= 0) {
        toast.error("Informe um valor válido para o pagamento");
        return;
      }
      if (valorPagar > saldoRestante + 0.01) {
        toast.error(`Valor excede o saldo restante (${formatCurrency(saldoRestante)})`);
        return;
      }
    }
    
    try {
      const response = await axios.patch(`${API}/admin/contas-pagar/${quitarContaId}/quitar`, {
        data_pagamento: dataPagamento,
        conta_bancaria_id: quitarContaBancaria,
        valor_pago: tipoPagamento === "parcial" ? valorPagar : null,
        valor_juros: parseCurrency(valorJuros) || 0,
        valor_multa: parseCurrency(valorMulta) || 0,
        valor_desconto: parseCurrency(valorDesconto) || 0,
        observacao: observacaoPagamento || null
      });
      
      const msg = response.data.status === "quitada" 
        ? "Conta quitada com sucesso!" 
        : `Pagamento parcial registrado! Saldo restante: ${formatCurrency(response.data.saldo_restante)}`;
      toast.success(msg);
      
      setShowQuitarModal(false);
      setQuitarContaId(null);
      setQuitarContaInfo(null);
      setQuitarContaBancaria("");
      setValorPagamento("");
      setTipoPagamento("total");
      setObservacaoPagamento("");
      setValorJuros("");
      setValorMulta("");
      setValorDesconto("");
      fetchContas();
    } catch (error) { 
      toast.error(error.response?.data?.detail || "Erro ao processar pagamento"); 
    }
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
        valor: conta.valor ? formatCurrencyInput((conta.valor * 100).toString()) : "",
        valor_desconto: conta.valor_desconto ? formatCurrencyInput((conta.valor_desconto * 100).toString()) : "R$ 0,00",
        valor_juros: conta.valor_juros ? formatCurrencyInput((conta.valor_juros * 100).toString()) : "R$ 0,00",
        valor_multa: conta.valor_multa ? formatCurrencyInput((conta.valor_multa * 100).toString()) : "R$ 0,00",
        data_emissao: conta.data_emissao || "",
        data_vencimento: conta.data_vencimento || "",
        plano_conta_id: conta.plano_conta_id || "",
        plano_conta_nome: conta.plano_conta_nome || "",
        subconta_id: conta.subconta_id || "",
        subconta_nome: conta.subconta_nome || "",
        centro_custo: conta.centro_custo || "",
        frota_id: conta.frota_id || "",
        frota_nome: conta.frota_nome || "",
        conta_bancaria_id: conta.conta_bancaria_id || "",
        conta_bancaria_nome: conta.conta_bancaria_nome || "",
        forma_pagamento: conta.forma_pagamento || "boleto",
        conta_movimento: conta.conta_movimento || "",
        observacoes: conta.observacoes || "",
        numero_parcela: conta.numero_parcela ? String(conta.numero_parcela) : "",
        total_parcelas: conta.total_parcelas ? String(conta.total_parcelas) : ""
      });
    } else {
      setEditingConta(null);
      setFormData({
        fornecedor_nome: "", documento: "", numero_doc: "", descricao: "",
        valor: "", valor_desconto: "R$ 0,00", valor_juros: "R$ 0,00", valor_multa: "R$ 0,00",
        data_emissao: new Date().toISOString().split("T")[0], data_vencimento: "",
        plano_conta_id: "", plano_conta_nome: "", 
        subconta_id: "", subconta_nome: "",
        centro_custo: "",
        frota_id: "", frota_nome: "",
        conta_bancaria_id: "", conta_bancaria_nome: "",
        forma_pagamento: "boleto", conta_movimento: "", observacoes: "",
        numero_parcela: "", total_parcelas: ""
      });
    }
    setIsModalOpen(true);
  };

  const closeModal = () => { 
    setIsModalOpen(false); 
    setEditingConta(null); 
    setIsParcelado(false);
    setTotalParcelas("1");
    setIntervaloDias("30");
  };

  const formatCurrency = (v) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(v || 0);

  // Calcula valor final: Valor - Desconto + Juros + Multa
  const calcularValorFinal = () => {
    const valor = parseCurrency(formData.valor) || 0;
    const desconto = parseCurrency(formData.valor_desconto) || 0;
    const juros = parseCurrency(formData.valor_juros) || 0;
    const multa = parseCurrency(formData.valor_multa) || 0;
    return valor - desconto + juros + multa;
  };

  const getStatusInfo = (conta) => {
    if (conta.status === "quitada") return { label: "Quitada", color: "bg-green-100 text-green-700", icon: CheckCircle2 };
    if (conta.status === "parcial") return { label: "Parcial", color: "bg-yellow-100 text-yellow-700", icon: CircleDot };
    if (conta.status === "cancelada") return { label: "Cancelada", color: "bg-gray-100 text-gray-700", icon: X };
    const hoje = new Date().toISOString().split("T")[0];
    if (conta.data_vencimento < hoje) return { label: "Vencida", color: "bg-red-100 text-red-700", icon: AlertCircle };
    if (conta.data_vencimento === hoje) return { label: "Vence Hoje", color: "bg-orange-100 text-[#E31A1A]", icon: Clock };
    return { label: "Em Aberto", color: "bg-blue-100 text-[#D4A000]", icon: Calendar };
  };

  const filteredContas = contas.filter(c => {
    const s = search.toLowerCase();
    const matchSearch = c.descricao?.toLowerCase().includes(s) ||
      c.fornecedor_nome?.toLowerCase().includes(s) ||
      c.documento?.toLowerCase().includes(s) ||
      c.numero_doc?.toLowerCase?.().includes(s) ||
      String(c.numero_doc || "").includes(s) ||
      String(c.numero || "").includes(s);
    
    if (!matchSearch) return false;
    if (filterStatus && filterStatus !== "all" && c.status !== filterStatus) return false;
    if (filterFormaPag && filterFormaPag !== "all" && c.forma_pagamento !== filterFormaPag) return false;
    
    const hoje = new Date().toISOString().split("T")[0];
    if (filterVencimento === "vencidas" && !["em_aberto", "pendente", "parcial"].includes(c.status) || (filterVencimento === "vencidas" && c.data_vencimento >= hoje)) return false;
    if (filterVencimento === "hoje" && c.data_vencimento !== hoje) return false;
    if (filterVencimento === "a_vencer" && (!["em_aberto", "pendente", "parcial"].includes(c.status) || c.data_vencimento <= hoje)) return false;
    
    return true;
  });

  // Totais
  const totalEmAberto = filteredContas.filter(c => c.status === "em_aberto" || c.status === "pendente" || c.status === "parcial").reduce((s, c) => s + (c.saldo_restante || c.valor_final || c.valor || 0), 0);
  const totalVencidas = filteredContas.filter(c => (c.status === "em_aberto" || c.status === "pendente" || c.status === "parcial") && c.data_vencimento < new Date().toISOString().split("T")[0]).reduce((s, c) => s + (c.saldo_restante || c.valor_final || c.valor || 0), 0);
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
          <Input placeholder="Buscar por descrição, fornecedor, NF, nº doc..." value={search} onChange={(e) => setSearch(e.target.value)} className="pl-10" data-testid="contas-pagar-search" />
        </div>
        <Select value={filterStatus} onValueChange={setFilterStatus}>
          <SelectTrigger className="h-11"><SelectValue placeholder="Todos Status" /></SelectTrigger>
          <SelectContent className="z-[9999]">
            <SelectItem value="all">Todos Status</SelectItem>
            <SelectItem value="em_aberto">Em Aberto</SelectItem>
            <SelectItem value="parcial">Parcialmente Pagas</SelectItem>
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
        <Input
          type="number"
          step="0.01"
          placeholder="Buscar por valor"
          value={valorBusca}
          onChange={(e) => setValorBusca(e.target.value)}
          className="h-11"
          data-testid="contas-pagar-busca-valor"
        />
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
                    <td className="p-3 max-w-[200px]">
                      <div className="truncate">{c.descricao}</div>
                      {c.total_parcelas > 1 && (
                        <span className="text-xs text-blue-600 font-medium">
                          Parcela {c.numero_parcela}/{c.total_parcelas}
                        </span>
                      )}
                    </td>
                    <td className="p-3">{c.documento || "-"}</td>
                    <td className="p-3">{c.data_emissao ? new Date(c.data_emissao).toLocaleDateString('pt-BR') : "-"}</td>
                    <td className="p-3">{new Date(c.data_vencimento).toLocaleDateString('pt-BR')}</td>
                    <td className="p-3 text-right font-medium text-red-600">{formatCurrency(c.valor_final || c.valor)}</td>
                    <td className="p-3 text-xs">{formasPagamentoDB.find(f => f.nome?.toLowerCase() === c.forma_pagamento?.toLowerCase())?.nome || formasPagamento.find(f => f.value === c.forma_pagamento)?.label || c.forma_pagamento}</td>
                    <td className="p-3"><span className={`px-2 py-1 rounded text-xs ${status.color}`}><StatusIcon className="inline mr-1" size={12} />{status.label}</span></td>
                    <td className="p-3 text-center" onClick={(e) => e.stopPropagation()}>
                      <div className="flex justify-center gap-1">
                        {(c.status === "em_aberto" || c.status === "pendente" || c.status === "parcial") && <Button size="sm" variant="outline" className="text-green-600" onClick={() => openQuitarModal(c)} title={c.status === "parcial" ? "Registrar Pagamento" : "Quitar"} data-testid={`quitar-btn-${c.id}`}><CheckCircle2 size={14} /></Button>}
                        {(c.pagamentos && c.pagamentos.length > 0) && <Button size="sm" variant="outline" className="text-blue-600" onClick={() => { setQuitarContaInfo(c); setShowHistoricoPagamentos(true); }} title="Ver Histórico"><History size={14} /></Button>}
                        <Button size="sm" variant="outline" onClick={() => openModal(c)}><Edit size={14} /></Button>
                        {(c.status === "em_aberto" || c.status === "pendente") && <Button size="sm" variant="outline" className="text-[#E31A1A]" onClick={() => handleCancelar(c.id)} title="Cancelar"><X size={14} /></Button>}
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
                <div className="flex gap-2">
                  <Select 
                    value={formData.fornecedor_nome || "none"} 
                    onValueChange={(value) => setFormData({...formData, fornecedor_nome: value === "none" ? "" : value})}
                  >
                    <SelectTrigger className="w-full h-11">
                      <SelectValue placeholder="Selecione um fornecedor..." />
                    </SelectTrigger>
                    <SelectContent className="z-[9999]">
                      <SelectItem value="none">Selecione...</SelectItem>
                      {cadastros.map(c => (
                        <SelectItem key={c.id} value={c.nome_razao || c.nome || c.razao_social}>
                          {c.nome_razao || c.nome || c.razao_social} {c.cnpj_cpf ? `(${c.cnpj_cpf})` : ''}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Button 
                    type="button" 
                    variant="outline" 
                    className="h-11 px-3 shrink-0"
                    onClick={() => setShowNovoCadastro(true)}
                    title="Cadastrar novo fornecedor"
                  >
                    <UserPlus size={18} />
                  </Button>
                </div>
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
              <div><label className="form-label">Nº Doc.</label><Input value={formData.numero_doc} onChange={(e) => setFormData({...formData, numero_doc: e.target.value})} data-testid="input-numero-doc-cp" /></div>
              <div><label className="form-label">Conta Movimento</label><Input value={formData.conta_movimento} onChange={(e) => setFormData({...formData, conta_movimento: e.target.value})} /></div>
            </div>
            {/* Nº da Parcela e Total de Parcelas — editável também após lançado */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="form-label">Nº da Parcela <span className="text-gray-400 text-xs font-normal">(opcional)</span></label>
                <Input
                  type="number"
                  min="1"
                  value={formData.numero_parcela}
                  onChange={(e) => setFormData({...formData, numero_parcela: e.target.value})}
                  placeholder="Ex: 3"
                  data-testid="input-numero-parcela-cp"
                />
              </div>
              <div>
                <label className="form-label">Total de Parcelas <span className="text-gray-400 text-xs font-normal">(opcional)</span></label>
                <Input
                  type="number"
                  min="1"
                  value={formData.total_parcelas}
                  onChange={(e) => setFormData({...formData, total_parcelas: e.target.value})}
                  placeholder="Ex: 12"
                  data-testid="input-total-parcelas-cp"
                />
              </div>
            </div>
            <div>
              <label className="form-label">Descrição *</label>
              <Input value={formData.descricao} onChange={(e) => setFormData({...formData, descricao: e.target.value})} required />
            </div>
            <div className="grid grid-cols-4 gap-4">
              <div><label className="form-label">Valor *</label><Input value={formData.valor} onChange={(e) => setFormData({...formData, valor: formatCurrencyInput(e.target.value)})} placeholder="R$ 0,00" required /></div>
              <div><label className="form-label">Desconto</label><Input value={formData.valor_desconto} onChange={(e) => setFormData({...formData, valor_desconto: formatCurrencyInput(e.target.value)})} placeholder="R$ 0,00" /></div>
              <div><label className="form-label">Juros</label><Input value={formData.valor_juros} onChange={(e) => setFormData({...formData, valor_juros: formatCurrencyInput(e.target.value)})} placeholder="R$ 0,00" /></div>
              <div><label className="form-label">Multa</label><Input value={formData.valor_multa} onChange={(e) => setFormData({...formData, valor_multa: formatCurrencyInput(e.target.value)})} placeholder="R$ 0,00" /></div>
            </div>
            {/* Valor Final Calculado */}
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-3 flex items-center justify-between">
              <span className="text-sm text-gray-600">Valor Final (Valor - Desconto + Juros + Multa):</span>
              <span className="text-lg font-semibold text-gray-900">{formatCurrency(calcularValorFinal())}</span>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div><label className="form-label">Data Emissão</label><MaskedDateInput value={formData.data_emissao} onChange={(v) => setFormData({...formData, data_emissao: v})} /></div>
              <div><label className="form-label">{isParcelado ? "Data 1º Vencimento *" : "Data Vencimento *"}</label><MaskedDateInput value={formData.data_vencimento} onChange={(v) => setFormData({...formData, data_vencimento: v})} required /></div>
            </div>
            
            {/* Seção de Parcelamento - apenas para novas contas */}
            {!editingConta && (
              <div className="border-2 border-blue-300 rounded-lg p-4 bg-gradient-to-r from-blue-50 to-blue-100">
                <div className="flex items-center gap-3 mb-3">
                  <input
                    type="checkbox"
                    id="isParcelado"
                    checked={isParcelado}
                    onChange={(e) => {
                      setIsParcelado(e.target.checked);
                      if (!e.target.checked) {
                        setTotalParcelas("1");
                        setIntervaloDias("30");
                      }
                    }}
                    className="h-5 w-5 rounded border-gray-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
                  />
                  <label htmlFor="isParcelado" className="text-sm font-semibold text-blue-700 cursor-pointer">
                    📋 Parcelar esta conta em múltiplas vezes
                  </label>
                </div>
                
                {isParcelado && (
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="form-label">Número de Parcelas *</label>
                      <Input
                        type="number"
                        min="2"
                        max="360"
                        value={totalParcelas}
                        onChange={(e) => setTotalParcelas(e.target.value)}
                        placeholder="Ex: 12"
                        className="h-11"
                        data-testid="input-total-parcelas"
                      />
                      <p className="text-xs text-gray-500 mt-1">Mínimo 2, máximo 360 parcelas</p>
                    </div>
                    <div>
                      <label className="form-label">Intervalo entre Parcelas</label>
                      <Select value={intervaloDias} onValueChange={setIntervaloDias}>
                        <SelectTrigger className="w-full h-11">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent className="z-[9999]">
                          <SelectItem value="7">7 dias</SelectItem>
                          <SelectItem value="14">14 dias</SelectItem>
                          <SelectItem value="15">15 dias</SelectItem>
                          <SelectItem value="21">21 dias</SelectItem>
                          <SelectItem value="28">28 dias</SelectItem>
                          <SelectItem value="30">30 dias (mensal)</SelectItem>
                          <SelectItem value="45">45 dias</SelectItem>
                          <SelectItem value="60">60 dias</SelectItem>
                          <SelectItem value="90">90 dias</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                )}
                
                {isParcelado && parseInt(totalParcelas) > 1 && formData.valor && (
                  <div className="mt-3 p-3 bg-white rounded border border-blue-200">
                    <p className="text-sm text-gray-600">
                      <strong>Resumo:</strong> {totalParcelas}x de{" "}
                      <span className="font-semibold text-blue-600">
                        {formatCurrency((parseCurrency(formData.valor) || 0) / parseInt(totalParcelas))}
                      </span>
                      {" "}(Total: {formatCurrency(parseCurrency(formData.valor) || 0)})
                    </p>
                  </div>
                )}
              </div>
            )}
            
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
              <div>
                <label className="form-label">Frota (Opcional)</label>
                <Select value={formData.frota_id || "none"} onValueChange={(value) => {
                  if (value === "none") {
                    setFormData({...formData, frota_id: "", frota_nome: ""});
                  } else {
                    const frota = frotas.find(f => f.id === value);
                    setFormData({...formData, frota_id: value, frota_nome: frota?.name || ""});
                  }
                }}>
                  <SelectTrigger className="w-full h-11"><SelectValue placeholder="Selecione uma frota..." /></SelectTrigger>
                  <SelectContent className="z-[9999]">
                    <SelectItem value="none">Nenhuma</SelectItem>
                    {frotas.map(f => <SelectItem key={f.id} value={f.id}>{f.name}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="form-label">Conta Bancária</label>
                <Select value={formData.conta_bancaria_id || "none"} onValueChange={(value) => {
                  if (value === "none") {
                    setFormData({...formData, conta_bancaria_id: "", conta_bancaria_nome: ""});
                  } else {
                    const conta = contasBancarias.find(c => c.id === value);
                    setFormData({...formData, conta_bancaria_id: value, conta_bancaria_nome: conta?.nome || ""});
                  }
                }}>
                  <SelectTrigger className="w-full h-11"><SelectValue placeholder="Selecione uma conta..." /></SelectTrigger>
                  <SelectContent className="z-[9999]">
                    <SelectItem value="none">Nenhuma</SelectItem>
                    {contasBancarias.map(c => <SelectItem key={c.id} value={c.id}>{c.nome} - {c.banco}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div>
              <label className="form-label">Observações</label>
              <Input value={formData.observacoes} onChange={(e) => setFormData({...formData, observacoes: e.target.value})} />
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

      {/* Modal Cadastro Completo de Fornecedor */}
      <CadastroFormModal
        open={showNovoCadastro}
        onOpenChange={setShowNovoCadastro}
        defaultTipo="fornecedor"
        onSuccess={handleNovoCadastroSuccess}
      />

      {/* Modal de Quitação com Opção Parcial */}
      <Dialog open={showQuitarModal} onOpenChange={setShowQuitarModal}>
        <DialogContent className="sm:max-w-[480px]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-green-600">
              <CheckCircle2 size={20} />
              Registrar Pagamento
            </DialogTitle>
          </DialogHeader>
          {quitarContaInfo && (
            <div className="space-y-4">
              {/* Info da Conta */}
              <div className="bg-gray-50 p-3 rounded-lg space-y-2">
                <div className="flex justify-between">
                  <span className="text-gray-500">Fornecedor:</span>
                  <span className="font-medium">{quitarContaInfo.fornecedor_nome || "-"}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Descrição:</span>
                  <span className="font-medium truncate max-w-[200px]">{quitarContaInfo.descricao}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Valor Total:</span>
                  <span className="font-bold text-gray-700">{formatCurrency(quitarContaInfo.valor_final || quitarContaInfo.valor)}</span>
                </div>
                {(quitarContaInfo.valor_pago > 0) && (
                  <>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Já Pago:</span>
                      <span className="font-medium text-green-600">{formatCurrency(quitarContaInfo.valor_pago)}</span>
                    </div>
                    <div className="flex justify-between border-t pt-2">
                      <span className="text-gray-500 font-medium">Saldo Restante:</span>
                      <span className="font-bold text-red-600">{formatCurrency((quitarContaInfo.valor_final || quitarContaInfo.valor) - quitarContaInfo.valor_pago)}</span>
                    </div>
                  </>
                )}
                <div className="flex justify-between">
                  <span className="text-gray-500">Vencimento:</span>
                  <span className="font-medium">{new Date(quitarContaInfo.data_vencimento).toLocaleDateString('pt-BR')}</span>
                </div>
              </div>
              
              {/* Tipo de Pagamento */}
              <div className="space-y-2">
                <label className="text-sm font-medium flex items-center gap-2">
                  <DollarSign size={16} className="text-green-600" />
                  Tipo de Pagamento
                </label>
                <div className="flex gap-2">
                  <Button 
                    type="button"
                    variant={tipoPagamento === "total" ? "default" : "outline"}
                    className={tipoPagamento === "total" ? "flex-1 bg-green-600 hover:bg-green-700" : "flex-1"}
                    onClick={() => {
                      setTipoPagamento("total");
                      const saldo = (quitarContaInfo.valor_final || quitarContaInfo.valor) - (quitarContaInfo.valor_pago || 0);
                      setValorPagamento(formatCurrencyInput(saldo.toFixed(2)));
                    }}
                  >
                    Quitar Total
                  </Button>
                  <Button 
                    type="button"
                    variant={tipoPagamento === "parcial" ? "default" : "outline"}
                    className={tipoPagamento === "parcial" ? "flex-1 bg-yellow-600 hover:bg-yellow-700" : "flex-1"}
                    onClick={() => setTipoPagamento("parcial")}
                  >
                    Pagamento Parcial
                  </Button>
                </div>
              </div>

              {/* Valor do Pagamento (só mostra se for parcial) */}
              {tipoPagamento === "parcial" && (
                <div className="space-y-2">
                  <label className="text-sm font-medium flex items-center gap-2">
                    <DollarSign size={16} className="text-yellow-600" />
                    Valor do Pagamento *
                  </label>
                  <Input
                    value={valorPagamento}
                    onChange={(e) => setValorPagamento(formatCurrencyInput(e.target.value))}
                    placeholder="R$ 0,00"
                    className="text-lg font-semibold"
                  />
                  <p className="text-xs text-gray-500">
                    Saldo restante: {formatCurrency((quitarContaInfo.valor_final || quitarContaInfo.valor) - (quitarContaInfo.valor_pago || 0))}
                  </p>
                </div>
              )}
              
              <div className="space-y-2">
                <label className="text-sm font-medium flex items-center gap-2">
                  <Calendar size={16} className="text-green-600" />
                  Data do Pagamento *
                </label>
                <MaskedDateInput
                  value={dataPagamento}
                  onChange={(v) => setDataPagamento(v)}
                  className="w-full"
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium flex items-center gap-2">
                  <Landmark size={16} className="text-green-600" />
                  Conta Bancária (Saída) *
                </label>
                <Select value={quitarContaBancaria} onValueChange={setQuitarContaBancaria}>
                  <SelectTrigger>
                    <SelectValue placeholder="Selecione a conta bancária..." />
                  </SelectTrigger>
                  <SelectContent>
                    {contasBancarias.map(c => (
                      <SelectItem key={c.id} value={c.id}>
                        {c.nome} - {c.banco}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Observação */}
              <div className="space-y-2">
                <label className="text-sm font-medium">Observação (opcional)</label>
                <Textarea
                  value={observacaoPagamento}
                  onChange={(e) => setObservacaoPagamento(e.target.value)}
                  placeholder="Ex: Pagamento referente a parcela 1/3"
                  rows={2}
                />
              </div>

              {/* Juros / Multa / Desconto (todos opcionais) */}
              <div className="space-y-2 border-t pt-3">
                <p className="text-xs uppercase font-semibold text-gray-500 tracking-wide">
                  Ajustes (opcionais)
                </p>
                <div className="grid grid-cols-3 gap-3">
                  <div className="space-y-1">
                    <label className="text-xs font-medium text-orange-700 flex items-center gap-1">
                      <TrendingUp size={12} /> Juros
                    </label>
                    <Input
                      value={valorJuros}
                      onChange={(e) => setValorJuros(formatCurrencyInput(e.target.value))}
                      placeholder="R$ 0,00"
                      className="text-sm"
                      data-testid="input-juros-pagamento"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs font-medium text-red-700 flex items-center gap-1">
                      <AlertCircle size={12} /> Multa
                    </label>
                    <Input
                      value={valorMulta}
                      onChange={(e) => setValorMulta(formatCurrencyInput(e.target.value))}
                      placeholder="R$ 0,00"
                      className="text-sm"
                      data-testid="input-multa-pagamento"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs font-medium text-green-700 flex items-center gap-1">
                      <TrendingDown size={12} /> Desconto
                    </label>
                    <Input
                      value={valorDesconto}
                      onChange={(e) => setValorDesconto(formatCurrencyInput(e.target.value))}
                      placeholder="R$ 0,00"
                      className="text-sm"
                      data-testid="input-desconto-pagamento"
                    />
                  </div>
                </div>
                {(parseCurrency(valorJuros) + parseCurrency(valorMulta) + parseCurrency(valorDesconto) > 0) && (() => {
                  const j = parseCurrency(valorJuros) || 0;
                  const m = parseCurrency(valorMulta) || 0;
                  const d = parseCurrency(valorDesconto) || 0;
                  const base = tipoPagamento === "parcial" ? (parseCurrency(valorPagamento) || 0) : (quitarContaInfo.valor_final || quitarContaInfo.valor || 0) - (quitarContaInfo.valor_pago || 0);
                  const liquido = base + j + m - d;
                  return (
                    <div className="bg-blue-50 p-2 rounded text-xs space-y-0.5 mt-1">
                      <div className="flex justify-between"><span>Base:</span><span className="font-mono">{formatCurrency(base)}</span></div>
                      {j > 0 && <div className="flex justify-between text-orange-700"><span>+ Juros:</span><span className="font-mono">{formatCurrency(j)}</span></div>}
                      {m > 0 && <div className="flex justify-between text-red-700"><span>+ Multa:</span><span className="font-mono">{formatCurrency(m)}</span></div>}
                      {d > 0 && <div className="flex justify-between text-green-700"><span>- Desconto:</span><span className="font-mono">{formatCurrency(d)}</span></div>}
                      <div className="flex justify-between border-t pt-1 font-bold"><span>Valor Líquido:</span><span className="font-mono">{formatCurrency(liquido)}</span></div>
                    </div>
                  );
                })()}
              </div>

              <div className="flex gap-3 pt-2">
                <Button type="button" variant="outline" onClick={() => setShowQuitarModal(false)} className="flex-1">
                  Cancelar
                </Button>
                <Button 
                  onClick={handleQuitar} 
                  className={tipoPagamento === "total" ? "flex-1 bg-green-600 hover:bg-green-700" : "flex-1 bg-yellow-600 hover:bg-yellow-700"}
                >
                  <CheckCircle2 size={16} className="mr-2" />
                  {tipoPagamento === "total" ? "Quitar Total" : "Registrar Pagamento"}
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Modal de Histórico de Pagamentos */}
      <Dialog open={showHistoricoPagamentos} onOpenChange={setShowHistoricoPagamentos}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-blue-600">
              <History size={20} />
              Histórico de Pagamentos
            </DialogTitle>
          </DialogHeader>
          {quitarContaInfo && (() => {
            const valorTotal = quitarContaInfo.valor_final || quitarContaInfo.valor || 0;
            const valorPago = quitarContaInfo.valor_pago || 0;
            const saldo = Math.max(0, valorTotal - valorPago);
            const pct = valorTotal > 0 ? Math.min(100, (valorPago / valorTotal) * 100) : 0;
            const nParcelas = (quitarContaInfo.pagamentos || []).length;
            let barColor = "bg-orange-500";
            if (pct >= 100) barColor = "bg-green-500";
            else if (pct >= 75) barColor = "bg-blue-500";
            else if (pct < 25) barColor = "bg-red-500";
            return (
            <div className="space-y-4">
              {/* Cronograma visual */}
              <div className="bg-gradient-to-br from-blue-50 to-purple-50 p-4 rounded-lg space-y-3 border border-blue-100">
                <div>
                  <p className="text-xs text-gray-500 uppercase font-semibold tracking-wide">
                    {quitarContaInfo.descricao}
                  </p>
                </div>
                <div className="space-y-1">
                  <div className="flex justify-between items-baseline">
                    <span className="text-2xl font-bold text-gray-800">{pct.toFixed(0)}%</span>
                    <span className="text-xs text-gray-500">
                      {formatCurrency(valorPago)} de {formatCurrency(valorTotal)}
                    </span>
                  </div>
                  <div className="h-3 bg-gray-200 rounded-full overflow-hidden" data-testid="progress-pagamento">
                    <div
                      className={`h-full ${barColor} transition-all duration-700 ease-out rounded-full relative`}
                      style={{ width: `${pct}%` }}
                    >
                      {pct > 10 && (
                        <div className="absolute inset-0 bg-white/20 animate-pulse" />
                      )}
                    </div>
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-2 pt-1 text-center">
                  <div>
                    <p className="text-[10px] uppercase text-gray-500 tracking-wide">Parcelas</p>
                    <p className="text-sm font-bold text-blue-700">{nParcelas}</p>
                  </div>
                  <div>
                    <p className="text-[10px] uppercase text-gray-500 tracking-wide">Pago</p>
                    <p className="text-sm font-bold text-green-600">{formatCurrency(valorPago)}</p>
                  </div>
                  <div>
                    <p className="text-[10px] uppercase text-gray-500 tracking-wide">Saldo</p>
                    <p className={`text-sm font-bold ${saldo < 0.01 ? "text-green-600" : "text-red-600"}`}>
                      {formatCurrency(saldo)}
                    </p>
                  </div>
                </div>
                {saldo < 0.01 && (
                  <div className="bg-green-100 text-green-800 text-xs text-center py-1.5 rounded font-medium">
                    ✓ Conta quitada!
                  </div>
                )}
              </div>

              {/* Lista de Pagamentos */}
              <div className="space-y-2">
                <h4 className="font-medium text-sm">Pagamentos Realizados</h4>
                {quitarContaInfo.pagamentos && quitarContaInfo.pagamentos.length > 0 ? (
                  <div className="space-y-2 max-h-[300px] overflow-y-auto">
                    {quitarContaInfo.pagamentos.map((p, idx) => (
                      <div key={p.id || idx} className="bg-white border rounded-lg p-3 space-y-1">
                        <div className="flex justify-between items-center gap-2">
                          <span className="text-sm text-gray-500">
                            {new Date(p.data).toLocaleDateString('pt-BR')}
                          </span>
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-green-600">{formatCurrency(p.valor)}</span>
                            {p.id && (
                              <Button
                                size="sm"
                                variant="outline"
                                className="h-7 px-2 text-xs text-blue-600 hover:bg-blue-50"
                                title="Baixar recibo deste pagamento parcial"
                                data-testid={`btn-recibo-parcial-${p.id}`}
                                onClick={async () => {
                                  try {
                                    const resp = await axios.get(
                                      `${API}/export/recibo/contas_pagar/${quitarContaInfo.id}?pagamento_id=${p.id}`,
                                      { responseType: 'blob' }
                                    );
                                    const url = window.URL.createObjectURL(new Blob([resp.data], { type: 'application/pdf' }));
                                    const link = document.createElement('a');
                                    link.href = url;
                                    link.setAttribute('download', `Recibo_Parcial_${p.id.substring(0,8)}.pdf`);
                                    document.body.appendChild(link);
                                    link.click();
                                    link.remove();
                                    window.URL.revokeObjectURL(url);
                                    toast.success("Recibo baixado");
                                  } catch (err) {
                                    toast.error("Erro ao baixar recibo");
                                  }
                                }}
                              >
                                <FileDown size={12} className="mr-1" /> Recibo
                              </Button>
                            )}
                          </div>
                        </div>
                        {p.observacao && (
                          <p className="text-xs text-gray-500">{p.observacao}</p>
                        )}
                        <p className="text-xs text-gray-400">
                          Por: {p.created_by} em {new Date(p.created_at).toLocaleString('pt-BR')}
                        </p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-gray-500 text-center py-4">Nenhum pagamento registrado</p>
                )}
              </div>

              <Button 
                type="button" 
                variant="outline" 
                onClick={() => setShowHistoricoPagamentos(false)} 
                className="w-full"
              >
                Fechar
              </Button>
            </div>
            );
          })()}
        </DialogContent>
      </Dialog>
    </div>
  );
}
