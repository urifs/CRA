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
  LogOut
} from "lucide-react";

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
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [viewMode, setViewMode] = useState("grid"); // "grid" or "list"
  const [currentPath, setCurrentPath] = useState(searchParams.get("path") || "/");
  const [breadcrumbs, setBreadcrumbs] = useState([{ name: "Início", path: "/" }]);

  // Modals
  const [showNewFolderModal, setShowNewFolderModal] = useState(false);
  const [newFolderName, setNewFolderName] = useState("");
  const [showRenameModal, setShowRenameModal] = useState(false);
  const [renameItem, setRenameItem] = useState(null);
  const [newName, setNewName] = useState("");
  const [showPreviewModal, setShowPreviewModal] = useState(false);
  const [previewItem, setPreviewItem] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  const token = localStorage.getItem("token");

  useEffect(() => {
    fetchItems();
    updateBreadcrumbs();
  }, [currentPath]);

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
        { name: newFolderName, parent_path: currentPath },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success("Pasta criada com sucesso!");
      setShowNewFolderModal(false);
      setNewFolderName("");
      fetchItems();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao criar pasta");
    }
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
    if (!confirm(`Excluir "${item.name}"?`)) return;
    try {
      await axios.delete(`${API}/storage/delete`, {
        params: { path: item.path },
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success("Item excluído!");
      fetchItems();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao excluir");
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

  const handlePreview = (item) => {
    setPreviewItem(item);
    setShowPreviewModal(true);
  };

  const isPreviewable = (filename) => {
    const ext = filename.split('.').pop()?.toLowerCase();
    return ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg', 'pdf'].includes(ext);
  };

  const filteredItems = items.filter(item =>
    item.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const folders = filteredItems.filter(i => i.type === "folder");
  const files = filteredItems.filter(i => i.type === "file");

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-[#E31A1A] text-white sticky top-0 z-40">
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

      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Toolbar */}
        <div className="flex flex-col sm:flex-row gap-4 mb-6">
          {/* Search */}
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
            <Input
              placeholder="Pesquisar arquivos..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 pr-10"
            />
            {searchTerm && (
              <button className="absolute right-3 top-1/2 -translate-y-1/2" onClick={() => setSearchTerm("")}>
                <X size={16} className="text-gray-400" />
              </button>
            )}
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={() => setShowNewFolderModal(true)}>
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
            <div className="flex border rounded-md">
              <Button variant={viewMode === "grid" ? "secondary" : "ghost"} size="sm" className="rounded-r-none" onClick={() => setViewMode("grid")}>
                <Grid size={18} />
              </Button>
              <Button variant={viewMode === "list" ? "secondary" : "ghost"} size="sm" className="rounded-l-none" onClick={() => setViewMode("list")}>
                <List size={18} />
              </Button>
            </div>
          </div>
        </div>

        {/* Upload Progress */}
        {uploading && (
          <div className="mb-4 bg-red-50 rounded-lg p-4">
            <div className="flex items-center gap-3">
              <Loader2 className="animate-spin text-[#E31A1A]" size={20} />
              <span className="text-red-700">Enviando... {uploadProgress}%</span>
            </div>
            <div className="mt-2 bg-red-200 rounded-full h-2">
              <div className="bg-[#E31A1A] h-2 rounded-full transition-all" style={{ width: `${uploadProgress}%` }} />
            </div>
          </div>
        )}

        {/* Breadcrumbs */}
        <div className="flex items-center gap-1 text-sm mb-4 overflow-x-auto pb-2">
          {breadcrumbs.map((crumb, index) => (
            <div key={crumb.path} className="flex items-center gap-1 whitespace-nowrap">
              {index > 0 && <ChevronRight size={14} className="text-gray-400" />}
              <button
                onClick={() => handleNavigate(crumb.path)}
                className={`hover:text-[#E31A1A] ${index === breadcrumbs.length - 1 ? 'text-[#E31A1A] font-medium' : 'text-gray-600'}`}
              >
                {index === 0 ? <Home size={16} /> : crumb.name}
              </button>
            </div>
          ))}
        </div>

        {/* Content */}
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="animate-spin text-blue-600" size={40} />
          </div>
        ) : filteredItems.length === 0 ? (
          <div className="text-center py-20">
            <FolderOpen size={64} className="mx-auto text-gray-300 mb-4" />
            <p className="text-gray-500 mb-4">
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
                className="hover:shadow-lg cursor-pointer transition-all group"
                onDoubleClick={() => handleNavigate(item.path)}
              >
                <CardContent className="p-4 text-center relative">
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="sm" className="absolute top-1 right-1 opacity-0 group-hover:opacity-100">
                        <MoreVertical size={16} />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent>
                      <DropdownMenuItem onClick={() => { setRenameItem(item); setNewName(item.name); setShowRenameModal(true); }}>
                        <Edit size={14} className="mr-2" /> Renomear
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => handleDelete(item)} className="text-red-600">
                        <Trash2 size={14} className="mr-2" /> Excluir
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                  <FolderOpen size={48} className="mx-auto text-[#D4A000] mb-2" />
                  <p className="text-sm font-medium truncate">{item.name}</p>
                  <p className="text-xs text-gray-400">{item.items_count || 0} itens</p>
                </CardContent>
              </Card>
            ))}
            {/* Then files */}
            {files.map((item) => {
              const fileType = getFileIcon(item.name);
              const FileIcon = fileType.icon;
              return (
                <Card
                  key={item.path}
                  className="hover:shadow-lg cursor-pointer transition-all group"
                  onDoubleClick={() => isPreviewable(item.name) ? handlePreview(item) : handleDownload(item)}
                >
                  <CardContent className="p-4 text-center relative">
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="sm" className="absolute top-1 right-1 opacity-0 group-hover:opacity-100">
                          <MoreVertical size={16} />
                        </Button>
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
                    <FileIcon size={48} className={`mx-auto ${fileType.color} mb-2`} />
                    <p className="text-sm font-medium truncate">{item.name}</p>
                    <p className="text-xs text-gray-400">{formatFileSize(item.size)}</p>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        ) : (
          <Card>
            <CardContent className="p-0">
              <table className="w-full">
                <thead className="bg-gray-50 border-b">
                  <tr>
                    <th className="text-left p-3 font-medium text-gray-600">Nome</th>
                    <th className="text-left p-3 font-medium text-gray-600 hidden sm:table-cell">Tamanho</th>
                    <th className="text-left p-3 font-medium text-gray-600 hidden md:table-cell">Modificado</th>
                    <th className="text-right p-3 font-medium text-gray-600">Ações</th>
                  </tr>
                </thead>
                <tbody>
                  {folders.map((item) => (
                    <tr key={item.path} className="border-b hover:bg-gray-50 cursor-pointer" onDoubleClick={() => handleNavigate(item.path)}>
                      <td className="p-3">
                        <div className="flex items-center gap-3">
                          <FolderOpen size={24} className="text-[#D4A000]" />
                          <span className="font-medium">{item.name}</span>
                        </div>
                      </td>
                      <td className="p-3 text-gray-500 hidden sm:table-cell">{item.items_count || 0} itens</td>
                      <td className="p-3 text-gray-500 hidden md:table-cell">{new Date(item.modified_at).toLocaleDateString("pt-BR")}</td>
                      <td className="p-3 text-right">
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="sm"><MoreVertical size={16} /></Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent>
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
                  ))}
                  {files.map((item) => {
                    const fileType = getFileIcon(item.name);
                    const FileIcon = fileType.icon;
                    return (
                      <tr key={item.path} className="border-b hover:bg-gray-50 cursor-pointer" onDoubleClick={() => handleDownload(item)}>
                        <td className="p-3">
                          <div className="flex items-center gap-3">
                            <FileIcon size={24} className={fileType.color} />
                            <span>{item.name}</span>
                          </div>
                        </td>
                        <td className="p-3 text-gray-500 hidden sm:table-cell">{formatFileSize(item.size)}</td>
                        <td className="p-3 text-gray-500 hidden md:table-cell">{new Date(item.modified_at).toLocaleDateString("pt-BR")}</td>
                        <td className="p-3 text-right">
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" size="sm"><MoreVertical size={16} /></Button>
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
            <DialogTitle>Nova Pasta</DialogTitle>
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
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowNewFolderModal(false)}>Cancelar</Button>
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
            <Button onClick={handleRename} className="bg-blue-600 hover:bg-blue-700">Renomear</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Preview Modal */}
      <Dialog open={showPreviewModal} onOpenChange={setShowPreviewModal}>
        <DialogContent className="max-w-4xl max-h-[90vh]">
          <DialogHeader>
            <DialogTitle>{previewItem?.name}</DialogTitle>
          </DialogHeader>
          <div className="flex items-center justify-center min-h-[400px] bg-gray-100 rounded-lg overflow-hidden">
            {previewItem && (
              previewItem.name.toLowerCase().endsWith('.pdf') ? (
                <iframe
                  src={`${API}/storage/download?path=${encodeURIComponent(previewItem.path)}&token=${token}`}
                  className="w-full h-[70vh]"
                />
              ) : (
                <img
                  src={`${API}/storage/download?path=${encodeURIComponent(previewItem.path)}&token=${token}`}
                  alt={previewItem.name}
                  className="max-w-full max-h-[70vh] object-contain"
                />
              )
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowPreviewModal(false)}>Fechar</Button>
            <Button onClick={() => previewItem && handleDownload(previewItem)} className="bg-blue-600 hover:bg-blue-700">
              <Download size={16} className="mr-2" />
              Baixar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
