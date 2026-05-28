import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth, API } from "@/App";
import axios from "axios";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import ChatbotWidget from "@/components/ChatbotWidget";
import DriveConnectionCard from "@/components/DriveConnectionCard";
import {
  Shield,
  Users,
  Activity,
  ArrowLeft,
  Plus,
  Eye,
  Trash2,
  Loader2,
  Clock,
  Calendar,
  User,
  FileText,
  Wrench,
  Package,
  DollarSign,
  Edit,
  Search,
  Building2,
  Crown,
  Info,
  Database,
  Download,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  Send,
  Inbox,
  AlertTriangle,
  AlertCircle,
  Paperclip,
  X as XIcon,
  KeyRound,
  Copy,
  Cloud
} from "lucide-react";

// Tipos de usuário
const USER_ROLES = {
  gerenciamento: { label: "Gerenciamento", icon: Wrench, color: "bg-[#E31A1A]" },
  administrativo: { label: "Administrativo", icon: Building2, color: "bg-[#D4A000]" },
  rh: { label: "RH", icon: Users, color: "bg-[#10B981]" },
  ambos: { label: "Gerenciamento + Administrativo", icon: Users, color: "bg-purple-500" },
  ambos_rh: { label: "Ger + Admin + RH", icon: Crown, color: "bg-purple-600" },
  gerenciamento_rh: { label: "Gerenciamento + RH", icon: Users, color: "bg-pink-500" },
  administrativo_rh: { label: "Administrativo + RH", icon: Building2, color: "bg-orange-500" },
  admin: { label: "Administrador", icon: Crown, color: "bg-green-500" },
  programador: { label: "Programador", icon: Crown, color: "bg-blue-600" }
};

// Prioridades
const PRIORITIES = {
  baixa: { label: "Baixa", color: "bg-blue-500", icon: Info },
  media: { label: "Média", color: "bg-yellow-500", icon: AlertCircle },
  alta: { label: "Alta", color: "bg-red-500", icon: AlertTriangle }
};

// Sistemas alvo
const TARGET_SYSTEMS = {
  gerenciamento: { label: "Gerenciamento", color: "bg-[#E31A1A]" },
  administrativo: { label: "Administrativo", color: "bg-[#D4A000]" },
  rh: { label: "RH", color: "bg-[#10B981]" }
};

// Coleções disponíveis
const COLLECTIONS = [
  { id: "users", label: "Usuários", icon: Users },
  { id: "machines", label: "Máquinas", icon: Wrench },
  { id: "maintenances", label: "Manutenções", icon: Wrench },
  { id: "categories", label: "Categorias", icon: FileText },
  { id: "stock_items", label: "Estoque", icon: Package },
  { id: "obras", label: "Obras", icon: Building2 },
  { id: "contas_pagar", label: "Contas a Pagar", icon: DollarSign },
  { id: "contas_receber", label: "Contas a Receber", icon: DollarSign },
  { id: "cadastros", label: "Cadastros", icon: Users },
  { id: "produtos_admin", label: "Produtos", icon: Package },
  { id: "ordens_servico", label: "Ordens de Serviço", icon: FileText },
  { id: "alugueis", label: "Aluguéis", icon: Calendar },
  { id: "audit_logs", label: "Logs de Auditoria", icon: Activity },
];

