import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { API } from "@/App";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { 
  Truck, 
  Wrench, 
  Shield, 
  AlertTriangle, 
  Plus,
  ArrowRight,
  Calendar,
  Package
} from "lucide-react";

export default function DashboardPage() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    fetchDashboard();
  }, []);

  const fetchDashboard = async () => {
    try {
      const response = await axios.get(`${API}/dashboard`);
      setStats(response.data);
    } catch (error) {
      toast.error("Erro ao carregar dashboard");
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

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="spinner w-12 h-12"></div>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-fade-in" data-testid="dashboard-page">
      {/* Page header */}
      <div className="page-header">
        <div>
          <h1 className="page-title font-heading">Dashboard</h1>
          <p className="text-gray-500 mt-1">Visão geral do sistema de manutenção</p>
        </div>
        <Button
          className="bg-[#E31A1A] hover:bg-[#E31A1A] text-white font-bold"
          onClick={() => navigate("/maintenances/new")}
          data-testid="dashboard-new-maintenance-btn"
        >
          <Plus size={18} className="mr-2" />
          Nova Manutenção
        </Button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Machines */}
        <Card className="stat-card group" data-testid="stat-total-machines">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-bold uppercase tracking-wider text-gray-500">
                  Total de Máquinas
                </p>
                <p className="text-4xl font-black text-black mt-2 font-heading">
                  {stats?.total_machines || 0}
                </p>
              </div>
              <div className="w-14 h-14 bg-gray-100 rounded-xl flex items-center justify-center group-hover:bg-gray-200 transition-colors">
                <Truck className="text-gray-600" size={28} />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Total Maintenances */}
        <Card className="stat-card group" data-testid="stat-total-maintenances">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-bold uppercase tracking-wider text-gray-500">
                  Manutenções
                </p>
                <p className="text-4xl font-black text-black mt-2 font-heading">
                  {stats?.total_maintenances || 0}
                </p>
              </div>
              <div className="w-14 h-14 bg-gray-100 rounded-xl flex items-center justify-center group-hover:bg-gray-200 transition-colors">
                <Wrench className="text-gray-600" size={28} />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Preventive */}
        <Card className="stat-card group" data-testid="stat-preventive">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-bold uppercase tracking-wider text-gray-500">
                  Preventivas
                </p>
                <p className="text-4xl font-black text-green-600 mt-2 font-heading">
                  {stats?.preventive_count || 0}
                </p>
              </div>
              <div className="w-14 h-14 bg-green-50 rounded-xl flex items-center justify-center group-hover:bg-green-100 transition-colors">
                <Shield className="text-green-600" size={28} />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Corrective */}
        <Card className="stat-card group" data-testid="stat-corrective">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-bold uppercase tracking-wider text-gray-500">
                  Corretivas
                </p>
                <p className="text-4xl font-black text-[#E31A1A] mt-2 font-heading">
                  {stats?.corrective_count || 0}
                </p>
              </div>
              <div className="w-14 h-14 bg-orange-50 rounded-xl flex items-center justify-center group-hover:bg-orange-100 transition-colors">
                <AlertTriangle className="text-[#E31A1A]" size={28} />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Low Stock Alert */}
      {stats?.low_stock_count > 0 && (
        <Card className="bg-orange-50 border-orange-200" data-testid="low-stock-alert">
          <CardContent className="py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center">
                  <Package className="text-[#E31A1A]" size={20} />
                </div>
                <div>
                  <p className="font-bold text-orange-800">Alerta de Estoque</p>
                  <p className="text-sm text-[#E31A1A]">
                    {stats.low_stock_count} {stats.low_stock_count === 1 ? "item está" : "itens estão"} abaixo do estoque mínimo
                  </p>
                </div>
              </div>
              <Button
                className="bg-[#E31A1A] hover:bg-[#E31A1A]"
                onClick={() => navigate("/gerenciamento/stock")}
              >
                Ver Estoque
                <ArrowRight size={16} className="ml-2" />
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Recent Maintenances */}
      <Card data-testid="recent-maintenances-card">
        <CardHeader className="border-b border-gray-200">
          <div className="flex items-center justify-between">
            <CardTitle className="font-heading text-xl font-bold">
              Manutenções Recentes
            </CardTitle>
            <Button
              variant="ghost"
              className="text-gray-600 hover:text-black"
              onClick={() => navigate("/gerenciamento/maintenances")}
            >
              Ver Todas
              <ArrowRight size={16} className="ml-2" />
            </Button>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {stats?.recent_maintenances?.length > 0 ? (
            <div className="divide-y divide-slate-100">
              {stats.recent_maintenances.map((maintenance) => (
                <div
                  key={maintenance.id}
                  className="flex items-center justify-between p-4 hover:bg-white cursor-pointer transition-colors"
                  onClick={() => navigate(`/maintenances/${maintenance.id}`)}
                  data-testid={`maintenance-item-${maintenance.id}`}
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
                      <p className="text-sm text-gray-500">
                        <span className="font-mono">{maintenance.machine_plate}</span>
                        {" - "}
                        {maintenance.machine_name}
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
              <p className="text-gray-500">Nenhuma manutenção registrada</p>
              <Button
                className="mt-4 bg-[#E31A1A] hover:bg-[#E31A1A]"
                onClick={() => navigate("/maintenances/new")}
              >
                <Plus size={18} className="mr-2" />
                Registrar Primeira Manutenção
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card
          className="stat-card cursor-pointer group"
          onClick={() => navigate("/gerenciamento/machines")}
          data-testid="quick-action-machines"
        >
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center group-hover:bg-orange-50 transition-colors">
                <Truck className="text-gray-600 group-hover:text-[#E31A1A] transition-colors" size={24} />
              </div>
              <div>
                <p className="font-bold text-black">Gerenciar Máquinas</p>
                <p className="text-sm text-gray-500">Cadastrar e editar máquinas</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card
          className="stat-card cursor-pointer group"
          onClick={() => navigate("/maintenances/new")}
          data-testid="quick-action-new-maintenance"
        >
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center group-hover:bg-orange-50 transition-colors">
                <Plus className="text-gray-600 group-hover:text-[#E31A1A] transition-colors" size={24} />
              </div>
              <div>
                <p className="font-bold text-black">Nova Manutenção</p>
                <p className="text-sm text-gray-500">Registrar ficha de manutenção</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card
          className="stat-card cursor-pointer group"
          onClick={() => navigate("/gerenciamento/stock")}
          data-testid="quick-action-stock"
        >
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center group-hover:bg-orange-50 transition-colors">
                <Package className="text-gray-600 group-hover:text-[#E31A1A] transition-colors" size={24} />
              </div>
              <div>
                <p className="font-bold text-black">Estoque</p>
                <p className="text-sm text-gray-500">Controle de peças</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card
          className="stat-card cursor-pointer group"
          onClick={() => navigate("/gerenciamento/categories")}
          data-testid="quick-action-categories"
        >
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center group-hover:bg-orange-50 transition-colors">
                <Wrench className="text-gray-600 group-hover:text-[#E31A1A] transition-colors" size={24} />
              </div>
              <div>
                <p className="font-bold text-black">Categorias</p>
                <p className="text-sm text-gray-500">Tipos de máquinas</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
