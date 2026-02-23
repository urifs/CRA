import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "@/App";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { 
  Plus, 
  DollarSign,
  FolderTree,
  ChevronRight,
  ChevronDown,
  Edit,
  Trash2,
  TrendingUp,
  TrendingDown
} from "lucide-react";
import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

export default function PlanoContasPage() {
  const [contas, setContas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingConta, setEditingConta] = useState(null);
  const [expandedGroups, setExpandedGroups] = useState(new Set(["receitas", "despesas"]));
  const [formData, setFormData] = useState({
    codigo: "",
    nome: "",
    tipo: "despesa",
    grupo: "",
    descricao: ""
  });

  useEffect(() => {
    fetchContas();
  }, []);

  const fetchContas = async () => {
    try {
      const response = await axios.get(`${API}/admin/plano-contas`);
      setContas(response.data);
    } catch (error) {
      console.error("Erro ao carregar plano de contas:", error);
      toast.error("Erro ao carregar plano de contas");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingConta) {
        await axios.put(`${API}/admin/plano-contas/${editingConta.id}`, formData);
        toast.success("Conta atualizada com sucesso!");
      } else {
        await axios.post(`${API}/admin/plano-contas`, formData);
        toast.success("Conta cadastrada com sucesso!");
      }
      fetchContas();
      closeModal();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao salvar conta");
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Deseja realmente excluir esta conta?")) return;
    try {
      await axios.delete(`${API}/admin/plano-contas/${id}`);
      toast.success("Conta excluída com sucesso!");
      fetchContas();
    } catch (error) {
      toast.error("Erro ao excluir conta");
    }
  };

  const openModal = (conta = null) => {
    if (conta) {
      setEditingConta(conta);
      setFormData({
        codigo: conta.codigo || "",
        nome: conta.nome,
        tipo: conta.tipo,
        grupo: conta.grupo || "",
        descricao: conta.descricao || ""
      });
    } else {
      setEditingConta(null);
      setFormData({
        codigo: "",
        nome: "",
        tipo: "despesa",
        grupo: "",
        descricao: ""
      });
    }
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setEditingConta(null);
  };

  const toggleGroup = (group) => {
    const newExpanded = new Set(expandedGroups);
    if (newExpanded.has(group)) {
      newExpanded.delete(group);
    } else {
      newExpanded.add(group);
    }
    setExpandedGroups(newExpanded);
  };

  // Group accounts by type
  const receitas = contas.filter(c => c.tipo === "receita");
  const despesas = contas.filter(c => c.tipo === "despesa");

  // Group by sub-group
  const groupByGrupo = (items) => {
    const groups = {};
    items.forEach(item => {
      const grupo = item.grupo || "Outros";
      if (!groups[grupo]) groups[grupo] = [];
      groups[grupo].push(item);
    });
    return groups;
  };

  const receitasAgrupadas = groupByGrupo(receitas);
  const despesasAgrupadas = groupByGrupo(despesas);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="spinner w-12 h-12"></div>
      </div>
    );
  }

  const renderGroup = (title, items, groupedItems, color, icon) => {
    const Icon = icon;
    const isExpanded = expandedGroups.has(title.toLowerCase());
    
    return (
      <Card className={`border-l-4 ${color}`}>
        <CardHeader 
          className="cursor-pointer hover:bg-slate-50"
          onClick={() => toggleGroup(title.toLowerCase())}
        >
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Icon size={20} />
              <span>{title}</span>
              <span className="text-sm font-normal text-slate-500">({items.length} contas)</span>
            </div>
            {isExpanded ? <ChevronDown size={20} /> : <ChevronRight size={20} />}
          </CardTitle>
        </CardHeader>
        {isExpanded && (
          <CardContent className="pt-0">
            {Object.keys(groupedItems).length === 0 ? (
              <p className="text-slate-400 text-center py-4">Nenhuma conta cadastrada</p>
            ) : (
              Object.entries(groupedItems).map(([grupo, contas]) => (
                <div key={grupo} className="mb-4 last:mb-0">
                  <h4 className="text-sm font-medium text-slate-600 mb-2 flex items-center gap-2">
                    <FolderTree size={14} />
                    {grupo}
                  </h4>
                  <div className="space-y-2 pl-4">
                    {contas.map((conta) => (
                      <div 
                        key={conta.id}
                        className="flex items-center justify-between p-2 bg-slate-50 rounded-lg hover:bg-slate-100"
                      >
                        <div className="flex items-center gap-2">
                          {conta.codigo && (
                            <span className="text-xs font-mono bg-slate-200 px-1.5 py-0.5 rounded">
                              {conta.codigo}
                            </span>
                          )}
                          <span className="text-sm font-medium">{conta.nome}</span>
                        </div>
                        <div className="flex gap-1">
                          <Button size="sm" variant="ghost" onClick={() => openModal(conta)}>
                            <Edit size={14} />
                          </Button>
                          <Button 
                            size="sm" 
                            variant="ghost" 
                            className="text-red-600 hover:bg-red-50"
                            onClick={() => handleDelete(conta.id)}
                          >
                            <Trash2 size={14} />
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))
            )}
          </CardContent>
        )}
      </Card>
    );
  };

  return (
    <div data-testid="plano-contas-page">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Plano de Contas</h1>
          <p className="text-slate-500 mt-1">Categorias financeiras para classificação</p>
        </div>
        <Button onClick={() => openModal()} className="bg-blue-600 hover:bg-blue-700" data-testid="new-plano-conta-btn">
          <Plus size={18} className="mr-2" />
          Nova Conta
        </Button>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <Card className="stat-card">
          <CardContent className="p-4 flex items-center gap-3">
            <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
              <TrendingUp className="text-green-600" size={20} />
            </div>
            <div>
              <p className="text-xs text-slate-500">Receitas</p>
              <p className="text-lg font-bold text-green-600">{receitas.length}</p>
            </div>
          </CardContent>
        </Card>
        <Card className="stat-card">
          <CardContent className="p-4 flex items-center gap-3">
            <div className="w-10 h-10 bg-red-100 rounded-lg flex items-center justify-center">
              <TrendingDown className="text-red-600" size={20} />
            </div>
            <div>
              <p className="text-xs text-slate-500">Despesas</p>
              <p className="text-lg font-bold text-red-600">{despesas.length}</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Accounts tree */}
      <div className="space-y-4">
        {renderGroup("Receitas", receitas, receitasAgrupadas, "border-l-green-500", TrendingUp)}
        {renderGroup("Despesas", despesas, despesasAgrupadas, "border-l-red-500", TrendingDown)}
      </div>

      {/* Modal */}
      <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>{editingConta ? "Editar Conta" : "Nova Conta Contábil"}</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="form-label">Código</label>
                <Input
                  value={formData.codigo}
                  onChange={(e) => setFormData({...formData, codigo: e.target.value})}
                  placeholder="Ex: 1.1.01"
                  data-testid="input-codigo-conta"
                />
              </div>
              <div>
                <label className="form-label">Tipo *</label>
                <select
                  className="form-select"
                  value={formData.tipo}
                  onChange={(e) => setFormData({...formData, tipo: e.target.value})}
                  required
                  data-testid="select-tipo-conta"
                >
                  <option value="receita">Receita</option>
                  <option value="despesa">Despesa</option>
                </select>
              </div>
              <div className="col-span-2">
                <label className="form-label">Nome da Conta *</label>
                <Input
                  value={formData.nome}
                  onChange={(e) => setFormData({...formData, nome: e.target.value})}
                  placeholder="Ex: Vendas de Serviços"
                  required
                  data-testid="input-nome-conta"
                />
              </div>
              <div className="col-span-2">
                <label className="form-label">Grupo</label>
                <Input
                  value={formData.grupo}
                  onChange={(e) => setFormData({...formData, grupo: e.target.value})}
                  placeholder="Ex: Operacional, Administrativo..."
                  data-testid="input-grupo-conta"
                />
              </div>
              <div className="col-span-2">
                <label className="form-label">Descrição</label>
                <Input
                  value={formData.descricao}
                  onChange={(e) => setFormData({...formData, descricao: e.target.value})}
                  placeholder="Descrição da conta"
                  data-testid="input-desc-conta"
                />
              </div>
            </div>
            <div className="flex gap-3 pt-2">
              <Button type="button" variant="outline" onClick={closeModal} className="flex-1">
                Cancelar
              </Button>
              <Button type="submit" className="flex-1 bg-blue-600 hover:bg-blue-700" data-testid="submit-conta-contabil">
                {editingConta ? "Atualizar" : "Cadastrar"}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
