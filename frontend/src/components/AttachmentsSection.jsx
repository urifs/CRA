import { useState, useEffect, useRef } from "react";
import axios from "axios";
import { API, useAuth } from "@/App";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { toast } from "sonner";
import { 
  Paperclip, 
  Upload, 
  File, 
  FileText, 
  Image, 
  Trash2, 
  Download, 
  Loader2,
  X,
  Eye
} from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

const getFileIcon = (fileType) => {
  if (fileType?.startsWith("image/")) return Image;
  if (fileType?.includes("pdf")) return FileText;
  return File;
};

const formatFileSize = (bytes) => {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

export default function AttachmentsSection({ entityType, entityId, accentColor = "#D4A000" }) {
  const { token } = useAuth();
  const [attachments, setAttachments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [previewType, setPreviewType] = useState(null);
  const [previewName, setPreviewName] = useState(null);
  const [loadingPreview, setLoadingPreview] = useState(false);
  const fileInputRef = useRef(null);

  useEffect(() => {
    if (entityId) {
      fetchAttachments();
    }
  }, [entityId]);

  const fetchAttachments = async () => {
    if (!entityId) return;
    setLoading(true);
    try {
      const response = await axios.get(
        `${API}/attachments/${entityType}/${entityId}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setAttachments(response.data);
    } catch (error) {
      console.error("Erro ao carregar anexos:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleFileSelect = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validações
    const allowedTypes = ['application/pdf', 'image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/webp'];
    if (!allowedTypes.includes(file.type)) {
      toast.error("Tipo de arquivo não permitido. Use PDF ou imagens.");
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      toast.error("Arquivo muito grande. Máximo: 10MB");
      return;
    }

    setUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("entity_type", entityType);
      formData.append("entity_id", entityId);

      await axios.post(`${API}/attachments/upload`, formData, {
        headers: { 
          Authorization: `Bearer ${token}`,
          "Content-Type": "multipart/form-data"
        }
      });

      toast.success("Arquivo anexado com sucesso!");
      fetchAttachments();
    } catch (error) {
      console.error("Erro ao enviar arquivo:", error);
      toast.error("Erro ao enviar arquivo");
    } finally {
      setUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  const handleDelete = async (attachmentId, filename) => {
    if (!confirm(`Remover anexo "${filename}"?`)) return;

    try {
      await axios.delete(`${API}/attachments/${attachmentId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success("Anexo removido!");
      fetchAttachments();
    } catch (error) {
      console.error("Erro ao remover anexo:", error);
      toast.error("Erro ao remover anexo");
    }
  };

  const handleDownload = async (attachmentId, filename) => {
    try {
      const response = await axios.get(`${API}/attachments/download/${attachmentId}`, {
        headers: { Authorization: `Bearer ${token}` },
        responseType: 'blob'
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error("Erro ao baixar arquivo:", error);
      toast.error("Erro ao baixar arquivo");
    }
  };

  const handlePreview = async (attachment) => {
    setLoadingPreview(true);
    try {
      const response = await axios.get(`${API}/attachments/download/${attachment.id}`, {
        headers: { Authorization: `Bearer ${token}` },
        responseType: 'blob'
      });
      
      const blob = new Blob([response.data], { type: attachment.file_type });
      const url = window.URL.createObjectURL(blob);
      setPreviewUrl(url);
      setPreviewName(attachment.filename);
      
      if (attachment.file_type?.startsWith("image/")) {
        setPreviewType("image");
      } else if (attachment.file_type?.includes("pdf")) {
        setPreviewType("pdf");
      }
    } catch (error) {
      toast.error("Erro ao carregar visualização");
    } finally {
      setLoadingPreview(false);
    }
  };

  const closePreview = () => {
    if (previewUrl) {
      window.URL.revokeObjectURL(previewUrl);
    }
    setPreviewUrl(null);
    setPreviewType(null);
    setPreviewName(null);
  };

  if (!entityId) {
    return (
      <div className="border border-dashed border-gray-300 rounded-lg p-4 text-center text-gray-500">
        <Paperclip size={24} className="mx-auto mb-2 opacity-50" />
        <p className="text-sm">Salve o registro para anexar arquivos</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-medium text-gray-700 flex items-center gap-2">
          <Paperclip size={16} style={{ color: accentColor }} />
          Anexos ({attachments.length})
        </h4>
        <div>
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.png,.jpg,.jpeg,.gif,.webp"
            onChange={handleFileSelect}
            className="hidden"
            id={`file-upload-${entityId}`}
          />
          <Button
            variant="outline"
            size="sm"
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
            className="text-xs"
          >
            {uploading ? (
              <Loader2 size={14} className="animate-spin mr-1" />
            ) : (
              <Upload size={14} className="mr-1" />
            )}
            Anexar
          </Button>
        </div>
      </div>

      {/* Lista de anexos */}
      {loading ? (
        <div className="flex justify-center py-4">
          <Loader2 size={20} className="animate-spin text-gray-400" />
        </div>
      ) : attachments.length === 0 ? (
        <div className="border border-dashed border-gray-200 rounded-lg p-4 text-center text-gray-400">
          <p className="text-sm">Nenhum anexo</p>
        </div>
      ) : (
        <div className="space-y-2">
          {attachments.map((attachment) => {
            const FileIcon = getFileIcon(attachment.file_type);
            const isImage = attachment.file_type?.startsWith("image/");
            const isPdf = attachment.file_type?.includes("pdf");
            const canPreview = isImage || isPdf;

            return (
              <div 
                key={attachment.id}
                className="flex items-center gap-3 p-2 bg-gray-50 rounded-lg border border-gray-100 hover:border-gray-200 transition-colors"
              >
                <div 
                  className="w-8 h-8 rounded flex items-center justify-center shrink-0"
                  style={{ backgroundColor: `${accentColor}15` }}
                >
                  <FileIcon size={16} style={{ color: accentColor }} />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {attachment.filename}
                  </p>
                  <p className="text-xs text-gray-500">
                    {formatFileSize(attachment.file_size)} • {new Date(attachment.created_at).toLocaleDateString("pt-BR")}
                  </p>
                </div>
                <div className="flex items-center gap-1 shrink-0">
                  {canPreview && (
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="h-7 w-7 p-0 text-gray-400 hover:text-gray-600"
                      onClick={() => handlePreview(attachment)}
                      title="Visualizar"
                    >
                      <Eye size={14} />
                    </Button>
                  )}
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="h-7 w-7 p-0 text-gray-400 hover:text-blue-600"
                    onClick={() => handleDownload(attachment.id, attachment.filename)}
                    title="Baixar"
                  >
                    <Download size={14} />
                  </Button>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="h-7 w-7 p-0 text-gray-400 hover:text-red-600"
                    onClick={() => handleDelete(attachment.id, attachment.filename)}
                    title="Excluir"
                  >
                    <Trash2 size={14} />
                  </Button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Preview Modal */}
      <Dialog open={!!previewUrl} onOpenChange={closePreview}>
        <DialogContent className="max-w-4xl max-h-[90vh] p-0 overflow-hidden">
          <DialogHeader className="p-4 border-b bg-gray-50">
            <div className="flex items-center justify-between">
              <DialogTitle className="text-base font-medium truncate pr-4">
                {previewName || "Visualização"}
              </DialogTitle>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  className="h-8"
                  onClick={() => {
                    const link = document.createElement('a');
                    link.href = previewUrl;
                    link.setAttribute('download', previewName || 'arquivo');
                    document.body.appendChild(link);
                    link.click();
                    link.remove();
                  }}
                >
                  <Download size={14} className="mr-1" />
                  Baixar
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-8 w-8 p-0"
                  onClick={closePreview}
                >
                  <X size={16} />
                </Button>
              </div>
            </div>
          </DialogHeader>
          
          <div className="flex-1 overflow-auto bg-gray-100">
            {loadingPreview ? (
              <div className="flex items-center justify-center h-[60vh]">
                <Loader2 size={32} className="animate-spin text-gray-400" />
              </div>
            ) : previewType === "image" && previewUrl ? (
              <div className="flex items-center justify-center p-4 min-h-[60vh]">
                <img 
                  src={previewUrl} 
                  alt={previewName || "Preview"} 
                  className="max-h-[75vh] max-w-full object-contain rounded shadow-lg"
                />
              </div>
            ) : previewType === "pdf" && previewUrl ? (
              <iframe
                src={previewUrl}
                title={previewName || "PDF Preview"}
                className="w-full h-[75vh] border-0"
              />
            ) : null}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
