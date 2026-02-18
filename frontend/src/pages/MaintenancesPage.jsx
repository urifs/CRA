import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { API } from "@/App";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { 
  Wrench, 
  Plus, 
  Search,
  Eye,
  Trash2,
  Calendar,
  Shield,
  AlertTriangle,
  Filter
} from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";

export default function MaintenancesPage() {
  const [maintenances, setMaintenances] = useState([]);
  const [machines, setMachines] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterType, setFilterType] = useState("all");
  const [filterMachine, setFilterMachine] = useState("all");
  const [deleteId, setDeleteId] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [maintenancesRes, machinesRes] = await Promise.all([
        axios.get(`${API}/maintenances`),
        axios.get(`${API}/machines`)
      ]);
      setMaintenances(maintenancesRes.data);
      setMachines(machinesRes.data);
    } catch (error) {
      toast.error("Erro ao carregar dados");
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteId) return;
    
    try {
      await axios.delete(`${API}/maintenances/${deleteId}`);
      toast.success("Manutenção removida com sucesso!");
      setDeleteId(null);
      fetchData();
    } catch (error) {
      toast.error("Erro ao remover manutenção");
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat("pt-BR", {
      style: "currency",
      currency: "BRL"
    }).format(value);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString("pt-BR");
  };

  const filteredMaintenances = maintenances.filter((m) => {
    const matchesSearch = 
      m.part_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      m.machine_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      m.machine_plate?.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesType = filterType === "all" || m.maintenance_type === filterType;
    const matchesMachine = filterMachine === "all" || m.machine_id === filterMachine;
    
    return matchesSearch && matchesType && matchesMachine;
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="spinner w-12 h-12"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in" data-testid="maintenances-page">
      {/* Page header */}
      <div className="page-header">
        <div>
          <h1 className="page-title font-heading">Manutenções</h1>
          <p className="text-slate-500 mt-1">Histórico de todas as manutenções</p>
        </div>
        <Button
          className="bg-orange-500 hover:bg-orange-600 text-white font-bold"
          onClick={() => navigate("/maintenances/new")}
          data-testid="new-maintenance-btn"
        >
          <Plus size={18} className="mr-2" />
          Nova Manutenção
        </Button>
      </div>

      {/* Filters */}
      <div className="flex flex-col md:flex-row gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={20} />
          <Input
            placeholder="Buscar por peça, máquina ou placa..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10 form-input"
            data-testid="maintenances-search-input"
          />
        </div>
        
        <div className="flex gap-2">
          <Select value={filterType} onValueChange={setFilterType}>
            <SelectTrigger className="w-[160px]" data-testid="filter-type-select">
              <Filter size={16} className="mr-2" />
              <SelectValue placeholder="Tipo" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todos os tipos</SelectItem>
              <SelectItem value="preventiva">Preventiva</SelectItem>
              <SelectItem value="corretiva">Corretiva</SelectItem>
            </SelectContent>
          </Select>

          <Select value={filterMachine} onValueChange={setFilterMachine}>
            <SelectTrigger className="w-[180px]" data-testid="filter-machine-select">
              <SelectValue placeholder="Máquina" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todas as máquinas</SelectItem>
              {machines.map((m) => (
                <SelectItem key={m.id} value={m.id}>
                  {m.plate} - {m.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Maintenances Table */}
      {filteredMaintenances.length > 0 ? (
        <Card>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Tipo</th>
                    <th>Peça</th>
                    <th>Máquina</th>
                    <th>Data</th>
                    <th>Valor</th>
                    <th>Fotos</th>
                    <th className="text-right">Ações</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredMaintenances.map((maintenance) => (
                    <tr 
                      key={maintenance.id}
                      className="cursor-pointer"
                      data-testid={`maintenance-row-${maintenance.id}`}
                    >
                      <td>
                        <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                          maintenance.maintenance_type === "preventiva" 
                            ? "bg-green-50" 
                            : "bg-orange-50"
                        }`}>
                          {maintenance.maintenance_type === "preventiva" ? (
                            <Shield className="text-green-600" size={16} />
                          ) : (
                            <AlertTriangle className="text-orange-500" size={16} />
                          )}
                        </div>
                      </td>
                      <td className="font-medium text-slate-900">{maintenance.part_name}</td>
                      <td>
                        <div>
                          <span className="font-mono text-slate-600">{maintenance.machine_plate}</span>
                          <br />
                          <span className="text-xs text-slate-400">{maintenance.machine_name}</span>
                        </div>
                      </td>
                      <td className="font-mono">{formatDate(maintenance.replacement_date)}</td>
                      <td className="font-bold">{formatCurrency(maintenance.part_value)}</td>
                      <td>
                        {maintenance.photos?.length > 0 ? (
                          <span className="text-sm text-slate-600">
                            {maintenance.photos.length} foto(s)
                          </span>
                        ) : (
                          <span className="text-sm text-slate-400">-</span>
                        )}
                      </td>
                      <td>
                        <div className="flex justify-end gap-1">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => navigate(`/maintenances/${maintenance.id}`)}
                            data-testid={`view-maintenance-${maintenance.id}`}
                          >
                            <Eye size={16} />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-red-600 hover:text-red-700 hover:bg-red-50"
                            onClick={(e) => {
                              e.stopPropagation();
                              setDeleteId(maintenance.id);
                            }}
                            data-testid={`delete-maintenance-${maintenance.id}`}
                          >
                            <Trash2 size={16} />
                          </Button>
                        </div>
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
          <Wrench className="text-slate-300 mb-4" size={64} />
          <p className="text-lg font-medium text-slate-600">Nenhuma manutenção encontrada</p>
          <p className="text-slate-400 mb-4">
            {searchTerm || filterType !== "all" || filterMachine !== "all"
              ? "Tente ajustar os filtros"
              : "Registre sua primeira manutenção"
            }
          </p>
          {!searchTerm && filterType === "all" && filterMachine === "all" && (
            <Button
              className="bg-orange-500 hover:bg-orange-600"
              onClick={() => navigate("/maintenances/new")}
            >
              <Plus size={18} className="mr-2" />
              Registrar Manutenção
            </Button>
          )}
        </div>
      )}

      {/* Delete Confirmation Dialog */}
      <Dialog open={!!deleteId} onOpenChange={() => setDeleteId(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="text-red-600">Confirmar Exclusão</DialogTitle>
            <DialogDescription>
              Tem certeza que deseja excluir esta manutenção? Esta ação não pode ser desfeita.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteId(null)}>
              Cancelar
            </Button>
            <Button
              className="bg-red-600 hover:bg-red-700"
              onClick={handleDelete}
              data-testid="confirm-delete-maintenance-btn"
            >
              Excluir
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
