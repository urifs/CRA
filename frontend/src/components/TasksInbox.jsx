import { useState, useEffect } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import { API } from "@/App";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Inbox,
  X,
  AlertTriangle,
  AlertCircle,
  Info,
  Download,
  CheckCircle,
  FileText,
  Image,
  File,
  Clock,
  User,
  ExternalLink,
  Trash2,
  Trash,
} from "lucide-react";
import { toast } from "sonner";

const priorityConfig = {
  alta: { label: "Alta", color: "bg-red-500", icon: AlertTriangle },
  media: { label: "Média", color: "bg-yellow-500", icon: AlertCircle },
  baixa: { label: "Baixa", color: "bg-blue-500", icon: Info }
};

const formatFileSize = (bytes) => {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

const getFileIcon = (contentType) => {
  if (contentType?.startsWith("image/")) return Image;
  if (contentType?.includes("pdf")) return FileText;
  return File;
};

export default function TasksInbox({ system, accentColor = "#E31A1A" }) {
  const navigate = useNavigate();
  const [isOpen, setIsOpen] = useState(false);
  const [tasks, setTasks] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [selectedTask, setSelectedTask] = useState(null);
  const [showTaskDetail, setShowTaskDetail] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchUnreadCount();
    const interval = setInterval(fetchUnreadCount, 15000); // Check every 15 seconds
    return () => clearInterval(interval);
  }, [system]);

  useEffect(() => {
    if (isOpen) {
      fetchTasks();
    }
  }, [isOpen, system]);

  const fetchUnreadCount = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await axios.get(`${API}/tasks/unread-count?system=${system}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setUnreadCount(response.data.count);
    } catch (error) {
      console.error("Error fetching unread count:", error);
    }
  };

  const fetchTasks = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem("token");
      const response = await axios.get(`${API}/tasks?system=${system}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setTasks(response.data);
    } catch (error) {
      console.error("Error fetching tasks:", error);
      toast.error("Erro ao carregar tarefas");
    } finally {
      setLoading(false);
    }
  };

  const handleOpenTask = async (task) => {
    setSelectedTask(task);
    setShowTaskDetail(true);

    // Mark as read if not already
    if (!task.read) {
      try {
        const token = localStorage.getItem("token");
        await axios.patch(`${API}/tasks/${task.id}/read`, {}, {
          headers: { Authorization: `Bearer ${token}` }
        });
        
        // Update local state
        setTasks(prev => prev.map(t => 
          t.id === task.id ? { ...t, read: true } : t
        ));
        setUnreadCount(prev => Math.max(0, prev - 1));
      } catch (error) {
        console.error("Error marking task as read:", error);
      }
    }
  };

  const handleDownloadAttachment = async (task, attachment) => {
    try {
      const token = localStorage.getItem("token");
      const response = await axios.get(
        `${API}/tasks/${task.id}/attachments/${attachment.filename}`,
        {
          headers: { Authorization: `Bearer ${token}` },
          responseType: "blob"
        }
      );

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", attachment.original_name);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error("Error downloading attachment:", error);
      toast.error("Erro ao baixar anexo");
    }
  };

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleString("pt-BR", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit"
    });
  };

  // Resolve a rota e o label do botão "Abrir tela" baseado em origem.tipo
  const getOrigemAction = (task) => {
    const origem = task?.origem;
    if (!origem || typeof origem !== "object") return null;
    if (origem.rota) {
      const labels = {
        solicitacao_folha: "Abrir solicitação no Financeiro",
        folha_importada: "Ver folha importada",
        folha_aceita: "Ver folha lançada",
        folha_rejeitada: "Ver folha rejeitada",
      };
      return {
        rota: origem.rota,
        label: labels[origem.tipo] || "Abrir tela relacionada",
      };
    }
    // Fallback para tipos conhecidos sem campo `rota`
    const map = {
      folha_importada: { rota: "/rh/folha-importacao", label: "Ver folha importada" },
      folha_aceita: { rota: "/rh/folha-importacao", label: "Ver folha lançada" },
      folha_rejeitada: { rota: "/rh/folha-importacao", label: "Ver folha rejeitada" },
      solicitacao_folha: {
        rota: "/administrativo/solicitacoes-folha",
        label: "Abrir solicitação no Financeiro",
      },
    };
    return map[origem.tipo] || null;
  };

  const handleAbrirOrigem = (task) => {
    const action = getOrigemAction(task);
    if (!action) return;
    setShowTaskDetail(false);
    setIsOpen(false);
    navigate(action.rota);
  };

  const handleDeleteTask = async (e, task) => {
    if (e) {
      e.stopPropagation();
      e.preventDefault();
    }
    if (!window.confirm(`Excluir esta tarefa?\n\n"${task.title}"\n\nElla deixará de aparecer na sua Caixa de Tarefas.`)) return;
    try {
      const token = localStorage.getItem("token");
      await axios.delete(`${API}/tasks/${task.id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      toast.success("Tarefa excluída");
      // Atualização otimista
      setTasks((prev) => prev.filter((t) => t.id !== task.id));
      if (!task.read) setUnreadCount((prev) => Math.max(0, prev - 1));
      if (selectedTask?.id === task.id) {
        setShowTaskDetail(false);
        setSelectedTask(null);
      }
    } catch (err) {
      console.error(err);
      toast.error(err.response?.data?.detail || "Erro ao excluir tarefa");
    }
  };

  const handleClearAll = async () => {
    if (tasks.length === 0) return;
    if (!window.confirm(`Limpar TODAS as ${tasks.length} tarefas desta caixa?\n\nEsta ação não pode ser desfeita.`)) return;
    try {
      const token = localStorage.getItem("token");
      const res = await axios.delete(`${API}/tasks/clear-all/${system}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      toast.success(`${res.data.removidas} tarefa(s) removida(s)`);
      setTasks([]);
      setUnreadCount(0);
    } catch (err) {
      console.error(err);
      toast.error(err.response?.data?.detail || "Erro ao limpar tarefas");
    }
  };

  return (
    <>
      {/* Inbox Button */}
      <Button
        onClick={() => setIsOpen(true)}
        variant="ghost"
        className="relative p-2 hover:bg-gray-900"
        data-testid="tasks-inbox-btn"
      >
        <Inbox size={22} className="text-gray-300" />
        {unreadCount > 0 && (
          <span 
            className="absolute -top-1 -right-1 min-w-[18px] h-[18px] flex items-center justify-center text-xs font-bold rounded-full text-white"
            style={{ backgroundColor: accentColor }}
          >
            {unreadCount > 99 ? "99+" : unreadCount}
          </span>
        )}
      </Button>

      {/* Tasks List Dialog */}
      <Dialog open={isOpen} onOpenChange={setIsOpen}>
        <DialogContent className="max-w-lg max-h-[80vh] overflow-hidden flex flex-col">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Inbox size={20} />
              Caixa de Tarefas
              {unreadCount > 0 && (
                <Badge variant="destructive" className="ml-2">
                  {unreadCount} {unreadCount === 1 ? "nova" : "novas"}
                </Badge>
              )}
              {tasks.length > 0 && (
                <button
                  type="button"
                  onClick={handleClearAll}
                  className="ml-auto mr-6 inline-flex items-center gap-1 text-xs text-gray-500 hover:text-red-600 hover:bg-red-50 px-2 py-1 rounded-md transition-colors"
                  title="Limpar todas as tarefas desta caixa"
                  data-testid="btn-limpar-todas-tasks"
                >
                  <Trash size={13} />
                  Limpar todas
                </button>
              )}
            </DialogTitle>
          </DialogHeader>

          <div className="flex-1 overflow-y-auto space-y-3 pr-2">
            {loading ? (
              <div className="text-center py-8 text-gray-500">Carregando...</div>
            ) : tasks.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <Inbox size={48} className="mx-auto mb-2 opacity-50" />
                <p>Nenhuma tarefa recebida</p>
              </div>
            ) : (
              tasks.map((task) => {
                const PriorityIcon = priorityConfig[task.priority]?.icon || Info;
                return (
                  <Card
                    key={task.id}
                    className={`cursor-pointer hover:shadow-md transition-shadow ${
                      !task.read ? "border-l-4" : ""
                    }`}
                    style={{ borderLeftColor: !task.read ? accentColor : undefined }}
                    onClick={() => handleOpenTask(task)}
                  >
                    <CardContent className="p-4">
                      <div className="flex items-start gap-3">
                        <div className={`p-2 rounded-full ${priorityConfig[task.priority]?.color}`}>
                          <PriorityIcon size={16} className="text-white" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <h4 className={`font-medium truncate ${!task.read ? "font-bold" : ""}`}>
                              {task.title}
                            </h4>
                            {!task.read && (
                              <Badge variant="secondary" className="text-xs shrink-0">Nova</Badge>
                            )}
                          </div>
                          <p className="text-sm text-gray-500 truncate">{task.message}</p>
                          <div className="flex items-center gap-3 mt-2 text-xs text-gray-400">
                            <span className="flex items-center gap-1">
                              <User size={12} />
                              {task.created_by_name}
                            </span>
                            <span className="flex items-center gap-1">
                              <Clock size={12} />
                              {formatDate(task.created_at)}
                            </span>
                            {task.attachments?.length > 0 && (
                              <span className="flex items-center gap-1">
                                <File size={12} />
                                {task.attachments.length} anexo{task.attachments.length > 1 ? "s" : ""}
                              </span>
                            )}
                          </div>
                        </div>
                        {/* Lixeira para excluir tarefa individualmente */}
                        <button
                          type="button"
                          onClick={(e) => handleDeleteTask(e, task)}
                          className="p-2 rounded-md text-gray-400 hover:text-red-600 hover:bg-red-50 transition-colors shrink-0"
                          title="Excluir tarefa"
                          data-testid={`btn-excluir-task-${task.id}`}
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </CardContent>
                  </Card>
                );
              })
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* Task Detail Dialog */}
      <Dialog open={showTaskDetail} onOpenChange={setShowTaskDetail}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-hidden flex flex-col">
          {selectedTask && (
            <>
              <DialogHeader>
                <div className="flex items-start gap-3">
                  <div className={`p-2 rounded-full ${priorityConfig[selectedTask.priority]?.color} shrink-0`}>
                    {(() => {
                      const PriorityIcon = priorityConfig[selectedTask.priority]?.icon || Info;
                      return <PriorityIcon size={20} className="text-white" />;
                    })()}
                  </div>
                  <div className="flex-1">
                    <DialogTitle className="text-lg">{selectedTask.title}</DialogTitle>
                    <div className="flex items-center gap-3 mt-1 text-sm text-gray-500">
                      <Badge className={priorityConfig[selectedTask.priority]?.color}>
                        Prioridade {priorityConfig[selectedTask.priority]?.label}
                      </Badge>
                      {selectedTask.read && (
                        <span className="flex items-center gap-1 text-green-600">
                          <CheckCircle size={14} />
                          Lida
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </DialogHeader>

              <div className="flex-1 overflow-y-auto space-y-4">
                {/* Sender info */}
                <div className="flex items-center gap-2 text-sm text-gray-500 border-b pb-3">
                  <User size={16} />
                  <span>De: <strong>{selectedTask.created_by_name}</strong></span>
                  <span className="text-gray-300">•</span>
                  <Clock size={16} />
                  <span>{formatDate(selectedTask.created_at)}</span>
                </div>

                {/* Message */}
                <div className="bg-gray-50 rounded-lg p-4">
                  <p className="whitespace-pre-wrap text-gray-700">{selectedTask.message}</p>
                </div>

                {/* Attachments */}
                {selectedTask.attachments?.length > 0 && (
                  <div>
                    <h4 className="font-medium mb-3 flex items-center gap-2">
                      <File size={18} />
                      Anexos ({selectedTask.attachments.length})
                    </h4>
                    <div className="space-y-2">
                      {selectedTask.attachments.map((att) => {
                        const FileIcon = getFileIcon(att.content_type);
                        return (
                          <div
                            key={att.id}
                            className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border"
                          >
                            <div className="flex items-center gap-3">
                              <FileIcon size={20} className="text-gray-500" />
                              <div>
                                <p className="font-medium text-sm">{att.original_name}</p>
                                <p className="text-xs text-gray-500">{formatFileSize(att.size)}</p>
                              </div>
                            </div>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleDownloadAttachment(selectedTask, att)}
                            >
                              <Download size={16} className="mr-1" />
                              Baixar
                            </Button>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* Read info */}
                {selectedTask.read && selectedTask.read_at && (
                  <div className="text-xs text-gray-400 border-t pt-3">
                    Lida por {selectedTask.read_by} em {formatDate(selectedTask.read_at)}
                  </div>
                )}
              </div>

              {/* Botão de ação para abrir tela relacionada + lixeira */}
              <div className="border-t pt-3 mt-2 flex justify-between items-center gap-2">
                <Button
                  variant="outline"
                  onClick={() => handleDeleteTask(null, selectedTask)}
                  className="text-red-600 border-red-300 hover:bg-red-50"
                  data-testid="btn-excluir-task-detail"
                >
                  <Trash2 size={16} className="mr-2" />
                  Excluir tarefa
                </Button>
                {getOrigemAction(selectedTask) && (
                  <Button
                    onClick={() => handleAbrirOrigem(selectedTask)}
                    className="text-white"
                    style={{ backgroundColor: accentColor }}
                    data-testid="btn-abrir-origem-task"
                  >
                    <ExternalLink size={16} className="mr-2" />
                    {getOrigemAction(selectedTask).label}
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
