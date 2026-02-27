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
  Calendar,
  Droplet,
  CircleDot,
  TrendingDown,
  User
} from "lucide-react";

export default function CombustivelPage() {
  const [loading, setLoading] = useState(true);
  const [registros, setRegistros] = useState([]);
  const [abastecedores, setAbastecedores] = useState([]);
  const [machines, setMachines] = useState([]);
  const [operadores, setOperadores] = useState([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [activeTab, setActiveTab] = useState("registros");
  
  // Modal states
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isAbastecedorModalOpen, setIsAbastecedorModalOpen] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [editingAbastecedorId, setEditingAbastecedorId] = useState(null);
  
  // Form states
  const [tipoRegistro, setTipoRegistro] = useState(null); // null, "abastecedor", "abastecido"
  const [formData, setFormData] = useState({
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
    operador_id: "",
    observacoes: ""
  });
  
  const [abastecedorForm, setAbastecedorForm] = useState({
    machine_id: "",
    capacidade_diesel: "",
    capacidade_oleo: "",
    capacidade_graxa: "",
    litros_diesel: "",
    litros_oleo: "",
    litros_graxa: "",
    operador_id: ""
  });
  
  const token = localStorage.getItem("token");

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [registrosRes, abastecedoresRes, machinesRes, operadoresRes] = await Promise.all([
        axios.get(`${API}/combustivel`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API}/combustivel/abastecedores`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API}/machines`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API}/operadores`, { headers: { Authorization: `Bearer ${token}` } })
      ]);
      
      setRegistros(registrosRes.data);
      setAbastecedores(abastecedoresRes.data);
      setMachines(machinesRes.data);
      setOperadores(operadoresRes.data);
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

      await axios.post(`${API}/combustivel`, payload, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      toast.success("Registro criado com sucesso!");
      setIsModalOpen(false);
      resetForm();
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao salvar registro");
    }
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
    setTipoRegistro(null);
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
        ...abastecedorForm,
        capacidade_diesel: parseFloat(abastecedorForm.capacidade_diesel) || 0,
        capacidade_oleo: parseFloat(abastecedorForm.capacidade_oleo) || 0,
        capacidade_graxa: parseFloat(abastecedorForm.capacidade_graxa) || 0,
        litros_diesel: parseFloat(abastecedorForm.litros_diesel) || 0,
        litros_oleo: parseFloat(abastecedorForm.litros_oleo) || 0,
        litros_graxa: parseFloat(abastecedorForm.litros_graxa) || 0
      };

      if (editingAbastecedorId) {
        await axios.put(`${API}/combustivel/abastecedores/${editingAbastecedorId}`, payload, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success("Veículo abastecedor atualizado!");
      } else {
        await axios.post(`${API}/combustivel/abastecedores`, payload, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success("Veículo abastecedor cadastrado!");
      }
      
      setIsAbastecedorModalOpen(false);
      resetAbastecedorForm();
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao salvar veículo abastecedor");
    }
  };

  const handleEditAbastecedor = (abast) => {
    setEditingAbastecedorId(abast.id);
    setAbastecedorForm({
      machine_id: abast.machine_id,
      capacidade_diesel: abast.capacidade_diesel?.toString() || "",
      capacidade_oleo: abast.capacidade_oleo?.toString() || "",
      capacidade_graxa: abast.capacidade_graxa?.toString() || "",
      litros_diesel: abast.litros_diesel?.toString() || "",
      litros_oleo: abast.litros_oleo?.toString() || "",
      litros_graxa: abast.litros_graxa?.toString() || "",
      operador_id: abast.operador_id || ""
    });
    setIsAbastecedorModalOpen(true);
  };

  const handleDeleteAbastecedor = async (id) => {
    if (!confirm("Tem certeza que deseja remover este veículo abastecedor?")) return;
    
    try {
      await axios.delete(`${API}/combustivel/abastecedores/${id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success("Veículo abastecedor removido!");
      fetchData();
    } catch (error) {
      toast.error("Erro ao remover veículo abastecedor");
    }
  };

  const resetAbastecedorForm = () => {
    setEditingAbastecedorId(null);
    setAbastecedorForm({
      machine_id: "",
      capacidade_diesel: "",
      capacidade_oleo: "",
      capacidade_graxa: "",
      litros_diesel: "",
      litros_oleo: "",
      litros_graxa: "",
      operador_id: ""
    });
  };

  const openNewModal = (tipo) => {
    resetForm();
    setTipoRegistro(tipo);
    setFormData(prev => ({ ...prev, tipo_registro: tipo }));
    setIsModalOpen(true);
  };

  // Helpers
  const getMachineName = (id) => machines.find(m => m.id === id)?.name || "Máquina não encontrada";
  const getOperadorName = (id) => operadores.find(o => o.id === id)?.nome || "-";
  
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
            <div className="flex gap-2">
              <Button 
                onClick={() => openNewModal("abastecedor")} 
                className="bg-green-600 hover:bg-green-700"
              >
                <Plus size={18} className="mr-2" />
                Registro Abastecedor
              </Button>
              <Button 
                onClick={() => openNewModal("abastecido")} 
                className="bg-[#E31A1A] hover:bg-red-700"
              >
                <Plus size={18} className="mr-2" />
                Registro Abastecido
              </Button>
            </div>
          </div>

          {/* Lista de Registros */}
          <Card>
            <CardContent className="p-0">
              {filteredRegistros.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12 text-gray-500">
                  <Fuel size={48} className="mb-4 text-gray-300" />
                  <p>Nenhum registro encontrado</p>
                  <p className="text-sm">Clique em um dos botões acima para criar um registro</p>
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
                      <TableRow key={registro.id}>
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
                                : 'text-gray-500'
                            }`}>
                              {registro.fonte_abastecimento === "interno" 
                                ? registro.veiculo_abastecedor_nome || "Interno"
                                : "Externo"}
                            </span>
                          ) : "-"}
                        </TableCell>
                        <TableCell className="text-sm">{registro.operador_nome || "-"}</TableCell>
                        <TableCell className="text-right">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDelete(registro.id)}
                            className="text-red-600 hover:text-red-700 hover:bg-red-50"
                          >
                            <Trash2 size={16} />
                          </Button>
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
            >
              <Plus size={18} className="mr-2" />
              Cadastrar Veículo Tanque
            </Button>
          </div>

          {/* Cards dos Abastecedores - 3 colunas horizontal */}
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
                const oleoPercent = calcPercentage(abast.litros_oleo, abast.capacidade_oleo);
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
                      
                      {/* Óleo */}
                      <div>
                        <div className="flex justify-between text-sm mb-1">
                          <span className="flex items-center gap-1 font-medium">
                            <CircleDot size={14} className="text-blue-600" /> Óleo
                          </span>
                          <span className="text-gray-600">
                            {abast.litros_oleo?.toFixed(0) || 0}L / {abast.capacidade_oleo?.toFixed(0) || 0}L
                          </span>
                        </div>
                        <Progress value={oleoPercent} className="h-3" />
                        <p className="text-xs text-right text-gray-500 mt-0.5">{oleoPercent}%</p>
                      </div>
                      
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

      {/* Modal de Registro de Combustível */}
      <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
        <DialogContent className="sm:max-w-[600px]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Fuel className={tipoRegistro === "abastecedor" ? "text-green-500" : "text-blue-500"} />
              {tipoRegistro === "abastecedor" 
                ? "Registro de Entrada (Abastecedor)" 
                : "Registro de Abastecimento"}
            </DialogTitle>
          </DialogHeader>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Info do tipo */}
            <div className={`p-3 rounded-lg ${
              tipoRegistro === "abastecedor" ? 'bg-green-50 border border-green-200' : 'bg-blue-50 border border-blue-200'
            }`}>
              <p className={`text-sm ${tipoRegistro === "abastecedor" ? 'text-green-700' : 'text-blue-700'}`}>
                {tipoRegistro === "abastecedor" 
                  ? "Registre a entrada de combustível no veículo tanque"
                  : "Registre o abastecimento de uma máquina"}
              </p>
            </div>

            {/* Máquina */}
            <div className="space-y-2">
              <Label>
                {tipoRegistro === "abastecedor" ? "Veículo Tanque *" : "Máquina a Abastecer *"}
              </Label>
              <Select 
                value={formData.machine_id} 
                onValueChange={(value) => setFormData({...formData, machine_id: value})}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Selecione..." />
                </SelectTrigger>
                <SelectContent>
                  {tipoRegistro === "abastecedor" 
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

            {/* Se for abastecido, mostrar fonte */}
            {tipoRegistro === "abastecido" && (
              <div className="space-y-2">
                <Label>Fonte do Abastecimento *</Label>
                <RadioGroup 
                  value={formData.fonte_abastecimento} 
                  onValueChange={(value) => setFormData({...formData, fonte_abastecimento: value, veiculo_abastecedor_id: ""})}
                  className="flex gap-4"
                >
                  <div className="flex items-center space-x-2">
                    <RadioGroupItem value="interno" id="fonte_interno" />
                    <Label htmlFor="fonte_interno" className="cursor-pointer font-normal">
                      Veículo Abastecedor (Interno)
                    </Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <RadioGroupItem value="externo" id="fonte_externo" />
                    <Label htmlFor="fonte_externo" className="cursor-pointer font-normal">
                      Abastecimento Externo
                    </Label>
                  </div>
                </RadioGroup>
              </div>
            )}

            {/* Seleção do veículo abastecedor se fonte for interna */}
            {tipoRegistro === "abastecido" && formData.fonte_abastecimento === "interno" && (
              <div className="space-y-2">
                <Label>Veículo Abastecedor *</Label>
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
              <Button type="submit" className={tipoRegistro === "abastecedor" ? "bg-green-600 hover:bg-green-700" : "bg-[#E31A1A] hover:bg-red-700"}>
                Salvar Registro
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Modal de Cadastro de Veículo Abastecedor */}
      <Dialog open={isAbastecedorModalOpen} onOpenChange={setIsAbastecedorModalOpen}>
        <DialogContent className="sm:max-w-[600px]">
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
            </div>

            {/* Capacidades - 3 campos horizontais */}
            <div>
              <Label className="text-sm font-medium text-gray-700 mb-2 block">Capacidades Máximas</Label>
              <div className="grid grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label className="text-xs flex items-center gap-1">
                    <Droplet size={12} className="text-yellow-600" />
                    Diesel (L)
                  </Label>
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
                  <Label className="text-xs flex items-center gap-1">
                    <CircleDot size={12} className="text-blue-600" />
                    Óleo (L)
                  </Label>
                  <Input
                    type="number"
                    step="1"
                    min="0"
                    placeholder="Ex: 500"
                    value={abastecedorForm.capacidade_oleo}
                    onChange={(e) => setAbastecedorForm({...abastecedorForm, capacidade_oleo: e.target.value})}
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-xs flex items-center gap-1">
                    <TrendingDown size={12} className="text-gray-600" />
                    Graxa (L)
                  </Label>
                  <Input
                    type="number"
                    step="1"
                    min="0"
                    placeholder="Ex: 200"
                    value={abastecedorForm.capacidade_graxa}
                    onChange={(e) => setAbastecedorForm({...abastecedorForm, capacidade_graxa: e.target.value})}
                  />
                </div>
              </div>
            </div>

            {/* Níveis Atuais - 3 campos horizontais */}
            <div>
              <Label className="text-sm font-medium text-gray-700 mb-2 block">Níveis Atuais no Reservatório</Label>
              <div className="grid grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label className="text-xs flex items-center gap-1">
                    <Droplet size={12} className="text-yellow-600" />
                    Diesel (L)
                  </Label>
                  <Input
                    type="number"
                    step="0.1"
                    min="0"
                    placeholder="Litros atuais"
                    value={abastecedorForm.litros_diesel}
                    onChange={(e) => setAbastecedorForm({...abastecedorForm, litros_diesel: e.target.value})}
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-xs flex items-center gap-1">
                    <CircleDot size={12} className="text-blue-600" />
                    Óleo (L)
                  </Label>
                  <Input
                    type="number"
                    step="0.1"
                    min="0"
                    placeholder="Litros atuais"
                    value={abastecedorForm.litros_oleo}
                    onChange={(e) => setAbastecedorForm({...abastecedorForm, litros_oleo: e.target.value})}
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-xs flex items-center gap-1">
                    <TrendingDown size={12} className="text-gray-600" />
                    Graxa (L)
                  </Label>
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
