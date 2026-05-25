/**
 * StoragePickerModal
 * --------------------
 * Modal para selecionar arquivos do módulo Armazenamento da plataforma.
 *
 * Funcionalidades:
 * - Navegação por pastas (click expande inline com arquivos)
 * - Barra de busca por nome de arquivo (server-side)
 * - Prompt de senha em pastas protegidas
 * - Multi-seleção
 * - Callback onSelect([{ path, name, size, ... }])
 */
import { useEffect, useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "./ui/dialog";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Checkbox } from "./ui/checkbox";
import {
  Folder,
  FolderOpen,
  FileText,
  Search,
  ChevronRight,
  ChevronDown,
  Loader2,
  Lock,
  ArrowLeft,
} from "lucide-react";
import axios from "axios";
import { toast } from "sonner";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function StoragePickerModal({
  open,
  onClose,
  onSelect,
  title = "Selecionar do Armazenamento",
  multiple = true,
}) {
  const [rootItems, setRootItems] = useState([]);
  const [folderContents, setFolderContents] = useState({}); // { folderPath: [items] }
  const [expanded, setExpanded] = useState({}); // { folderPath: boolean }
  const [loadingFolder, setLoadingFolder] = useState({}); // { folderPath: boolean }
  const [unlocked, setUnlocked] = useState(new Set());
  const [search, setSearch] = useState("");
  const [searchResults, setSearchResults] = useState(null);
  const [searching, setSearching] = useState(false);
  const [selected, setSelected] = useState([]); // array of {path, name, size}
  const [loadingRoot, setLoadingRoot] = useState(false);
  const [passwordPrompt, setPasswordPrompt] = useState({ open: false, path: "", password: "" });

  useEffect(() => {
    if (!open) return;
    setSelected([]);
    setSearch("");
    setSearchResults(null);
    setExpanded({});
    loadRoot();
  }, [open]);

  const loadRoot = async () => {
    setLoadingRoot(true);
    try {
      const r = await axios.get(`${API}/storage/list`, { params: { path: "/" } });
      // Filter out virtual /Sistemas folder (it's a special read-only group)
      const items = (r.data || []).filter((i) => i.name !== "Sistemas");
      setRootItems(items);
    } catch (e) {
      toast.error("Erro ao carregar pastas");
    } finally {
      setLoadingRoot(false);
    }
  };

  const loadFolder = async (folderPath) => {
    setLoadingFolder((p) => ({ ...p, [folderPath]: true }));
    try {
      const r = await axios.get(`${API}/storage/list`, { params: { path: folderPath } });
      setFolderContents((p) => ({ ...p, [folderPath]: r.data || [] }));
    } catch (e) {
      toast.error("Erro ao carregar pasta");
    } finally {
      setLoadingFolder((p) => ({ ...p, [folderPath]: false }));
    }
  };

  const toggleFolder = async (folder) => {
    const path = folder.path;
    // Folder protegida → exige senha primeiro (se ainda não desbloqueada)
    if (folder.has_password && !unlocked.has(path)) {
      setPasswordPrompt({ open: true, path, password: "" });
      return;
    }
    if (expanded[path]) {
      setExpanded((p) => ({ ...p, [path]: false }));
      return;
    }
    if (!folderContents[path]) {
      await loadFolder(path);
    }
    setExpanded((p) => ({ ...p, [path]: true }));
  };

  const confirmPassword = async () => {
    const { path, password } = passwordPrompt;
    if (!password) {
      toast.error("Digite a senha");
      return;
    }
    try {
      const r = await axios.post(`${API}/storage/folder/check-password`, { path, password });
      if (r.data?.ok || r.data?.success || r.status === 200) {
        setUnlocked((p) => new Set(p).add(path));
        setPasswordPrompt({ open: false, path: "", password: "" });
        await loadFolder(path);
        setExpanded((p) => ({ ...p, [path]: true }));
      }
    } catch (e) {
      toast.error("Senha incorreta");
    }
  };

  const runSearch = async () => {
    const term = search.trim();
    if (!term) {
      setSearchResults(null);
      return;
    }
    setSearching(true);
    try {
      const r = await axios.get(`${API}/storage/search`, { params: { q: term } });
      const arr = r.data?.results || r.data || [];
      setSearchResults(arr.filter((i) => i.type === "file"));
    } catch (e) {
      toast.error("Erro na busca");
    } finally {
      setSearching(false);
    }
  };

  const toggleSelect = (file) => {
    const key = file.path;
    const exists = selected.find((s) => s.path === key);
    if (exists) {
      setSelected(selected.filter((s) => s.path !== key));
    } else {
      if (multiple) setSelected([...selected, file]);
      else setSelected([file]);
    }
  };

  const isSelected = (file) => selected.some((s) => s.path === file.path);

  const confirmSelection = () => {
    if (selected.length === 0) {
      toast.error("Selecione ao menos um arquivo");
      return;
    }
    onSelect(selected);
    onClose();
  };

  const showingSearch = searchResults !== null;

  return (
    <>
      <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
        <DialogContent className="max-w-3xl max-h-[85vh] flex flex-col" data-testid="storage-picker-modal">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <FolderOpen size={20} className="text-amber-600" />
              {title}
            </DialogTitle>
          </DialogHeader>

          {/* Barra de busca */}
          <div className="flex gap-2 items-center">
            <div className="relative flex-1">
              <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
              <Input
                placeholder="Buscar por nome do arquivo (em todas as pastas)..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && runSearch()}
                className="pl-9"
                data-testid="storage-search-input"
              />
            </div>
            <Button
              onClick={runSearch}
              disabled={searching}
              variant="secondary"
              data-testid="storage-search-btn"
            >
              {searching ? <Loader2 size={14} className="animate-spin" /> : "Buscar"}
            </Button>
            {showingSearch && (
              <Button
                onClick={() => {
                  setSearch("");
                  setSearchResults(null);
                }}
                variant="ghost"
              >
                <ArrowLeft size={14} className="mr-1" /> Voltar
              </Button>
            )}
          </div>

          {/* Lista */}
          <div className="flex-1 overflow-y-auto border rounded-md bg-gray-50 p-2">
            {loadingRoot ? (
              <div className="flex items-center gap-2 p-4 text-gray-500">
                <Loader2 size={16} className="animate-spin" /> Carregando...
              </div>
            ) : showingSearch ? (
              <SearchResults
                results={searchResults}
                isSelected={isSelected}
                toggleSelect={toggleSelect}
              />
            ) : (
              <StorageFolderTree
                items={rootItems}
                expanded={expanded}
                folderContents={folderContents}
                loadingFolder={loadingFolder}
                toggleFolder={toggleFolder}
                isSelected={isSelected}
                toggleSelect={toggleSelect}
                unlocked={unlocked}
              />
            )}
          </div>

          {/* Footer */}
          <div className="flex items-center justify-between pt-3 border-t">
            <div className="text-sm text-gray-600">
              {selected.length} arquivo(s) selecionado(s)
            </div>
            <div className="flex gap-2">
              <Button variant="ghost" onClick={onClose} data-testid="storage-picker-cancel">
                Cancelar
              </Button>
              <Button
                onClick={confirmSelection}
                disabled={selected.length === 0}
                className="bg-amber-600 hover:bg-amber-700 text-white"
                data-testid="storage-picker-confirm"
              >
                Anexar {selected.length > 0 ? `(${selected.length})` : ""}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Password Prompt */}
      <Dialog
        open={passwordPrompt.open}
        onOpenChange={(v) => !v && setPasswordPrompt({ open: false, path: "", password: "" })}
      >
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Lock size={16} /> Pasta protegida
            </DialogTitle>
          </DialogHeader>
          <p className="text-sm text-gray-600">
            A pasta <span className="font-medium">{passwordPrompt.path}</span> está protegida. Digite a senha para acessá-la.
          </p>
          <Input
            type="password"
            placeholder="Senha da pasta"
            value={passwordPrompt.password}
            onChange={(e) => setPasswordPrompt((p) => ({ ...p, password: e.target.value }))}
            onKeyDown={(e) => e.key === "Enter" && confirmPassword()}
            autoFocus
            data-testid="folder-password-input"
          />
          <DialogFooter>
            <Button
              variant="ghost"
              onClick={() => setPasswordPrompt({ open: false, path: "", password: "" })}
            >
              Cancelar
            </Button>
            <Button onClick={confirmPassword} data-testid="folder-password-confirm">
              Acessar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}

