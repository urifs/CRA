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
  Landmark,
  Crown,
  Info
} from "lucide-react";

// Tipos de usuário
const USER_ROLES = {
  gerenciamento: { label: "Gerenciamento Geral", icon: Landmark, color: "bg-[#E31A1A]" },
  administrativo: { label: "Administrativo", icon: Building2, color: "bg-[#D4A000]" },
  ambos: { label: "Gerenciamento + Administrativo", icon: Users, color: "bg-purple-500" },
  admin: { label: "Administrador", icon: Crown, color: "bg-green-500" }
};

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

  useEffect(() => {
    fetchUsers();
    fetchAuditLogs();
  }, []);

  const fetchUsers = async () => {
    try {
      const response = await axios.get(`${API}/admin-panel/users`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setUsers(response.data);
    } catch (error) {
      console.error("Erro ao carregar usuários:", error);
      toast.error("Erro ao carregar usuários");
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

  const fetchUserActivities = async (userId, userName, userRole) => {
    try {
      const response = await axios.get(`${API}/admin-panel/users/${userId}/activities`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setUserActivities(response.data);
      setSelectedUser({ id: userId, name: userName, role: userRole });
      setShowActivitiesModal(true);
    } catch (error) {
      console.error("Erro ao carregar atividades:", error);
      toast.error("Erro ao carregar atividades do usuário");
    }
  };

  const handleCreateUser = async (e) => {
    e.preventDefault();
    
    if (createForm.password !== createForm.confirmPassword) {
      toast.error("As senhas não coincidem");
      return;
    }

    if (createForm.password.length < 6) {
      toast.error("A senha deve ter pelo menos 6 caracteres");
      return;
    }

    setCreating(true);
    try {
      await axios.post(`${API}/admin-panel/users`, {
        name: createForm.name,
        email: createForm.email,
        password: createForm.password,
        role: createForm.role
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success("Usuário criado com sucesso!");
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
    if (userId === user?.id) {
      toast.error("Você não pode excluir sua própria conta");
      return;
    }

    if (!confirm(`Tem certeza que deseja excluir o usuário "${userName}"?`)) {
      return;
    }

    try {
      await axios.delete(`${API}/admin-panel/users/${userId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success("Usuário excluído com sucesso!");
      fetchUsers();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao excluir usuário");
    }
  };

  const openActivityDetail = (activity) => {
    setSelectedActivity(activity);
    setShowActivityDetailModal(true);
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return "-";
    return new Date(dateStr).toLocaleString("pt-BR");
  };

  const formatDateShort = (dateStr) => {
    if (!dateStr) return "-";
    return new Date(dateStr).toLocaleDateString("pt-BR");
  };

  const getActionIcon = (action) => {
    if (action?.includes("manutenção") || action?.includes("maintenance")) return <Wrench size={14} />;
    if (action?.includes("estoque") || action?.includes("stock")) return <Package size={14} />;
    if (action?.includes("financeiro") || action?.includes("conta")) return <DollarSign size={14} />;
    if (action?.includes("usuário") || action?.includes("user") || action?.includes("Criou usuário") || action?.includes("Excluiu usuário")) return <User size={14} />;
    return <FileText size={14} />;
  };

  const getActionColor = (action) => {
    if (action?.includes("criou") || action?.includes("create") || action?.includes("Criou")) return "bg-green-500/20 text-green-400";
    if (action?.includes("editou") || action?.includes("update") || action?.includes("Editou") || action?.includes("Atualizou")) return "bg-blue-500/20 text-blue-400";
    if (action?.includes("excluiu") || action?.includes("delete") || action?.includes("Excluiu")) return "bg-red-500/20 text-red-400";
    return "bg-gray-500/20 text-gray-400";
  };

  const getRoleBadge = (role) => {
    const roleInfo = USER_ROLES[role] || USER_ROLES.gerenciamento;
    const Icon = roleInfo.icon;
    return (
      <Badge className={`${roleInfo.color} text-white text-xs flex items-center gap-1`}>
        <Icon size={12} />
        {roleInfo.label}
      </Badge>
    );
  };

  const filteredUsers = users.filter(u => 
    u.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    u.email?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const filteredLogs = auditLogs.filter(log =>
    log.user_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    log.action?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-[#E31A1A]" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black text-white">
      {/* Header */}
      <header className="bg-gray-900 border-b border-gray-800 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate("/select-system")}
              className="text-gray-400 hover:text-white"
              data-testid="back-btn"
            >
              <ArrowLeft size={20} />
            </Button>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-[#E31A1A] rounded-lg flex items-center justify-center">
                <Shield className="text-white" size={20} />
              </div>
              <div>
                <h1 className="font-bold text-lg">Painel Administrativo</h1>
                <p className="text-xs text-gray-400">Gestão de usuários e auditoria</p>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-400">Logado como:</span>
            <Badge variant="secondary" className="bg-gray-800">{user?.name}</Badge>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <Card className="bg-gray-900 border-gray-800">
            <CardContent className="p-6">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-[#E31A1A]/20 rounded-lg flex items-center justify-center">
                  <Users className="text-[#E31A1A]" size={24} />
                </div>
                <div>
                  <p className="text-sm text-gray-400">Total de Usuários</p>
                  <p className="text-2xl font-bold text-white">{users.length}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-gray-900 border-gray-800">
            <CardContent className="p-6">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-[#D4A000]/20 rounded-lg flex items-center justify-center">
                  <Activity className="text-[#D4A000]" size={24} />
                </div>
                <div>
                  <p className="text-sm text-gray-400">Atividades Hoje</p>
                  <p className="text-2xl font-bold text-white">
                    {auditLogs.filter(log => {
                      const today = new Date().toDateString();
                      return new Date(log.created_at).toDateString() === today;
                    }).length}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-gray-900 border-gray-800">
            <CardContent className="p-6">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-green-500/20 rounded-lg flex items-center justify-center">
                  <Clock className="text-green-500" size={24} />
                </div>
                <div>
                  <p className="text-sm text-gray-400">Total de Registros</p>
                  <p className="text-2xl font-bold text-white">{auditLogs.length}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 mb-6">
          <Button
            variant={activeTab === "users" ? "default" : "outline"}
            className={activeTab === "users" ? "bg-[#E31A1A] hover:bg-red-700" : "bg-transparent border-gray-700 text-gray-400 hover:bg-gray-800"}
            onClick={() => setActiveTab("users")}
            data-testid="tab-users"
          >
            <Users size={18} className="mr-2" />
            Usuários
          </Button>
          <Button
            variant={activeTab === "audit" ? "default" : "outline"}
            className={activeTab === "audit" ? "bg-[#E31A1A] hover:bg-red-700" : "bg-transparent border-gray-700 text-gray-400 hover:bg-gray-800"}
            onClick={() => setActiveTab("audit")}
            data-testid="tab-audit"
          >
            <Activity size={18} className="mr-2" />
            Auditoria
          </Button>
        </div>

        {/* Search and Actions */}
        <div className="flex flex-col md:flex-row gap-4 mb-6">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" size={18} />
            <Input
              placeholder={activeTab === "users" ? "Buscar usuários..." : "Buscar atividades..."}
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 bg-gray-900 border-gray-700 text-white placeholder:text-gray-500"
              data-testid="search-input"
            />
          </div>
          {activeTab === "users" && (
            <Button
              className="bg-[#E31A1A] hover:bg-red-700"
              onClick={() => setShowCreateModal(true)}
              data-testid="create-user-btn"
            >
              <Plus size={18} className="mr-2" />
              Novo Usuário
            </Button>
          )}
        </div>

        {/* Users Tab */}
        {activeTab === "users" && (
          <Card className="bg-gray-900 border-gray-800">
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow className="border-gray-800 hover:bg-transparent">
                    <TableHead className="text-gray-400">Nome</TableHead>
                    <TableHead className="text-gray-400">Email</TableHead>
                    <TableHead className="text-gray-400">Tipo de Acesso</TableHead>
                    <TableHead className="text-gray-400">Criado em</TableHead>
                    <TableHead className="text-gray-400">Último acesso</TableHead>
                    <TableHead className="text-gray-400 text-right">Ações</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredUsers.map((u) => (
                    <TableRow 
                      key={u.id} 
                      className="border-gray-800 hover:bg-gray-800/50 cursor-pointer"
                      onClick={() => fetchUserActivities(u.id, u.name, u.role)}
                      data-testid={`user-row-${u.id}`}
                    >
                      <TableCell className="font-medium text-white">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 bg-gray-700 rounded-full flex items-center justify-center">
                            <User size={16} className="text-gray-400" />
                          </div>
                          {u.name}
                          {u.id === user?.id && (
                            <Badge className="bg-[#E31A1A]/20 text-[#E31A1A] text-xs">Você</Badge>
                          )}
                        </div>
                      </TableCell>
                      <TableCell className="text-gray-400">{u.email}</TableCell>
                      <TableCell>{getRoleBadge(u.role)}</TableCell>
                      <TableCell className="text-gray-400">{formatDateShort(u.created_at)}</TableCell>
                      <TableCell className="text-gray-400">{formatDate(u.last_login) || "Nunca"}</TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-gray-400 hover:text-white"
                            onClick={(e) => {
                              e.stopPropagation();
                              fetchUserActivities(u.id, u.name, u.role);
                            }}
                            data-testid={`view-activities-${u.id}`}
                          >
                            <Eye size={16} />
                          </Button>
                          {u.id !== user?.id && (
                            <Button
                              variant="ghost"
                              size="sm"
                              className="text-red-400 hover:text-red-300"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleDeleteUser(u.id, u.name);
                              }}
                              data-testid={`delete-user-${u.id}`}
                            >
                              <Trash2 size={16} />
                            </Button>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                  {filteredUsers.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={6} className="text-center text-gray-500 py-8">
                        Nenhum usuário encontrado
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        )}

        {/* Audit Tab */}
        {activeTab === "audit" && (
          <Card className="bg-gray-900 border-gray-800">
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow className="border-gray-800 hover:bg-transparent">
                    <TableHead className="text-gray-400">Data/Hora</TableHead>
                    <TableHead className="text-gray-400">Usuário</TableHead>
                    <TableHead className="text-gray-400">Ação</TableHead>
                    <TableHead className="text-gray-400">Detalhes</TableHead>
                    <TableHead className="text-gray-400 text-right">Ver mais</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredLogs.slice(0, 100).map((log, index) => (
                    <TableRow 
                      key={log.id || index} 
                      className="border-gray-800 hover:bg-gray-800/50 cursor-pointer"
                      onClick={() => openActivityDetail(log)}
                      data-testid={`audit-row-${index}`}
                    >
                      <TableCell className="text-gray-400 whitespace-nowrap">
                        <div className="flex items-center gap-2">
                          <Calendar size={14} />
                          {formatDate(log.created_at)}
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge 
                          className="bg-gray-700 text-gray-300 cursor-pointer hover:bg-gray-600"
                          onClick={(e) => {
                            e.stopPropagation();
                            const foundUser = users.find(u => u.name === log.user_name);
                            if (foundUser) fetchUserActivities(foundUser.id, foundUser.name, foundUser.role);
                          }}
                        >
                          {log.user_name || "Sistema"}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <span className={`p-1 rounded ${getActionColor(log.action)}`}>
                            {getActionIcon(log.action)}
                          </span>
                          <span className="text-white">{log.action}</span>
                        </div>
                      </TableCell>
                      <TableCell className="text-gray-400 max-w-xs truncate">
                        {log.details || "-"}
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-gray-400 hover:text-white"
                          onClick={(e) => {
                            e.stopPropagation();
                            openActivityDetail(log);
                          }}
                        >
                          <Info size={16} />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                  {filteredLogs.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={5} className="text-center text-gray-500 py-8">
                        Nenhuma atividade registrada
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        )}
      </main>

      {/* Create User Modal */}
      <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
        <DialogContent className="bg-gray-900 border-gray-800 text-white">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Plus size={20} className="text-[#E31A1A]" />
              Criar Novo Usuário
            </DialogTitle>
          </DialogHeader>
          <form onSubmit={handleCreateUser} className="space-y-4">
            <div>
              <Label className="text-gray-400">Nome</Label>
              <Input
                value={createForm.name}
                onChange={(e) => setCreateForm({...createForm, name: e.target.value})}
                className="bg-gray-800 border-gray-700 text-white"
                placeholder="Nome completo"
                required
                data-testid="create-user-name"
              />
            </div>
            <div>
              <Label className="text-gray-400">Email</Label>
              <Input
                type="email"
                value={createForm.email}
                onChange={(e) => setCreateForm({...createForm, email: e.target.value})}
                className="bg-gray-800 border-gray-700 text-white"
                placeholder="email@exemplo.com"
                required
                data-testid="create-user-email"
              />
            </div>
            <div>
              <Label className="text-gray-400">Tipo de Acesso</Label>
              <Select 
                value={createForm.role} 
                onValueChange={(value) => setCreateForm({...createForm, role: value})}
              >
                <SelectTrigger className="bg-gray-800 border-gray-700 text-white" data-testid="create-user-role">
                  <SelectValue placeholder="Selecione o tipo de acesso" />
                </SelectTrigger>
                <SelectContent className="bg-gray-800 border-gray-700">
                  <SelectItem value="gerenciamento" className="text-white hover:bg-gray-700">
                    <div className="flex items-center gap-2">
                      <Landmark size={16} className="text-[#E31A1A]" />
                      <span>Gerenciamento Geral</span>
                    </div>
                  </SelectItem>
                  <SelectItem value="administrativo" className="text-white hover:bg-gray-700">
                    <div className="flex items-center gap-2">
                      <Building2 size={16} className="text-[#D4A000]" />
                      <span>Administrativo</span>
                    </div>
                  </SelectItem>
                  <SelectItem value="ambos" className="text-white hover:bg-gray-700">
                    <div className="flex items-center gap-2">
                      <Users size={16} className="text-purple-500" />
                      <span>Gerenciamento + Administrativo</span>
                    </div>
                  </SelectItem>
                  <SelectItem value="admin" className="text-white hover:bg-gray-700">
                    <div className="flex items-center gap-2">
                      <Crown size={16} className="text-green-500" />
                      <span>Administrador (Acesso Total)</span>
                    </div>
                  </SelectItem>
                </SelectContent>
              </Select>
              <p className="text-xs text-gray-500 mt-1">
                {createForm.role === "gerenciamento" && "Acesso apenas ao módulo de Gerenciamento Geral (Máquinas, Manutenções, Estoque)"}
                {createForm.role === "administrativo" && "Acesso apenas ao módulo Administrativo (Financeiro, Fornecedores, Produtos)"}
                {createForm.role === "ambos" && "Acesso aos módulos Gerenciamento Geral e Administrativo"}
                {createForm.role === "admin" && "Acesso total: todos os módulos + Painel Administrativo"}
              </p>
            </div>
            <div>
              <Label className="text-gray-400">Senha</Label>
              <Input
                type="password"
                value={createForm.password}
                onChange={(e) => setCreateForm({...createForm, password: e.target.value})}
                className="bg-gray-800 border-gray-700 text-white"
                placeholder="••••••••"
                required
                data-testid="create-user-password"
              />
            </div>
            <div>
              <Label className="text-gray-400">Confirmar Senha</Label>
              <Input
                type="password"
                value={createForm.confirmPassword}
                onChange={(e) => setCreateForm({...createForm, confirmPassword: e.target.value})}
                className="bg-gray-800 border-gray-700 text-white"
                placeholder="••••••••"
                required
                data-testid="create-user-confirm-password"
              />
            </div>
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => setShowCreateModal(false)}
                className="bg-transparent border-gray-700 text-gray-400 hover:bg-gray-800"
              >
                Cancelar
              </Button>
              <Button
                type="submit"
                className="bg-[#E31A1A] hover:bg-red-700"
                disabled={creating}
                data-testid="create-user-submit"
              >
                {creating ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Plus size={18} className="mr-2" />}
                Criar Usuário
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* User Activities Modal */}
      <Dialog open={showActivitiesModal} onOpenChange={setShowActivitiesModal}>
        <DialogContent className="bg-gray-900 border-gray-800 text-white max-w-2xl max-h-[80vh] overflow-hidden flex flex-col">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Activity size={20} className="text-[#D4A000]" />
              <span>Atividades de {selectedUser?.name}</span>
              {selectedUser?.role && (
                <span className="ml-2">{getRoleBadge(selectedUser.role)}</span>
              )}
            </DialogTitle>
          </DialogHeader>
          <div className="flex-1 overflow-y-auto">
            {userActivities.length > 0 ? (
              <div className="space-y-3">
                {userActivities.map((activity, index) => (
                  <div 
                    key={index} 
                    className="bg-gray-800 rounded-lg p-4 border border-gray-700 cursor-pointer hover:border-gray-600 transition-colors"
                    onClick={() => openActivityDetail(activity)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-3">
                        <span className={`p-2 rounded-lg ${getActionColor(activity.action)}`}>
                          {getActionIcon(activity.action)}
                        </span>
                        <div>
                          <p className="text-white font-medium">{activity.action}</p>
                          <p className="text-sm text-gray-400 truncate max-w-md">{activity.details || "Sem detalhes"}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-gray-500 whitespace-nowrap">
                          {formatDate(activity.created_at)}
                        </span>
                        <Info size={14} className="text-gray-500" />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <Activity size={40} className="mx-auto mb-4 opacity-50" />
                <p>Nenhuma atividade registrada para este usuário</p>
              </div>
            )}
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowActivitiesModal(false)}
              className="bg-transparent border-gray-700 text-gray-400 hover:bg-gray-800"
            >
              Fechar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Activity Detail Modal */}
      <Dialog open={showActivityDetailModal} onOpenChange={setShowActivityDetailModal}>
        <DialogContent className="bg-gray-900 border-gray-800 text-white max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Info size={20} className="text-[#D4A000]" />
              Detalhes da Atividade
            </DialogTitle>
          </DialogHeader>
          {selectedActivity && (
            <div className="space-y-4">
              <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
                <div className="flex items-center gap-3 mb-4">
                  <span className={`p-3 rounded-lg ${getActionColor(selectedActivity.action)}`}>
                    {getActionIcon(selectedActivity.action)}
                  </span>
                  <div>
                    <p className="text-white font-bold text-lg">{selectedActivity.action}</p>
                    <p className="text-sm text-gray-400">
                      Por: {selectedActivity.user_name || "Sistema"}
                    </p>
                  </div>
                </div>
                
                <div className="space-y-3">
                  <div className="flex items-center gap-2 text-sm">
                    <Calendar size={16} className="text-gray-400" />
                    <span className="text-gray-400">Data/Hora:</span>
                    <span className="text-white">{formatDate(selectedActivity.created_at)}</span>
                  </div>
                  
                  {selectedActivity.user_id && (
                    <div className="flex items-center gap-2 text-sm">
                      <User size={16} className="text-gray-400" />
                      <span className="text-gray-400">ID do Usuário:</span>
                      <span className="text-white font-mono text-xs">{selectedActivity.user_id}</span>
                    </div>
                  )}
                  
                  {selectedActivity.id && (
                    <div className="flex items-center gap-2 text-sm">
                      <FileText size={16} className="text-gray-400" />
                      <span className="text-gray-400">ID do Registro:</span>
                      <span className="text-white font-mono text-xs">{selectedActivity.id}</span>
                    </div>
                  )}
                </div>
              </div>
              
              {selectedActivity.details && (
                <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
                  <p className="text-sm text-gray-400 mb-2">Detalhes Completos:</p>
                  <p className="text-white whitespace-pre-wrap">{selectedActivity.details}</p>
                </div>
              )}
              
              {!selectedActivity.details && (
                <div className="bg-gray-800 rounded-lg p-4 border border-gray-700 text-center">
                  <p className="text-gray-500">Nenhum detalhe adicional disponível</p>
                </div>
              )}
            </div>
          )}
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowActivityDetailModal(false)}
              className="bg-transparent border-gray-700 text-gray-400 hover:bg-gray-800"
            >
              Fechar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
