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
  Zap
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
  
  // Contas bancárias
  const [contasBancarias, setContasBancarias] = useState([]);
  const [selectedContaBancaria, setSelectedContaBancaria] = useState("");
  
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
      const [contasBancariasRes, conciliacoesRes] = await Promise.all([
        axios.get(`${API}/admin/contas-bancarias?ativo=true`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API}/conciliacao`, { headers: { Authorization: `Bearer ${token}` } }).catch(() => ({ data: [] }))
      ]);
      
      setContasBancarias(contasBancariasRes.data);
      setConciliacoes(conciliacoesRes.data || []);
      
      // Se tiver uma conta bancária selecionada, buscar extratos
      if (contasBancariasRes.data.length > 0) {
        setSelectedContaBancaria(contasBancariasRes.data[0].id);
        await fetchExtratosEContas(contasBancariasRes.data[0].id);
      }
    } catch (error) {
      console.error("Erro ao carregar dados:", error);
      toast.error("Erro ao carregar dados");
    } finally {
      setLoading(false);
    }
  };

  const fetchExtratosEContas = async (contaBancariaId) => {
    try {
      const [extratosRes, contasPagarRes, contasReceberRes] = await Promise.all([
        axios.get(`${API}/conciliacao/extratos/${contaBancariaId}`, { headers: { Authorization: `Bearer ${token}` } }).catch(() => ({ data: [] })),
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
    
    if (!selectedContaBancaria) {
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
    formData.append("conta_bancaria_id", selectedContaBancaria);
    
    try {
      const response = await axios.post(`${API}/conciliacao/importar-extrato`, formData, {
        headers: { 
          Authorization: `Bearer ${token}`,
          "Content-Type": "multipart/form-data"
        }
      });
      
      toast.success(`${response.data.count || 0} movimentações importadas!`);
      await fetchExtratosEContas(selectedContaBancaria);
    } catch (error) {
      console.error("Erro ao importar extrato:", error);
      toast.error(error.response?.data?.detail || "Erro ao importar extrato PDF");
    } finally {
      setImportando(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
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
            onClick={() => fileInputRef.current?.click()}
            disabled={importando || !selectedContaBancaria}
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

      {/* Seleção de Conta Bancária */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row gap-4 items-end">
            <div className="flex-1">
              <Label>Conta Bancária</Label>
              <Select 
                value={selectedContaBancaria} 
                onValueChange={(value) => {
                  setSelectedContaBancaria(value);
                  fetchExtratosEContas(value);
                }}
              >
                <SelectTrigger className="mt-1">
                  <SelectValue placeholder="Selecione uma conta..." />
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
            </div>
            
            <Button 
              variant="outline" 
              onClick={() => fetchExtratosEContas(selectedContaBancaria)}
              disabled={!selectedContaBancaria}
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

      {/* Botão de Conciliar */}
      <div className="flex justify-center">
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
      </div>

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
    </div>
  );
}
