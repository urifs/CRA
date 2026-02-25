import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "@/App";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
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
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";
import { 
  Clock, 
  Plus, 
  Truck,
  AlertTriangle,
  Loader2,
  History,
  Droplet,
  Calendar,
  Search,
  X,
  Trash2
} from "lucide-react";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

export default function UsagePage() {
  const [machines, setMachines] = useState([]);
  const [oilStatus, setOilStatus] = useState([]);
  const [usageLogs, setUsageLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [showLogDialog, setShowLogDialog] = useState(false);
  const [formLoading, setFormLoading] = useState(false);
  const [activeTab, setActiveTab] = useState("status");

  const [logForm, setLogForm] = useState({
    machine_id: "",
    hours: "",
    notes: ""
  });

  const [deleteDialog, setDeleteDialog] = useState({
    open: false,
    logId: null,
    machineName: "",
    hours: 0
  });
  const [deleteLoading, setDeleteLoading] = useState(false);

  // Estado para exclusão de máquina (card de status)
  const [deleteMachineDialog, setDeleteMachineDialog] = useState({
    open: false,
    machineId: null,
    machineName: "",
    machinePlate: ""
  });
  const [deleteMachineLoading, setDeleteMachineLoading] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [machinesRes, statusRes, logsRes] = await Promise.all([
        axios.get(`${API}/machines`),
        axios.get(`${API}/oil-change-status`),
        axios.get(`${API}/usage-logs`)
      ]);
      setMachines(machinesRes.data);
      setOilStatus(statusRes.data);
      setUsageLogs(logsRes.data);
    } catch (error) {
      toast.error("Erro ao carregar dados");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setFormLoading(true);

    try {
      await axios.post(`${API}/usage-logs`, {
        machine_id: logForm.machine_id,
        hours: parseFloat(logForm.hours),
        notes: logForm.notes
      });
      toast.success("Horas de uso registradas com sucesso!");
      setShowLogDialog(false);
      setLogForm({ machine_id: "", hours: "", notes: "" });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao registrar horas");
    } finally {
      setFormLoading(false);
    }
  };

  const handleDeleteLog = async () => {
    if (!deleteDialog.logId) return;
    
    setDeleteLoading(true);
    try {
      await axios.delete(`${API}/usage-logs/${deleteDialog.logId}`);
      toast.success("Registro de uso excluído com sucesso!");
      setDeleteDialog({ open: false, logId: null, machineName: "", hours: 0 });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao excluir registro");
    } finally {
      setDeleteLoading(false);
    }
  };

  const openDeleteDialog = (log) => {
    setDeleteDialog({
      open: true,
      logId: log.id,
      machineName: log.machine_name,
      hours: log.hours
    });
  };

  // Funções para exclusão de máquina
  const handleDeleteMachine = async () => {
    if (!deleteMachineDialog.machineId) return;
    
    setDeleteMachineLoading(true);
    try {
      await axios.delete(`${API}/machines/${deleteMachineDialog.machineId}`);
      toast.success("Máquina excluída com sucesso!");
      setDeleteMachineDialog({ open: false, machineId: null, machineName: "", machinePlate: "" });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao excluir máquina");
    } finally {
      setDeleteMachineLoading(false);
    }
  };

  const openDeleteMachineDialog = (status) => {
    setDeleteMachineDialog({
      open: true,
      machineId: status.machine_id,
      machineName: status.machine_name,
      machinePlate: status.machine_plate
    });
  };

  const formatDate = (dateString) => {
    if (!dateString) return "Nunca";
    return new Date(dateString).toLocaleDateString("pt-BR");
  };

  const formatDateTime = (dateString) => {
    return new Date(dateString).toLocaleString("pt-BR");
  };

  const getProgressColor = (hoursRemaining, daysRemaining) => {
    if (hoursRemaining <= 0 || daysRemaining <= 0) return "bg-red-500";
    if (hoursRemaining <= 50 || daysRemaining <= 60) return "bg-[#E31A1A]";
    return "bg-green-500";
  };

  const alertMachines = oilStatus.filter(s => s.needs_alert);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="spinner w-12 h-12"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in" data-testid="usage-page">
      {/* Page header */}
      <div className="page-header">
        <div>
          <h1 className="page-title font-heading">Tempo de Uso</h1>
          <p className="text-gray-500 mt-1">Controle de horas de uso e troca de óleo</p>
        </div>
        <Button
          className="bg-[#E31A1A] hover:bg-[#E31A1A] text-white font-bold"
          onClick={() => setShowLogDialog(true)}
          data-testid="add-hours-btn"
        >
          <Plus size={18} className="mr-2" />
          Registrar Horas
        </Button>
      </div>

      {/* Search Bar */}
      <div className="flex gap-4 max-w-lg">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
          <Input
            type="text"
            placeholder="Pesquisar máquinas..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10 pr-10 h-10 bg-white border-gray-200"
            data-testid="search-usage"
          />
          {searchTerm && (
            <button
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
              onClick={() => setSearchTerm("")}
            >
              <X size={16} />
            </button>
          )}
        </div>
        <Button className="bg-[#E31A1A] hover:bg-[#c41616] text-white">
          <Search size={16} className="mr-2" />
          Buscar
        </Button>
      </div>

      {/* Alert summary */}
      {alertMachines.filter(s => 
        s.machine_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (s.machine_plate || "").toLowerCase().includes(searchTerm.toLowerCase())
      ).length > 0 && (
        <Card className="bg-orange-50 border-orange-200">
          <CardContent className="py-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center">
                <Droplet className="text-[#E31A1A]" size={20} />
              </div>
              <div className="flex-1">
                <p className="font-bold text-orange-800">Atenção: Troca de Óleo Necessária</p>
                <p className="text-sm text-[#E31A1A]">
                  {alertMachines.length} {alertMachines.length === 1 ? "máquina precisa" : "máquinas precisam"} de troca de óleo
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="status" data-testid="tab-status">
            <Droplet size={16} className="mr-2" />
            Status das Máquinas
          </TabsTrigger>
          <TabsTrigger value="history" data-testid="tab-history">
            <History size={16} className="mr-2" />
            Histórico de Uso
          </TabsTrigger>
        </TabsList>

        {/* Status Tab */}
        <TabsContent value="status" className="space-y-4">
          {oilStatus.filter(s => 
            s.machine_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            (s.machine_plate || "").toLowerCase().includes(searchTerm.toLowerCase())
          ).length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
              {oilStatus
                .filter(s => 
                  s.machine_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                  (s.machine_plate || "").toLowerCase().includes(searchTerm.toLowerCase())
                )
                .map((status) => (
                <Card 
                  key={status.machine_id}
                  className={`${status.needs_alert ? "border-orange-300 bg-orange-50/50" : ""} relative group`}
                  data-testid={`oil-status-${status.machine_id}`}
                >
                  {/* Botão de excluir no canto superior direito */}
                  <Button
                    variant="ghost"
                    size="sm"
                    className="absolute top-1 right-1 opacity-0 group-hover:opacity-100 transition-opacity text-gray-400 hover:text-red-500 hover:bg-red-50 h-7 w-7 p-0"
                    onClick={() => openDeleteMachineDialog(status)}
                    data-testid={`delete-machine-${status.machine_id}`}
                  >
                    <Trash2 size={14} />
                  </Button>
                  
                  <CardContent className="p-3">
                    {/* Machine header - compacto */}
                    <div className="flex items-center gap-2 mb-2">
                      <div className={`w-8 h-8 rounded flex items-center justify-center flex-shrink-0 ${
                        status.needs_alert ? "bg-orange-100" : "bg-gray-100"
                      }`}>
                        <Truck className={status.needs_alert ? "text-[#E31A1A]" : "text-gray-600"} size={16} />
                      </div>
                      <div className="min-w-0 flex-1">
                        <h3 className="font-bold text-black text-sm truncate">{status.machine_name}</h3>
                        {status.machine_plate && (
                          <p className="font-mono text-xs text-gray-500">{status.machine_plate}</p>
                        )}
                      </div>
                      {status.needs_alert && (
                        <span className="bg-orange-100 text-orange-700 text-xs px-1.5 py-0.5 rounded flex items-center gap-1 flex-shrink-0">
                          <AlertTriangle size={10} />
                        </span>
                      )}
                    </div>

                    {/* Hours progress - compacto */}
                    <div className="space-y-1 mb-2">
                      <div className="flex justify-between text-xs">
                        <span className="text-gray-500">Horas</span>
                        <span className="font-semibold">
                          {status.hours_since_change.toFixed(0)}h / 500h
                        </span>
                      </div>
                      <Progress 
                        value={(status.hours_since_change / 500) * 100} 
                        className="h-1.5"
                      />
                      <p className={`text-xs ${status.hours_remaining <= 50 ? "text-[#E31A1A] font-medium" : "text-gray-400"}`}>
                        {status.hours_remaining > 0 
                          ? `Restam ${status.hours_remaining.toFixed(0)}h`
                          : "Limite!"
                        }
                      </p>
                    </div>

                    {/* Time progress - compacto */}
                    <div className="space-y-1 mb-2">
                      <div className="flex justify-between text-xs">
                        <span className="text-gray-500">Tempo</span>
                        <span className="font-semibold">
                          {status.days_since_change}d / 365d
                        </span>
                      </div>
                      <Progress 
                        value={(status.days_since_change / 365) * 100} 
                        className="h-1.5"
                      />
                      <p className={`text-xs ${status.days_remaining <= 60 ? "text-[#E31A1A] font-medium" : "text-gray-400"}`}>
                        {status.days_remaining > 0 
                          ? `Restam ${status.days_remaining}d`
                          : "1 ano!"
                        }
                      </p>
                    </div>

                    {/* Info - compacto */}
                    <div className="pt-2 border-t border-gray-100 text-xs flex justify-between items-center">
                      <span className="text-gray-400 flex items-center gap-1">
                        <Calendar size={10} />
                        Troca:
                      </span>
                      <span className="font-medium text-gray-600">{formatDate(status.last_oil_change_date)}</span>
                    </div>

                    {/* Alert message - compacto */}
                    {status.alert_reason && (
                      <div className="mt-2 p-1.5 bg-orange-100 rounded text-xs text-orange-800">
                        ⚠️ {status.alert_reason}
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <div className="empty-state">
              <Truck className="text-gray-300 mb-4" size={64} />
              <p className="text-lg font-medium text-gray-600">Nenhuma máquina cadastrada</p>
              <p className="text-gray-400">Cadastre máquinas para controlar o tempo de uso</p>
            </div>
          )}
        </TabsContent>

        {/* History Tab */}
        <TabsContent value="history">
          {usageLogs.length > 0 ? (
            <Card>
              <CardContent className="p-0">
                <div className="overflow-x-auto">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Máquina</th>
                        <th>Placa</th>
                        <th>Horas</th>
                        <th>Observações</th>
                        <th>Data</th>
                        <th className="text-right">Ações</th>
                      </tr>
                    </thead>
                    <tbody>
                      {usageLogs.map((log) => (
                        <tr key={log.id} data-testid={`usage-log-${log.id}`}>
                          <td className="font-medium text-black">{log.machine_name}</td>
                          <td className="font-mono text-gray-500">{log.machine_plate}</td>
                          <td>
                            <span className="font-bold text-[#E31A1A]">+{log.hours}h</span>
                          </td>
                          <td className="text-gray-600">{log.notes || "-"}</td>
                          <td className="text-sm text-gray-500">{formatDateTime(log.created_at)}</td>
                          <td className="text-right">
                            <Button
                              variant="ghost"
                              size="sm"
                              className="text-red-500 hover:text-red-700 hover:bg-red-50"
                              onClick={() => openDeleteDialog(log)}
                              data-testid={`delete-log-${log.id}`}
                            >
                              <Trash2 size={16} />
                            </Button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          ) : (
            <div className="empty-state">
              <Clock className="text-gray-300 mb-4" size={64} />
              <p className="text-lg font-medium text-gray-600">Nenhum registro de uso</p>
              <p className="text-gray-400 mb-4">Registre as horas de uso das máquinas</p>
              <Button
                className="bg-[#E31A1A] hover:bg-[#E31A1A]"
                onClick={() => setShowLogDialog(true)}
              >
                <Plus size={18} className="mr-2" />
                Registrar Horas
              </Button>
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* Add Hours Dialog */}
      <Dialog open={showLogDialog} onOpenChange={setShowLogDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="font-heading text-xl font-bold flex items-center gap-2">
              <Clock className="text-[#E31A1A]" size={24} />
              Registrar Horas de Uso
            </DialogTitle>
            <DialogDescription>
              Adicione as horas de uso de uma máquina. Essas horas serão contabilizadas para o controle de troca de óleo.
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label className="form-label">Máquina *</Label>
              <Select
                value={logForm.machine_id}
                onValueChange={(value) => setLogForm({...logForm, machine_id: value})}
              >
                <SelectTrigger className="form-input" data-testid="usage-machine-select">
                  <SelectValue placeholder="Selecione a máquina" />
                </SelectTrigger>
                <SelectContent>
                  {machines.map((machine) => (
                    <SelectItem key={machine.id} value={machine.id}>
                      <span className="font-mono">{machine.plate}</span> - {machine.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label className="form-label">Horas de Uso *</Label>
              <Input
                type="number"
                step="0.1"
                min="0.1"
                value={logForm.hours}
                onChange={(e) => setLogForm({...logForm, hours: e.target.value})}
                placeholder="Ex: 8.5"
                required
                className="form-input font-mono text-lg"
                data-testid="usage-hours-input"
              />
              <p className="text-xs text-gray-500">
                Informe quantas horas a máquina foi utilizada
              </p>
            </div>

            <div className="space-y-2">
              <Label className="form-label">Observações</Label>
              <Input
                value={logForm.notes}
                onChange={(e) => setLogForm({...logForm, notes: e.target.value})}
                placeholder="Notas opcionais..."
                className="form-input"
                data-testid="usage-notes-input"
              />
            </div>

            <DialogFooter className="gap-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => setShowLogDialog(false)}
              >
                Cancelar
              </Button>
              <Button
                type="submit"
                className="bg-[#E31A1A] hover:bg-[#E31A1A]"
                disabled={formLoading || !logForm.machine_id}
                data-testid="usage-submit-btn"
              >
                {formLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Registrando...
                  </>
                ) : (
                  "Registrar Horas"
                )}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteDialog.open} onOpenChange={(open) => !open && setDeleteDialog({ ...deleteDialog, open: false })}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center gap-2 text-red-600">
              <Trash2 size={20} />
              Excluir Registro de Uso
            </AlertDialogTitle>
            <AlertDialogDescription className="space-y-2">
              <p>Tem certeza que deseja excluir este registro?</p>
              <div className="bg-gray-100 p-3 rounded-lg mt-2">
                <p className="font-medium text-black">{deleteDialog.machineName}</p>
                <p className="text-sm text-gray-600">Horas: <span className="font-bold text-[#E31A1A]">+{deleteDialog.hours}h</span></p>
              </div>
              <p className="text-orange-600 text-sm font-medium mt-2">
                ⚠️ As horas serão subtraídas do total da máquina.
              </p>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={deleteLoading}>Cancelar</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteLog}
              disabled={deleteLoading}
              className="bg-red-600 hover:bg-red-700"
              data-testid="confirm-delete-log"
            >
              {deleteLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Excluindo...
                </>
              ) : (
                "Excluir"
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Delete Machine Confirmation Dialog */}
      <AlertDialog open={deleteMachineDialog.open} onOpenChange={(open) => !open && setDeleteMachineDialog({ ...deleteMachineDialog, open: false })}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center gap-2 text-red-600">
              <Truck size={20} />
              Excluir Máquina
            </AlertDialogTitle>
            <AlertDialogDescription className="space-y-2">
              <p>Tem certeza que deseja excluir esta máquina do sistema?</p>
              <div className="bg-gray-100 p-3 rounded-lg mt-2">
                <p className="font-medium text-black">{deleteMachineDialog.machineName}</p>
                <p className="text-sm text-gray-600 font-mono">{deleteMachineDialog.machinePlate}</p>
              </div>
              <div className="bg-red-50 border border-red-200 p-3 rounded-lg mt-2">
                <p className="text-red-700 text-sm font-medium">
                  ⚠️ Esta ação irá:
                </p>
                <ul className="text-red-600 text-sm mt-1 list-disc list-inside">
                  <li>Remover a máquina do sistema</li>
                  <li>Excluir todas as manutenções associadas</li>
                  <li>Esta ação não pode ser desfeita</li>
                </ul>
              </div>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={deleteMachineLoading}>Cancelar</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteMachine}
              disabled={deleteMachineLoading}
              className="bg-red-600 hover:bg-red-700"
              data-testid="confirm-delete-machine"
            >
              {deleteMachineLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Excluindo...
                </>
              ) : (
                "Excluir Máquina"
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
