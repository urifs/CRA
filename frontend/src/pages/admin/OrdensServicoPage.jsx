import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "@/App";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { MaskedDateInput } from "@/components/MaskedDateInput";
import CadastroFormModal from "@/components/CadastroFormModal";
import { formatCEP, formatTelefone, formatCPFouCNPJ } from "@/utils/masks";
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
  Minus,
  FileDown,
  UserPlus,
  Loader2
} from "lucide-react";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

export default function OrdensServicoPage() {
  const [ordens, setOrdens] = useState([]);
  const [centrosCusto, setCentrosCusto] = useState([]);
  const [machines, setMachines] = useState([]);
  const [fornecedores, setFornecedores] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("todas");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingOrdem, setEditingOrdem] = useState(null);
  const [formData, setFormData] = useState({
    numero_contrato: "",
    cliente_nome: "",
    cliente_fantasia: "",
    cliente_documento: "",
    cliente_email: "",
    cliente_telefone: "",
    cliente_celular: "",
    cliente_ie: "",
    cliente_endereco: "",
    cliente_bairro: "",
    cliente_cidade: "",
    cliente_uf: "",
    cliente_cep: "",
    endereco_entrega: "",
    obra: "",
    descricao: "",
    tipo_atendimento: "",
    periodo: "",
    numero_documento_fiscal: "",
    data_abertura: new Date().toISOString().split("T")[0],
    data_fechamento: "",
    data_previsao_entrega: "",
    valor_total: "",
    valor_desconto: "",
    valor_antecipado: "",
    forma_pagamento: "",
    condicao_pagamento: "",
    observacao_servicos: "",
    notas_gerais: "",
    atendente_nome: "",
    empresa_emissora: "locadora",
    tipo_financeiro: "nenhum",
    frotas_ids: [],
    maquinas_ids: [],
    fornecedores_ids: [],
    observacoes: "",
    periodicidade: "",
    km: "",
    valores_extras: []
  });
  const [cadastros, setCadastros] = useState([]);
  const [showNovoCadastro, setShowNovoCadastro] = useState(false);
  const [showNovoFornecedor, setShowNovoFornecedor] = useState(false);
  const [consultandoCep, setConsultandoCep] = useState(false);

  const handleExportPdf = async (ordem) => {
    try {
      const r = await axios.get(`${API}/admin/ordens-servico/${ordem.id}/export-pdf`, {
        responseType: 'blob'
      });
      const url = window.URL.createObjectURL(new Blob([r.data], { type: 'application/pdf' }));
      const a = document.createElement('a');
      a.href = url;
      a.setAttribute('download', `OS_${ordem.numero || ordem.id.substring(0,8)}.pdf`);
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      toast.success("OS exportada");
    } catch (err) {
      toast.error("Erro ao exportar OS");
    }
  };

  useEffect(() => {
    fetchOrdens();
    fetchCentrosCusto();
    fetchMachines();
    fetchFornecedores();
    fetchCadastros();
  }, []);

  const fetchCadastros = async () => {
    try {
      // Carrega clientes (e cli_forn) para o dropdown de Cliente da OS
      const response = await axios.get(`${API}/admin/cadastros`);
      const lista = (response.data || []).filter(
        (c) => c.tipo_cadastro === "cliente" || c.tipo_cadastro === "cli_forn"
      );
      setCadastros(lista);
    } catch (error) {
      console.error("Erro ao carregar cadastros:", error);
    }
  };

  // Auto-preenche todos os campos do cliente a partir do cadastro selecionado
  const handleSelectCliente = (clienteId) => {
    if (!clienteId || clienteId === "none") {
      setFormData((prev) => ({
        ...prev,
        cliente_id: "",
        cliente_nome: "",
        cliente_fantasia: "",
        cliente_documento: "",
        cliente_ie: "",
        cliente_email: "",
        cliente_telefone: "",
        cliente_celular: "",
        cliente_endereco: "",
        cliente_bairro: "",
        cliente_cidade: "",
        cliente_uf: "",
        cliente_cep: ""
      }));
      return;
    }
    const c = cadastros.find((x) => x.id === clienteId);
    if (!c) return;
    const enderecoCompleto = [c.endereco, c.numero, c.complemento]
      .filter(Boolean)
      .join(", ");
    setFormData((prev) => ({
      ...prev,
      cliente_id: c.id,
      cliente_nome: c.nome_razao || prev.cliente_nome || "",
      cliente_fantasia: c.apelido_fantasia || "",
      cliente_documento: c.cpf_cnpj || "",
      cliente_ie: c.rg_ie || "",
      cliente_email: c.email || "",
      cliente_telefone: c.telefone || "",
      cliente_celular: c.celular || "",
      cliente_endereco: enderecoCompleto || c.endereco || "",
      cliente_bairro: c.bairro || "",
      cliente_cidade: c.cidade || "",
      cliente_uf: c.uf || "",
      cliente_cep: c.cep || ""
    }));
  };

  const handleNovoCadastroSuccess = (novoCadastro) => {
    // Adiciona o novo cadastro à lista e seleciona automaticamente
    setCadastros((prev) => [...prev, novoCadastro]);
    handleSelectCliente(novoCadastro.id);
    fetchCadastros();
  };

  const handleNovoFornecedorSuccess = (novoFornecedor) => {
    // Recarrega lista de fornecedores e marca o novo como selecionado
    fetchFornecedores();
    setFormData((prev) => ({
      ...prev,
      fornecedores_ids: [...(prev.fornecedores_ids || []), novoFornecedor.id],
    }));
    toast.success(`Fornecedor "${novoFornecedor.nome_razao}" vinculado à OS`);
  };

  // Calcula data de entrega/fechamento a partir da data de abertura + periodicidade
  const PERIODICIDADE_DIAS = {
    diaria: 1,
    semanal: 7,
    quinzenal: 15,
    mensal: 30,
    semestral: 180,
    anual: 365,
  };

  const calcularDataEntrega = (dataAberturaIso, periodicidade) => {
    if (!dataAberturaIso || !periodicidade) return "";
    const dias = PERIODICIDADE_DIAS[periodicidade];
    if (!dias) return "";
    const d = new Date(`${dataAberturaIso}T00:00:00`);
    if (Number.isNaN(d.getTime())) return "";
    d.setDate(d.getDate() + dias);
    return d.toISOString().split("T")[0];
  };

  const handlePeriodicidadeChange = (periodicidade) => {
    const novaPrevisao = calcularDataEntrega(formData.data_abertura, periodicidade);
    setFormData((prev) => ({
      ...prev,
      periodicidade,
      data_previsao_entrega: novaPrevisao || prev.data_previsao_entrega,
    }));
  };

  const handleDataAberturaChange = (novaData) => {
    setFormData((prev) => {
      const novaPrevisao = prev.periodicidade
        ? calcularDataEntrega(novaData, prev.periodicidade)
        : prev.data_previsao_entrega;
      return {
        ...prev,
        data_abertura: novaData,
        data_previsao_entrega: novaPrevisao || prev.data_previsao_entrega,
      };
    });
  };

  // Consulta endereço a partir do CEP via ViaCEP
  const handleConsultaCep = async (cepValue) => {
    const cep = (cepValue || formData.cliente_cep || "").replace(/\D/g, "");
    if (cep.length !== 8) return;
    setConsultandoCep(true);
    try {
      const response = await axios.get(`https://viacep.com.br/ws/${cep}/json/`);
      if (response.data.erro) {
        toast.error("CEP não encontrado");
        return;
      }
      setFormData((prev) => ({
        ...prev,
        cliente_endereco: response.data.logradouro || prev.cliente_endereco,
        cliente_bairro: response.data.bairro || prev.cliente_bairro,
        cliente_cidade: response.data.localidade || prev.cliente_cidade,
        cliente_uf: response.data.uf || prev.cliente_uf
      }));
      toast.success("Endereço preenchido!");
    } catch (error) {
      toast.error("Erro ao consultar CEP");
    } finally {
      setConsultandoCep(false);
    }
  };

  const fetchCentrosCusto = async () => {
    try {
      const response = await axios.get(`${API}/admin/centros-custo`);
      // Apenas centros ativos. Se algum tem flag eh_empresa_emissora, filtra só esses;
      // caso contrário, mostra todos (retrocompatibilidade).
      const ativos = (response.data || []).filter(c => c.status === "ativo");
      const emissoras = ativos.filter(c => c.eh_empresa_emissora);
      setCentrosCusto(emissoras.length > 0 ? emissoras : ativos);
    } catch (error) {
      console.error("Erro ao carregar centros de custo:", error);
    }
  };

  const fetchMachines = async () => {
    try {
      const response = await axios.get(`${API}/machines`);
      setMachines(response.data || []);
    } catch (error) {
      console.error("Erro ao carregar máquinas:", error);
    }
  };

  const fetchFornecedores = async () => {
    try {
      const response = await axios.get(`${API}/admin/cadastros?tipo=fornecedor`);
      setFornecedores(response.data || []);
    } catch (error) {
      console.error("Erro ao carregar fornecedores:", error);
    }
  };

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
      // Soma valor principal + extras - desconto = valor final automático
      const valorPrincipal = parseFloat(formData.valor_total) || 0;
      const valorDesconto = parseFloat(formData.valor_desconto) || 0;
      const valorAntecipado = parseFloat(formData.valor_antecipado) || 0;
      const extras = (formData.valores_extras || [])
        .map((v) => ({ descricao: v.descricao || "", valor: parseFloat(v.valor) || 0 }));
      const totalExtras = extras.reduce((s, v) => s + v.valor, 0);
      const valorFinal = valorPrincipal + totalExtras - valorDesconto;

      const dataToSend = {
        ...formData,
        valor_total: valorFinal,
        valor_principal: valorPrincipal,
        valor_desconto: valorDesconto,
        valor_antecipado: valorAntecipado,
        valores_extras: extras,
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
      // Backend pode retornar `detail` como array de validação Pydantic.
      // Converter para string para evitar crash do React ao renderizar no toast.
      let msg = "Erro ao salvar ordem";
      const detail = error.response?.data?.detail;
      if (typeof detail === "string") {
        msg = detail;
      } else if (Array.isArray(detail)) {
        msg = detail
          .map((d) => `${(d.loc || []).slice(-1)[0] || "campo"}: ${d.msg || d.message || ""}`)
          .join("; ");
      } else if (detail) {
        msg = JSON.stringify(detail);
      }
      toast.error(msg);
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
    const baseEmpty = {
      numero_contrato: "",
      cliente_nome: "", cliente_fantasia: "", cliente_documento: "",
      cliente_email: "", cliente_telefone: "", cliente_celular: "",
      cliente_ie: "", cliente_endereco: "", cliente_bairro: "",
      cliente_cidade: "", cliente_uf: "", cliente_cep: "",
      endereco_entrega: "", obra: "",
      tipo_atendimento: "", periodo: "",
      numero_documento_fiscal: "",
      descricao: "",
      data_abertura: new Date().toISOString().split("T")[0],
      data_fechamento: "", data_previsao_entrega: "",
      valor_total: "", valor_desconto: "", valor_antecipado: "",
      forma_pagamento: "", condicao_pagamento: "",
      observacao_servicos: "", notas_gerais: "",
      atendente_nome: "", empresa_emissora: "locadora",
      tipo_financeiro: "nenhum", observacoes: "",
      frotas_ids: [], maquinas_ids: [], fornecedores_ids: [],
      cliente_id: "",
      periodicidade: "",
      km: "",
      valores_extras: [],
    };
    if (ordem) {
      setEditingOrdem(ordem);
      setFormData({
        ...baseEmpty,
        ...Object.fromEntries(
          Object.keys(baseEmpty).map((k) => {
            const v = ordem[k];
            if (v == null) return [k, baseEmpty[k]];
            if (k.startsWith("data_")) return [k, String(v).split("T")[0]];
            if (k.startsWith("valor_") && k !== "valores_extras") return [k, String(v)];
            if (k === "valores_extras") return [k, Array.isArray(v) ? v : []];
            if (k.endsWith("_ids")) return [k, Array.isArray(v) ? v : []];
            return [k, v];
          })
        ),
      });
    } else {
      setEditingOrdem(null);
      setFormData(baseEmpty);
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
        return { label: "Aberta", color: "bg-blue-100 text-[#D4A000]", icon: Clock };
      case "em_andamento":
        return { label: "Em Andamento", color: "bg-orange-100 text-[#E31A1A]", icon: AlertCircle };
      case "concluida":
        return { label: "Concluída", color: "bg-green-100 text-green-700", icon: CheckCircle2 };
      case "cancelada":
        return { label: "Cancelada", color: "bg-red-100 text-red-700", icon: AlertCircle };
      default:
        return { label: "Aberta", color: "bg-blue-100 text-[#D4A000]", icon: Clock };
    }
  };

  const getTipoFinanceiroInfo = (tipo) => {
    switch (tipo) {
      case "a_pagar":
        return { label: "A Pagar", color: "bg-red-50 text-red-600", icon: TrendingDown };
      case "a_receber":
        return { label: "A Receber", color: "bg-green-50 text-green-600", icon: TrendingUp };
      default:
        return { label: "-", color: "bg-white text-gray-400", icon: Minus };
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
          <p className="text-gray-500 mt-1">Gerenciamento de OS</p>
        </div>
        <Button onClick={() => openModal()} className="bg-[#D4A000] hover:bg-[#D4A000]" data-testid="new-os-btn">
          <Plus size={18} className="mr-2" />
          Nova OS
        </Button>
      </div>

      {/* Resumo */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <Card className="stat-card">
          <CardContent className="p-4 flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
              <ClipboardList className="text-[#D4A000]" size={20} />
            </div>
            <div>
              <p className="text-xs text-gray-500">Total OS</p>
              <p className="text-lg font-bold text-[#D4A000]">{totalOS}</p>
            </div>
          </CardContent>
        </Card>
        <Card className="stat-card">
          <CardContent className="p-4 flex items-center gap-3">
            <div className="w-10 h-10 bg-red-100 rounded-lg flex items-center justify-center">
              <TrendingDown className="text-red-600" size={20} />
            </div>
            <div>
              <p className="text-xs text-gray-500">Total A Pagar</p>
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
              <p className="text-xs text-gray-500">Total A Receber</p>
              <p className="text-lg font-bold text-green-600">{formatCurrency(totalAReceber)}</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <div className="flex flex-col md:flex-row gap-4 mb-6">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
          <Input
            placeholder="Buscar por número, cliente, obra ou descrição..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-10"
            data-testid="search-os"
          />
        </div>
        <Button className="bg-[#D4A000] hover:bg-[#b38900] text-black shrink-0">
          <Search size={16} className="mr-2" />
          Buscar
        </Button>
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
              className={filter === f.value ? "bg-[#D4A000]" : ""}
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
          <CardContent className="py-12 text-center text-gray-400">
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
              <Card 
                key={ordem.id} 
                className="hover:shadow-md transition-shadow cursor-pointer" 
                data-testid={`os-${ordem.id}`}
                onClick={() => openModal(ordem)}
              >
                <CardContent className="p-4">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1 flex-wrap">
                        <span className="font-bold text-[#D4A000]">OS-{ordem.numero}</span>
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
                      <h3 className="font-medium text-black truncate">{ordem.descricao || "Sem descrição"}</h3>
                      {(ordem.cliente_nome || ordem.cliente_fantasia) && (
                        <p className="text-sm text-gray-500 flex items-center gap-1">
                          <User size={14} />
                          {ordem.cliente_fantasia || ordem.cliente_nome}
                        </p>
                      )}
                      {ordem.obra && (
                        <p className="text-sm text-gray-500">Obra: {ordem.obra}</p>
                      )}
                      <p className="text-sm text-gray-500 flex items-center gap-1">
                        <Calendar size={14} />
                        Abertura: {new Date(ordem.data_abertura).toLocaleDateString('pt-BR')}
                        {ordem.data_previsao_entrega && ` | Previsão: ${new Date(ordem.data_previsao_entrega).toLocaleDateString('pt-BR')}`}
                      </p>
                    </div>
                    <div className="text-right">
                      {ordem.valor_total > 0 && (
                        <p className="text-lg font-bold text-black">{formatCurrency(ordem.valor_total)}</p>
                      )}
                      {ordem.valor_restante > 0 && ordem.valor_antecipado > 0 && (
                        <p className="text-xs text-gray-500">Restante: {formatCurrency(ordem.valor_restante)}</p>
                      )}
                      <div className="flex gap-1 mt-2">
                        {ordem.status === "em_aberto" && (
                          <Button
                            size="sm"
                            variant="outline"
                            className="text-[#E31A1A]"
                            onClick={(e) => { e.stopPropagation(); handleUpdateStatus(ordem.id, "em_andamento"); }}
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
                            onClick={(e) => { e.stopPropagation(); handleUpdateStatus(ordem.id, "concluida"); }}
                            title="Concluir"
                          >
                            <CheckCircle2 size={16} />
                          </Button>
                        )}
                        <Button size="sm" variant="outline" onClick={(e) => { e.stopPropagation(); handleExportPdf(ordem); }} title="Exportar PDF" data-testid={`btn-export-os-${ordem.id}`}>
                          <FileDown size={16} />
                        </Button>
                        <Button size="sm" variant="outline" onClick={(e) => { e.stopPropagation(); openModal(ordem); }}>
                          <Edit size={16} />
                        </Button>
                        <Button 
                          size="sm" 
                          variant="outline" 
                          className="text-red-600 hover:bg-red-50"
                          onClick={(e) => { e.stopPropagation(); handleDelete(ordem.id); }}
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
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{editingOrdem ? "Editar Ordem de Serviço" : "Nova Ordem de Serviço"}</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Identificação */}
            <div className="grid grid-cols-3 gap-3">
              <div>
                <label className="form-label">Nº Contrato <span className="text-gray-400 text-xs font-normal">(opcional)</span></label>
                <Input
                  value={formData.numero_contrato}
                  onChange={(e) => setFormData({...formData, numero_contrato: e.target.value})}
                  placeholder="CONT-2024-001"
                />
              </div>
              <div>
                <label className="form-label">Nº Doc Fiscal <span className="text-gray-400 text-xs font-normal">(opcional)</span></label>
                <Input
                  value={formData.numero_documento_fiscal}
                  onChange={(e) => setFormData({...formData, numero_documento_fiscal: e.target.value})}
                  placeholder="NF nº"
                />
              </div>
              <div>
                <label className="form-label">Empresa Emissora *</label>
                <Select value={formData.empresa_emissora} onValueChange={(v) => setFormData({...formData, empresa_emissora: v})}>
                  <SelectTrigger className="w-full h-11" data-testid="select-empresa-emissora"><SelectValue placeholder="Selecione" /></SelectTrigger>
                  <SelectContent className="z-[9999]">
                    {centrosCusto.length === 0 && (
                      <>
                        <SelectItem value="locadora">CRA Locações (padrão)</SelectItem>
                        <SelectItem value="construtora">CRA Construções (padrão)</SelectItem>
                      </>
                    )}
                    {centrosCusto.map((c) => (
                      <SelectItem key={c.id} value={c.id}>
                        {c.codigo ? `${c.codigo} — ${c.nome}` : c.nome}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {centrosCusto.length === 0 && (
                  <p className="text-xs text-amber-600 mt-1">
                    💡 Cadastre empresas em Centro de Custo para aparecerem aqui
                  </p>
                )}
              </div>
            </div>

            {/* Cliente */}
            <fieldset className="border rounded p-3">
              <legend className="text-xs font-semibold uppercase px-1">Cliente</legend>
              <div className="grid grid-cols-2 gap-3">
                <div className="col-span-2">
                  <label className="form-label">Cliente (Razão Social)</label>
                  <div className="flex gap-2">
                    <Select 
                      value={formData.cliente_id || "none"} 
                      onValueChange={(v) => handleSelectCliente(v)}
                    >
                      <SelectTrigger className="w-full" data-testid="select-cliente-os">
                        <SelectValue placeholder="Selecione um cliente cadastrado..." />
                      </SelectTrigger>
                      <SelectContent className="z-[9999]">
                        <SelectItem value="none">Selecione...</SelectItem>
                        {cadastros.map((c) => (
                          <SelectItem key={c.id} value={c.id}>
                            {c.nome_razao || c.apelido_fantasia} {c.cpf_cnpj ? `(${c.cpf_cnpj})` : ""}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <Button 
                      type="button" 
                      variant="outline" 
                      className="px-3 shrink-0"
                      onClick={() => setShowNovoCadastro(true)}
                      title="Cadastrar novo cliente"
                      data-testid="btn-novo-cliente-os"
                    >
                      <UserPlus size={18} />
                    </Button>
                  </div>
                  {!formData.cliente_id && (
                    <Input 
                      className="mt-2" 
                      value={formData.cliente_nome} 
                      onChange={(e) => setFormData({...formData, cliente_nome: e.target.value})} 
                      placeholder="Ou digite o nome/razão social manualmente" 
                    />
                  )}
                </div>
                <div>
                  <label className="form-label">Fantasia</label>
                  <Input value={formData.cliente_fantasia} onChange={(e) => setFormData({...formData, cliente_fantasia: e.target.value})} placeholder="Nome fantasia" />
                </div>
                <div>
                  <label className="form-label">CPF/CNPJ</label>
                  <Input 
                    value={formData.cliente_documento} 
                    onChange={(e) => setFormData({...formData, cliente_documento: formatCPFouCNPJ(e.target.value)})} 
                    placeholder="000.000.000-00" 
                  />
                </div>
                <div>
                  <label className="form-label">IE / RG <span className="text-gray-400 text-xs font-normal">(opcional)</span></label>
                  <Input value={formData.cliente_ie} onChange={(e) => setFormData({...formData, cliente_ie: e.target.value})} placeholder="Inscrição Estadual" />
                </div>
                <div>
                  <label className="form-label">E-mail <span className="text-gray-400 text-xs font-normal">(opcional)</span></label>
                  <Input type="email" value={formData.cliente_email} onChange={(e) => setFormData({...formData, cliente_email: e.target.value})} placeholder="cliente@email.com" />
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="form-label">Fone</label>
                    <Input 
                      value={formData.cliente_telefone} 
                      onChange={(e) => setFormData({...formData, cliente_telefone: formatTelefone(e.target.value)})} 
                      placeholder="(63) 0000-0000" 
                    />
                  </div>
                  <div>
                    <label className="form-label">Celular</label>
                    <Input 
                      value={formData.cliente_celular} 
                      onChange={(e) => setFormData({...formData, cliente_celular: formatTelefone(e.target.value)})} 
                      placeholder="(63) 90000-0000" 
                    />
                  </div>
                </div>
                <div>
                  <label className="form-label">CEP</label>
                  <div className="relative">
                    <Input 
                      value={formData.cliente_cep} 
                      onChange={(e) => {
                        const formatted = formatCEP(e.target.value);
                        setFormData({...formData, cliente_cep: formatted});
                        // Quando o CEP estiver completo, dispara busca automática
                        if (formatted.replace(/\D/g, "").length === 8) {
                          handleConsultaCep(formatted);
                        }
                      }}
                      onBlur={(e) => {
                        if (e.target.value.replace(/\D/g, "").length === 8) {
                          handleConsultaCep(e.target.value);
                        }
                      }}
                      placeholder="77000-000" 
                      maxLength={9}
                      data-testid="input-cep-cliente"
                    />
                    {consultandoCep && (
                      <Loader2 size={16} className="absolute right-2 top-1/2 -translate-y-1/2 animate-spin text-blue-500" />
                    )}
                  </div>
                  <p className="text-[10px] text-gray-400 mt-1">Endereço é preenchido automaticamente</p>
                </div>
                <div className="col-span-2">
                  <label className="form-label">Endereço</label>
                  <Input value={formData.cliente_endereco} onChange={(e) => setFormData({...formData, cliente_endereco: e.target.value})} placeholder="Rua, número, complemento" />
                </div>
                <div>
                  <label className="form-label">Bairro</label>
                  <Input value={formData.cliente_bairro} onChange={(e) => setFormData({...formData, cliente_bairro: e.target.value})} />
                </div>
                <div className="grid grid-cols-3 gap-2">
                  <div className="col-span-2">
                    <label className="form-label">Cidade</label>
                    <Input value={formData.cliente_cidade} onChange={(e) => setFormData({...formData, cliente_cidade: e.target.value})} />
                  </div>
                  <div>
                    <label className="form-label">UF</label>
                    <Input value={formData.cliente_uf} onChange={(e) => setFormData({...formData, cliente_uf: e.target.value.toUpperCase().slice(0,2)})} maxLength={2} placeholder="TO" />
                  </div>
                </div>
              </div>
            </fieldset>

            {/* Obra / Atendimento */}
            <fieldset className="border rounded p-3">
              <legend className="text-xs font-semibold uppercase px-1">Obra / Atendimento</legend>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="form-label">Obra</label>
                  <Input value={formData.obra} onChange={(e) => setFormData({...formData, obra: e.target.value})} placeholder="Nome da obra/projeto" />
                </div>
                <div>
                  <label className="form-label">Endereço de Entrega</label>
                  <Input value={formData.endereco_entrega} onChange={(e) => setFormData({...formData, endereco_entrega: e.target.value})} placeholder="Local de entrega/serviço" />
                </div>
                <div>
                  <label className="form-label">Tipo Atendimento</label>
                  <Input value={formData.tipo_atendimento} onChange={(e) => setFormData({...formData, tipo_atendimento: e.target.value})} placeholder="Locação / Serviço / Venda..." />
                </div>
                <div>
                  <label className="form-label">Período</label>
                  <Input value={formData.periodo} onChange={(e) => setFormData({...formData, periodo: e.target.value})} placeholder="Ex: 30 dias / Mensal" />
                </div>
                <div>
                  <label className="form-label">Periodicidade</label>
                  <Select 
                    value={formData.periodicidade || "nenhuma"} 
                    onValueChange={(v) => handlePeriodicidadeChange(v === "nenhuma" ? "" : v)}
                  >
                    <SelectTrigger className="w-full" data-testid="select-periodicidade">
                      <SelectValue placeholder="Selecione..." />
                    </SelectTrigger>
                    <SelectContent className="z-[9999]">
                      <SelectItem value="nenhuma">Nenhuma</SelectItem>
                      <SelectItem value="diaria">Diária (+1 dia)</SelectItem>
                      <SelectItem value="semanal">Semanal (+7 dias)</SelectItem>
                      <SelectItem value="quinzenal">Quinzenal (+15 dias)</SelectItem>
                      <SelectItem value="mensal">Mensal (+30 dias)</SelectItem>
                      <SelectItem value="semestral">Semestral (+180 dias)</SelectItem>
                      <SelectItem value="anual">Anual (+365 dias)</SelectItem>
                    </SelectContent>
                  </Select>
                  {formData.periodicidade && (
                    <p className="text-[10px] text-blue-600 mt-1">📅 Previsão de entrega calculada automaticamente</p>
                  )}
                </div>
                <div>
                  <label className="form-label">KM <span className="text-gray-400 text-xs font-normal">(opcional)</span></label>
                  <Input 
                    value={formData.km} 
                    onChange={(e) => setFormData({...formData, km: e.target.value.replace(/[^\d.,]/g, "")})} 
                    placeholder="Ex: 12500"
                    data-testid="input-km-os"
                  />
                </div>
                <div>
                  <label className="form-label">Data Abertura *</label>
                  <MaskedDateInput value={formData.data_abertura} onChange={(v) => handleDataAberturaChange(v)} required />
                </div>
                <div>
                  <label className="form-label">Data Fechamento</label>
                  <MaskedDateInput value={formData.data_fechamento} onChange={(v) => setFormData({...formData, data_fechamento: v})} />
                </div>
                <div>
                  <label className="form-label">Previsão Entrega</label>
                  <MaskedDateInput value={formData.data_previsao_entrega} onChange={(v) => setFormData({...formData, data_previsao_entrega: v})} />
                </div>
                <div>
                  <label className="form-label">Atendente</label>
                  <Input value={formData.atendente_nome} onChange={(e) => setFormData({...formData, atendente_nome: e.target.value})} placeholder="Nome do atendente" />
                </div>
              </div>
            </fieldset>

            {/* Descrição e financeiro */}
            <fieldset className="border rounded p-3">
              <legend className="text-xs font-semibold uppercase px-1">Descrição & Financeiro</legend>
              <div className="space-y-3">
                <div>
                  <label className="form-label">Descrição do Serviço *</label>
                  <Textarea
                    value={formData.descricao}
                    onChange={(e) => setFormData({...formData, descricao: e.target.value})}
                    placeholder="Descreva os serviços / produtos da OS"
                    required
                    rows={3}
                  />
                </div>
                <div className="grid grid-cols-3 gap-3">
                  <div>
                    <label className="form-label">Valor Principal</label>
                    <Input type="number" step="0.01" value={formData.valor_total} onChange={(e) => setFormData({...formData, valor_total: e.target.value})} placeholder="0,00" data-testid="input-valor-principal" />
                  </div>
                  <div>
                    <label className="form-label">Valor Desconto</label>
                    <Input type="number" step="0.01" value={formData.valor_desconto} onChange={(e) => setFormData({...formData, valor_desconto: e.target.value})} placeholder="0,00" />
                  </div>
                  <div>
                    <label className="form-label">Valor Antecipado</label>
                    <Input type="number" step="0.01" value={formData.valor_antecipado} onChange={(e) => setFormData({...formData, valor_antecipado: e.target.value})} placeholder="0,00" />
                  </div>
                </div>

                {/* Valores Adicionais (compostos) */}
                <div className="border rounded p-3 bg-amber-50/50">
                  <div className="flex items-center justify-between mb-2">
                    <label className="form-label mb-0">Valores Adicionais <span className="text-gray-400 text-xs font-normal">(opcional)</span></label>
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      className="h-7 px-2 text-xs"
                      onClick={() => setFormData({
                        ...formData,
                        valores_extras: [...(formData.valores_extras || []), { descricao: "", valor: "" }]
                      })}
                      data-testid="btn-add-valor-extra"
                    >
                      <Plus size={12} className="mr-1" />
                      Adicionar valor
                    </Button>
                  </div>
                  {(formData.valores_extras || []).length === 0 && (
                    <p className="text-xs text-gray-400">Use para somar deslocamento, hora extra, materiais, taxas, etc.</p>
                  )}
                  {(formData.valores_extras || []).map((v, idx) => (
                    <div key={idx} className="grid grid-cols-12 gap-2 mt-2 items-end">
                      <div className="col-span-7">
                        <label className="text-xs text-gray-500">Descrição</label>
                        <Input
                          value={v.descricao}
                          onChange={(e) => {
                            const arr = [...formData.valores_extras];
                            arr[idx] = { ...arr[idx], descricao: e.target.value };
                            setFormData({ ...formData, valores_extras: arr });
                          }}
                          placeholder="Ex: Deslocamento, Hora extra..."
                          data-testid={`input-valor-extra-desc-${idx}`}
                        />
                      </div>
                      <div className="col-span-4">
                        <label className="text-xs text-gray-500">Valor</label>
                        <Input
                          type="number"
                          step="0.01"
                          value={v.valor}
                          onChange={(e) => {
                            const arr = [...formData.valores_extras];
                            arr[idx] = { ...arr[idx], valor: e.target.value };
                            setFormData({ ...formData, valores_extras: arr });
                          }}
                          placeholder="0,00"
                          data-testid={`input-valor-extra-val-${idx}`}
                        />
                      </div>
                      <div className="col-span-1">
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          className="text-red-600 h-9 w-full px-0"
                          onClick={() => {
                            const arr = formData.valores_extras.filter((_, i) => i !== idx);
                            setFormData({ ...formData, valores_extras: arr });
                          }}
                          data-testid={`btn-remove-valor-extra-${idx}`}
                        >
                          <Trash2 size={14} />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Total calculado automaticamente */}
                <div className="bg-gray-100 border rounded-lg p-3 flex items-center justify-between">
                  <span className="text-sm text-gray-600">Valor Total (Principal + Adicionais − Desconto):</span>
                  <span className="text-lg font-bold text-[#D4A000]" data-testid="os-valor-total-calc">
                    {formatCurrency(
                      (parseFloat(formData.valor_total) || 0)
                      + (formData.valores_extras || []).reduce((s, v) => s + (parseFloat(v.valor) || 0), 0)
                      - (parseFloat(formData.valor_desconto) || 0)
                    )}
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="form-label">Forma de Pagamento</label>
                    <Input value={formData.forma_pagamento} onChange={(e) => setFormData({...formData, forma_pagamento: e.target.value})} placeholder="Boleto / PIX / Dinheiro..." />
                  </div>
                  <div>
                    <label className="form-label">Condição de Pagamento</label>
                    <Input value={formData.condicao_pagamento} onChange={(e) => setFormData({...formData, condicao_pagamento: e.target.value})} placeholder="Ex: 30/60/90 dias" />
                  </div>
                </div>
                <div>
                  <label className="form-label">Tipo Financeiro *</label>
                  <Select value={formData.tipo_financeiro} onValueChange={(v) => setFormData({...formData, tipo_financeiro: v})}>
                    <SelectTrigger className="w-full h-11"><SelectValue /></SelectTrigger>
                    <SelectContent className="z-[9999]">
                      <SelectItem value="nenhum">Nenhum</SelectItem>
                      <SelectItem value="a_pagar">A Pagar (Despesa)</SelectItem>
                      <SelectItem value="a_receber">A Receber (Receita)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </fieldset>

            {/* Vínculos: Máquinas / Frotas / Fornecedores */}
            <fieldset className="border rounded p-3">
              <legend className="text-xs font-semibold uppercase px-1">Vínculos (opcional)</legend>
              <div className="grid grid-cols-1 gap-3">
                {/* Máquinas */}
                <div>
                  <label className="form-label">Máquinas</label>
                  <div className="border rounded p-2 max-h-32 overflow-y-auto bg-white">
                    {machines.length === 0 && (
                      <p className="text-xs text-gray-400">Nenhuma máquina cadastrada</p>
                    )}
                    {machines.map((m) => {
                      const checked = (formData.maquinas_ids || []).includes(m.id);
                      return (
                        <label key={m.id} className="flex items-center gap-2 text-sm py-1 cursor-pointer hover:bg-gray-50 px-1 rounded">
                          <input
                            type="checkbox"
                            checked={checked}
                            onChange={() => {
                              const arr = formData.maquinas_ids || [];
                              setFormData({
                                ...formData,
                                maquinas_ids: checked ? arr.filter((x) => x !== m.id) : [...arr, m.id],
                              });
                            }}
                            data-testid={`checkbox-maquina-${m.id}`}
                          />
                          <span>{m.name} {m.plate && <span className="text-gray-500">({m.plate})</span>}</span>
                          {m.type && <span className="text-xs text-gray-400 ml-auto">{m.type}</span>}
                        </label>
                      );
                    })}
                  </div>
                  {formData.maquinas_ids?.length > 0 && (
                    <p className="text-xs text-blue-600 mt-1">{formData.maquinas_ids.length} selecionada(s)</p>
                  )}
                </div>

                {/* Frotas */}
                <div>
                  <label className="form-label">Frotas (Veículos)</label>
                  <div className="border rounded p-2 max-h-32 overflow-y-auto bg-white">
                    {machines.filter(m => m.plate).length === 0 && (
                      <p className="text-xs text-gray-400">Nenhuma frota com placa cadastrada</p>
                    )}
                    {machines.filter(m => m.plate).map((m) => {
                      const checked = (formData.frotas_ids || []).includes(m.id);
                      return (
                        <label key={m.id} className="flex items-center gap-2 text-sm py-1 cursor-pointer hover:bg-gray-50 px-1 rounded">
                          <input
                            type="checkbox"
                            checked={checked}
                            onChange={() => {
                              const arr = formData.frotas_ids || [];
                              setFormData({
                                ...formData,
                                frotas_ids: checked ? arr.filter((x) => x !== m.id) : [...arr, m.id],
                              });
                            }}
                            data-testid={`checkbox-frota-${m.id}`}
                          />
                          <span>{m.name} <span className="text-gray-500">({m.plate})</span></span>
                          {m.model && <span className="text-xs text-gray-400 ml-auto">{m.model}</span>}
                        </label>
                      );
                    })}
                  </div>
                  {formData.frotas_ids?.length > 0 && (
                    <p className="text-xs text-blue-600 mt-1">{formData.frotas_ids.length} selecionada(s)</p>
                  )}
                </div>

                {/* Fornecedores */}
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label className="form-label mb-0">Fornecedores</label>
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      className="h-7 px-2 text-xs"
                      onClick={() => setShowNovoFornecedor(true)}
                      data-testid="btn-novo-fornecedor-os"
                    >
                      <UserPlus size={12} className="mr-1" />
                      Cadastrar novo
                    </Button>
                  </div>
                  <div className="border rounded p-2 max-h-32 overflow-y-auto bg-white">
                    {fornecedores.length === 0 && (
                      <p className="text-xs text-gray-400">Nenhum fornecedor cadastrado — use o botão "Cadastrar novo" acima</p>
                    )}
                    {fornecedores.map((f) => {
                      const checked = (formData.fornecedores_ids || []).includes(f.id);
                      const label = f.nome_razao || f.razao_social || f.nome || "Sem nome";
                      return (
                        <label key={f.id} className="flex items-center gap-2 text-sm py-1 cursor-pointer hover:bg-gray-50 px-1 rounded">
                          <input
                            type="checkbox"
                            checked={checked}
                            onChange={() => {
                              const arr = formData.fornecedores_ids || [];
                              setFormData({
                                ...formData,
                                fornecedores_ids: checked ? arr.filter((x) => x !== f.id) : [...arr, f.id],
                              });
                            }}
                            data-testid={`checkbox-fornecedor-${f.id}`}
                          />
                          <span>{label}</span>
                          {f.cpf_cnpj && <span className="text-xs text-gray-400 ml-auto">{f.cpf_cnpj}</span>}
                        </label>
                      );
                    })}
                  </div>
                  {formData.fornecedores_ids?.length > 0 && (
                    <p className="text-xs text-blue-600 mt-1">{formData.fornecedores_ids.length} selecionado(s)</p>
                  )}
                </div>
              </div>
            </fieldset>

            {/* Observações */}
            <fieldset className="border rounded p-3">
              <legend className="text-xs font-semibold uppercase px-1">Observações</legend>
              <div className="space-y-3">
                <div>
                  <label className="form-label">Observação dos Serviços</label>
                  <Textarea value={formData.observacao_servicos} onChange={(e) => setFormData({...formData, observacao_servicos: e.target.value})} rows={2} placeholder="Detalhes específicos sobre os serviços executados" />
                </div>
                <div>
                  <label className="form-label">Notas Gerais (rodapé)</label>
                  <Textarea value={formData.notas_gerais} onChange={(e) => setFormData({...formData, notas_gerais: e.target.value})} rows={2} placeholder="Cláusulas, garantias, condições gerais..." />
                </div>
                <div>
                  <label className="form-label">Observações Internas</label>
                  <Input value={formData.observacoes} onChange={(e) => setFormData({...formData, observacoes: e.target.value})} placeholder="Notas para uso interno (não saem no PDF)" />
                </div>
              </div>
            </fieldset>

            <div className="flex gap-3 pt-2">
              <Button type="button" variant="outline" onClick={closeModal} className="flex-1">
                Cancelar
              </Button>
              <Button type="submit" className="flex-1 bg-[#D4A000] hover:bg-[#D4A000]">
                {editingOrdem ? "Atualizar" : "Criar OS"}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      {/* Modal de Cadastro Rápido de Cliente (reutilizado de Contas a Receber) */}
      <CadastroFormModal
        open={showNovoCadastro}
        onOpenChange={setShowNovoCadastro}
        defaultTipo="cliente"
        onSuccess={handleNovoCadastroSuccess}
      />

      {/* Modal de Cadastro Rápido de Fornecedor */}
      <CadastroFormModal
        open={showNovoFornecedor}
        onOpenChange={setShowNovoFornecedor}
        defaultTipo="fornecedor"
        onSuccess={handleNovoFornecedorSuccess}
      />
    </div>
  );
}
