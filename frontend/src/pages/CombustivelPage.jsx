import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "@/App";
import { useAuth } from "@/App";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
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
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { 
  Fuel, 
  Plus, 
  Search, 
  Trash2, 
  Edit2, 
  Truck,
  Calendar,
  Droplets,
  TrendingUp,
  Filter,
  Gauge
} from "lucide-react";

export default function CombustivelPage() {
  const { token } = useAuth();
  const [registros, setRegistros] = useState([]);
  const [machines, setMachines] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterMachine, setFilterMachine] = useState("all");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [formData, setFormData] = useState({
    machine_id: "",
    data: new Date().toISOString().split("T")[0],
    tipo_medicao: "litros_hora",  // litros_hora ou litros_km
    hora_km_inicial: "",
    litros_inicial: "",
    litros_final: "",
    operador: "",
    observacoes: ""
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [registrosRes, machinesRes] = await Promise.all([
        axios.get(`${API}/combustivel`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get(`${API}/machines`, {
          headers: { Authorization: `Bearer ${token}` }
        })
      ]);
      setRegistros(registrosRes.data);
      setMachines(machinesRes.data);
    } catch (error) {
      toast.error("Erro ao carregar dados");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.machine_id) {
      toast.error("Selecione uma máquina");
      return;
    }
    if (!formData.litros_inicial || !formData.litros_final) {
      toast.error("Preencha os litros inicial e final");
      return;
    }
    
    const litrosInicial = parseFloat(formData.litros_inicial);
    const litrosFinal = parseFloat(formData.litros_final);
    const horaKmInicial = parseFloat(formData.hora_km_inicial) || 0;
    
    if (litrosFinal < litrosInicial) {
      toast.error("Litros final deve ser maior que litros inicial");
      return;
    }

    try {
      const payload = {
        ...formData,
        hora_km_inicial: horaKmInicial,
        litros_inicial: litrosInicial,
        litros_final: litrosFinal,
        litros_consumidos: litrosFinal - litrosInicial
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

  const handleEdit = (registro) => {
    setEditingId(registro.id);
    setFormData({
      machine_id: registro.machine_id,
      data: registro.data,
      tipo_medicao: registro.tipo_medicao || "litros_hora",
      hora_km_inicial: registro.hora_km_inicial?.toString() || "",
      litros_inicial: registro.litros_inicial.toString(),
      litros_final: registro.litros_final.toString(),
      operador: registro.operador || "",
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
      tipo_medicao: "litros_hora",
      hora_km_inicial: "",
      litros_inicial: "",
      litros_final: "",
      operador: "",
      observacoes: ""
    });
  };

  const openNewModal = () => {
    resetForm();
    setIsModalOpen(true);
  };

  const getMachineName = (machineId) => {
    const machine = machines.find(m => m.id === machineId);
    return machine ? machine.name : "Máquina não encontrada";
  };

  const formatDate = (dateString) => {
    if (!dateString) return "-";
    return new Date(dateString + "T00:00:00").toLocaleDateString("pt-BR");
  };

  const getTipoLabel = (tipo) => {
    return tipo === "litros_hora" ? "L/hora" : "L/km";
  };

  // Filtros
  const filteredRegistros = registros.filter(registro => {
    const matchesSearch = 
      getMachineName(registro.machine_id).toLowerCase().includes(searchTerm.toLowerCase()) ||
      (registro.operador || "").toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesMachine = filterMachine === "all" || registro.machine_id === filterMachine;
    
    return matchesSearch && matchesMachine;
  });

  // Estatísticas
  const totalLitros = registros.reduce((sum, r) => sum + (r.litros_consumidos || 0), 0);
  const registrosHoje = registros.filter(r => r.data === new Date().toISOString().split("T")[0]).length;
  const mediaLitros = registros.length > 0 ? (totalLitros / registros.length).toFixed(1) : 0;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="combustivel-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Fuel className="text-green-500" />
            Combustível
          </h1>
          <p className="text-gray-500 text-sm mt-1">
            Registre e acompanhe o consumo de combustível das máquinas
          </p>
        </div>
        <Button 
          onClick={openNewModal}
          className="bg-green-500 hover:bg-green-600 text-white"
          data-testid="new-combustivel-btn"
        >
          <Plus size={18} className="mr-2" />
          Novo Registro
        </Button>
      </div>

      {/* Estatísticas */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="bg-gradient-to-br from-green-50 to-green-100 border-green-200">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-500 rounded-lg">
                <Droplets className="text-white" size={20} />
              </div>
              <div>
                <p className="text-sm text-green-700">Total Consumido</p>
                <p className="text-2xl font-bold text-green-900">{totalLitros.toFixed(1)}L</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-500 rounded-lg">
                <Calendar className="text-white" size={20} />
              </div>
              <div>
                <p className="text-sm text-blue-700">Registros Hoje</p>
                <p className="text-2xl font-bold text-blue-900">{registrosHoje}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-orange-50 to-orange-100 border-orange-200">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-orange-500 rounded-lg">
                <TrendingUp className="text-white" size={20} />
              </div>
              <div>
                <p className="text-sm text-orange-700">Média por Registro</p>
                <p className="text-2xl font-bold text-orange-900">{mediaLitros}L</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-purple-50 to-purple-100 border-purple-200">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-500 rounded-lg">
                <Truck className="text-white" size={20} />
              </div>
              <div>
                <p className="text-sm text-purple-700">Total de Registros</p>
                <p className="text-2xl font-bold text-purple-900">{registros.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filtros */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={18} />
              <Input
                placeholder="Buscar por máquina ou operador..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            <div className="w-full sm:w-64">
              <Select value={filterMachine} onValueChange={setFilterMachine}>
                <SelectTrigger>
                  <Filter size={16} className="mr-2" />
                  <SelectValue placeholder="Filtrar por máquina" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todas as máquinas</SelectItem>
                  {machines.map(machine => (
                    <SelectItem key={machine.id} value={machine.id}>
                      {machine.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Tabela de Registros */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Registros de Combustível</CardTitle>
        </CardHeader>
        <CardContent>
          {filteredRegistros.length === 0 ? (
            <div className="text-center py-12">
              <Fuel className="mx-auto text-gray-300 mb-4" size={48} />
              <p className="text-gray-500">Nenhum registro encontrado</p>
              <Button 
                onClick={openNewModal} 
                variant="outline" 
                className="mt-4"
              >
                <Plus size={16} className="mr-2" />
                Criar primeiro registro
              </Button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Máquina</TableHead>
                    <TableHead>Data</TableHead>
                    <TableHead>Tipo</TableHead>
                    <TableHead className="text-right">Hora/Km Inicial</TableHead>
                    <TableHead className="text-right">Litros Consumidos</TableHead>
                    <TableHead>Operador</TableHead>
                    <TableHead className="text-right">Ações</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredRegistros.map((registro) => (
                    <TableRow key={registro.id} data-testid={`combustivel-row-${registro.id}`}>
                      <TableCell className="font-medium">
                        <div className="flex items-center gap-2">
                          <Truck size={16} className="text-green-500" />
                          {getMachineName(registro.machine_id)}
                        </div>
                      </TableCell>
                      <TableCell>{formatDate(registro.data)}</TableCell>
                      <TableCell>
                        <span className="bg-blue-100 text-blue-800 px-2 py-0.5 rounded text-xs font-medium">
                          {getTipoLabel(registro.tipo_medicao)}
                        </span>
                      </TableCell>
                      <TableCell className="text-right font-mono">
                        {registro.hora_km_inicial || "-"}
                      </TableCell>
                      <TableCell className="text-right">
                        <span className="bg-green-100 text-green-800 px-2 py-1 rounded-full text-sm font-medium">
                          {registro.litros_consumidos?.toFixed(1)}L
                        </span>
                      </TableCell>
                      <TableCell>{registro.operador || "-"}</TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleEdit(registro)}
                            className="text-blue-600 hover:text-blue-700 hover:bg-blue-50"
                          >
                            <Edit2 size={16} />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDelete(registro.id)}
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
            </div>
          )}
        </CardContent>
      </Card>

      {/* Modal de Criação/Edição */}
      <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Fuel className="text-green-500" />
              {editingId ? "Editar Registro" : "Novo Registro de Combustível"}
            </DialogTitle>
          </DialogHeader>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Seleção de Máquina */}
            <div className="space-y-2">
              <Label htmlFor="machine">Máquina *</Label>
              <Select 
                value={formData.machine_id} 
                onValueChange={(value) => setFormData({...formData, machine_id: value})}
              >
                <SelectTrigger data-testid="combustivel-machine-select">
                  <SelectValue placeholder="Selecione a máquina" />
                </SelectTrigger>
                <SelectContent>
                  {machines.map(machine => (
                    <SelectItem key={machine.id} value={machine.id}>
                      <div className="flex items-center gap-2">
                        <Truck size={14} />
                        {machine.name} {machine.model && `- ${machine.model}`}
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Tipo de Medição */}
            <div className="space-y-2">
              <Label htmlFor="tipo_medicao">Tipo de Medição *</Label>
              <Select 
                value={formData.tipo_medicao} 
                onValueChange={(value) => setFormData({...formData, tipo_medicao: value})}
              >
                <SelectTrigger data-testid="combustivel-tipo-select">
                  <SelectValue placeholder="Selecione o tipo" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="litros_hora">
                    <div className="flex items-center gap-2">
                      <Gauge size={14} />
                      Litros por Hora
                    </div>
                  </SelectItem>
                  <SelectItem value="litros_km">
                    <div className="flex items-center gap-2">
                      <Gauge size={14} />
                      Litros por Km
                    </div>
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Data */}
            <div className="space-y-2">
              <Label htmlFor="data">Data *</Label>
              <Input
                id="data"
                type="date"
                value={formData.data}
                onChange={(e) => setFormData({...formData, data: e.target.value})}
                required
              />
            </div>

            {/* Hora/Km Inicial */}
            <div className="space-y-2">
              <Label htmlFor="hora_km_inicial">
                {formData.tipo_medicao === "litros_hora" ? "Horímetro Inicial" : "Km Inicial"}
              </Label>
              <Input
                id="hora_km_inicial"
                type="number"
                step="0.1"
                min="0"
                placeholder={formData.tipo_medicao === "litros_hora" ? "Ex: 1250.5" : "Ex: 50000"}
                value={formData.hora_km_inicial}
                onChange={(e) => setFormData({...formData, hora_km_inicial: e.target.value})}
              />
            </div>

            {/* Litros */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="litros_inicial">Litros Inicial *</Label>
                <Input
                  id="litros_inicial"
                  type="number"
                  step="0.1"
                  min="0"
                  placeholder="Ex: 0"
                  value={formData.litros_inicial}
                  onChange={(e) => setFormData({...formData, litros_inicial: e.target.value})}
                  required
                />
                <p className="text-xs text-gray-500">Nível do tanque antes</p>
              </div>
              <div className="space-y-2">
                <Label htmlFor="litros_final">Litros Final *</Label>
                <Input
                  id="litros_final"
                  type="number"
                  step="0.1"
                  min="0"
                  placeholder="Ex: 150"
                  value={formData.litros_final}
                  onChange={(e) => setFormData({...formData, litros_final: e.target.value})}
                  required
                />
                <p className="text-xs text-gray-500">Litros abastecidos</p>
              </div>
            </div>

            {/* Preview de litros consumidos */}
            {formData.litros_inicial && formData.litros_final && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                <p className="text-sm text-green-700">
                  <strong>Litros abastecidos:</strong>{" "}
                  {(parseFloat(formData.litros_final) - parseFloat(formData.litros_inicial)).toFixed(1)}L
                </p>
              </div>
            )}

            {/* Operador */}
            <div className="space-y-2">
              <Label htmlFor="operador">Operador</Label>
              <Input
                id="operador"
                placeholder="Nome do operador"
                value={formData.operador}
                onChange={(e) => setFormData({...formData, operador: e.target.value})}
              />
            </div>

            {/* Observações */}
            <div className="space-y-2">
              <Label htmlFor="observacoes">Observações</Label>
              <Textarea
                id="observacoes"
                placeholder="Observações adicionais..."
                value={formData.observacoes}
                onChange={(e) => setFormData({...formData, observacoes: e.target.value})}
                rows={3}
              />
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setIsModalOpen(false)}>
                Cancelar
              </Button>
              <Button type="submit" className="bg-green-500 hover:bg-green-600 text-white">
                {editingId ? "Atualizar" : "Salvar"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
