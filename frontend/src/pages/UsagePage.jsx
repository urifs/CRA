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
  Calendar
} from "lucide-react";

export default function UsagePage() {
  const [machines, setMachines] = useState([]);
  const [oilStatus, setOilStatus] = useState([]);
  const [usageLogs, setUsageLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showLogDialog, setShowLogDialog] = useState(false);
  const [formLoading, setFormLoading] = useState(false);
  const [activeTab, setActiveTab] = useState("status");

  const [logForm, setLogForm] = useState({
    machine_id: "",
    hours: "",
    notes: ""
  });

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
          <p className="text-slate-500 mt-1">Controle de horas de uso e troca de óleo</p>
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

      {/* Alert summary */}
      {alertMachines.length > 0 && (
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
          {oilStatus.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {oilStatus.map((status) => (
                <Card 
                  key={status.machine_id}
                  className={`${status.needs_alert ? "border-orange-300 bg-orange-50/50" : ""}`}
                  data-testid={`oil-status-${status.machine_id}`}
                >
                  <CardContent className="pt-6">
                    {/* Machine header */}
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${
                          status.needs_alert ? "bg-orange-100" : "bg-slate-100"
                        }`}>
                          <Truck className={status.needs_alert ? "text-[#E31A1A]" : "text-slate-600"} size={24} />
                        </div>
                        <div>
                          <h3 className="font-bold text-slate-900">{status.machine_name}</h3>
                          <p className="font-mono text-sm text-slate-500">{status.machine_plate}</p>
                        </div>
                      </div>
                      {status.needs_alert && (
                        <span className="status-badge badge-maintenance flex items-center gap-1">
                          <AlertTriangle size={12} />
                          Alerta
                        </span>
                      )}
                    </div>

                    {/* Hours progress */}
                    <div className="space-y-2 mb-4">
                      <div className="flex justify-between text-sm">
                        <span className="text-slate-500">Horas de Uso</span>
                        <span className="font-bold">
                          {status.hours_since_change.toFixed(0)}h / 500h
                        </span>
                      </div>
                      <Progress 
                        value={(status.hours_since_change / 500) * 100} 
                        className="h-2"
                      />
                      <div className="flex justify-between text-xs">
                        <span className={`font-medium ${status.hours_remaining <= 50 ? "text-[#E31A1A]" : "text-slate-500"}`}>
                          {status.hours_remaining > 0 
                            ? `Restam ${status.hours_remaining.toFixed(0)}h`
                            : "Limite atingido!"
                          }
                        </span>
                      </div>
                    </div>

                    {/* Time progress */}
                    <div className="space-y-2 mb-4">
                      <div className="flex justify-between text-sm">
                        <span className="text-slate-500">Tempo desde última troca</span>
                        <span className="font-bold">
                          {status.days_since_change} dias / 365 dias
                        </span>
                      </div>
                      <Progress 
                        value={(status.days_since_change / 365) * 100} 
                        className="h-2"
                      />
                      <div className="flex justify-between text-xs">
                        <span className={`font-medium ${status.days_remaining <= 60 ? "text-[#E31A1A]" : "text-slate-500"}`}>
                          {status.days_remaining > 0 
                            ? `Restam ${status.days_remaining} dias`
                            : "1 ano atingido!"
                          }
                        </span>
                      </div>
                    </div>

                    {/* Info */}
                    <div className="pt-4 border-t border-slate-200 space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-slate-500 flex items-center gap-1">
                          <Calendar size={14} />
                          Última troca:
                        </span>
                        <span className="font-medium">{formatDate(status.last_oil_change_date)}</span>
                      </div>
                    </div>

                    {/* Alert message */}
                    {status.alert_reason && (
                      <div className="mt-4 p-3 bg-orange-100 rounded-lg">
                        <p className="text-sm text-orange-800 font-medium">
                          ⚠️ {status.alert_reason}
                        </p>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <div className="empty-state">
              <Truck className="text-slate-300 mb-4" size={64} />
              <p className="text-lg font-medium text-slate-600">Nenhuma máquina cadastrada</p>
              <p className="text-slate-400">Cadastre máquinas para controlar o tempo de uso</p>
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
                      </tr>
                    </thead>
                    <tbody>
                      {usageLogs.map((log) => (
                        <tr key={log.id} data-testid={`usage-log-${log.id}`}>
                          <td className="font-medium text-slate-900">{log.machine_name}</td>
                          <td className="font-mono text-slate-500">{log.machine_plate}</td>
                          <td>
                            <span className="font-bold text-[#E31A1A]">+{log.hours}h</span>
                          </td>
                          <td className="text-slate-600">{log.notes || "-"}</td>
                          <td className="text-sm text-slate-500">{formatDateTime(log.created_at)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          ) : (
            <div className="empty-state">
              <Clock className="text-slate-300 mb-4" size={64} />
              <p className="text-lg font-medium text-slate-600">Nenhum registro de uso</p>
              <p className="text-slate-400 mb-4">Registre as horas de uso das máquinas</p>
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
              <p className="text-xs text-slate-500">
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
    </div>
  );
}
