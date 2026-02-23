import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "@/App";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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
  Plus, Search, Edit, Trash2, Building2, CheckCircle2, XCircle
} from "lucide-react";
import { toast } from "sonner";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";

export default function CentroCustoPage() {
  const [centros, setCentros] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingCentro, setEditingCentro] = useState(null);
  const [formData, setFormData] = useState({
    codigo: "", nome: "", descricao: "", status: "ativo"
  });

  useEffect(() => { fetchCentros(); }, []);

  const fetchCentros = async () => {
    try {
      const response = await axios.get(`${API}/admin/centros-custo`);
      setCentros(response.data);
    } catch (error) { toast.error("Erro ao carregar centros de custo"); }
    finally { setLoading(false); }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingCentro) {
        await axios.put(`${API}/admin/centros-custo/${editingCentro.id}`, formData);
        toast.success("Centro de custo atualizado!");
      } else {
        await axios.post(`${API}/admin/centros-custo`, formData);
        toast.success("Centro de custo cadastrado!");
      }
      fetchCentros(); closeModal();
    } catch (error) { toast.error(error.response?.data?.detail || "Erro ao salvar"); }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Excluir este centro de custo?")) return;
    try {
      await axios.delete(`${API}/admin/centros-custo/${id}`);
      toast.success("Centro de custo excluído!"); fetchCentros();
    } catch (error) { toast.error(error.response?.data?.detail || "Erro ao excluir"); }
  };

  const openModal = (centro = null) => {
    if (centro) {
      setEditingCentro(centro);
      setFormData({
        codigo: centro.codigo || "",
        nome: centro.nome || "",
        descricao: centro.descricao || "",
        status: centro.status || "ativo"
      });
    } else {
      setEditingCentro(null);
      setFormData({ codigo: "", nome: "", descricao: "", status: "ativo" });
    }
    setIsModalOpen(true);
  };

  const closeModal = () => { setIsModalOpen(false); setEditingCentro(null); };

  const filteredCentros = centros.filter(c =>
    c.nome?.toLowerCase().includes(search.toLowerCase()) ||
    c.codigo?.toLowerCase().includes(search.toLowerCase()) ||
    c.descricao?.toLowerCase().includes(search.toLowerCase())
  );

  if (loading) return <div className="flex items-center justify-center min-h-[400px]"><div className="spinner w-12 h-12"></div></div>;

  return (
    <div data-testid="centro-custo-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Centros de Custo</h1>
          <p className="text-slate-500 mt-1">Gerencie os centros de custo da empresa</p>
        </div>
        <Button onClick={() => openModal()} className="bg-blue-600 hover:bg-blue-700" data-testid="new-centro-btn">
          <Plus size={18} className="mr-2" />Novo Centro
        </Button>
      </div>

      {/* Busca */}
      <div className="mb-6">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400" size={20} />
          <Input 
            placeholder="Buscar por código, nome ou descrição..." 
            value={search} 
            onChange={(e) => setSearch(e.target.value)} 
            className="pl-10" 
          />
        </div>
      </div>

      {/* Resumo */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <Card className="stat-card">
          <CardContent className="p-4 flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
              <Building2 className="text-blue-600" size={20} />
            </div>
            <div>
              <p className="text-xs text-slate-500">Total de Centros</p>
              <p className="text-lg font-bold text-blue-600">{centros.length}</p>
            </div>
          </CardContent>
        </Card>
        <Card className="stat-card">
          <CardContent className="p-4 flex items-center gap-3">
            <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
              <CheckCircle2 className="text-green-600" size={20} />
            </div>
            <div>
              <p className="text-xs text-slate-500">Ativos</p>
              <p className="text-lg font-bold text-green-600">{centros.filter(c => c.status === "ativo").length}</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Lista */}
      {filteredCentros.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-slate-400">
            <Building2 className="mx-auto mb-4" size={48} />
            <p>Nenhum centro de custo encontrado</p>
          </CardContent>
        </Card>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full border-collapse bg-white rounded-lg overflow-hidden shadow text-sm">
            <thead className="bg-slate-100">
              <tr>
                <th className="text-left p-3 font-medium text-slate-600">Código</th>
                <th className="text-left p-3 font-medium text-slate-600">Nome</th>
                <th className="text-left p-3 font-medium text-slate-600">Descrição</th>
                <th className="text-left p-3 font-medium text-slate-600">Status</th>
                <th className="text-center p-3 font-medium text-slate-600">Ações</th>
              </tr>
            </thead>
            <tbody>
              {filteredCentros.map((c) => (
                <tr key={c.id} className="border-t hover:bg-slate-50" data-testid={`centro-${c.id}`}>
                  <td className="p-3 font-mono">{c.codigo || "-"}</td>
                  <td className="p-3 font-medium">{c.nome}</td>
                  <td className="p-3 text-slate-500 max-w-[200px] truncate">{c.descricao || "-"}</td>
                  <td className="p-3">
                    {c.status === "ativo" ? (
                      <span className="px-2 py-1 rounded text-xs bg-green-100 text-green-700">
                        <CheckCircle2 className="inline mr-1" size={12} />Ativo
                      </span>
                    ) : (
                      <span className="px-2 py-1 rounded text-xs bg-slate-100 text-slate-600">
                        <XCircle className="inline mr-1" size={12} />Inativo
                      </span>
                    )}
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
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>{editingCentro ? "Editar Centro de Custo" : "Novo Centro de Custo"}</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="form-label">Código</label>
                <Input value={formData.codigo} onChange={(e) => setFormData({...formData, codigo: e.target.value})} placeholder="Ex: CC001" />
              </div>
              <div>
                <label className="form-label">Status</label>
                <select className="form-select" value={formData.status} onChange={(e) => setFormData({...formData, status: e.target.value})}>
                  <option value="ativo">Ativo</option>
                  <option value="inativo">Inativo</option>
                </select>
              </div>
            </div>
            <div>
              <label className="form-label">Nome *</label>
              <Input value={formData.nome} onChange={(e) => setFormData({...formData, nome: e.target.value})} required placeholder="Nome do centro de custo" />
            </div>
            <div>
              <label className="form-label">Descrição</label>
              <Input value={formData.descricao} onChange={(e) => setFormData({...formData, descricao: e.target.value})} placeholder="Descrição opcional" />
            </div>
            <div className="flex gap-3 pt-2">
              <Button type="button" variant="outline" onClick={closeModal} className="flex-1">Cancelar</Button>
              <Button type="submit" className="flex-1 bg-blue-600 hover:bg-blue-700">{editingCentro ? "Atualizar" : "Cadastrar"}</Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
