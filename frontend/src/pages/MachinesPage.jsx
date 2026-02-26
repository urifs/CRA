import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { API } from "@/App";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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
  Truck, 
  Plus, 
  Search,
  Edit,
  Trash2,
  Eye,
  Loader2,
  FolderTree,
  User,
  LayoutGrid,
  List,
  ChevronRight
} from "lucide-react";

export default function MachinesPage() {
  const [machines, setMachines] = useState([]);
  const [categories, setCategories] = useState([]);
  const [fleets, setFleets] = useState([]);
  const [subfleets, setSubfleets] = useState([]);
  const [cadastros, setCadastros] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [showDialog, setShowDialog] = useState(false);
  const [editingMachine, setEditingMachine] = useState(null);
  const [formLoading, setFormLoading] = useState(false);
  const [deleteId, setDeleteId] = useState(null);
  const [viewMode, setViewMode] = useState("grid"); // grid ou list
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    name: "",
    plate: "",
    category_id: "",
    subcategory_id: "",
    brand: "",
    model: "",
    year: "",
    notes: "",
    fleet_id: "",
    subfleet_id: "",
    operator_id: ""
  });

  const [subcategories, setSubcategories] = useState([]);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    const token = localStorage.getItem("token");
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    
    try {
      const [machinesRes, categoriesRes, fleetsRes, subfleetsRes, cadastrosRes, subcategoriesRes] = await Promise.all([
        axios.get(`${API}/machines`, { headers }),
        axios.get(`${API}/categories`, { headers }),
        axios.get(`${API}/fleets`, { headers }),
        axios.get(`${API}/subfleets`, { headers }),
        axios.get(`${API}/admin/cadastros`, { headers }).catch(() => ({ data: [] })),
        axios.get(`${API}/subcategories`, { headers })
      ]);
      setMachines(machinesRes.data);
      setCategories(categoriesRes.data);
      setFleets(fleetsRes.data);
      setSubfleets(subfleetsRes.data);
      setCadastros(cadastrosRes.data);
      setSubcategories(subcategoriesRes.data);
    } catch (error) {
      toast.error("Erro ao carregar dados");
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
        year: formData.year ? parseInt(formData.year) : null,
        fleet_id: formData.fleet_id || null,
        subfleet_id: formData.subfleet_id || null,
        operator_id: formData.operator_id || null,
        subcategory_id: formData.subcategory_id || null
      };

      if (editingMachine) {
        await axios.put(`${API}/machines/${editingMachine.id}`, payload);
        toast.success("Máquina atualizada com sucesso!");
      } else {
        await axios.post(`${API}/machines`, payload);
        toast.success("Máquina cadastrada com sucesso!");
      }
      
      setShowDialog(false);
      resetForm();
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao salvar máquina");
    } finally {
      setFormLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteId) return;
    
    try {
      await axios.delete(`${API}/machines/${deleteId}`);
      toast.success("Máquina removida com sucesso!");
      setDeleteId(null);
      fetchData();
    } catch (error) {
      toast.error("Erro ao remover máquina");
    }
  };

  const openEditDialog = (machine) => {
    setEditingMachine(machine);
    setFormData({
      name: machine.name,
      plate: machine.plate || "",
      category_id: machine.category_id,
      subcategory_id: machine.subcategory_id || "",
      brand: machine.brand || "",
      model: machine.model || "",
      year: machine.year?.toString() || "",
      notes: machine.notes || "",
      fleet_id: machine.fleet_id || "",
      subfleet_id: machine.subfleet_id || "",
      operator_id: machine.operator_id || ""
    });
    setShowDialog(true);
  };

  const resetForm = () => {
    setFormData({
      name: "",
      plate: "",
      category_id: "",
      subcategory_id: "",
      brand: "",
      model: "",
      year: "",
      notes: "",
      fleet_id: "",
      subfleet_id: "",
      operator_id: ""
    });
    setEditingMachine(null);
  };

  // Filtrar subfrotas com base na frota selecionada
  const filteredSubfleets = formData.fleet_id 
    ? subfleets.filter(s => s.fleet_id === formData.fleet_id)
    : [];

  // Filtrar subcategorias com base na categoria selecionada
  const filteredSubcategories = formData.category_id 
    ? subcategories.filter(s => s.category_id === formData.category_id)
    : [];

  const filteredMachines = machines.filter(
    (m) =>
      m.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      m.plate.toLowerCase().includes(searchTerm.toLowerCase()) ||
      m.category_name?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getStatusBadge = (status) => {
    const badges = {
      operational: { class: "badge-operational", label: "Operacional" },
      maintenance: { class: "badge-maintenance", label: "Em Manutenção" },
      broken: { class: "badge-broken", label: "Quebrado" }
    };
    const badge = badges[status] || badges.operational;
    return (
      <span className={`status-badge ${badge.class}`}>
        {badge.label}
      </span>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="spinner w-12 h-12"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in" data-testid="machines-page">
      {/* Page header */}
      <div className="page-header">
        <div>
          <h1 className="page-title font-heading">Máquinas</h1>
          <p className="text-gray-500 mt-1">Gerencie sua frota de máquinas</p>
        </div>
        <Button
          className="bg-black hover:bg-gray-900 text-white font-bold"
          onClick={() => {
            resetForm();
            setShowDialog(true);
          }}
          data-testid="new-machine-btn"
        >
          <Plus size={18} className="mr-2" />
          Nova Máquina
        </Button>
      </div>

      {/* Search Bar */}
      <div className="flex items-center gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
          <Input
            placeholder="Buscar por nome, placa ou categoria..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10 h-11 bg-white border border-gray-300 rounded-md focus:border-[#E31A1A] focus:ring-2 focus:ring-[#E31A1A] focus:outline-none"
            data-testid="machines-search-input"
          />
        </div>
        <div className="flex border rounded-lg overflow-hidden">
          <Button 
            variant={viewMode === "grid" ? "default" : "ghost"} 
            size="sm" 
            onClick={() => setViewMode("grid")}
            className={viewMode === "grid" ? "bg-[#E31A1A] hover:bg-red-700" : ""}
          >
            <LayoutGrid size={18} />
          </Button>
          <Button 
            variant={viewMode === "list" ? "default" : "ghost"} 
            size="sm" 
            onClick={() => setViewMode("list")}
            className={viewMode === "list" ? "bg-[#E31A1A] hover:bg-red-700" : ""}
          >
            <List size={18} />
          </Button>
        </div>
      </div>

      {/* Machines Grid/List */}
      {filteredMachines.length > 0 ? (
        viewMode === "grid" ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredMachines.map((machine) => (
              <Card 
                key={machine.id} 
                className="machine-card"
                data-testid={`machine-card-${machine.id}`}
              >
                <CardContent className="p-0">
                  {/* Card Header */}
                  <div className="p-4 border-b border-gray-100">
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-3">
                        <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center">
                          <Truck className="text-gray-600" size={24} />
                        </div>
                        <div>
                          <h3 className="font-bold text-black">{machine.name}</h3>
                          {machine.plate && <p className="font-mono text-sm text-gray-500">{machine.plate}</p>}
                        </div>
                      </div>
                      {getStatusBadge(machine.status)}
                    </div>
                  </div>

                  {/* Card Body */}
                  <div className="p-4 space-y-1.5 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-500">Categoria:</span>
                      <span className="font-medium text-black">{machine.category_name || "-"}</span>
                    </div>
                    {machine.brand && (
                      <div className="flex justify-between">
                        <span className="text-gray-500">Marca:</span>
                        <span className="font-medium text-black">{machine.brand}</span>
                      </div>
                    )}
                    {machine.fleet_name && (
                      <div className="flex justify-between">
                        <span className="text-gray-500 flex items-center gap-1">
                          <FolderTree size={12} /> Frota:
                        </span>
                        <span className="font-medium text-black">{machine.fleet_name}</span>
                      </div>
                    )}
                    {machine.subfleet_name && (
                      <div className="flex justify-between">
                        <span className="text-gray-500 flex items-center gap-1">
                          <ChevronRight size={12} /> Subfrota:
                        </span>
                        <span className="font-medium text-black">{machine.subfleet_name}</span>
                      </div>
                    )}
                    {machine.operator_name && (
                      <div className="flex justify-between">
                        <span className="text-gray-500 flex items-center gap-1">
                          <User size={12} /> Operador:
                        </span>
                        <span className="font-medium text-black truncate max-w-[120px]">{machine.operator_name}</span>
                      </div>
                    )}
                    {machine.notes && (
                      <div className="pt-1 border-t mt-1">
                        <p className="text-gray-500 text-xs truncate" title={machine.notes}>
                          📝 {machine.notes}
                        </p>
                      </div>
                    )}
                  </div>

                  {/* Card Actions */}
                  <div className="p-4 pt-0 flex gap-2">
                    <Button variant="outline" size="sm" className="flex-1" onClick={() => navigate(`/machines/${machine.id}`)} data-testid={`view-machine-${machine.id}`}>
                      <Eye size={16} className="mr-1" /> Ver
                    </Button>
                    <Button variant="outline" size="sm" className="flex-1" onClick={() => openEditDialog(machine)} data-testid={`edit-machine-${machine.id}`}>
                      <Edit size={16} className="mr-1" /> Editar
                    </Button>
                    <Button variant="outline" size="sm" className="text-red-600 hover:text-red-700 hover:bg-red-50" onClick={() => setDeleteId(machine.id)} data-testid={`delete-machine-${machine.id}`}>
                      <Trash2 size={16} />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          /* List View */
          <Card>
            <CardContent className="p-0">
              <table className="data-table w-full">
                <thead>
                  <tr>
                    <th>Nome</th>
                    <th>Placa</th>
                    <th>Categoria</th>
                    <th>Frota</th>
                    <th>Operador</th>
                    <th>Status</th>
                    <th className="text-right">Ações</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredMachines.map((machine) => (
                    <tr key={machine.id} data-testid={`machine-row-${machine.id}`}>
                      <td className="font-medium text-black">
                        <div className="flex items-center gap-2">
                          <Truck size={16} className="text-gray-400" />
                          {machine.name}
                        </div>
                      </td>
                      <td className="font-mono text-gray-500">{machine.plate || "-"}</td>
                      <td>{machine.category_name || "-"}</td>
                      <td>
                        {machine.fleet_name ? (
                          <span className="text-sm">
                            {machine.fleet_name}
                            {machine.subfleet_name && <span className="text-gray-400"> / {machine.subfleet_name}</span>}
                          </span>
                        ) : "-"}
                      </td>
                      <td className="truncate max-w-[150px]">{machine.operator_name || "-"}</td>
                      <td>{getStatusBadge(machine.status)}</td>
                      <td className="text-right">
                        <div className="flex justify-end gap-1">
                          <Button variant="ghost" size="sm" onClick={() => navigate(`/machines/${machine.id}`)}>
                            <Eye size={16} />
                          </Button>
                          <Button variant="ghost" size="sm" onClick={() => openEditDialog(machine)}>
                            <Edit size={16} />
                          </Button>
                          <Button variant="ghost" size="sm" className="text-red-600" onClick={() => setDeleteId(machine.id)}>
                            <Trash2 size={16} />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CardContent>
          </Card>
        )
      ) : (
        <div className="empty-state">
          <Truck className="text-gray-300 mb-4" size={64} />
          <p className="text-lg font-medium text-gray-600">Nenhuma máquina encontrada</p>
          <p className="text-gray-400 mb-4">
            {searchTerm ? "Tente uma busca diferente" : "Cadastre sua primeira máquina"}
          </p>
          {!searchTerm && (
            <Button
              className="bg-[#E31A1A] hover:bg-[#E31A1A]"
              onClick={() => setShowDialog(true)}
            >
              <Plus size={18} className="mr-2" />
              Cadastrar Máquina
            </Button>
          )}
        </div>
      )}

      {/* Create/Edit Dialog */}
      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="font-heading text-xl font-bold">
              {editingMachine ? "Editar Máquina" : "Nova Máquina"}
            </DialogTitle>
            <DialogDescription>
              {editingMachine 
                ? "Atualize as informações da máquina"
                : "Preencha os dados para cadastrar uma nova máquina"
              }
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label className="form-label">Nome *</Label>
                <Input
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                  placeholder="Ex: Trator John Deere"
                  required
                  className="form-input"
                  data-testid="machine-name-input"
                />
              </div>
              <div className="space-y-2">
                <Label className="form-label">Placa (opcional)</Label>
                <Input
                  value={formData.plate}
                  onChange={(e) => setFormData({...formData, plate: e.target.value.toUpperCase()})}
                  placeholder="Ex: ABC-1234"
                  className="form-input font-mono"
                  data-testid="machine-plate-input"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label className="form-label">Categoria *</Label>
                <Select
                  value={formData.category_id}
                  onValueChange={(value) => setFormData({...formData, category_id: value, subcategory_id: ""})}
                  required
                >
                  <SelectTrigger className="form-input" data-testid="machine-category-select">
                    <SelectValue placeholder="Selecione uma categoria" />
                  </SelectTrigger>
                  <SelectContent>
                    {categories.map((cat) => (
                      <SelectItem key={cat.id} value={cat.id}>
                        {cat.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {categories.length === 0 && (
                  <p className="text-sm text-[#E31A1A]">
                    Nenhuma categoria cadastrada.{" "}
                    <button
                      type="button"
                      className="underline"
                      onClick={() => {
                        setShowDialog(false);
                        navigate("/categories");
                      }}
                    >
                      Cadastrar categoria
                    </button>
                  </p>
                )}
              </div>
              <div className="space-y-2">
                <Label className="form-label">Subcategoria (opcional)</Label>
                <Select
                  value={formData.subcategory_id}
                  onValueChange={(value) => setFormData({...formData, subcategory_id: value === "__none__" ? "" : value})}
                  disabled={!formData.category_id || filteredSubcategories.length === 0}
                >
                  <SelectTrigger className="form-input" data-testid="machine-subcategory-select">
                    <SelectValue placeholder={!formData.category_id ? "Selecione categoria primeiro" : filteredSubcategories.length === 0 ? "Sem subcategorias" : "Selecione subcategoria"} />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="__none__">Nenhuma</SelectItem>
                    {filteredSubcategories.map((sub) => (
                      <SelectItem key={sub.id} value={sub.id}>
                        {sub.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label className="form-label">Marca</Label>
                <Input
                  value={formData.brand}
                  onChange={(e) => setFormData({...formData, brand: e.target.value})}
                  placeholder="Ex: John Deere"
                  className="form-input"
                  data-testid="machine-brand-input"
                />
              </div>
              <div className="space-y-2">
                <Label className="form-label">Modelo</Label>
                <Input
                  value={formData.model}
                  onChange={(e) => setFormData({...formData, model: e.target.value})}
                  placeholder="Ex: 6175J"
                  className="form-input"
                  data-testid="machine-model-input"
                />
              </div>
              <div className="space-y-2">
                <Label className="form-label">Ano</Label>
                <Input
                  type="number"
                  value={formData.year}
                  onChange={(e) => setFormData({...formData, year: e.target.value})}
                  placeholder="Ex: 2020"
                  min="1900"
                  max={new Date().getFullYear() + 1}
                  className="form-input font-mono"
                  data-testid="machine-year-input"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label className="form-label">Observações</Label>
              <Input
                value={formData.notes}
                onChange={(e) => setFormData({...formData, notes: e.target.value})}
                placeholder="Informações adicionais..."
                className="form-input"
                data-testid="machine-notes-input"
              />
            </div>

            {/* Frota e Subfrota */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label className="form-label flex items-center gap-1">
                  <FolderTree size={14} className="text-gray-400" />
                  Frota (opcional)
                </Label>
                <Select
                  value={formData.fleet_id}
                  onValueChange={(value) => setFormData({...formData, fleet_id: value === "__none__" ? "" : value, subfleet_id: ""})}
                >
                  <SelectTrigger className="form-input" data-testid="machine-fleet-select">
                    <SelectValue placeholder="Selecione uma frota" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="__none__">Nenhuma</SelectItem>
                    {fleets.map((fleet) => (
                      <SelectItem key={fleet.id} value={fleet.id}>
                        {fleet.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label className="form-label">Subfrota (opcional)</Label>
                <Select
                  value={formData.subfleet_id}
                  onValueChange={(value) => setFormData({...formData, subfleet_id: value === "__none__" ? "" : value})}
                  disabled={!formData.fleet_id}
                >
                  <SelectTrigger className="form-input" data-testid="machine-subfleet-select">
                    <SelectValue placeholder={formData.fleet_id ? "Selecione uma subfrota" : "Selecione uma frota primeiro"} />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="__none__">Nenhuma</SelectItem>
                    {filteredSubfleets.map((subfleet) => (
                      <SelectItem key={subfleet.id} value={subfleet.id}>
                        {subfleet.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Operador/Funcionário */}
            <div className="space-y-2">
              <Label className="form-label flex items-center gap-1">
                <User size={14} className="text-gray-400" />
                Operador/Funcionário (opcional)
              </Label>
              <Select
                value={formData.operator_id}
                onValueChange={(value) => setFormData({...formData, operator_id: value === "__none__" ? "" : value})}
              >
                <SelectTrigger className="form-input" data-testid="machine-operator-select">
                  <SelectValue placeholder="Selecione um funcionário" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="__none__">Nenhum</SelectItem>
                  {cadastros.map((c) => (
                    <SelectItem key={c.id} value={c.id}>
                      {c.nome_razao} {c.cpf_cnpj ? `(${c.cpf_cnpj})` : ""}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

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
                disabled={formLoading || !formData.category_id}
                data-testid="machine-submit-btn"
              >
                {formLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Salvando...
                  </>
                ) : editingMachine ? (
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
              Tem certeza que deseja excluir esta máquina? Esta ação também removerá todas as manutenções associadas e não pode ser desfeita.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteId(null)}>
              Cancelar
            </Button>
            <Button
              className="bg-red-600 hover:bg-red-700"
              onClick={handleDelete}
              data-testid="confirm-delete-btn"
            >
              Excluir
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
