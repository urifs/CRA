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
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
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
  Clock, 
  Plus, 
  Search, 
  Trash2, 
  Edit2, 
  Truck,
  Calendar,
  Timer,
  TrendingUp,
  Filter,
  Gauge
} from "lucide-react";

export default function HorimetroPage() {
  const { token } = useAuth();
  const [registros, setRegistros] = useState([]);
  const [machines, setMachines] = useState([]);
  const [operadores, setOperadores] = useState([]); // Lista unificada de operadores
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterMachine, setFilterMachine] = useState("all");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [formData, setFormData] = useState({
    machine_id: "",
    data: new Date().toISOString().split("T")[0],
    hora_inicial: "",
    hora_final: "",
    operador: "",
    observacoes: "",
    tipo_medicao: "hora" // "hora" ou "km"
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [registrosRes, machinesRes, cadastrosRes, funcionariosRes] = await Promise.all([
        axios.get(`${API}/horimetro`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get(`${API}/machines`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get(`${API}/admin/cadastros`, {
          headers: { Authorization: `Bearer ${token}` }
        }).catch(() => ({ data: [] })),
        axios.get(`${API}/rh/funcionarios`, {
          headers: { Authorization: `Bearer ${token}` }
        }).catch(() => ({ data: [] }))
      ]);
      
      setRegistros(registrosRes.data);
      setMachines(machinesRes.data);
      
      // Unificar cadastros e funcionários como operadores
      const cadastrosOperadores = (cadastrosRes.data || []).map(c => ({
        id: c.id,
        nome: c.nome || c.razao_social,
        tipo: 'Cadastro',
        documento: c.documento
      }));
      
      const funcionariosOperadores = (funcionariosRes.data || []).map(f => ({
        id: f.id,
        nome: f.nome,
        tipo: 'Funcionário',
        cargo: f.cargo
      }));
      
      // Combinar e ordenar por nome
      const todosOperadores = [...funcionariosOperadores, ...cadastrosOperadores]
        .sort((a, b) => a.nome?.localeCompare(b.nome || '') || 0);
      
      setOperadores(todosOperadores);
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
    if (!formData.hora_inicial || !formData.hora_final) {
      toast.error("Preencha as horas inicial e final");
      return;
    }
    
    const horaInicial = parseFloat(formData.hora_inicial);
    const horaFinal = parseFloat(formData.hora_final);
    
    if (horaFinal < horaInicial) {
      toast.error("Hora final deve ser maior que hora inicial");
      return;
    }

    try {
      const payload = {
        ...formData,
        hora_inicial: horaInicial,
        hora_final: horaFinal,
        horas_trabalhadas: horaFinal - horaInicial
      };

      if (editingId) {
        await axios.put(`${API}/horimetro/${editingId}`, payload, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success("Registro atualizado com sucesso!");
      } else {
        await axios.post(`${API}/horimetro`, payload, {
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
      hora_inicial: registro.hora_inicial.toString(),
      hora_final: registro.hora_final.toString(),
      operador: registro.operador || "",
      observacoes: registro.observacoes || "",
      tipo_medicao: registro.tipo_medicao || "hora"
    });
    setIsModalOpen(true);
  };

  const handleDelete = async (id) => {
    if (!confirm("Tem certeza que deseja excluir este registro?")) return;
    
    try {
      await axios.delete(`${API}/horimetro/${id}`, {
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
      hora_inicial: "",
      hora_final: "",
      operador: "",
      observacoes: "",
      tipo_medicao: "hora" // "hora" ou "km"
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

  // Filtros
  const filteredRegistros = registros.filter(registro => {
    const matchesSearch = 
      getMachineName(registro.machine_id).toLowerCase().includes(searchTerm.toLowerCase()) ||
      (registro.operador || "").toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesMachine = filterMachine === "all" || registro.machine_id === filterMachine;
    
    return matchesSearch && matchesMachine;
  });

  // Estatísticas
  const totalHoras = registros.reduce((sum, r) => sum + (r.horas_trabalhadas || 0), 0);
  const registrosHoje = registros.filter(r => r.data === new Date().toISOString().split("T")[0]).length;
  const mediaHorasDia = registros.length > 0 ? (totalHoras / registros.length).toFixed(1) : 0;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-yellow-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="horimetro-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Clock className="text-yellow-500" />
            Horímetro
          </h1>
          <p className="text-gray-500 text-sm mt-1">
            Registre e acompanhe as horas de utilização das máquinas
          </p>
        </div>
        <Button 
          onClick={openNewModal}
          className="bg-yellow-500 hover:bg-yellow-600 text-black"
          data-testid="new-horimetro-btn"
        >
          <Plus size={18} className="mr-2" />
          Novo Registro
        </Button>
      </div>

      {/* Estatísticas */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="bg-gradient-to-br from-yellow-50 to-yellow-100 border-yellow-200">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-yellow-500 rounded-lg">
                <Timer className="text-white" size={20} />
              </div>
              <div>
                <p className="text-sm text-yellow-700">Total de Horas</p>
                <p className="text-2xl font-bold text-yellow-900">{totalHoras.toFixed(1)}h</p>
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

        <Card className="bg-gradient-to-br from-green-50 to-green-100 border-green-200">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-500 rounded-lg">
                <TrendingUp className="text-white" size={20} />
              </div>
              <div>
                <p className="text-sm text-green-700">Média por Registro</p>
                <p className="text-2xl font-bold text-green-900">{mediaHorasDia}h</p>
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
          <CardTitle className="text-lg">Registros de Horímetro</CardTitle>
        </CardHeader>
        <CardContent>
          {filteredRegistros.length === 0 ? (
            <div className="text-center py-12">
              <Clock className="mx-auto text-gray-300 mb-4" size={48} />
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
                    <TableHead className="text-right">Inicial</TableHead>
                    <TableHead className="text-right">Final</TableHead>
                    <TableHead className="text-right">Trabalhado</TableHead>
                    <TableHead>Operador</TableHead>
                    <TableHead className="text-right">Ações</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredRegistros.map((registro) => {
                    const isKm = registro.tipo_medicao === "km";
                    const unit = isKm ? "km" : "h";
                    return (
                    <TableRow key={registro.id} data-testid={`horimetro-row-${registro.id}`}>
                      <TableCell className="font-medium">
                        <div className="flex items-center gap-2">
                          <Truck size={16} className="text-yellow-500" />
                          {getMachineName(registro.machine_id)}
                        </div>
                      </TableCell>
                      <TableCell>{formatDate(registro.data)}</TableCell>
                      <TableCell>
                        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                          isKm ? 'bg-blue-100 text-blue-700' : 'bg-yellow-100 text-yellow-700'
                        }`}>
                          {isKm ? 'Km' : 'Hora'}
                        </span>
                      </TableCell>
                      <TableCell className="text-right font-mono">{registro.hora_inicial}{unit}</TableCell>
                      <TableCell className="text-right font-mono">{registro.hora_final}{unit}</TableCell>
                      <TableCell className="text-right">
                        <span className={`px-2 py-1 rounded-full text-sm font-medium ${
                          isKm ? 'bg-blue-100 text-blue-800' : 'bg-yellow-100 text-yellow-800'
                        }`}>
                          {registro.horas_trabalhadas?.toFixed(1)}{unit}
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
                    );
                  })}
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
              <Clock className="text-yellow-500" />
              {editingId ? "Editar Registro" : "Novo Registro de Horímetro"}
            </DialogTitle>
          </DialogHeader>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Tipo de Medição */}
            <div className="space-y-2">
              <Label className="flex items-center gap-2">
                <Gauge size={16} className="text-yellow-500" />
                Tipo de Medição *
              </Label>
              <RadioGroup 
                value={formData.tipo_medicao} 
                onValueChange={(value) => setFormData({...formData, tipo_medicao: value})}
                className="flex gap-4"
              >
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="hora" id="tipo_hora" />
                  <Label htmlFor="tipo_hora" className="cursor-pointer font-normal">
                    Horas (Horímetro)
                  </Label>
                </div>
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="km" id="tipo_km" />
                  <Label htmlFor="tipo_km" className="cursor-pointer font-normal">
                    Quilômetros (Odômetro)
                  </Label>
                </div>
              </RadioGroup>
            </div>

            {/* Seleção de Máquina */}
            <div className="space-y-2">
              <Label htmlFor="machine">Máquina *</Label>
              <Select 
                value={formData.machine_id} 
                onValueChange={(value) => setFormData({...formData, machine_id: value})}
              >
                <SelectTrigger data-testid="machine-select">
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

            {/* Horas/Km */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="hora_inicial">
                  {formData.tipo_medicao === "km" ? "Km Inicial" : "Hora Inicial"} *
                </Label>
                <Input
                  id="hora_inicial"
                  type="number"
                  step="0.1"
                  min="0"
                  placeholder={formData.tipo_medicao === "km" ? "Ex: 45000" : "Ex: 1250.5"}
                  value={formData.hora_inicial}
                  onChange={(e) => setFormData({...formData, hora_inicial: e.target.value})}
                  required
                />
                <p className="text-xs text-gray-500">
                  Leitura do {formData.tipo_medicao === "km" ? "odômetro" : "horímetro"}
                </p>
              </div>
              <div className="space-y-2">
                <Label htmlFor="hora_final">
                  {formData.tipo_medicao === "km" ? "Km Final" : "Hora Final"} *
                </Label>
                <Input
                  id="hora_final"
                  type="number"
                  step="0.1"
                  min="0"
                  placeholder={formData.tipo_medicao === "km" ? "Ex: 45150" : "Ex: 1258.0"}
                  value={formData.hora_final}
                  onChange={(e) => setFormData({...formData, hora_final: e.target.value})}
                  required
                />
                <p className="text-xs text-gray-500">
                  Leitura do {formData.tipo_medicao === "km" ? "odômetro" : "horímetro"}
                </p>
              </div>
            </div>

            {/* Preview de horas/km trabalhados */}
            {formData.hora_inicial && formData.hora_final && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                <p className="text-sm text-yellow-700">
                  <strong>{formData.tipo_medicao === "km" ? "Km percorridos:" : "Horas trabalhadas:"}</strong>{" "}
                  {(parseFloat(formData.hora_final) - parseFloat(formData.hora_inicial)).toFixed(1)}
                  {formData.tipo_medicao === "km" ? " km" : "h"}
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
              <Button type="submit" className="bg-yellow-500 hover:bg-yellow-600 text-black">
                {editingId ? "Atualizar" : "Salvar"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