export default function PainelAdminPage() {
  const navigate = useNavigate();
  const { user, token } = useAuth();
  const [users, setUsers] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [selectedUser, setSelectedUser] = useState(null);
  const [userActivities, setUserActivities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showActivitiesModal, setShowActivitiesModal] = useState(false);
  const [showActivityDetailModal, setShowActivityDetailModal] = useState(false);
  const [selectedActivity, setSelectedActivity] = useState(null);
  const [activeTab, setActiveTab] = useState("users");
  const [searchTerm, setSearchTerm] = useState("");
  const [showEditRoleModal, setShowEditRoleModal] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [newRole, setNewRole] = useState("");
  const [updatingRole, setUpdatingRole] = useState(false);
  const [createForm, setCreateForm] = useState({
    name: "",
    email: "",
    password: "",
    confirmPassword: "",
    role: "gerenciamento"
  });
  const [creating, setCreating] = useState(false);

  // Database states
  const [selectedCollection, setSelectedCollection] = useState("users");
  const [dbDocuments, setDbDocuments] = useState([]);
  const [dbLoading, setDbLoading] = useState(false);
  const [dbSearchTerm, setDbSearchTerm] = useState("");
  const [dbPage, setDbPage] = useState(1);
  const [dbTotal, setDbTotal] = useState(0);
  const [showDocModal, setShowDocModal] = useState(false);
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [docEditMode, setDocEditMode] = useState(false);
  const [docJson, setDocJson] = useState("");
  const [showAddDocModal, setShowAddDocModal] = useState(false);
  const [newDocJson, setNewDocJson] = useState("{\n  \n}");
  const [dbExportLoading, setDbExportLoading] = useState(false);

  // Task states
  const [tasks, setTasks] = useState([]);
  const [tasksLoading, setTasksLoading] = useState(false);
  const [taskForm, setTaskForm] = useState({
    target_system: "gerenciamento",
    priority: "media",
    title: "",
    message: ""
  });
  const [taskAttachments, setTaskAttachments] = useState([]);
  const [uploadingTask, setUploadingTask] = useState(false);
  const [creatingTask, setCreatingTask] = useState(false);
  const [showTaskDetailModal, setShowTaskDetailModal] = useState(false);
  const [selectedTask, setSelectedTask] = useState(null);

  useEffect(() => {
    fetchUsers();
    fetchAuditLogs();
  }, []);

  useEffect(() => {
    if (activeTab === "database") {
      fetchDbDocuments();
    }
    if (activeTab === "tasks") {
      fetchTasks();
    }
  }, [activeTab, selectedCollection, dbPage]);

  const fetchTasks = async () => {
    setTasksLoading(true);
    try {
      const response = await axios.get(`${API}/admin-panel/tasks`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setTasks(response.data);
    } catch (error) {
      console.error("Erro ao carregar tarefas:", error);
    } finally {
      setTasksLoading(false);
    }
  };

  const handleCreateTask = async () => {
    if (!taskForm.title.trim() || !taskForm.message.trim()) {
      toast.error("Preencha o título e a mensagem");
      return;
    }

    setCreatingTask(true);
    try {
      // Create task first
      const response = await axios.post(`${API}/admin-panel/tasks`, taskForm, {
        headers: { Authorization: `Bearer ${token}` }
      });

      const taskId = response.data.id;

      // Upload attachments if any
      for (const file of taskAttachments) {
        const formData = new FormData();
        formData.append("file", file);
        
        await axios.post(`${API}/admin-panel/tasks/${taskId}/attachments`, formData, {
          headers: { 
            Authorization: `Bearer ${token}`,
            "Content-Type": "multipart/form-data"
          }
        });
      }

      toast.success("Tarefa criada e enviada com sucesso!");
      setTaskForm({ target_system: "gerenciamento", priority: "media", title: "", message: "" });
      setTaskAttachments([]);
      fetchTasks();
    } catch (error) {
      console.error("Erro ao criar tarefa:", error);
      toast.error(error.response?.data?.detail || "Erro ao criar tarefa");
    } finally {
      setCreatingTask(false);
    }
  };

  const handleTaskFileSelect = (e) => {
    const files = Array.from(e.target.files);
    const validFiles = [];
    
    for (const file of files) {
      if (file.size > 100 * 1024 * 1024) {
        toast.error(`${file.name} é muito grande. Máximo: 100MB`);
      } else {
        validFiles.push(file);
      }
    }
    
    setTaskAttachments(prev => [...prev, ...validFiles]);
    e.target.value = "";
  };

  const removeTaskAttachment = (index) => {
    setTaskAttachments(prev => prev.filter((_, i) => i !== index));
  };

  const handleDeleteTask = async (taskId) => {
    if (!confirm("Tem certeza que deseja excluir esta tarefa?")) return;
    
    try {
      await axios.delete(`${API}/admin-panel/tasks/${taskId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success("Tarefa excluída");
      fetchTasks();
    } catch (error) {
      toast.error("Erro ao excluir tarefa");
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const fetchUsers = async () => {
    try {
      const response = await axios.get(`${API}/admin-panel/users`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setUsers(response.data);
    } catch (error) {
      console.error("Erro ao carregar usuários:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchAuditLogs = async () => {
    try {
      const response = await axios.get(`${API}/admin-panel/audit-logs`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setAuditLogs(response.data);
    } catch (error) {
      console.error("Erro ao carregar logs:", error);
    }
  };

  const fetchDbDocuments = async () => {
    setDbLoading(true);
    try {
      const response = await axios.get(`${API}/admin-panel/database/${selectedCollection}`, {
        headers: { Authorization: `Bearer ${token}` },
        params: { page: dbPage, limit: 20, search: dbSearchTerm }
      });
      setDbDocuments(response.data.documents || []);
      setDbTotal(response.data.total || 0);
    } catch (error) {
      console.error("Erro ao carregar documentos:", error);
      toast.error("Erro ao carregar documentos");
    } finally {
      setDbLoading(false);
    }
  };

  // Faz o download do backup completo do banco (todas as collections + schema + DDL)
  const handleExportDatabase = async () => {
    if (dbExportLoading) return;
    setDbExportLoading(true);
    const tId = toast.loading("Gerando backup completo do banco... isso pode levar alguns segundos.");
    try {
      const resp = await axios.get(`${API}/admin-panel/database-export`, {
        headers: { Authorization: `Bearer ${token}` },
        responseType: "blob",
      });
      const totalDocs = resp.headers["x-export-total-docs"];
      const totalCols = resp.headers["x-export-collections"];
      // Extrai filename do Content-Disposition
      const cd = resp.headers["content-disposition"] || "";
      const m = /filename="?([^";]+)"?/i.exec(cd);
      const filename = (m && m[1]) || `backup_db_${new Date().toISOString().replace(/[:.]/g, "-")}.zip`;
      const url = window.URL.createObjectURL(new Blob([resp.data], { type: "application/zip" }));
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      setTimeout(() => window.URL.revokeObjectURL(url), 1000);
      toast.success(`Backup gerado: ${totalDocs} documentos em ${totalCols} collections`, { id: tId });
    } catch (e) {
      console.error("Erro ao exportar banco:", e);
      toast.error("Falha ao gerar o backup do banco. Verifique se você é admin.", { id: tId });
    } finally {
      setDbExportLoading(false);
    }
  };

  // === Object Storage (migração persistente entre deploys) ===
  const [storageMigrating, setStorageMigrating] = useState(false);
  const [storageExporting, setStorageExporting] = useState(false);
  const [storageImporting, setStorageImporting] = useState(false);

  const handleMigrateStorage = async () => {
    if (storageMigrating) return;
    setStorageMigrating(true);
    const tId = toast.loading("Migrando arquivos do filesystem local para Object Storage...");
    try {
      const resp = await axios.post(`${API}/storage/migrate-to-object-storage`, null, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const d = resp.data || {};
      toast.success(`Migração: ${d.files_migrated || 0} arquivos, ${d.folders_created || 0} pastas (pulou ${d.skipped || 0})`, { id: tId });
    } catch (e) {
      console.error("Erro ao migrar storage:", e);
      toast.error("Falha na migração. Veja o console para detalhes.", { id: tId });
    } finally {
      setStorageMigrating(false);
    }
  };

  const handleExportStorageZip = async () => {
    if (storageExporting) return;
    setStorageExporting(true);
    const tId = toast.loading("Gerando ZIP de todo o armazenamento...");
    try {
      const resp = await axios.get(`${API}/storage/export-zip`, {
        headers: { Authorization: `Bearer ${token}` },
        responseType: "blob",
      });
      const url = window.URL.createObjectURL(new Blob([resp.data], { type: "application/zip" }));
      const a = document.createElement("a");
      a.href = url;
      a.download = `storage_export_${new Date().toISOString().replace(/[:.]/g, "-")}.zip`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      setTimeout(() => window.URL.revokeObjectURL(url), 1000);
      toast.success("ZIP gerado com sucesso", { id: tId });
    } catch (e) {
      console.error("Erro ao exportar storage:", e);
      toast.error("Falha ao exportar storage.", { id: tId });
    } finally {
      setStorageExporting(false);
    }
  };

  const handleImportStorageZip = async (file) => {
    if (!file || storageImporting) return;
    setStorageImporting(true);
    const tId = toast.loading(`Importando ${file.name}...`);
    try {
      const fd = new FormData();
      fd.append("file", file);
      const resp = await axios.post(`${API}/storage/import-zip`, fd, {
        headers: { Authorization: `Bearer ${token}`, "Content-Type": "multipart/form-data" },
      });
      const d = resp.data || {};
      toast.success(`Importação: ${d.files_imported || 0} arquivos, ${d.folders_created || 0} pastas`, { id: tId });
    } catch (e) {
      console.error("Erro ao importar storage:", e);
      toast.error("Falha na importação. Verifique se é um ZIP válido.", { id: tId });
    } finally {
      setStorageImporting(false);
    }
  };

  const fetchUserActivities = async (userId, userName, userRole) => {
    try {
      const response = await axios.get(`${API}/admin-panel/users/${userId}/activities`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setUserActivities(response.data);
      setSelectedUser({ id: userId, name: userName, role: userRole });
      setShowActivitiesModal(true);
    } catch (error) {
      toast.error("Erro ao carregar atividades");
    }
  };

  const handleCreateUser = async (e) => {
    e.preventDefault();
    if (createForm.password !== createForm.confirmPassword) {
      toast.error("As senhas não coincidem");
      return;
    }
    setCreating(true);
    try {
      await axios.post(`${API}/admin-panel/users`, {
        name: createForm.name,
        email: createForm.email,
        password: createForm.password,
        role: createForm.role
      }, { headers: { Authorization: `Bearer ${token}` } });
      toast.success("Usuário criado!");
      setShowCreateModal(false);
      setCreateForm({ name: "", email: "", password: "", confirmPassword: "", role: "gerenciamento" });
      fetchUsers();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao criar usuário");
    } finally {
      setCreating(false);
    }
  };

  const handleDeleteUser = async (userId, userName) => {
    if (userId === user?.id) return toast.error("Você não pode excluir sua própria conta");
    if (!confirm(`Excluir usuário "${userName}"?`)) return;
    try {
      await axios.delete(`${API}/admin-panel/users/${userId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success("Usuário excluído!");
      fetchUsers();
    } catch (error) {
      toast.error("Erro ao excluir");
    }
  };

  const [resetPasswordResult, setResetPasswordResult] = useState(null); // { name, password, copied }

  const handleResetPassword = async (userId, userName, userEmail) => {
    const escolha = window.prompt(
      `Resetar senha de "${userName}".\n\n` +
      `Digite a nova senha (mínimo 6 caracteres) ou deixe em branco para gerar automaticamente:`,
      ""
    );
    if (escolha === null) return; // cancelado
    if (escolha && escolha.trim().length > 0 && escolha.trim().length < 6) {
      toast.error("A senha deve ter ao menos 6 caracteres");
      return;
    }
    try {
      const r = await axios.post(
        `${API}/admin-panel/users/${userId}/reset-password`,
        { new_password: escolha && escolha.trim().length >= 6 ? escolha.trim() : null },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setResetPasswordResult({
        name: userName,
        email: userEmail,
        password: r.data.new_password,
        gerada: r.data.gerada_automaticamente,
      });
      toast.success("Senha resetada com sucesso");
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao resetar senha");
    }
  };

  const openEditRoleModal = (userToEdit) => {
    setEditingUser(userToEdit);
    setNewRole(userToEdit.role || "gerenciamento");
    setShowEditRoleModal(true);
  };

  const handleUpdateRole = async () => {
    if (!editingUser) return;
    setUpdatingRole(true);
    try {
      await axios.patch(`${API}/admin-panel/users/${editingUser.id}/role`, 
        { role: newRole },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success(`Permissão de ${editingUser.name} atualizada para ${newRole}!`);
      setShowEditRoleModal(false);
      fetchUsers();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao atualizar permissão");
    } finally {
      setUpdatingRole(false);
    }
  };

  const handleViewDoc = (doc) => {
    setSelectedDoc(doc);
    setDocJson(JSON.stringify(doc, null, 2));
    setDocEditMode(false);
    setShowDocModal(true);
  };

  const handleUpdateDoc = async () => {
    try {
      const parsed = JSON.parse(docJson);
      await axios.put(`${API}/admin-panel/database/${selectedCollection}/${selectedDoc.id || selectedDoc._id}`, parsed, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success("Documento atualizado!");
      setShowDocModal(false);
      fetchDbDocuments();
    } catch (error) {
      toast.error(error.message || "Erro ao atualizar");
    }
  };

  const handleDeleteDoc = async (docId) => {
    if (!confirm("Excluir este documento?")) return;
    try {
      await axios.delete(`${API}/admin-panel/database/${selectedCollection}/${docId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success("Documento excluído!");
      fetchDbDocuments();
    } catch (error) {
      toast.error("Erro ao excluir");
    }
  };

  const handleAddDoc = async () => {
    try {
      const parsed = JSON.parse(newDocJson);
      await axios.post(`${API}/admin-panel/database/${selectedCollection}`, parsed, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success("Documento adicionado!");
      setShowAddDocModal(false);
      setNewDocJson("{\n  \n}");
      fetchDbDocuments();
    } catch (error) {
      toast.error(error.message || "Erro ao adicionar");
    }
  };

  const openActivityDetail = (activity) => {
    setSelectedActivity(activity);
    setShowActivityDetailModal(true);
  };

  const formatDate = (dateStr) => dateStr ? new Date(dateStr).toLocaleString("pt-BR") : "-";
  const formatDateShort = (dateStr) => dateStr ? new Date(dateStr).toLocaleDateString("pt-BR") : "-";

  const getActionIcon = (action, entityType) => {
    const text = (action || "").toLowerCase() + (entityType || "").toLowerCase();
    if (text.includes("manutenção") || text.includes("manutencao") || text.includes("máquina") || text.includes("maquina")) return <Wrench size={14} />;
    if (text.includes("estoque") || text.includes("produto")) return <Package size={14} />;
    if (text.includes("conta") || text.includes("financ") || text.includes("pagamento")) return <DollarSign size={14} />;
    if (text.includes("usuário") || text.includes("usuario") || text.includes("user")) return <User size={14} />;
    if (text.includes("obra") || text.includes("cadastro")) return <Building2 size={14} />;
    if (text.includes("ordem") || text.includes("serviço")) return <FileText size={14} />;
    if (text.includes("aluguel")) return <Calendar size={14} />;
    return <Activity size={14} />;
  };

  const getActionColor = (action) => {
    const text = (action || "").toLowerCase();
    if (text.includes("criou") || text.includes("create") || text.includes("criar")) return "bg-green-500/20 text-green-400";
    if (text.includes("editou") || text.includes("atualizou") || text.includes("update") || text.includes("editar")) return "bg-blue-500/20 text-blue-400";
    if (text.includes("excluiu") || text.includes("delete") || text.includes("excluir")) return "bg-red-500/20 text-red-400";
    return "bg-gray-500/20 text-gray-400";
  };

  const getModuleBadge = (module) => {
    const moduleColors = {
      "Gerenciamento": "bg-[#E31A1A] text-white",
      "Administrativo": "bg-[#D4A000] text-white",
      "Painel Admin": "bg-purple-600 text-white",
      "Sistema": "bg-gray-600 text-white"
    };
    return <Badge className={`${moduleColors[module] || moduleColors["Sistema"]} text-xs`}>{module || "Sistema"}</Badge>;
  };

  const getRoleBadge = (role) => {
    const roleInfo = USER_ROLES[role] || USER_ROLES.gerenciamento;
    const Icon = roleInfo.icon;
    return <Badge className={`${roleInfo.color} text-white text-xs flex items-center gap-1`}><Icon size={12} />{roleInfo.label}</Badge>;
  };

  const filteredUsers = users.filter(u => u.name?.toLowerCase().includes(searchTerm.toLowerCase()) || u.email?.toLowerCase().includes(searchTerm.toLowerCase()));
  const filteredLogs = auditLogs.filter(log => 
    log.user_name?.toLowerCase().includes(searchTerm.toLowerCase()) || 
    log.action?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    log.module?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    log.entity_name?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) {
    return <div className="min-h-screen bg-black flex items-center justify-center"><Loader2 className="w-8 h-8 animate-spin text-[#E31A1A]" /></div>;
  }

  return (
    <div className="min-h-screen bg-black text-white">
      {/* Header */}
      <header className="bg-gray-900 border-b border-gray-800 px-4 md:px-6 py-3 md:py-4 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2 md:gap-4">
            <Button variant="ghost" size="sm" onClick={() => navigate("/select-system")} className="text-gray-400 hover:text-white p-1 md:p-2">
              <ArrowLeft size={20} />
            </Button>
            <div className="flex items-center gap-2 md:gap-3">
              <div className="w-8 h-8 md:w-10 md:h-10 bg-[#E31A1A] rounded-lg flex items-center justify-center">
                <Shield className="text-white" size={18} />
              </div>
              <div>
                <h1 className="font-bold text-base md:text-lg">Painel Admin</h1>
                <p className="text-xs text-gray-400 hidden md:block">Gestão de usuários, auditoria e banco de dados</p>
              </div>
            </div>
          </div>
          <Badge variant="secondary" className="bg-gray-800 text-xs hidden sm:flex">{user?.name}</Badge>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 md:px-6 py-4 md:py-8">
        {/* Stats */}
        <div className="grid grid-cols-3 md:grid-cols-3 gap-2 md:gap-6 mb-4 md:mb-8">
          <Card className="bg-gray-900 border-gray-800">
            <CardContent className="p-3 md:p-6 flex flex-col md:flex-row items-center gap-2 md:gap-4">
              <div className="w-10 h-10 md:w-12 md:h-12 bg-[#E31A1A]/20 rounded-lg flex items-center justify-center">
                <Users className="text-[#E31A1A]" size={20} />
              </div>
              <div className="text-center md:text-left">
                <p className="text-xs text-gray-400">Usuários</p>
                <p className="text-xl md:text-2xl font-bold text-white">{users.length}</p>
              </div>
            </CardContent>
          </Card>
          <Card className="bg-gray-900 border-gray-800">
            <CardContent className="p-3 md:p-6 flex flex-col md:flex-row items-center gap-2 md:gap-4">
              <div className="w-10 h-10 md:w-12 md:h-12 bg-[#D4A000]/20 rounded-lg flex items-center justify-center">
                <Activity className="text-[#D4A000]" size={20} />
              </div>
              <div className="text-center md:text-left">
                <p className="text-xs text-gray-400">Atividades</p>
                <p className="text-xl md:text-2xl font-bold text-white">{auditLogs.filter(log => new Date(log.created_at).toDateString() === new Date().toDateString()).length}</p>
              </div>
            </CardContent>
          </Card>
          <Card className="bg-gray-900 border-gray-800">
            <CardContent className="p-3 md:p-6 flex flex-col md:flex-row items-center gap-2 md:gap-4">
              <div className="w-10 h-10 md:w-12 md:h-12 bg-green-500/20 rounded-lg flex items-center justify-center">
                <Database className="text-green-500" size={20} />
              </div>
              <div className="text-center md:text-left">
                <p className="text-xs text-gray-400">Coleções</p>
                <p className="text-xl md:text-2xl font-bold text-white">{COLLECTIONS.length}</p>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Tabs - Mobile optimized */}
        <div className="flex flex-wrap gap-2 mb-4 md:mb-6">
          <Button size="sm" variant={activeTab === "users" ? "default" : "outline"} className={activeTab === "users" ? "bg-[#E31A1A] hover:bg-red-700 text-white" : "bg-transparent border-gray-700 text-gray-400 hover:bg-gray-800"} onClick={() => setActiveTab("users")}>
            <Users size={16} className="mr-1 md:mr-2" /><span className="hidden sm:inline">Usuários</span><span className="sm:hidden">Usuários</span>
          </Button>
          <Button size="sm" variant={activeTab === "audit" ? "default" : "outline"} className={activeTab === "audit" ? "bg-[#D4A000] hover:bg-yellow-700 text-white" : "bg-transparent border-gray-700 text-gray-400 hover:bg-gray-800"} onClick={() => setActiveTab("audit")}>
            <Activity size={16} className="mr-1 md:mr-2" /><span className="hidden sm:inline">Auditoria</span><span className="sm:hidden">Auditoria</span>
          </Button>
          <Button size="sm" variant={activeTab === "database" ? "default" : "outline"} className={activeTab === "database" ? "bg-green-600 hover:bg-green-700 text-white" : "bg-transparent border-gray-700 text-gray-400 hover:bg-gray-800"} onClick={() => setActiveTab("database")}>
            <Database size={16} className="mr-1 md:mr-2" /><span className="hidden sm:inline">Banco de Dados</span><span className="sm:hidden">Banco</span>
          </Button>
          <Button size="sm" variant={activeTab === "tasks" ? "default" : "outline"} className={activeTab === "tasks" ? "bg-purple-600 hover:bg-purple-700 text-white" : "bg-transparent border-gray-700 text-gray-400 hover:bg-gray-800"} onClick={() => setActiveTab("tasks")}>
            <Send size={16} className="mr-1 md:mr-2" /><span className="hidden sm:inline">Lançar Tarefa</span><span className="sm:hidden">Tarefas</span>
          </Button>
          <Button size="sm" variant={activeTab === "integrations" ? "default" : "outline"} className={activeTab === "integrations" ? "bg-blue-600 hover:bg-blue-700 text-white" : "bg-transparent border-gray-700 text-gray-400 hover:bg-gray-800"} onClick={() => setActiveTab("integrations")} data-testid="tab-integracoes">
            <Cloud size={16} className="mr-1 md:mr-2" /><span className="hidden sm:inline">Integrações</span><span className="sm:hidden">Integrações</span>
          </Button>
        </div>

        {/* Users Tab */}
        {activeTab === "users" && (
          <>
            <div className="flex flex-col md:flex-row gap-4 mb-6">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" size={18} />
                <Input placeholder="Buscar usuários..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} className="pl-10 bg-gray-900 border-gray-700 text-white" />
              </div>
              <Button className="bg-[#D4A000] hover:bg-[#b38900] text-black">
                <Search size={16} className="mr-2" />
                Buscar
              </Button>
              <Button className="bg-[#E31A1A] hover:bg-red-700" onClick={() => setShowCreateModal(true)}>
                <Plus size={18} className="mr-2" />Novo Usuário
              </Button>
            </div>
            <Card className="bg-gray-900 border-gray-800">
              <CardContent className="p-0">
                <Table>
                  <TableHeader>
                    <TableRow className="border-gray-800">
                      <TableHead className="text-gray-400">Nome</TableHead>
                      <TableHead className="text-gray-400">Email</TableHead>
                      <TableHead className="text-gray-400">Tipo</TableHead>
                      <TableHead className="text-gray-400">Criado</TableHead>
                      <TableHead className="text-gray-400">Último acesso</TableHead>
                      <TableHead className="text-gray-400 text-right">Ações</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredUsers.map((u) => (
                      <TableRow key={u.id} className="border-gray-800 hover:bg-gray-800/50 cursor-pointer" onClick={() => fetchUserActivities(u.id, u.name, u.role)}>
                        <TableCell className="font-medium text-white">
                          <div className="flex items-center gap-3">
                            <div className="w-8 h-8 bg-gray-700 rounded-full flex items-center justify-center"><User size={16} className="text-gray-400" /></div>
                            {u.name}{u.id === user?.id && <Badge className="bg-[#E31A1A]/20 text-[#E31A1A] text-xs">Você</Badge>}
                          </div>
                        </TableCell>
                        <TableCell className="text-gray-400">{u.email}</TableCell>
                        <TableCell>{getRoleBadge(u.role)}</TableCell>
                        <TableCell className="text-gray-400">{formatDateShort(u.created_at)}</TableCell>
                        <TableCell className="text-gray-400">{formatDate(u.last_login) || "Nunca"}</TableCell>
                        <TableCell className="text-right">
                          <Button variant="ghost" size="sm" className="text-gray-400 hover:text-white" onClick={(e) => { e.stopPropagation(); fetchUserActivities(u.id, u.name, u.role); }} title="Ver atividades"><Eye size={16} /></Button>
                          <Button variant="ghost" size="sm" className="text-blue-400 hover:text-blue-300" onClick={(e) => { e.stopPropagation(); openEditRoleModal(u); }} title="Editar permissões"><Edit size={16} /></Button>
                          <Button variant="ghost" size="sm" className="text-amber-400 hover:text-amber-300" onClick={(e) => { e.stopPropagation(); handleResetPassword(u.id, u.name, u.email); }} title="Resetar senha" data-testid={`btn-reset-password-${u.id}`}><KeyRound size={16} /></Button>
                          {u.id !== user?.id && <Button variant="ghost" size="sm" className="text-red-400 hover:text-red-300" onClick={(e) => { e.stopPropagation(); handleDeleteUser(u.id, u.name); }} title="Excluir"><Trash2 size={16} /></Button>}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </>
        )}

        {/* Audit Tab */}
        {activeTab === "audit" && (
          <>
            <div className="flex flex-col md:flex-row gap-4 mb-6">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" size={18} />
                <Input placeholder="Buscar por usuário, ação, módulo..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} className="pl-10 bg-gray-900 border-gray-700 text-white" />
              </div>
            </div>
            <Card className="bg-gray-900 border-gray-800">
              <CardContent className="p-0">
                <Table>
                  <TableHeader>
                    <TableRow className="border-gray-800">
                      <TableHead className="text-gray-400">Data/Hora</TableHead>
                      <TableHead className="text-gray-400">Usuário</TableHead>
                      <TableHead className="text-gray-400">Módulo</TableHead>
                      <TableHead className="text-gray-400">Ação</TableHead>
                      <TableHead className="text-gray-400">Detalhes</TableHead>
                      <TableHead className="text-gray-400 text-right">Ver</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredLogs.slice(0, 100).map((log, index) => (
                      <TableRow key={log.id || index} className="border-gray-800 hover:bg-gray-800/50 cursor-pointer" onClick={() => openActivityDetail(log)}>
                        <TableCell className="text-gray-400 whitespace-nowrap"><Clock size={14} className="inline mr-2" />{formatDate(log.created_at)}</TableCell>
                        <TableCell><Badge className="bg-gray-700 text-white">{log.user_name || "Sistema"}</Badge></TableCell>
                        <TableCell>{getModuleBadge(log.module)}</TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <span className={`p-1.5 rounded ${getActionColor(log.action)}`}>{getActionIcon(log.action, log.entity_type)}</span>
                            <span className="text-white font-medium">{log.action}</span>
                          </div>
                        </TableCell>
                        <TableCell className="text-gray-400 max-w-xs truncate">{log.details || "-"}</TableCell>
                        <TableCell className="text-right"><Button variant="ghost" size="sm" className="text-gray-400 hover:text-white"><Info size={16} /></Button></TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </>
        )}

        {/* Database Tab */}
        {activeTab === "database" && (
          <>
            {/* Object Storage - Migração e backup ZIP */}
            <Card className="bg-gray-900 border-gray-800 mb-6">
              <CardHeader className="pb-3">
                <CardTitle className="text-white text-base flex items-center gap-2">
                  <Database size={18} className="text-amber-500" />
                  Armazenamento (Object Storage)
                </CardTitle>
                <p className="text-xs text-gray-400 mt-1">
                  Migre os arquivos do disco local para o Object Storage da Emergent (persistente entre deploys). Use Exportar ZIP no preview e Importar ZIP em produção para migração one-shot.
                </p>
              </CardHeader>
              <CardContent className="flex flex-wrap gap-2 pb-4">
                <Button
                  className="bg-amber-600 hover:bg-amber-700 text-white"
                  onClick={handleMigrateStorage}
                  disabled={storageMigrating}
                  data-testid="storage-migrate-btn"
                  title="Varre /app/backend/storage e move tudo para o Object Storage + MongoDB metadata."
                >
                  {storageMigrating ? <Loader2 size={16} className="mr-2 animate-spin" /> : <RefreshCw size={16} className="mr-2" />}
                  Migrar FS → Object Storage
                </Button>
                <Button
                  className="bg-blue-600 hover:bg-blue-700 text-white"
                  onClick={handleExportStorageZip}
                  disabled={storageExporting}
                  data-testid="storage-export-zip-btn"
                  title="Baixa um ZIP com TODO o conteúdo do storage (MongoDB+OS+FS legado)."
                >
                  {storageExporting ? <Loader2 size={16} className="mr-2 animate-spin" /> : <Download size={16} className="mr-2" />}
                  Exportar Storage (ZIP)
                </Button>
                <label className="inline-flex">
                  <input
                    type="file"
                    accept=".zip,application/zip"
                    className="hidden"
                    onChange={(e) => {
                      const f = e.target.files?.[0];
                      if (f) handleImportStorageZip(f);
                      e.target.value = "";
                    }}
                    data-testid="storage-import-zip-input"
                  />
                  <Button
                    asChild
                    className="bg-green-600 hover:bg-green-700 text-white cursor-pointer"
                    disabled={storageImporting}
                    data-testid="storage-import-zip-btn"
                    title="Sobe um ZIP (gerado pelo Exportar Storage) para popular MongoDB + Object Storage."
                  >
                    <span>
                      {storageImporting ? <Loader2 size={16} className="mr-2 animate-spin" /> : <Plus size={16} className="mr-2" />}
                      Importar Storage (ZIP)
                    </span>
                  </Button>
                </label>
              </CardContent>
            </Card>

            <div className="flex flex-col md:flex-row gap-4 mb-6">
              <Select value={selectedCollection} onValueChange={(v) => { setSelectedCollection(v); setDbPage(1); }}>
                <SelectTrigger className="w-[250px] bg-gray-900 border-gray-700 text-white">
                  <SelectValue placeholder="Selecione a coleção" />
                </SelectTrigger>
                <SelectContent className="bg-gray-800 border-gray-700">
                  {COLLECTIONS.map(c => (
                    <SelectItem key={c.id} value={c.id} className="text-white hover:bg-gray-700">
                      <div className="flex items-center gap-2"><c.icon size={16} />{c.label}</div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" size={18} />
                <Input placeholder="Buscar documentos..." value={dbSearchTerm} onChange={(e) => setDbSearchTerm(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && fetchDbDocuments()} className="pl-10 bg-gray-900 border-gray-700 text-white" />
              </div>
              <Button variant="outline" className="bg-transparent border-gray-700 text-gray-400 hover:bg-gray-800" onClick={fetchDbDocuments}>
                <RefreshCw size={18} className={dbLoading ? "animate-spin" : ""} />
              </Button>
              <Button
                className="bg-blue-600 hover:bg-blue-700 text-white"
                onClick={handleExportDatabase}
                disabled={dbExportLoading}
                data-testid="db-export-full-btn"
                title="Baixa um ZIP com todo o banco de dados (dump.json + schema.json + MANIFEST.md + DDL Postgres). Útil para migrar/auditar."
              >
                {dbExportLoading
                  ? <Loader2 size={18} className="mr-2 animate-spin" />
                  : <Download size={18} className="mr-2" />}
                <span className="hidden md:inline">Exportar Banco</span>
                <span className="md:hidden">Backup</span>
              </Button>
              <Button className="bg-[#E31A1A] hover:bg-red-700" onClick={() => setShowAddDocModal(true)}>
                <Plus size={18} className="mr-2" />Adicionar
              </Button>
            </div>

            <Card className="bg-gray-900 border-gray-800">
              <CardContent className="p-0">
                {dbLoading ? (
                  <div className="flex items-center justify-center py-12"><Loader2 className="w-8 h-8 animate-spin text-[#E31A1A]" /></div>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow className="border-gray-800">
                        <TableHead className="text-gray-400">ID</TableHead>
                        <TableHead className="text-gray-400">Dados</TableHead>
                        <TableHead className="text-gray-400">Criado</TableHead>
                        <TableHead className="text-gray-400 text-right">Ações</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {dbDocuments.map((doc, index) => (
                        <TableRow key={doc.id || doc._id || index} className="border-gray-800 hover:bg-gray-800/50 cursor-pointer" onClick={() => handleViewDoc(doc)}>
                          <TableCell className="font-mono text-xs text-gray-400">{(doc.id || doc._id || "").toString().slice(0, 12)}...</TableCell>
                          <TableCell className="text-white max-w-md truncate">{doc.name || doc.email || doc.titulo || doc.descricao || doc.action || JSON.stringify(doc).slice(0, 60)}...</TableCell>
                          <TableCell className="text-gray-400">{formatDateShort(doc.created_at)}</TableCell>
                          <TableCell className="text-right">
                            <Button variant="ghost" size="sm" className="text-gray-400 hover:text-white" onClick={(e) => { e.stopPropagation(); handleViewDoc(doc); }}><Eye size={16} /></Button>
                            <Button variant="ghost" size="sm" className="text-red-400 hover:text-red-300" onClick={(e) => { e.stopPropagation(); handleDeleteDoc(doc.id || doc._id); }}><Trash2 size={16} /></Button>
                          </TableCell>
                        </TableRow>
                      ))}
                      {dbDocuments.length === 0 && (
                        <TableRow><TableCell colSpan={4} className="text-center text-gray-500 py-8">Nenhum documento encontrado</TableCell></TableRow>
                      )}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>

            {/* Pagination */}
            <div className="flex items-center justify-between mt-4">
              <p className="text-sm text-gray-400">Total: {dbTotal} documentos</p>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" className="bg-transparent border-gray-700 text-gray-400" disabled={dbPage === 1} onClick={() => setDbPage(p => p - 1)}>
                  <ChevronLeft size={16} />
                </Button>
                <span className="text-gray-400 px-3 py-1">Página {dbPage}</span>
                <Button variant="outline" size="sm" className="bg-transparent border-gray-700 text-gray-400" disabled={dbDocuments.length < 20} onClick={() => setDbPage(p => p + 1)}>
                  <ChevronRight size={16} />
                </Button>
              </div>
            </div>
          </>
        )}

        {/* Tasks Tab */}
        {activeTab === "tasks" && (
          <div className="grid lg:grid-cols-2 gap-6">
            {/* Create Task Form */}
            <Card className="bg-gray-900 border-gray-700">
              <CardContent className="p-4 md:p-6">
                <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                  <Send size={20} className="text-purple-500" />
                  Nova Tarefa
                </h3>

                <div className="space-y-4">
                  {/* Target System */}
                  <div>
                    <Label className="text-gray-400 mb-2 block">Sistema Destino</Label>
                    <div className="grid grid-cols-2 gap-2">
                      {Object.entries(TARGET_SYSTEMS).map(([key, { label, color }]) => (
                        <Button
                          key={key}
                          type="button"
                          variant={taskForm.target_system === key ? "default" : "outline"}
                          className={taskForm.target_system === key 
                            ? `${color} text-white` 
                            : "bg-transparent border-gray-700 text-gray-400 hover:bg-gray-800"}
                          onClick={() => setTaskForm({ ...taskForm, target_system: key })}
                        >
                          {label}
                        </Button>
                      ))}
                    </div>
                  </div>

                  {/* Priority */}
                  <div>
                    <Label className="text-gray-400 mb-2 block">Prioridade</Label>
                    <div className="grid grid-cols-3 gap-2">
                      {Object.entries(PRIORITIES).map(([key, { label, color, icon: Icon }]) => (
                        <Button
                          key={key}
                          type="button"
                          variant={taskForm.priority === key ? "default" : "outline"}
                          className={taskForm.priority === key 
                            ? `${color} text-white` 
                            : "bg-transparent border-gray-700 text-gray-400 hover:bg-gray-800"}
                          onClick={() => setTaskForm({ ...taskForm, priority: key })}
                        >
                          <Icon size={14} className="mr-1" />
                          {label}
                        </Button>
                      ))}
                    </div>
                  </div>

                  {/* Title */}
                  <div>
                    <Label className="text-gray-400">Título</Label>
                    <Input
                      value={taskForm.title}
                      onChange={(e) => setTaskForm({ ...taskForm, title: e.target.value })}
                      placeholder="Ex: Verificar estoque de peças"
                      className="bg-gray-800 border-gray-700 text-white"
                    />
                  </div>

                  {/* Message */}
                  <div>
                    <Label className="text-gray-400">Mensagem</Label>
                    <Textarea
                      value={taskForm.message}
                      onChange={(e) => setTaskForm({ ...taskForm, message: e.target.value })}
                      placeholder="Descreva a tarefa em detalhes..."
                      className="bg-gray-800 border-gray-700 text-white min-h-[120px]"
                    />
                  </div>

                  {/* Attachments */}
                  <div>
                    <Label className="text-gray-400 mb-2 block">Anexos (máx. 100MB cada)</Label>
                    <div className="flex flex-wrap gap-2 mb-2">
                      {taskAttachments.map((file, index) => (
                        <div key={index} className="flex items-center gap-2 bg-gray-800 rounded-lg px-3 py-2 text-sm">
                          <Paperclip size={14} className="text-gray-400" />
                          <span className="text-white truncate max-w-[150px]">{file.name}</span>
                          <span className="text-gray-500 text-xs">({formatFileSize(file.size)})</span>
                          <button onClick={() => removeTaskAttachment(index)} className="text-red-400 hover:text-red-300">
                            <XIcon size={14} />
                          </button>
                        </div>
                      ))}
                    </div>
                    <label className="cursor-pointer">
                      <input
                        type="file"
                        multiple
                        onChange={handleTaskFileSelect}
                        className="hidden"
                      />
                      <div className="flex items-center gap-2 text-purple-400 hover:text-purple-300 text-sm">
                        <Paperclip size={16} />
                        <span>Adicionar anexo</span>
                      </div>
                    </label>
                  </div>

                  {/* Submit */}
                  <Button
                    onClick={handleCreateTask}
                    disabled={creatingTask || !taskForm.title.trim() || !taskForm.message.trim()}
                    className="w-full bg-purple-600 hover:bg-purple-700"
                  >
                    {creatingTask ? (
                      <><Loader2 size={18} className="mr-2 animate-spin" />Enviando...</>
                    ) : (
                      <><Send size={18} className="mr-2" />Enviar Tarefa</>
                    )}
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Tasks History */}
            <Card className="bg-gray-900 border-gray-700">
              <CardContent className="p-4 md:p-6">
                <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                  <Inbox size={20} className="text-purple-500" />
                  Histórico de Tarefas
                </h3>

                {tasksLoading ? (
                  <div className="text-center py-8">
                    <Loader2 className="w-8 h-8 animate-spin mx-auto text-purple-500" />
                  </div>
                ) : tasks.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <Inbox size={48} className="mx-auto mb-2 opacity-50" />
                    <p>Nenhuma tarefa enviada</p>
                  </div>
                ) : (
                  <div className="space-y-3 max-h-[500px] overflow-y-auto">
                    {tasks.map((task) => {
                      const PriorityIcon = PRIORITIES[task.priority]?.icon || Info;
                      return (
                        <div
                          key={task.id}
                          className="bg-gray-800 rounded-lg p-4 border border-gray-700 hover:border-gray-600 cursor-pointer"
                          onClick={() => { setSelectedTask(task); setShowTaskDetailModal(true); }}
                        >
                          <div className="flex items-start gap-3">
                            <div className={`p-2 rounded-full ${PRIORITIES[task.priority]?.color} shrink-0`}>
                              <PriorityIcon size={14} className="text-white" />
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 flex-wrap mb-1">
                                <h4 className="font-medium text-white truncate">{task.title}</h4>
                                <Badge className={`${TARGET_SYSTEMS[task.target_system]?.color} text-white text-xs`}>
                                  {TARGET_SYSTEMS[task.target_system]?.label}
                                </Badge>
                                {task.read && (
                                  <Badge variant="outline" className="text-green-400 border-green-600 text-xs">Lida</Badge>
                                )}
                              </div>
                              <p className="text-sm text-gray-400 truncate">{task.message}</p>
                              <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
                                <span>{new Date(task.created_at).toLocaleString("pt-BR")}</span>
                                {task.attachments?.length > 0 && (
                                  <span className="flex items-center gap-1">
                                    <Paperclip size={12} />
                                    {task.attachments.length}
                                  </span>
                                )}
                              </div>
                            </div>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="text-red-400 hover:text-red-300 hover:bg-red-900/30 shrink-0"
                              onClick={(e) => { e.stopPropagation(); handleDeleteTask(task.id); }}
                            >
                              <Trash2 size={16} />
                            </Button>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        )}

        {/* Integrations Tab */}
        {activeTab === "integrations" && (
          <div className="space-y-4" data-testid="integrations-tab-content">
            <div className="mb-4">
              <h3 className="text-lg font-bold text-white mb-1 flex items-center gap-2">
                <Cloud size={20} className="text-blue-500" />
                Integrações Externas
              </h3>
              <p className="text-sm text-gray-400">
                Conecte serviços externos para estender as funcionalidades do sistema.
              </p>
            </div>
            <DriveConnectionCard />
          </div>
        )}
      </main>

      {/* Edit Role Modal */}
      <Dialog open={showEditRoleModal} onOpenChange={setShowEditRoleModal}>
        <DialogContent className="bg-gray-900 border-gray-800 text-white">
          <DialogHeader>
            <DialogTitle>
              <Edit size={20} className="inline mr-2 text-blue-400" />
              Editar Permissões
            </DialogTitle>
          </DialogHeader>
          {editingUser && (
            <div className="space-y-4">
              <div className="bg-gray-800 rounded-lg p-4">
                <p className="text-white font-medium">{editingUser.name}</p>
                <p className="text-gray-400 text-sm">{editingUser.email}</p>
                <p className="text-gray-500 text-xs mt-1">Permissão atual: {USER_ROLES[editingUser.role]?.label || editingUser.role}</p>
              </div>
              
              <div>
                <Label className="text-gray-400 mb-2 block">Nova Permissão</Label>
                <Select value={newRole} onValueChange={setNewRole}>
                  <SelectTrigger className="bg-gray-800 border-gray-700 text-white">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-gray-800 border-gray-700">
                    <SelectItem value="gerenciamento" className="text-white">
                      <span className="flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-[#E31A1A]"></span>
                        Gerenciamento
                      </span>
                    </SelectItem>
                    <SelectItem value="administrativo" className="text-white">
                      <span className="flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-[#D4A000]"></span>
                        Administrativo
                      </span>
                    </SelectItem>
                    <SelectItem value="rh" className="text-white">
                      <span className="flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-[#10B981]"></span>
                        RH
                      </span>
                    </SelectItem>
                    <SelectItem value="ambos" className="text-white">
                      <span className="flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-purple-500"></span>
                        Gerenciamento + Administrativo
                      </span>
                    </SelectItem>
                    <SelectItem value="gerenciamento_rh" className="text-white">
                      <span className="flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-pink-500"></span>
                        Gerenciamento + RH
                      </span>
                    </SelectItem>
                    <SelectItem value="administrativo_rh" className="text-white">
                      <span className="flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-orange-500"></span>
                        Administrativo + RH
                      </span>
                    </SelectItem>
                    <SelectItem value="ambos_rh" className="text-white">
                      <span className="flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-purple-600"></span>
                        Ger + Admin + RH
                      </span>
                    </SelectItem>
                    <SelectItem value="admin" className="text-white">
                      <span className="flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-green-500"></span>
                        Administrador (Acesso Total)
                      </span>
                    </SelectItem>
                    <SelectItem value="programador" className="text-white">
                      <span className="flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-blue-600"></span>
                        Programador (Acesso Total)
                      </span>
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <DialogFooter>
                <Button variant="outline" onClick={() => setShowEditRoleModal(false)} className="bg-transparent border-gray-700 text-gray-400">
                  Cancelar
                </Button>
                <Button onClick={handleUpdateRole} className="bg-blue-600 hover:bg-blue-700" disabled={updatingRole}>
                  {updatingRole ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Edit size={18} className="mr-2" />}
                  Salvar
                </Button>
              </DialogFooter>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Create User Modal */}
      <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
        <DialogContent className="bg-gray-900 border-gray-800 text-white">
          <DialogHeader><DialogTitle><Plus size={20} className="inline mr-2 text-[#E31A1A]" />Criar Novo Usuário</DialogTitle></DialogHeader>
          <form onSubmit={handleCreateUser} className="space-y-4">
            <div><Label className="text-gray-400">Nome</Label><Input value={createForm.name} onChange={(e) => setCreateForm({...createForm, name: e.target.value})} className="bg-gray-800 border-gray-700 text-white" required /></div>
            <div><Label className="text-gray-400">Email</Label><Input type="email" value={createForm.email} onChange={(e) => setCreateForm({...createForm, email: e.target.value})} className="bg-gray-800 border-gray-700 text-white" required /></div>
            <div>
              <Label className="text-gray-400">Tipo de Acesso</Label>
              <Select value={createForm.role} onValueChange={(v) => setCreateForm({...createForm, role: v})}>
                <SelectTrigger className="bg-gray-800 border-gray-700 text-white"><SelectValue /></SelectTrigger>
                <SelectContent className="bg-gray-800 border-gray-700">
                  <SelectItem value="gerenciamento" className="text-white">Gerenciamento</SelectItem>
                  <SelectItem value="administrativo" className="text-white">Administrativo</SelectItem>
                  <SelectItem value="rh" className="text-white">RH</SelectItem>
                  <SelectItem value="ambos" className="text-white">Gerenciamento + Administrativo</SelectItem>
                  <SelectItem value="gerenciamento_rh" className="text-white">Gerenciamento + RH</SelectItem>
                  <SelectItem value="administrativo_rh" className="text-white">Administrativo + RH</SelectItem>
                  <SelectItem value="ambos_rh" className="text-white">Ger + Admin + RH</SelectItem>
                  <SelectItem value="admin" className="text-white">Administrador (Acesso Total)</SelectItem>
                  <SelectItem value="programador" className="text-white">Programador (Acesso Total)</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div><Label className="text-gray-400">Senha</Label><Input type="password" value={createForm.password} onChange={(e) => setCreateForm({...createForm, password: e.target.value})} className="bg-gray-800 border-gray-700 text-white" required /></div>
            <div><Label className="text-gray-400">Confirmar Senha</Label><Input type="password" value={createForm.confirmPassword} onChange={(e) => setCreateForm({...createForm, confirmPassword: e.target.value})} className="bg-gray-800 border-gray-700 text-white" required /></div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setShowCreateModal(false)} className="bg-transparent border-gray-700 text-gray-400">Cancelar</Button>
              <Button type="submit" className="bg-[#E31A1A] hover:bg-red-700" disabled={creating}>{creating ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Plus size={18} className="mr-2" />}Criar</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Activities Modal */}
      <Dialog open={showActivitiesModal} onOpenChange={setShowActivitiesModal}>
        <DialogContent className="bg-gray-900 border-gray-800 text-white max-w-2xl max-h-[80vh] overflow-hidden flex flex-col">
          <DialogHeader><DialogTitle><Activity size={20} className="inline mr-2 text-[#D4A000]" />Atividades de {selectedUser?.name}</DialogTitle></DialogHeader>
          <div className="flex-1 overflow-y-auto">
            {userActivities.length > 0 ? userActivities.map((activity, index) => (
              <div key={index} className="bg-gray-800 rounded-lg p-4 border border-gray-700 mb-3 cursor-pointer hover:border-gray-600" onClick={() => openActivityDetail(activity)}>
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-start gap-3 flex-1">
                    <span className={`p-2 rounded-lg shrink-0 ${getActionColor(activity.action)}`}>{getActionIcon(activity.action, activity.entity_type)}</span>
                    <div className="min-w-0">
                      <div className="flex items-center gap-2 flex-wrap mb-1">
                        <p className="text-white font-medium">{activity.action}</p>
                        {activity.module && getModuleBadge(activity.module)}
                      </div>
                      <p className="text-sm text-gray-400 break-words">{activity.details || "Sem detalhes"}</p>
                    </div>
                  </div>
                  <span className="text-xs text-gray-500 whitespace-nowrap shrink-0">{formatDate(activity.created_at)}</span>
                </div>
              </div>
            )) : <div className="text-center py-8 text-gray-500"><Activity size={40} className="mx-auto mb-4 opacity-50" /><p>Nenhuma atividade registrada</p></div>}
          </div>
          <DialogFooter><Button variant="outline" onClick={() => setShowActivitiesModal(false)} className="bg-transparent border-gray-700 text-gray-400">Fechar</Button></DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Activity Detail Modal */}
      <Dialog open={showActivityDetailModal} onOpenChange={setShowActivityDetailModal}>
        <DialogContent className="bg-gray-900 border-gray-800 text-white max-w-lg">
          <DialogHeader><DialogTitle><Info size={20} className="inline mr-2 text-[#D4A000]" />Detalhes da Atividade</DialogTitle></DialogHeader>
          {selectedActivity && (
            <div className="space-y-4">
              <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
                <div className="flex items-start gap-3 mb-4">
                  <span className={`p-3 rounded-lg shrink-0 ${getActionColor(selectedActivity.action)}`}>{getActionIcon(selectedActivity.action, selectedActivity.entity_type)}</span>
                  <div>
                    <p className="text-white font-bold text-lg">{selectedActivity.action}</p>
                    <p className="text-sm text-gray-400">Por: {selectedActivity.user_name || "Sistema"}</p>
                  </div>
                </div>
                <div className="space-y-3 text-sm">
                  <div className="flex items-center gap-2">
                    <Calendar size={14} className="text-gray-400 shrink-0" />
                    <span className="text-gray-400">Data:</span>
                    <span className="text-white">{formatDate(selectedActivity.created_at)}</span>
                  </div>
                  {selectedActivity.module && (
                    <div className="flex items-center gap-2">
                      <Building2 size={14} className="text-gray-400 shrink-0" />
                      <span className="text-gray-400">Módulo:</span>
                      {getModuleBadge(selectedActivity.module)}
                    </div>
                  )}
                  {selectedActivity.entity_name && (
                    <div className="flex items-center gap-2">
                      <FileText size={14} className="text-gray-400 shrink-0" />
                      <span className="text-gray-400">Item:</span>
                      <span className="text-white">{selectedActivity.entity_name}</span>
                    </div>
                  )}
                  {selectedActivity.user_id && (
                    <div className="flex items-center gap-2">
                      <User size={14} className="text-gray-400 shrink-0" />
                      <span className="text-gray-400">User ID:</span>
                      <span className="text-white font-mono text-xs">{selectedActivity.user_id}</span>
                    </div>
                  )}
                </div>
              </div>
              {selectedActivity.details && (
                <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
                  <p className="text-sm text-gray-400 mb-2">Descrição Completa:</p>
                  <p className="text-white whitespace-pre-wrap">{selectedActivity.details}</p>
                </div>
              )}
            </div>
          )}
          <DialogFooter><Button variant="outline" onClick={() => setShowActivityDetailModal(false)} className="bg-transparent border-gray-700 text-gray-400">Fechar</Button></DialogFooter>
        </DialogContent>
      </Dialog>

      {/* View/Edit Document Modal */}
      <Dialog open={showDocModal} onOpenChange={setShowDocModal}>
        <DialogContent className="bg-gray-900 border-gray-800 text-white max-w-2xl max-h-[80vh] overflow-hidden flex flex-col">
          <DialogHeader>
            <DialogTitle className="flex items-center justify-between">
              <span><Database size={20} className="inline mr-2 text-green-500" />{docEditMode ? "Editar" : "Visualizar"} Documento</span>
              <Button variant="ghost" size="sm" onClick={() => setDocEditMode(!docEditMode)} className="text-gray-400 hover:text-white"><Edit size={16} className="mr-1" />{docEditMode ? "Visualizar" : "Editar"}</Button>
            </DialogTitle>
          </DialogHeader>
          <div className="flex-1 overflow-hidden">
            <Textarea value={docJson} onChange={(e) => setDocJson(e.target.value)} readOnly={!docEditMode} className={`h-[400px] font-mono text-sm bg-gray-800 border-gray-700 text-white resize-none ${!docEditMode && 'opacity-80'}`} />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDocModal(false)} className="bg-transparent border-gray-700 text-gray-400">Fechar</Button>
            {docEditMode && <Button className="bg-[#E31A1A] hover:bg-red-700" onClick={handleUpdateDoc}>Salvar</Button>}
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Add Document Modal */}
      <Dialog open={showAddDocModal} onOpenChange={setShowAddDocModal}>
        <DialogContent className="bg-gray-900 border-gray-800 text-white max-w-2xl">
          <DialogHeader><DialogTitle><Plus size={20} className="inline mr-2 text-green-500" />Adicionar Documento em {selectedCollection}</DialogTitle></DialogHeader>
          <Textarea value={newDocJson} onChange={(e) => setNewDocJson(e.target.value)} className="h-[300px] font-mono text-sm bg-gray-800 border-gray-700 text-white" placeholder='{"campo": "valor"}' />
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowAddDocModal(false)} className="bg-transparent border-gray-700 text-gray-400">Cancelar</Button>
            <Button className="bg-[#E31A1A] hover:bg-red-700" onClick={handleAddDoc}><Plus size={18} className="mr-2" />Adicionar</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Task Detail Modal */}
      <Dialog open={showTaskDetailModal} onOpenChange={setShowTaskDetailModal}>
        <DialogContent className="bg-gray-900 border-gray-800 text-white max-w-2xl max-h-[80vh] overflow-hidden flex flex-col">
          {selectedTask && (
            <>
              <DialogHeader>
                <div className="flex items-start gap-3">
                  <div className={`p-2 rounded-full ${PRIORITIES[selectedTask.priority]?.color} shrink-0`}>
                    {(() => {
                      const PriorityIcon = PRIORITIES[selectedTask.priority]?.icon || Info;
                      return <PriorityIcon size={20} className="text-white" />;
                    })()}
                  </div>
                  <div className="flex-1">
                    <DialogTitle className="text-lg">{selectedTask.title}</DialogTitle>
                    <div className="flex items-center gap-2 mt-1">
                      <Badge className={`${TARGET_SYSTEMS[selectedTask.target_system]?.color} text-white`}>
                        {TARGET_SYSTEMS[selectedTask.target_system]?.label}
                      </Badge>
                      <Badge className={PRIORITIES[selectedTask.priority]?.color}>
                        Prioridade {PRIORITIES[selectedTask.priority]?.label}
                      </Badge>
                      {selectedTask.read && (
                        <Badge variant="outline" className="text-green-400 border-green-600">Lida</Badge>
                      )}
                    </div>
                  </div>
                </div>
              </DialogHeader>

              <div className="flex-1 overflow-y-auto space-y-4 py-4">
                {/* Message */}
                <div className="bg-gray-800 rounded-lg p-4">
                  <p className="whitespace-pre-wrap text-gray-300">{selectedTask.message}</p>
                </div>

                {/* Attachments */}
                {selectedTask.attachments?.length > 0 && (
                  <div>
                    <h4 className="font-medium mb-3 flex items-center gap-2 text-white">
                      <Paperclip size={18} />
                      Anexos ({selectedTask.attachments.length})
                    </h4>
                    <div className="space-y-2">
                      {selectedTask.attachments.map((att) => (
                        <div
                          key={att.id}
                          className="flex items-center justify-between p-3 bg-gray-800 rounded-lg border border-gray-700"
                        >
                          <div className="flex items-center gap-3">
                            <Paperclip size={18} className="text-gray-400" />
                            <div>
                              <p className="font-medium text-sm text-white">{att.original_name}</p>
                              <p className="text-xs text-gray-500">{formatFileSize(att.size)}</p>
                            </div>
                          </div>
                          <a
                            href={`${API}/tasks/${selectedTask.id}/attachments/${att.filename}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center gap-1 text-purple-400 hover:text-purple-300 text-sm"
                          >
                            <Download size={16} />
                            Baixar
                          </a>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Meta info */}
                <div className="text-xs text-gray-500 border-t border-gray-700 pt-3 space-y-1">
                  <p>Criada em: {new Date(selectedTask.created_at).toLocaleString("pt-BR")}</p>
                  {selectedTask.read && selectedTask.read_at && (
                    <p className="text-green-400">Lida por {selectedTask.read_by} em {new Date(selectedTask.read_at).toLocaleString("pt-BR")}</p>
                  )}
                </div>
              </div>

              <DialogFooter>
                <Button variant="outline" onClick={() => setShowTaskDetailModal(false)} className="bg-transparent border-gray-700 text-gray-400">
                  Fechar
                </Button>
              </DialogFooter>
            </>
          )}
        </DialogContent>
      </Dialog>

      {/* Modal de Senha Resetada */}
      <Dialog open={!!resetPasswordResult} onOpenChange={(o) => !o && setResetPasswordResult(null)}>
        <DialogContent className="bg-gray-900 border-gray-800 text-white max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-amber-400">
              <KeyRound size={20} />
              Senha resetada
            </DialogTitle>
          </DialogHeader>
          {resetPasswordResult && (
            <div className="space-y-4">
              <div className="rounded-lg bg-amber-500/10 border border-amber-500/30 p-4">
                <p className="text-sm text-amber-200 mb-2">
                  <strong>{resetPasswordResult.name}</strong> ({resetPasswordResult.email})
                </p>
                <p className="text-xs text-amber-300/80 mb-3">
                  {resetPasswordResult.gerada
                    ? "Senha gerada automaticamente. Compartilhe com o usuário por canal seguro."
                    : "Senha definida manualmente conforme você digitou."}
                </p>
                <div className="flex items-center gap-2 bg-gray-950 rounded p-3 font-mono text-sm">
                  <code className="flex-1 break-all text-emerald-300" data-testid="reset-password-value">
                    {resetPasswordResult.password}
                  </code>
                  <Button
                    size="sm"
                    variant="ghost"
                    className="text-amber-400 hover:text-amber-300 hover:bg-amber-500/10"
                    onClick={() => {
                      navigator.clipboard.writeText(resetPasswordResult.password);
                      toast.success("Senha copiada para a área de transferência");
                    }}
                    data-testid="btn-copy-reset-password"
                  >
                    <Copy size={14} />
                  </Button>
                </div>
              </div>
              <p className="text-xs text-gray-400 italic">
                ⚠️ Esta é a única vez que a senha em texto puro será exibida. Anote ou copie agora.
              </p>
              <DialogFooter>
                <Button
                  onClick={() => setResetPasswordResult(null)}
                  className="bg-amber-600 hover:bg-amber-700 text-white border-0"
                  data-testid="btn-fechar-reset-modal"
                >
                  Entendi
                </Button>
              </DialogFooter>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Chatbot Widget */}
      <ChatbotWidget module="admin" accentColor="#9333ea" />
    </div>
  );
}
