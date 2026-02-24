import { useState, useEffect, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import { API } from "@/App";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { 
  ArrowLeft, 
  Calendar,
  Shield,
  AlertTriangle,
  Truck,
  DollarSign,
  ImagePlus,
  Trash2,
  Loader2,
  X,
  ZoomIn
} from "lucide-react";
import {
  Dialog,
  DialogContent,
} from "@/components/ui/dialog";

export default function MaintenanceDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const fileInputRef = useRef(null);
  
  const [maintenance, setMaintenance] = useState(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [selectedPhoto, setSelectedPhoto] = useState(null);

  useEffect(() => {
    fetchMaintenance();
  }, [id]);

  const fetchMaintenance = async () => {
    try {
      const response = await axios.get(`${API}/maintenances/${id}`);
      setMaintenance(response.data);
    } catch (error) {
      toast.error("Erro ao carregar manutenção");
      navigate("/maintenances");
    } finally {
      setLoading(false);
    }
  };

  const handleFileSelect = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Check file type
    if (!file.type.startsWith("image/")) {
      toast.error("Por favor, selecione uma imagem");
      return;
    }

    // Check file size (max 5MB)
    if (file.size > 5 * 1024 * 1024) {
      toast.error("A imagem deve ter no máximo 5MB");
      return;
    }

    setUploading(true);
    
    try {
      const formData = new FormData();
      formData.append("file", file);
      
      await axios.post(`${API}/maintenances/${id}/photos`, formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      
      toast.success("Foto adicionada com sucesso!");
      fetchMaintenance();
    } catch (error) {
      toast.error("Erro ao enviar foto");
    } finally {
      setUploading(false);
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  const handleDeletePhoto = async (index) => {
    try {
      await axios.delete(`${API}/maintenances/${id}/photos/${index}`);
      toast.success("Foto removida com sucesso!");
      fetchMaintenance();
    } catch (error) {
      toast.error("Erro ao remover foto");
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat("pt-BR", {
      style: "currency",
      currency: "BRL"
    }).format(value);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString("pt-BR");
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="spinner w-12 h-12"></div>
      </div>
    );
  }

  if (!maintenance) {
    return null;
  }

  return (
    <div className="space-y-6 animate-fade-in" data-testid="maintenance-detail-page">
      {/* Back button */}
      <Button
        variant="ghost"
        onClick={() => navigate("/maintenances")}
        className="text-slate-600 hover:text-slate-900"
        data-testid="back-btn"
      >
        <ArrowLeft size={18} className="mr-2" />
        Voltar para Manutenções
      </Button>

      {/* Header Card */}
      <Card>
        <CardContent className="p-6">
          <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
            <div className="flex items-start gap-4">
              <div className={`w-14 h-14 rounded-xl flex items-center justify-center ${
                maintenance.maintenance_type === "preventiva" 
                  ? "bg-green-100" 
                  : "bg-orange-100"
              }`}>
                {maintenance.maintenance_type === "preventiva" ? (
                  <Shield className="text-green-600" size={28} />
                ) : (
                  <AlertTriangle className="text-[#E31A1A]" size={28} />
                )}
              </div>
              <div>
                <span className={`status-badge mb-2 ${
                  maintenance.maintenance_type === "preventiva" 
                    ? "badge-operational" 
                    : "badge-maintenance"
                }`}>
                  Manutenção {maintenance.maintenance_type}
                </span>
                <h1 className="text-2xl font-bold font-heading text-slate-900 mt-2">
                  {maintenance.part_name}
                </h1>
              </div>
            </div>
            
            <div className="text-right">
              <p className="text-3xl font-black text-slate-900 font-heading">
                {formatCurrency(maintenance.part_value)}
              </p>
              <p className="text-sm text-slate-500 flex items-center justify-end gap-1 mt-1">
                <Calendar size={14} />
                {formatDate(maintenance.replacement_date)}
              </p>
            </div>
          </div>

          {/* Machine Info */}
          <div className="mt-6 pt-6 border-t border-slate-200">
            <div 
              className="flex items-center gap-4 p-4 bg-slate-50 rounded-lg cursor-pointer hover:bg-slate-100 transition-colors"
              onClick={() => navigate(`/machines/${maintenance.machine_id}`)}
            >
              <div className="w-12 h-12 bg-slate-200 rounded-lg flex items-center justify-center">
                <Truck className="text-slate-600" size={24} />
              </div>
              <div>
                <p className="font-bold text-slate-900">{maintenance.machine_name}</p>
                <p className="font-mono text-sm text-slate-500">{maintenance.machine_plate}</p>
              </div>
            </div>
          </div>

          {/* Description */}
          {maintenance.description && (
            <div className="mt-6 pt-6 border-t border-slate-200">
              <p className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
                Descrição / Observações
              </p>
              <p className="text-slate-700">{maintenance.description}</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Photos Section */}
      <Card>
        <CardHeader className="border-b border-slate-200">
          <div className="flex items-center justify-between">
            <CardTitle className="font-heading text-xl font-bold">
              Fotos da Manutenção
            </CardTitle>
            <div>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={handleFileSelect}
                className="hidden"
                data-testid="photo-input"
              />
              <Button
                className="bg-slate-900 hover:bg-slate-800"
                onClick={() => fileInputRef.current?.click()}
                disabled={uploading}
                data-testid="add-photo-btn"
              >
                {uploading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Enviando...
                  </>
                ) : (
                  <>
                    <ImagePlus size={18} className="mr-2" />
                    Adicionar Foto
                  </>
                )}
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent className="pt-6">
          {maintenance.photos && maintenance.photos.length > 0 ? (
            <div className="photo-grid">
              {maintenance.photos.map((photo, index) => (
                <div 
                  key={index} 
                  className="photo-item"
                  data-testid={`photo-item-${index}`}
                >
                  <img src={photo} alt={`Foto ${index + 1}`} />
                  <div className="photo-overlay">
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-white hover:bg-white/20"
                      onClick={() => setSelectedPhoto(photo)}
                    >
                      <ZoomIn size={20} />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-red-300 hover:bg-red-500/20"
                      onClick={() => handleDeletePhoto(index)}
                      data-testid={`delete-photo-${index}`}
                    >
                      <Trash2 size={20} />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-state py-12">
              <ImagePlus className="text-slate-300 mb-4" size={48} />
              <p className="text-slate-500">Nenhuma foto anexada</p>
              <p className="text-sm text-slate-400 mt-1">
                Clique em "Adicionar Foto" para documentar a manutenção
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Photo Modal */}
      <Dialog open={!!selectedPhoto} onOpenChange={() => setSelectedPhoto(null)}>
        <DialogContent className="max-w-4xl p-0 overflow-hidden">
          <button
            className="absolute top-4 right-4 z-10 p-2 bg-black/50 rounded-full text-white hover:bg-black/70 transition-colors"
            onClick={() => setSelectedPhoto(null)}
          >
            <X size={20} />
          </button>
          {selectedPhoto && (
            <img 
              src={selectedPhoto} 
              alt="Foto ampliada" 
              className="w-full h-auto max-h-[80vh] object-contain"
            />
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
