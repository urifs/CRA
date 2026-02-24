import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { API } from "@/App";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";
import { 
  DollarSign, 
  Truck,
  Shield,
  AlertTriangle,
  TrendingUp,
  Calendar,
  BarChart3,
  ArrowRight
} from "lucide-react";

export default function BalancePage() {
  const [balance, setBalance] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("overview");
  const navigate = useNavigate();

  useEffect(() => {
    fetchBalance();
  }, []);

  const fetchBalance = async () => {
    try {
      const response = await axios.get(`${API}/balance`);
      setBalance(response.data);
    } catch (error) {
      toast.error("Erro ao carregar dados do balanço");
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
    if (!dateString) return "-";
    return new Date(dateString).toLocaleDateString("pt-BR");
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="spinner w-12 h-12"></div>
      </div>
    );
  }

  const preventivePercentage = balance?.total_maintenances > 0 
    ? (balance.preventive_count / balance.total_maintenances) * 100 
    : 0;

  return (
    <div className="space-y-6 animate-fade-in" data-testid="balance-page">
      {/* Page header */}
      <div className="page-header">
        <div>
          <h1 className="page-title font-heading">Balanço Financeiro</h1>
          <p className="text-slate-500 mt-1">Análise de gastos com manutenções</p>
        </div>
      </div>

      {/* Main Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="bg-slate-900 text-white">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-bold uppercase tracking-wider text-slate-400">
                  Total Investido
                </p>
                <p className="text-3xl font-black mt-2 font-heading">
                  {formatCurrency(balance?.total_spent || 0)}
                </p>
              </div>
              <div className="w-14 h-14 bg-[#E31A1A] rounded-xl flex items-center justify-center">
                <DollarSign className="text-white" size={28} />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="stat-card">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-bold uppercase tracking-wider text-slate-500">
                  Total Manutenções
                </p>
                <p className="text-3xl font-black text-slate-900 mt-2 font-heading">
                  {balance?.total_maintenances || 0}
                </p>
              </div>
              <div className="w-14 h-14 bg-slate-100 rounded-xl flex items-center justify-center">
                <BarChart3 className="text-slate-600" size={28} />
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
                <p className="text-3xl font-black text-green-600 mt-2 font-heading">
                  {formatCurrency(balance?.preventive_total || 0)}
                </p>
                <p className="text-xs text-slate-500 mt-1">
                  {balance?.preventive_count || 0} manutenções
                </p>
              </div>
              <div className="w-14 h-14 bg-green-50 rounded-xl flex items-center justify-center">
                <Shield className="text-green-600" size={28} />
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
                <p className="text-3xl font-black text-[#E31A1A] mt-2 font-heading">
                  {formatCurrency(balance?.corrective_total || 0)}
                </p>
                <p className="text-xs text-slate-500 mt-1">
                  {balance?.corrective_count || 0} manutenções
                </p>
              </div>
              <div className="w-14 h-14 bg-orange-50 rounded-xl flex items-center justify-center">
                <AlertTriangle className="text-[#E31A1A]" size={28} />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Preventive vs Corrective Ratio */}
      <Card>
        <CardContent className="py-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-bold text-slate-900">Proporção Preventiva vs Corretiva</h3>
              <p className="text-sm text-slate-500">
                {preventivePercentage.toFixed(1)}% das manutenções são preventivas
              </p>
            </div>
            <div className="text-right">
              <p className="text-sm text-slate-500">Média por manutenção</p>
              <p className="font-bold text-slate-900">
                {formatCurrency(balance?.average_per_maintenance || 0)}
              </p>
            </div>
          </div>
          <div className="flex gap-2 items-center">
            <div className="flex-1">
              <div className="h-4 rounded-full overflow-hidden bg-orange-100 flex">
                <div 
                  className="h-full bg-green-500 transition-all duration-500"
                  style={{ width: `${preventivePercentage}%` }}
                />
                <div 
                  className="h-full bg-[#E31A1A] transition-all duration-500"
                  style={{ width: `${100 - preventivePercentage}%` }}
                />
              </div>
            </div>
          </div>
          <div className="flex justify-between mt-2 text-sm">
            <span className="text-green-600 font-medium flex items-center gap-1">
              <Shield size={14} />
              Preventiva ({balance?.preventive_count || 0})
            </span>
            <span className="text-[#E31A1A] font-medium flex items-center gap-1">
              <AlertTriangle size={14} />
              Corretiva ({balance?.corrective_count || 0})
            </span>
          </div>
        </CardContent>
      </Card>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="machines" data-testid="tab-machines">
            <Truck size={16} className="mr-2" />
            Por Máquina
          </TabsTrigger>
          <TabsTrigger value="monthly" data-testid="tab-monthly">
            <Calendar size={16} className="mr-2" />
            Por Mês
          </TabsTrigger>
        </TabsList>

        {/* By Machine Tab */}
        <TabsContent value="machines" className="space-y-4">
          {balance?.expenses_by_machine?.length > 0 ? (
            <div className="space-y-3">
              {balance.expenses_by_machine.map((machine, index) => (
                <Card 
                  key={machine.machine_id}
                  className="hover:shadow-md transition-shadow cursor-pointer"
                  onClick={() => navigate(`/machines/${machine.machine_id}`)}
                  data-testid={`machine-expense-${machine.machine_id}`}
                >
                  <CardContent className="py-4">
                    <div className="flex items-center gap-4">
                      <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                        index === 0 ? "bg-orange-100" : "bg-slate-100"
                      }`}>
                        <span className={`font-bold ${index === 0 ? "text-[#E31A1A]" : "text-slate-600"}`}>
                          #{index + 1}
                        </span>
                      </div>
                      
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <h3 className="font-bold text-slate-900">{machine.machine_name}</h3>
                          <span className="font-mono text-sm text-slate-500">({machine.machine_plate})</span>
                          {machine.category_name && (
                            <span className="text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded">
                              {machine.category_name}
                            </span>
                          )}
                        </div>
                        <div className="flex items-center gap-4 mt-1 text-sm text-slate-500">
                          <span>{machine.total_maintenances} manutenções</span>
                          <span>•</span>
                          <span>Última: {formatDate(machine.last_maintenance_date)}</span>
                        </div>
                      </div>
                      
                      <div className="text-right">
                        <p className="text-xl font-black text-slate-900">
                          {formatCurrency(machine.total_spent)}
                        </p>
                        <div className="flex gap-3 mt-1 text-xs">
                          <span className="text-green-600">
                            <Shield size={12} className="inline mr-1" />
                            {formatCurrency(machine.preventive_spent)}
                          </span>
                          <span className="text-[#E31A1A]">
                            <AlertTriangle size={12} className="inline mr-1" />
                            {formatCurrency(machine.corrective_spent)}
                          </span>
                        </div>
                      </div>
                      
                      <ArrowRight className="text-slate-400" size={20} />
                    </div>
                    
                    {/* Progress bar showing preventive vs corrective */}
                    {machine.total_spent > 0 && (
                      <div className="mt-3">
                        <div className="h-1.5 rounded-full overflow-hidden bg-slate-100 flex">
                          <div 
                            className="h-full bg-green-500"
                            style={{ width: `${(machine.preventive_spent / machine.total_spent) * 100}%` }}
                          />
                          <div 
                            className="h-full bg-[#E31A1A]"
                            style={{ width: `${(machine.corrective_spent / machine.total_spent) * 100}%` }}
                          />
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <div className="empty-state py-12">
              <Truck className="text-slate-300 mb-4" size={64} />
              <p className="text-lg font-medium text-slate-600">Nenhuma manutenção registrada</p>
              <p className="text-slate-400">Os gastos por máquina aparecerão aqui</p>
            </div>
          )}
        </TabsContent>

        {/* By Month Tab */}
        <TabsContent value="monthly">
          {balance?.expenses_by_month?.length > 0 ? (
            <Card>
              <CardContent className="p-0">
                <div className="overflow-x-auto">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Mês</th>
                        <th>Ano</th>
                        <th>Manutenções</th>
                        <th>Total Gasto</th>
                        <th>Média</th>
                      </tr>
                    </thead>
                    <tbody>
                      {balance.expenses_by_month.map((month, index) => (
                        <tr key={`${month.year}-${month.month}`} data-testid={`month-expense-${index}`}>
                          <td className="font-medium text-slate-900">{month.month}</td>
                          <td className="font-mono text-slate-500">{month.year}</td>
                          <td>
                            <span className="bg-slate-100 text-slate-700 px-2 py-1 rounded text-sm font-medium">
                              {month.maintenance_count}
                            </span>
                          </td>
                          <td className="font-bold text-slate-900">
                            {formatCurrency(month.total_spent)}
                          </td>
                          <td className="text-slate-600">
                            {formatCurrency(month.total_spent / month.maintenance_count)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          ) : (
            <div className="empty-state py-12">
              <Calendar className="text-slate-300 mb-4" size={64} />
              <p className="text-lg font-medium text-slate-600">Nenhuma manutenção registrada</p>
              <p className="text-slate-400">Os gastos mensais aparecerão aqui</p>
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* Tips Card */}
      <Card className="bg-slate-50 border-slate-200">
        <CardContent className="py-6">
          <div className="flex items-start gap-4">
            <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center flex-shrink-0">
              <TrendingUp className="text-green-600" size={20} />
            </div>
            <div>
              <h3 className="font-bold text-slate-900">Dica de Economia</h3>
              <p className="text-sm text-slate-600 mt-1">
                Manutenções preventivas costumam ser mais baratas e evitam problemas maiores. 
                {preventivePercentage < 50 ? (
                  <span className="text-[#E31A1A] font-medium">
                    {" "}Considere aumentar a frequência de manutenções preventivas para reduzir custos a longo prazo.
                  </span>
                ) : (
                  <span className="text-green-600 font-medium">
                    {" "}Você está no caminho certo com {preventivePercentage.toFixed(0)}% de manutenções preventivas!
                  </span>
                )}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
