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
  Plus, ChevronRight, ChevronDown, Edit, Trash2, 
  FileText, Download, FolderOpen, Receipt, Search,
  ArrowUpRight, ArrowDownLeft, Calendar
} from "lucide-react";
import { toast } from "sonner";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import AnexosManager from "@/components/AnexosManager";

export default function PlanoContasPage() {
  const [contas, setContas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingConta, setEditingConta] = useState(null);
  const anexosRef = useRef(null);
  const [expandedContas, setExpandedContas] = useState(new Set());
  const [expandedSubcontas, setExpandedSubcontas] = useState(new Set());
  const [expandedExtratos, setExpandedExtratos] = useState(new Set());
  const [extratos, setExtratos] = useState({});
  const [loadingExtrato, setLoadingExtrato] = useState({});
  const [selectedForReport, setSelectedForReport] = useState("");
  const [searchTerm, setSearchTerm] = useState("");
  
  const [formData, setFormData] = useState({
    codigo: "", nome: "", nivel: 1, pai_id: "", descricao: ""
  });

  useEffect(() => { fetchContas(); }, []);

  const fetchContas = async () => {
    try {
      const response = await axios.get(`${API}/admin/plano-contas`);
      setContas(response.data);
    } catch (error) { toast.error("Erro ao carregar plano de contas"); }
    finally { setLoading(false); }
  };

  // Buscar extrato (contas a pagar e receber vinculadas)
  const fetchExtrato = async (contaId, isSubconta = false) => {
    const key = `${contaId}-${isSubconta ? 'sub' : 'main'}`;
    if (extratos[key]) return; // Já carregado
    
    setLoadingExtrato(prev => ({ ...prev, [key]: true }));
    try {
      // Buscar contas a pagar vinculadas
      const [pagarRes, receberRes] = await Promise.all([
        axios.get(`${API}/admin/contas-pagar`),
        axios.get(`${API}/admin/contas-receber`)
      ]);
      
      // Filtrar por plano_conta_id ou subconta_id
      const filterField = isSubconta ? 'subconta_id' : 'plano_conta_id';
      const contasPagar = pagarRes.data.filter(c => c[filterField] === contaId);
      const contasReceber = receberRes.data.filter(c => c[filterField] === contaId);
      
      setExtratos(prev => ({
        ...prev,
        [key]: { pagar: contasPagar, receber: contasReceber }
      }));
    } catch (error) {
      toast.error("Erro ao carregar extrato");
    } finally {
      setLoadingExtrato(prev => ({ ...prev, [key]: false }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const dataToSend = { ...formData, tipo: "geral" }; // Tipo fixo como geral
      if (editingConta) {
        await axios.put(`${API}/admin/plano-contas/${editingConta.id}`, dataToSend);
        await anexosRef.current?.flushPending(editingConta.id);
        toast.success("Conta atualizada!");
      } else {
        const _resp = await axios.post(`${API}/admin/plano-contas`, dataToSend);
        await anexosRef.current?.flushPending(_resp.data?.id);
        toast.success("Conta cadastrada!");
      }
      fetchContas(); closeModal();
    } catch (error) { toast.error(error.response?.data?.detail || "Erro ao salvar"); }
  };

  const handleDelete = async (id) => {
    const conta = contas.find(c => c.id === id);
    const subcontas = contas.filter(c => c.pai_id === id);
    
    let confirmMsg = `Excluir a conta "${conta?.nome}"?`;
    if (subcontas.length > 0) {
      confirmMsg += `\n\nATENÇÃO: ${subcontas.length} subconta(s) também serão excluídas!`;
    }
    
    if (!window.confirm(confirmMsg)) return;
    try {
      const response = await axios.delete(`${API}/admin/plano-contas/${id}`);
      toast.success(response.data?.message || "Conta excluída!"); 
      fetchContas();
    } catch (error) { toast.error(error.response?.data?.detail || "Erro ao excluir"); }
  };

  const openModal = (conta = null, isSubconta = false, paiId = null) => {
    if (conta) {
      setEditingConta(conta);
      setFormData({
        codigo: conta.codigo || "",
        nome: conta.nome,
        nivel: conta.nivel,
        pai_id: conta.pai_id || "",
        descricao: conta.descricao || ""
      });
    } else {
      setEditingConta(null);
      setFormData({
        codigo: "",
        nome: "",
        nivel: isSubconta ? 2 : 1,
        pai_id: paiId || "",
        descricao: ""
      });
    }
    setIsModalOpen(true);
  };

  const closeModal = () => { setIsModalOpen(false); setEditingConta(null); };

  const toggleConta = (contaId) => {
    const newExpanded = new Set(expandedContas);
    if (newExpanded.has(contaId)) newExpanded.delete(contaId);
    else newExpanded.add(contaId);
    setExpandedContas(newExpanded);
  };

  const toggleSubconta = (subcontaId) => {
    const newExpanded = new Set(expandedSubcontas);
    if (newExpanded.has(subcontaId)) newExpanded.delete(subcontaId);
    else newExpanded.add(subcontaId);
    setExpandedSubcontas(newExpanded);
  };

  const toggleExtrato = (contaId, isSubconta = false) => {
    const key = `${contaId}-${isSubconta ? 'sub' : 'main'}`;
    const newExpanded = new Set(expandedExtratos);
    if (newExpanded.has(key)) {
      newExpanded.delete(key);
    } else {
      newExpanded.add(key);
      fetchExtrato(contaId, isSubconta);
    }
    setExpandedExtratos(newExpanded);
  };

  const exportToPDF = async () => {
    if (!selectedForReport) {
      toast.error("Selecione uma conta para exportar");
      return;
    }
    
    const conta = contas.find(c => c.id === selectedForReport);
    const subcontas = contas.filter(c => c.pai_id === selectedForReport);
    
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
        </style>
      </head>
      <body>
        <h1>Relatório do Plano de Contas</h1>
        <p><strong>Conta:</strong> ${conta?.codigo || ''} - ${conta?.nome}</p>
        <p><strong>Descrição:</strong> ${conta?.descricao || '-'}</p>
        
        ${subcontas.length > 0 ? `
          <h2>Subcontas</h2>
          <table>
            <thead><tr><th>Código</th><th>Nome</th><th>Descrição</th></tr></thead>
            <tbody>
              ${subcontas.map(s => `<tr><td>${s.codigo || '-'}</td><td>${s.nome}</td><td>${s.descricao || '-'}</td></tr>`).join('')}
            </tbody>
          </table>
        ` : '<p>Nenhuma subconta cadastrada.</p>'}
        
        <p style="margin-top: 30px; color: #666; font-size: 12px;">Gerado em: ${new Date().toLocaleString('pt-BR')}</p>
      </body>
      </html>
    `;
    
    const printWindow = window.open('', '_blank');
    printWindow.document.write(content);
    printWindow.document.close();
    printWindow.print();
  };

  const formatCurrency = (v) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(v || 0);
  const formatDate = (d) => d ? new Date(d).toLocaleDateString('pt-BR') : '-';

  // Filtrar contas de nível 1
  const contasNivel1 = contas.filter(c => c.nivel === 1);
  const getSubcontas = (paiId) => contas.filter(c => c.pai_id === paiId);

  // Filtro de busca
  const filteredContas = contasNivel1.filter(c => 
    c.nome.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (c.codigo && c.codigo.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  // Renderizar extrato
  const renderExtrato = (contaId, isSubconta = false) => {
    const key = `${contaId}-${isSubconta ? 'sub' : 'main'}`;
    const extrato = extratos[key];
    const isLoading = loadingExtrato[key];
    
    if (isLoading) {
      return <div className="p-4 text-center text-gray-500">Carregando extrato...</div>;
    }
    
    if (!extrato) return null;
    
    const { pagar, receber } = extrato;
    const totalPagar = pagar.reduce((sum, c) => sum + (c.valor_final || c.valor || 0), 0);
    const totalReceber = receber.reduce((sum, c) => sum + (c.valor_final || c.valor || 0), 0);
    const todos = [
      ...pagar.map(c => ({ ...c, tipo_conta: 'pagar' })),
      ...receber.map(c => ({ ...c, tipo_conta: 'receber' }))
    ].sort((a, b) => new Date(b.data_vencimento) - new Date(a.data_vencimento));
    
    return (
      <div className="bg-gray-50 rounded-lg p-4 mt-2 border">
        {/* Resumo */}
        <div className="grid grid-cols-3 gap-4 mb-4">
          <div className="bg-white p-3 rounded border">
            <p className="text-xs text-gray-500">Total a Pagar</p>
            <p className="text-lg font-bold text-red-600">{formatCurrency(totalPagar)}</p>
            <p className="text-xs text-gray-400">{pagar.length} registro(s)</p>
          </div>
          <div className="bg-white p-3 rounded border">
            <p className="text-xs text-gray-500">Total a Receber</p>
            <p className="text-lg font-bold text-green-600">{formatCurrency(totalReceber)}</p>
            <p className="text-xs text-gray-400">{receber.length} registro(s)</p>
          </div>
          <div className="bg-white p-3 rounded border">
            <p className="text-xs text-gray-500">Saldo</p>
            <p className={`text-lg font-bold ${totalReceber - totalPagar >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {formatCurrency(totalReceber - totalPagar)}
            </p>
          </div>
        </div>
        
        {/* Lista de movimentações */}
        {todos.length === 0 ? (
          <p className="text-center text-gray-400 py-4">Nenhuma movimentação registrada</p>
        ) : (
          <div className="space-y-2 max-h-[300px] overflow-y-auto">
            {todos.map((item, idx) => (
              <div key={`${item.tipo_conta}-${item.id || idx}`} className="flex items-center justify-between bg-white p-3 rounded border text-sm">
                <div className="flex items-center gap-3">
                  {item.tipo_conta === 'pagar' ? (
                    <ArrowUpRight className="text-red-500" size={18} />
                  ) : (
                    <ArrowDownLeft className="text-green-500" size={18} />
                  )}
                  <div>
                    <p className="font-medium">{item.descricao || item.fornecedor_nome || item.cliente_nome || '-'}</p>
                    <p className="text-xs text-gray-500 flex items-center gap-1">
                      <Calendar size={12} />
                      {formatDate(item.data_vencimento)}
                      <span className={`ml-2 px-1.5 py-0.5 rounded text-xs ${
                        item.status === 'quitada' ? 'bg-green-100 text-green-700' :
                        item.status === 'cancelada' ? 'bg-gray-100 text-gray-700' :
                        'bg-yellow-100 text-yellow-700'
                      }`}>
                        {item.status === 'quitada' ? 'Quitada' : item.status === 'cancelada' ? 'Cancelada' : 'Em Aberto'}
                      </span>
                    </p>
                  </div>
                </div>
                <p className={`font-bold ${item.tipo_conta === 'pagar' ? 'text-red-600' : 'text-green-600'}`}>
                  {item.tipo_conta === 'pagar' ? '-' : '+'} {formatCurrency(item.valor_final || item.valor)}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  if (loading) return <div className="flex items-center justify-center min-h-[400px]"><div className="spinner w-12 h-12"></div></div>;

  return (
    <div data-testid="plano-contas-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Plano de Contas</h1>
          <p className="text-gray-500 mt-1">Gerencie suas categorias financeiras</p>
        </div>
        <Button onClick={() => openModal()} className="bg-[#D4A000] hover:bg-[#b38900]">
          <Plus size={18} className="mr-2" />Novo Plano de Conta
        </Button>
      </div>

      {/* Barra de busca e exportação */}
      <Card className="mb-6">
        <CardContent className="p-4">
          <div className="flex items-center gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={18} />
              <Input 
                placeholder="Buscar plano de contas..." 
                value={searchTerm} 
                onChange={(e) => setSearchTerm(e.target.value)} 
                className="pl-10"
              />
            </div>
            <div className="flex items-center gap-2">
              <Select value={selectedForReport} onValueChange={setSelectedForReport}>
                <SelectTrigger className="w-[250px] h-11">
                  <SelectValue placeholder="Selecione para exportar..." />
                </SelectTrigger>
                <SelectContent className="z-[9999]">
                  {contasNivel1.map(c => (
                    <SelectItem key={c.id} value={c.id}>{c.codigo ? `${c.codigo} - ` : ''}{c.nome}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Button onClick={exportToPDF} disabled={!selectedForReport} variant="outline">
                <Download size={16} className="mr-2" />PDF
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Resumo */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <Card>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
              <FolderOpen className="text-blue-600" size={20} />
            </div>
            <div>
              <p className="text-xs text-gray-500">Planos de Conta</p>
              <p className="text-lg font-bold text-blue-600">{contasNivel1.length}</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
              <Receipt className="text-purple-600" size={20} />
            </div>
            <div>
              <p className="text-xs text-gray-500">Total de Subcontas</p>
              <p className="text-lg font-bold text-purple-600">{contas.filter(c => c.nivel === 2).length}</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Lista de Planos de Conta */}
      <Card>
        <CardContent className="p-0">
          {filteredContas.length === 0 ? (
            <div className="p-8 text-center text-gray-400">
              <FolderOpen className="mx-auto mb-4" size={48} />
              <p>Nenhum plano de conta encontrado</p>
            </div>
          ) : (
            <div className="divide-y">
              {filteredContas.map(conta => {
                const subcontas = getSubcontas(conta.id);
                const isExpanded = expandedContas.has(conta.id);
                const extratoKey = `${conta.id}-main`;
                const isExtratoExpanded = expandedExtratos.has(extratoKey);
                
                return (
                  <div key={conta.id} className="p-4">
                    {/* Linha principal do Plano de Conta */}
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <button 
                          onClick={() => toggleConta(conta.id)} 
                          className="p-1 hover:bg-gray-100 rounded"
                          title={subcontas.length > 0 ? "Expandir subcontas" : "Sem subcontas"}
                        >
                          {subcontas.length > 0 ? (
                            isExpanded ? <ChevronDown size={18} /> : <ChevronRight size={18} />
                          ) : (
                            <span className="w-[18px]" />
                          )}
                        </button>
                        <div>
                          <div className="flex items-center gap-2">
                            {conta.codigo && (
                              <span className="text-xs font-mono bg-gray-200 px-2 py-0.5 rounded">{conta.codigo}</span>
                            )}
                            <span className="font-semibold text-gray-800">{conta.nome}</span>
                            <span className="text-xs text-gray-400">({subcontas.length} subcontas)</span>
                          </div>
                          {conta.descricao && (
                            <p className="text-xs text-gray-500 mt-0.5">{conta.descricao}</p>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center gap-1">
                        <Button 
                          size="sm" 
                          variant={isExtratoExpanded ? "default" : "outline"}
                          onClick={() => toggleExtrato(conta.id, false)} 
                          title="Ver extrato"
                          className={isExtratoExpanded ? "bg-blue-600 hover:bg-blue-700" : ""}
                        >
                          <FileText size={14} className="mr-1" />
                          Extrato
                        </Button>
                        <Button size="sm" variant="outline" onClick={(e) => { e.stopPropagation(); openModal(null, true, conta.id); }} title="Adicionar Subconta">
                          <Plus size={14} />
                        </Button>
                        <Button size="sm" variant="ghost" onClick={() => openModal(conta)}>
                          <Edit size={14} />
                        </Button>
                        <Button size="sm" variant="ghost" className="text-red-600" onClick={() => handleDelete(conta.id)}>
                          <Trash2 size={14} />
                        </Button>
                      </div>
                    </div>
                    
                    {/* Extrato do Plano de Conta */}
                    {isExtratoExpanded && renderExtrato(conta.id, false)}
                    
                    {/* Subcontas (dropdown) */}
                    {isExpanded && subcontas.length > 0 && (
                      <div className="ml-8 mt-3 border-l-2 border-gray-200 pl-4 space-y-2">
                        {subcontas.map(sub => {
                          const subExtratoKey = `${sub.id}-sub`;
                          const isSubExtratoExpanded = expandedExtratos.has(subExtratoKey);
                          
                          return (
                            <div key={sub.id} className="bg-gray-50 rounded-lg p-3">
                              <div className="flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                  {sub.codigo && (
                                    <span className="text-xs font-mono bg-white px-2 py-0.5 rounded border">{sub.codigo}</span>
                                  )}
                                  <span className="font-medium text-gray-700">{sub.nome}</span>
                                </div>
                                <div className="flex items-center gap-1">
                                  <Button 
                                    size="sm" 
                                    variant={isSubExtratoExpanded ? "default" : "outline"}
                                    onClick={() => toggleExtrato(sub.id, true)} 
                                    title="Ver extrato da subconta"
                                    className={`text-xs ${isSubExtratoExpanded ? "bg-purple-600 hover:bg-purple-700" : ""}`}
                                  >
                                    <FileText size={12} className="mr-1" />
                                    Extrato
                                  </Button>
                                  <Button size="sm" variant="ghost" onClick={() => openModal(sub)}>
                                    <Edit size={12} />
                                  </Button>
                                  <Button size="sm" variant="ghost" className="text-red-600" onClick={() => handleDelete(sub.id)}>
                                    <Trash2 size={12} />
                                  </Button>
                                </div>
                              </div>
                              {sub.descricao && (
                                <p className="text-xs text-gray-500 mt-1">{sub.descricao}</p>
                              )}
                              
                              {/* Extrato da Subconta */}
                              {isSubExtratoExpanded && renderExtrato(sub.id, true)}
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Modal */}
      <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>
              {editingConta ? "Editar" : formData.nivel === 2 ? "Nova Subconta" : "Novo Plano de Conta"}
            </DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="form-label">Código</label>
              <Input 
                value={formData.codigo} 
                onChange={(e) => setFormData({...formData, codigo: e.target.value})} 
                placeholder="Ex: 1.1.01" 
              />
            </div>
            
            {formData.nivel === 2 && (
              <div>
                <label className="form-label">Plano de Conta Pai *</label>
                <Select value={formData.pai_id} onValueChange={(v) => setFormData({...formData, pai_id: v})}>
                  <SelectTrigger className="w-full h-11"><SelectValue placeholder="Selecione..." /></SelectTrigger>
                  <SelectContent className="z-[9999]">
                    {contasNivel1.map(c => (
                      <SelectItem key={c.id} value={c.id}>{c.codigo ? `${c.codigo} - ` : ''}{c.nome}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}
            
            <div>
              <label className="form-label">Nome *</label>
              <Input 
                value={formData.nome} 
                onChange={(e) => setFormData({...formData, nome: e.target.value})} 
                required 
                placeholder={formData.nivel === 2 ? "Nome da subconta" : "Nome do plano de conta"}
              />
            </div>
            
            <div>
              <label className="form-label">Descrição</label>
              <Input 
                value={formData.descricao} 
                onChange={(e) => setFormData({...formData, descricao: e.target.value})} 
                placeholder="Descrição opcional"
              />
            </div>
            
            <div className="flex gap-3 pt-2">
              <Button type="button" variant="outline" onClick={closeModal} className="flex-1">Cancelar</Button>
              <Button type="submit" className="flex-1 bg-[#D4A000] hover:bg-[#b38900]">
                {editingConta ? "Atualizar" : "Cadastrar"}
              </Button>
            </div>
          
            <AnexosManager
              ref={anexosRef}
              entityType="plano_contas"
              entityId={editingConta?.id}
            />
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
