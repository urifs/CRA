import { useState, useEffect } from "react";
import axios from "axios";
import { toast } from "sonner";
import { API } from "@/App";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { 
  Plus, 
  Edit2, 
  Trash2, 
  Fuel, 
  Loader2,
  Search,
  Truck,
  Droplet,
  CircleDot,
  TrendingDown,
  User,
  MapPin,
  X,
  Package
} from "lucide-react";

const UNIDADES_MEDIDA = [
  { value: "L", label: "Litros (L)" },
  { value: "ML", label: "Mililitros (ML)" },
  { value: "KG", label: "Quilogramas (KG)" },
  { value: "G", label: "Gramas (G)" },
  { value: "UN", label: "Unidade (UN)" }
];

export default function CombustivelPage() {
  const [loading, setLoading] = useState(true);
  const [registros, setRegistros] = useState([]);
  const [abastecedores, setAbastecedores] = useState([]);
  const [machines, setMachines] = useState([]);
  const [operadores, setOperadores] = useState([]);
  const [stockItems, setStockItems] = useState([]);
  const [postos, setPostos] = useState([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [activeTab, setActiveTab] = useState("registros");
  
  // Modal states
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isAbastecedorModalOpen, setIsAbastecedorModalOpen] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [editingAbastecedorId, setEditingAbastecedorId] = useState(null);
  
  // Form states - Formulário unificado de combustível
  const [formData, setFormData] = useState({
    machine_id: "",
    data: new Date().toISOString().split("T")[0],
    tipo_registro: "abastecido",
    tipo_medicao: "litros",
    hora_km_inicial: "",
    litros_diesel: "",
    litros_oleo: "",
    litros_graxa: "",
    fonte_abastecimento: "externo", // "interno", "externo", "posto"
    veiculo_abastecedor_id: "",
    posto_id: "",
    operador_id: "",
    observacoes: ""
  });
  
  // Formulário de veículo abastecedor com compartimentos dinâmicos
  const [abastecedorForm, setAbastecedorForm] = useState({
    machine_id: "",
    capacidade_diesel: "",
    capacidade_graxa: "",
    litros_diesel: "",
    litros_graxa: "",
    operador_id: "",
    compartimentos_oleo: [] // Lista de compartimentos de óleo
  });
  
  const token = localStorage.getItem("token");

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [registrosRes, abastecedoresRes, machinesRes, operadoresRes, stockRes, cadastrosRes] = await Promise.all([
        axios.get(`${API}/combustivel`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API}/combustivel/abastecedores`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API}/machines`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API}/operadores`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API}/stock/items`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API}/admin/cadastros`, { headers: { Authorization: `Bearer ${token}` } })
      ]);
      
      setRegistros(registrosRes.data);
      setAbastecedores(abastecedoresRes.data);
      setMachines(machinesRes.data);
      setOperadores(operadoresRes.data);
      setStockItems(stockRes.data);
      // Filtrar apenas fornecedores (postos parceiros)
      setPostos(cadastrosRes.data.filter(c => c.tipo_cadastro === "fornecedor" || c.tipo_cadastro === "cli_forn"));
    } catch (error) {
      toast.error("Erro ao carregar dados");
    } finally {
      setLoading(false);
    }
  };

  // Handlers para registro de combustível
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.machine_id) {
      toast.error("Selecione uma máquina");
      return;
    }
    
    try {
      const payload = {
        ...formData,
        litros_diesel: parseFloat(formData.litros_diesel) || 0,
        litros_oleo: parseFloat(formData.litros_oleo) || 0,
        litros_graxa: parseFloat(formData.litros_graxa) || 0,
        hora_km_inicial: parseFloat(formData.hora_km_inicial) || 0
      };

      if (editingId) {
        await axios.put(`${API}/combustivel/${editingId}`, payload, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success("Registro atualizado com sucesso!");
      } else {
        await axios.post(`${API}/combustivel`, payload, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success("Registro criado com sucesso!");
      }
      
      setIsModalOpen(false);
      resetForm();
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao salvar registro");
    }
  };

  const handleEditRegistro = (registro) => {
    setEditingId(registro.id);
    setFormData({
      machine_id: registro.machine_id || "",
      data: registro.data || new Date().toISOString().split("T")[0],
      tipo_registro: registro.tipo_registro || "abastecido",
      tipo_medicao: registro.tipo_medicao || "litros",
      hora_km_inicial: registro.hora_km_inicial?.toString() || "",
      litros_diesel: registro.litros_diesel?.toString() || "",
      litros_oleo: registro.litros_oleo?.toString() || "",
      litros_graxa: registro.litros_graxa?.toString() || "",
      fonte_abastecimento: registro.fonte_abastecimento || "externo",
      veiculo_abastecedor_id: registro.veiculo_abastecedor_id || "",
      posto_id: registro.posto_id || "",
      operador_id: registro.operador_id || "",
      observacoes: registro.observacoes || ""
    });
    setIsModalOpen(true);
  };

  const handleDelete = async (id) => {
    if (!confirm("Tem certeza que deseja excluir este registro?")) return;
    
    try {
      await axios.delete(`${API}/combustivel/${id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success("Registro excluído com sucesso!");
      fetchData();
    } catch (error) {
      toast.error("Erro ao excluir registro");
    }
  };

  const resetForm = () => {
    setEditingId(null);
    setFormData({
      machine_id: "",
      data: new Date().toISOString().split("T")[0],
      tipo_registro: "abastecido",
      tipo_medicao: "litros",
      hora_km_inicial: "",
      litros_diesel: "",
      litros_oleo: "",
      litros_graxa: "",
      fonte_abastecimento: "externo",
      veiculo_abastecedor_id: "",
      posto_id: "",
      operador_id: "",
      observacoes: ""
    });
  };

  // Handlers para veículos abastecedores
  const handleAbastecedorSubmit = async (e) => {
    e.preventDefault();
    
    if (!abastecedorForm.machine_id) {
      toast.error("Selecione uma máquina");
      return;
    }
    
    try {
      const payload = {
        machine_id: abastecedorForm.machine_id,
        capacidade_diesel: parseFloat(abastecedorForm.capacidade_diesel) || 0,
        capacidade_oleo: 0, // Legado - agora usa compartimentos
        capacidade_graxa: parseFloat(abastecedorForm.capacidade_graxa) || 0,
        litros_diesel: parseFloat(abastecedorForm.litros_diesel) || 0,
        litros_oleo: 0, // Legado
        litros_graxa: parseFloat(abastecedorForm.litros_graxa) || 0,
        operador_id: abastecedorForm.operador_id,
        compartimentos_oleo: abastecedorForm.compartimentos_oleo.map(c => ({
          id: c.id,
          item_estoque_id: c.item_estoque_id,
          unidade_medida: c.unidade_medida,
          capacidade: parseFloat(c.capacidade) || 0,
          quantidade_atual: parseFloat(c.quantidade_atual) || 0
        }))
      };

      if (editingAbastecedorId) {
        await axios.put(`${API}/combustivel/abastecedores/${editingAbastecedorId}`, payload, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success("Veículo tanque atualizado!");
      } else {
        await axios.post(`${API}/combustivel/abastecedores`, payload, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success("Veículo tanque cadastrado!");
      }
      
      setIsAbastecedorModalOpen(false);
      resetAbastecedorForm();
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao salvar veículo tanque");
    }
  };

  const handleEditAbastecedor = (abast) => {
    setEditingAbastecedorId(abast.id);
    setAbastecedorForm({
      machine_id: abast.machine_id,
      capacidade_diesel: abast.capacidade_diesel?.toString() || "",
      capacidade_graxa: abast.capacidade_graxa?.toString() || "",
      litros_diesel: abast.litros_diesel?.toString() || "",
      litros_graxa: abast.litros_graxa?.toString() || "",
      operador_id: abast.operador_id || "",
      compartimentos_oleo: abast.compartimentos_oleo || []
    });
    setIsAbastecedorModalOpen(true);
  };

  const handleDeleteAbastecedor = async (id) => {
    if (!confirm("Tem certeza que deseja remover este veículo tanque?")) return;
    
    try {
      await axios.delete(`${API}/combustivel/abastecedores/${id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success("Veículo tanque removido!");
      fetchData();
    } catch (error) {
      toast.error("Erro ao remover veículo tanque");
    }
  };

  const resetAbastecedorForm = () => {
    setEditingAbastecedorId(null);
    setAbastecedorForm({
      machine_id: "",
      capacidade_diesel: "",
      capacidade_graxa: "",
      litros_diesel: "",
      litros_graxa: "",
      operador_id: "",
      compartimentos_oleo: []
    });
  };

  // Adicionar compartimento de óleo
  const addCompartimentoOleo = () => {
    setAbastecedorForm(prev => ({
      ...prev,
      compartimentos_oleo: [
        ...prev.compartimentos_oleo,
        {
          id: `temp-${Date.now()}`,
          item_estoque_id: "",
          item_nome: "",
          unidade_medida: "L",
          capacidade: "",
          quantidade_atual: ""
        }
      ]
    }));
  };

  // Remover compartimento de óleo
  const removeCompartimentoOleo = (index) => {
    setAbastecedorForm(prev => ({
      ...prev,
      compartimentos_oleo: prev.compartimentos_oleo.filter((_, i) => i !== index)
    }));
  };

  // Atualizar compartimento de óleo
  const updateCompartimentoOleo = (index, field, value) => {
    setAbastecedorForm(prev => ({
      ...prev,
      compartimentos_oleo: prev.compartimentos_oleo.map((comp, i) => {
        if (i !== index) return comp;
        
        // Se estiver atualizando o item do estoque, buscar o nome
        if (field === "item_estoque_id") {
          const item = stockItems.find(s => s.id === value);
          return { ...comp, [field]: value, item_nome: item?.name || "" };
        }
        
        return { ...comp, [field]: value };
      })
    }));
  };

  // Helpers
  const getMachineName = (id) => machines.find(m => m.id === id)?.name || "Máquina não encontrada";
  const getOperadorName = (id) => operadores.find(o => o.id === id)?.nome || "-";
  const getPostoName = (id) => postos.find(p => p.id === id)?.nome_razao || "-";
  
  const formatDate = (dateStr) => {
    if (!dateStr) return "-";
    const [year, month, day] = dateStr.split("-");
    return `${day}/${month}/${year}`;
  };

  const calcPercentage = (current, capacity) => {
    if (!capacity || capacity === 0) return 0;
    return Math.min(100, Math.round((current / capacity) * 100));
  };

  const filteredRegistros = registros.filter(r => 
    r.machine_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    r.observacoes?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Máquinas disponíveis para serem abastecedores (que ainda não são)
  const machinesDisponiveis = machines.filter(m => 
    !abastecedores.some(a => a.machine_id === m.id)
  );

  // Filtrar itens do estoque que são óleos/lubrificantes
  const itensOleo = stockItems.filter(item => 
    item.name?.toLowerCase().includes("óleo") ||
    item.name?.toLowerCase().includes("oleo") ||
    item.name?.toLowerCase().includes("lubrificante") ||
    item.category_name?.toLowerCase().includes("óleo") ||
    item.category_name?.toLowerCase().includes("lubrificante")
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="animate-spin text-[#E31A1A]" size={48} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Controle de Combustível</h1>
          <p className="text-gray-500">Gerencie abastecimentos e veículos tanque</p>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full max-w-md grid-cols-2">
          <TabsTrigger value="registros" className="flex items-center gap-2">
            <Fuel size={16} /> Registros
          </TabsTrigger>
          <TabsTrigger value="abastecedores" className="flex items-center gap-2">
            <Truck size={16} /> Veículos Tanque
          </TabsTrigger>
        </TabsList>

        {/* Tab: Registros de Combustível */}
        <TabsContent value="registros" className="space-y-4">
          {/* Ações e Busca */}
          <div className="flex flex-col sm:flex-row gap-4 justify-between">
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={18} />
              <Input
                placeholder="Buscar registros..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            {/* Botão único de Novo Registro */}
            <Button 
              onClick={() => { resetForm(); setIsModalOpen(true); }} 
              className="bg-[#E31A1A] hover:bg-red-700"
              data-testid="btn-novo-registro"
            >
              <Plus size={18} className="mr-2" />
              Novo Registro de Combustível
            </Button>
          </div>

          {/* Lista de Registros */}
          <Card>
            <CardContent className="p-0">
              {filteredRegistros.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12 text-gray-500">
                  <Fuel size={48} className="mb-4 text-gray-300" />
                  <p>Nenhum registro encontrado</p>
                  <p className="text-sm">Clique no botão acima para criar um registro</p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Tipo</TableHead>
                      <TableHead>Máquina</TableHead>
                      <TableHead>Data</TableHead>
                      <TableHead className="text-right">Diesel (L)</TableHead>
                      <TableHead className="text-right">Óleo (L)</TableHead>
                      <TableHead className="text-right">Graxa (L)</TableHead>
                      <TableHead>Fonte</TableHead>
                      <TableHead>Operador</TableHead>
                      <TableHead className="text-right">Ações</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredRegistros.map((registro) => (
                      <TableRow 
                        key={registro.id} 
                        className="cursor-pointer hover:bg-gray-50"
                        onClick={() => handleEditRegistro(registro)}
                      >
                        <TableCell>
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                            registro.tipo_registro === "abastecedor" 
                              ? 'bg-green-100 text-green-700' 
                              : 'bg-blue-100 text-blue-700'
                          }`}>
                            {registro.tipo_registro === "abastecedor" ? "Entrada" : "Saída"}
                          </span>
                        </TableCell>
                        <TableCell className="font-medium">
                          <div className="flex items-center gap-2">
                            <Truck size={16} className="text-gray-400" />
                            {registro.machine_name}
                          </div>
                        </TableCell>
                        <TableCell>{formatDate(registro.data)}</TableCell>
                        <TableCell className="text-right font-mono">
                          {registro.litros_diesel > 0 ? `${registro.litros_diesel}L` : "-"}
                        </TableCell>
                        <TableCell className="text-right font-mono">
                          {registro.litros_oleo > 0 ? `${registro.litros_oleo}L` : "-"}
                        </TableCell>
                        <TableCell className="text-right font-mono">
                          {registro.litros_graxa > 0 ? `${registro.litros_graxa}L` : "-"}
                        </TableCell>
                        <TableCell>
                          {registro.tipo_registro === "abastecido" ? (
                            <span className={`text-xs ${
                              registro.fonte_abastecimento === "interno" 
                                ? 'text-purple-600' 
                                : registro.fonte_abastecimento === "posto"
                                ? 'text-blue-600'
                                : 'text-gray-500'
                            }`}>
                              {registro.fonte_abastecimento === "interno" 
                                ? registro.veiculo_abastecedor_nome || "Tanque Interno"
                                : registro.fonte_abastecimento === "posto"
                                ? registro.posto_nome || "Posto Parceiro"
                                : "Externo"}
                            </span>
                          ) : "-"}
                        </TableCell>
                        <TableCell className="text-sm">{registro.operador_nome || "-"}</TableCell>
                        <TableCell className="text-right">
                          <div className="flex justify-end gap-1">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={(e) => { e.stopPropagation(); handleEditRegistro(registro); }}
                              className="text-blue-600 hover:text-blue-700 hover:bg-blue-50"
                            >
                              <Edit2 size={16} />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={(e) => { e.stopPropagation(); handleDelete(registro.id); }}
                              className="text-red-600 hover:text-red-700 hover:bg-red-50"
                            >
                              <Trash2 size={16} />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab: Veículos Abastecedores */}
        <TabsContent value="abastecedores" className="space-y-4">
          <div className="flex justify-end">
            <Button 
              onClick={() => { resetAbastecedorForm(); setIsAbastecedorModalOpen(true); }}
              className="bg-[#E31A1A] hover:bg-red-700"
              data-testid="btn-cadastrar-tanque"
            >
              <Plus size={18} className="mr-2" />
              Cadastrar Veículo Tanque
            </Button>
          </div>

          {/* Cards dos Abastecedores */}
          {abastecedores.length === 0 ? (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12 text-gray-500">
                <Truck size={48} className="mb-4 text-gray-300" />
                <p>Nenhum veículo tanque cadastrado</p>
                <p className="text-sm">Cadastre uma máquina como veículo abastecedor</p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
              {abastecedores.map((abast) => {
                const dieselPercent = calcPercentage(abast.litros_diesel, abast.capacidade_diesel);
                const graxaPercent = calcPercentage(abast.litros_graxa, abast.capacidade_graxa);
                
                return (
                  <Card key={abast.id} className="col-span-1 overflow-hidden border-l-4 border-l-green-500">
                    <CardHeader className="pb-2 bg-gray-50">
                      <div className="flex justify-between items-start">
                        <div className="flex items-center gap-3">
                          <div className="w-12 h-12 bg-green-500 rounded-lg flex items-center justify-center">
                            <Truck className="text-white" size={24} />
                          </div>
                          <div>
                            <CardTitle className="text-lg">{abast.machine_name}</CardTitle>
                            {abast.operador_nome && (
                              <p className="text-sm text-gray-500 flex items-center gap-1">
                                <User size={12} /> {abast.operador_nome}
                              </p>
                            )}
                          </div>
                        </div>
                        <div className="flex gap-1">
                          <Button variant="ghost" size="sm" onClick={() => handleEditAbastecedor(abast)}>
                            <Edit2 size={16} />
                          </Button>
                          <Button 
                            variant="ghost" 
                            size="sm" 
                            className="text-red-600"
                            onClick={() => handleDeleteAbastecedor(abast.id)}
                          >
                            <Trash2 size={16} />
                          </Button>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-4 pt-4">
                      {/* Diesel */}
                      <div>
                        <div className="flex justify-between text-sm mb-1">
                          <span className="flex items-center gap-1 font-medium">
                            <Droplet size={14} className="text-yellow-600" /> Diesel
                          </span>
                          <span className="text-gray-600">
                            {abast.litros_diesel?.toFixed(0) || 0}L / {abast.capacidade_diesel?.toFixed(0) || 0}L
                          </span>
                        </div>
                        <Progress value={dieselPercent} className="h-3" />
                        <p className="text-xs text-right text-gray-500 mt-0.5">{dieselPercent}%</p>
                      </div>
                      
                      {/* Compartimentos de Óleo Dinâmicos */}
                      {abast.compartimentos_oleo?.length > 0 && (
                        <div className="space-y-3 border-t pt-3">
                          <p className="text-xs font-semibold text-gray-600 uppercase">Compartimentos de Óleo</p>
                          {abast.compartimentos_oleo.map((comp, idx) => {
                            const oleoPercent = calcPercentage(comp.quantidade_atual, comp.capacidade);
                            return (
                              <div key={comp.id || idx}>
                                <div className="flex justify-between text-sm mb-1">
                                  <span className="flex items-center gap-1 font-medium">
                                    <CircleDot size={14} className="text-blue-600" />
                                    {comp.item_nome || "Óleo"}
                                  </span>
                                  <span className="text-gray-600">
                                    {comp.quantidade_atual?.toFixed(1) || 0}{comp.unidade_medida} / {comp.capacidade?.toFixed(0) || 0}{comp.unidade_medida}
                                  </span>
                                </div>
                                <Progress value={oleoPercent} className="h-2" />
                              </div>
                            );
                          })}
                        </div>
                      )}
                      
                      {/* Graxa */}
                      <div>
                        <div className="flex justify-between text-sm mb-1">
                          <span className="flex items-center gap-1 font-medium">
                            <TrendingDown size={14} className="text-gray-600" /> Graxa
                          </span>
                          <span className="text-gray-600">
                            {abast.litros_graxa?.toFixed(0) || 0}L / {abast.capacidade_graxa?.toFixed(0) || 0}L
                          </span>
                        </div>
                        <Progress value={graxaPercent} className="h-3" />
                        <p className="text-xs text-right text-gray-500 mt-0.5">{graxaPercent}%</p>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* Modal Unificado de Registro de Combustível */}
      <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
        <DialogContent className="sm:max-w-[650px] max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Fuel className="text-[#E31A1A]" />
              {editingId ? "Editar Registro de Combustível" : "Novo Registro de Combustível"}
            </DialogTitle>
          </DialogHeader>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Tipo de Registro */}
            <div className="space-y-2">
              <Label>Tipo de Registro *</Label>
              <RadioGroup 
                value={formData.tipo_registro} 
                onValueChange={(value) => setFormData({...formData, tipo_registro: value})}
                className="flex gap-4"
              >
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="abastecido" id="tipo_abastecido" />
                  <Label htmlFor="tipo_abastecido" className="cursor-pointer font-normal">
                    Abastecimento (Saída)
                  </Label>
                </div>
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="abastecedor" id="tipo_abastecedor" />
                  <Label htmlFor="tipo_abastecedor" className="cursor-pointer font-normal">
                    Entrada no Tanque
                  </Label>
                </div>
              </RadioGroup>
            </div>

            {/* Info do tipo */}
            <div className={`p-3 rounded-lg ${
              formData.tipo_registro === "abastecedor" ? 'bg-green-50 border border-green-200' : 'bg-blue-50 border border-blue-200'
            }`}>
              <p className={`text-sm ${formData.tipo_registro === "abastecedor" ? 'text-green-700' : 'text-blue-700'}`}>
                {formData.tipo_registro === "abastecedor" 
                  ? "Registre a entrada de combustível no veículo tanque"
                  : "Registre o abastecimento de uma máquina"}
              </p>
            </div>

            {/* Máquina */}
            <div className="space-y-2">
              <Label>
                {formData.tipo_registro === "abastecedor" ? "Veículo Tanque *" : "Máquina a Abastecer *"}
              </Label>
              {formData.tipo_registro === "abastecedor" && abastecedores.length === 0 ? (
                <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                  <p className="text-sm text-yellow-700">
                    Nenhum veículo tanque cadastrado. Vá para a aba "Veículos Tanque" e cadastre um primeiro.
                  </p>
                </div>
              ) : (
                <Select 
                  value={formData.machine_id} 
                  onValueChange={(value) => setFormData({...formData, machine_id: value})}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Selecione..." />
                  </SelectTrigger>
                  <SelectContent>
                    {formData.tipo_registro === "abastecedor" 
                      ? abastecedores.map(a => (
                          <SelectItem key={a.machine_id} value={a.machine_id}>
                            <div className="flex items-center gap-2">
                              <Truck size={14} className="text-green-500" />
                              {a.machine_name}
                            </div>
                          </SelectItem>
                        ))
                      : machines.map(m => (
                          <SelectItem key={m.id} value={m.id}>
                            <div className="flex items-center gap-2">
                              <Truck size={14} />
                              {m.name}
                            </div>
                          </SelectItem>
                        ))
                    }
                  </SelectContent>
                </Select>
              )}
            </div>

            {/* Data */}
            <div className="space-y-2">
              <Label>Data *</Label>
              <Input
                type="date"
                value={formData.data}
                onChange={(e) => setFormData({...formData, data: e.target.value})}
                required
              />
            </div>

            {/* Fonte do Abastecimento - apenas para tipo "abastecido" */}
            {formData.tipo_registro === "abastecido" && (
              <div className="space-y-2">
                <Label>Fonte do Abastecimento *</Label>
                <RadioGroup 
                  value={formData.fonte_abastecimento} 
                  onValueChange={(value) => setFormData({...formData, fonte_abastecimento: value, veiculo_abastecedor_id: "", posto_id: ""})}
                  className="flex flex-col gap-2"
                >
                  <div className="flex items-center space-x-2">
                    <RadioGroupItem value="interno" id="fonte_interno" />
                    <Label htmlFor="fonte_interno" className="cursor-pointer font-normal flex items-center gap-2">
                      <Truck size={16} className="text-green-600" />
                      Veículo Tanque (Interno)
                    </Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <RadioGroupItem value="posto" id="fonte_posto" />
                    <Label htmlFor="fonte_posto" className="cursor-pointer font-normal flex items-center gap-2">
                      <MapPin size={16} className="text-blue-600" />
                      Posto Parceiro
                    </Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <RadioGroupItem value="externo" id="fonte_externo" />
                    <Label htmlFor="fonte_externo" className="cursor-pointer font-normal flex items-center gap-2">
                      <Fuel size={16} className="text-gray-600" />
                      Outro (Externo)
                    </Label>
                  </div>
                </RadioGroup>
              </div>
            )}

            {/* Seleção do veículo abastecedor se fonte for interna */}
            {formData.tipo_registro === "abastecido" && formData.fonte_abastecimento === "interno" && (
              <div className="space-y-2">
                <Label>Veículo Tanque *</Label>
                <Select 
                  value={formData.veiculo_abastecedor_id} 
                  onValueChange={(value) => setFormData({...formData, veiculo_abastecedor_id: value})}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Selecione o veículo tanque..." />
                  </SelectTrigger>
                  <SelectContent>
                    {abastecedores.map(a => (
                      <SelectItem key={a.id} value={a.id}>
                        <div className="flex items-center gap-2">
                          <Truck size={14} className="text-green-500" />
                          {a.machine_name} 
                          <span className="text-xs text-gray-400">
                            (Diesel: {a.litros_diesel?.toFixed(0)}L)
                          </span>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}

            {/* Seleção do posto parceiro */}
            {formData.tipo_registro === "abastecido" && formData.fonte_abastecimento === "posto" && (
              <div className="space-y-2">
                <Label>Posto Parceiro</Label>
                <Select 
                  value={formData.posto_id} 
                  onValueChange={(value) => setFormData({...formData, posto_id: value})}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Selecione o posto parceiro..." />
                  </SelectTrigger>
                  <SelectContent>
                    {postos.length === 0 ? (
                      <div className="p-2 text-sm text-gray-500 text-center">
                        Nenhum posto/fornecedor cadastrado
                      </div>
                    ) : (
                      postos.map(p => (
                        <SelectItem key={p.id} value={p.id}>
                          <div className="flex items-center gap-2">
                            <MapPin size={14} className="text-blue-500" />
                            {p.nome_razao}
                            {p.cidade && <span className="text-xs text-gray-400">({p.cidade})</span>}
                          </div>
                        </SelectItem>
                      ))
                    )}
                  </SelectContent>
                </Select>
                <p className="text-xs text-gray-500">
                  Cadastre postos parceiros em Administrativo → Cadastros como "Fornecedor"
                </p>
              </div>
            )}

            {/* Litros - 3 campos horizontais */}
            <div className="grid grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label className="flex items-center gap-1">
                  <Droplet size={14} className="text-yellow-600" />
                  Diesel (L)
                </Label>
                <Input
                  type="number"
                  step="0.1"
                  min="0"
                  placeholder="0"
                  value={formData.litros_diesel}
                  onChange={(e) => setFormData({...formData, litros_diesel: e.target.value})}
                />
              </div>
              <div className="space-y-2">
                <Label className="flex items-center gap-1">
                  <CircleDot size={14} className="text-blue-600" />
                  Óleo (L)
                </Label>
                <Input
                  type="number"
                  step="0.1"
                  min="0"
                  placeholder="0"
                  value={formData.litros_oleo}
                  onChange={(e) => setFormData({...formData, litros_oleo: e.target.value})}
                />
              </div>
              <div className="space-y-2">
                <Label className="flex items-center gap-1">
                  <TrendingDown size={14} className="text-gray-600" />
                  Graxa (L)
                </Label>
                <Input
                  type="number"
                  step="0.1"
                  min="0"
                  placeholder="0"
                  value={formData.litros_graxa}
                  onChange={(e) => setFormData({...formData, litros_graxa: e.target.value})}
                />
              </div>
            </div>

            {/* Operador */}
            <div className="space-y-2">
              <Label>Operador</Label>
              <Select 
                value={formData.operador_id} 
                onValueChange={(value) => setFormData({...formData, operador_id: value})}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Selecione o operador..." />
                </SelectTrigger>
                <SelectContent>
                  {operadores.map(op => (
                    <SelectItem key={op.id} value={op.id}>
                      <div className="flex items-center gap-2">
                        <User size={14} />
                        {op.nome}
                        <span className={`text-xs px-1 rounded ${
                          op.tipo === "rh" ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700'
                        }`}>
                          {op.tipo === "rh" ? "RH" : "Cadastro"}
                        </span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Observações */}
            <div className="space-y-2">
              <Label>Observações</Label>
              <Textarea
                value={formData.observacoes}
                onChange={(e) => setFormData({...formData, observacoes: e.target.value})}
                placeholder="Observações adicionais..."
                rows={2}
              />
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setIsModalOpen(false)}>
                Cancelar
              </Button>
              <Button type="submit" className="bg-[#E31A1A] hover:bg-red-700">
                Salvar Registro
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Modal de Cadastro de Veículo Abastecedor */}
      <Dialog open={isAbastecedorModalOpen} onOpenChange={setIsAbastecedorModalOpen}>
        <DialogContent className="sm:max-w-[700px] max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Truck className="text-green-500" />
              {editingAbastecedorId ? "Editar Veículo Tanque" : "Cadastrar Veículo Tanque"}
            </DialogTitle>
          </DialogHeader>
          
          <form onSubmit={handleAbastecedorSubmit} className="space-y-4">
            {/* Máquina */}
            <div className="space-y-2">
              <Label>Selecione a Máquina *</Label>
              {!editingAbastecedorId && machinesDisponiveis.length === 0 ? (
                <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                  <p className="text-sm text-yellow-700">
                    Todas as máquinas já estão cadastradas como veículos tanque.
                    Cadastre uma nova máquina primeiro ou remova um veículo tanque existente.
                  </p>
                </div>
              ) : (
                <Select 
                  value={abastecedorForm.machine_id} 
                  onValueChange={(value) => setAbastecedorForm({...abastecedorForm, machine_id: value})}
                  disabled={!!editingAbastecedorId}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Selecione a máquina..." />
                  </SelectTrigger>
                  <SelectContent>
                    {(editingAbastecedorId ? machines : machinesDisponiveis).map(m => (
                      <SelectItem key={m.id} value={m.id}>
                        <div className="flex items-center gap-2">
                          <Truck size={14} />
                          {m.name}
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            </div>

            {/* Combustível Principal (Diesel) */}
            <div className="grid grid-cols-2 gap-4 p-4 bg-yellow-50 rounded-lg border border-yellow-200">
              <div className="col-span-2">
                <Label className="text-sm font-medium text-yellow-800 flex items-center gap-2">
                  <Droplet size={16} className="text-yellow-600" />
                  Compartimento de Diesel
                </Label>
              </div>
              <div className="space-y-2">
                <Label className="text-xs">Capacidade (L)</Label>
                <Input
                  type="number"
                  step="1"
                  min="0"
                  placeholder="Ex: 5000"
                  value={abastecedorForm.capacidade_diesel}
                  onChange={(e) => setAbastecedorForm({...abastecedorForm, capacidade_diesel: e.target.value})}
                />
              </div>
              <div className="space-y-2">
                <Label className="text-xs">Quantidade Atual (L)</Label>
                <Input
                  type="number"
                  step="0.1"
                  min="0"
                  placeholder="Litros atuais"
                  value={abastecedorForm.litros_diesel}
                  onChange={(e) => setAbastecedorForm({...abastecedorForm, litros_diesel: e.target.value})}
                />
              </div>
            </div>

            {/* Compartimentos de Óleo Dinâmicos */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Label className="text-sm font-medium flex items-center gap-2">
                  <CircleDot size={16} className="text-blue-600" />
                  Compartimentos de Óleo
                </Label>
                <Button 
                  type="button" 
                  variant="outline" 
                  size="sm"
                  onClick={addCompartimentoOleo}
                  className="text-blue-600 border-blue-300 hover:bg-blue-50"
                >
                  <Plus size={14} className="mr-1" />
                  Adicionar Óleo
                </Button>
              </div>
              
              {abastecedorForm.compartimentos_oleo.length === 0 ? (
                <div className="p-4 border-2 border-dashed border-gray-200 rounded-lg text-center text-gray-500">
                  <Package size={24} className="mx-auto mb-2 opacity-50" />
                  <p className="text-sm">Nenhum compartimento de óleo adicionado</p>
                  <p className="text-xs">Clique em "Adicionar Óleo" para criar compartimentos</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {abastecedorForm.compartimentos_oleo.map((comp, index) => (
                    <div key={comp.id || index} className="p-3 bg-blue-50 rounded-lg border border-blue-200">
                      <div className="flex items-center justify-between mb-3">
                        <span className="text-sm font-medium text-blue-800">Compartimento {index + 1}</span>
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={() => removeCompartimentoOleo(index)}
                          className="text-red-600 hover:bg-red-50 h-6 w-6 p-0"
                        >
                          <X size={14} />
                        </Button>
                      </div>
                      <div className="grid grid-cols-4 gap-3">
                        <div className="col-span-2 space-y-1">
                          <Label className="text-xs">Tipo de Óleo (Estoque) *</Label>
                          <Select 
                            value={comp.item_estoque_id}
                            onValueChange={(value) => updateCompartimentoOleo(index, "item_estoque_id", value)}
                          >
                            <SelectTrigger className="h-9">
                              <SelectValue placeholder="Selecione..." />
                            </SelectTrigger>
                            <SelectContent>
                              {stockItems.length === 0 ? (
                                <div className="p-2 text-sm text-gray-500">
                                  Nenhum item no estoque
                                </div>
                              ) : (
                                stockItems.map(item => (
                                  <SelectItem key={item.id} value={item.id}>
                                    {item.name}
                                    {item.category_name && (
                                      <span className="text-xs text-gray-400 ml-1">({item.category_name})</span>
                                    )}
                                  </SelectItem>
                                ))
                              )}
                            </SelectContent>
                          </Select>
                        </div>
                        <div className="space-y-1">
                          <Label className="text-xs">Unidade</Label>
                          <Select 
                            value={comp.unidade_medida}
                            onValueChange={(value) => updateCompartimentoOleo(index, "unidade_medida", value)}
                          >
                            <SelectTrigger className="h-9">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              {UNIDADES_MEDIDA.map(u => (
                                <SelectItem key={u.value} value={u.value}>{u.label}</SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>
                        <div className="space-y-1">
                          <Label className="text-xs">Capacidade</Label>
                          <Input
                            type="number"
                            step="0.1"
                            min="0"
                            placeholder="0"
                            className="h-9"
                            value={comp.capacidade}
                            onChange={(e) => updateCompartimentoOleo(index, "capacidade", e.target.value)}
                          />
                        </div>
                        <div className="col-span-4">
                          <Label className="text-xs">Quantidade Atual ({comp.unidade_medida})</Label>
                          <Input
                            type="number"
                            step="0.1"
                            min="0"
                            placeholder="Quantidade atual no compartimento"
                            className="h-9 mt-1"
                            value={comp.quantidade_atual}
                            onChange={(e) => updateCompartimentoOleo(index, "quantidade_atual", e.target.value)}
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Graxa */}
            <div className="grid grid-cols-2 gap-4 p-4 bg-gray-50 rounded-lg border border-gray-200">
              <div className="col-span-2">
                <Label className="text-sm font-medium text-gray-700 flex items-center gap-2">
                  <TrendingDown size={16} className="text-gray-600" />
                  Compartimento de Graxa
                </Label>
              </div>
              <div className="space-y-2">
                <Label className="text-xs">Capacidade (L)</Label>
                <Input
                  type="number"
                  step="1"
                  min="0"
                  placeholder="Ex: 200"
                  value={abastecedorForm.capacidade_graxa}
                  onChange={(e) => setAbastecedorForm({...abastecedorForm, capacidade_graxa: e.target.value})}
                />
              </div>
              <div className="space-y-2">
                <Label className="text-xs">Quantidade Atual (L)</Label>
                <Input
                  type="number"
                  step="0.1"
                  min="0"
                  placeholder="Litros atuais"
                  value={abastecedorForm.litros_graxa}
                  onChange={(e) => setAbastecedorForm({...abastecedorForm, litros_graxa: e.target.value})}
                />
              </div>
            </div>

            {/* Operador */}
            <div className="space-y-2">
              <Label>Operador Responsável</Label>
              <Select 
                value={abastecedorForm.operador_id} 
                onValueChange={(value) => setAbastecedorForm({...abastecedorForm, operador_id: value})}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Selecione o operador..." />
                </SelectTrigger>
                <SelectContent>
                  {operadores.map(op => (
                    <SelectItem key={op.id} value={op.id}>
                      <div className="flex items-center gap-2">
                        <User size={14} />
                        {op.nome}
                        <span className={`text-xs px-1 rounded ${
                          op.tipo === "rh" ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700'
                        }`}>
                          {op.tipo === "rh" ? "RH" : "Cadastro"}
                        </span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setIsAbastecedorModalOpen(false)}>
                Cancelar
              </Button>
              <Button type="submit" className="bg-green-600 hover:bg-green-700">
                {editingAbastecedorId ? "Salvar Alterações" : "Cadastrar Veículo"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
