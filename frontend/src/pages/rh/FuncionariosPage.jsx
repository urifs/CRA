import { useState, useEffect, useRef } from "react";
import axios from "axios";
import { API } from "@/App";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { 
  Plus, Search, Users, Phone, Mail, MapPin, Edit, Trash2, 
  User, Filter, Paperclip, Eye, Download, X, FileText, 
  Image as ImageIcon, Loader2, Calendar, DollarSign, Briefcase
} from "lucide-react";
import { toast } from "sonner";

export default function FuncionariosPage() {
  const [funcionarios, setFuncionarios] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [filterStatus, setFilterStatus] = useState("");
  const [filterRegime, setFilterRegime] = useState("");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingFuncionario, setEditingFuncionario] = useState(null);
  
  // Anexos
  const [anexos, setAnexos] = useState([]);
  const [uploadingAnexo, setUploadingAnexo] = useState(false);
  const [previewModal, setPreviewModal] = useState({ open: false, url: null, name: null, type: null });
  const fileInputRef = useRef(null);
  
  // Consulta CEP
  const [consultandoCep, setConsultandoCep] = useState(false);
  
  const [formData, setFormData] = useState({
    nome: "",
    cpf: "",
    rg: "",
    data_nascimento: "",
    telefone: "",
    celular: "",
    email: "",
    cep: "",
    endereco: "",
    numero: "",
    complemento: "",
    bairro: "",
    cidade: "",
    uf: "",
    cargo: "",
    funcao: "",
    departamento: "",
    salario: "",
    data_admissao: "",
    regime_contratacao: "CLT",
    status: "ativo",
    observacoes: ""
  });

  const regimesContratacao = [
    { value: "CLT", label: "CLT" },
    { value: "PJ", label: "PJ" },
    { value: "Contrato", label: "Contrato" },
    { value: "Estagio", label: "Estágio" },
    { value: "Prestador", label: "Prestador de Serviço" }
  ];

  const statusOptions = [
    { value: "ativo", label: "Ativo" },
    { value: "ferias", label: "Férias" },
    { value: "afastado", label: "Afastado" },
    { value: "desligado", label: "Desligado" }
  ];

  useEffect(() => {
    fetchFuncionarios();
  }, [filterStatus, filterRegime]);

  const fetchFuncionarios = async () => {
    try {
      let url = `${API}/rh/funcionarios`;
      const params = new URLSearchParams();
      if (filterStatus) params.append("status", filterStatus);
      if (filterRegime) params.append("regime", filterRegime);
      if (params.toString()) url += `?${params.toString()}`;
      
      const response = await axios.get(url);
      setFuncionarios(response.data);
    } catch (error) {
      toast.error("Erro ao carregar funcionários");
    } finally {
      setLoading(false);
    }
  };

  const handleConsultaCep = async () => {
    const cep = formData.cep.replace(/\D/g, '');
    if (cep.length !== 8) {
      toast.error("CEP deve ter 8 dígitos");
      return;
    }
    
    setConsultandoCep(true);
    try {
      const response = await axios.get(`${API}/consulta/cep/${cep}`);
      const dados = response.data.data;
      
      setFormData(prev => ({
        ...prev,
        endereco: dados.endereco || prev.endereco,
        complemento: dados.complemento || prev.complemento,
        bairro: dados.bairro || prev.bairro,
        cidade: dados.cidade || prev.cidade,
        uf: dados.uf || prev.uf
      }));
      
      toast.success("Endereço preenchido!");
    } catch (error) {
      toast.error(error.response?.data?.detail || "CEP não encontrado");
    } finally {
      setConsultandoCep(false);
    }
  };

  const handleUploadAnexo = async (e) => {
    const files = e.target.files;
    if (!files?.length || !editingFuncionario?.id) return;
    
    setUploadingAnexo(true);
    try {
      for (const file of files) {
        const formDataFile = new FormData();
        formDataFile.append("file", file);
        await axios.post(`${API}/rh/funcionarios/${editingFuncionario.id}/anexos`, formDataFile, {
          headers: { "Content-Type": "multipart/form-data" }
        });
      }
      toast.success("Anexo(s) adicionado(s)!");
      const response = await axios.get(`${API}/rh/funcionarios/${editingFuncionario.id}`);
      setAnexos(response.data.anexos || []);
    } catch (error) {
      toast.error("Erro ao anexar arquivo");
    } finally {
      setUploadingAnexo(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const handleDeleteAnexo = async (anexoId) => {
    if (!confirm("Excluir este anexo?")) return;
    try {
      await axios.delete(`${API}/rh/funcionarios/${editingFuncionario.id}/anexos/${anexoId}`);
      setAnexos(anexos.filter(a => a.id !== anexoId));
      toast.success("Anexo excluído!");
    } catch (error) {
      toast.error("Erro ao excluir anexo");
    }
  };

  const handleViewAnexo = (anexo) => {
    const url = `${API.replace('/api', '')}/uploads/funcionarios/${anexo.filename}`;
    const ext = anexo.filename.split('.').pop().toLowerCase();
    const isImage = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg'].includes(ext);
    const isPdf = ext === 'pdf';
    setPreviewModal({ open: true, url, name: anexo.original_name || anexo.filename, type: isImage ? 'image' : isPdf ? 'pdf' : 'other' });
  };

  const handleDownloadAnexo = async (anexo) => {
    try {
      const response = await axios.get(`${API}/rh/funcionarios/${editingFuncionario.id}/anexos/${anexo.id}/download`, {
        responseType: 'blob'
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', anexo.original_name || anexo.filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      toast.error("Erro ao baixar anexo");
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const dataToSend = {
        ...formData,
        salario: formData.salario ? parseFloat(formData.salario) : 0
      };
      
      if (editingFuncionario) {
        await axios.put(`${API}/rh/funcionarios/${editingFuncionario.id}`, dataToSend);
        toast.success("Funcionário atualizado!");
      } else {
        await axios.post(`${API}/rh/funcionarios`, dataToSend);
        toast.success("Funcionário cadastrado!");
      }
      fetchFuncionarios();
      closeModal();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao salvar");
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Deseja excluir este funcionário?")) return;
    try {
      await axios.delete(`${API}/rh/funcionarios/${id}`);
      toast.success("Funcionário excluído!");
      fetchFuncionarios();
    } catch (error) {
      toast.error("Erro ao excluir");
    }
  };

  const openModal = (funcionario = null) => {
    if (funcionario) {
      setEditingFuncionario(funcionario);
      setAnexos(funcionario.anexos || []);
      setFormData({
        nome: funcionario.nome || "",
        cpf: funcionario.cpf || "",
        rg: funcionario.rg || "",
        data_nascimento: funcionario.data_nascimento || "",
        telefone: funcionario.telefone || "",
        celular: funcionario.celular || "",
        email: funcionario.email || "",
        cep: funcionario.cep || "",
        endereco: funcionario.endereco || "",
        numero: funcionario.numero || "",
        complemento: funcionario.complemento || "",
        bairro: funcionario.bairro || "",
        cidade: funcionario.cidade || "",
        uf: funcionario.uf || "",
        cargo: funcionario.cargo || "",
        funcao: funcionario.funcao || "",
        departamento: funcionario.departamento || "",
        salario: funcionario.salario?.toString() || "",
        data_admissao: funcionario.data_admissao || "",
        regime_contratacao: funcionario.regime_contratacao || "CLT",
        status: funcionario.status || "ativo",
        observacoes: funcionario.observacoes || ""
      });
    } else {
      setEditingFuncionario(null);
      setAnexos([]);
      setFormData({
        nome: "",
        cpf: "",
        rg: "",
        data_nascimento: "",
        telefone: "",
        celular: "",
        email: "",
        cep: "",
        endereco: "",
        numero: "",
        complemento: "",
        bairro: "",
        cidade: "",
        uf: "",
        cargo: "",
        funcao: "",
        departamento: "",
        salario: "",
        data_admissao: "",
        regime_contratacao: "CLT",
        status: "ativo",
        observacoes: ""
      });
    }
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setEditingFuncionario(null);
  };

  const filteredFuncionarios = funcionarios.filter(f =>
    f.nome?.toLowerCase().includes(search.toLowerCase()) ||
    f.cpf?.includes(search) ||
    f.cargo?.toLowerCase().includes(search.toLowerCase())
  );

  const formatCurrency = (value) => {
    return new Intl.NumberFormat("pt-BR", {
      style: "currency",
      currency: "BRL"
    }).format(value || 0);
  };

  const getStatusBadge = (status) => {
    const colors = {
      ativo: "bg-green-100 text-green-700",
      ferias: "bg-blue-100 text-blue-700",
      afastado: "bg-yellow-100 text-yellow-700",
      desligado: "bg-red-100 text-red-700"
    };
    const labels = {
      ativo: "Ativo",
      ferias: "Férias",
      afastado: "Afastado",
      desligado: "Desligado"
    };
    return (
      <span className={`px-2 py-1 rounded text-xs ${colors[status] || colors.ativo}`}>
        {labels[status] || status}
      </span>
    );
  };

  if (loading) {
    return <div className="flex items-center justify-center min-h-[400px]"><div className="spinner w-12 h-12"></div></div>;
  }

  return (
    <div data-testid="funcionarios-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Funcionários</h1>
          <p className="text-gray-500 mt-1">Gestão de colaboradores</p>
        </div>
        <Button onClick={() => openModal()} className="bg-[#10B981] hover:bg-[#059669]" data-testid="btn-novo-funcionario">
          <Plus size={18} className="mr-2" />Novo Funcionário
        </Button>
      </div>

      {/* Filtros */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6">
        <div className="relative md:col-span-2">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
          <Input
            placeholder="Buscar por nome, CPF, cargo..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-10"
            data-testid="search-funcionarios"
          />
        </div>
        <Select value={filterStatus || "all"} onValueChange={(v) => setFilterStatus(v === "all" ? "" : v)}>
          <SelectTrigger className="h-11"><SelectValue placeholder="Todos os status" /></SelectTrigger>
          <SelectContent className="z-[9999]">
            <SelectItem value="all">Todos os status</SelectItem>
            {statusOptions.map(s => (
              <SelectItem key={s.value} value={s.value}>{s.label}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={filterRegime || "all"} onValueChange={(v) => setFilterRegime(v === "all" ? "" : v)}>
          <SelectTrigger className="h-11"><SelectValue placeholder="Todos os regimes" /></SelectTrigger>
          <SelectContent className="z-[9999]">
            <SelectItem value="all">Todos os regimes</SelectItem>
            {regimesContratacao.map(r => (
              <SelectItem key={r.value} value={r.value}>{r.label}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Button className="h-11 bg-[#10B981] hover:bg-[#059669]">
          <Search size={16} className="mr-2" />
          Buscar
        </Button>
      </div>

      {/* Cards de resumo */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-bold text-[#10B981]">{funcionarios.filter(f => f.status === 'ativo').length}</p>
            <p className="text-sm text-gray-500">Ativos</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-bold text-blue-600">{funcionarios.filter(f => f.status === 'ferias').length}</p>
            <p className="text-sm text-gray-500">Férias</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-bold text-yellow-600">{funcionarios.filter(f => f.status === 'afastado').length}</p>
            <p className="text-sm text-gray-500">Afastados</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-bold text-gray-600">{funcionarios.length}</p>
            <p className="text-sm text-gray-500">Total</p>
          </CardContent>
        </Card>
      </div>

      {/* Lista */}
      {filteredFuncionarios.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-gray-400">
            <Users className="mx-auto mb-4" size={48} />
            <p>Nenhum funcionário encontrado</p>
          </CardContent>
        </Card>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full border-collapse bg-white rounded-lg overflow-hidden shadow">
            <thead className="bg-gray-100">
              <tr>
                <th className="text-left p-3 text-sm font-medium text-gray-600">Nome</th>
                <th className="text-left p-3 text-sm font-medium text-gray-600">CPF</th>
                <th className="text-left p-3 text-sm font-medium text-gray-600">Cargo</th>
                <th className="text-left p-3 text-sm font-medium text-gray-600">Regime</th>
                <th className="text-left p-3 text-sm font-medium text-gray-600">Salário</th>
                <th className="text-left p-3 text-sm font-medium text-gray-600">Admissão</th>
                <th className="text-left p-3 text-sm font-medium text-gray-600">Status</th>
                <th className="text-center p-3 text-sm font-medium text-gray-600">Ações</th>
              </tr>
            </thead>
            <tbody>
              {filteredFuncionarios.map((f) => (
                <tr 
                  key={f.id} 
                  className="border-t hover:bg-gray-50 cursor-pointer transition-colors"
                  onClick={() => openModal(f)}
                  data-testid={`funcionario-row-${f.id}`}
                >
                  <td className="p-3 text-sm font-medium">{f.nome}</td>
                  <td className="p-3 text-sm font-mono">{f.cpf || "-"}</td>
                  <td className="p-3 text-sm">{f.cargo || "-"}</td>
                  <td className="p-3 text-sm">
                    <span className="px-2 py-1 bg-gray-100 rounded text-xs">{f.regime_contratacao}</span>
                  </td>
                  <td className="p-3 text-sm font-medium">{formatCurrency(f.salario)}</td>
                  <td className="p-3 text-sm">{f.data_admissao ? new Date(f.data_admissao).toLocaleDateString('pt-BR') : "-"}</td>
                  <td className="p-3 text-sm">{getStatusBadge(f.status)}</td>
                  <td className="p-3 text-center" onClick={(e) => e.stopPropagation()}>
                    <div className="flex justify-center gap-1">
                      <Button size="sm" variant="outline" onClick={() => openModal(f)}><Edit size={14} /></Button>
                      <Button size="sm" variant="outline" className="text-red-600" onClick={() => handleDelete(f.id)}><Trash2 size={14} /></Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Modal de Cadastro/Edição */}
      <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{editingFuncionario ? "Editar Funcionário" : "Novo Funcionário"}</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Dados Pessoais */}
            <div className="border-b pb-4">
              <h3 className="font-semibold text-lg mb-3 flex items-center gap-2">
                <User size={18} className="text-[#10B981]" />
                Dados Pessoais
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                <div className="col-span-2 md:col-span-1">
                  <Label>Nome Completo *</Label>
                  <Input value={formData.nome} onChange={(e) => setFormData({...formData, nome: e.target.value})} required />
                </div>
                <div>
                  <Label>CPF *</Label>
                  <Input value={formData.cpf} onChange={(e) => setFormData({...formData, cpf: e.target.value})} placeholder="000.000.000-00" required />
                </div>
                <div>
                  <Label>RG</Label>
                  <Input value={formData.rg} onChange={(e) => setFormData({...formData, rg: e.target.value})} />
                </div>
                <div>
                  <Label>Data de Nascimento</Label>
                  <Input type="date" value={formData.data_nascimento} onChange={(e) => setFormData({...formData, data_nascimento: e.target.value})} />
                </div>
                <div>
                  <Label>Telefone</Label>
                  <Input value={formData.telefone} onChange={(e) => setFormData({...formData, telefone: e.target.value})} placeholder="(00) 0000-0000" />
                </div>
                <div>
                  <Label>Celular</Label>
                  <Input value={formData.celular} onChange={(e) => setFormData({...formData, celular: e.target.value})} placeholder="(00) 00000-0000" />
                </div>
                <div className="col-span-2 md:col-span-1">
                  <Label>Email</Label>
                  <Input type="email" value={formData.email} onChange={(e) => setFormData({...formData, email: e.target.value})} />
                </div>
              </div>
            </div>

            {/* Endereço */}
            <div className="border-b pb-4">
              <h3 className="font-semibold text-lg mb-3 flex items-center gap-2">
                <MapPin size={18} className="text-[#10B981]" />
                Endereço
              </h3>
              <div className="grid grid-cols-6 gap-4">
                <div>
                  <Label>CEP</Label>
                  <div className="flex gap-1">
                    <Input 
                      value={formData.cep} 
                      onChange={(e) => setFormData({...formData, cep: e.target.value})} 
                      placeholder="00000-000" 
                      className="flex-1"
                    />
                    <Button 
                      type="button" 
                      size="sm" 
                      variant="outline"
                      onClick={handleConsultaCep}
                      disabled={consultandoCep}
                      className="text-[#10B981] border-[#10B981] hover:bg-[#10B981] hover:text-white px-2"
                      title="Buscar endereço"
                    >
                      {consultandoCep ? <Loader2 size={14} className="animate-spin" /> : <Search size={14} />}
                    </Button>
                  </div>
                </div>
                <div className="col-span-3">
                  <Label>Endereço</Label>
                  <Input value={formData.endereco} onChange={(e) => setFormData({...formData, endereco: e.target.value})} />
                </div>
                <div>
                  <Label>Número</Label>
                  <Input value={formData.numero} onChange={(e) => setFormData({...formData, numero: e.target.value})} />
                </div>
                <div>
                  <Label>Complemento</Label>
                  <Input value={formData.complemento} onChange={(e) => setFormData({...formData, complemento: e.target.value})} />
                </div>
                <div className="col-span-2">
                  <Label>Bairro</Label>
                  <Input value={formData.bairro} onChange={(e) => setFormData({...formData, bairro: e.target.value})} />
                </div>
                <div className="col-span-2">
                  <Label>Cidade</Label>
                  <Input value={formData.cidade} onChange={(e) => setFormData({...formData, cidade: e.target.value})} />
                </div>
                <div>
                  <Label>UF</Label>
                  <Input value={formData.uf} onChange={(e) => setFormData({...formData, uf: e.target.value})} maxLength={2} />
                </div>
              </div>
            </div>

            {/* Dados Profissionais */}
            <div className="border-b pb-4">
              <h3 className="font-semibold text-lg mb-3 flex items-center gap-2">
                <Briefcase size={18} className="text-[#10B981]" />
                Dados Profissionais
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <Label>Cargo *</Label>
                  <Input value={formData.cargo} onChange={(e) => setFormData({...formData, cargo: e.target.value})} required />
                </div>
                <div>
                  <Label>Função</Label>
                  <Input value={formData.funcao} onChange={(e) => setFormData({...formData, funcao: e.target.value})} />
                </div>
                <div>
                  <Label>Departamento</Label>
                  <Input value={formData.departamento} onChange={(e) => setFormData({...formData, departamento: e.target.value})} />
                </div>
                <div>
                  <Label>Salário *</Label>
                  <Input type="number" step="0.01" value={formData.salario} onChange={(e) => setFormData({...formData, salario: e.target.value})} required />
                </div>
                <div>
                  <Label>Data de Admissão *</Label>
                  <Input type="date" value={formData.data_admissao} onChange={(e) => setFormData({...formData, data_admissao: e.target.value})} required />
                </div>
                <div>
                  <Label>Regime de Contratação *</Label>
                  <Select value={formData.regime_contratacao} onValueChange={(v) => setFormData({...formData, regime_contratacao: v})}>
                    <SelectTrigger className="w-full h-11"><SelectValue /></SelectTrigger>
                    <SelectContent className="z-[9999]">
                      {regimesContratacao.map(r => <SelectItem key={r.value} value={r.value}>{r.label}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Status *</Label>
                  <Select value={formData.status} onValueChange={(v) => setFormData({...formData, status: v})}>
                    <SelectTrigger className="w-full h-11"><SelectValue /></SelectTrigger>
                    <SelectContent className="z-[9999]">
                      {statusOptions.map(s => <SelectItem key={s.value} value={s.value}>{s.label}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </div>

            {/* Observações */}
            <div>
              <Label>Observações</Label>
              <Textarea 
                value={formData.observacoes} 
                onChange={(e) => setFormData({...formData, observacoes: e.target.value})} 
                rows={3}
              />
            </div>

            {/* Anexos - só aparece ao editar */}
            {editingFuncionario && (
              <div className="border-t pt-4">
                <div className="flex items-center justify-between mb-3">
                  <Label className="flex items-center gap-2 mb-0">
                    <Paperclip size={16} /> Anexos ({anexos.length})
                  </Label>
                  <Button 
                    type="button" 
                    size="sm" 
                    variant="outline"
                    onClick={() => fileInputRef.current?.click()}
                    disabled={uploadingAnexo}
                  >
                    {uploadingAnexo ? <Loader2 size={14} className="animate-spin mr-1" /> : <Plus size={14} className="mr-1" />}
                    Anexar
                  </Button>
                  <input
                    ref={fileInputRef}
                    type="file"
                    multiple
                    className="hidden"
                    onChange={handleUploadAnexo}
                  />
                </div>
                
                {anexos.length > 0 && (
                  <div className="space-y-2 max-h-40 overflow-y-auto">
                    {anexos.map((anexo) => {
                      const ext = anexo.filename?.split('.').pop()?.toLowerCase() || '';
                      const isImage = ['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(ext);
                      const isPdf = ext === 'pdf';
                      const canPreview = isImage || isPdf;
                      
                      return (
                        <div key={anexo.id} className="flex items-center justify-between p-2 bg-gray-50 rounded-lg">
                          <div className="flex items-center gap-2 flex-1 min-w-0">
                            {isImage ? <ImageIcon size={16} className="text-blue-500" /> : <FileText size={16} className="text-gray-500" />}
                            <span className="text-sm truncate">{anexo.original_name || anexo.filename}</span>
                          </div>
                          <div className="flex items-center gap-1">
                            {canPreview && (
                              <Button type="button" size="sm" variant="ghost" onClick={() => handleViewAnexo(anexo)} title="Visualizar">
                                <Eye size={14} className="text-[#10B981]" />
                              </Button>
                            )}
                            <Button type="button" size="sm" variant="ghost" onClick={() => handleDownloadAnexo(anexo)} title="Baixar">
                              <Download size={14} className="text-gray-500" />
                            </Button>
                            <Button type="button" size="sm" variant="ghost" onClick={() => handleDeleteAnexo(anexo.id)} title="Excluir">
                              <Trash2 size={14} className="text-red-500" />
                            </Button>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            )}

            <DialogFooter className="gap-2">
              <Button type="button" variant="outline" onClick={closeModal}>Cancelar</Button>
              <Button type="submit" className="bg-[#10B981] hover:bg-[#059669]">{editingFuncionario ? "Atualizar" : "Cadastrar"}</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Modal de Preview */}
      <Dialog open={previewModal.open} onOpenChange={(open) => setPreviewModal({ ...previewModal, open })}>
        <DialogContent className="max-w-4xl max-h-[90vh]">
          <DialogHeader>
            <DialogTitle>{previewModal.name}</DialogTitle>
          </DialogHeader>
          <div className="flex items-center justify-center min-h-[400px] bg-gray-100 rounded-lg overflow-auto">
            {previewModal.type === 'image' && previewModal.url && (
              <img src={previewModal.url} alt={previewModal.name} className="max-w-full max-h-[70vh] object-contain" />
            )}
            {previewModal.type === 'pdf' && previewModal.url && (
              <iframe src={previewModal.url} className="w-full h-[70vh]" title="PDF Preview" />
            )}
            {previewModal.type === 'other' && (
              <p className="text-gray-500">Preview não disponível para este tipo de arquivo</p>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setPreviewModal({ open: false, url: null, name: null, type: null })}>
              Fechar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
