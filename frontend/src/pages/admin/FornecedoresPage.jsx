import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "@/App";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { 
  Plus, 
  Search, 
  Users,
  Phone,
  Mail,
  MapPin,
  Edit,
  Trash2,
  Building
} from "lucide-react";
import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

export default function FornecedoresPage() {
  const [fornecedores, setFornecedores] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingFornecedor, setEditingFornecedor] = useState(null);
  const [formData, setFormData] = useState({
    nome: "",
    cnpj: "",
    email: "",
    telefone: "",
    endereco: "",
    cidade: "",
    estado: "",
    observacoes: ""
  });

  useEffect(() => {
    fetchFornecedores();
  }, []);

  const fetchFornecedores = async () => {
    try {
      const response = await axios.get(`${API}/admin/fornecedores`);
      setFornecedores(response.data);
    } catch (error) {
      console.error("Erro ao carregar fornecedores:", error);
      toast.error("Erro ao carregar fornecedores");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingFornecedor) {
        await axios.put(`${API}/admin/fornecedores/${editingFornecedor.id}`, formData);
        toast.success("Fornecedor atualizado com sucesso!");
      } else {
        await axios.post(`${API}/admin/fornecedores`, formData);
        toast.success("Fornecedor cadastrado com sucesso!");
      }
      fetchFornecedores();
      closeModal();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao salvar fornecedor");
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Deseja realmente excluir este fornecedor?")) return;
    try {
      await axios.delete(`${API}/admin/fornecedores/${id}`);
      toast.success("Fornecedor excluído com sucesso!");
      fetchFornecedores();
    } catch (error) {
      toast.error("Erro ao excluir fornecedor");
    }
  };

  const openModal = (fornecedor = null) => {
    if (fornecedor) {
      setEditingFornecedor(fornecedor);
      setFormData({
        nome: fornecedor.nome,
        cnpj: fornecedor.cnpj || "",
        email: fornecedor.email || "",
        telefone: fornecedor.telefone || "",
        endereco: fornecedor.endereco || "",
        cidade: fornecedor.cidade || "",
        estado: fornecedor.estado || "",
        observacoes: fornecedor.observacoes || ""
      });
    } else {
      setEditingFornecedor(null);
      setFormData({
        nome: "",
        cnpj: "",
        email: "",
        telefone: "",
        endereco: "",
        cidade: "",
        estado: "",
        observacoes: ""
      });
    }
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setEditingFornecedor(null);
  };

  const filteredFornecedores = fornecedores.filter(f =>
    f.nome.toLowerCase().includes(search.toLowerCase()) ||
    (f.cnpj && f.cnpj.includes(search)) ||
    (f.cidade && f.cidade.toLowerCase().includes(search.toLowerCase()))
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="spinner w-12 h-12"></div>
      </div>
    );
  }

  return (
    <div data-testid="fornecedores-page">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Fornecedores</h1>
          <p className="text-slate-500 mt-1">Cadastro de fornecedores</p>
        </div>
        <Button onClick={() => openModal()} className="bg-[#FFC232] hover:bg-[#FFC232]" data-testid="new-fornecedor-btn">
          <Plus size={18} className="mr-2" />
          Novo Fornecedor
        </Button>
      </div>

      {/* Search */}
      <div className="relative mb-6">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400" size={20} />
        <Input
          placeholder="Buscar por nome, CNPJ ou cidade..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pl-10"
          data-testid="search-fornecedores"
        />
      </div>

      {/* Lista */}
      {filteredFornecedores.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-slate-400">
            <Users className="mx-auto mb-4" size={48} />
            <p className="font-medium">Nenhum fornecedor encontrado</p>
            <p className="text-sm">Cadastre um novo fornecedor</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filteredFornecedores.map((fornecedor) => (
            <Card key={fornecedor.id} className="hover:shadow-md transition-shadow" data-testid={`fornecedor-${fornecedor.id}`}>
              <CardContent className="p-4">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                      <Building className="text-[#FFC232]" size={20} />
                    </div>
                    <div>
                      <h3 className="font-medium text-slate-900">{fornecedor.nome}</h3>
                      {fornecedor.cnpj && (
                        <p className="text-xs text-slate-500">CNPJ: {fornecedor.cnpj}</p>
                      )}
                    </div>
                  </div>
                </div>
                
                <div className="space-y-1 text-sm text-slate-600 mb-3">
                  {fornecedor.telefone && (
                    <p className="flex items-center gap-2">
                      <Phone size={14} className="text-slate-400" />
                      {fornecedor.telefone}
                    </p>
                  )}
                  {fornecedor.email && (
                    <p className="flex items-center gap-2">
                      <Mail size={14} className="text-slate-400" />
                      {fornecedor.email}
                    </p>
                  )}
                  {(fornecedor.cidade || fornecedor.estado) && (
                    <p className="flex items-center gap-2">
                      <MapPin size={14} className="text-slate-400" />
                      {[fornecedor.cidade, fornecedor.estado].filter(Boolean).join(" - ")}
                    </p>
                  )}
                </div>

                <div className="flex gap-2 pt-2 border-t">
                  <Button size="sm" variant="outline" className="flex-1" onClick={() => openModal(fornecedor)}>
                    <Edit size={14} className="mr-1" /> Editar
                  </Button>
                  <Button 
                    size="sm" 
                    variant="outline" 
                    className="text-red-600 hover:bg-red-50"
                    onClick={() => handleDelete(fornecedor.id)}
                  >
                    <Trash2 size={14} />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Modal */}
      <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>{editingFornecedor ? "Editar Fornecedor" : "Novo Fornecedor"}</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="col-span-2">
                <label className="form-label">Nome / Razão Social *</label>
                <Input
                  value={formData.nome}
                  onChange={(e) => setFormData({...formData, nome: e.target.value})}
                  placeholder="Nome da empresa"
                  required
                  data-testid="input-nome-fornecedor"
                />
              </div>
              <div>
                <label className="form-label">CNPJ</label>
                <Input
                  value={formData.cnpj}
                  onChange={(e) => setFormData({...formData, cnpj: e.target.value})}
                  placeholder="00.000.000/0000-00"
                  data-testid="input-cnpj"
                />
              </div>
              <div>
                <label className="form-label">Telefone</label>
                <Input
                  value={formData.telefone}
                  onChange={(e) => setFormData({...formData, telefone: e.target.value})}
                  placeholder="(00) 00000-0000"
                  data-testid="input-telefone"
                />
              </div>
              <div className="col-span-2">
                <label className="form-label">Email</label>
                <Input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({...formData, email: e.target.value})}
                  placeholder="contato@empresa.com"
                  data-testid="input-email-fornecedor"
                />
              </div>
              <div className="col-span-2">
                <label className="form-label">Endereço</label>
                <Input
                  value={formData.endereco}
                  onChange={(e) => setFormData({...formData, endereco: e.target.value})}
                  placeholder="Rua, número, bairro"
                  data-testid="input-endereco"
                />
              </div>
              <div>
                <label className="form-label">Cidade</label>
                <Input
                  value={formData.cidade}
                  onChange={(e) => setFormData({...formData, cidade: e.target.value})}
                  placeholder="Cidade"
                  data-testid="input-cidade"
                />
              </div>
              <div>
                <label className="form-label">Estado</label>
                <Input
                  value={formData.estado}
                  onChange={(e) => setFormData({...formData, estado: e.target.value})}
                  placeholder="UF"
                  maxLength={2}
                  data-testid="input-estado"
                />
              </div>
              <div className="col-span-2">
                <label className="form-label">Observações</label>
                <Input
                  value={formData.observacoes}
                  onChange={(e) => setFormData({...formData, observacoes: e.target.value})}
                  placeholder="Observações adicionais"
                  data-testid="input-obs-fornecedor"
                />
              </div>
            </div>
            <div className="flex gap-3 pt-2">
              <Button type="button" variant="outline" onClick={closeModal} className="flex-1">
                Cancelar
              </Button>
              <Button type="submit" className="flex-1 bg-[#FFC232] hover:bg-[#FFC232]" data-testid="submit-fornecedor">
                {editingFornecedor ? "Atualizar" : "Cadastrar"}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
