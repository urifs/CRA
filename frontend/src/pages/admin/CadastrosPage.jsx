import { useState, useEffect, useRef } from "react";
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
  Plus, Search, Users, Phone, Mail, MapPin, Edit, Trash2, Building, User, Filter,
  Paperclip, Eye, Download, X, FileText, Image as ImageIcon, Loader2
} from "lucide-react";
import { toast } from "sonner";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter,
} from "@/components/ui/dialog";
import { formatCPF, formatCNPJ, formatCEP, formatTelefone } from "@/utils/masks";

export default function CadastrosPage() {
  const [cadastros, setCadastros] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [filterTipo, setFilterTipo] = useState("");
  const [filterStatus, setFilterStatus] = useState("");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingCadastro, setEditingCadastro] = useState(null);
  
  // Anexos
  const [anexos, setAnexos] = useState([]);
  const [uploadingAnexo, setUploadingAnexo] = useState(false);
  const [previewModal, setPreviewModal] = useState({ open: false, url: null, name: null, type: null });
  const fileInputRef = useRef(null);
  
  // Consultas
  const [consultandoCnpj, setConsultandoCnpj] = useState(false);
  const [consultandoCep, setConsultandoCep] = useState(false);
  
  const [formData, setFormData] = useState({
    tipo_cadastro: "cliente",
    tipo_pessoa: "PF",
    status: "ativo",
    nome_razao: "",
    apelido_fantasia: "",
    cpf_cnpj: "",
    rg_ie: "",
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
    grupo: "",
    rota: "",
    vendedor: "",
    limite_credito: "",
    observacoes: ""
  });

  const tiposCadastro = [
    { value: "cliente", label: "Cliente" },
    { value: "fornecedor", label: "Fornecedor" },
    { value: "cli_forn", label: "Cliente/Fornecedor" },
    { value: "transportador", label: "Transportador" }
  ];

  useEffect(() => {
    fetchCadastros();
  }, [filterTipo, filterStatus]);

  const fetchCadastros = async () => {
    try {
      let url = `${API}/admin/cadastros`;
      const params = new URLSearchParams();
      if (filterTipo) params.append("tipo", filterTipo);
      if (filterStatus) params.append("status", filterStatus);
      if (params.toString()) url += `?${params.toString()}`;
      
      const response = await axios.get(url);
      setCadastros(response.data);
    } catch (error) {
      toast.error("Erro ao carregar cadastros");
    } finally {
      setLoading(false);
    }
  };

  const handleUploadAnexo = async (e) => {
    const files = e.target.files;
    if (!files?.length || !editingCadastro?.id) return;
    
    setUploadingAnexo(true);
    try {
      for (const file of files) {
        const formDataFile = new FormData();
        formDataFile.append("file", file);
        await axios.post(`${API}/admin/cadastros/${editingCadastro.id}/anexos`, formDataFile, {
          headers: { "Content-Type": "multipart/form-data" }
        });
      }
      toast.success("Anexo(s) adicionado(s)!");
      // Refresh cadastro to get updated anexos
      const response = await axios.get(`${API}/admin/cadastros/${editingCadastro.id}`);
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
      await axios.delete(`${API}/admin/cadastros/${editingCadastro.id}/anexos/${anexoId}`);
      setAnexos(anexos.filter(a => a.id !== anexoId));
      toast.success("Anexo excluído!");
    } catch (error) {
      toast.error("Erro ao excluir anexo");
    }
  };

  const handleViewAnexo = (anexo) => {
    const url = `${API.replace('/api', '')}/uploads/cadastros/${anexo.filename}`;
    const ext = anexo.filename.split('.').pop().toLowerCase();
    const isImage = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg'].includes(ext);
    const isPdf = ext === 'pdf';
    setPreviewModal({ open: true, url, name: anexo.original_name || anexo.filename, type: isImage ? 'image' : isPdf ? 'pdf' : 'other' });
  };

  const handleDownloadAnexo = async (anexo) => {
    try {
      const response = await axios.get(`${API}/admin/cadastros/${editingCadastro.id}/anexos/${anexo.id}/download`, {
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

  const handleConsultaCnpj = async () => {
    const cnpj = formData.cpf_cnpj.replace(/\D/g, '');
    if (cnpj.length !== 14) {
      toast.error("CNPJ deve ter 14 dígitos");
      return;
    }
    
    setConsultandoCnpj(true);
    try {
      const response = await axios.get(`${API}/consulta/cnpj/${cnpj}`);
      const dados = response.data.data;
      
      setFormData(prev => ({
        ...prev,
        nome_razao: dados.razao_social || prev.nome_razao,
        apelido_fantasia: dados.nome_fantasia || prev.apelido_fantasia,
        rg_ie: dados.inscricao_estadual || prev.rg_ie,
        telefone: dados.telefone || prev.telefone,
        email: dados.email || prev.email,
        cep: dados.cep || prev.cep,
        endereco: dados.endereco || prev.endereco,
        numero: dados.numero || prev.numero,
        complemento: dados.complemento || prev.complemento,
        bairro: dados.bairro || prev.bairro,
        cidade: dados.cidade || prev.cidade,
        uf: dados.uf || prev.uf
      }));
      
      toast.success("Dados preenchidos automaticamente!");
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao consultar CNPJ");
    } finally {
      setConsultandoCnpj(false);
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

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const dataToSend = {
        ...formData,
        limite_credito: formData.limite_credito ? parseFloat(formData.limite_credito) : null
      };
      
      if (editingCadastro) {
        await axios.put(`${API}/admin/cadastros/${editingCadastro.id}`, dataToSend);
        toast.success("Cadastro atualizado!");
      } else {
        await axios.post(`${API}/admin/cadastros`, dataToSend);
        toast.success("Cadastro criado!");
      }
      fetchCadastros();
      closeModal();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao salvar");
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Deseja excluir este cadastro?")) return;
    try {
      await axios.delete(`${API}/admin/cadastros/${id}`);
      toast.success("Cadastro excluído!");
      fetchCadastros();
    } catch (error) {
      toast.error("Erro ao excluir");
    }
  };

  const openModal = (cadastro = null) => {
    if (cadastro) {
      setEditingCadastro(cadastro);
      setAnexos(cadastro.anexos || []);
      setFormData({
        tipo_cadastro: cadastro.tipo_cadastro || "cliente",
        tipo_pessoa: cadastro.tipo_pessoa || "PF",
        status: cadastro.status || "ativo",
        nome_razao: cadastro.nome_razao || "",
        apelido_fantasia: cadastro.apelido_fantasia || "",
        cpf_cnpj: cadastro.cpf_cnpj || "",
        rg_ie: cadastro.rg_ie || "",
        telefone: cadastro.telefone || "",
        celular: cadastro.celular || "",
        email: cadastro.email || "",
        cep: cadastro.cep || "",
        endereco: cadastro.endereco || "",
        numero: cadastro.numero || "",
        complemento: cadastro.complemento || "",
        bairro: cadastro.bairro || "",
        cidade: cadastro.cidade || "",
        uf: cadastro.uf || "",
        grupo: cadastro.grupo || "",
        rota: cadastro.rota || "",
        vendedor: cadastro.vendedor || "",
        limite_credito: cadastro.limite_credito?.toString() || "",
        observacoes: cadastro.observacoes || ""
      });
    } else {
      setEditingCadastro(null);
      setAnexos([]);
      setFormData({
        tipo_cadastro: "cliente",
        tipo_pessoa: "PF",
        status: "ativo",
        nome_razao: "",
        apelido_fantasia: "",
        cpf_cnpj: "",
        rg_ie: "",
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
        grupo: "",
        rota: "",
        vendedor: "",
        limite_credito: "",
        observacoes: ""
      });
    }
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setEditingCadastro(null);
  };

  const filteredCadastros = cadastros.filter(c =>
    c.nome_razao?.toLowerCase().includes(search.toLowerCase()) ||
    c.apelido_fantasia?.toLowerCase().includes(search.toLowerCase()) ||
    c.cpf_cnpj?.includes(search) ||
    c.cidade?.toLowerCase().includes(search.toLowerCase())
  );

  const getTipoLabel = (tipo) => tiposCadastro.find(t => t.value === tipo)?.label || tipo;

  if (loading) {
    return <div className="flex items-center justify-center min-h-[400px]"><div className="spinner w-12 h-12"></div></div>;
  }

  return (
    <div data-testid="cadastros-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Cadastros</h1>
          <p className="text-gray-500 mt-1">Clientes, Fornecedores, Transportadores</p>
        </div>
        <Button onClick={() => openModal()} className="bg-[#D4A000] hover:bg-[#D4A000]">
          <Plus size={18} className="mr-2" />Novo Cadastro
        </Button>
      </div>

      {/* Filtros */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6">
        <div className="relative md:col-span-2">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
          <Input
            placeholder="Buscar por nome, CPF/CNPJ, cidade..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-10"
          />
        </div>
        <Select value={filterTipo || "all"} onValueChange={(v) => setFilterTipo(v === "all" ? "" : v)}>
          <SelectTrigger className="h-11"><SelectValue placeholder="Todos os tipos" /></SelectTrigger>
          <SelectContent className="z-[9999]">
            <SelectItem value="all">Todos os tipos</SelectItem>
            {tiposCadastro.map(t => (
              <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={filterStatus || "all"} onValueChange={(v) => setFilterStatus(v === "all" ? "" : v)}>
          <SelectTrigger className="h-11"><SelectValue placeholder="Todos os status" /></SelectTrigger>
          <SelectContent className="z-[9999]">
            <SelectItem value="all">Todos os status</SelectItem>
            <SelectItem value="ativo">Ativo</SelectItem>
            <SelectItem value="inativo">Inativo</SelectItem>
          </SelectContent>
        </Select>
        <Button className="h-11 bg-[#D4A000] hover:bg-[#b38900] text-black">
          <Search size={16} className="mr-2" />
          Buscar
        </Button>
      </div>

      {/* Lista */}
      {filteredCadastros.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-gray-400">
            <Users className="mx-auto mb-4" size={48} />
            <p>Nenhum cadastro encontrado</p>
          </CardContent>
        </Card>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full border-collapse bg-white rounded-lg overflow-hidden shadow">
            <thead className="bg-gray-100">
              <tr>
                <th className="text-left p-3 text-sm font-medium text-gray-600">Cód.</th>
                <th className="text-left p-3 text-sm font-medium text-gray-600">Nome/Razão Social</th>
                <th className="text-left p-3 text-sm font-medium text-gray-600">Fantasia</th>
                <th className="text-left p-3 text-sm font-medium text-gray-600">CPF/CNPJ</th>
                <th className="text-left p-3 text-sm font-medium text-gray-600">Telefone</th>
                <th className="text-left p-3 text-sm font-medium text-gray-600">Cidade</th>
                <th className="text-left p-3 text-sm font-medium text-gray-600">UF</th>
                <th className="text-left p-3 text-sm font-medium text-gray-600">Tipo</th>
                <th className="text-left p-3 text-sm font-medium text-gray-600">Status</th>
                <th className="text-center p-3 text-sm font-medium text-gray-600">Ações</th>
              </tr>
            </thead>
            <tbody>
              {filteredCadastros.map((c) => (
                <tr 
                  key={c.id} 
                  className="border-t hover:bg-gray-50 cursor-pointer transition-colors"
                  onClick={() => openModal(c)}
                >
                  <td className="p-3 text-sm font-mono">{c.codigo}</td>
                  <td className="p-3 text-sm font-medium">{c.nome_razao}</td>
                  <td className="p-3 text-sm text-gray-600">{c.apelido_fantasia || "-"}</td>
                  <td className="p-3 text-sm font-mono">{c.cpf_cnpj || "-"}</td>
                  <td className="p-3 text-sm">{c.telefone || c.celular || "-"}</td>
                  <td className="p-3 text-sm">{c.cidade || "-"}</td>
                  <td className="p-3 text-sm">{c.uf || "-"}</td>
                  <td className="p-3 text-sm">
                    <span className="px-2 py-1 bg-gray-100 rounded text-xs">{getTipoLabel(c.tipo_cadastro)}</span>
                  </td>
                  <td className="p-3 text-sm">
                    <span className={`px-2 py-1 rounded text-xs ${c.status === 'ativo' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                      {c.status === 'ativo' ? 'Ativo' : 'Inativo'}
                    </span>
                  </td>
                  <td className="p-3 text-center" onClick={(e) => e.stopPropagation()}>
                    <div className="flex justify-center gap-1">
                      <Button size="sm" variant="outline" onClick={() => openModal(c)}><Edit size={14} /></Button>
                      <Button size="sm" variant="outline" className="text-red-600" onClick={() => handleDelete(c.id)}><Trash2 size={14} /></Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Modal */}
      <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{editingCadastro ? "Editar Cadastro" : "Novo Cadastro"}</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Tipo e Status */}
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="form-label">Tipo de Cadastro *</label>
                <Select value={formData.tipo_cadastro} onValueChange={(v) => setFormData({...formData, tipo_cadastro: v})}>
                  <SelectTrigger className="w-full h-11"><SelectValue /></SelectTrigger>
                  <SelectContent className="z-[9999]">
                    {tiposCadastro.map(t => <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="form-label">Pessoa *</label>
                <Select value={formData.tipo_pessoa} onValueChange={(v) => setFormData({...formData, tipo_pessoa: v})}>
                  <SelectTrigger className="w-full h-11"><SelectValue /></SelectTrigger>
                  <SelectContent className="z-[9999]">
                    <SelectItem value="PF">Pessoa Física</SelectItem>
                    <SelectItem value="PJ">Pessoa Jurídica</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="form-label">Status *</label>
                <Select value={formData.status} onValueChange={(v) => setFormData({...formData, status: v})}>
                  <SelectTrigger className="w-full h-11"><SelectValue /></SelectTrigger>
                  <SelectContent className="z-[9999]">
                    <SelectItem value="ativo">Ativo</SelectItem>
                    <SelectItem value="inativo">Inativo</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Dados principais */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="form-label">{formData.tipo_pessoa === "PJ" ? "Razão Social" : "Nome"} *</label>
                <Input value={formData.nome_razao} onChange={(e) => setFormData({...formData, nome_razao: e.target.value})} required />
              </div>
              <div>
                <label className="form-label">{formData.tipo_pessoa === "PJ" ? "Nome Fantasia" : "Apelido"}</label>
                <Input value={formData.apelido_fantasia} onChange={(e) => setFormData({...formData, apelido_fantasia: e.target.value})} />
              </div>
              <div>
                <label className="form-label">{formData.tipo_pessoa === "PJ" ? "CNPJ" : "CPF"}</label>
                <div className="flex gap-2">
                  <Input 
                    value={formData.cpf_cnpj} 
                    onChange={(e) => setFormData({...formData, cpf_cnpj: formData.tipo_pessoa === "PJ" ? formatCNPJ(e.target.value) : formatCPF(e.target.value)})} 
                    placeholder={formData.tipo_pessoa === "PJ" ? "00.000.000/0000-00" : "000.000.000-00"} 
                    className="flex-1"
                  />
                  {formData.tipo_pessoa === "PJ" && (
                    <Button 
                      type="button" 
                      size="sm" 
                      variant="outline"
                      onClick={handleConsultaCnpj}
                      disabled={consultandoCnpj}
                      className="text-[#D4A000] border-[#D4A000] hover:bg-[#D4A000] hover:text-white"
                      title="Consultar CNPJ e preencher dados"
                    >
                      {consultandoCnpj ? <Loader2 size={14} className="animate-spin" /> : <Search size={14} />}
                    </Button>
                  )}
                </div>
                {formData.tipo_pessoa === "PJ" && (
                  <p className="text-xs text-gray-500 mt-1">Clique na lupa para consultar e preencher automaticamente</p>
                )}
              </div>
              <div>
                <label className="form-label">{formData.tipo_pessoa === "PJ" ? "Inscrição Estadual" : "RG"}</label>
                <Input value={formData.rg_ie} onChange={(e) => setFormData({...formData, rg_ie: e.target.value})} />
              </div>
            </div>

            {/* Contato */}
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="form-label">Telefone</label>
                <Input value={formData.telefone} onChange={(e) => setFormData({...formData, telefone: e.target.value})} placeholder="(00) 0000-0000" />
              </div>
              <div>
                <label className="form-label">Celular</label>
                <Input value={formData.celular} onChange={(e) => setFormData({...formData, celular: e.target.value})} placeholder="(00) 00000-0000" />
              </div>
              <div>
                <label className="form-label">Email</label>
                <Input type="email" value={formData.email} onChange={(e) => setFormData({...formData, email: e.target.value})} />
              </div>
            </div>

            {/* Endereço */}
            <div className="grid grid-cols-6 gap-4">
              <div>
                <label className="form-label">CEP</label>
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
                    className="text-blue-600 border-blue-600 hover:bg-blue-600 hover:text-white px-2"
                    title="Buscar endereço pelo CEP"
                  >
                    {consultandoCep ? <Loader2 size={14} className="animate-spin" /> : <Search size={14} />}
                  </Button>
                </div>
              </div>
              <div className="col-span-3">
                <label className="form-label">Endereço</label>
                <Input value={formData.endereco} onChange={(e) => setFormData({...formData, endereco: e.target.value})} />
              </div>
              <div>
                <label className="form-label">Número</label>
                <Input value={formData.numero} onChange={(e) => setFormData({...formData, numero: e.target.value})} />
              </div>
              <div>
                <label className="form-label">Complemento</label>
                <Input value={formData.complemento} onChange={(e) => setFormData({...formData, complemento: e.target.value})} />
              </div>
              <div className="col-span-2">
                <label className="form-label">Bairro</label>
                <Input value={formData.bairro} onChange={(e) => setFormData({...formData, bairro: e.target.value})} />
              </div>
              <div className="col-span-2">
                <label className="form-label">Cidade</label>
                <Input value={formData.cidade} onChange={(e) => setFormData({...formData, cidade: e.target.value})} />
              </div>
              <div>
                <label className="form-label">UF</label>
                <Input value={formData.uf} onChange={(e) => setFormData({...formData, uf: e.target.value})} maxLength={2} />
              </div>
            </div>

            {/* Dados adicionais */}
            <div className="grid grid-cols-4 gap-4">
              <div>
                <label className="form-label">Grupo</label>
                <Input value={formData.grupo} onChange={(e) => setFormData({...formData, grupo: e.target.value})} />
              </div>
              <div>
                <label className="form-label">Rota</label>
                <Input value={formData.rota} onChange={(e) => setFormData({...formData, rota: e.target.value})} />
              </div>
              <div>
                <label className="form-label">Vendedor</label>
                <Input value={formData.vendedor} onChange={(e) => setFormData({...formData, vendedor: e.target.value})} />
              </div>
              <div>
                <label className="form-label">Limite de Crédito</label>
                <Input type="number" step="0.01" value={formData.limite_credito} onChange={(e) => setFormData({...formData, limite_credito: e.target.value})} />
              </div>
            </div>

            <div>
              <label className="form-label">Observações</label>
              <Input value={formData.observacoes} onChange={(e) => setFormData({...formData, observacoes: e.target.value})} />
            </div>

            {/* Anexos - só aparece ao editar */}
            {editingCadastro && (
              <div className="border-t pt-4">
                <div className="flex items-center justify-between mb-3">
                  <label className="form-label flex items-center gap-2 mb-0">
                    <Paperclip size={16} /> Anexos ({anexos.length})
                  </label>
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
                                <Eye size={14} className="text-[#D4A000]" />
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

            <div className="flex gap-3 pt-4">
              <Button type="button" variant="outline" onClick={closeModal} className="flex-1">Cancelar</Button>
              <Button type="submit" className="flex-1 bg-[#D4A000] hover:bg-[#D4A000]">{editingCadastro ? "Atualizar" : "Cadastrar"}</Button>
            </div>
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