function StorageFolderTree({
  items,
  expanded,
  folderContents,
  loadingFolder,
  toggleFolder,
  isSelected,
  toggleSelect,
  unlocked,
}) {
  if (!items?.length) {
    return <p className="text-sm text-gray-500 p-4 text-center">Nenhuma pasta encontrada</p>;
  }
  return (
    <ul className="space-y-1">
      {items.map((item) => {
        if (item.type === "folder") {
          const isOpen = expanded[item.path];
          const isLoading = loadingFolder[item.path];
          const contents = folderContents[item.path] || [];
          const locked = item.has_password && !unlocked.has(item.path);
          return (
            <li key={item.path}>
              <button
                onClick={() => toggleFolder(item)}
                className="flex items-center gap-2 w-full p-2 rounded hover:bg-amber-100 text-left"
                data-testid={`folder-${item.name}`}
              >
                {isLoading ? (
                  <Loader2 size={14} className="animate-spin shrink-0" />
                ) : isOpen ? (
                  <ChevronDown size={14} className="shrink-0 text-gray-500" />
                ) : (
                  <ChevronRight size={14} className="shrink-0 text-gray-500" />
                )}
                {isOpen ? (
                  <FolderOpen size={16} className="text-amber-600 shrink-0" />
                ) : (
                  <Folder size={16} className="text-amber-600 shrink-0" />
                )}
                <span className="text-sm font-medium text-gray-800 truncate">{item.name}</span>
                {locked && <Lock size={12} className="text-gray-500 shrink-0" />}
                <span className="ml-auto text-xs text-gray-500 shrink-0">
                  {item.items_count} ite{item.items_count === 1 ? "m" : "ns"}
                </span>
              </button>
              {isOpen && (
                <div className="ml-6 mt-1 space-y-1 border-l-2 border-amber-200 pl-2">
                  {contents.length === 0 ? (
                    <p className="text-xs text-gray-500 p-2">Pasta vazia</p>
                  ) : (
                    contents.map((sub) => {
                      if (sub.type === "folder") {
                        // Permite navegação recursiva
                        const subOpen = expanded[sub.path];
                        const subLoading = loadingFolder[sub.path];
                        return (
                          <div key={sub.path}>
                            <button
                              onClick={() => toggleFolder(sub)}
                              className="flex items-center gap-2 w-full p-1.5 rounded hover:bg-amber-100 text-left"
                            >
                              {subLoading ? (
                                <Loader2 size={12} className="animate-spin shrink-0" />
                              ) : subOpen ? (
                                <ChevronDown size={12} className="shrink-0 text-gray-500" />
                              ) : (
                                <ChevronRight size={12} className="shrink-0 text-gray-500" />
                              )}
                              <Folder size={14} className="text-amber-600 shrink-0" />
                              <span className="text-sm text-gray-700 truncate">{sub.name}</span>
                            </button>
                            {subOpen && folderContents[sub.path] && (
                              <div className="ml-6 mt-1 space-y-1 border-l-2 border-amber-200 pl-2">
                                {folderContents[sub.path].map((nested) =>
                                  nested.type === "file" ? (
                                    <FileRow
                                      key={nested.path}
                                      file={nested}
                                      selected={isSelected(nested)}
                                      onToggle={() => toggleSelect(nested)}
                                    />
                                  ) : null,
                                )}
                              </div>
                            )}
                          </div>
                        );
                      }
                      return (
                        <FileRow
                          key={sub.path}
                          file={sub}
                          selected={isSelected(sub)}
                          onToggle={() => toggleSelect(sub)}
                        />
                      );
                    })
                  )}
                </div>
              )}
            </li>
          );
        }
        // Root-level file
        return (
          <FileRow
            key={item.path}
            file={item}
            selected={isSelected(item)}
            onToggle={() => toggleSelect(item)}
          />
        );
      })}
    </ul>
  );
}

