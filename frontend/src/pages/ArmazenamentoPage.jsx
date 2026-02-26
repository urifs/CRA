import { useState, useEffect, useRef } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import axios from "axios";
import { API, useAuth } from "@/App";
import { toast } from "sonner";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  FolderOpen,
  File,
  Upload,
  Plus,
  Trash2,
  Download,
  MoreVertical,
  ArrowLeft,
  Home,
  Search,
  X,
  Image,
  FileText,
  FileSpreadsheet,
  FileArchive,
  Film,
  Music,
  ChevronRight,
  Loader2,
  FolderPlus,
  Grid,
  List,
  Edit,
  Eye,
  HardDrive,
  LogOut,
  RotateCcw,
  Trash
} from "lucide-react";
import { Lock, LockOpen, KeyRound } from "lucide-react";

const getFileIcon = (filename) => {
  const ext = filename.split('.').pop()?.toLowerCase();
  const imageExts = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg', 'bmp'];
  const docExts = ['pdf', 'doc', 'docx', 'txt', 'rtf'];
  const spreadExts = ['xls', 'xlsx', 'csv'];
  const archiveExts = ['zip', 'rar', '7z', 'tar', 'gz'];
  const videoExts = ['mp4', 'avi', 'mov', 'wmv', 'mkv'];
  const audioExts = ['mp3', 'wav', 'ogg', 'flac', 'aac'];

  if (imageExts.includes(ext)) return { icon: Image, color: "text-green-500" };
  if (docExts.includes(ext)) return { icon: FileText, color: "text-red-500" };
  if (spreadExts.includes(ext)) return { icon: FileSpreadsheet, color: "text-emerald-500" };
  if (archiveExts.includes(ext)) return { icon: FileArchive, color: "text-yellow-500" };
  if (videoExts.includes(ext)) return { icon: Film, color: "text-purple-500" };
  if (audioExts.includes(ext)) return { icon: Music, color: "text-pink-500" };
  return { icon: File, color: "text-gray-500" };
};

