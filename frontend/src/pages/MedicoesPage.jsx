import { useState, useEffect } from "react";
import { useParams, useNavigate, useSearchParams } from "react-router-dom";
import axios from "axios";
import { API } from "@/App";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { DecimalInput } from "@/components/DecimalInput";
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { 
  ArrowLeft,
  Plus,
  Truck,
  Clock,
  Gauge,
  Fuel,
  Package,
  Ruler,
  Edit,
  Trash2,
  Search,
  Filter,
  Calendar,
  BarChart3,
  TrendingUp,
  AlertCircle,
  Loader2,
  HardHat,
  ChevronDown
} from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

const TIPOS_MEDICAO = [
  { value: "horimetro", label: "Horímetro", icon: Clock, unidade: "horas", color: "text-blue-500" },
  { value: "km", label: "Quilometragem", icon: Gauge, unidade: "km", color: "text-green-500" },
  { value: "combustivel", label: "Combustível", icon: Fuel, unidade: "litros", color: "text-orange-500" },
  { value: "producao", label: "Produção", icon: Package, unidade: "toneladas", color: "text-purple-500" },
  { value: "outro", label: "Outro", icon: Ruler, unidade: "", color: "text-gray-500" }
];

const UNIDADES = [
  "horas", "km", "litros", "toneladas", "m³", "m²", "metros", "unidades", "viagens", "cargas"
];

