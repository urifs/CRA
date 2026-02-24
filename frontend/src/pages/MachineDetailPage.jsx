import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import { API } from "@/App";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { 
  Truck, 
  ArrowLeft, 
  Calendar,
  Shield,
  AlertTriangle,
  Wrench,
  Plus,
  DollarSign
} from "lucide-react";

export default function MachineDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [machine, setMachine] = useState(null);
  const [maintenances, setMaintenances] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, [id]);

  const fetchData = async () => {
    try {
      const [machineRes, maintenancesRes] = await Promise.all([
        axios.get(`${API}/machines/${id}`),
        axios.get(`${API}/maintenances?machine_id=${id}`)
      ]);
      setMachine(machineRes.data);
      setMaintenances(maintenancesRes.data);
    } catch (error) {
      toast.error("Erro ao carregar dados da máquina");
      navigate("/machines");
    } finally {
      setLoading(false);
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

  const getStatusBadge = (status) => {
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

  const totalSpent = maintenances.reduce((sum, m) => sum + m.part_value, 0);
  const preventiveCount = maintenances.filter(m => m.maintenance_type === "preventiva").length;
  const correctiveCount = maintenances.filter(m => m.maintenance_type === "corretiva").length;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="spinner w-12 h-12"></div>
      </div>
    );
  }

  if (!machine) {
    return null;
  }

  return (
    <div className="space-y-6 animate-fade-in" data-testid="machine-detail-page">
      {/* Back button */}
      <Button
        variant="ghost"
        onClick={() => navigate("/machines")}
        className="text-slate-600 hover:text-slate-900"
        data-testid="back-btn"
      >
        <ArrowLeft size={18} className="mr-2" />
        Voltar para Máquinas
      </Button>

      {/* Machine Header */}
      <Card>
        <CardContent className="p-6">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 bg-slate-100 rounded-xl flex items-center justify-center">
                <Truck className="text-slate-600" size={32} />
              </div>
              <div>
                <div className="flex items-center gap-3">
                  <h1 className="text-2xl font-bold font-heading text-slate-900">
                    {machine.name}
                  </h1>
                  {getStatusBadge(machine.status)}
                </div>
                <p className="font-mono text-lg text-slate-500 mt-1">{machine.plate}</p>
              </div>
            </div>
            <Button
              className="bg-[#E31A1A] hover:bg-[#E31A1A]"
              onClick={() => navigate(`/maintenances/new?machine=${machine.id}`)}
              data-testid="new-maintenance-for-machine-btn"
            >
              <Plus size={18} className="mr-2" />
              Nova Manutenção
            </Button>
          </div>

          {/* Machine Details */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6 pt-6 border-t border-slate-200">
            <div>
              <p className="text-xs font-bold uppercase tracking-wider text-slate-500">Categoria</p>
              <p className="font-medium text-slate-900 mt-1">{machine.category_name || "-"}</p>
            </div>
            <div>
              <p className="text-xs font-bold uppercase tracking-wider text-slate-500">Marca</p>
              <p className="font-medium text-slate-900 mt-1">{machine.brand || "-"}</p>
            </div>
            <div>
              <p className="text-xs font-bold uppercase tracking-wider text-slate-500">Modelo</p>
              <p className="font-medium text-slate-900 mt-1">{machine.model || "-"}</p>
            </div>
            <div>
              <p className="text-xs font-bold uppercase tracking-wider text-slate-500">Ano</p>
              <p className="font-mono text-slate-900 mt-1">{machine.year || "-"}</p>
            </div>
          </div>

          {machine.notes && (
            <div className="mt-4 pt-4 border-t border-slate-200">
              <p className="text-xs font-bold uppercase tracking-wider text-slate-500">Observações</p>
              <p className="text-slate-700 mt-1">{machine.notes}</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="stat-card">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-bold uppercase tracking-wider text-slate-500">
                  Total de Manutenções
                </p>
                <p className="text-3xl font-black text-slate-900 mt-1 font-heading">
                  {maintenances.length}
                </p>
              </div>
              <div className="w-12 h-12 bg-slate-100 rounded-lg flex items-center justify-center">
                <Wrench className="text-slate-600" size={24} />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="stat-card">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-bold uppercase tracking-wider text-slate-500">
                  Preventivas
                </p>
                <p className="text-3xl font-black text-green-600 mt-1 font-heading">
                  {preventiveCount}
                </p>
              </div>
              <div className="w-12 h-12 bg-green-50 rounded-lg flex items-center justify-center">
                <Shield className="text-green-600" size={24} />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="stat-card">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-bold uppercase tracking-wider text-slate-500">
                  Corretivas
                </p>
                <p className="text-3xl font-black text-[#E31A1A] mt-1 font-heading">
                  {correctiveCount}
                </p>
              </div>
              <div className="w-12 h-12 bg-orange-50 rounded-lg flex items-center justify-center">
                <AlertTriangle className="text-[#E31A1A]" size={24} />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="stat-card">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-bold uppercase tracking-wider text-slate-500">
                  Total Gasto
                </p>
                <p className="text-2xl font-black text-slate-900 mt-1 font-heading">
                  {formatCurrency(totalSpent)}
                </p>
              </div>
              <div className="w-12 h-12 bg-slate-100 rounded-lg flex items-center justify-center">
                <DollarSign className="text-slate-600" size={24} />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Maintenance History */}
      <Card>
        <CardHeader className="border-b border-slate-200">
          <CardTitle className="font-heading text-xl font-bold">
            Histórico de Manutenções
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {maintenances.length > 0 ? (
            <div className="divide-y divide-slate-100">
              {maintenances.map((maintenance) => (
                <div
                  key={maintenance.id}
                  className="flex items-center justify-between p-4 hover:bg-slate-50 cursor-pointer transition-colors"
                  onClick={() => navigate(`/maintenances/${maintenance.id}`)}
                  data-testid={`maintenance-history-item-${maintenance.id}`}
                >
                  <div className="flex items-center gap-4">
                    <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                      maintenance.maintenance_type === "preventiva" 
                        ? "bg-green-50" 
                        : "bg-orange-50"
                    }`}>
                      {maintenance.maintenance_type === "preventiva" ? (
                        <Shield className="text-green-600" size={20} />
                      ) : (
                        <AlertTriangle className="text-[#E31A1A]" size={20} />
                      )}
                    </div>
                    <div>
                      <p className="font-semibold text-slate-900">
                        {maintenance.part_name}
                      </p>
                      <p className="text-sm text-slate-500 capitalize">
                        Manutenção {maintenance.maintenance_type}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-bold text-slate-900">
                      {formatCurrency(maintenance.part_value)}
                    </p>
                    <p className="text-sm text-slate-500 flex items-center justify-end gap-1">
                      <Calendar size={14} />
                      {formatDate(maintenance.replacement_date)}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-state py-12">
              <Wrench className="text-slate-300 mb-4" size={48} />
              <p className="text-slate-500">Nenhuma manutenção registrada para esta máquina</p>
              <Button
                className="mt-4 bg-[#E31A1A] hover:bg-[#E31A1A]"
                onClick={() => navigate(`/maintenances/new?machine=${machine.id}`)}
              >
                <Plus size={18} className="mr-2" />
                Registrar Manutenção
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
