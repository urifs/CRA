import { useState, useEffect, useRef, useCallback } from "react";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card } from "@/components/ui/card";
import {
  Plus,
  Send,
  Loader2,
  Trash2,
  Sparkles,
  MessageSquare,
  User,
  Bot,
  Menu,
  X,
  FileDown,
  BookOpen,
  Paperclip,
  FileText,
} from "lucide-react";
import { toast } from "sonner";
import { useNavigate } from "react-router-dom";

const API = process.env.REACT_APP_BACKEND_URL;

const formatMessage = (text) => {
  if (!text) return "";
  let f = text;
  // bold
  f = f.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  // bullets
  f = f.replace(/^•\s+(.+)$/gm, '<div class="flex gap-2 my-1"><span>•</span><span>$1</span></div>');
  // line breaks
  f = f.replace(/\n/g, "<br/>");
  return f;
};

export default function RHChatPage() {
  const navigate = useNavigate();
  const token = localStorage.getItem("token");
  const headers = { Authorization: `Bearer ${token}` };

  const [conversations, setConversations] = useState([]);
  const [activeId, setActiveId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loadingConv, setLoadingConv] = useState(false);
  const [sending, setSending] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [pendingFiles, setPendingFiles] = useState([]); // arquivos selecionados ainda não enviados
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);
  const fileInputRef = useRef(null);

  const fetchConversations = useCallback(async () => {
    try {
      const r = await axios.get(`${API}/api/chatbot/conversations?module=rh`, { headers });
      setConversations(r.data || []);
      return r.data || [];
    } catch (e) {
      console.error("Erro ao listar conversas:", e);
      return [];
    }
  }, []);

  const loadMessages = async (convId) => {
    setLoadingConv(true);
    try {
      const r = await axios.get(`${API}/api/chatbot/conversations/${convId}/messages`, { headers });
      setMessages(r.data || []);
    } catch (e) {
      console.error("Erro ao carregar mensagens:", e);
      toast.error("Erro ao carregar mensagens");
    } finally {
      setLoadingConv(false);
    }
  };

  const newConversation = async () => {
    try {
      const r = await axios.post(
        `${API}/api/chatbot/conversations`,
        { title: "Nova conversa", module: "rh" },
        { headers }
      );
      const created = r.data;
      setConversations((prev) => [created, ...prev]);
      setActiveId(created.id);
      setMessages([]);
      setSidebarOpen(false);
      setTimeout(() => textareaRef.current?.focus(), 100);
    } catch {
      toast.error("Falha ao criar nova conversa");
    }
  };

  const deleteConversation = async (id, e) => {
    e?.stopPropagation();
    if (!window.confirm("Excluir esta conversa? Esta ação é irreversível.")) return;
    try {
      await axios.delete(`${API}/api/chatbot/conversations/${id}`, { headers });
      setConversations((prev) => prev.filter((c) => c.id !== id));
      if (activeId === id) {
        setActiveId(null);
        setMessages([]);
      }
    } catch {
      toast.error("Erro ao excluir conversa");
    }
  };

  const sendMessage = async () => {
    const text = input.trim();
    const hasFiles = pendingFiles.length > 0;
    if ((!text && !hasFiles) || sending) return;

    let convId = activeId;
    if (!convId) {
      try {
        const r = await axios.post(
          `${API}/api/chatbot/conversations`,
          { title: "Nova conversa", module: "rh" },
          { headers }
        );
        convId = r.data.id;
        setActiveId(convId);
        setConversations((prev) => [r.data, ...prev]);
      } catch {
        toast.error("Erro ao iniciar conversa");
        return;
      }
    }

    // Otimista: insere mensagem do usuário imediatamente
    const userMsg = {
      id: `tmp-${Date.now()}`,
      role: "user",
      content: text || "(arquivos anexados)",
      attachments: pendingFiles.map((f) => ({ filename: f.name, mime: f.type, size: f.size })),
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    const filesToSend = pendingFiles;
    setPendingFiles([]);
    setSending(true);

    try {
      let r;
      if (hasFiles) {
        const fd = new FormData();
        fd.append("content", text);
        filesToSend.forEach((f) => fd.append("files", f, f.name));
        r = await axios.post(
          `${API}/api/chatbot/conversations/${convId}/messages-with-files`,
          fd,
          { headers: { ...headers, "Content-Type": "multipart/form-data" } }
        );
      } else {
        r = await axios.post(
          `${API}/api/chatbot/conversations/${convId}/messages`,
          { content: text },
          { headers }
        );
      }
      const assistantMsg = r.data;
      setMessages((prev) => [...prev, assistantMsg]);
      fetchConversations();
    } catch (e) {
      toast.error(e.response?.data?.detail || "Erro ao enviar mensagem");
      setMessages((prev) => prev.filter((m) => m.id !== userMsg.id));
      setPendingFiles(filesToSend); // restaura para o usuário tentar de novo
    } finally {
      setSending(false);
      setTimeout(() => textareaRef.current?.focus(), 80);
    }
  };

  const handleFilesSelected = (e) => {
    const arr = Array.from(e.target.files || []);
    if (arr.length === 0) return;
    // Limite de tamanho ~25MB por arquivo
    const validos = arr.filter((f) => {
      if (f.size > 25 * 1024 * 1024) {
        toast.error(`${f.name}: máximo 25MB`);
        return false;
      }
      return true;
    });
    setPendingFiles((prev) => [...prev, ...validos]);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const removerPendingFile = (idx) => {
    setPendingFiles((prev) => prev.filter((_, i) => i !== idx));
  };

  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, sending]);

  // Inicial: carrega conversas e abre a mais recente (carrega mensagens uma única vez)
  useEffect(() => {
    let cancelled = false;
    (async () => {
      const list = await fetchConversations();
      if (cancelled) return;
      if (list.length > 0) {
        setActiveId(list[0].id);
        await loadMessages(list[0].id);
      }
    })();
    return () => { cancelled = true; };
  }, [fetchConversations]);

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const downloadArtifact = async (artifact) => {
    try {
      const url = artifact.download_url.startsWith("http")
        ? artifact.download_url
        : `${API}${artifact.download_url}`;
      const r = await axios.get(url, { headers, responseType: "blob" });
      const blob = new Blob([r.data], { type: artifact.content_type || "application/octet-stream" });
      const link = document.createElement("a");
      link.href = window.URL.createObjectURL(blob);
      const name = artifact.label?.replace(/^Baixar\s+/i, "") || "arquivo";
      link.download = `${name}.pdf`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(link.href);
    } catch (e) {
      console.error("Erro ao baixar:", e);
      toast.error("Erro ao baixar arquivo gerado");
    }
  };

  const examplePrompts = [
    "Quantos funcionários temos ativos hoje?",
    "Qual o custo total da folha de pagamento do mês atual?",
    "Liste funcionários com mais de 5 faltas no mês",
    "Resumo das contas a pagar vencidas",
  ];

  return (
    <div className="flex h-screen md:h-screen bg-[#0f0f10] text-gray-100">
      {/* Sidebar */}
      <aside
        className={`${
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        } md:translate-x-0 transition-transform duration-200 fixed md:static inset-y-0 left-0 z-30 w-72 bg-[#171718] border-r border-gray-800 flex flex-col`}
        data-testid="rhchat-sidebar"
      >
        <div className="p-3 border-b border-gray-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sparkles size={18} className="text-emerald-400" />
            <span className="font-semibold text-sm">RH Assistant</span>
          </div>
          <button
            className="md:hidden text-gray-400 hover:text-white"
            onClick={() => setSidebarOpen(false)}
            data-testid="rhchat-close-sidebar"
          >
            <X size={18} />
          </button>
        </div>

        <div className="p-3">
          <Button
            onClick={newConversation}
            className="w-full bg-emerald-600 hover:bg-emerald-700 text-white border-0 justify-start gap-2"
            data-testid="rhchat-new-conversation"
          >
            <Plus size={16} />
            Nova conversa
          </Button>
        </div>

        <div className="flex-1 overflow-y-auto px-2 pb-3">
          <p className="text-[11px] uppercase tracking-wider text-gray-500 px-2 py-1">
            Histórico ({conversations.length})
          </p>
          {conversations.length === 0 ? (
            <p className="text-xs text-gray-500 px-2 py-4 italic">
              Nenhuma conversa ainda. Clique em "Nova conversa" para começar.
            </p>
          ) : (
            <div className="space-y-1">
              {conversations.map((c) => (
                <button
                  key={c.id}
                  onClick={async () => {
                    if (activeId !== c.id) {
                      setActiveId(c.id);
                      await loadMessages(c.id);
                    }
                    setSidebarOpen(false);
                  }}
                  className={`w-full text-left px-2 py-2 rounded-md text-sm group hover:bg-gray-800 flex items-start gap-2 ${
                    activeId === c.id ? "bg-gray-800" : ""
                  }`}
                  data-testid={`rhchat-conv-${c.id}`}
                >
                  <MessageSquare
                    size={14}
                    className="mt-0.5 text-gray-500 flex-shrink-0"
                  />
                  <div className="flex-1 min-w-0">
                    <p className="truncate text-gray-200">{c.title}</p>
                    {c.last_message_preview && (
                      <p className="truncate text-[11px] text-gray-500">
                        {c.last_message_preview}
                      </p>
                    )}
                  </div>
                  <button
                    onClick={(e) => deleteConversation(c.id, e)}
                    className="opacity-0 group-hover:opacity-100 text-gray-500 hover:text-red-400 transition-opacity"
                    title="Excluir conversa"
                    data-testid={`rhchat-delete-conv-${c.id}`}
                  >
                    <Trash2 size={13} />
                  </button>
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="p-3 border-t border-gray-800 space-y-2">
          <button
            onClick={() => navigate("/admin/chat-knowledge-base")}
            className="w-full flex items-center gap-2 px-2 py-2 rounded-md text-xs text-gray-300 hover:bg-gray-800 hover:text-white transition-colors"
            data-testid="rhchat-kb-link"
          >
            <BookOpen size={14} className="text-emerald-400" />
            <span>Base de Conhecimento</span>
          </button>
          <div className="text-[11px] text-gray-500 px-2">
            Powered by Gemini 2.5 Flash
          </div>
        </div>
      </aside>

      {/* Backdrop mobile */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/60 z-20 md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Main */}
      <main className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <div className="border-b border-gray-800 bg-[#171718] px-4 py-3 flex items-center gap-3">
          <button
            className="md:hidden text-gray-300 hover:text-white"
            onClick={() => setSidebarOpen(true)}
            data-testid="rhchat-open-sidebar"
          >
            <Menu size={20} />
          </button>
          <Bot size={18} className="text-emerald-400" />
          <h1 className="font-semibold text-sm md:text-base flex-1 truncate">
            {conversations.find((c) => c.id === activeId)?.title || "Assistente RH"}
          </h1>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto bg-[#0f0f10]">
          {loadingConv ? (
            <div className="flex items-center justify-center h-full text-gray-500">
              <Loader2 className="animate-spin mr-2" size={18} /> Carregando...
            </div>
          ) : messages.length === 0 ? (
            <div className="max-w-3xl mx-auto px-4 py-12 md:py-20">
              <div className="text-center mb-10">
                <div className="inline-flex items-center justify-center w-14 h-14 rounded-full bg-emerald-500/10 mb-4">
                  <Sparkles size={28} className="text-emerald-400" />
                </div>
                <h2 className="text-2xl md:text-3xl font-semibold text-white mb-2">
                  Como posso ajudar?
                </h2>
                <p className="text-gray-400 text-sm">
                  Pergunte qualquer coisa sobre o RH, finanças, frota ou qualquer dado registrado na plataforma.
                </p>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-w-2xl mx-auto">
                {examplePrompts.map((p, i) => (
                  <Card
                    key={i}
                    onClick={() => {
                      setInput(p);
                      setTimeout(() => textareaRef.current?.focus(), 0);
                    }}
                    className="bg-[#1c1c1e] border-gray-800 hover:border-emerald-500/40 hover:bg-[#222224] cursor-pointer p-4 transition-colors"
                    data-testid={`rhchat-example-${i}`}
                  >
                    <p className="text-sm text-gray-200">{p}</p>
                  </Card>
                ))}
              </div>
            </div>
          ) : (
            <div className="max-w-3xl mx-auto px-4 py-12 flex flex-col gap-20 md:gap-24">
              {messages.map((m) => (
                <div
                  key={m.id}
                  className={`flex gap-3 ${m.role === "user" ? "flex-row-reverse" : ""}`}
                  data-testid={`rhchat-msg-${m.role}`}
                >
                  <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                      m.role === "user"
                        ? "bg-emerald-600"
                        : "bg-gradient-to-br from-emerald-500 to-cyan-600"
                    }`}
                  >
                    {m.role === "user" ? <User size={16} /> : <Bot size={16} />}
                  </div>
                  <div
                    className={`max-w-[85%] rounded-2xl px-5 py-4 text-sm leading-relaxed shadow-sm ${
                      m.role === "user"
                        ? "bg-emerald-600 text-white"
                        : "bg-[#1c1c1e] text-gray-100 border border-gray-800"
                    }`}
                  >
                    <div
                      dangerouslySetInnerHTML={{ __html: formatMessage(m.content) }}
                    />
                    {/* Chips de anexos enviados pelo usuário */}
                    {m.role === "user" && Array.isArray(m.attachments) && m.attachments.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-1.5">
                        {m.attachments.map((a, idx) => (
                          <span
                            key={idx}
                            className="inline-flex items-center gap-1 bg-emerald-900/40 border border-emerald-400/40 rounded-full px-2 py-0.5 text-[10px]"
                          >
                            <FileText size={10} />
                            <span className="truncate max-w-[180px]">{a.filename}</span>
                          </span>
                        ))}
                      </div>
                    )}
                    {m.artifact && (
                      <div className="mt-3 pt-3 border-t border-gray-700">
                        <button
                          onClick={() => downloadArtifact(m.artifact)}
                          className="inline-flex items-center gap-2 px-3 py-2 bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-300 rounded-lg text-xs font-medium transition-colors"
                          data-testid={`rhchat-artifact-${m.id}`}
                        >
                          <FileDown size={14} />
                          {m.artifact.label || m.artifact.filename || "Baixar arquivo gerado"}
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              ))}
              {sending && (
                <div className="flex gap-3" data-testid="rhchat-typing">
                  <div className="w-8 h-8 rounded-full flex items-center justify-center bg-gradient-to-br from-emerald-500 to-cyan-600 flex-shrink-0">
                    <Bot size={16} />
                  </div>
                  <div className="bg-[#1c1c1e] border border-gray-800 rounded-2xl px-4 py-3">
                    <div className="flex gap-1.5">
                      <span className="w-2 h-2 bg-emerald-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                      <span className="w-2 h-2 bg-emerald-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                      <span className="w-2 h-2 bg-emerald-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Input */}
        <div className="border-t border-gray-800 bg-[#171718] px-4 py-3">
          <div className="max-w-3xl mx-auto space-y-2">
            {/* Chips dos arquivos pendentes */}
            {pendingFiles.length > 0 && (
              <div className="flex flex-wrap gap-2" data-testid="chat-pending-files">
                {pendingFiles.map((f, idx) => (
                  <div
                    key={`${f.name}-${idx}`}
                    className="flex items-center gap-2 bg-emerald-900/40 border border-emerald-600 rounded-full px-3 py-1 text-xs text-emerald-100"
                  >
                    <FileText size={12} />
                    <span className="truncate max-w-[200px]">{f.name}</span>
                    <span className="text-emerald-300">({(f.size / 1024).toFixed(0)}KB)</span>
                    <button
                      type="button"
                      onClick={() => removerPendingFile(idx)}
                      className="hover:text-red-300"
                      title="Remover"
                    >
                      <X size={12} />
                    </button>
                  </div>
                ))}
              </div>
            )}
            <div className="flex items-end gap-2">
              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept=".pdf,.png,.jpg,.jpeg,.webp,.gif,.txt,.md,.csv,.xlsx,.xls,.docx,.doc,application/pdf,image/*,text/*,.xlsx,.xls,.docx,.doc,application/vnd.ms-excel,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                onChange={handleFilesSelected}
                className="hidden"
                data-testid="rhchat-file-input"
              />
              <Button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                disabled={sending}
                className="bg-[#0f0f10] hover:bg-[#252527] text-gray-300 border border-gray-800 h-10 w-10 p-0 flex-shrink-0"
                title="Anexar arquivo (PDF, imagem, Excel, CSV, Word, texto)"
                data-testid="rhchat-attach-btn"
              >
                <Paperclip size={16} />
              </Button>
              <Textarea
                ref={textareaRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={pendingFiles.length > 0 ? "Pergunte algo sobre os arquivos ou peça uma alteração..." : "Pergunte algo sobre RH, finanças, dados da plataforma..."}
                rows={1}
                className="resize-none bg-[#0f0f10] border-gray-800 text-gray-100 focus-visible:ring-emerald-500 max-h-40"
                data-testid="rhchat-input"
              />
              <Button
                onClick={sendMessage}
                disabled={(!input.trim() && pendingFiles.length === 0) || sending}
                className="bg-emerald-600 hover:bg-emerald-700 text-white border-0 h-10 w-10 p-0 flex-shrink-0"
                data-testid="rhchat-send"
              >
                {sending ? (
                  <Loader2 className="animate-spin" size={16} />
                ) : (
                  <Send size={16} />
                )}
              </Button>
            </div>
          </div>
          <p className="text-[10px] text-center text-gray-500 mt-2">
            Modelo: Gemini 2.5 Flash · Anexe arquivos (PDF, imagem, Excel, CSV, Word, texto) e peça análise ou alterações. Pode cometer erros.
          </p>
        </div>
      </main>
    </div>
  );
}
