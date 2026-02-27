import { useState, useEffect, useRef } from "react";
import axios from "axios";
import { API } from "@/App";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { 
  Plus, Search, Building, Calendar, User, MapPin, CheckCircle2, Clock, XCircle,
  Edit, Trash2, DollarSign, Phone, FileText, Paperclip, Eye, Download, X, Home,
  Ruler, Key, AlertCircle
} from "lucide-react";
import { toast } from "sonner";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { formatCEP, formatTelefone, formatCurrency, parseCurrency } from "@/utils/masks";

const tiposPeriodo = [
  { value: "diaria", label: "Diária" },
  { value: "semanal", label: "Semanal" },
  { value: "quinzenal", label: "Quinzenal" },
  { value: "mensal", label: "Mensal" },
  { value: "trimestral", label: "Trimestral" },
  { value: "semestral", label: "Semestral" },
  { value: "anual", label: "Anual" },
  { value: "outro", label: "Outro (especificar)" }
];

const tiposImovel = [
  { value: "apartamento", label: "Apartamento" },
  { value: "casa", label: "Casa" },
  { value: "sala_comercial", label: "Sala Comercial" },
  { value: "loja", label: "Loja" },
  { value: "galpao", label: "Galpão" },
  { value: "terreno", label: "Terreno" },
  { value: "kitnet", label: "Kitnet" },
  { value: "cobertura", label: "Cobertura" },
  { value: "fazenda", label: "Fazenda/Sítio" },
  { value: "outro", label: "Outro" }
];