const formatFileSize = (bytes) => {
  if (!bytes) return "0 B";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`;
};

export default function ArmazenamentoPage() {
  const navigate = useNavigate();
  const { logout } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const fileInputRef = useRef(null);

  const [items, setItems] = useState([]);
  const [trashItems, setTrashItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [viewMode, setViewMode] = useState("grid"); // "grid" or "list"
  const [currentPath, setCurrentPath] = useState(searchParams.get("path") || "/");
  const [breadcrumbs, setBreadcrumbs] = useState([{ name: "Início", path: "/" }]);
  const [showTrash, setShowTrash] = useState(false);

  // Modals
  const [showNewFolderModal, setShowNewFolderModal] = useState(false);
  const [newFolderName, setNewFolderName] = useState("");
  const [newFolderPassword, setNewFolderPassword] = useState("");
  const [showRenameModal, setShowRenameModal] = useState(false);
  const [renameItem, setRenameItem] = useState(null);
  const [newName, setNewName] = useState("");
  const [showPreviewModal, setShowPreviewModal] = useState(false);
  const [previewItem, setPreviewItem] = useState(null);
  const [previewBlobUrl, setPreviewBlobUrl] = useState(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  // Password protection
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [passwordFolder, setPasswordFolder] = useState(null);
  const [folderPassword, setFolderPassword] = useState("");
  const [passwordError, setPasswordError] = useState("");
  const [showSetPasswordModal, setShowSetPasswordModal] = useState(false);
  const [passwordTargetFolder, setPasswordTargetFolder] = useState(null);
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [unlockedFolders, setUnlockedFolders] = useState(new Set()); // Track unlocked folders in session

  const token = localStorage.getItem("token");

  useEffect(() => {
    if (showTrash) {
      fetchTrashItems();
    } else {
      fetchItems();
      updateBreadcrumbs();
    }
  }, [currentPath, showTrash]);

  // Fetch trash count on mount
  useEffect(() => {
    fetchTrashItems();
  }, []);

  const updateBreadcrumbs = () => {
    const parts = currentPath.split('/').filter(p => p);
    const crumbs = [{ name: "Início", path: "/" }];
    let path = "";
    for (const part of parts) {
      path += "/" + part;
      crumbs.push({ name: part, path });
    }
    setBreadcrumbs(crumbs);
  };

  const fetchItems = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/storage/list`, {
        params: { path: currentPath },
        headers: { Authorization: `Bearer ${token}` }
      });
      setItems(response.data);
    } catch (error) {
      console.error("Erro ao carregar itens:", error);
      if (error.response?.status === 401) {
        toast.error("Sessão expirada");
        navigate("/login");
      }
    } finally {
      setLoading(false);
    }
  };

  const fetchTrashItems = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/storage/trash`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setTrashItems(response.data);
    } catch (error) {
      console.error("Erro ao carregar lixeira:", error);
      if (error.response?.status === 401) {
        toast.error("Sessão expirada");
        navigate("/login");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleNavigate = (path) => {
    setCurrentPath(path);
    setSearchParams({ path });
  };

  const handleCreateFolder = async () => {
    if (!newFolderName.trim()) {
      toast.error("Digite um nome para a pasta");
      return;
    }
    try {
      await axios.post(`${API}/storage/folder`, 
        { 
          name: newFolderName, 
          parent_path: currentPath,
          password: newFolderPassword || null
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success("Pasta criada com sucesso!" + (newFolderPassword ? " (protegida com senha)" : ""));
      setShowNewFolderModal(false);
      setNewFolderName("");
      setNewFolderPassword("");
      fetchItems();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao criar pasta");
    }
  };

  // Verificar senha e navegar para pasta
  const handleFolderClick = async (folder) => {
    if (folder.has_password && !unlockedFolders.has(folder.path)) {
      // Pasta protegida - mostrar modal de senha
      setPasswordFolder(folder);
      setFolderPassword("");
      setPasswordError("");
      setShowPasswordModal(true);
    } else {
      // Pasta não protegida ou já desbloqueada - navegar
      navigateToFolder(folder.path);
    }
  };

  const navigateToFolder = (path) => {
    setCurrentPath(path);
    setSearchParams({ path });
  };

  const handlePasswordSubmit = async () => {
    if (!folderPassword) {
      setPasswordError("Digite a senha");
      return;
    }
    
    try {
      await axios.post(`${API}/storage/folder/check-password`, 
        { path: passwordFolder.path, password: folderPassword },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      // Senha correta - desbloquear e navegar
      setUnlockedFolders(prev => new Set([...prev, passwordFolder.path]));
      setShowPasswordModal(false);
      setFolderPassword("");
      navigateToFolder(passwordFolder.path);
    } catch (error) {
      setPasswordError("Senha incorreta");
    }
  };

  // Definir/remover senha de pasta
  const handleSetPassword = async () => {
    if (newPassword && newPassword !== confirmPassword) {
      toast.error("As senhas não coincidem");
      return;
    }
    
    try {
      await axios.post(`${API}/storage/folder/set-password`, 
        { path: passwordTargetFolder.path, password: newPassword || null },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      toast.success(newPassword ? "Senha definida com sucesso!" : "Senha removida com sucesso!");
      setShowSetPasswordModal(false);
      setPasswordTargetFolder(null);
      setNewPassword("");
      setConfirmPassword("");
      fetchItems();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao definir senha");
    }
  };

  const openSetPasswordModal = (folder) => {
    setPasswordTargetFolder(folder);
    setNewPassword("");
    setConfirmPassword("");
    setShowSetPasswordModal(true);
  };

  const handleUpload = async (e) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    setUploading(true);
    setUploadProgress(0);

    try {
      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        const formData = new FormData();
        formData.append("file", file);
        formData.append("path", currentPath);

        await axios.post(`${API}/storage/upload`, formData, {
          headers: { 
            Authorization: `Bearer ${token}`,
            "Content-Type": "multipart/form-data"
          },
          onUploadProgress: (progressEvent) => {
            const progress = Math.round(
              ((i + progressEvent.loaded / progressEvent.total) / files.length) * 100
            );
            setUploadProgress(progress);
          }
        });
      }
      toast.success(`${files.length} arquivo(s) enviado(s) com sucesso!`);
      fetchItems();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao enviar arquivo");
    } finally {
      setUploading(false);
      setUploadProgress(0);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const handleDelete = async (item) => {
    if (!confirm(`Mover "${item.name}" para a lixeira?`)) return;
    try {
      await axios.delete(`${API}/storage/delete`, {
        params: { path: item.path },
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success("Item movido para lixeira!");
      fetchItems();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao excluir");
    }
  };

  const handleRestore = async (item) => {
    try {
      await axios.post(`${API}/storage/trash/${item.id}/restore`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success("Item restaurado!");
      fetchTrashItems();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao restaurar");
    }
  };

  const handleDeletePermanently = async (item) => {
    if (!confirm(`Excluir "${item.original_name}" permanentemente? Esta ação não pode ser desfeita.`)) return;
    try {
      await axios.delete(`${API}/storage/trash/${item.id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success("Item excluído permanentemente!");
      fetchTrashItems();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao excluir");
    }
  };

  const handleEmptyTrash = async () => {
    if (!confirm("Esvaziar toda a lixeira? Esta ação não pode ser desfeita.")) return;
    try {
      await axios.delete(`${API}/storage/trash`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success("Lixeira esvaziada!");
      fetchTrashItems();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao esvaziar lixeira");
    }
  };

  const handleRename = async () => {
    if (!newName.trim() || !renameItem) return;
    try {
      await axios.patch(`${API}/storage/rename`, 
        { path: renameItem.path, new_name: newName },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success("Renomeado com sucesso!");
      setShowRenameModal(false);
      setRenameItem(null);
      setNewName("");
      fetchItems();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao renomear");
    }
  };

  const handleDownload = async (item) => {
    try {
      const response = await axios.get(`${API}/storage/download`, {
        params: { path: item.path },
        headers: { Authorization: `Bearer ${token}` },
        responseType: "blob"
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", item.name);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      toast.error("Erro ao baixar arquivo");
    }
  };

  const handlePreview = async (item) => {
    setPreviewItem(item);
    setShowPreviewModal(true);
    setPreviewLoading(true);
    setPreviewBlobUrl(null);
    
    try {
      const response = await axios.get(`${API}/storage/download`, {
        params: { path: item.path },
        headers: { Authorization: `Bearer ${token}` },
        responseType: "blob"
      });
      const blobUrl = window.URL.createObjectURL(response.data);
      setPreviewBlobUrl(blobUrl);
    } catch (error) {
      toast.error("Erro ao carregar preview");
    } finally {
      setPreviewLoading(false);
    }
  };

  const closePreviewModal = () => {
    if (previewBlobUrl) {
      window.URL.revokeObjectURL(previewBlobUrl);
    }
    setPreviewBlobUrl(null);
    setPreviewItem(null);
    setShowPreviewModal(false);
  };

  const isPreviewable = (filename) => {
    const ext = filename.split('.').pop()?.toLowerCase();
    // Imagens, PDFs, vídeos, Word e Excel podem ser visualizados
    return ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg', 'pdf', 'mp4', 'webm', 'ogg', 'doc', 'docx', 'xls', 'xlsx'].includes(ext);
  };

  const getPreviewType = (filename) => {
    const ext = filename.split('.').pop()?.toLowerCase();
    if (['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg'].includes(ext)) return 'image';
    if (ext === 'pdf') return 'pdf';
    if (['mp4', 'webm', 'ogg'].includes(ext)) return 'video';
    if (['doc', 'docx'].includes(ext)) return 'word';
    if (['xls', 'xlsx'].includes(ext)) return 'excel';
    return 'other';
  };

  const filteredItems = items.filter(item =>
    item.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const filteredTrashItems = trashItems.filter(item =>
    item.original_name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const folders = filteredItems.filter(i => i.type === "folder");
  const files = filteredItems.filter(i => i.type === "file");

  return (
    <div className="min-h-screen bg-black">
      {/* Background pattern - same as login */}
      <div className="absolute inset-0 opacity-5">
        <div className="absolute inset-0" style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='1'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`
        }} />
      </div>

      {/* Header */}
      <header className="bg-[#E31A1A] text-white sticky top-0 z-40 relative">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Button variant="ghost" size="sm" className="text-white hover:bg-red-700" onClick={() => navigate("/select-system")}>
              <ArrowLeft size={20} />
            </Button>
            <HardDrive size={24} />
            <h1 className="text-xl font-bold">Armazenamento</h1>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" className="text-white hover:bg-red-700" onClick={() => { logout(); navigate("/login"); }}>
              <LogOut size={18} className="mr-2" />
              Sair
            </Button>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 py-6 relative z-10">
        {/* Toolbar */}
        <div className="flex flex-col sm:flex-row gap-4 mb-6">
          {/* Search */}
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" size={18} />
            <Input
              placeholder={showTrash ? "Pesquisar na lixeira..." : "Pesquisar arquivos..."}
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 pr-10 bg-gray-900 border-gray-700 text-white placeholder:text-gray-500"
            />
            {searchTerm && (
              <button className="absolute right-3 top-1/2 -translate-y-1/2" onClick={() => setSearchTerm("")}>
                <X size={16} className="text-gray-500" />
              </button>
            )}
          </div>
          
          <Button className="bg-[#D4A000] hover:bg-[#b38900] text-black shrink-0">
            <Search size={16} className="mr-2" />
            Buscar
          </Button>

          {/* Actions */}
          <div className="flex items-center gap-2">
            {!showTrash ? (
              <>
                <Button variant="outline" size="sm" onClick={() => setShowNewFolderModal(true)} className="border-gray-700 text-gray-300 hover:bg-gray-800 hover:text-white">
                  <FolderPlus size={18} className="mr-2" />
                  Nova Pasta
                </Button>
                <Button className="bg-[#E31A1A] hover:bg-red-700" size="sm" onClick={() => fileInputRef.current?.click()}>
                  <Upload size={18} className="mr-2" />
                  Upload
                </Button>
                <input
                  ref={fileInputRef}
                  type="file"
                  multiple
                  className="hidden"
                  onChange={handleUpload}
                />
              </>
            ) : (
              <Button 
                variant="outline" 
                size="sm" 
                onClick={handleEmptyTrash} 
                className="border-red-700 text-red-500 hover:bg-red-900/30 hover:text-red-400"
                disabled={trashItems.length === 0}
              >
                <Trash2 size={18} className="mr-2" />
                Esvaziar Lixeira
              </Button>
            )}
            <Button 
              variant={showTrash ? "secondary" : "outline"} 
              size="sm" 
              onClick={() => { setShowTrash(!showTrash); setSearchTerm(""); }} 
              className={showTrash ? "bg-gray-700 text-white" : "border-gray-700 text-gray-300 hover:bg-gray-800 hover:text-white"}
            >
              <Trash size={18} className="mr-2" />
              Lixeira
              {trashItems.length > 0 && !showTrash && (
                <span className="ml-2 bg-red-600 text-white text-xs px-1.5 py-0.5 rounded-full">{trashItems.length}</span>
              )}
            </Button>
            <div className="flex border border-gray-700 rounded-md">
              <Button variant={viewMode === "grid" ? "secondary" : "ghost"} size="sm" className={`rounded-r-none ${viewMode === "grid" ? "bg-gray-700" : "text-gray-400 hover:text-white"}`} onClick={() => setViewMode("grid")}>
                <Grid size={18} />
              </Button>
              <Button variant={viewMode === "list" ? "secondary" : "ghost"} size="sm" className={`rounded-l-none ${viewMode === "list" ? "bg-gray-700" : "text-gray-400 hover:text-white"}`} onClick={() => setViewMode("list")}>
                <List size={18} />
              </Button>
            </div>
          </div>
        </div>

        {/* Upload Progress */}
        {uploading && (
          <div className="mb-4 bg-gray-900 border border-gray-700 rounded-lg p-4">
            <div className="flex items-center gap-3">
              <Loader2 className="animate-spin text-[#E31A1A]" size={20} />
              <span className="text-gray-300">Enviando... {uploadProgress}%</span>
            </div>
            <div className="mt-2 bg-gray-700 rounded-full h-2">
              <div className="bg-[#E31A1A] h-2 rounded-full transition-all" style={{ width: `${uploadProgress}%` }} />
            </div>
          </div>
        )}

        {/* Breadcrumbs or Trash Header */}
        {showTrash ? (
          <div className="flex items-center gap-2 text-sm mb-4">
            <Trash size={16} className="text-gray-400" />
            <span className="text-gray-400">Lixeira</span>
            <span className="text-gray-500">({trashItems.length} itens)</span>
          </div>
        ) : (
          <div className="flex items-center gap-1 text-sm mb-4 overflow-x-auto pb-2">
            {breadcrumbs.map((crumb, index) => (
              <div key={crumb.path} className="flex items-center gap-1 whitespace-nowrap">
                {index > 0 && <ChevronRight size={14} className="text-gray-500" />}
                <button
                  onClick={() => handleNavigate(crumb.path)}
                  className={`hover:text-[#E31A1A] ${index === breadcrumbs.length - 1 ? 'text-[#E31A1A] font-medium' : 'text-gray-400'}`}
                >
                  {index === 0 ? <Home size={16} /> : crumb.name}
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Content */}
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="animate-spin text-[#E31A1A]" size={40} />
          </div>
        ) : showTrash ? (
          /* Trash View */
          filteredTrashItems.length === 0 ? (
            <div className="text-center py-20">
              <Trash size={64} className="mx-auto text-gray-600 mb-4" />
              <p className="text-gray-400 mb-4">
                {searchTerm ? "Nenhum item encontrado" : "A lixeira está vazia"}
              </p>
              <Button onClick={() => setShowTrash(false)} className="bg-gray-700 hover:bg-gray-600">
                <ArrowLeft size={18} className="mr-2" />
                Voltar aos Arquivos
              </Button>
            </div>
          ) : viewMode === "grid" ? (
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
              {filteredTrashItems.map((item) => {
                const isFolder = item.type === "folder";
                const fileType = !isFolder ? getFileIcon(item.original_name) : null;
                const FileIcon = fileType?.icon || FolderOpen;
                return (
                  <Card
                    key={item.id}
                    className="bg-gray-900 border-gray-800 hover:shadow-lg hover:border-gray-700 transition-all group"
                  >
                    <CardContent className="p-4 text-center relative">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="sm" className="absolute top-1 right-1 opacity-0 group-hover:opacity-100 text-gray-400 hover:text-white">
                            <MoreVertical size={16} />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent>
                          <DropdownMenuItem onClick={() => handleRestore(item)}>
                            <RotateCcw size={14} className="mr-2" /> Restaurar
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => handleDeletePermanently(item)} className="text-red-600">
                            <Trash2 size={14} className="mr-2" /> Excluir Permanentemente
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                      {isFolder ? (
                        <FolderOpen size={48} className="mx-auto text-gray-500 mb-2" />
                      ) : (
                        <FileIcon size={48} className={`mx-auto ${fileType?.color || "text-gray-500"} mb-2 opacity-50`} />
                      )}
                      <p className="text-sm font-medium truncate text-gray-400">{item.original_name}</p>
                      <p className="text-xs text-gray-600">
                        {new Date(item.deleted_at).toLocaleDateString("pt-BR")}
                      </p>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          ) : (
            <Card className="bg-gray-900 border-gray-800">
              <CardContent className="p-0">
                <table className="w-full">
                  <thead className="bg-gray-800 border-b border-gray-700">
                    <tr>
                      <th className="text-left p-3 font-medium text-gray-300">Nome</th>
                      <th className="text-left p-3 font-medium text-gray-300 hidden sm:table-cell">Caminho Original</th>
                      <th className="text-left p-3 font-medium text-gray-300 hidden md:table-cell">Excluído em</th>
                      <th className="text-right p-3 font-medium text-gray-300">Ações</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredTrashItems.map((item) => {
                      const isFolder = item.type === "folder";
                      const fileType = !isFolder ? getFileIcon(item.original_name) : null;
                      const FileIcon = fileType?.icon || FolderOpen;
                      return (
                        <tr key={item.id} className="border-b border-gray-800 hover:bg-gray-800">
                          <td className="p-3">
                            <div className="flex items-center gap-3">
                              {isFolder ? (
                                <FolderOpen size={24} className="text-gray-500" />
                              ) : (
                                <FileIcon size={24} className={`${fileType?.color || "text-gray-500"} opacity-50`} />
                              )}
                              <span className="text-gray-400">{item.original_name}</span>
                            </div>
                          </td>
                          <td className="p-3 text-gray-500 hidden sm:table-cell">{item.original_path}</td>
                          <td className="p-3 text-gray-500 hidden md:table-cell">{new Date(item.deleted_at).toLocaleDateString("pt-BR")}</td>
                          <td className="p-3 text-right">
                            <div className="flex justify-end gap-1">
                              <Button variant="ghost" size="sm" onClick={() => handleRestore(item)} className="text-green-500 hover:text-green-400">
                                <RotateCcw size={16} />
                              </Button>
                              <Button variant="ghost" size="sm" onClick={() => handleDeletePermanently(item)} className="text-red-500 hover:text-red-400">
                                <Trash2 size={16} />
                              </Button>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </CardContent>
            </Card>
          )
        ) : filteredItems.length === 0 ? (
          <div className="text-center py-20">
            <FolderOpen size={64} className="mx-auto text-gray-600 mb-4" />
            <p className="text-gray-400 mb-4">
              {searchTerm ? "Nenhum item encontrado" : "Esta pasta está vazia"}
            </p>
            <Button onClick={() => fileInputRef.current?.click()} className="bg-[#E31A1A] hover:bg-red-700">
              <Upload size={18} className="mr-2" />
              Fazer Upload
            </Button>
          </div>
        ) : viewMode === "grid" ? (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
            {/* Folders first */}
            {folders.map((item) => (
              <Card
                key={item.path}
                className="bg-gray-900 border-gray-800 hover:shadow-lg hover:border-gray-700 cursor-pointer transition-all group"
                onClick={() => handleFolderClick(item)}
              >
                <CardContent className="p-4 text-center relative">
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="sm" className="absolute top-1 right-1 opacity-0 group-hover:opacity-100 text-gray-400 hover:text-white" onClick={(e) => e.stopPropagation()}>
                        <MoreVertical size={16} />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent>
                      <DropdownMenuItem onClick={(e) => { e.stopPropagation(); setRenameItem(item); setNewName(item.name); setShowRenameModal(true); }}>
                        <Edit size={14} className="mr-2" /> Renomear
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={(e) => { e.stopPropagation(); openSetPasswordModal(item); }}>
                        {item.has_password ? <LockOpen size={14} className="mr-2" /> : <Lock size={14} className="mr-2" />}
                        {item.has_password ? "Alterar/Remover Senha" : "Definir Senha"}
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={(e) => { e.stopPropagation(); handleDelete(item); }} className="text-red-600">
                        <Trash2 size={14} className="mr-2" /> Excluir
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                  <div className="relative inline-block">
                    <FolderOpen size={48} className="mx-auto text-[#D4A000] mb-2" />
                    {item.has_password && (
                      <Lock size={16} className="absolute -bottom-1 -right-1 text-yellow-500 bg-gray-900 rounded-full p-0.5" />
                    )}
                  </div>
                  <p className="text-sm font-medium truncate text-white">{item.name}</p>
                  <p className="text-xs text-gray-500">{item.items_count || 0} itens</p>
                </CardContent>
              </Card>
            ))}
            {/* Then files */}
            {files.map((item) => {
              const fileType = getFileIcon(item.name);
              const FileIcon = fileType.icon;
              const canPreview = isPreviewable(item.name);
              return (
                <Card
                  key={item.path}
                  className="bg-gray-900 border-gray-800 hover:shadow-lg hover:border-gray-700 cursor-pointer transition-all group"
                  onClick={() => canPreview ? handlePreview(item) : handleDownload(item)}
                >
                  <CardContent className="p-4 text-center relative">
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="sm" className="absolute top-1 right-1 opacity-0 group-hover:opacity-100 text-gray-400 hover:text-white" onClick={(e) => e.stopPropagation()}>
                          <MoreVertical size={16} />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent>
                        {canPreview && (
                          <DropdownMenuItem onClick={(e) => { e.stopPropagation(); handlePreview(item); }}>
                            <Eye size={14} className="mr-2" /> Visualizar
                          </DropdownMenuItem>
                        )}
                        <DropdownMenuItem onClick={(e) => { e.stopPropagation(); handleDownload(item); }}>
                          <Download size={14} className="mr-2" /> Baixar
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={(e) => { e.stopPropagation(); setRenameItem(item); setNewName(item.name); setShowRenameModal(true); }}>
                          <Edit size={14} className="mr-2" /> Renomear
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={(e) => { e.stopPropagation(); handleDelete(item); }} className="text-red-600">
                          <Trash2 size={14} className="mr-2" /> Excluir
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                    <FileIcon size={48} className={`mx-auto ${fileType.color} mb-2`} />
                    <p className="text-sm font-medium truncate text-white">{item.name}</p>
                    <p className="text-xs text-gray-500">{formatFileSize(item.size)}</p>
                    {canPreview && (
                      <p className="text-xs text-[#D4A000] mt-1 flex items-center justify-center gap-1">
                        <Eye size={12} /> Clique para visualizar
                      </p>
                    )}
                  </CardContent>
                </Card>
              );
            })}
          </div>
        ) : (
          <Card className="bg-gray-900 border-gray-800">
            <CardContent className="p-0">
              <table className="w-full">
                <thead className="bg-gray-800 border-b border-gray-700">
                  <tr>
                    <th className="text-left p-3 font-medium text-gray-300">Nome</th>
                    <th className="text-left p-3 font-medium text-gray-300 hidden sm:table-cell">Tamanho</th>
                    <th className="text-left p-3 font-medium text-gray-300 hidden md:table-cell">Modificado</th>
                    <th className="text-right p-3 font-medium text-gray-300">Ações</th>
                  </tr>
                </thead>
                <tbody>
                  {folders.map((item) => (
                    <tr key={item.path} className="border-b border-gray-800 hover:bg-gray-800 cursor-pointer" onClick={() => handleFolderClick(item)}>
                      <td className="p-3">
                        <div className="flex items-center gap-3">
                          <div className="relative">
                            <FolderOpen size={24} className="text-[#D4A000]" />
                            {item.has_password && (
                              <Lock size={10} className="absolute -bottom-0.5 -right-0.5 text-yellow-500 bg-gray-900 rounded-full p-0.5" />
                            )}
                          </div>
                          <span className="font-medium text-white">{item.name}</span>
                          {item.has_password && <Lock size={12} className="text-yellow-500" />}
                        </div>
                      </td>
                      <td className="p-3 text-gray-400 hidden sm:table-cell">{item.items_count || 0} itens</td>
                      <td className="p-3 text-gray-400 hidden md:table-cell">{new Date(item.modified_at).toLocaleDateString("pt-BR")}</td>
                      <td className="p-3 text-right">
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="sm" className="text-gray-400 hover:text-white" onClick={(e) => e.stopPropagation()}><MoreVertical size={16} /></Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent>
                            <DropdownMenuItem onClick={(e) => { e.stopPropagation(); setRenameItem(item); setNewName(item.name); setShowRenameModal(true); }}>
                              <Edit size={14} className="mr-2" /> Renomear
                            </DropdownMenuItem>
                            <DropdownMenuItem onClick={(e) => { e.stopPropagation(); openSetPasswordModal(item); }}>
                              {item.has_password ? <LockOpen size={14} className="mr-2" /> : <Lock size={14} className="mr-2" />}
                              {item.has_password ? "Alterar/Remover Senha" : "Definir Senha"}
                            </DropdownMenuItem>
                            <DropdownMenuItem onClick={(e) => { e.stopPropagation(); handleDelete(item); }} className="text-red-600">
                              <Trash2 size={14} className="mr-2" /> Excluir
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </td>
                    </tr>
                  ))}
                  {files.map((item) => {
                    const fileType = getFileIcon(item.name);
                    const FileIcon = fileType.icon;
                    return (
                      <tr key={item.path} className="border-b border-gray-800 hover:bg-gray-800 cursor-pointer" onDoubleClick={() => handleDownload(item)}>
                        <td className="p-3">
                          <div className="flex items-center gap-3">
                            <FileIcon size={24} className={fileType.color} />
                            <span className="text-white">{item.name}</span>
                          </div>
                        </td>
                        <td className="p-3 text-gray-400 hidden sm:table-cell">{formatFileSize(item.size)}</td>
                        <td className="p-3 text-gray-400 hidden md:table-cell">{new Date(item.modified_at).toLocaleDateString("pt-BR")}</td>
                        <td className="p-3 text-right">
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" size="sm" className="text-gray-400 hover:text-white"><MoreVertical size={16} /></Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent>
                              {isPreviewable(item.name) && (
                                <DropdownMenuItem onClick={() => handlePreview(item)}>
                                  <Eye size={14} className="mr-2" /> Visualizar
                                </DropdownMenuItem>
                              )}
                              <DropdownMenuItem onClick={() => handleDownload(item)}>
                                <Download size={14} className="mr-2" /> Baixar
                              </DropdownMenuItem>
                              <DropdownMenuItem onClick={() => { setRenameItem(item); setNewName(item.name); setShowRenameModal(true); }}>
                                <Edit size={14} className="mr-2" /> Renomear
                              </DropdownMenuItem>
                              <DropdownMenuItem onClick={() => handleDelete(item)} className="text-red-600">
                                <Trash2 size={14} className="mr-2" /> Excluir
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </CardContent>
          </Card>
        )}
      </div>

      {/* New Folder Modal */}
      <Dialog open={showNewFolderModal} onOpenChange={setShowNewFolderModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <FolderPlus className="text-[#D4A000]" size={20} />
              Nova Pasta
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>Nome da pasta</Label>
              <Input
                value={newFolderName}
                onChange={(e) => setNewFolderName(e.target.value)}
                placeholder="Minha pasta"
                onKeyDown={(e) => e.key === "Enter" && handleCreateFolder()}
              />
            </div>
            <div>
              <Label className="flex items-center gap-2">
                <Lock size={14} className="text-yellow-500" />
                Senha (opcional)
              </Label>
              <Input
                type="password"
                value={newFolderPassword}
                onChange={(e) => setNewFolderPassword(e.target.value)}
                placeholder="Deixe vazio para não proteger"
              />
              <p className="text-xs text-gray-500 mt-1">
                Defina uma senha para proteger o acesso à pasta
              </p>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => { setShowNewFolderModal(false); setNewFolderPassword(""); }}>Cancelar</Button>
            <Button onClick={handleCreateFolder} className="bg-[#E31A1A] hover:bg-red-700">Criar</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Rename Modal */}
      <Dialog open={showRenameModal} onOpenChange={setShowRenameModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Renomear</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>Novo nome</Label>
              <Input
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleRename()}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowRenameModal(false)}>Cancelar</Button>
            <Button onClick={handleRename} className="bg-[#E31A1A] hover:bg-red-700">Renomear</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Preview Modal */}
      <Dialog open={showPreviewModal} onOpenChange={closePreviewModal}>
        <DialogContent className="max-w-4xl max-h-[90vh]">
          <DialogHeader>
            <DialogTitle>{previewItem?.name}</DialogTitle>
          </DialogHeader>
          <div className="flex items-center justify-center min-h-[400px] bg-gray-100 rounded-lg overflow-hidden">
            {previewLoading ? (
              <div className="flex flex-col items-center gap-2">
                <Loader2 className="animate-spin text-[#E31A1A]" size={48} />
                <p className="text-gray-500">Carregando preview...</p>
              </div>
            ) : previewItem && previewBlobUrl ? (
              getPreviewType(previewItem.name) === 'pdf' ? (
                <div className="w-full h-[70vh] flex flex-col">
                  <object
                    data={previewBlobUrl}
                    type="application/pdf"
                    className="w-full flex-1"
                  >
                    <div className="flex flex-col items-center justify-center h-full text-gray-500">
                      <FileText size={48} className="mb-4 opacity-50" />
                      <p>Seu navegador não suporta visualização de PDF inline.</p>
                      <Button 
                        onClick={() => window.open(previewBlobUrl, '_blank')}
                        className="mt-4 bg-[#E31A1A] hover:bg-red-700"
                      >
                        Abrir em nova aba
                      </Button>
                    </div>
                  </object>
                </div>
              ) : getPreviewType(previewItem.name) === 'video' ? (
                <video
                  src={previewBlobUrl}
                  controls
                  className="max-w-full max-h-[70vh]"
                >
                  Seu navegador não suporta o elemento de vídeo.
                </video>
              ) : getPreviewType(previewItem.name) === 'image' ? (
                <img
                  src={previewBlobUrl}
                  alt={previewItem.name}
                  className="max-w-full max-h-[70vh] object-contain"
                />
              ) : (
                <div className="text-gray-500 text-center p-8">
                  <FileText size={48} className="mx-auto mb-4 opacity-50" />
                  <p>Este tipo de arquivo não pode ser visualizado.</p>
                  <p className="text-sm mt-2">Clique em "Baixar" para obter o arquivo.</p>
                </div>
              )
            ) : (
              <div className="text-gray-500 text-center p-8">
                <FileText size={48} className="mx-auto mb-4 opacity-50" />
                <p>Erro ao carregar preview.</p>
                <p className="text-sm mt-2">Clique em "Baixar" para obter o arquivo.</p>
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={closePreviewModal}>Fechar</Button>
            <Button onClick={() => previewItem && handleDownload(previewItem)} className="bg-[#E31A1A] hover:bg-red-700">
              <Download size={16} className="mr-2" />
              Baixar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Password Entry Modal */}
      <Dialog open={showPasswordModal} onOpenChange={setShowPasswordModal}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Lock className="text-yellow-500" size={20} />
              Pasta Protegida
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <p className="text-gray-600">
              A pasta <span className="font-medium text-white">"{passwordFolder?.name}"</span> está protegida com senha.
            </p>
            <div>
              <label className="text-sm font-medium text-gray-300 mb-2 block">Digite a senha:</label>
              <Input
                type="password"
                value={folderPassword}
                onChange={(e) => { setFolderPassword(e.target.value); setPasswordError(""); }}
                onKeyDown={(e) => e.key === "Enter" && handlePasswordSubmit()}
                placeholder="Senha da pasta"
                className={passwordError ? "border-red-500" : ""}
              />
              {passwordError && <p className="text-red-500 text-sm mt-1">{passwordError}</p>}
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowPasswordModal(false)}>Cancelar</Button>
            <Button onClick={handlePasswordSubmit} className="bg-[#E31A1A] hover:bg-red-700">
              <KeyRound size={16} className="mr-2" />
              Desbloquear
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Set Password Modal */}
      <Dialog open={showSetPasswordModal} onOpenChange={setShowSetPasswordModal}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              {passwordTargetFolder?.has_password ? <LockOpen className="text-yellow-500" size={20} /> : <Lock className="text-yellow-500" size={20} />}
              {passwordTargetFolder?.has_password ? "Alterar/Remover Senha" : "Definir Senha"}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <p className="text-gray-600">
              Pasta: <span className="font-medium text-white">"{passwordTargetFolder?.name}"</span>
            </p>
            {passwordTargetFolder?.has_password && (
              <div className="bg-yellow-900/20 border border-yellow-600/30 p-3 rounded-lg">
                <p className="text-yellow-500 text-sm">
                  ⚠️ Esta pasta já possui senha. Deixe os campos vazios para remover a proteção.
                </p>
              </div>
            )}
            <div>
              <label className="text-sm font-medium text-gray-300 mb-2 block">Nova senha:</label>
              <Input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder={passwordTargetFolder?.has_password ? "Deixe vazio para remover" : "Digite uma senha"}
              />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-300 mb-2 block">Confirmar senha:</label>
              <Input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSetPassword()}
                placeholder="Confirme a senha"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowSetPasswordModal(false)}>Cancelar</Button>
            <Button onClick={handleSetPassword} className={newPassword ? "bg-[#E31A1A] hover:bg-red-700" : "bg-yellow-600 hover:bg-yellow-700"}>
              {newPassword ? (
                <>
                  <Lock size={16} className="mr-2" />
                  Definir Senha
                </>
              ) : (
                <>
                  <LockOpen size={16} className="mr-2" />
                  Remover Senha
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
