/**
 * AnexosManager
 * --------------
 * Componente reutilizável para gerenciar anexos de qualquer entidade do ERP.
 *
 * Props:
 * - entityType: tipo da entidade (ex: "funcionario", "produto", "maquina")
 * - entityId: ID da entidade. Se null/undefined → modo "create" (mantém pendentes em memória).
 * - onPendingChange: callback chamado quando anexos pendentes mudam (para o pai persistir após criar a entidade)
 * - title: título da seção (opcional)
 *
 * API exposta via ref (forwardRef):
 * - flushPending(newEntityId): após o pai criar a entidade, chama este método com o novo ID
 *   para fazer o upload dos anexos pendentes.
 */
import {
  forwardRef,
  useEffect,
  useImperativeHandle,
  useRef,
  useState,
} from "react";
import { Button } from "./ui/button";
import {
  Paperclip,
  Upload,
  X,
  Download,
  Loader2,
  FileText,
  HardDrive,
  Cloud,
  Eye,
} from "lucide-react";
import axios from "axios";
import { toast } from "sonner";
import StoragePickerModal from "./StoragePickerModal";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "./ui/dialog";
import { useAuth } from "../App";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const AnexosManager = forwardRef(function AnexosManager(
  { entityType, entityId, onPendingChange, title = "Anexos", disabled = false },
  ref,
) {
  const [anexos, setAnexos] = useState([]);
  const [pendingFiles, setPendingFiles] = useState([]); // local files queued for upload (create mode)
  const [pendingStorage, setPendingStorage] = useState([]); // storage refs queued (create mode)
  const [uploading, setUploading] = useState(false);
  const [pickerOpen, setPickerOpen] = useState(false);
  const [preview, setPreview] = useState({ open: false, anexo: null });
  const fileInputRef = useRef(null);
  const { token } = useAuth();

  const isCreateMode = !entityId;

  useEffect(() => {
    if (entityId) loadAnexos();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [entityId, entityType]);

  useEffect(() => {
    onPendingChange?.({ files: pendingFiles, storage: pendingStorage });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pendingFiles, pendingStorage]);

  useImperativeHandle(ref, () => ({
    flushPending: async (newEntityId) => {
      if (!newEntityId) return;
      const created = [];
      for (const file of pendingFiles) {
        try {
          const fd = new FormData();
          fd.append("file", file);
          const r = await axios.post(
            `${API}/anexos/${entityType}/${newEntityId}/upload`,
            fd,
            { headers: { "Content-Type": "multipart/form-data" } },
          );
          created.push(r.data?.anexo);
        } catch (e) {
          toast.error(`Falha ao enviar ${file.name}`);
        }
      }
      if (pendingStorage.length > 0) {
        try {
          await axios.post(`${API}/anexos/${entityType}/${newEntityId}/from-storage`, {
            storage_paths: pendingStorage.map((s) => s.path),
          });
        } catch (e) {
          toast.error("Falha ao vincular arquivos do armazenamento");
        }
      }
      setPendingFiles([]);
      setPendingStorage([]);
      return created;
    },
    hasPending: () => pendingFiles.length > 0 || pendingStorage.length > 0,
  }));

  const loadAnexos = async () => {
    try {
      const r = await axios.get(`${API}/anexos/${entityType}/${entityId}`);
      setAnexos(r.data?.items || []);
    } catch (e) {
      // Silencioso em modo criação
    }
  };

  const handleLocalUpload = async (e) => {
    const files = Array.from(e.target.files || []);
    if (!files.length) return;

    if (isCreateMode) {
      setPendingFiles((p) => [...p, ...files]);
      if (fileInputRef.current) fileInputRef.current.value = "";
      return;
    }

    setUploading(true);
    try {
      for (const file of files) {
        const fd = new FormData();
        fd.append("file", file);
        await axios.post(`${API}/anexos/${entityType}/${entityId}/upload`, fd, {
          headers: { "Content-Type": "multipart/form-data" },
        });
      }
      toast.success(`${files.length} anexo(s) enviado(s)`);
      await loadAnexos();
    } catch (e) {
      toast.error("Erro ao enviar anexo");
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const handleStorageSelect = async (items) => {
    if (isCreateMode) {
      setPendingStorage((p) => [...p, ...items]);
      return;
    }

    setUploading(true);
    try {
      await axios.post(`${API}/anexos/${entityType}/${entityId}/from-storage`, {
        storage_paths: items.map((i) => i.path),
      });
      toast.success(`${items.length} arquivo(s) vinculado(s) do armazenamento`);
      await loadAnexos();
    } catch (e) {
      toast.error("Erro ao vincular arquivo do armazenamento");
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (anexo) => {
    if (!confirm(`Remover anexo "${anexo.original_name}"?`)) return;
    try {
      await axios.delete(`${API}/anexos/${entityType}/${entityId}/${anexo.id}`);
      toast.success("Anexo removido");
      await loadAnexos();
    } catch (e) {
      toast.error("Erro ao remover anexo");
    }
  };

  const handleRemovePending = (type, index) => {
    if (type === "file") setPendingFiles(pendingFiles.filter((_, i) => i !== index));
    else setPendingStorage(pendingStorage.filter((_, i) => i !== index));
  };

  const handleDownload = async (anexo) => {
    try {
      const r = await axios.get(`${API}/anexos/download/${anexo.id}`, {
        responseType: "blob",
      });
      const url = window.URL.createObjectURL(new Blob([r.data]));
      const a = document.createElement("a");
      a.href = url;
      a.download = anexo.original_name;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (e) {
      toast.error("Erro ao baixar anexo");
    }
  };

  const totalCount =
    anexos.length + pendingFiles.length + pendingStorage.length;

  return (
    <div className="border-2 border-dashed border-amber-300 rounded-lg p-3 bg-amber-50/40 space-y-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Paperclip size={16} className="text-amber-700" />
          <span className="text-sm font-semibold text-amber-900">
            {title} {totalCount > 0 && <span className="text-amber-700">({totalCount})</span>}
          </span>
        </div>
        <div className="flex gap-1.5">
          <input
            ref={fileInputRef}
            type="file"
            multiple
            className="hidden"
            onChange={handleLocalUpload}
            data-testid={`anexo-file-input-${entityType}`}
          />
          <Button
            type="button"
            size="sm"
            variant="outline"
            onClick={() => fileInputRef.current?.click()}
            disabled={disabled || uploading}
            className="border-amber-400 text-amber-800 hover:bg-amber-100"
            data-testid={`anexo-local-btn-${entityType}`}
          >
            {uploading ? (
              <Loader2 size={13} className="animate-spin mr-1" />
            ) : (
              <Upload size={13} className="mr-1" />
            )}
            <HardDrive size={13} className="mr-1" />
            Do computador
          </Button>
          <Button
            type="button"
            size="sm"
            variant="outline"
            onClick={() => setPickerOpen(true)}
            disabled={disabled || uploading}
            className="border-amber-400 text-amber-800 hover:bg-amber-100"
            data-testid={`anexo-storage-btn-${entityType}`}
          >
            <Cloud size={13} className="mr-1" />
            Do armazenamento
          </Button>
        </div>
      </div>

      {/* Aviso para modo criação */}
      {isCreateMode && totalCount === 0 && (
        <p className="text-xs text-amber-700 italic">
          Os anexos selecionados serão enviados automaticamente após salvar.
        </p>
      )}

      {/* Lista de anexos */}
      <ul className="space-y-1 max-h-40 overflow-y-auto">
        {anexos.map((a) => (
          <li
            key={a.id}
            className="flex items-center gap-2 bg-white border border-gray-200 rounded px-2 py-1.5 text-xs"
            data-testid={`anexo-item-${a.id}`}
          >
            <FileText size={13} className="text-gray-500 shrink-0" />
            {a.source === "storage" ? (
              <Cloud size={11} className="text-amber-600 shrink-0" title="Vinculado do armazenamento" />
            ) : (
              <HardDrive size={11} className="text-blue-600 shrink-0" title="Enviado do computador" />
            )}
            <span className="flex-1 truncate text-gray-800">{a.original_name}</span>
            <span className="text-[10px] text-gray-500 shrink-0">
              {formatSize(a.size)}
            </span>
            <Button
              type="button"
              size="sm"
              variant="ghost"
              onClick={() => setPreview({ open: true, anexo: a })}
              className="h-6 w-6 p-0 text-amber-700 hover:text-amber-800"
              title="Visualizar"
              data-testid={`anexo-preview-btn-${a.id}`}
            >
              <Eye size={12} />
            </Button>
            <Button
              type="button"
              size="sm"
              variant="ghost"
              onClick={() => handleDownload(a)}
              className="h-6 w-6 p-0"
              title="Baixar"
            >
              <Download size={12} />
            </Button>
            <Button
              type="button"
              size="sm"
              variant="ghost"
              onClick={() => handleDelete(a)}
              className="h-6 w-6 p-0 text-red-600 hover:text-red-700"
              title="Remover"
            >
              <X size={12} />
            </Button>
          </li>
        ))}
        {pendingFiles.map((f, idx) => (
          <li
            key={`pending-file-${idx}`}
            className="flex items-center gap-2 bg-blue-50 border border-blue-200 rounded px-2 py-1.5 text-xs"
          >
            <HardDrive size={11} className="text-blue-600 shrink-0" />
            <span className="flex-1 truncate text-blue-900">{f.name}</span>
            <span className="text-[10px] text-blue-700 shrink-0 italic">pendente</span>
            <Button
              type="button"
              size="sm"
              variant="ghost"
              onClick={() => handleRemovePending("file", idx)}
              className="h-6 w-6 p-0 text-red-600 hover:text-red-700"
            >
              <X size={12} />
            </Button>
          </li>
        ))}
        {pendingStorage.map((s, idx) => (
          <li
            key={`pending-storage-${idx}`}
            className="flex items-center gap-2 bg-amber-50 border border-amber-200 rounded px-2 py-1.5 text-xs"
          >
            <Cloud size={11} className="text-amber-600 shrink-0" />
            <span className="flex-1 truncate text-amber-900">{s.name}</span>
            <span className="text-[10px] text-amber-700 shrink-0 italic">pendente</span>
            <Button
              type="button"
              size="sm"
              variant="ghost"
              onClick={() => handleRemovePending("storage", idx)}
              className="h-6 w-6 p-0 text-red-600 hover:text-red-700"
            >
              <X size={12} />
            </Button>
          </li>
        ))}
      </ul>

      <StoragePickerModal
        open={pickerOpen}
        onClose={() => setPickerOpen(false)}
        onSelect={handleStorageSelect}
      />

      <PreviewDialog
        preview={preview}
        onClose={() => setPreview({ open: false, anexo: null })}
        token={token}
        onDownload={handleDownload}
      />
    </div>
  );
});

function PreviewDialog({ preview, onClose, token, onDownload }) {
  const { open, anexo } = preview;
  if (!anexo) return null;

  const ext = (anexo.original_name || "").split(".").pop().toLowerCase();
  const isImage = ["jpg", "jpeg", "png", "gif", "webp", "svg", "bmp"].includes(ext);
  const isPdf = ext === "pdf";
  const isVideo = ["mp4", "webm", "ogg"].includes(ext);
  const isAudio = ["mp3", "wav", "ogg", "aac"].includes(ext);
  const isText = ["txt", "csv", "json", "xml", "md", "log"].includes(ext);

  const url = `${API}/anexos/download/${anexo.id}?token=${encodeURIComponent(token || "")}`;

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="max-w-4xl max-h-[90vh] flex flex-col" data-testid="anexo-preview-modal">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 pr-8">
            <FileText size={16} className="text-gray-500 shrink-0" />
            <span className="truncate">{anexo.original_name}</span>
            <span className="text-xs font-normal text-gray-500">({formatSize(anexo.size)})</span>
          </DialogTitle>
        </DialogHeader>
        <div className="flex-1 overflow-auto flex items-center justify-center bg-gray-100 rounded-md min-h-[400px]">
          {isImage && (
            <img
              src={url}
              alt={anexo.original_name}
              className="max-w-full max-h-[70vh] object-contain"
            />
          )}
          {isPdf && (
            <iframe
              src={url}
              title={anexo.original_name}
              className="w-full h-[70vh] border-0"
            />
          )}
          {isVideo && (
            <video controls src={url} className="max-w-full max-h-[70vh]" />
          )}
          {isAudio && <audio controls src={url} className="w-full" />}
          {isText && (
            <iframe
              src={url}
              title={anexo.original_name}
              className="w-full h-[70vh] border-0 bg-white"
            />
          )}
          {!isImage && !isPdf && !isVideo && !isAudio && !isText && (
            <div className="flex flex-col items-center gap-3 p-8 text-gray-600">
              <FileText size={48} className="text-gray-400" />
              <p className="text-sm">
                Preview não disponível para arquivos <span className="font-semibold">.{ext}</span>
              </p>
              <Button
                type="button"
                onClick={() => onDownload(anexo)}
                className="bg-amber-600 hover:bg-amber-700 text-white"
              >
                <Download size={14} className="mr-1.5" />
                Baixar arquivo
              </Button>
            </div>
          )}
        </div>
        <div className="flex justify-end gap-2 pt-2 border-t">
          <Button
            type="button"
            variant="outline"
            onClick={() => onDownload(anexo)}
            data-testid="anexo-preview-download"
          >
            <Download size={14} className="mr-1.5" />
            Baixar
          </Button>
          <Button type="button" onClick={onClose} data-testid="anexo-preview-close">
            Fechar
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}

function formatSize(bytes) {
  if (!bytes) return "";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default AnexosManager;
