import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { API } from "@/App";
import { toast } from "sonner";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { 
  HardHat, 
  Plus, 
  Search,
  Edit,
  Trash2,
  Eye,
  Loader2,
  Truck,
  DollarSign,
  MapPin,
  Calendar
} from "lucide-react";
import AnexosManager from "@/components/AnexosManager";

export default function ObrasPage() {
  const [obras, setObras] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [showDialog, setShowDialog] = useState(false);
  const [editingObra, setEditingObra] = useState(null);
  const anexosRef = useRef(null);
  const [formLoading, setFormLoading] = useState(false);
  const [deleteId, setDeleteId] = useState(null);
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    name: "",
    description: "",
    location: "",
    start_date: "",
    end_date: "",
    status: "em_andamento"
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const response = await axios.get(`${API}/obras`);
      setObras(response.data);
    } catch (error) {
      toast.error("Erro ao carregar obras");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setFormLoading(true);

    try {
      const payload = {
        ...formData,
        start_date: formData.start_date || null,
        end_date: formData.end_date || null
      };

      if (editingObra) {
        await axios.put(`${API}/obras/${editingObra.id}`, payload);
        await anexosRef.current?.flushPending(editingObra.id);
        toast.success("Obra atualizada com sucesso!");
      } else {
        const _resp = await axios.post(`${API}/obras`, payload);
        await anexosRef.current?.flushPending(_resp.data?.id);
        toast.success("Obra cadastrada com sucesso!");
      }
      
      setShowDialog(false);
      resetForm();
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao salvar obra");
    } finally {
      setFormLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteId) return;
    
    try {
      await axios.delete(`${API}/obras/${deleteId}`);
      toast.success("Obra removida com sucesso!");
      setDeleteId(null);
      fetchData();
    } catch (error) {
      toast.error("Erro ao remover obra");
    }
  };

  const openEditDialog = (obra) => {
    setEditingObra(obra);
    setFormData({
      name: obra.name,
      description: obra.description || "",
      location: obra.location || "",
      start_date: obra.start_date || "",
      end_date: obra.end_date || "",
      status: obra.status || "em_andamento"
    });
    setShowDialog(true);
  };

  const resetForm = () => {
    setFormData({
      name: "",
      description: "",
      location: "",
      start_date: "",
      end_date: "",
      status: "em_andamento"
    });
    setEditingObra(null);
  };

  const filteredObras = obras.filter(
    (o) =>
      o.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      o.location?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      o.description?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getStatusBadge = (status) => {
    const badges = {
      em_andamento: { class: "bg-green-100 text-green-700 border-green-200", label: "Em Andamento" },
      concluida: { class: "bg-blue-100 text-[#D4A000] border-blue-200", label: "Concluída" },
      pausada: { class: "bg-yellow-100 text-yellow-700 border-yellow-200", label: "Pausada" }
    };
    const badge = badges[status] || badges.em_andamento;
    return (
      <span className={`px-2 py-1 text-xs font-bold rounded-full border ${badge.class}`}>
        {badge.label}
      </span>
    );
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat("pt-BR", {
      style: "currency",
      currency: "BRL"
    }).format(value);
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return "-";
    return new Date(dateStr).toLocaleDateString("pt-BR");
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="spinner w-12 h-12"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in" data-testid="obras-page">
      {/* Page header */}
      <div className="page-header">
        <div>
          <h1 className="page-title font-heading">Plano de Obras</h1>
          <p className="text-gray-500 mt-1">Gerencie suas obras e vincule máquinas</p>
        </div>
        <Button
          className="bg-black hover:bg-gray-900 text-white font-bold"
          onClick={() => {
            resetForm();
            setShowDialog(true);
          }}
          data-testid="new-obra-btn"
        >
          <Plus size={18} className="mr-2" />
          Nova Obra
        </Button>
      </div>

      {/* Search */}
      <div className="flex gap-4 max-w-lg">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
          <Input
            placeholder="Buscar por nome, local ou descrição..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10 h-11 bg-white border border-gray-300 rounded-md focus:border-[#E31A1A] focus:ring-2 focus:ring-[#E31A1A] focus:outline-none"
            data-testid="obras-search-input"
          />
        </div>
        <Button className="bg-[#E31A1A] hover:bg-[#c41616] text-white">
          <Search size={16} className="mr-2" />
          Buscar
        </Button>
      </div>

      {/* Obras Grid */}
      {filteredObras.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredObras.map((obra) => (
            <Card 
              key={obra.id} 
              className="machine-card hover:shadow-lg transition-shadow cursor-pointer"
              data-testid={`obra-card-${obra.id}`}
              onClick={() => navigate(`/gerenciamento/obras/${obra.id}`)}
            >
              <CardContent className="p-0">
                {/* Card Header */}
                <div className="p-4 border-b border-gray-100">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center">
                        <HardHat className="text-[#E31A1A]" size={24} />
                      </div>
                      <div>
                        <h3 className="font-bold text-black">{obra.name}</h3>
                        {obra.location && (
                          <p className="text-sm text-gray-500 flex items-center gap-1">
                            <MapPin size={12} />
                            {obra.location}
                          </p>
                        )}
                      </div>
                    </div>
                    {getStatusBadge(obra.status)}
                  </div>
                </div>

                {/* Card Body */}
                <div className="p-4 space-y-3">
                  {obra.description && (
                    <p className="text-sm text-gray-600 line-clamp-2">{obra.description}</p>
                  )}
                  
                  <div className="grid grid-cols-2 gap-2 pt-2">
                    <div className="flex items-center gap-2 text-sm">
                      <Truck className="text-gray-400" size={16} />
                      <span className="text-gray-600">
                        <span className="font-bold text-black">{obra.machine_count}</span> máquinas
                      </span>
                    </div>
                    <div className="flex items-center gap-2 text-sm">
                      <DollarSign className="text-gray-400" size={16} />
                      <span className="font-mono text-black font-medium">
                        {formatCurrency(obra.total_maintenance_cost)}
                      </span>
                    </div>
                  </div>

                  {(obra.start_date || obra.end_date) && (
                    <div className="flex items-center gap-2 text-sm text-gray-500 pt-1">
                      <Calendar size={14} />
                      <span>
                        {formatDate(obra.start_date)} - {formatDate(obra.end_date)}
                      </span>
                    </div>
                  )}
                </div>

                {/* Card Actions */}
                <div className="p-4 pt-0 flex gap-2" onClick={(e) => e.stopPropagation()}>
                  <Button
                    variant="outline"
                    size="sm"
                    className="flex-1"
                    onClick={() => navigate(`/gerenciamento/obras/${obra.id}`)}
                    data-testid={`view-obra-${obra.id}`}
                  >
                    <Eye size={16} className="mr-1" />
                    Detalhes
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    className="flex-1"
                    onClick={() => openEditDialog(obra)}
                    data-testid={`edit-obra-${obra.id}`}
                  >
                    <Edit size={16} className="mr-1" />
                    Editar
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    className="text-red-600 hover:text-red-700 hover:bg-red-50"
                    onClick={() => setDeleteId(obra.id)}
                    data-testid={`delete-obra-${obra.id}`}
                  >
                    <Trash2 size={16} />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <div className="empty-state">
          <HardHat className="text-gray-300 mb-4" size={64} />
          <p className="text-lg font-medium text-gray-600">Nenhuma obra encontrada</p>
          <p className="text-gray-400 mb-4">
            {searchTerm ? "Tente uma busca diferente" : "Cadastre sua primeira obra"}
          </p>
          {!searchTerm && (
            <Button
              className="bg-[#E31A1A] hover:bg-[#E31A1A]"
              onClick={() => setShowDialog(true)}
            >
              <Plus size={18} className="mr-2" />
              Cadastrar Obra
            </Button>
          )}
        </div>
      )}

      {/* Create/Edit Dialog */}
      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="font-heading text-xl font-bold">
              {editingObra ? "Editar Obra" : "Nova Obra"}
            </DialogTitle>
            <DialogDescription>
              {editingObra 
                ? "Atualize as informações da obra"
                : "Preencha os dados para cadastrar uma nova obra"
              }
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label className="form-label">Nome da Obra *</Label>
              <Input
                value={formData.name}
                onChange={(e) => setFormData({...formData, name: e.target.value})}
                placeholder="Ex: Construção Galpão Industrial"
                required
                className="form-input"
                data-testid="obra-name-input"
              />
            </div>

            <div className="space-y-2">
              <Label className="form-label">Localização</Label>
              <Input
                value={formData.location}
                onChange={(e) => setFormData({...formData, location: e.target.value})}
                placeholder="Ex: Rodovia BR-101, Km 45"
                className="form-input"
                data-testid="obra-location-input"
              />
            </div>

            <div className="space-y-2">
              <Label className="form-label">Descrição</Label>
              <Input
                value={formData.description}
                onChange={(e) => setFormData({...formData, description: e.target.value})}
                placeholder="Breve descrição da obra..."
                className="form-input"
                data-testid="obra-description-input"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label className="form-label">Data Início</Label>
                <Input
                  type="date"
                  value={formData.start_date}
                  onChange={(e) => setFormData({...formData, start_date: e.target.value})}
                  className="form-input"
                  data-testid="obra-start-date-input"
                />
              </div>
              <div className="space-y-2">
                <Label className="form-label">Data Fim</Label>
                <Input
                  type="date"
                  value={formData.end_date}
                  onChange={(e) => setFormData({...formData, end_date: e.target.value})}
                  className="form-input"
                  data-testid="obra-end-date-input"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label className="form-label">Status</Label>
              <Select
                value={formData.status}
                onValueChange={(value) => setFormData({...formData, status: value})}
              >
                <SelectTrigger className="form-input" data-testid="obra-status-select">
                  <SelectValue placeholder="Selecione o status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="em_andamento">Em Andamento</SelectItem>
                  <SelectItem value="concluida">Concluída</SelectItem>
                  <SelectItem value="pausada">Pausada</SelectItem>
                </SelectContent>
              </Select>
            </div>

                        <AnexosManager
              ref={anexosRef}
              entityType="obra"
              entityId={editingObra?.id}
            />
<DialogFooter className="gap-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => setShowDialog(false)}
              >
                Cancelar
              </Button>
              <Button
                type="submit"
                className="bg-black hover:bg-gray-900"
                disabled={formLoading}
                data-testid="obra-submit-btn"
              >
                {formLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Salvando...
                  </>
                ) : editingObra ? (
                  "Atualizar"
                ) : (
                  "Cadastrar"
                )}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={!!deleteId} onOpenChange={() => setDeleteId(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="text-red-600">Confirmar Exclusão</DialogTitle>
            <DialogDescription>
              Tem certeza que deseja excluir esta obra? As máquinas vinculadas serão desvinculadas, mas não serão excluídas.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteId(null)}>
              Cancelar
            </Button>
            <Button
              className="bg-red-600 hover:bg-red-700"
              onClick={handleDelete}
              data-testid="confirm-delete-obra-btn"
            >
              Excluir
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
