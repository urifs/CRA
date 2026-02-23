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
  Plus, DollarSign, FolderTree, ChevronRight, ChevronDown, Edit, Trash2, 
  TrendingUp, TrendingDown, FileText, Download
} from "lucide-react";
import { toast } from "sonner";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";

export default function PlanoContasPage() {
  const [contas, setContas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingConta, setEditingConta] = useState(null);
  const [expandedGroups, setExpandedGroups] = useState(new Set(["receitas", "despesas"]));
  const [selectedForReport, setSelectedForReport] = useState("");
  const [formData, setFormData] = useState({
    codigo: "", nome: "", tipo: "despesa", nivel: 1, pai_id: "", descricao: ""
  });

  useEffect(() => { fetchContas(); }, []);

  const fetchContas = async () => {
    try {
      const response = await axios.get(`${API}/admin/plano-contas`);
      setContas(response.data);
    } catch (error) { toast.error("Erro ao carregar plano de contas"); }
    finally { setLoading(false); }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingConta) {
        await axios.put(`${API}/admin/plano-contas/${editingConta.id}`, formData);
        toast.success("Conta atualizada!");
      } else {
        await axios.post(`${API}/admin/plano-contas`, formData);
        toast.success("Conta cadastrada!");
      }
      fetchContas(); closeModal();
    } catch (error) { toast.error(error.response?.data?.detail || "Erro ao salvar"); }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Excluir esta conta? Subcontas também serão afetadas.")) return;
    try {
      await axios.delete(`${API}/admin/plano-contas/${id}`);
      toast.success("Conta excluída!"); fetchContas();
    } catch (error) { toast.error(error.response?.data?.detail || "Erro ao excluir"); }
  };

  const openModal = (conta = null, isSubconta = false, paiId = null, paiTipo = null) => {
    if (conta) {
      setEditingConta(conta);
      setFormData({
        codigo: conta.codigo || "",
        nome: conta.nome,
        tipo: conta.tipo,
        nivel: conta.nivel,
        pai_id: conta.pai_id || "",
        descricao: conta.descricao || ""
      });
    } else {
      setEditingConta(null);
      setFormData({
        codigo: "",
        nome: "",
        tipo: paiTipo || "despesa",
        nivel: isSubconta ? 2 : 1,
        pai_id: paiId || "",
        descricao: ""
      });
    }
    setIsModalOpen(true);
  };

  const closeModal = () => { setIsModalOpen(false); setEditingConta(null); };

  const toggleGroup = (group) => {
    const newExpanded = new Set(expandedGroups);
    if (newExpanded.has(group)) newExpanded.delete(group);
    else newExpanded.add(group);
    setExpandedGroups(newExpanded);
  };

  const exportToPDF = async () => {
    if (!selectedForReport) {
      toast.error("Selecione uma conta para exportar");
      return;
    }
    
    const conta = contas.find(c => c.id === selectedForReport);
    const subcontas = contas.filter(c => c.pai_id === selectedForReport);
    
    // Criar conteúdo do relatório
    let content = `
      <html>
      <head>
        <title>Relatório - ${conta?.nome}</title>
        <style>
          body { font-family: Arial, sans-serif; padding: 20px; }
          h1 { color: #1e40af; border-bottom: 2px solid #1e40af; padding-bottom: 10px; }
          table { width: 100%; border-collapse: collapse; margin-top: 20px; }
          th, td { border: 1px solid #ddd; padding: 10px; text-align: left; }
          th { background: #f3f4f6; }
          .tipo-receita { color: #16a34a; }
          .tipo-despesa { color: #dc2626; }
          .total { font-weight: bold; background: #f9fafb; }
        </style>
      </head>
      <body>
        <h1>Relatório do Plano de Contas</h1>
        <p><strong>Conta:</strong> ${conta?.codigo || ''} - ${conta?.nome}</p>
        <p><strong>Tipo:</strong> <span class="tipo-${conta?.tipo}">${conta?.tipo === 'receita' ? 'Receita' : 'Despesa'}</span></p>
        <p><strong>Descrição:</strong> ${conta?.descricao || '-'}</p>
        
        ${subcontas.length > 0 ? `
          <h2>Subcontas</h2>
          <table>
            <thead>
              <tr>
                <th>Código</th>
                <th>Nome</th>
                <th>Descrição</th>
              </tr>
            </thead>
            <tbody>
              ${subcontas.map(s => `
                <tr>
                  <td>${s.codigo || '-'}</td>
                  <td>${s.nome}</td>
                  <td>${s.descricao || '-'}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        ` : '<p>Nenhuma subconta cadastrada.</p>'}
        
        <p style="margin-top: 30px; color: #666; font-size: 12px;">
          Gerado em: ${new Date().toLocaleString('pt-BR')}
        </p>
      </body>
      </html>
    `;
    
    // Abrir em nova janela para impressão
    const printWindow = window.open('', '_blank');
    printWindow.document.write(content);
    printWindow.document.close();
    printWindow.print();
  };

  // Agrupar por tipo
  const receitas = contas.filter(c => c.tipo === "receita" && c.nivel === 1);
  const despesas = contas.filter(c => c.tipo === "despesa" && c.nivel === 1);

  const getSubcontas = (paiId) => contas.filter(c => c.pai_id === paiId);

  if (loading) return <div className="flex items-center justify-center min-h-[400px]"><div className="spinner w-12 h-12"></div></div>;

  const renderConta = (conta, level = 0) => {
    const subcontas = getSubcontas(conta.id);
    const isExpanded = expandedGroups.has(conta.id);
    
    return (
      <div key={conta.id}>
        <div className={`flex items-center justify-between p-3 hover:bg-slate-100 rounded-lg ${level > 0 ? 'ml-6 border-l-2 border-slate-200' : ''}`}>
          <div className="flex items-center gap-2">
            {subcontas.length > 0 && (
              <button onClick={() => toggleGroup(conta.id)} className="p-1 hover:bg-slate-200 rounded">
                {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
              </button>
            )}
            {subcontas.length === 0 && <span className="w-6" />}
            {conta.codigo && <span className="text-xs font-mono bg-slate-200 px-2 py-0.5 rounded">{conta.codigo}</span>}
            <span className="font-medium">{conta.nome}</span>
            {conta.nivel === 1 && <span className="text-xs text-slate-500">({subcontas.length} subcontas)</span>}
          </div>
          <div className="flex gap-1">
            {conta.nivel === 1 && (
              <Button size="sm" variant="outline" onClick={() => openModal(null, true, conta.id, conta.tipo)} title="Adicionar Subconta">
                <Plus size={14} />
              </Button>
            )}
            <Button size="sm" variant="ghost" onClick={() => openModal(conta)}><Edit size={14} /></Button>
            <Button size="sm" variant="ghost" className="text-red-600" onClick={() => handleDelete(conta.id)}><Trash2 size={14} /></Button>
          </div>
        </div>
        {isExpanded && subcontas.map(sub => renderConta(sub, level + 1))}
      </div>
    );
  };

  const renderGroup = (title, items, color, icon) => {
    const Icon = icon;
    const isExpanded = expandedGroups.has(title.toLowerCase());
    
    return (
      <Card className={`border-l-4 ${color}`}>
        <CardHeader className="cursor-pointer hover:bg-slate-50" onClick={() => toggleGroup(title.toLowerCase())}>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Icon size={20} />
              <span>{title}</span>
              <span className="text-sm font-normal text-slate-500">({items.length} contas)</span>
            </div>
            <div className="flex items-center gap-2">
              <Button size="sm" variant="outline" onClick={(e) => { e.stopPropagation(); openModal(null, false, null, title.toLowerCase() === 'receitas' ? 'receita' : 'despesa'); }}>
                <Plus size={14} className="mr-1" /> Nova Conta
              </Button>
              {isExpanded ? <ChevronDown size={20} /> : <ChevronRight size={20} />}
            </div>
          </CardTitle>
        </CardHeader>
        {isExpanded && (
          <CardContent className="pt-0">
            {items.length === 0 ? (
              <p className="text-slate-400 text-center py-4">Nenhuma conta cadastrada</p>
            ) : (
              items.map(conta => renderConta(conta))
            )}
          </CardContent>
        )}
      </Card>
    );
  };

  // Contas de nível 1 para o select de relatório
  const contasNivel1 = contas.filter(c => c.nivel === 1);

  return (
    <div data-testid="plano-contas-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Plano de Contas</h1>
          <p className="text-slate-500 mt-1">Categorias financeiras com subcontas</p>
        </div>
        <Button onClick={() => openModal()} className="bg-blue-600 hover:bg-blue-700">
          <Plus size={18} className="mr-2" />Nova Conta
        </Button>
      </div>

      {/* Exportar Relatório */}
      <Card className="mb-6">
        <CardContent className="p-4">
          <div className="flex items-center gap-4">
            <FileText className="text-slate-500" size={24} />
            <div className="flex-1">
              <label className="form-label">Exportar Relatório</label>
              <Select value={selectedForReport} onValueChange={setSelectedForReport}>
                <SelectTrigger className="w-full h-11"><SelectValue placeholder="Selecione uma conta..." /></SelectTrigger>
                <SelectContent className="z-[9999]">
                  {contasNivel1.map(c => (
                    <SelectItem key={c.id} value={c.id}>{c.codigo ? `${c.codigo} - ` : ''}{c.nome} ({c.tipo})</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <Button onClick={exportToPDF} disabled={!selectedForReport} className="bg-green-600 hover:bg-green-700">
              <Download size={18} className="mr-2" />Exportar PDF
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Resumo */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <Card className="stat-card">
          <CardContent className="p-4 flex items-center gap-3">
            <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
              <TrendingUp className="text-green-600" size={20} />
            </div>
            <div>
              <p className="text-xs text-slate-500">Receitas</p>
              <p className="text-lg font-bold text-green-600">{receitas.length} contas</p>
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
              <p className="text-lg font-bold text-red-600">{despesas.length} contas</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Árvore de contas */}
      <div className="space-y-4">
        {renderGroup("Receitas", receitas, "border-l-green-500", TrendingUp)}
        {renderGroup("Despesas", despesas, "border-l-red-500", TrendingDown)}
      </div>

      {/* Modal */}
      <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>
              {editingConta ? "Editar Conta" : formData.nivel === 2 ? "Nova Subconta" : "Nova Conta"}
            </DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="form-label">Código</label>
                <Input value={formData.codigo} onChange={(e) => setFormData({...formData, codigo: e.target.value})} placeholder="Ex: 1.1.01" />
              </div>
              <div>
                <label className="form-label">Tipo *</label>
                <Select value={formData.tipo} onValueChange={(v) => setFormData({...formData, tipo: v})} disabled={formData.nivel === 2}>
                  <SelectTrigger className="w-full h-11"><SelectValue /></SelectTrigger>
                  <SelectContent className="z-[9999]">
                    <SelectItem value="receita">Receita</SelectItem>
                    <SelectItem value="despesa">Despesa</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            {formData.nivel === 2 && (
              <div>
                <label className="form-label">Conta Pai</label>
                <Select value={formData.pai_id} onValueChange={(v) => setFormData({...formData, pai_id: v})}>
                  <SelectTrigger className="w-full h-11"><SelectValue placeholder="Selecione..." /></SelectTrigger>
                  <SelectContent className="z-[9999]">
                    {contasNivel1.filter(c => c.tipo === formData.tipo).map(c => (
                      <SelectItem key={c.id} value={c.id}>{c.codigo ? `${c.codigo} - ` : ''}{c.nome}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}
            <div>
              <label className="form-label">Nome da Conta *</label>
              <Input value={formData.nome} onChange={(e) => setFormData({...formData, nome: e.target.value})} required />
            </div>
            <div>
              <label className="form-label">Descrição</label>
              <Input value={formData.descricao} onChange={(e) => setFormData({...formData, descricao: e.target.value})} />
            </div>
            <div className="flex gap-3 pt-2">
              <Button type="button" variant="outline" onClick={closeModal} className="flex-1">Cancelar</Button>
              <Button type="submit" className="flex-1 bg-blue-600 hover:bg-blue-700">{editingConta ? "Atualizar" : "Cadastrar"}</Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
