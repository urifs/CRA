import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { API } from "@/App";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { History, Undo2, ChevronRight, RefreshCw, CheckCircle2, AlertTriangle } from "lucide-react";
import { toast } from "sonner";
import { formatDateTimeBR } from "@/utils/dateFormat";

/**
 * Painel lateral de Histórico do Sistema Financeiro (módulo "Administrativo").
 * Lista as últimas ações do usuário logado e permite desfazer ações reversíveis
 * (atualmente: exclusão e edição de contas a pagar/receber).
 */
export default function FinanceiroHistoryPanel({ open, onClose }) {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [reverting, setReverting] = useState(null);

  const fetchLogs = useCallback(async () => {
    setLoading(true);
    try {
      const r = await axios.get(`${API}/audit-logs/my-history`, {
        params: { module: "Administrativo", limit: 80 },
      });
      setLogs(r.data || []);
    } catch (err) {
      console.error(err);
      toast.error("Erro ao carregar histórico");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (open) fetchLogs();
  }, [open, fetchLogs]);

  const handleRollback = async (log) => {
    if (!log.reversible || log.rolled_back) return;
    if (!window.confirm(`Desfazer esta ação?\n\n${log.action}\n${log.details || ""}`)) return;
    setReverting(log.id);
    try {
      const r = await axios.post(`${API}/audit-logs/${log.id}/rollback`);
      toast.success(r.data?.message || "Ação desfeita");
      fetchLogs();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Não foi possível desfazer");
    } finally {
      setReverting(null);
    }
  };

  const getIconForAction = (action) => {
    const a = (action || "").toLowerCase();
    if (a.includes("excluiu")) return <AlertTriangle size={14} className="text-red-500" />;
    if (a.includes("editou")) return <RefreshCw size={14} className="text-amber-500" />;
    if (a.includes("criou")) return <CheckCircle2 size={14} className="text-emerald-500" />;
    return <ChevronRight size={14} className="text-gray-400" />;
  };

  return (
    <Sheet open={open} onOpenChange={onClose}>
      <SheetContent side="right" className="w-full sm:w-[480px] flex flex-col p-0" data-testid="financeiro-history-panel">
        <SheetHeader className="px-5 py-4 border-b">
          <SheetTitle className="flex items-center gap-2">
            <History size={18} className="text-red-600" />
            Histórico de Ações
          </SheetTitle>
          <p className="text-xs text-gray-500">
            Suas últimas ações no Financeiro. Use o botão "Desfazer" para reverter exclusões e edições.
          </p>
        </SheetHeader>

        <div className="px-5 py-3 border-b flex items-center justify-between">
          <span className="text-xs text-gray-500">{logs.length} registro(s)</span>
          <Button size="sm" variant="outline" onClick={fetchLogs} disabled={loading} data-testid="btn-refresh-history">
            <RefreshCw size={13} className={`mr-1 ${loading ? "animate-spin" : ""}`} />
            Atualizar
          </Button>
        </div>

        <div className="flex-1 overflow-y-auto px-3 py-2 space-y-2">
          {loading && logs.length === 0 && (
            <p className="text-sm text-center text-gray-400 py-8">Carregando...</p>
          )}
          {!loading && logs.length === 0 && (
            <p className="text-sm text-center text-gray-400 py-8">Nenhuma ação registrada ainda.</p>
          )}
          {logs.map((log) => (
            <div
              key={log.id}
              className={`rounded-lg border px-3 py-2 ${
                log.rolled_back
                  ? "bg-gray-50 border-gray-200 opacity-70"
                  : "bg-white border-gray-200 hover:border-red-200"
              }`}
              data-testid={`history-item-${log.id}`}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5 mb-0.5">
                    {getIconForAction(log.action)}
                    <span className="text-sm font-medium text-gray-900 truncate">
                      {log.action}
                    </span>
                    {log.rolled_back && (
                      <span className="text-[10px] font-medium text-gray-500 bg-gray-200 px-1.5 py-0.5 rounded">
                        DESFEITA
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-gray-600 truncate" title={log.entity_name}>
                    {log.entity_name || "—"}
                  </p>
                  {log.details && (
                    <p className="text-[11px] text-gray-400 mt-0.5 line-clamp-2">
                      {log.details}
                    </p>
                  )}
                  <p className="text-[10px] text-gray-400 mt-1">
                    {formatDateTimeBR(log.created_at)}
                  </p>
                </div>
                {log.reversible && !log.rolled_back && (
                  <Button
                    size="sm"
                    variant="outline"
                    className="text-xs text-blue-600 border-blue-200 hover:bg-blue-50 shrink-0"
                    disabled={reverting === log.id}
                    onClick={() => handleRollback(log)}
                    data-testid={`btn-undo-${log.id}`}
                  >
                    <Undo2 size={12} className="mr-1" />
                    {reverting === log.id ? "Desfazendo..." : "Desfazer"}
                  </Button>
                )}
              </div>
            </div>
          ))}
        </div>
      </SheetContent>
    </Sheet>
  );
}
