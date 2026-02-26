import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "@/App";
import { Card, CardContent } from "@/components/ui/card";
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
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { 
  Clock, Users, Play, Pause, Square, AlertTriangle, CheckCircle, 
  Calendar, Search, Filter, Plus, Edit, Trash2, Coffee
} from "lucide-react";
import { toast } from "sonner";

export default function PontoPage() {
  const [registros, setRegistros] = useState([]);
  const [funcionarios, setFuncionarios] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [selectedFuncionario, setSelectedFuncionario] = useState("");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingRegistro, setEditingRegistro] = useState(null);
  const [resumoDia, setResumoDia] = useState({ presentes: 0, ausentes: 0, atrasados: 0 });
  
  const [formData, setFormData] = useState({
    funcionario_id: "",
    data: new Date().toISOString().split('T')[0],
    entrada: "",
    saida_almoco: "",
    retorno_almoco: "",
    saida: "",
    observacoes: ""
  });

  // Jornada padrão
  const JORNADA = {
    seg_sex: { entrada: "08:00", saida_almoco: "11:30", retorno_almoco: "13:30", saida: "18:00" },
    sabado: { entrada: "08:00", saida: "12:00" }
  };

  useEffect(() => {
    fetchFuncionarios();
  }, []);

  useEffect(() => {
    fetchRegistros();
  }, [selectedDate, selectedFuncionario]);

  const fetchFuncionarios = async () => {
    try {
      const response = await axios.get(`${API}/rh/funcionarios?status=ativo`);
      setFuncionarios(response.data);
    } catch (error) {
      console.error("Erro ao carregar funcionários:", error);
    }
  };

  const fetchRegistros = async () => {
    setLoading(true);
    try {
      let url = `${API}/rh/ponto?data=${selectedDate}`;
      if (selectedFuncionario) url += `&funcionario_id=${selectedFuncionario}`;
      
      const response = await axios.get(url);
      setRegistros(response.data.registros || []);
      setResumoDia(response.data.resumo || { presentes: 0, ausentes: 0, atrasados: 0 });
    } catch (error) {
      toast.error("Erro ao carregar registros");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingRegistro) {
        await axios.put(`${API}/rh/ponto/${editingRegistro.id}`, formData);
        toast.success("Registro atualizado!");
      } else {
        await axios.post(`${API}/rh/ponto`, formData);
        toast.success("Ponto registrado!");
      }
      fetchRegistros();
      closeModal();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao salvar");
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Deseja excluir este registro de ponto?")) return;
    try {
      await axios.delete(`${API}/rh/ponto/${id}`);
      toast.success("Registro excluído!");
      fetchRegistros();
    } catch (error) {
      toast.error("Erro ao excluir");
    }
  };

  const openModal = (registro = null) => {
    if (registro) {
      setEditingRegistro(registro);
      setFormData({
        funcionario_id: registro.funcionario_id,
        data: registro.data,
        entrada: registro.entrada || "",
        saida_almoco: registro.saida_almoco || "",
        retorno_almoco: registro.retorno_almoco || "",
        saida: registro.saida || "",
        observacoes: registro.observacoes || ""
      });
    } else {
      setEditingRegistro(null);
      setFormData({
        funcionario_id: "",
        data: selectedDate,
        entrada: "",
        saida_almoco: "",
        retorno_almoco: "",
        saida: "",
        observacoes: ""
      });
    }
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setEditingRegistro(null);
  };

  const calcularHorasTrabalhadas = (registro) => {
    if (!registro.entrada || !registro.saida) return "-";
    
    const [hEntrada, mEntrada] = registro.entrada.split(':').map(Number);
    const [hSaida, mSaida] = registro.saida.split(':').map(Number);
    
    let minutosTotal = (hSaida * 60 + mSaida) - (hEntrada * 60 + mEntrada);
    
    // Desconta intervalo de almoço se houver
    if (registro.saida_almoco && registro.retorno_almoco) {
      const [hSaidaAlmoco, mSaidaAlmoco] = registro.saida_almoco.split(':').map(Number);
      const [hRetornoAlmoco, mRetornoAlmoco] = registro.retorno_almoco.split(':').map(Number);
      const intervalo = (hRetornoAlmoco * 60 + mRetornoAlmoco) - (hSaidaAlmoco * 60 + mSaidaAlmoco);
      minutosTotal -= intervalo;
    }
    
    const horas = Math.floor(minutosTotal / 60);
    const minutos = minutosTotal % 60;
    return `${horas}h ${minutos}min`;
  };

  const getStatusBadge = (registro) => {
    const diaSemana = new Date(registro.data + 'T12:00:00').getDay();
    const isSabado = diaSemana === 6;
    const jornada = isSabado ? JORNADA.sabado : JORNADA.seg_sex;
    
    if (!registro.entrada) {
      return <span className="px-2 py-1 bg-red-100 text-red-700 rounded text-xs">Ausente</span>;
    }
    
    // Verifica atraso
    const [hEntrada, mEntrada] = registro.entrada.split(':').map(Number);
    const [hJornada, mJornada] = jornada.entrada.split(':').map(Number);
    
    if (hEntrada > hJornada || (hEntrada === hJornada && mEntrada > mJornada)) {
      const atraso = (hEntrada * 60 + mEntrada) - (hJornada * 60 + mJornada);
      return <span className="px-2 py-1 bg-yellow-100 text-yellow-700 rounded text-xs">Atraso {atraso}min</span>;
    }
    
    return <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs">Regular</span>;
  };

  const getFuncionarioNome = (id) => {
    const func = funcionarios.find(f => f.id === id);
    return func?.nome || "-";
  };

  if (loading && funcionarios.length === 0) {
    return <div className="flex items-center justify-center min-h-[400px]"><div className="spinner w-12 h-12"></div></div>;
  }

  return (
    <div data-testid="ponto-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Ponto Eletrônico</h1>
          <p className="text-gray-500 mt-1">Registro de entrada e saída</p>
        </div>
        <Button onClick={() => openModal()} className="bg-[#10B981] hover:bg-[#059669]" data-testid="btn-novo-ponto">
          <Plus size={18} className="mr-2" />Registrar Ponto
        </Button>
      </div>

      {/* Filtros */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div>
          <Label>Data</Label>
          <Input 
            type="date" 
            value={selectedDate} 
            onChange={(e) => setSelectedDate(e.target.value)}
            data-testid="filtro-data"
          />
        </div>
        <div>
          <Label>Funcionário</Label>
          <Select value={selectedFuncionario || "all"} onValueChange={(v) => setSelectedFuncionario(v === "all" ? "" : v)}>
            <SelectTrigger><SelectValue placeholder="Todos" /></SelectTrigger>
            <SelectContent className="z-[9999]">
              <SelectItem value="all">Todos</SelectItem>
              {funcionarios.map(f => (
                <SelectItem key={f.id} value={f.id}>{f.nome}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="flex items-end">
          <Button onClick={fetchRegistros} className="w-full bg-[#10B981] hover:bg-[#059669]">
            <Search size={16} className="mr-2" />Buscar
          </Button>
        </div>
      </div>

      {/* Cards de resumo */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <Card>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="w-12 h-12 rounded-lg bg-green-100 flex items-center justify-center">
              <CheckCircle className="text-green-600" size={24} />
            </div>
            <div>
              <p className="text-2xl font-bold text-green-600">{resumoDia.presentes}</p>
              <p className="text-sm text-gray-500">Presentes</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="w-12 h-12 rounded-lg bg-red-100 flex items-center justify-center">
              <Users className="text-red-600" size={24} />
            </div>
            <div>
              <p className="text-2xl font-bold text-red-600">{resumoDia.ausentes}</p>
              <p className="text-sm text-gray-500">Ausentes</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="w-12 h-12 rounded-lg bg-yellow-100 flex items-center justify-center">
              <AlertTriangle className="text-yellow-600" size={24} />
            </div>
            <div>
              <p className="text-2xl font-bold text-yellow-600">{resumoDia.atrasados}</p>
              <p className="text-sm text-gray-500">Atrasados</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Jornada de referência */}
      <Card className="mb-6">
        <CardContent className="p-4">
          <h3 className="font-semibold mb-3 flex items-center gap-2">
            <Clock size={18} className="text-[#10B981]" />
            Jornada de Trabalho
          </h3>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div className="p-3 bg-gray-50 rounded-lg">
              <p className="font-medium mb-2">Segunda a Sexta</p>
              <div className="flex items-center gap-4 text-gray-600">
                <span>🟢 08:00 - 11:30</span>
                <span>🍽️ Almoço</span>
                <span>🟢 13:30 - 18:00</span>
              </div>
            </div>
            <div className="p-3 bg-gray-50 rounded-lg">
              <p className="font-medium mb-2">Sábado</p>
              <div className="flex items-center gap-4 text-gray-600">
                <span>🟢 08:00 - 12:00</span>
                <span className="text-yellow-600">(Carga reduzida)</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Lista de registros */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <div className="spinner w-12 h-12"></div>
        </div>
      ) : registros.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-gray-400">
            <Clock className="mx-auto mb-4" size={48} />
            <p>Nenhum registro de ponto para esta data</p>
          </CardContent>
        </Card>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full border-collapse bg-white rounded-lg overflow-hidden shadow">
            <thead className="bg-gray-100">
              <tr>
                <th className="text-left p-3 text-sm font-medium text-gray-600">Funcionário</th>
                <th className="text-center p-3 text-sm font-medium text-gray-600">Entrada</th>
                <th className="text-center p-3 text-sm font-medium text-gray-600">Saída Almoço</th>
                <th className="text-center p-3 text-sm font-medium text-gray-600">Retorno</th>
                <th className="text-center p-3 text-sm font-medium text-gray-600">Saída</th>
                <th className="text-center p-3 text-sm font-medium text-gray-600">Horas</th>
                <th className="text-center p-3 text-sm font-medium text-gray-600">Status</th>
                <th className="text-center p-3 text-sm font-medium text-gray-600">Ações</th>
              </tr>
            </thead>
            <tbody>
              {registros.map((r) => (
                <tr key={r.id} className="border-t hover:bg-gray-50">
                  <td className="p-3 text-sm font-medium">{getFuncionarioNome(r.funcionario_id)}</td>
                  <td className="p-3 text-sm text-center">
                    <span className="inline-flex items-center gap-1">
                      <Play size={14} className="text-green-600" />
                      {r.entrada || "-"}
                    </span>
                  </td>
                  <td className="p-3 text-sm text-center">
                    <span className="inline-flex items-center gap-1">
                      <Coffee size={14} className="text-orange-500" />
                      {r.saida_almoco || "-"}
                    </span>
                  </td>
                  <td className="p-3 text-sm text-center">
                    <span className="inline-flex items-center gap-1">
                      <Coffee size={14} className="text-blue-500" />
                      {r.retorno_almoco || "-"}
                    </span>
                  </td>
                  <td className="p-3 text-sm text-center">
                    <span className="inline-flex items-center gap-1">
                      <Square size={14} className="text-red-600" />
                      {r.saida || "-"}
                    </span>
                  </td>
                  <td className="p-3 text-sm text-center font-medium">{calcularHorasTrabalhadas(r)}</td>
                  <td className="p-3 text-sm text-center">{getStatusBadge(r)}</td>
                  <td className="p-3 text-center">
                    <div className="flex justify-center gap-1">
                      <Button size="sm" variant="outline" onClick={() => openModal(r)}><Edit size={14} /></Button>
                      <Button size="sm" variant="outline" className="text-red-600" onClick={() => handleDelete(r.id)}><Trash2 size={14} /></Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Modal de Registro */}
      <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>{editingRegistro ? "Editar Registro" : "Registrar Ponto"}</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label>Funcionário *</Label>
              <Select value={formData.funcionario_id} onValueChange={(v) => setFormData({...formData, funcionario_id: v})}>
                <SelectTrigger><SelectValue placeholder="Selecione" /></SelectTrigger>
                <SelectContent className="z-[9999]">
                  {funcionarios.map(f => (
                    <SelectItem key={f.id} value={f.id}>{f.nome}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div>
              <Label>Data *</Label>
              <Input type="date" value={formData.data} onChange={(e) => setFormData({...formData, data: e.target.value})} required />
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Entrada</Label>
                <Input type="time" value={formData.entrada} onChange={(e) => setFormData({...formData, entrada: e.target.value})} />
              </div>
              <div>
                <Label>Saída Almoço</Label>
                <Input type="time" value={formData.saida_almoco} onChange={(e) => setFormData({...formData, saida_almoco: e.target.value})} />
              </div>
              <div>
                <Label>Retorno Almoço</Label>
                <Input type="time" value={formData.retorno_almoco} onChange={(e) => setFormData({...formData, retorno_almoco: e.target.value})} />
              </div>
              <div>
                <Label>Saída</Label>
                <Input type="time" value={formData.saida} onChange={(e) => setFormData({...formData, saida: e.target.value})} />
              </div>
            </div>
            
            <div>
              <Label>Observações</Label>
              <Input value={formData.observacoes} onChange={(e) => setFormData({...formData, observacoes: e.target.value})} placeholder="Ex: Atestado médico, folga compensada..." />
            </div>

            <DialogFooter className="gap-2">
              <Button type="button" variant="outline" onClick={closeModal}>Cancelar</Button>
              <Button type="submit" className="bg-[#10B981] hover:bg-[#059669]">{editingRegistro ? "Atualizar" : "Registrar"}</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
