import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth, API } from "@/App";
import axios from "axios";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent } from "@/components/ui/card";
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
  Search,
  Building2,
  Crown,
  Info,
  Database,
  RefreshCw,
  Edit,
  ChevronLeft,
  ChevronRight
} from "lucide-react";

// Tipos de usuário
const USER_ROLES = {
  gerenciamento: { label: "Gerenciamento Geral", icon: Wrench, color: "bg-[#E31A1A]" },
  administrativo: { label: "Administrativo", icon: Building2, color: "bg-[#D4A000]" },
  ambos: { label: "Gerenciamento + Administrativo", icon: Users, color: "bg-purple-500" },
  admin: { label: "Administrador", icon: Crown, color: "bg-green-500" }
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

  useEffect(() => {
    fetchUsers();
    fetchAuditLogs();
  }, []);

  useEffect(() => {
    if (activeTab === "database") {
      fetchDbDocuments();
    }
  }, [activeTab, selectedCollection, dbPage]);

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
      "Gerenciamento Geral": "bg-[#E31A1A] text-white",
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
      <header className="bg-gray-900 border-b border-gray-800 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="sm" onClick={() => navigate("/select-system")} className="text-gray-400 hover:text-white">
              <ArrowLeft size={20} />
            </Button>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-[#E31A1A] rounded-lg flex items-center justify-center">
                <Shield className="text-white" size={20} />
              </div>
              <div>
                <h1 className="font-bold text-lg">Painel Administrativo</h1>
                <p className="text-xs text-gray-400">Gestão de usuários, auditoria e banco de dados</p>
              </div>
            </div>
          </div>
          <Badge variant="secondary" className="bg-gray-800">{user?.name}</Badge>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <Card className="bg-gray-900 border-gray-800">
            <CardContent className="p-6 flex items-center gap-4">
              <div className="w-12 h-12 bg-[#E31A1A]/20 rounded-lg flex items-center justify-center">
                <Users className="text-[#E31A1A]" size={24} />
              </div>
              <div>
                <p className="text-sm text-gray-400">Total de Usuários</p>
                <p className="text-2xl font-bold text-white">{users.length}</p>
              </div>
            </CardContent>
          </Card>
          <Card className="bg-gray-900 border-gray-800">
            <CardContent className="p-6 flex items-center gap-4">
              <div className="w-12 h-12 bg-[#D4A000]/20 rounded-lg flex items-center justify-center">
                <Activity className="text-[#D4A000]" size={24} />
              </div>
              <div>
                <p className="text-sm text-gray-400">Atividades Hoje</p>
                <p className="text-2xl font-bold text-white">{auditLogs.filter(log => new Date(log.created_at).toDateString() === new Date().toDateString()).length}</p>
              </div>
            </CardContent>
          </Card>
          <Card className="bg-gray-900 border-gray-800">
            <CardContent className="p-6 flex items-center gap-4">
              <div className="w-12 h-12 bg-green-500/20 rounded-lg flex items-center justify-center">
                <Database className="text-green-500" size={24} />
              </div>
              <div>
                <p className="text-sm text-gray-400">Coleções</p>
                <p className="text-2xl font-bold text-white">{COLLECTIONS.length}</p>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 mb-6 flex-wrap">
          <Button variant={activeTab === "users" ? "default" : "outline"} className={activeTab === "users" ? "bg-[#E31A1A] hover:bg-red-700" : "bg-transparent border-gray-700 text-gray-400 hover:bg-gray-800"} onClick={() => setActiveTab("users")}>
            <Users size={18} className="mr-2" />Usuários
          </Button>
          <Button variant={activeTab === "audit" ? "default" : "outline"} className={activeTab === "audit" ? "bg-[#E31A1A] hover:bg-red-700" : "bg-transparent border-gray-700 text-gray-400 hover:bg-gray-800"} onClick={() => setActiveTab("audit")}>
            <Activity size={18} className="mr-2" />Auditoria
          </Button>
          <Button variant={activeTab === "database" ? "default" : "outline"} className={activeTab === "database" ? "bg-[#E31A1A] hover:bg-red-700" : "bg-transparent border-gray-700 text-gray-400 hover:bg-gray-800"} onClick={() => setActiveTab("database")}>
            <Database size={18} className="mr-2" />Banco de Dados
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
                          <Button variant="ghost" size="sm" className="text-gray-400 hover:text-white" onClick={(e) => { e.stopPropagation(); fetchUserActivities(u.id, u.name, u.role); }}><Eye size={16} /></Button>
                          {u.id !== user?.id && <Button variant="ghost" size="sm" className="text-red-400 hover:text-red-300" onClick={(e) => { e.stopPropagation(); handleDeleteUser(u.id, u.name); }}><Trash2 size={16} /></Button>}
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
      </main>

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
                  <SelectItem value="gerenciamento" className="text-white">Gerenciamento Geral</SelectItem>
                  <SelectItem value="administrativo" className="text-white">Administrativo</SelectItem>
                  <SelectItem value="ambos" className="text-white">Gerenciamento + Administrativo</SelectItem>
                  <SelectItem value="admin" className="text-white">Administrador (Acesso Total)</SelectItem>
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

      {/* Chatbot Widget */}
      <ChatbotWidget module="admin" accentColor="#9333ea" />
    </div>
  );
}
