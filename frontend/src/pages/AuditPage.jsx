import { useState, useEffect } from "react";
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
  ClipboardList, 
  Search,
  User,
  Calendar,
  Plus,
  Pencil,
  Trash2,
  Filter
} from "lucide-react";

export default function AuditPage() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterType, setFilterType] = useState("all");
  const [filterAction, setFilterAction] = useState("all");

  useEffect(() => {
    fetchLogs();
  }, []);

  const fetchLogs = async () => {
    try {
      const response = await axios.get(`${API}/audit-logs?limit=500`);
      setLogs(response.data);
    } catch (error) {
      toast.error("Erro ao carregar logs de auditoria");
    } finally {
      setLoading(false);
    }
  };

  const getActionIcon = (action) => {
    switch (action) {
      case "criar":
        return <Plus className="text-green-500" size={16} />;
      case "editar":
        return <Pencil className="text-[#D4A000]" size={16} />;
      case "excluir":
        return <Trash2 className="text-red-500" size={16} />;
      default:
        return <ClipboardList className="text-gray-500" size={16} />;
    }
  };

  const getActionBadge = (action) => {
    const badges = {
      criar: { class: "bg-green-100 text-green-700 border-green-200", label: "Criar" },
      editar: { class: "bg-blue-100 text-[#D4A000] border-blue-200", label: "Editar" },
      excluir: { class: "bg-red-100 text-red-700 border-red-200", label: "Excluir" }
    };
    const badge = badges[action] || { class: "bg-gray-100 text-gray-700", label: action };
    return (
      <span className={`px-2 py-0.5 text-xs font-bold rounded-full border ${badge.class}`}>
        {badge.label}
      </span>
    );
  };

  const getEntityTypeBadge = (type) => {
    const colors = {
      "máquina": "bg-blue-50 text-[#D4A000]",
      "manutenção": "bg-orange-50 text-[#E31A1A]",
      "categoria": "bg-purple-50 text-purple-700",
      "obra": "bg-yellow-50 text-yellow-700",
      "item de estoque": "bg-green-50 text-green-700",
      "categoria de estoque": "bg-teal-50 text-teal-700",
      "registro de uso": "bg-cyan-50 text-cyan-700"
    };
    const colorClass = colors[type] || "bg-white text-gray-700";
    return (
      <span className={`px-2 py-0.5 text-xs font-medium rounded ${colorClass}`}>
        {type}
      </span>
    );
  };

  const formatDate = (dateStr) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString("pt-BR", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit"
    });
  };

  // Get unique entity types for filter (filter out empty strings)
  const entityTypes = [...new Set(logs.map(l => l.entity_type))].filter(t => t && t.trim() !== "");

  const filteredLogs = logs.filter(log => {
    const matchesSearch = 
      (log.user_name || "").toLowerCase().includes(searchTerm.toLowerCase()) ||
      (log.entity_name || "").toLowerCase().includes(searchTerm.toLowerCase()) ||
      (log.entity_type || "").toLowerCase().includes(searchTerm.toLowerCase()) ||
      (log.details && log.details.toLowerCase().includes(searchTerm.toLowerCase()));
    
    const matchesType = filterType === "all" || log.entity_type === filterType;
    const matchesAction = filterAction === "all" || log.action === filterAction;
    
    return matchesSearch && matchesType && matchesAction;
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="spinner w-12 h-12"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in" data-testid="audit-page">
      {/* Page header */}
      <div className="page-header">
        <div>
          <h1 className="page-title font-heading">Auditoria</h1>
          <p className="text-gray-500 mt-1">Histórico de alterações realizadas pelos funcionários</p>
        </div>
        <div className="text-right">
          <p className="text-sm text-gray-500">{filteredLogs.length} registros</p>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
              <Input
                placeholder="Buscar por funcionário, item ou detalhes..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 h-11 bg-white border border-gray-300 rounded-md focus:border-[#E31A1A] focus:ring-2 focus:ring-[#E31A1A] focus:outline-none"
                data-testid="audit-search-input"
              />
            </div>
            <Button className="bg-[#E31A1A] hover:bg-[#c41616] text-white shrink-0">
              <Search size={16} className="mr-2" />
              Buscar
            </Button>
            <div className="flex gap-2">
              <Select value={filterType} onValueChange={setFilterType}>
                <SelectTrigger className="w-[180px]" data-testid="audit-type-filter">
                  <Filter size={16} className="mr-2" />
                  <SelectValue placeholder="Tipo" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todos os tipos</SelectItem>
                  {entityTypes.map(type => (
                    <SelectItem key={type} value={type}>{type}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Select value={filterAction} onValueChange={setFilterAction}>
                <SelectTrigger className="w-[150px]" data-testid="audit-action-filter">
                  <SelectValue placeholder="Ação" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todas as ações</SelectItem>
                  <SelectItem value="criar">Criar</SelectItem>
                  <SelectItem value="editar">Editar</SelectItem>
                  <SelectItem value="excluir">Excluir</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Audit Logs */}
      {filteredLogs.length > 0 ? (
        <Card>
          <CardContent className="p-0">
            <div className="divide-y divide-slate-100">
              {filteredLogs.map((log) => (
                <div
                  key={log.id}
                  className="p-4 hover:bg-white transition-colors"
                  data-testid={`audit-log-${log.id}`}
                >
                  <div className="flex items-start gap-4">
                    {/* Action Icon */}
                    <div className="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center flex-shrink-0">
                      {getActionIcon(log.action)}
                    </div>
                    
                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap mb-1">
                        <span className="font-bold text-black">{log.user_name}</span>
                        {getActionBadge(log.action)}
                        {getEntityTypeBadge(log.entity_type)}
                      </div>
                      
                      <p className="text-gray-700">
                        <span className="font-medium">{log.entity_name}</span>
                      </p>
                      
                      {log.details && (
                        <p className="text-sm text-gray-500 mt-1">{log.details}</p>
                      )}
                      
                      <div className="flex items-center gap-4 mt-2 text-xs text-gray-400">
                        <span className="flex items-center gap-1">
                          <User size={12} />
                          {log.user_email}
                        </span>
                        <span className="flex items-center gap-1">
                          <Calendar size={12} />
                          {formatDate(log.created_at)}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="empty-state">
          <ClipboardList className="text-gray-300 mb-4" size={64} />
          <p className="text-lg font-medium text-gray-600">Nenhum registro encontrado</p>
          <p className="text-gray-400">
            {searchTerm || filterType !== "all" || filterAction !== "all" 
              ? "Tente ajustar os filtros de busca" 
              : "Os logs de auditoria aparecerão aqui quando houver alterações no sistema"
            }
          </p>
        </div>
      )}
    </div>
  );
}
