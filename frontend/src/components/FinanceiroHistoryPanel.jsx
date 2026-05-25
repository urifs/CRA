import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { API } from "@/App";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { History, Undo2, RefreshCw, CheckCircle2, AlertTriangle, ChevronRight, User, Calendar, FileText, Tag } from "lucide-react";
import { toast } from "sonner";
import { formatDateTimeBR } from "@/utils/dateFormat";

/**
 * Painel lateral de Histórico do Sistema Financeiro.
 * - Lista as últimas ações do usuário em TODOS os módulos do ERP.
 * - Cada item é clicável → abre modal de detalhes.
 * - Botão "Desfazer" disponível para ações reversíveis (exclusão/edição
 *   de contas a pagar/receber, etc.).
 */
export default function FinanceiroHistoryPanel({ open, onClose }) {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [reverting, setReverting] = useState(null);
  const [selectedLog, setSelectedLog] = useState(null);

  const fetchLogs = useCallback(async () => {
    setLoading(true);
    try {
      const r = await axios.get(`${API}/audit-logs/my-history`, {
        params: { limit: 200 },
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
    if (!log.reversible || log.rolled_back) {
      toast.error("Esta ação não pode ser desfeita");
      return;
    }
    if (!window.confirm(`Desfazer esta ação?\n\n${log.action}\n${log.entity_name || ""}\n\n${log.details || ""}`)) return;
    setReverting(log.id);
    try {
      const r = await axios.post(`${API}/audit-logs/${log.id}/rollback`);
      toast.success(r.data?.message || "Ação desfeita");
      setSelectedLog(null);
      fetchLogs();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Não foi possível desfazer");
    } finally {
      setReverting(null);
    }
  };

  const getIconForAction = (action) => {
    const a = (action || "").toLowerCase();
    if (a.includes("excluiu") || a.startsWith("delete")) return <AlertTriangle size={14} className="text-red-500" />;
    if (a.includes("editou") || a.startsWith("update")) return <RefreshCw size={14} className="text-amber-500" />;
    if (a.includes("criou") || a.startsWith("create")) return <CheckCircle2 size={14} className="text-emerald-500" />;
    return <ChevronRight size={14} className="text-gray-400" />;
  };

  return (
    <>
      <Sheet open={open} onOpenChange={onClose}>
        <SheetContent side="right" className="w-full sm:w-[480px] flex flex-col p-0" data-testid="financeiro-history-panel">
          <SheetHeader className="px-5 py-4 border-b">
            <SheetTitle className="flex items-center gap-2">
              <History size={18} className="text-red-600" />
              Histórico de Ações
            </SheetTitle>
            <p className="text-xs text-gray-500">
              Clique em uma ação para ver detalhes e desfazê-la (quando aplicável).
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
              <button
                type="button"
                key={log.id}
                onClick={() => setSelectedLog(log)}
                className={`w-full text-left rounded-lg border px-3 py-2 transition-colors cursor-pointer ${
                  log.rolled_back
                    ? "bg-gray-50 border-gray-200 opacity-70 hover:bg-gray-100"
                    : "bg-white border-gray-200 hover:border-red-300 hover:bg-red-50/40"
                }`}
                data-testid={`history-item-${log.id}`}
              >
                <div className="flex items-start gap-2">
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
                      {log.reversible && !log.rolled_back && (
                        <span className="text-[10px] font-medium text-blue-600 bg-blue-50 px-1.5 py-0.5 rounded">
                          REVERSÍVEL
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-gray-600 truncate" title={log.entity_name}>
                      {log.entity_name || "—"}
                    </p>
                    <p className="text-[10px] text-gray-400 mt-1">
                      {formatDateTimeBR(log.created_at)}
                    </p>
                  </div>
                  <ChevronRight size={14} className="text-gray-300 flex-shrink-0 mt-1" />
                </div>
              </button>
            ))}
          </div>
        </SheetContent>
      </Sheet>

      {/* Modal de detalhes da ação */}
      <Dialog open={!!selectedLog} onOpenChange={(o) => !o && setSelectedLog(null)}>
        <DialogContent className="max-w-lg" data-testid="history-detail-modal">
          {selectedLog && (
            <>
              <DialogHeader>
                <DialogTitle className="flex items-center gap-2">
                  {getIconForAction(selectedLog.action)}
                  Detalhes da Ação
                </DialogTitle>
              </DialogHeader>

              <div className="space-y-3 py-2 text-sm">
                <div className="flex items-start gap-2">
                  <Tag size={14} className="text-gray-400 mt-0.5 flex-shrink-0" />
                  <div className="flex-1">
                    <p className="text-xs text-gray-500">Ação</p>
                    <p className="font-medium">{selectedLog.action}</p>
                  </div>
                </div>

                <div className="flex items-start gap-2">
                  <FileText size={14} className="text-gray-400 mt-0.5 flex-shrink-0" />
                  <div className="flex-1">
                    <p className="text-xs text-gray-500">Entidade</p>
                    <p className="font-medium break-words">{selectedLog.entity_name || "—"}</p>
                    <p className="text-xs text-gray-400 mt-0.5">{selectedLog.entity_type}</p>
                  </div>
                </div>

                {selectedLog.details && (
                  <div className="flex items-start gap-2">
                    <ChevronRight size={14} className="text-gray-400 mt-0.5 flex-shrink-0" />
                    <div className="flex-1">
                      <p className="text-xs text-gray-500">Detalhes</p>
                      <p className="text-sm break-words whitespace-pre-line">{selectedLog.details}</p>
                    </div>
                  </div>
                )}

                <div className="flex items-start gap-2">
                  <User size={14} className="text-gray-400 mt-0.5 flex-shrink-0" />
                  <div className="flex-1">
                    <p className="text-xs text-gray-500">Por</p>
                    <p className="text-sm">{selectedLog.user_name || "Usuário"}</p>
                  </div>
                </div>

                <div className="flex items-start gap-2">
                  <Calendar size={14} className="text-gray-400 mt-0.5 flex-shrink-0" />
                  <div className="flex-1">
                    <p className="text-xs text-gray-500">Quando</p>
                    <p className="text-sm">{formatDateTimeBR(selectedLog.created_at)}</p>
                  </div>
                </div>

                {selectedLog.rolled_back && (
                  <div className="bg-gray-100 border border-gray-200 rounded-md p-2 text-xs text-gray-600">
                    Esta ação já foi desfeita anteriormente
                    {selectedLog.rolled_back_at && (
                      <span> em {formatDateTimeBR(selectedLog.rolled_back_at)}</span>
                    )}.
                  </div>
                )}

                {!selectedLog.reversible && !selectedLog.rolled_back && (
                  <div className="bg-amber-50 border border-amber-200 rounded-md p-2 text-xs text-amber-700">
                    {(selectedLog.action || "").toLowerCase().includes("export")
                      ? "Exportações apenas geram arquivos e não modificam dados — não há nada para desfazer."
                      : "Esta ação foi registrada apenas para consulta. Não há estado anterior salvo para reverter."}
                  </div>
                )}
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setSelectedLog(null)}
                  data-testid="btn-fechar-detalhes"
                >
                  Fechar
                </Button>
                {selectedLog.reversible && !selectedLog.rolled_back && (
                  <Button
                    type="button"
                    onClick={() => handleRollback(selectedLog)}
                    disabled={reverting === selectedLog.id}
                    className="bg-blue-600 hover:bg-blue-700 text-white"
                    data-testid="btn-desfazer-acao"
                  >
                    <Undo2 size={14} className="mr-1.5" />
                    {reverting === selectedLog.id ? "Desfazendo..." : "Desfazer Ação"}
                  </Button>
                )}
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>
    </>
  );
}