export default function MedicoesPage() {
  const { obraId } = useParams();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  
  const [obra, setObra] = useState(null);
  const [maquinas, setMaquinas] = useState([]);
  const [medicoes, setMedicoes] = useState([]);
  const [resumo, setResumo] = useState(null);
  const [loading, setLoading] = useState(true);
  
  // Filters
  const [searchTerm, setSearchTerm] = useState("");
  const [filterMaquina, setFilterMaquina] = useState("");
  const [filterTipo, setFilterTipo] = useState("");
  const [filterDataInicio, setFilterDataInicio] = useState("");
  const [filterDataFim, setFilterDataFim] = useState("");
  
  // Modal
  const [showModal, setShowModal] = useState(false);
  const [editingMedicao, setEditingMedicao] = useState(null);
  const anexosRef = useRef(null);
  const [formLoading, setFormLoading] = useState(false);
  
  const [formData, setFormData] = useState({
    maquina_id: searchParams.get("maquina") || "",
    tipo: "horimetro",
    valor_anterior: "",
    valor_atual: "",
    unidade: "horas",
    data_medicao: new Date().toISOString().split("T")[0],
    observacoes: ""
  });

  useEffect(() => {
    fetchData();
  }, [obraId]);

  const fetchData = async () => {
    try {
      const [obraRes, maquinasRes, medicoesRes, resumoRes] = await Promise.all([
        axios.get(`${API}/obras/${obraId}`),
        axios.get(`${API}/machines`),
        axios.get(`${API}/medicoes?obra_id=${obraId}`),
        axios.get(`${API}/medicoes/resumo/${obraId}`)
      ]);
      
      setObra(obraRes.data);
      // Filter machines that belong to this obra
      const obraMachines = maquinasRes.data.filter(m => m.obra_id === obraId);
      setMaquinas(obraMachines);
      setMedicoes(medicoesRes.data);
      setResumo(resumoRes.data);
    } catch (error) {
      toast.error("Erro ao carregar dados");
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenModal = (medicao = null) => {
    if (medicao) {
      setEditingMedicao(medicao);
      setFormData({
        maquina_id: medicao.maquina_id,
        tipo: medicao.tipo,
        valor_anterior: medicao.valor_anterior?.toString() || "",
        valor_atual: medicao.valor_atual?.toString() || "",
        unidade: medicao.unidade,
        data_medicao: medicao.data_medicao?.split("T")[0] || "",
        observacoes: medicao.observacoes || ""
      });
    } else {
      setEditingMedicao(null);
      
      // Get last measurement for selected machine
      const maquinaId = searchParams.get("maquina") || (maquinas.length > 0 ? maquinas[0].id : "");
      let valorAnterior = "";
      
      if (maquinaId) {
        const ultimaMedicao = medicoes.find(m => m.maquina_id === maquinaId && m.tipo === "horimetro");
        if (ultimaMedicao) {
          valorAnterior = ultimaMedicao.valor_atual?.toString() || "";
        }
      }
      
      setFormData({
        maquina_id: maquinaId,
        tipo: "horimetro",
        valor_anterior: valorAnterior,
        valor_atual: "",
        unidade: "horas",
        data_medicao: new Date().toISOString().split("T")[0],
        observacoes: ""
      });
    }
    setShowModal(true);
  };

  const handleTipoChange = (tipo) => {
    const tipoInfo = TIPOS_MEDICAO.find(t => t.value === tipo);
    
    // Get last measurement for this type and machine
    let valorAnterior = "";
    if (formData.maquina_id) {
      const ultimaMedicao = medicoes.find(m => m.maquina_id === formData.maquina_id && m.tipo === tipo);
      if (ultimaMedicao) {
        valorAnterior = ultimaMedicao.valor_atual?.toString() || "";
      }
    }
    
    setFormData({
      ...formData,
      tipo,
      unidade: tipoInfo?.unidade || "",
      valor_anterior: valorAnterior
    });
  };

  const handleMaquinaChange = (maquinaId) => {
    // Get last measurement for this machine and current type
    let valorAnterior = "";
    const ultimaMedicao = medicoes.find(m => m.maquina_id === maquinaId && m.tipo === formData.tipo);
    if (ultimaMedicao) {
      valorAnterior = ultimaMedicao.valor_atual?.toString() || "";
    }
    
    setFormData({
      ...formData,
      maquina_id: maquinaId,
      valor_anterior: valorAnterior
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.maquina_id || !formData.valor_atual) {
      toast.error("Preencha todos os campos obrigatórios");
      return;
    }
    
    setFormLoading(true);
    try {
      const payload = {
        obra_id: obraId,
        maquina_id: formData.maquina_id,
        tipo: formData.tipo,
        valor_anterior: parseFloat(formData.valor_anterior) || 0,
        valor_atual: parseFloat(formData.valor_atual),
        unidade: formData.unidade,
        data_medicao: formData.data_medicao,
        observacoes: formData.observacoes
      };

      if (editingMedicao) {
        await axios.put(`${API}/medicoes/${editingMedicao.id}`, payload);
        await anexosRef.current?.flushPending(editingMedicao.id);
        toast.success("Medição atualizada!");
      } else {
        const _r = await axios.post(`${API}/medicoes`, payload);
        await anexosRef.current?.flushPending(_r.data?.id);
        toast.success("Medição registrada!");
      }
      
      setShowModal(false);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao salvar medição");
    } finally {
      setFormLoading(false);
    }
  };

  const handleDelete = async (medicaoId) => {
    if (!confirm("Excluir esta medição?")) return;
    try {
      await axios.delete(`${API}/medicoes/${medicaoId}`);
      toast.success("Medição excluída!");
      fetchData();
    } catch (error) {
      toast.error("Erro ao excluir medição");
    }
  };

  const getTipoInfo = (tipo) => TIPOS_MEDICAO.find(t => t.value === tipo) || TIPOS_MEDICAO[4];

  const filteredMedicoes = medicoes.filter(m => {
    if (searchTerm && !m.maquina_nome?.toLowerCase().includes(searchTerm.toLowerCase())) return false;
    if (filterMaquina && m.maquina_id !== filterMaquina) return false;
    if (filterTipo && m.tipo !== filterTipo) return false;
    if (filterDataInicio && m.data_medicao < filterDataInicio) return false;
    if (filterDataFim && m.data_medicao > filterDataFim) return false;
    return true;
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="w-8 h-8 animate-spin text-[#E31A1A]" />
      </div>
    );
  }

  return (
    <div data-testid="medicoes-page">
      {/* Header */}
      <div className="page-header flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="sm" onClick={() => navigate(`/gerenciamento/obras/${obraId}`)} className="p-1">
            <ArrowLeft size={20} />
          </Button>
          <div>
            <h1 className="page-title flex items-center gap-2">
              <BarChart3 className="text-[#D4A000]" />
              Medições de Máquinas
            </h1>
            <p className="text-gray-500 text-sm">{obra?.name}</p>
          </div>
        </div>
        <Button className="bg-[#E31A1A] hover:bg-red-700" onClick={() => handleOpenModal()}>
          <Plus size={18} className="mr-2" />
          Nova Medição
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center">
                <Truck className="text-blue-600" size={20} />
              </div>
              <div>
                <p className="text-xs text-gray-500">Máquinas na Obra</p>
                <p className="text-xl font-bold">{maquinas.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-green-100 flex items-center justify-center">
                <BarChart3 className="text-green-600" size={20} />
              </div>
              <div>
                <p className="text-xs text-gray-500">Total de Medições</p>
                <p className="text-xl font-bold">{medicoes.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-orange-100 flex items-center justify-center">
                <Clock className="text-orange-600" size={20} />
              </div>
              <div>
                <p className="text-xs text-gray-500">Horas Totais</p>
                <p className="text-xl font-bold">
                  {medicoes.filter(m => m.tipo === "horimetro").reduce((acc, m) => acc + (m.diferenca || 0), 0).toFixed(0)}h
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-purple-100 flex items-center justify-center">
                <Gauge className="text-purple-600" size={20} />
              </div>
              <div>
                <p className="text-xs text-gray-500">Km Totais</p>
                <p className="text-xl font-bold">
                  {medicoes.filter(m => m.tipo === "km").reduce((acc, m) => acc + (m.diferenca || 0), 0).toFixed(0)} km
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="lista" className="mb-6">
        <TabsList className="grid w-full max-w-md grid-cols-2">
          <TabsTrigger value="lista">Lista de Medições</TabsTrigger>
          <TabsTrigger value="resumo">Resumo por Máquina</TabsTrigger>
        </TabsList>

        <TabsContent value="lista">
          {/* Filters */}
          <Card className="mb-4">
            <CardContent className="p-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-6 gap-4">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
                  <Input
                    placeholder="Buscar máquina..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-9"
                  />
                </div>
                <Select value={filterMaquina} onValueChange={(v) => setFilterMaquina(v === "all" ? "" : v)}>
                  <SelectTrigger>
                    <SelectValue placeholder="Todas as máquinas" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Todas as máquinas</SelectItem>
                    {maquinas.map(m => (
                      <SelectItem key={m.id} value={m.id}>{m.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Select value={filterTipo} onValueChange={(v) => setFilterTipo(v === "all" ? "" : v)}>
                  <SelectTrigger>
                    <SelectValue placeholder="Todos os tipos" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Todos os tipos</SelectItem>
                    {TIPOS_MEDICAO.map(t => (
                      <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Input
                  type="date"
                  placeholder="Data início"
                  value={filterDataInicio}
                  onChange={(e) => setFilterDataInicio(e.target.value)}
                />
                <Input
                  type="date"
                  placeholder="Data fim"
                  value={filterDataFim}
                  onChange={(e) => setFilterDataFim(e.target.value)}
                />
                <Button className="bg-[#E31A1A] hover:bg-[#c41616] text-white">
                  <Search size={16} className="mr-2" />
                  Buscar
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Medicoes List */}
          {filteredMedicoes.length === 0 ? (
            <Card>
              <CardContent className="p-8 text-center">
                <BarChart3 size={48} className="mx-auto text-gray-300 mb-4" />
                <p className="text-gray-500">Nenhuma medição encontrada</p>
                <Button className="mt-4 bg-[#E31A1A] hover:bg-red-700" onClick={() => handleOpenModal()}>
                  <Plus size={16} className="mr-2" />
                  Registrar Primeira Medição
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-3">
              {filteredMedicoes.map(medicao => {
                const tipoInfo = getTipoInfo(medicao.tipo);
                const TipoIcon = tipoInfo.icon;
                return (
                  <Card key={medicao.id} className="hover:shadow-md transition-shadow">
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                          <div className={`w-12 h-12 rounded-lg bg-gray-100 flex items-center justify-center`}>
                            <TipoIcon className={tipoInfo.color} size={24} />
                          </div>
                          <div>
                            <div className="flex items-center gap-2">
                              <span className="font-semibold">{medicao.maquina_nome}</span>
                              {medicao.maquina_placa && (
                                <span className="text-xs bg-gray-100 px-2 py-0.5 rounded">{medicao.maquina_placa}</span>
                              )}
                            </div>
                            <div className="flex items-center gap-3 text-sm text-gray-500 mt-1">
                              <span className="flex items-center gap-1">
                                <Calendar size={14} />
                                {new Date(medicao.data_medicao).toLocaleDateString("pt-BR")}
                              </span>
                              <span className="capitalize">{tipoInfo.label}</span>
                            </div>
                          </div>
                        </div>
                        
                        <div className="flex items-center gap-6">
                          <div className="text-right">
                            <div className="flex items-center gap-2">
                              <span className="text-sm text-gray-400">{medicao.valor_anterior}</span>
                              <TrendingUp size={16} className="text-green-500" />
                              <span className="font-bold text-lg">{medicao.valor_atual}</span>
                              <span className="text-sm text-gray-500">{medicao.unidade}</span>
                            </div>
                            <p className="text-sm text-green-600">
                              +{medicao.diferenca?.toFixed(2)} {medicao.unidade}
                            </p>
                          </div>
                          
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" size="sm">
                                <ChevronDown size={16} />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent>
                              <DropdownMenuItem onClick={() => handleOpenModal(medicao)}>
                                <Edit size={14} className="mr-2" /> Editar
                              </DropdownMenuItem>
                              <DropdownMenuItem onClick={() => handleDelete(medicao.id)} className="text-red-600">
                                <Trash2 size={14} className="mr-2" /> Excluir
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </div>
                      </div>
                      {medicao.observacoes && (
                        <p className="text-sm text-gray-500 mt-2 pl-16 border-l-2 border-gray-200 ml-6">
                          {medicao.observacoes}
                        </p>
                      )}
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </TabsContent>

        <TabsContent value="resumo">
          {/* Summary by Machine */}
          {resumo?.maquinas?.length === 0 ? (
            <Card>
              <CardContent className="p-8 text-center">
                <Truck size={48} className="mx-auto text-gray-300 mb-4" />
                <p className="text-gray-500">Nenhuma máquina com medições</p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4">
              {resumo?.maquinas?.map(maq => (
                <Card key={maq.maquina_id}>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-lg flex items-center gap-2">
                      <Truck className="text-[#D4A000]" size={20} />
                      {maq.maquina_nome}
                      {maq.maquina_placa && (
                        <span className="text-sm font-normal bg-gray-100 px-2 py-0.5 rounded">{maq.maquina_placa}</span>
                      )}
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      {Object.values(maq.medicoes_por_tipo).map(tipo => {
                        const tipoInfo = getTipoInfo(tipo.tipo);
                        const TipoIcon = tipoInfo.icon;
                        return (
                          <div key={tipo.tipo} className="bg-gray-50 rounded-lg p-3">
                            <div className="flex items-center gap-2 mb-2">
                              <TipoIcon className={tipoInfo.color} size={16} />
                              <span className="text-sm font-medium capitalize">{tipoInfo.label}</span>
                            </div>
                            <p className="text-2xl font-bold">{tipo.total_diferenca.toFixed(2)}</p>
                            <p className="text-xs text-gray-500">{tipo.unidade} trabalhadas</p>
                            <div className="text-xs text-gray-400 mt-1">
                              {tipo.valor_inicial} → {tipo.valor_final} ({tipo.qtd_medicoes} medições)
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* Modal */}
      <Dialog open={showModal} onOpenChange={setShowModal}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>
              {editingMedicao ? "Editar Medição" : "Nova Medição"}
            </DialogTitle>
          </DialogHeader>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Machine Selection */}
            <div>
              <Label>Máquina *</Label>
              <Select value={formData.maquina_id} onValueChange={handleMaquinaChange}>
                <SelectTrigger>
                  <SelectValue placeholder="Selecione a máquina" />
                </SelectTrigger>
                <SelectContent>
                  {maquinas.map(m => (
                    <SelectItem key={m.id} value={m.id}>
                      {m.name} {m.plate && `(${m.plate})`}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {maquinas.length === 0 && (
                <p className="text-xs text-orange-600 mt-1 flex items-center gap-1">
                  <AlertCircle size={12} />
                  Nenhuma máquina vinculada a esta obra
                </p>
              )}
            </div>

            {/* Measurement Type */}
            <div>
              <Label>Tipo de Medição *</Label>
              <div className="grid grid-cols-5 gap-2 mt-2">
                {TIPOS_MEDICAO.map(tipo => {
                  const Icon = tipo.icon;
                  return (
                    <Button
                      key={tipo.value}
                      type="button"
                      variant={formData.tipo === tipo.value ? "default" : "outline"}
                      className={`flex flex-col items-center h-auto py-3 ${formData.tipo === tipo.value ? "bg-[#E31A1A]" : ""}`}
                      onClick={() => handleTipoChange(tipo.value)}
                    >
                      <Icon size={20} className={formData.tipo === tipo.value ? "text-white" : tipo.color} />
                      <span className="text-xs mt-1">{tipo.label}</span>
                    </Button>
                  );
                })}
              </div>
            </div>

            {/* Values */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Valor Anterior</Label>
                <DecimalInput
                  value={formData.valor_anterior}
                  onChange={(v) => setFormData({...formData, valor_anterior: v})}
                  placeholder="0,00"
                />
              </div>
              <div>
                <Label>Valor Atual *</Label>
                <DecimalInput
                  value={formData.valor_atual}
                  onChange={(v) => setFormData({...formData, valor_atual: v})}
                  placeholder="0,00"
                  required
                />
              </div>
            </div>

            {/* Calculated Difference */}
            {formData.valor_atual && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-3 text-center">
                <p className="text-sm text-green-700">Diferença calculada:</p>
                <p className="text-2xl font-bold text-green-600">
                  +{(parseFloat(formData.valor_atual || 0) - parseFloat(formData.valor_anterior || 0)).toFixed(2)} {formData.unidade}
                </p>
              </div>
            )}

            {/* Unit */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Unidade</Label>
                <Select value={formData.unidade} onValueChange={(v) => setFormData({...formData, unidade: v})}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {UNIDADES.map(u => (
                      <SelectItem key={u} value={u}>{u}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Data da Medição *</Label>
                <Input
                  type="date"
                  value={formData.data_medicao}
                  onChange={(e) => setFormData({...formData, data_medicao: e.target.value})}
                  required
                />
              </div>
            </div>

            {/* Notes */}
            <div>
              <Label>Observações</Label>
              <Textarea
                value={formData.observacoes}
                onChange={(e) => setFormData({...formData, observacoes: e.target.value})}
                placeholder="Observações sobre a medição..."
                rows={2}
              />
            </div>

            <AnexosManager
              ref={anexosRef}
              entityType="medicao"
              entityId={editingMedicao?.id}
            />

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setShowModal(false)}>
                Cancelar
              </Button>
              <Button type="submit" className="bg-[#E31A1A] hover:bg-red-700" disabled={formLoading}>
                {formLoading ? <Loader2 className="animate-spin mr-2" size={16} /> : null}
                {editingMedicao ? "Atualizar" : "Registrar"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
