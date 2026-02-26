import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import { API, useAuth } from "@/App";
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
  DollarSign,
  Clock,
  Timer,
  Fuel,
  Droplets
} from "lucide-react";

export default function MachineDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { token } = useAuth();
  const [machine, setMachine] = useState(null);
  const [maintenances, setMaintenances] = useState([]);
  const [horimetros, setHorimetros] = useState([]);
  const [combustiveis, setCombustiveis] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, [id]);

  const fetchData = async () => {
    try {
      const config = { headers: { Authorization: `Bearer ${token}` } };
      const [machineRes, maintenancesRes, horimetroRes, combustivelRes] = await Promise.all([
        axios.get(`${API}/machines/${id}`, config),
        axios.get(`${API}/maintenances?machine_id=${id}`, config),
        axios.get(`${API}/horimetro/machine/${id}`, config).catch(() => ({ data: [] })),
        axios.get(`${API}/combustivel/machine/${id}`, config).catch(() => ({ data: [] }))
      ]);
      setMachine(machineRes.data);
      setMaintenances(maintenancesRes.data);
      setHorimetros(horimetroRes.data || []);
      setCombustiveis(combustivelRes.data || []);
    } catch (error) {
      toast.error("Erro ao carregar dados da máquina");
      navigate("/gerenciamento/machines");
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
  const totalHorasTrabalhadas = horimetros.reduce((sum, h) => sum + (h.horas_trabalhadas || 0), 0);
  const totalLitrosConsumidos = combustiveis.reduce((sum, c) => sum + (c.litros_consumidos || 0), 0);

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
        onClick={() => navigate("/gerenciamento/machines")}
        className="text-gray-600 hover:text-black"
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
              <div className="w-16 h-16 bg-gray-100 rounded-xl flex items-center justify-center">
                <Truck className="text-gray-600" size={32} />
              </div>
              <div>
                <div className="flex items-center gap-3">
                  <h1 className="text-2xl font-bold font-heading text-black">
                    {machine.name}
                  </h1>
                  {getStatusBadge(machine.status)}
                </div>
                <p className="font-mono text-lg text-gray-500 mt-1">{machine.plate}</p>
              </div>
            </div>
            <Button
              className="bg-[#E31A1A] hover:bg-[#E31A1A]"
              onClick={() => navigate(`/gerenciamento/maintenances/new?machine=${machine.id}`)}
              data-testid="new-maintenance-for-machine-btn"
            >
              <Plus size={18} className="mr-2" />
              Nova Manutenção
            </Button>
          </div>

          {/* Machine Details */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6 pt-6 border-t border-gray-200">
            <div>
              <p className="text-xs font-bold uppercase tracking-wider text-gray-500">Categoria</p>
              <p className="font-medium text-black mt-1">{machine.category_name || "-"}</p>
            </div>
            <div>
              <p className="text-xs font-bold uppercase tracking-wider text-gray-500">Marca</p>
              <p className="font-medium text-black mt-1">{machine.brand || "-"}</p>
            </div>
            <div>
              <p className="text-xs font-bold uppercase tracking-wider text-gray-500">Modelo</p>
              <p className="font-medium text-black mt-1">{machine.model || "-"}</p>
            </div>
            <div>
              <p className="text-xs font-bold uppercase tracking-wider text-gray-500">Ano</p>
              <p className="font-mono text-black mt-1">{machine.year || "-"}</p>
            </div>
          </div>

          {/* Chassi/Número de Série */}
          {machine.identificador_numero && (
            <div className="mt-4 pt-4 border-t border-gray-200">
              <div className="flex items-center gap-2">
                <p className="text-xs font-bold uppercase tracking-wider text-gray-500">
                  {machine.identificador_tipo === "chassi" ? "Chassi" : "Número de Série"}
                </p>
              </div>
              <p className="font-mono text-lg text-black mt-1 bg-gray-50 px-3 py-2 rounded-lg inline-block">
                {machine.identificador_numero}
              </p>
            </div>
          )}

          {machine.notes && (
            <div className="mt-4 pt-4 border-t border-gray-200">
              <p className="text-xs font-bold uppercase tracking-wider text-gray-500">Observações</p>
              <p className="text-gray-700 mt-1">{machine.notes}</p>
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
                <p className="text-xs font-bold uppercase tracking-wider text-gray-500">
                  Total de Manutenções
                </p>
                <p className="text-3xl font-black text-black mt-1 font-heading">
                  {maintenances.length}
                </p>
              </div>
              <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center">
                <Wrench className="text-gray-600" size={24} />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="stat-card">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-bold uppercase tracking-wider text-gray-500">
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
                <p className="text-xs font-bold uppercase tracking-wider text-gray-500">
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
                <p className="text-xs font-bold uppercase tracking-wider text-gray-500">
                  Total Gasto
                </p>
                <p className="text-2xl font-black text-black mt-1 font-heading">
                  {formatCurrency(totalSpent)}
                </p>
              </div>
              <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center">
                <DollarSign className="text-gray-600" size={24} />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Horímetro Section */}
      <Card>
        <CardHeader className="border-b border-gray-200">
          <div className="flex items-center justify-between">
            <CardTitle className="font-heading text-xl font-bold flex items-center gap-2">
              <Clock className="text-yellow-500" size={20} />
              Registros de Horímetro
            </CardTitle>
            <div className="flex items-center gap-4">
              <div className="text-right">
                <p className="text-xs text-gray-500">Total trabalhado</p>
                <p className="text-lg font-bold text-yellow-600">{totalHorasTrabalhadas.toFixed(1)}h</p>
              </div>
              <Button
                size="sm"
                className="bg-yellow-500 hover:bg-yellow-600 text-black"
                onClick={() => navigate("/gerenciamento/horimetro")}
              >
                <Plus size={16} className="mr-1" />
                Novo Registro
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {horimetros.length > 0 ? (
            <div className="divide-y divide-slate-100">
              {horimetros.slice(0, 10).map((horimetro) => (
                <div
                  key={horimetro.id}
                  className="flex items-center justify-between p-4 hover:bg-gray-50 transition-colors"
                  data-testid={`horimetro-item-${horimetro.id}`}
                >
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 rounded-lg flex items-center justify-center bg-yellow-50">
                      <Timer className="text-yellow-600" size={20} />
                    </div>
                    <div>
                      <p className="font-semibold text-black">
                        {horimetro.horas_trabalhadas?.toFixed(1)}h trabalhadas
                      </p>
                      <p className="text-sm text-gray-500">
                        {horimetro.operador ? `Operador: ${horimetro.operador}` : "Sem operador registrado"}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-mono text-sm text-gray-700">
                      {horimetro.hora_inicial}h → {horimetro.hora_final}h
                    </p>
                    <p className="text-sm text-gray-500 flex items-center justify-end gap-1">
                      <Calendar size={14} />
                      {new Date(horimetro.data + "T00:00:00").toLocaleDateString("pt-BR")}
                    </p>
                  </div>
                </div>
              ))}
              {horimetros.length > 10 && (
                <div className="p-4 text-center">
                  <Button
                    variant="link"
                    onClick={() => navigate("/gerenciamento/horimetro")}
                    className="text-yellow-600"
                  >
                    Ver todos os {horimetros.length} registros
                  </Button>
                </div>
              )}
            </div>
          ) : (
            <div className="empty-state py-12">
              <Clock className="text-gray-300 mb-4" size={48} />
              <p className="text-gray-500">Nenhum registro de horímetro para esta máquina</p>
              <Button
                className="mt-4 bg-yellow-500 hover:bg-yellow-600 text-black"
                onClick={() => navigate("/gerenciamento/horimetro")}
              >
                <Plus size={18} className="mr-2" />
                Registrar Horas
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Combustível Section */}
      <Card>
        <CardHeader className="border-b border-gray-200">
          <div className="flex items-center justify-between">
            <CardTitle className="font-heading text-xl font-bold flex items-center gap-2">
              <Fuel className="text-green-500" size={20} />
              Registros de Combustível
            </CardTitle>
            <div className="flex items-center gap-4">
              <div className="text-right">
                <p className="text-xs text-gray-500">Total consumido</p>
                <p className="text-lg font-bold text-green-600">{totalLitrosConsumidos.toFixed(1)}L</p>
              </div>
              <Button
                size="sm"
                className="bg-green-500 hover:bg-green-600 text-white"
                onClick={() => navigate("/gerenciamento/combustivel")}
              >
                <Plus size={16} className="mr-1" />
                Novo Registro
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {combustiveis.length > 0 ? (
            <div className="divide-y divide-slate-100">
              {combustiveis.slice(0, 10).map((combustivel) => (
                <div
                  key={combustivel.id}
                  className="flex items-center justify-between p-4 hover:bg-gray-50 transition-colors"
                  data-testid={`combustivel-item-${combustivel.id}`}
                >
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 rounded-lg flex items-center justify-center bg-green-50">
                      <Droplets className="text-green-600" size={20} />
                    </div>
                    <div>
                      <p className="font-semibold text-black">
                        {combustivel.litros_consumidos?.toFixed(1)}L abastecidos
                      </p>
                      <p className="text-sm text-gray-500">
                        {combustivel.operador ? `Operador: ${combustivel.operador}` : "Sem operador"} • {combustivel.tipo_medicao === "litros_hora" ? "L/hora" : "L/km"}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-mono text-sm text-gray-700">
                      {combustivel.litros_inicial}L → {combustivel.litros_final}L
                    </p>
                    <p className="text-sm text-gray-500 flex items-center justify-end gap-1">
                      <Calendar size={14} />
                      {new Date(combustivel.data + "T00:00:00").toLocaleDateString("pt-BR")}
                    </p>
                  </div>
                </div>
              ))}
              {combustiveis.length > 10 && (
                <div className="p-4 text-center">
                  <Button
                    variant="link"
                    onClick={() => navigate("/gerenciamento/combustivel")}
                    className="text-green-600"
                  >
                    Ver todos os {combustiveis.length} registros
                  </Button>
                </div>
              )}
            </div>
          ) : (
            <div className="empty-state py-12">
              <Fuel className="text-gray-300 mb-4" size={48} />
              <p className="text-gray-500">Nenhum registro de combustível para esta máquina</p>
              <Button
                className="mt-4 bg-green-500 hover:bg-green-600 text-white"
                onClick={() => navigate("/gerenciamento/combustivel")}
              >
                <Plus size={18} className="mr-2" />
                Registrar Abastecimento
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Maintenance History */}
      <Card>
        <CardHeader className="border-b border-gray-200">
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
                  className="flex items-center justify-between p-4 hover:bg-white cursor-pointer transition-colors"
                  onClick={() => navigate(`/gerenciamento/maintenances/${maintenance.id}`)}
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
                      <p className="font-semibold text-black">
                        {maintenance.part_name}
                      </p>
                      <p className="text-sm text-gray-500 capitalize">
                        Manutenção {maintenance.maintenance_type}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-bold text-black">
                      {formatCurrency(maintenance.part_value)}
                    </p>
                    <p className="text-sm text-gray-500 flex items-center justify-end gap-1">
                      <Calendar size={14} />
                      {formatDate(maintenance.replacement_date)}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-state py-12">
              <Wrench className="text-gray-300 mb-4" size={48} />
              <p className="text-gray-500">Nenhuma manutenção registrada para esta máquina</p>
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
