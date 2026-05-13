import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "@/App";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { MaskedDateInput } from "@/components/MaskedDateInput";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
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
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";
import { 
  ArrowLeftRight, 
  Plus, 
  Trash2, 
  ArrowUpCircle, 
  ArrowDownCircle,
  RefreshCw,
  Loader2,
  Filter,
  FileX,
  Repeat,
  Undo2,
  Settings,
  Building2
} from "lucide-react";
import { formatCurrency, parseCurrency, formatCPFouCNPJ } from "@/utils/masks";

export default function MovimentacoesPage() {
  const [movimentacoes, setMovimentacoes] = useState([]);
  const [contasBancarias, setContasBancarias] = useState([]);
  const [centrosCusto, setCentrosCusto] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [salvando, setSalvando] = useState(false);
  
  // Filtros
  const [filterTipo, setFilterTipo] = useState("todos");
  const [filterCategoria, setFilterCategoria] = useState("todos");
  const [filterContaBancaria, setFilterContaBancaria] = useState("todos");
  const [filterCentroCusto, setFilterCentroCusto] = useState("todos");
  
  // Formulário
  const [formData, setFormData] = useState({
    tipo: "transferencia",
    descricao: "",
    valor: "",
    data_movimentacao: new Date().toISOString().split("T")[0],
    conta_bancaria_origem_id: "",
    conta_bancaria_origem_nome: "",
    centro_custo_origem_id: "",
    centro_custo_origem_nome: "",
    conta_bancaria_destino_id: "",
    conta_bancaria_destino_nome: "",
    centro_custo_destino_id: "",
    centro_custo_destino_nome: "",
    categoria: "transferencia_interna",
    documento_referencia: "",
    observacoes: ""
  });

  const categorias = [
    { value: "cancelamento_nf", label: "Cancelamento de NF", icon: FileX },
    { value: "estorno", label: "Estorno", icon: Undo2 },
    { value: "devolucao", label: "Devolução", icon: Repeat },
    { value: "transferencia_interna", label: "Transferência Interna", icon: ArrowLeftRight },
    { value: "ajuste", label: "Ajuste de Saldo", icon: Settings },
    { value: "outros", label: "Outros", icon: Building2 }
  ];

  const tipos = [
    { value: "entrada", label: "Entrada", icon: ArrowDownCircle, color: "text-green-600" },
    { value: "saida", label: "Saída", icon: ArrowUpCircle, color: "text-red-600" },
    { value: "transferencia", label: "Transferência", icon: ArrowLeftRight, color: "text-blue-600" }
  ];

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    fetchMovimentacoes();
  }, [filterTipo, filterCategoria, filterContaBancaria, filterCentroCusto]);

  const fetchData = async () => {
    try {
      const [contasRes, centrosRes] = await Promise.all([
        axios.get(`${API}/admin/contas-bancarias`),
        axios.get(`${API}/admin/centros-custo`)
      ]);
      setContasBancarias(contasRes.data);
      setCentrosCusto(centrosRes.data);
    } catch (error) {
      console.error("Erro ao carregar dados:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchMovimentacoes = async () => {
    try {
      const params = new URLSearchParams();
      if (filterTipo !== "todos") params.append("tipo", filterTipo);
      if (filterCategoria !== "todos") params.append("categoria", filterCategoria);
      if (filterContaBancaria !== "todos") params.append("conta_bancaria_id", filterContaBancaria);
      if (filterCentroCusto !== "todos") params.append("centro_custo_id", filterCentroCusto);
      
      const response = await axios.get(`${API}/admin/movimentacoes?${params.toString()}`);
      setMovimentacoes(response.data);
    } catch (error) {
      console.error("Erro ao carregar movimentações:", error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.descricao.trim()) {
      toast.error("Informe a descrição da movimentação");
      return;
    }
    
    const valor = parseCurrency(formData.valor);
    if (!valor || valor <= 0) {
      toast.error("Informe um valor válido");
      return;
    }
    
    // Validações por tipo
    if (formData.tipo === "entrada" && !formData.conta_bancaria_destino_id) {
      toast.error("Selecione a conta de destino para a entrada");
      return;
    }
    
    if (formData.tipo === "saida" && !formData.conta_bancaria_origem_id) {
      toast.error("Selecione a conta de origem para a saída");
      return;
    }
    
    if (formData.tipo === "transferencia") {
      if (!formData.conta_bancaria_origem_id && !formData.centro_custo_origem_id) {
        toast.error("Selecione a origem da transferência");
        return;
      }
      if (!formData.conta_bancaria_destino_id && !formData.centro_custo_destino_id) {
        toast.error("Selecione o destino da transferência");
        return;
      }
    }
    
    setSalvando(true);
    try {
      // Buscar nomes
      let dados = { ...formData, valor };
      
      if (formData.conta_bancaria_origem_id) {
        const conta = contasBancarias.find(c => c.id === formData.conta_bancaria_origem_id);
        dados.conta_bancaria_origem_nome = conta?.nome || "";
      }
      if (formData.conta_bancaria_destino_id) {
        const conta = contasBancarias.find(c => c.id === formData.conta_bancaria_destino_id);
        dados.conta_bancaria_destino_nome = conta?.nome || "";
      }
      if (formData.centro_custo_origem_id) {
        const centro = centrosCusto.find(c => c.id === formData.centro_custo_origem_id);
        dados.centro_custo_origem_nome = centro?.nome || "";
      }
      if (formData.centro_custo_destino_id) {
        const centro = centrosCusto.find(c => c.id === formData.centro_custo_destino_id);
        dados.centro_custo_destino_nome = centro?.nome || "";
      }
      
      await axios.post(`${API}/admin/movimentacoes`, dados);
      toast.success("Movimentação registrada com sucesso!");
      setIsModalOpen(false);
      resetForm();
      fetchMovimentacoes();
      fetchData(); // Atualizar saldos
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao registrar movimentação");
    } finally {
      setSalvando(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Excluir esta movimentação? Os saldos serão revertidos.")) return;
    
    try {
      await axios.delete(`${API}/admin/movimentacoes/${id}`);
      toast.success("Movimentação excluída e saldos revertidos!");
      fetchMovimentacoes();
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao excluir");
    }
  };

  const resetForm = () => {
    setFormData({
      tipo: "transferencia",
      descricao: "",
      valor: "",
      data_movimentacao: new Date().toISOString().split("T")[0],
      conta_bancaria_origem_id: "",
      conta_bancaria_origem_nome: "",
      centro_custo_origem_id: "",
      centro_custo_origem_nome: "",
      conta_bancaria_destino_id: "",
      conta_bancaria_destino_nome: "",
      centro_custo_destino_id: "",
      centro_custo_destino_nome: "",
      categoria: "transferencia_interna",
      documento_referencia: "",
      observacoes: ""
    });
  };

  const getTipoBadge = (tipo) => {
    const config = tipos.find(t => t.value === tipo);
    if (!config) return null;
    const Icon = config.icon;
    return (
      <span className={`inline-flex items-center gap-1 ${config.color}`}>
        <Icon size={14} />
        {config.label}
      </span>
    );
  };

  const getCategoriaBadge = (categoria) => {
    const cat = categorias.find(c => c.value === categoria);
    return cat?.label || categoria;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Movimentação de Contas</h1>
          <p className="text-gray-500 text-sm mt-1">
            Transferências, estornos, devoluções e ajustes entre contas e centros de custo
          </p>
        </div>
        <Button onClick={() => setIsModalOpen(true)} data-testid="btn-nova-movimentacao">
          <Plus size={16} className="mr-2" />
          Nova Movimentação
        </Button>
      </div>

      {/* Filtros */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            <div>
              <Label>Tipo</Label>
              <Select value={filterTipo} onValueChange={setFilterTipo}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="todos">Todos</SelectItem>
                  {tipos.map(t => (
                    <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Categoria</Label>
              <Select value={filterCategoria} onValueChange={setFilterCategoria}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="todos">Todas</SelectItem>
                  {categorias.map(c => (
                    <SelectItem key={c.value} value={c.value}>{c.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Conta Bancária</Label>
              <Select value={filterContaBancaria} onValueChange={setFilterContaBancaria}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="todos">Todas</SelectItem>
                  {contasBancarias.map(c => (
                    <SelectItem key={c.id} value={c.id}>{c.nome}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Centro de Custo</Label>
              <Select value={filterCentroCusto} onValueChange={setFilterCentroCusto}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="todos">Todos</SelectItem>
                  {centrosCusto.map(c => (
                    <SelectItem key={c.id} value={c.id}>{c.nome}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-end">
              <Button variant="outline" onClick={fetchMovimentacoes} className="w-full">
                <Filter size={16} className="mr-2" />
                Filtrar
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Lista de Movimentações */}
      <Card>
        <CardContent className="pt-6">
          {movimentacoes.length === 0 ? (
            <p className="text-gray-500 text-center py-8">Nenhuma movimentação encontrada.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="text-left p-3">Nº</th>
                    <th className="text-left p-3">Tipo</th>
                    <th className="text-left p-3">Descrição</th>
                    <th className="text-left p-3">Origem</th>
                    <th className="text-left p-3">Destino</th>
                    <th className="text-right p-3">Valor</th>
                    <th className="text-left p-3">Data</th>
                    <th className="text-center p-3">Ações</th>
                  </tr>
                </thead>
                <tbody>
                  {movimentacoes.map(mov => (
                    <tr key={mov.id} className="border-b hover:bg-gray-50">
                      <td className="p-3 font-mono">{mov.numero}</td>
                      <td className="p-3">{getTipoBadge(mov.tipo)}</td>
                      <td className="p-3">
                        <div className="font-medium">{mov.descricao}</div>
                        <div className="text-xs text-gray-500">{getCategoriaBadge(mov.categoria)}</div>
                      </td>
                      <td className="p-3">
                        <div>{mov.conta_bancaria_origem_nome || "-"}</div>
                        {mov.centro_custo_origem_nome && (
                          <div className="text-xs text-gray-500">{mov.centro_custo_origem_nome}</div>
                        )}
                      </td>
                      <td className="p-3">
                        <div>{mov.conta_bancaria_destino_nome || "-"}</div>
                        {mov.centro_custo_destino_nome && (
                          <div className="text-xs text-gray-500">{mov.centro_custo_destino_nome}</div>
                        )}
                      </td>
                      <td className="p-3 text-right font-medium">
                        <span className={mov.tipo === "entrada" ? "text-green-600" : mov.tipo === "saida" ? "text-red-600" : "text-blue-600"}>
                          {formatCurrency(mov.valor)}
                        </span>
                      </td>
                      <td className="p-3 text-gray-500">
                        {mov.data_movimentacao}
                      </td>
                      <td className="p-3 text-center">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDelete(mov.id)}
                          title="Excluir"
                        >
                          <Trash2 size={14} className="text-red-500" />
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Modal Nova Movimentação */}
      <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Nova Movimentação</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Tipo e Categoria */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Tipo de Movimentação *</Label>
                <Select 
                  value={formData.tipo} 
                  onValueChange={(value) => setFormData({...formData, tipo: value})}
                >
                  <SelectTrigger data-testid="select-tipo-mov">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {tipos.map(t => {
                      const Icon = t.icon;
                      return (
                        <SelectItem key={t.value} value={t.value}>
                          <span className={`flex items-center gap-2 ${t.color}`}>
                            <Icon size={14} />
                            {t.label}
                          </span>
                        </SelectItem>
                      );
                    })}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Categoria *</Label>
                <Select 
                  value={formData.categoria} 
                  onValueChange={(value) => setFormData({...formData, categoria: value})}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {categorias.map(c => (
                      <SelectItem key={c.value} value={c.value}>{c.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Descrição */}
            <div>
              <Label>Descrição *</Label>
              <Input
                data-testid="input-descricao-mov"
                value={formData.descricao}
                onChange={(e) => setFormData({...formData, descricao: e.target.value})}
                placeholder="Ex: Estorno NF 12345, Transferência entre filiais, etc."
              />
            </div>

            {/* Valor e Data */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Valor *</Label>
                <Input
                  data-testid="input-valor-mov"
                  value={formData.valor}
                  onChange={(e) => setFormData({...formData, valor: formatCurrency(e.target.value)})}
                  placeholder="R$ 0,00"
                />
              </div>
              <div>
                <Label>Data da Movimentação *</Label>
                <MaskedDateInput
                  value={formData.data_movimentacao}
                  onChange={(v) => setFormData({...formData, data_movimentacao: v})}
                />
              </div>
            </div>

            {/* Origem (para saída e transferência) */}
            {(formData.tipo === "saida" || formData.tipo === "transferencia") && (
              <div className="border border-red-200 rounded-lg p-4 bg-red-50/50">
                <h4 className="font-medium text-red-700 mb-3 flex items-center gap-2">
                  <ArrowUpCircle size={16} />
                  Origem (De onde sai o valor)
                </h4>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Conta Bancária</Label>
                    <Select 
                      value={formData.conta_bancaria_origem_id} 
                      onValueChange={(value) => setFormData({...formData, conta_bancaria_origem_id: value})}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Selecione..." />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="none">Nenhuma</SelectItem>
                        {contasBancarias.map(c => (
                          <SelectItem key={c.id} value={c.id}>
                            {c.nome} ({formatCurrency(c.saldo_atual || 0)})
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label>Centro de Custo</Label>
                    <Select 
                      value={formData.centro_custo_origem_id} 
                      onValueChange={(value) => setFormData({...formData, centro_custo_origem_id: value})}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Selecione..." />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="none">Nenhum</SelectItem>
                        {centrosCusto.map(c => (
                          <SelectItem key={c.id} value={c.id}>{c.nome}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </div>
            )}

            {/* Destino (para entrada e transferência) */}
            {(formData.tipo === "entrada" || formData.tipo === "transferencia") && (
              <div className="border border-green-200 rounded-lg p-4 bg-green-50/50">
                <h4 className="font-medium text-green-700 mb-3 flex items-center gap-2">
                  <ArrowDownCircle size={16} />
                  Destino (Para onde vai o valor)
                </h4>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Conta Bancária</Label>
                    <Select 
                      value={formData.conta_bancaria_destino_id} 
                      onValueChange={(value) => setFormData({...formData, conta_bancaria_destino_id: value})}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Selecione..." />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="none">Nenhuma</SelectItem>
                        {contasBancarias.map(c => (
                          <SelectItem key={c.id} value={c.id}>
                            {c.nome} ({formatCurrency(c.saldo_atual || 0)})
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label>Centro de Custo</Label>
                    <Select 
                      value={formData.centro_custo_destino_id} 
                      onValueChange={(value) => setFormData({...formData, centro_custo_destino_id: value})}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Selecione..." />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="none">Nenhum</SelectItem>
                        {centrosCusto.map(c => (
                          <SelectItem key={c.id} value={c.id}>{c.nome}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </div>
            )}

            {/* Documento de Referência */}
            <div>
              <Label>Documento de Referência</Label>
              <Input
                value={formData.documento_referencia}
                onChange={(e) => setFormData({...formData, documento_referencia: e.target.value})}
                placeholder="Ex: NF 12345, Recibo 001, etc."
              />
            </div>

            {/* Observações */}
            <div>
              <Label>Observações</Label>
              <Textarea
                value={formData.observacoes}
                onChange={(e) => setFormData({...formData, observacoes: e.target.value})}
                placeholder="Detalhes adicionais sobre a movimentação..."
                rows={3}
              />
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setIsModalOpen(false)}>
                Cancelar
              </Button>
              <Button type="submit" disabled={salvando}>
                {salvando ? <Loader2 className="animate-spin mr-2" size={16} /> : null}
                Registrar Movimentação
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