export default function ImoveisPage() {
  const [imoveis, setImoveis] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("todos");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingImovel, setEditingImovel] = useState(null);
  const [contractFile, setContractFile] = useState(null);
  const [uploadingFile, setUploadingFile] = useState(false);
  const [previewModal, setPreviewModal] = useState({ open: false, url: null, name: null });
  const fileInputRef = useRef(null);
  const [formData, setFormData] = useState({
    // Dados do imóvel
    tipo_imovel: "apartamento",
    descricao: "",
    endereco: "",
    numero: "",
    complemento: "",
    bairro: "",
    cidade: "",
    estado: "TO",
    cep: "",
    area_m2: "",
    quartos: "",
    banheiros: "",
    vagas_garagem: "",
    // Dados do contrato
    cliente_nome: "",
    cliente_telefone: "",
    cliente_documento: "",
    numero_contrato: "",
    tipo_periodo: "mensal",
    periodo_especificado: "",
    data_inicio: new Date().toISOString().split("T")[0],
    data_vencimento: "",
    valor_aluguel: "",
    valor_condominio: "",
    valor_iptu: "",
    valor_caucao: "",
    dia_vencimento: "10",
    observacoes: "",
    gerar_conta_receber: true
  });

  useEffect(() => {
    fetchImoveis();
  }, []);

  const fetchImoveis = async () => {
    try {
      const response = await axios.get(`${API}/admin/imoveis`);
      setImoveis(response.data);
    } catch (error) {
      if (error.response?.status === 403) {
        toast.error("Sessão expirada. Faça login novamente.");
      } else {
        toast.error("Erro ao carregar imóveis");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.descricao || !formData.endereco || !formData.cliente_nome || !formData.valor_aluguel) {
      toast.error("Preencha os campos obrigatórios");
      return;
    }

    try {
      const payload = {
        ...formData,
        valor_aluguel: parseCurrency(formData.valor_aluguel) || 0,
        valor_condominio: parseCurrency(formData.valor_condominio) || 0,
        valor_iptu: parseCurrency(formData.valor_iptu) || 0,
        valor_caucao: parseCurrency(formData.valor_caucao) || 0,
        area_m2: parseFloat(formData.area_m2) || 0,
        quartos: parseInt(formData.quartos) || 0,
        banheiros: parseInt(formData.banheiros) || 0,
        vagas_garagem: parseInt(formData.vagas_garagem) || 0,
        dia_vencimento: parseInt(formData.dia_vencimento) || 10,
      };

      if (editingImovel) {
        await axios.put(`${API}/admin/imoveis/${editingImovel.id}`, payload);
        toast.success("Imóvel atualizado!");
      } else {
        await axios.post(`${API}/admin/imoveis`, payload);
        toast.success("Imóvel cadastrado!");
      }
      
      fetchImoveis();
      closeModal();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao salvar imóvel");
    }
  };

  const handleDelete = async (id) => {
    if (!confirm("Tem certeza que deseja excluir este imóvel?")) return;
    
    try {
      await axios.delete(`${API}/admin/imoveis/${id}`);
      toast.success("Imóvel excluído!");
      fetchImoveis();
    } catch (error) {
      toast.error("Erro ao excluir imóvel");
    }
  };

  const handleStatusChange = async (id, newStatus) => {
    try {
      await axios.patch(`${API}/admin/imoveis/${id}/status`, { status: newStatus });
      toast.success("Status atualizado!");
      fetchImoveis();
    } catch (error) {
      toast.error("Erro ao atualizar status");
    }
  };

  const handleFileUpload = async (imovelId) => {
    if (!contractFile) return;
    
    setUploadingFile(true);
    const uploadFormData = new FormData();
    uploadFormData.append("file", contractFile);
    
    try {
      await axios.post(`${API}/admin/imoveis/${imovelId}/contrato`, uploadFormData, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      toast.success("Contrato anexado!");
      fetchImoveis();
      setContractFile(null);
    } catch (error) {
      toast.error("Erro ao anexar contrato");
    } finally {
      setUploadingFile(false);
    }
  };

  const openEditModal = (imovel) => {
    setEditingImovel(imovel);
    setFormData({
      tipo_imovel: imovel.tipo_imovel || "apartamento",
      descricao: imovel.descricao || "",
      endereco: imovel.endereco || "",
      numero: imovel.numero || "",
      complemento: imovel.complemento || "",
      bairro: imovel.bairro || "",
      cidade: imovel.cidade || "",
      estado: imovel.estado || "TO",
      cep: imovel.cep || "",
      area_m2: imovel.area_m2?.toString() || "",
      quartos: imovel.quartos?.toString() || "",
      banheiros: imovel.banheiros?.toString() || "",
      vagas_garagem: imovel.vagas_garagem?.toString() || "",
      cliente_nome: imovel.cliente_nome || "",
      cliente_telefone: imovel.cliente_telefone || "",
      cliente_documento: imovel.cliente_documento || "",
      numero_contrato: imovel.numero_contrato || "",
      tipo_periodo: imovel.tipo_periodo || "mensal",
      periodo_especificado: imovel.periodo_especificado || "",
      data_inicio: imovel.data_inicio || new Date().toISOString().split("T")[0],
      data_vencimento: imovel.data_vencimento || "",
      valor_aluguel: imovel.valor_aluguel ? formatCurrency((imovel.valor_aluguel * 100).toString()) : "",
      valor_condominio: imovel.valor_condominio ? formatCurrency((imovel.valor_condominio * 100).toString()) : "",
      valor_iptu: imovel.valor_iptu ? formatCurrency((imovel.valor_iptu * 100).toString()) : "",
      valor_caucao: imovel.valor_caucao ? formatCurrency((imovel.valor_caucao * 100).toString()) : "",
      dia_vencimento: imovel.dia_vencimento?.toString() || "10",
      observacoes: imovel.observacoes || "",
      gerar_conta_receber: imovel.gerar_conta_receber !== false
    });
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setEditingImovel(null);
    setFormData({
      tipo_imovel: "apartamento",
      descricao: "",
      endereco: "",
      numero: "",
      complemento: "",
      bairro: "",
      cidade: "",
      estado: "TO",
      cep: "",
      area_m2: "",
      quartos: "",
      banheiros: "",
      vagas_garagem: "",
      cliente_nome: "",
      cliente_telefone: "",
      cliente_documento: "",
      numero_contrato: "",
      tipo_periodo: "mensal",
      periodo_especificado: "",
      data_inicio: new Date().toISOString().split("T")[0],
      data_vencimento: "",
      valor_aluguel: "",
      valor_condominio: "",
      valor_iptu: "",
      valor_caucao: "",
      dia_vencimento: "10",
      observacoes: "",
      gerar_conta_receber: true
    });
  };

  const buscarCep = async (cep) => {
    const cepLimpo = cep.replace(/\D/g, "");
    if (cepLimpo.length !== 8) return;
    
    try {
      const response = await axios.get(`https://viacep.com.br/ws/${cepLimpo}/json/`);
      if (!response.data.erro) {
        setFormData(prev => ({
          ...prev,
          endereco: response.data.logradouro || prev.endereco,
          bairro: response.data.bairro || prev.bairro,
          cidade: response.data.localidade || prev.cidade,
          estado: response.data.uf || prev.estado
        }));
      }
    } catch (error) {
      console.error("Erro ao buscar CEP:", error);
    }
  };

  const filteredImoveis = imoveis.filter(imovel => {
    const matchesSearch = 
      (imovel.descricao?.toLowerCase() || "").includes(search.toLowerCase()) ||
      (imovel.cliente_nome?.toLowerCase() || "").includes(search.toLowerCase()) ||
      (imovel.endereco?.toLowerCase() || "").includes(search.toLowerCase());
    const matchesFilter = filter === "todos" || imovel.status === filter;
    return matchesSearch && matchesFilter;
  });

  const getStatusColor = (status) => {
    const colors = {
      ativo: "bg-green-100 text-green-700",
      finalizado: "bg-gray-100 text-gray-700",
      pendente: "bg-yellow-100 text-yellow-700",
      cancelado: "bg-red-100 text-red-700"
    };
    return colors[status] || "bg-gray-100 text-gray-700";
  };

  const getStatusIcon = (status) => {
    const icons = {
      ativo: <CheckCircle2 size={14} />,
      finalizado: <XCircle size={14} />,
      pendente: <Clock size={14} />,
      cancelado: <AlertCircle size={14} />
    };
    return icons[status] || <Clock size={14} />;
  };

  const getTipoImovelLabel = (tipo) => {
    const found = tiposImovel.find(t => t.value === tipo);
    return found ? found.label : tipo;
  };

  const calcularValorTotal = () => {
    const aluguel = parseFloat(formData.valor_aluguel) || 0;
    const condominio = parseFloat(formData.valor_condominio) || 0;
    const iptu = parseFloat(formData.valor_iptu) || 0;
    return aluguel + condominio + iptu;
  };

  // Estatísticas
  const stats = {
    total: imoveis.length,
    ativos: imoveis.filter(i => i.status === "ativo").length,
    pendentes: imoveis.filter(i => i.status === "pendente").length,
    valorMensal: imoveis.filter(i => i.status === "ativo").reduce((acc, i) => acc + (i.valor_aluguel || 0), 0)
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin w-8 h-8 border-4 border-amber-500 border-t-transparent rounded-full"></div>
      </div>
    );
  }

  return (
    <div className="p-4 md:p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-lg bg-amber-100 flex items-center justify-center">
            <Building size={24} className="text-amber-600" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-gray-900">Imóveis para Locação</h1>
            <p className="text-sm text-gray-500">{stats.total} imóveis cadastrados</p>
          </div>
        </div>
        <Button 
          onClick={() => setIsModalOpen(true)}
          className="bg-amber-500 hover:bg-amber-600 text-white"
          data-testid="btn-novo-imovel"
        >
          <Plus size={18} className="mr-2" />
          Novo Imóvel
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="border-l-4 border-l-amber-500">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <Home className="text-amber-500" size={24} />
              <div>
                <p className="text-2xl font-bold text-gray-900">{stats.total}</p>
                <p className="text-xs text-gray-500">Total de Imóveis</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="border-l-4 border-l-green-500">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <Key className="text-green-500" size={24} />
              <div>
                <p className="text-2xl font-bold text-gray-900">{stats.ativos}</p>
                <p className="text-xs text-gray-500">Locados</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="border-l-4 border-l-yellow-500">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <Clock className="text-yellow-500" size={24} />
              <div>
                <p className="text-2xl font-bold text-gray-900">{stats.pendentes}</p>
                <p className="text-xs text-gray-500">Disponíveis</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="border-l-4 border-l-blue-500">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <DollarSign className="text-blue-500" size={24} />
              <div>
                <p className="text-2xl font-bold text-gray-900">
                  R$ {stats.valorMensal.toLocaleString('pt-BR', {minimumFractionDigits: 2})}
                </p>
                <p className="text-xs text-gray-500">Receita Mensal</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <div className="flex flex-col md:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
          <Input
            placeholder="Buscar por descrição, endereço ou inquilino..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-10"
            data-testid="search-imoveis"
          />
        </div>
        <Select value={filter} onValueChange={setFilter}>
          <SelectTrigger className="w-full md:w-48" data-testid="filter-status">
            <SelectValue placeholder="Filtrar por status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="todos">Todos</SelectItem>
            <SelectItem value="ativo">Locados</SelectItem>
            <SelectItem value="pendente">Disponíveis</SelectItem>
            <SelectItem value="finalizado">Finalizados</SelectItem>
            <SelectItem value="cancelado">Cancelados</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* List */}
      <div className="space-y-4">
        {filteredImoveis.length === 0 ? (
          <Card>
            <CardContent className="p-8 text-center text-gray-500">
              <Building size={48} className="mx-auto mb-4 text-gray-300" />
              <p>Nenhum imóvel encontrado</p>
            </CardContent>
          </Card>
        ) : (
          filteredImoveis.map((imovel) => (
            <Card key={imovel.id} className="hover:shadow-md transition-shadow" data-testid={`imovel-card-${imovel.id}`}>
              <CardContent className="p-4">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div className="flex items-start gap-4 flex-1">
                    <div className="w-12 h-12 rounded-lg bg-amber-50 flex items-center justify-center shrink-0">
                      <Building className="text-amber-500" size={24} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="font-semibold text-gray-900 truncate">{imovel.descricao}</h3>
                        <span className={`px-2 py-0.5 rounded-full text-xs font-medium flex items-center gap-1 ${getStatusColor(imovel.status)}`}>
                          {getStatusIcon(imovel.status)}
                          {imovel.status === "ativo" ? "Locado" : imovel.status === "pendente" ? "Disponível" : imovel.status}
                        </span>
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-2 text-sm text-gray-600">
                        <div className="flex items-center gap-1">
                          <Home size={14} className="text-gray-400" />
                          <span>{getTipoImovelLabel(imovel.tipo_imovel)}</span>
                          {imovel.area_m2 && <span className="text-gray-400">• {imovel.area_m2}m²</span>}
                        </div>
                        <div className="flex items-center gap-1">
                          <MapPin size={14} className="text-gray-400" />
                          <span className="truncate">{imovel.endereco}, {imovel.numero} - {imovel.bairro}</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <User size={14} className="text-gray-400" />
                          <span className="truncate">{imovel.cliente_nome || "Sem inquilino"}</span>
                        </div>
                      </div>
                      <div className="flex flex-wrap gap-4 mt-2 text-sm">
                        <div className="flex items-center gap-1 text-green-600 font-medium">
                          <DollarSign size={14} />
                          <span>R$ {(imovel.valor_aluguel || 0).toLocaleString('pt-BR', {minimumFractionDigits: 2})}/mês</span>
                        </div>
                        {imovel.data_vencimento && (
                          <div className="flex items-center gap-1 text-gray-500">
                            <Calendar size={14} />
                            <span>Venc: {imovel.data_vencimento}</span>
                          </div>
                        )}
                        {imovel.contrato_url && (
                          <button 
                            onClick={() => setPreviewModal({ open: true, url: imovel.contrato_url, name: "Contrato" })}
                            className="flex items-center gap-1 text-blue-600 hover:text-blue-700"
                          >
                            <FileText size={14} />
                            <span>Ver Contrato</span>
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Select 
                      value={imovel.status} 
                      onValueChange={(value) => handleStatusChange(imovel.id, value)}
                    >
                      <SelectTrigger className="w-32 h-8 text-xs">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="pendente">Disponível</SelectItem>
                        <SelectItem value="ativo">Locado</SelectItem>
                        <SelectItem value="finalizado">Finalizado</SelectItem>
                        <SelectItem value="cancelado">Cancelado</SelectItem>
                      </SelectContent>
                    </Select>
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => openEditModal(imovel)}
                    >
                      <Edit size={14} />
                    </Button>
                    <Button 
                      variant="outline" 
                      size="sm"
                      className="text-red-500 hover:text-red-700"
                      onClick={() => handleDelete(imovel.id)}
                    >
                      <Trash2 size={14} />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>

      {/* Modal de Cadastro/Edição */}
      <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Building className="text-amber-500" />
              {editingImovel ? "Editar Imóvel" : "Cadastrar Novo Imóvel"}
            </DialogTitle>
          </DialogHeader>
          
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Dados do Imóvel */}
            <div>
              <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
                <Home size={16} className="text-amber-500" />
                Dados do Imóvel
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="text-xs text-gray-500 block mb-1">Tipo de Imóvel *</label>
                  <Select value={formData.tipo_imovel} onValueChange={(v) => setFormData({...formData, tipo_imovel: v})}>
                    <SelectTrigger data-testid="select-tipo-imovel">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {tiposImovel.map(tipo => (
                        <SelectItem key={tipo.value} value={tipo.value}>{tipo.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="md:col-span-2">
                  <label className="text-xs text-gray-500 block mb-1">Descrição/Nome do Imóvel *</label>
                  <Input
                    value={formData.descricao}
                    onChange={(e) => setFormData({...formData, descricao: e.target.value})}
                    placeholder="Ex: Apartamento 3 quartos no centro"
                    required
                    data-testid="input-descricao"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-500 block mb-1">CEP</label>
                  <Input
                    value={formData.cep}
                    onChange={(e) => {
                      const formattedCep = formatCEP(e.target.value);
                      setFormData({...formData, cep: formattedCep});
                      if (formattedCep.replace(/\D/g, "").length === 8) {
                        buscarCep(formattedCep);
                      }
                    }}
                    placeholder="00000-000"
                  />
                </div>
                <div className="md:col-span-2">
                  <label className="text-xs text-gray-500 block mb-1">Endereço *</label>
                  <Input
                    value={formData.endereco}
                    onChange={(e) => setFormData({...formData, endereco: e.target.value})}
                    placeholder="Rua, Avenida..."
                    required
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-500 block mb-1">Número</label>
                  <Input
                    value={formData.numero}
                    onChange={(e) => setFormData({...formData, numero: e.target.value})}
                    placeholder="123"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-500 block mb-1">Complemento</label>
                  <Input
                    value={formData.complemento}
                    onChange={(e) => setFormData({...formData, complemento: e.target.value})}
                    placeholder="Apto, Sala..."
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-500 block mb-1">Bairro</label>
                  <Input
                    value={formData.bairro}
                    onChange={(e) => setFormData({...formData, bairro: e.target.value})}
                    placeholder="Bairro"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-500 block mb-1">Cidade</label>
                  <Input
                    value={formData.cidade}
                    onChange={(e) => setFormData({...formData, cidade: e.target.value})}
                    placeholder="Cidade"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-500 block mb-1">Estado</label>
                  <Input
                    value={formData.estado}
                    onChange={(e) => setFormData({...formData, estado: e.target.value})}
                    placeholder="UF"
                    maxLength={2}
                  />
                </div>
              </div>
              
              {/* Características */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
                <div>
                  <label className="text-xs text-gray-500 block mb-1">Área (m²)</label>
                  <Input
                    type="number"
                    value={formData.area_m2}
                    onChange={(e) => setFormData({...formData, area_m2: e.target.value})}
                    placeholder="0"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-500 block mb-1">Quartos</label>
                  <Input
                    type="number"
                    value={formData.quartos}
                    onChange={(e) => setFormData({...formData, quartos: e.target.value})}
                    placeholder="0"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-500 block mb-1">Banheiros</label>
                  <Input
                    type="number"
                    value={formData.banheiros}
                    onChange={(e) => setFormData({...formData, banheiros: e.target.value})}
                    placeholder="0"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-500 block mb-1">Vagas Garagem</label>
                  <Input
                    type="number"
                    value={formData.vagas_garagem}
                    onChange={(e) => setFormData({...formData, vagas_garagem: e.target.value})}
                    placeholder="0"
                  />
                </div>
              </div>
            </div>

            {/* Dados do Inquilino */}
            <div>
              <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
                <User size={16} className="text-amber-500" />
                Dados do Inquilino
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="text-xs text-gray-500 block mb-1">Nome do Inquilino *</label>
                  <Input
                    value={formData.cliente_nome}
                    onChange={(e) => setFormData({...formData, cliente_nome: e.target.value})}
                    placeholder="Nome completo"
                    required
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-500 block mb-1">Telefone</label>
                  <Input
                    value={formData.cliente_telefone}
                    onChange={(e) => setFormData({...formData, cliente_telefone: e.target.value})}
                    placeholder="(00) 00000-0000"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-500 block mb-1">CPF/CNPJ</label>
                  <Input
                    value={formData.cliente_documento}
                    onChange={(e) => setFormData({...formData, cliente_documento: e.target.value})}
                    placeholder="000.000.000-00"
                  />
                </div>
              </div>
            </div>

            {/* Dados do Contrato */}
            <div>
              <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
                <FileText size={16} className="text-amber-500" />
                Dados do Contrato
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div>
                  <label className="text-xs text-gray-500 block mb-1">Nº Contrato</label>
                  <Input
                    value={formData.numero_contrato}
                    onChange={(e) => setFormData({...formData, numero_contrato: e.target.value})}
                    placeholder="000/2025"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-500 block mb-1">Tipo de Período</label>
                  <Select value={formData.tipo_periodo} onValueChange={(v) => setFormData({...formData, tipo_periodo: v})}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {tiposPeriodo.map(tipo => (
                        <SelectItem key={tipo.value} value={tipo.value}>{tipo.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="text-xs text-gray-500 block mb-1">Data Início</label>
                  <Input
                    type="date"
                    value={formData.data_inicio}
                    onChange={(e) => setFormData({...formData, data_inicio: e.target.value})}
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-500 block mb-1">Data Término</label>
                  <Input
                    type="date"
                    value={formData.data_vencimento}
                    onChange={(e) => setFormData({...formData, data_vencimento: e.target.value})}
                  />
                </div>
              </div>
            </div>

            {/* Valores */}
            <div>
              <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
                <DollarSign size={16} className="text-amber-500" />
                Valores
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                <div>
                  <label className="text-xs text-gray-500 block mb-1">Aluguel *</label>
                  <Input
                    value={formData.valor_aluguel}
                    onChange={(e) => setFormData({...formData, valor_aluguel: formatCurrency(e.target.value)})}
                    placeholder="R$ 0,00"
                    required
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-500 block mb-1">Condomínio</label>
                  <Input
                    value={formData.valor_condominio}
                    onChange={(e) => setFormData({...formData, valor_condominio: formatCurrency(e.target.value)})}
                    placeholder="R$ 0,00"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-500 block mb-1">IPTU</label>
                  <Input
                    value={formData.valor_iptu}
                    onChange={(e) => setFormData({...formData, valor_iptu: formatCurrency(e.target.value)})}
                    placeholder="R$ 0,00"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-500 block mb-1">Caução</label>
                  <Input
                    value={formData.valor_caucao}
                    onChange={(e) => setFormData({...formData, valor_caucao: formatCurrency(e.target.value)})}
                    placeholder="R$ 0,00"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-500 block mb-1">Dia Vencimento</label>
                  <Input
                    type="number"
                    min="1"
                    max="31"
                    value={formData.dia_vencimento}
                    onChange={(e) => setFormData({...formData, dia_vencimento: e.target.value})}
                    placeholder="10"
                  />
                </div>
              </div>
              <div className="mt-3 p-3 bg-amber-50 rounded-lg">
                <p className="text-sm text-amber-700 font-medium">
                  Valor Total Mensal: R$ {calcularValorTotal().toLocaleString('pt-BR', {minimumFractionDigits: 2})}
                </p>
              </div>
            </div>

            {/* Observações */}
            <div>
              <label className="text-xs text-gray-500 block mb-1">Observações</label>
              <Textarea
                value={formData.observacoes}
                onChange={(e) => setFormData({...formData, observacoes: e.target.value})}
                placeholder="Observações adicionais..."
                rows={3}
              />
            </div>

            {/* Gerar conta a receber */}
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="gerar_conta"
                checked={formData.gerar_conta_receber}
                onChange={(e) => setFormData({...formData, gerar_conta_receber: e.target.checked})}
                className="w-4 h-4 rounded border-gray-300"
              />
              <label htmlFor="gerar_conta" className="text-sm text-gray-700">
                Gerar automaticamente conta a receber mensalmente
              </label>
            </div>

            {/* Botões */}
            <div className="flex justify-end gap-3 pt-4 border-t">
              <Button type="button" variant="outline" onClick={closeModal}>
                Cancelar
              </Button>
              <Button type="submit" className="bg-amber-500 hover:bg-amber-600 text-white" data-testid="btn-salvar-imovel">
                {editingImovel ? "Atualizar" : "Cadastrar"}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      {/* Modal de Preview */}
      <Dialog open={previewModal.open} onOpenChange={() => setPreviewModal({ open: false, url: null, name: null })}>
        <DialogContent className="max-w-4xl h-[80vh]">
          <DialogHeader>
            <DialogTitle className="flex items-center justify-between">
              {previewModal.name}
              <div className="flex gap-2">
                <Button variant="outline" size="sm" asChild>
                  <a href={previewModal.url} download target="_blank" rel="noopener noreferrer">
                    <Download size={14} className="mr-1" /> Download
                  </a>
                </Button>
              </div>
            </DialogTitle>
          </DialogHeader>
          <div className="flex-1 overflow-auto">
            {previewModal.url && (
              <object
                data={previewModal.url}
                type="application/pdf"
                className="w-full h-full min-h-[60vh]"
              >
                <p>Não foi possível exibir o arquivo. <a href={previewModal.url} target="_blank" rel="noopener noreferrer" className="text-blue-600">Clique aqui para baixar</a></p>
              </object>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