function FileRow({ file, selected, onToggle }) {
  return (
    <label
      className={`flex items-center gap-2 p-1.5 rounded cursor-pointer transition-colors ${
        selected ? "bg-amber-200 hover:bg-amber-200" : "hover:bg-amber-50"
      }`}
      data-testid={`file-${file.name}`}
    >
      <Checkbox checked={selected} onCheckedChange={onToggle} className="shrink-0" />
      <FileText size={14} className="text-gray-500 shrink-0" />
      <span className="text-sm text-gray-800 truncate flex-1">{file.name}</span>
      <span className="text-xs text-gray-500 shrink-0">
        {file.size ? formatSize(file.size) : ""}
      </span>
    </label>
  );
}

function SearchResults({ results, isSelected, toggleSelect }) {
  if (!results.length) {
    return <p className="text-sm text-gray-500 p-4 text-center">Nenhum arquivo encontrado</p>;
  }
  return (
    <div className="space-y-1">
      {results.map((file) => (
        <div key={file.path}>
          <FileRow
            file={file}
            selected={isSelected(file)}
            onToggle={() => toggleSelect(file)}
          />
          <div className="text-xs text-gray-400 ml-8 -mt-1 mb-1">{file.path}</div>
        </div>
      ))}
    </div>
  );
}

function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
