import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import { API } from "@/App";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
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
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { 
  ArrowLeft,
  HardHat, 
  Truck,
  Wrench,
  DollarSign,
  MapPin,
  Calendar,
  Plus,
  X,
  Eye,
  Edit,
  Loader2
} from "lucide-react";

export default function ObraDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [obra, setObra] = useState(null);
  const [loading, setLoading] = useState(true);
  const [allMachines, setAllMachines] = useState([]);
  const [showAddMachineDialog, setShowAddMachineDialog] = useState(false);
  const [selectedMachineId, setSelectedMachineId] = useState("");
  const [addingMachine, setAddingMachine] = useState(false);
  const [removingMachineId, setRemovingMachineId] = useState(null);

  useEffect(() => {
    fetchData();
  }, [id]);

  const fetchData = async () => {
    try {
      const [obraRes, machinesRes] = await Promise.all([
        axios.get(`${API}/obras/${id}`),
        axios.get(`${API}/machines`)
      ]);
      setObra(obraRes.data);
      setAllMachines(machinesRes.data);
    } catch (error) {
      toast.error("Erro ao carregar dados da obra");
      navigate("/obras");
    } finally {
      setLoading(false);
    }
  };

  const handleAddMachine = async () => {
    if (!selectedMachineId) return;
    setAddingMachine(true);
    
    try {
      await axios.patch(`${API}/machines/${selectedMachineId}/obra`, {
        obra_id: id
      });
      toast.success("Máquina vinculada à obra com sucesso!");
      setShowAddMachineDialog(false);
      setSelectedMachineId("");
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao vincular máquina");
    } finally {
      setAddingMachine(false);
    }
  };

  const handleRemoveMachine = async (machineId) => {
    setRemovingMachineId(machineId);
    
    try {
      await axios.patch(`${API}/machines/${machineId}/obra`, {
        obra_id: null
      });
      toast.success("Máquina removida da obra com sucesso!");
      fetchData();
    } catch (error) {
      toast.error("Erro ao remover máquina da obra");
    } finally {
      setRemovingMachineId(null);
    }
  };

  const getStatusBadge = (status) => {
    const badges = {
      em_andamento: { class: "bg-green-100 text-green-700 border-green-200", label: "Em Andamento" },
      concluida: { class: "bg-blue-100 text-[#FFC232] border-blue-200", label: "Concluída" },
      pausada: { class: "bg-yellow-100 text-yellow-700 border-yellow-200", label: "Pausada" }
    };
    const badge = badges[status] || badges.em_andamento;
    return (
      <span className={`px-3 py-1 text-sm font-bold rounded-full border ${badge.class}`}>
        {badge.label}
      </span>
    );
  };

  const getMachineStatusBadge = (status) => {
    const badges = {
      operational: { class: "badge-operational", label: "Operacional" },
      maintenance: { class: "badge-maintenance", label: "Em Manutenção" },
      broken: { class: "badge-broken", label: "Quebrado" }
    };
    const badge = badges[status] || badges.operational;
    return (
      <span className={`status-badge ${badge.class}`}>
        {badge.label}
      </span>
    );
  };

  const getMaintenanceTypeBadge = (type) => {
    const badges = {
      preventiva: { class: "bg-blue-100 text-[#FFC232]", label: "Preventiva" },
      corretiva: { class: "bg-orange-100 text-[#E31A1A]", label: "Corretiva" }
    };
    const badge = badges[type] || badges.corretiva;
    return (
      <span className={`px-2 py-0.5 text-xs font-bold rounded ${badge.class}`}>
        {badge.label}
      </span>
    );
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat("pt-BR", {
      style: "currency",
      currency: "BRL"
    }).format(value);
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return "-";
    return new Date(dateStr).toLocaleDateString("pt-BR");
  };

  // Get machines not assigned to any obra or assigned to another obra
  const availableMachines = allMachines.filter(m => !m.obra_id || m.obra_id !== id);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="spinner w-12 h-12"></div>
      </div>
    );
  }

  if (!obra) {
    return (
      <div className="text-center py-12">
        <p className="text-slate-600">Obra não encontrada</p>
        <Button variant="outline" onClick={() => navigate("/obras")} className="mt-4">
          Voltar para Obras
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in" data-testid="obra-detail-page">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => navigate("/obras")}
          data-testid="back-btn"
        >
          <ArrowLeft size={20} />
        </Button>
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <HardHat className="text-[#E31A1A]" size={32} />
            <div>
              <h1 className="page-title font-heading">{obra.name}</h1>
              {obra.location && (
                <p className="text-slate-500 flex items-center gap-1">
                  <MapPin size={14} />
                  {obra.location}
                </p>
              )}
            </div>
          </div>
        </div>
        {getStatusBadge(obra.status)}
      </div>

      {/* Info Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="stat-card">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Máquinas</p>
                <p className="text-2xl font-bold text-slate-900">{obra.machines.length}</p>
              </div>
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                <Truck className="text-[#FFC232]" size={24} />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="stat-card">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Manutenções</p>
                <p className="text-2xl font-bold text-slate-900">{obra.maintenances.length}</p>
              </div>
              <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center">
                <Wrench className="text-[#E31A1A]" size={24} />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="stat-card">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Total Gasto</p>
                <p className="text-2xl font-bold font-mono text-slate-900">{formatCurrency(obra.total_maintenance_cost)}</p>
              </div>
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                <DollarSign className="text-green-600" size={24} />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="stat-card">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Período</p>
                <p className="text-sm font-medium text-slate-900">
                  {formatDate(obra.start_date)} - {formatDate(obra.end_date)}
                </p>
              </div>
              <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                <Calendar className="text-purple-600" size={24} />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Cost Breakdown */}
      {obra.total_maintenance_cost > 0 && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-lg font-bold">Resumo de Custos</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center p-4 bg-slate-50 rounded-lg">
                <p className="text-sm text-slate-500">Total</p>
                <p className="text-xl font-bold font-mono text-slate-900">{formatCurrency(obra.total_maintenance_cost)}</p>
              </div>
              <div className="text-center p-4 bg-blue-50 rounded-lg">
                <p className="text-sm text-[#FFC232]">Preventiva</p>
                <p className="text-xl font-bold font-mono text-blue-900">{formatCurrency(obra.preventive_cost)}</p>
              </div>
              <div className="text-center p-4 bg-orange-50 rounded-lg">
                <p className="text-sm text-[#E31A1A]">Corretiva</p>
                <p className="text-xl font-bold font-mono text-orange-900">{formatCurrency(obra.corrective_cost)}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Machines Section */}
      <Card>
        <CardHeader className="flex-row items-center justify-between pb-2">
          <CardTitle className="text-lg font-bold">Máquinas na Obra</CardTitle>
          <Button
            size="sm"
            className="bg-slate-900 hover:bg-slate-800"
            onClick={() => setShowAddMachineDialog(true)}
            data-testid="add-machine-btn"
          >
            <Plus size={16} className="mr-1" />
            Adicionar Máquina
          </Button>
        </CardHeader>
        <CardContent>
          {obra.machines.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {obra.machines.map((machine) => (
                <div
                  key={machine.id}
                  className="border border-slate-200 rounded-lg p-4 hover:border-slate-300 transition-colors"
                  data-testid={`obra-machine-${machine.id}`}
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <Truck className="text-slate-400" size={20} />
                      <div>
                        <p className="font-bold text-slate-900">{machine.name}</p>
                        <p className="text-sm font-mono text-slate-500">{machine.plate}</p>
                      </div>
                    </div>
                    {getMachineStatusBadge(machine.status)}
                  </div>
                  <div className="flex items-center gap-2 mt-3">
                    <Button
                      variant="outline"
                      size="sm"
                      className="flex-1"
                      onClick={() => navigate(`/machines/${machine.id}`)}
                    >
                      <Eye size={14} className="mr-1" />
                      Ver
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      className="text-red-600 hover:text-red-700 hover:bg-red-50"
                      onClick={() => handleRemoveMachine(machine.id)}
                      disabled={removingMachineId === machine.id}
                      data-testid={`remove-machine-${machine.id}`}
                    >
                      {removingMachineId === machine.id ? (
                        <Loader2 size={14} className="animate-spin" />
                      ) : (
                        <X size={14} />
                      )}
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-slate-500">
              <Truck className="mx-auto mb-2 text-slate-300" size={48} />
              <p>Nenhuma máquina vinculada a esta obra</p>
              <Button
                variant="outline"
                size="sm"
                className="mt-2"
                onClick={() => setShowAddMachineDialog(true)}
              >
                <Plus size={14} className="mr-1" />
                Adicionar Máquina
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Maintenances Section */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-lg font-bold">Manutenções Realizadas</CardTitle>
        </CardHeader>
        <CardContent>
          {obra.maintenances.length > 0 ? (
            <div className="space-y-3">
              {obra.maintenances.slice(0, 10).map((maintenance) => (
                <div
                  key={maintenance.id}
                  className="flex items-center justify-between p-3 bg-slate-50 rounded-lg hover:bg-slate-100 transition-colors cursor-pointer"
                  onClick={() => navigate(`/maintenances/${maintenance.id}`)}
                  data-testid={`obra-maintenance-${maintenance.id}`}
                >
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-white rounded-lg flex items-center justify-center border">
                      <Wrench className="text-slate-600" size={18} />
                    </div>
                    <div>
                      <p className="font-medium text-slate-900">{maintenance.part_name}</p>
                      <p className="text-sm text-slate-500">
                        {maintenance.machine_name} • {maintenance.machine_plate}
                      </p>
                    </div>
                  </div>
                  <div className="text-right flex items-center gap-3">
                    {getMaintenanceTypeBadge(maintenance.maintenance_type)}
                    <div>
                      <p className="font-mono font-bold text-slate-900">{formatCurrency(maintenance.part_value)}</p>
                      <p className="text-xs text-slate-500">{formatDate(maintenance.replacement_date)}</p>
                    </div>
                  </div>
                </div>
              ))}
              {obra.maintenances.length > 10 && (
                <p className="text-center text-sm text-slate-500 pt-2">
                  E mais {obra.maintenances.length - 10} manutenções...
                </p>
              )}
            </div>
          ) : (
            <div className="text-center py-8 text-slate-500">
              <Wrench className="mx-auto mb-2 text-slate-300" size={48} />
              <p>Nenhuma manutenção registrada para as máquinas desta obra</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Add Machine Dialog */}
      <Dialog open={showAddMachineDialog} onOpenChange={setShowAddMachineDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="font-heading text-xl font-bold">Adicionar Máquina à Obra</DialogTitle>
            <DialogDescription>
              Selecione uma máquina para vincular a esta obra. As manutenções desta máquina serão automaticamente contabilizadas nos custos da obra.
            </DialogDescription>
          </DialogHeader>

          <div className="py-4">
            <Select
              value={selectedMachineId}
              onValueChange={setSelectedMachineId}
            >
              <SelectTrigger className="form-input" data-testid="select-machine-for-obra">
                <SelectValue placeholder="Selecione uma máquina" />
              </SelectTrigger>
              <SelectContent>
                {availableMachines.length > 0 ? (
                  availableMachines.map((machine) => (
                    <SelectItem key={machine.id} value={machine.id}>
                      {machine.name} ({machine.plate})
                      {machine.obra_name && <span className="text-slate-400 ml-2">• Em: {machine.obra_name}</span>}
                    </SelectItem>
                  ))
                ) : (
                  <div className="px-3 py-2 text-sm text-slate-500">
                    Todas as máquinas já estão nesta obra
                  </div>
                )}
              </SelectContent>
            </Select>
            
            {availableMachines.length === 0 && (
              <p className="text-sm text-[#E31A1A] mt-2">
                Todas as máquinas já estão vinculadas a esta obra ou não há máquinas cadastradas.
              </p>
            )}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowAddMachineDialog(false)}>
              Cancelar
            </Button>
            <Button
              className="bg-slate-900 hover:bg-slate-800"
              onClick={handleAddMachine}
              disabled={!selectedMachineId || addingMachine}
              data-testid="confirm-add-machine-btn"
            >
              {addingMachine ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Adicionando...
                </>
              ) : (
                "Adicionar"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
