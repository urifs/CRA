import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { API } from "@/App";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { 
  Bell, 
  Truck,
  AlertTriangle,
  Droplet,
  Clock,
  ArrowRight,
  CheckCircle
} from "lucide-react";

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    fetchNotifications();
  }, []);

  const fetchNotifications = async () => {
    try {
      const response = await axios.get(`${API}/notifications`);
      setNotifications(response.data);
    } catch (error) {
      toast.error("Erro ao carregar notificações");
    } finally {
      setLoading(false);
    }
  };

  const getIcon = (type) => {
    if (type.includes("urgent")) {
      return <AlertTriangle className="text-red-500" size={24} />;
    }
    return <Droplet className="text-orange-500" size={24} />;
  };

  const getCardClass = (type) => {
    if (type.includes("urgent")) {
      return "border-red-300 bg-red-50";
    }
    return "border-orange-200 bg-orange-50";
  };

  const urgentCount = notifications.filter(n => n.notification_type.includes("urgent")).length;
  const warningCount = notifications.filter(n => !n.notification_type.includes("urgent")).length;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="spinner w-12 h-12"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in" data-testid="notifications-page">
      {/* Page header */}
      <div className="page-header">
        <div>
          <h1 className="page-title font-heading">Notificações</h1>
          <p className="text-slate-500 mt-1">Alertas de troca de óleo e manutenções</p>
        </div>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="stat-card">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-bold uppercase tracking-wider text-slate-500">
                  Total de Alertas
                </p>
                <p className="text-4xl font-black text-slate-900 mt-2 font-heading">
                  {notifications.length}
                </p>
              </div>
              <div className="w-14 h-14 bg-slate-100 rounded-xl flex items-center justify-center">
                <Bell className="text-slate-600" size={28} />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="stat-card">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-bold uppercase tracking-wider text-slate-500">
                  Urgentes
                </p>
                <p className="text-4xl font-black text-red-600 mt-2 font-heading">
                  {urgentCount}
                </p>
              </div>
              <div className="w-14 h-14 bg-red-50 rounded-xl flex items-center justify-center">
                <AlertTriangle className="text-red-600" size={28} />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="stat-card">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-bold uppercase tracking-wider text-slate-500">
                  Avisos
                </p>
                <p className="text-4xl font-black text-orange-500 mt-2 font-heading">
                  {warningCount}
                </p>
              </div>
              <div className="w-14 h-14 bg-orange-50 rounded-xl flex items-center justify-center">
                <Clock className="text-orange-500" size={28} />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Notifications List */}
      {notifications.length > 0 ? (
        <div className="space-y-4">
          {notifications.map((notification) => (
            <Card 
              key={notification.id}
              className={getCardClass(notification.notification_type)}
              data-testid={`notification-${notification.id}`}
            >
              <CardContent className="py-4">
                <div className="flex items-start gap-4">
                  <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${
                    notification.notification_type.includes("urgent") ? "bg-red-100" : "bg-orange-100"
                  }`}>
                    {getIcon(notification.notification_type)}
                  </div>
                  
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`text-xs font-bold uppercase tracking-wider px-2 py-0.5 rounded ${
                        notification.notification_type.includes("urgent") 
                          ? "bg-red-200 text-red-800" 
                          : "bg-orange-200 text-orange-800"
                      }`}>
                        {notification.notification_type.includes("urgent") ? "URGENTE" : "AVISO"}
                      </span>
                      <span className="text-sm text-slate-500">
                        {notification.notification_type.includes("time") ? "Tempo" : "Horas de Uso"}
                      </span>
                    </div>
                    
                    <div className="flex items-center gap-2 mb-2">
                      <Truck className="text-slate-400" size={16} />
                      <span className="font-bold text-slate-900">{notification.machine_name}</span>
                      <span className="font-mono text-sm text-slate-500">({notification.machine_plate})</span>
                    </div>
                    
                    <p className="text-slate-700">{notification.message}</p>
                    
                    <div className="flex items-center gap-4 mt-3 text-sm text-slate-500">
                      {notification.hours_remaining !== null && (
                        <span className="flex items-center gap-1">
                          <Clock size={14} />
                          {notification.hours_remaining.toFixed(0)}h restantes
                        </span>
                      )}
                      {notification.days_remaining !== null && (
                        <span className="flex items-center gap-1">
                          <Clock size={14} />
                          {notification.days_remaining} dias restantes
                        </span>
                      )}
                    </div>
                  </div>
                  
                  <Button
                    variant="outline"
                    size="sm"
                    className="shrink-0"
                    onClick={() => navigate(`/machines/${notification.machine_id}`)}
                  >
                    Ver Máquina
                    <ArrowRight size={14} className="ml-1" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <Card>
          <CardContent className="py-16">
            <div className="empty-state">
              <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <CheckCircle className="text-green-600" size={40} />
              </div>
              <p className="text-lg font-medium text-slate-900">Tudo em dia!</p>
              <p className="text-slate-500 mt-1">
                Não há alertas de troca de óleo no momento
              </p>
              <Button
                variant="outline"
                className="mt-4"
                onClick={() => navigate("/usage")}
              >
                Ver Tempo de Uso
                <ArrowRight size={16} className="ml-2" />
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Info Card */}
      <Card className="bg-slate-50 border-slate-200">
        <CardContent className="py-6">
          <div className="flex items-start gap-4">
            <div className="w-10 h-10 bg-slate-200 rounded-lg flex items-center justify-center flex-shrink-0">
              <Droplet className="text-slate-600" size={20} />
            </div>
            <div>
              <h3 className="font-bold text-slate-900">Sobre as Notificações</h3>
              <p className="text-sm text-slate-600 mt-1">
                O sistema alerta automaticamente quando:
              </p>
              <ul className="text-sm text-slate-600 mt-2 space-y-1 list-disc list-inside">
                <li>Restam <strong>50 horas</strong> ou menos para atingir 500h de uso</li>
                <li>Faltam <strong>2 meses</strong> ou menos para completar 1 ano desde a última troca</li>
                <li>O limite de 500h ou 1 ano foi <strong>atingido ou ultrapassado</strong></li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
