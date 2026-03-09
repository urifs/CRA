import { useState, useEffect, useRef } from "react";
import axios from "axios";
import { API } from "@/App";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { 
  FileText, 
  Upload, 
  Download, 
  RefreshCw,
  Search,
  Filter,
  ArrowLeftRight,
  CheckCircle2,
  XCircle,
  Clock,
  DollarSign,
  TrendingUp,
  TrendingDown,
  Loader2,
  Calendar,
  Building2,
  Link2,
  Unlink,
  AlertCircle,
  ChevronLeft,
  ChevronRight,
  Sparkles,
  Check,
  X,
  Zap,
  Briefcase,
  Trash2
} from "lucide-react";

export default function ConciliacaoPage() {
  const [loading, setLoading] = useState(true);
  const [importando, setImportando] = useState(false);
  const [conciliando, setConciliando] = useState(false);
  
  // Dados do extrato importado
  const [extratoItems, setExtratoItems] = useState([]);
  const [selectedExtratoItem, setSelectedExtratoItem] = useState(null);
  
  // Dados das contas do sistema
  const [contas, setContas] = useState([]);
  const [selectedConta, setSelectedConta] = useState(null);
  
  // Contas bancárias (usado apenas para importação)
  const [contasBancarias, setContasBancarias] = useState([]);
  const [selectedContaBancariaImport, setSelectedContaBancariaImport] = useState("");
  
  // Centros de Custo
  const [centrosCusto, setCentrosCusto] = useState([]);
  const [selectedCentroCusto, setSelectedCentroCusto] = useState("todos");
  
  // Filtros do extrato
  const [filtroDataInicio, setFiltroDataInicio] = useState("");
  const [filtroDataFim, setFiltroDataFim] = useState("");
  const [filtroTipoExtrato, setFiltroTipoExtrato] = useState("todos"); // "entrada", "saida", "todos"
  
  // Filtros das contas
  const [filtroContas, setFiltroContas] = useState("todas"); // "quitadas", "a_pagar", "a_receber", "todas"
  const [buscaConta, setBuscaConta] = useState("");
  
  // Conciliações realizadas
  const [conciliacoes, setConciliacoes] = useState([]);
  
  // Resumos
  const [resumoExtrato, setResumoExtrato] = useState({ entradas: 0, saidas: 0, total: 0 });
  const [resumoContas, setResumoContas] = useState({ quitadas: 0, pendentes: 0, total: 0 });
  
  // Sugestões automáticas
  const [sugestoes, setSugestoes] = useState([]);
  const [showSugestoes, setShowSugestoes] = useState(false);
  const [processandoSugestoes, setProcessandoSugestoes] = useState(false);
  const [tolerancia, setTolerancia] = useState(0); // 0 = exato, 1 = 1%, 2 = 2%, etc.
  
  // Modal de seleção de conta bancária para importação
  const [showImportModal, setShowImportModal] = useState(false);
  
  const fileInputRef = useRef(null);
  const token = localStorage.getItem("token");

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    calcularResumos();
  }, [extratoItems, contas]);

  const fetchData = async () => {
    try {
      const [contasBancariasRes, conciliacoesRes, centrosCustoRes] = await Promise.all([
        axios.get(`${API}/admin/contas-bancarias?ativo=true`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API}/conciliacao`, { headers: { Authorization: `Bearer ${token}` } }).catch(() => ({ data: [] })),
        axios.get(`${API}/admin/centros-custo`, { headers: { Authorization: `Bearer ${token}` } }).catch(() => ({ data: [] }))
      ]);
      
      setContasBancarias(contasBancariasRes.data);
      setConciliacoes(conciliacoesRes.data || []);
      setCentrosCusto(centrosCustoRes.data || []);
      
      // Carregar todos os extratos e contas
      await fetchExtratosEContas();
    } catch (error) {
      console.error("Erro ao carregar dados:", error);
      toast.error("Erro ao carregar dados");
    } finally {
      setLoading(false);
    }
  };

  const fetchExtratosEContas = async () => {
    try {
      const [extratosRes, contasPagarRes, contasReceberRes] = await Promise.all([
        axios.get(`${API}/conciliacao/extratos`, { headers: { Authorization: `Bearer ${token}` } }).catch(() => ({ data: [] })),
        axios.get(`${API}/admin/contas-pagar`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API}/admin/contas-receber`, { headers: { Authorization: `Bearer ${token}` } })
      ]);
      
      setExtratoItems(extratosRes.data || []);
      
      // Combinar contas a pagar e a receber
      const todasContas = [
        ...contasPagarRes.data.map(c => ({ ...c, tipo: "pagar" })),
        ...contasReceberRes.data.map(c => ({ ...c, tipo: "receber" }))
      ].sort((a, b) => new Date(b.data_vencimento || b.created_at) - new Date(a.data_vencimento || a.created_at));
      
      setContas(todasContas);
    } catch (error) {
      console.error("Erro ao carregar extratos:", error);
    }
  };

  const calcularResumos = () => {
    const entradas = extratoItems.filter(e => e.tipo === "entrada").reduce((sum, e) => sum + (e.valor || 0), 0);
    const saidas = extratoItems.filter(e => e.tipo === "saida").reduce((sum, e) => sum + (e.valor || 0), 0);
    setResumoExtrato({ entradas, saidas, total: entradas - saidas });
    
    const quitadas = contas.filter(c => c.status === "quitada" || c.status === "recebida").length;
    const pendentes = contas.filter(c => c.status === "pendente").length;
    const totalContas = contas.reduce((sum, c) => sum + (c.valor || 0), 0);
    setResumoContas({ quitadas, pendentes, total: totalContas });
  };

  const handleImportarExtrato = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    if (!selectedContaBancariaImport) {
      toast.error("Selecione uma conta bancária primeiro");
      return;
    }
    
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      toast.error("Por favor, selecione um arquivo PDF");
      return;
    }
    
    setImportando(true);
    const formData = new FormData();
    formData.append("file", file);
    formData.append("conta_bancaria_id", selectedContaBancariaImport);
    
    try {
      const response = await axios.post(`${API}/conciliacao/importar-extrato`, formData, {
        headers: { 
          Authorization: `Bearer ${token}`,
          "Content-Type": "multipart/form-data"
        }
      });
      
      toast.success(`${response.data.count || 0} movimentações importadas!`);
      setShowImportModal(false);
      await fetchExtratosEContas();
    } catch (error) {
      console.error("Erro ao importar extrato:", error);
      toast.error(error.response?.data?.detail || "Erro ao importar extrato PDF");
    } finally {
      setImportando(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const handleLimparExtrato = async () => {
    if (!window.confirm("Tem certeza que deseja limpar todos os itens do extrato não conciliados?")) {
      return;
    }
    
    try {
      const response = await axios.delete(`${API}/conciliacao/extratos`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success(response.data.message || "Extrato limpo com sucesso!");
      setExtratoItems([]);
      setSelectedExtratoItem(null);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao limpar extrato");
    }
  };

  const handleConciliar = async () => {
    if (!selectedExtratoItem || !selectedConta) {
      toast.error("Selecione um item do extrato e uma conta para conciliar");
      return;
    }
    
    setConciliando(true);
    try {
      await axios.post(`${API}/conciliacao/conciliar`, {
        extrato_id: selectedExtratoItem.id,
        conta_id: selectedConta.id,
        conta_tipo: selectedConta.tipo
      }, { headers: { Authorization: `Bearer ${token}` } });
      
      toast.success("Conciliação realizada com sucesso!");
      setSelectedExtratoItem(null);
      setSelectedConta(null);
      await fetchExtratosEContas(selectedContaBancaria);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao conciliar");
    } finally {
      setConciliando(false);
    }
  };

  const handleDesfazerConciliacao = async (conciliacaoId) => {
    if (!confirm("Deseja desfazer esta conciliação?")) return;
    
    try {
      await axios.delete(`${API}/conciliacao/${conciliacaoId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success("Conciliação desfeita!");
      await fetchExtratosEContas(selectedContaBancaria);
    } catch (error) {
      toast.error("Erro ao desfazer conciliação");
    }
  };

  // Função para gerar sugestões automáticas
  const gerarSugestoes = () => {
    setProcessandoSugestoes(true);
    
    const novasSugestoes = [];
    const toleranciaPercent = tolerancia / 100;
    
    // Para cada item do extrato não conciliado
    extratosFiltrados.forEach(extrato => {
      const valorExtrato = extrato.valor || 0;
      
      // Buscar contas com valor igual ou similar
      const contasMatch = contasFiltradas.filter(conta => {
        if (conta.conciliado) return false;
        
        const valorConta = conta.valor || 0;
        
        // Verificar se tipos são compatíveis
        // Saída no extrato = Conta a Pagar
        // Entrada no extrato = Conta a Receber
        const tipoCompativel = 
          (extrato.tipo === "saida" && conta.tipo === "pagar") ||
          (extrato.tipo === "entrada" && conta.tipo === "receber");
        
        if (!tipoCompativel) return false;
        
        // Verificar tolerância de valor
        if (tolerancia === 0) {
          // Valor exato
          return Math.abs(valorExtrato - valorConta) < 0.01;
        } else {
          // Com tolerância
          const diferenca = Math.abs(valorExtrato - valorConta);
          const percentDiferenca = diferenca / Math.max(valorExtrato, valorConta);
          return percentDiferenca <= toleranciaPercent;
        }
      });
      
      // Adicionar sugestões encontradas
      contasMatch.forEach(conta => {
        const valorExtrato = extrato.valor || 0;
        const valorConta = conta.valor || 0;
        const diferenca = Math.abs(valorExtrato - valorConta);
        const percentMatch = 100 - (diferenca / Math.max(valorExtrato, valorConta) * 100);
        
        novasSugestoes.push({
          id: `${extrato.id}-${conta.id}`,
          extrato,
          conta,
          percentMatch: percentMatch.toFixed(1),
          diferenca,
          aceita: null // null = pendente, true = aceita, false = rejeitada
        });
      });
    });
    
    // Ordenar por melhor match
    novasSugestoes.sort((a, b) => parseFloat(b.percentMatch) - parseFloat(a.percentMatch));
    
    setSugestoes(novasSugestoes);
    setShowSugestoes(true);
    setProcessandoSugestoes(false);
    
    if (novasSugestoes.length === 0) {
      toast.info("Nenhuma correspondência encontrada com os critérios atuais");
    } else {
      toast.success(`${novasSugestoes.length} sugestão(ões) encontrada(s)!`);
    }
  };

  // Aceitar uma sugestão
  const aceitarSugestao = async (sugestao) => {
    setConciliando(true);
    try {
      await axios.post(`${API}/conciliacao/conciliar`, {
        extrato_id: sugestao.extrato.id,
        conta_id: sugestao.conta.id,
        conta_tipo: sugestao.conta.tipo
      }, { headers: { Authorization: `Bearer ${token}` } });
      
      // Remover a sugestão da lista
      setSugestoes(prev => prev.filter(s => s.id !== sugestao.id));
      toast.success("Conciliação realizada!");
      await fetchExtratosEContas(selectedContaBancaria);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao conciliar");
    } finally {
      setConciliando(false);
    }
  };

  // Rejeitar uma sugestão
  const rejeitarSugestao = (sugestaoId) => {
    setSugestoes(prev => prev.filter(s => s.id !== sugestaoId));
  };

  // Aceitar todas as sugestões
  const aceitarTodasSugestoes = async () => {
    if (sugestoes.length === 0) return;
    
    if (!confirm(`Deseja conciliar automaticamente ${sugestoes.length} itens?`)) return;
    
    setConciliando(true);
    let sucesso = 0;
    let erros = 0;
    
    for (const sugestao of sugestoes) {
      try {
        await axios.post(`${API}/conciliacao/conciliar`, {
          extrato_id: sugestao.extrato.id,
          conta_id: sugestao.conta.id,
          conta_tipo: sugestao.conta.tipo
        }, { headers: { Authorization: `Bearer ${token}` } });
        sucesso++;
      } catch {
        erros++;
      }
    }
    
    setSugestoes([]);
    setShowSugestoes(false);
    await fetchExtratosEContas(selectedContaBancaria);
    
    if (erros > 0) {
      toast.warning(`${sucesso} conciliações realizadas, ${erros} erros`);
    } else {
      toast.success(`${sucesso} conciliações realizadas com sucesso!`);
    }
    
    setConciliando(false);
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat("pt-BR", {
      style: "currency",
      currency: "BRL"
    }).format(value || 0);
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return "-";
    return new Date(dateStr).toLocaleDateString("pt-BR");
  };

  // Filtrar extratos
  const extratosFiltrados = extratoItems.filter(item => {
    if (filtroTipoExtrato !== "todos" && item.tipo !== filtroTipoExtrato) return false;
    if (filtroDataInicio && item.data < filtroDataInicio) return false;
    if (filtroDataFim && item.data > filtroDataFim) return false;
    if (item.conciliado) return false; // Ocultar já conciliados
    return true;
  });

  // Filtrar contas
  const contasFiltradas = contas.filter(conta => {
    const isQuitada = conta.status === "quitada" || conta.status === "recebida";
    
    // Filtro por centro de custo
    if (selectedCentroCusto && selectedCentroCusto !== "todos") {
      // Buscar o nome do centro de custo selecionado
      const centroCustoSelecionado = centrosCusto.find(cc => cc.id === selectedCentroCusto);
      if (centroCustoSelecionado) {
        if (conta.centro_custo !== centroCustoSelecionado.nome) return false;
      }
    }
    
    switch (filtroContas) {
      case "quitadas":
        if (!isQuitada) return false;
        break;
      case "a_pagar":
        if (conta.tipo !== "pagar" || isQuitada) return false;
        break;
      case "a_receber":
        if (conta.tipo !== "receber" || isQuitada) return false;
        break;
      default:
        break;
    }
    
    if (buscaConta) {
      const termo = buscaConta.toLowerCase();
      const descricao = (conta.descricao || conta.favorecido || "").toLowerCase();
      if (!descricao.includes(termo)) return false;
    }
    
    if (conta.conciliado) return false; // Ocultar já conciliados
    
    return true;
  });

  const getContaBancariaName = (id) => {
    const conta = contasBancarias.find(c => c.id === id);
    return conta ? `${conta.banco} - ${conta.agencia}/${conta.conta}` : "-";
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="animate-spin text-[#D4A000]" size={48} />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="conciliacao-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <ArrowLeftRight className="text-[#D4A000]" />
            Conciliação Bancária
          </h1>
          <p className="text-gray-500">Compare o extrato bancário com as contas do sistema</p>
        </div>
        
        <div className="flex gap-2">
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf"
            onChange={handleImportarExtrato}
            className="hidden"
          />
          <Button
            onClick={() => setShowImportModal(true)}
            disabled={importando}
            className="bg-[#D4A000] hover:bg-yellow-600"
          >
            {importando ? (
              <Loader2 className="animate-spin mr-2" size={18} />
            ) : (
              <Upload size={18} className="mr-2" />
            )}
            Importar Extrato PDF
          </Button>
        </div>
      </div>

      {/* Seleção de Centro de Custo */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row gap-4 items-end">
            <div className="flex-1">
              <Label className="flex items-center gap-2">
                <Briefcase size={16} className="text-[#D4A000]" />
                Centro de Custo
              </Label>
              <Select 
                value={selectedCentroCusto} 
                onValueChange={setSelectedCentroCusto}
              >
                <SelectTrigger className="mt-1">
                  <SelectValue placeholder="Selecione um centro de custo..." />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="todos">
                    <div className="flex items-center gap-2">
                      <Briefcase size={14} />
                      Todos os Centros de Custo
                    </div>
                  </SelectItem>
                  {centrosCusto.map(centro => (
                    <SelectItem key={centro.id} value={centro.id}>
                      <div className="flex items-center gap-2">
                        <Briefcase size={14} />
                        {centro.nome}
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <Button 
              variant="outline" 
              onClick={() => fetchExtratosEContas()}
            >
              <RefreshCw size={18} className="mr-2" />
              Atualizar
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Resumo */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="bg-green-50 border-green-200">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                <TrendingUp className="text-green-600" size={20} />
              </div>
              <div>
                <p className="text-xs text-green-600 font-medium">Entradas</p>
                <p className="text-lg font-bold text-green-700">{formatCurrency(resumoExtrato.entradas)}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-red-50 border-red-200">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-red-100 rounded-lg flex items-center justify-center">
                <TrendingDown className="text-red-600" size={20} />
              </div>
              <div>
                <p className="text-xs text-red-600 font-medium">Saídas</p>
                <p className="text-lg font-bold text-red-700">{formatCurrency(resumoExtrato.saidas)}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-blue-50 border-blue-200">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                <DollarSign className="text-blue-600" size={20} />
              </div>
              <div>
                <p className="text-xs text-blue-600 font-medium">Saldo Extrato</p>
                <p className="text-lg font-bold text-blue-700">{formatCurrency(resumoExtrato.total)}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-purple-50 border-purple-200">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                <CheckCircle2 className="text-purple-600" size={20} />
              </div>
              <div>
                <p className="text-xs text-purple-600 font-medium">Conciliados</p>
                <p className="text-lg font-bold text-purple-700">{conciliacoes.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Área de Conciliação - Lado a Lado */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Extrato Bancário (Esquerda) */}
        <Card className="border-2 border-yellow-200">
          <CardHeader className="bg-yellow-50 border-b border-yellow-200 pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg flex items-center gap-2">
                <FileText className="text-yellow-600" size={20} />
                Extrato Bancário
              </CardTitle>
              <Badge variant="outline" className="bg-yellow-100">
                {extratosFiltrados.length} itens
              </Badge>
            </div>
            
            {/* Filtros do Extrato */}
            <div className="flex flex-wrap gap-2 mt-3">
              <Select value={filtroTipoExtrato} onValueChange={setFiltroTipoExtrato}>
                <SelectTrigger className="w-32 h-8">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="todos">Todos</SelectItem>
                  <SelectItem value="entrada">Entradas</SelectItem>
                  <SelectItem value="saida">Saídas</SelectItem>
                </SelectContent>
              </Select>
              
              <Input 
                type="date" 
                value={filtroDataInicio}
                onChange={(e) => setFiltroDataInicio(e.target.value)}
                className="w-36 h-8"
                placeholder="Data início"
              />
              <Input 
                type="date" 
                value={filtroDataFim}
                onChange={(e) => setFiltroDataFim(e.target.value)}
                className="w-36 h-8"
                placeholder="Data fim"
              />
            </div>
          </CardHeader>
          <CardContent className="p-0 max-h-[500px] overflow-y-auto">
            {extratosFiltrados.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 text-gray-500">
                <FileText size={40} className="mb-3 text-gray-300" />
                <p>Nenhuma movimentação encontrada</p>
                <p className="text-sm">Importe um extrato bancário em PDF</p>
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow className="bg-yellow-50/50">
                    <TableHead className="w-10"></TableHead>
                    <TableHead>Data</TableHead>
                    <TableHead>Descrição</TableHead>
                    <TableHead className="text-right">Valor</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {extratosFiltrados.map((item) => (
                    <TableRow 
                      key={item.id}
                      className={`cursor-pointer transition-colors ${
                        selectedExtratoItem?.id === item.id 
                          ? 'bg-yellow-100 border-l-4 border-l-yellow-500' 
                          : 'hover:bg-yellow-50'
                      }`}
                      onClick={() => setSelectedExtratoItem(item)}
                    >
                      <TableCell>
                        <Checkbox 
                          checked={selectedExtratoItem?.id === item.id}
                          onCheckedChange={() => setSelectedExtratoItem(
                            selectedExtratoItem?.id === item.id ? null : item
                          )}
                        />
                      </TableCell>
                      <TableCell className="text-sm">{formatDate(item.data)}</TableCell>
                      <TableCell className="text-sm max-w-[200px] truncate" title={item.descricao}>
                        {item.descricao}
                      </TableCell>
                      <TableCell className={`text-right font-mono font-medium ${
                        item.tipo === "entrada" ? "text-green-600" : "text-red-600"
                      }`}>
                        {item.tipo === "entrada" ? "+" : "-"}{formatCurrency(item.valor)}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>

        {/* Contas do Sistema (Direita) */}
        <Card className="border-2 border-blue-200">
          <CardHeader className="bg-blue-50 border-b border-blue-200 pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg flex items-center gap-2">
                <DollarSign className="text-blue-600" size={20} />
                Contas do Sistema
              </CardTitle>
              <Badge variant="outline" className="bg-blue-100">
                {contasFiltradas.length} itens
              </Badge>
            </div>
            
            {/* Filtros das Contas */}
            <div className="flex flex-wrap gap-2 mt-3">
              <Select value={filtroContas} onValueChange={setFiltroContas}>
                <SelectTrigger className="w-36 h-8">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="todas">Todas</SelectItem>
                  <SelectItem value="quitadas">Quitadas</SelectItem>
                  <SelectItem value="a_pagar">A Pagar</SelectItem>
                  <SelectItem value="a_receber">A Receber</SelectItem>
                </SelectContent>
              </Select>
              
              <div className="relative flex-1">
                <Search className="absolute left-2 top-1/2 -translate-y-1/2 text-gray-400" size={14} />
                <Input 
                  placeholder="Buscar conta..."
                  value={buscaConta}
                  onChange={(e) => setBuscaConta(e.target.value)}
                  className="pl-8 h-8"
                />
              </div>
            </div>
          </CardHeader>
          <CardContent className="p-0 max-h-[500px] overflow-y-auto">
            {contasFiltradas.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 text-gray-500">
                <DollarSign size={40} className="mb-3 text-gray-300" />
                <p>Nenhuma conta encontrada</p>
                <p className="text-sm">Ajuste os filtros ou cadastre novas contas</p>
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow className="bg-blue-50/50">
                    <TableHead className="w-10"></TableHead>
                    <TableHead>Tipo</TableHead>
                    <TableHead>Vencimento</TableHead>
                    <TableHead>Descrição</TableHead>
                    <TableHead className="text-right">Valor</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {contasFiltradas.map((conta) => {
                    const isQuitada = conta.status === "quitada" || conta.status === "recebida";
                    return (
                      <TableRow 
                        key={`${conta.tipo}-${conta.id}`}
                        className={`cursor-pointer transition-colors ${
                          selectedConta?.id === conta.id && selectedConta?.tipo === conta.tipo
                            ? 'bg-blue-100 border-l-4 border-l-blue-500' 
                            : 'hover:bg-blue-50'
                        }`}
                        onClick={() => setSelectedConta(
                          selectedConta?.id === conta.id && selectedConta?.tipo === conta.tipo ? null : conta
                        )}
                      >
                        <TableCell>
                          <Checkbox 
                            checked={selectedConta?.id === conta.id && selectedConta?.tipo === conta.tipo}
                            onCheckedChange={() => setSelectedConta(
                              selectedConta?.id === conta.id ? null : conta
                            )}
                          />
                        </TableCell>
                        <TableCell>
                          <Badge className={
                            conta.tipo === "pagar" 
                              ? "bg-red-100 text-red-700 border-red-200" 
                              : "bg-green-100 text-green-700 border-green-200"
                          }>
                            {conta.tipo === "pagar" ? "Pagar" : "Receber"}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-sm">{formatDate(conta.data_vencimento)}</TableCell>
                        <TableCell className="text-sm max-w-[150px] truncate" title={conta.descricao || conta.favorecido}>
                          {conta.descricao || conta.favorecido || "-"}
                        </TableCell>
                        <TableCell className={`text-right font-mono font-medium ${
                          conta.tipo === "receber" ? "text-green-600" : "text-red-600"
                        }`}>
                          {formatCurrency(conta.valor)}
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Botão de Conciliar e Sugestões */}
      <div className="flex flex-col sm:flex-row justify-center gap-4">
        <Button
          onClick={handleConciliar}
          disabled={!selectedExtratoItem || !selectedConta || conciliando}
          size="lg"
          className="bg-green-600 hover:bg-green-700 px-8"
        >
          {conciliando ? (
            <Loader2 className="animate-spin mr-2" size={20} />
          ) : (
            <Link2 className="mr-2" size={20} />
          )}
          Conciliar Selecionados
        </Button>
        
        {/* Botão de Sugestões Automáticas */}
        <div className="flex items-center gap-2">
          <Select value={tolerancia.toString()} onValueChange={(v) => setTolerancia(parseInt(v))}>
            <SelectTrigger className="w-40">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="0">Valor Exato</SelectItem>
              <SelectItem value="1">Tolerância 1%</SelectItem>
              <SelectItem value="2">Tolerância 2%</SelectItem>
              <SelectItem value="5">Tolerância 5%</SelectItem>
              <SelectItem value="10">Tolerância 10%</SelectItem>
            </SelectContent>
          </Select>
          
          <Button
            onClick={gerarSugestoes}
            disabled={extratosFiltrados.length === 0 || contasFiltradas.length === 0 || processandoSugestoes}
            size="lg"
            className="bg-purple-600 hover:bg-purple-700 px-6"
          >
            {processandoSugestoes ? (
              <Loader2 className="animate-spin mr-2" size={20} />
            ) : (
              <Sparkles className="mr-2" size={20} />
            )}
            Sugerir Automático
          </Button>
        </div>
      </div>

      {/* Painel de Sugestões Automáticas */}
      {showSugestoes && sugestoes.length > 0 && (
        <Card className="border-2 border-purple-300 bg-purple-50/50">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg flex items-center gap-2">
                <Sparkles className="text-purple-600" size={20} />
                Sugestões de Conciliação
                <Badge className="bg-purple-100 text-purple-700 ml-2">
                  {sugestoes.length} sugestão(ões)
                </Badge>
              </CardTitle>
              <div className="flex gap-2">
                <Button
                  onClick={aceitarTodasSugestoes}
                  disabled={conciliando}
                  size="sm"
                  className="bg-green-600 hover:bg-green-700"
                >
                  <Zap size={16} className="mr-1" />
                  Aceitar Todas
                </Button>
                <Button
                  onClick={() => { setSugestoes([]); setShowSugestoes(false); }}
                  variant="outline"
                  size="sm"
                >
                  <X size={16} className="mr-1" />
                  Fechar
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent className="p-0 max-h-[400px] overflow-y-auto">
            <Table>
              <TableHeader>
                <TableRow className="bg-purple-100/50">
                  <TableHead>Match</TableHead>
                  <TableHead>Extrato</TableHead>
                  <TableHead className="text-right">Valor Extrato</TableHead>
                  <TableHead>Conta</TableHead>
                  <TableHead className="text-right">Valor Conta</TableHead>
                  <TableHead className="text-center">Ações</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {sugestoes.map((sugestao) => (
                  <TableRow key={sugestao.id} className="hover:bg-purple-50">
                    <TableCell>
                      <div className="flex items-center gap-1">
                        <div className={`w-3 h-3 rounded-full ${
                          parseFloat(sugestao.percentMatch) === 100 
                            ? 'bg-green-500' 
                            : parseFloat(sugestao.percentMatch) >= 98 
                            ? 'bg-yellow-500' 
                            : 'bg-orange-500'
                        }`}></div>
                        <span className={`text-sm font-medium ${
                          parseFloat(sugestao.percentMatch) === 100 
                            ? 'text-green-600' 
                            : parseFloat(sugestao.percentMatch) >= 98 
                            ? 'text-yellow-600' 
                            : 'text-orange-600'
                        }`}>
                          {sugestao.percentMatch}%
                        </span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div>
                        <p className="text-sm font-medium truncate max-w-[150px]" title={sugestao.extrato.descricao}>
                          {sugestao.extrato.descricao}
                        </p>
                        <p className="text-xs text-gray-500">{formatDate(sugestao.extrato.data)}</p>
                      </div>
                    </TableCell>
                    <TableCell className={`text-right font-mono ${
                      sugestao.extrato.tipo === "entrada" ? "text-green-600" : "text-red-600"
                    }`}>
                      {sugestao.extrato.tipo === "entrada" ? "+" : "-"}{formatCurrency(sugestao.extrato.valor)}
                    </TableCell>
                    <TableCell>
                      <div>
                        <p className="text-sm font-medium truncate max-w-[150px]" title={sugestao.conta.descricao || sugestao.conta.favorecido}>
                          {sugestao.conta.descricao || sugestao.conta.favorecido}
                        </p>
                        <Badge className={`text-xs ${
                          sugestao.conta.tipo === "pagar" 
                            ? "bg-red-100 text-red-700" 
                            : "bg-green-100 text-green-700"
                        }`}>
                          {sugestao.conta.tipo === "pagar" ? "A Pagar" : "A Receber"}
                        </Badge>
                      </div>
                    </TableCell>
                    <TableCell className={`text-right font-mono ${
                      sugestao.conta.tipo === "receber" ? "text-green-600" : "text-red-600"
                    }`}>
                      {formatCurrency(sugestao.conta.valor)}
                    </TableCell>
                    <TableCell>
                      <div className="flex justify-center gap-1">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => aceitarSugestao(sugestao)}
                          disabled={conciliando}
                          className="text-green-600 hover:bg-green-50"
                          title="Aceitar sugestão"
                        >
                          <Check size={18} />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => rejeitarSugestao(sugestao.id)}
                          className="text-red-600 hover:bg-red-50"
                          title="Rejeitar sugestão"
                        >
                          <X size={18} />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      {/* Detalhes da Seleção */}
      {(selectedExtratoItem || selectedConta) && (
        <Card className="border-2 border-dashed border-gray-300">
          <CardContent className="p-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {selectedExtratoItem && (
                <div className="p-3 bg-yellow-50 rounded-lg">
                  <p className="text-xs font-medium text-yellow-600 mb-1">EXTRATO SELECIONADO</p>
                  <p className="font-medium">{selectedExtratoItem.descricao}</p>
                  <p className="text-sm text-gray-600">{formatDate(selectedExtratoItem.data)}</p>
                  <p className={`text-lg font-bold ${selectedExtratoItem.tipo === "entrada" ? "text-green-600" : "text-red-600"}`}>
                    {selectedExtratoItem.tipo === "entrada" ? "+" : "-"}{formatCurrency(selectedExtratoItem.valor)}
                  </p>
                </div>
              )}
              
              {selectedConta && (
                <div className="p-3 bg-blue-50 rounded-lg">
                  <p className="text-xs font-medium text-blue-600 mb-1">CONTA SELECIONADA</p>
                  <p className="font-medium">{selectedConta.descricao || selectedConta.favorecido}</p>
                  <p className="text-sm text-gray-600">Vencimento: {formatDate(selectedConta.data_vencimento)}</p>
                  <p className={`text-lg font-bold ${selectedConta.tipo === "receber" ? "text-green-600" : "text-red-600"}`}>
                    {formatCurrency(selectedConta.valor)}
                  </p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Lista de Conciliações Realizadas */}
      {conciliacoes.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <CheckCircle2 className="text-green-600" size={20} />
              Conciliações Realizadas
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Data Conciliação</TableHead>
                  <TableHead>Extrato</TableHead>
                  <TableHead>Conta</TableHead>
                  <TableHead className="text-right">Valor</TableHead>
                  <TableHead className="text-center">Ações</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {conciliacoes.slice(0, 10).map((conc) => (
                  <TableRow key={conc.id}>
                    <TableCell>{formatDate(conc.created_at)}</TableCell>
                    <TableCell className="max-w-[200px] truncate">{conc.extrato_descricao}</TableCell>
                    <TableCell className="max-w-[200px] truncate">{conc.conta_descricao}</TableCell>
                    <TableCell className="text-right font-mono">{formatCurrency(conc.valor)}</TableCell>
                    <TableCell className="text-center">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDesfazerConciliacao(conc.id)}
                        className="text-red-600 hover:bg-red-50"
                      >
                        <Unlink size={16} />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      {/* Modal de Importação de Extrato */}
      <Dialog open={showImportModal} onOpenChange={setShowImportModal}>
        <DialogContent className="sm:max-w-[450px]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Upload className="text-[#D4A000]" size={20} />
              Importar Extrato Bancário
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label className="flex items-center gap-2">
                <Building2 size={16} className="text-gray-500" />
                Conta Bancária *
              </Label>
              <Select 
                value={selectedContaBancariaImport} 
                onValueChange={setSelectedContaBancariaImport}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Selecione a conta do extrato..." />
                </SelectTrigger>
                <SelectContent>
                  {contasBancarias.map(conta => (
                    <SelectItem key={conta.id} value={conta.id}>
                      <div className="flex items-center gap-2">
                        <Building2 size={14} />
                        {conta.banco} - Ag: {conta.agencia} / CC: {conta.conta}
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <p className="text-xs text-gray-500">
                O extrato será vinculado a esta conta bancária
              </p>
            </div>
            
            <div className="flex gap-3">
              <Button variant="outline" onClick={() => setShowImportModal(false)} className="flex-1">
                Cancelar
              </Button>
              <Button 
                onClick={() => {
                  if (!selectedContaBancariaImport) {
                    toast.error("Selecione uma conta bancária");
                    return;
                  }
                  fileInputRef.current?.click();
                }}
                disabled={!selectedContaBancariaImport || importando}
                className="flex-1 bg-[#D4A000] hover:bg-yellow-600"
              >
                {importando ? (
                  <Loader2 className="animate-spin mr-2" size={18} />
                ) : (
                  <Upload size={18} className="mr-2" />
                )}
                Selecionar PDF
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
