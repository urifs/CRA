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
    { value: "transportador", label: "Transportador" },
    { value: "funcionario", label: "Funcionário" }
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
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
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
                <tr key={c.id} className="border-t hover:bg-white">
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
                  <td className="p-3 text-center">
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
                <Input value={formData.cpf_cnpj} onChange={(e) => setFormData({...formData, cpf_cnpj: e.target.value})} placeholder={formData.tipo_pessoa === "PJ" ? "00.000.000/0000-00" : "000.000.000-00"} />
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
                <Input value={formData.cep} onChange={(e) => setFormData({...formData, cep: e.target.value})} placeholder="00000-000" />
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

            <div className="flex gap-3 pt-4">
              <Button type="button" variant="outline" onClick={closeModal} className="flex-1">Cancelar</Button>
              <Button type="submit" className="flex-1 bg-[#D4A000] hover:bg-[#D4A000]">{editingCadastro ? "Atualizar" : "Cadastrar"}</Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
