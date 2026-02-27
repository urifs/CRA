import { useState, useEffect } from "react";
import axios from "axios";
import { toast } from "sonner";
import { API } from "@/App";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { 
  Plus, 
  Edit, 
  Trash2, 
  Tags, 
  ChevronRight,
  Loader2,
  Search,
  Truck,
  Palette
} from "lucide-react";

// Cores predefinidas para categorias
const CATEGORY_COLORS = [
  { name: "Vermelho", value: "#E31A1A" },
  { name: "Azul", value: "#3B82F6" },
  { name: "Verde", value: "#10B981" },
  { name: "Amarelo", value: "#F59E0B" },
  { name: "Roxo", value: "#8B5CF6" },
  { name: "Rosa", value: "#EC4899" },
  { name: "Laranja", value: "#F97316" },
  { name: "Ciano", value: "#06B6D4" },
  { name: "Índigo", value: "#6366F1" },
  { name: "Cinza", value: "#6B7280" },
];

export default function CategoriesPage() {
  const [categories, setCategories] = useState([]);
  const [subcategories, setSubcategories] = useState([]);
  const [machines, setMachines] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  
  // Modal states
  const [showCategoryModal, setShowCategoryModal] = useState(false);
  const [showSubcategoryModal, setShowSubcategoryModal] = useState(false);
  const [editingCategory, setEditingCategory] = useState(null);
  const [editingSubcategory, setEditingSubcategory] = useState(null);
  
  // Form states
  const [categoryForm, setCategoryForm] = useState({ name: "", description: "", color: "#E31A1A" });
  const [subcategoryForm, setSubcategoryForm] = useState({ name: "", category_id: "", description: "" });
  
  const [formLoading, setFormLoading] = useState(false);

  const token = localStorage.getItem("token");

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [categoriesRes, subcategoriesRes, machinesRes] = await Promise.all([
        axios.get(`${API}/categories`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API}/subcategories`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API}/machines`, { headers: { Authorization: `Bearer ${token}` } })
      ]);
      setCategories(categoriesRes.data);
      setSubcategories(subcategoriesRes.data);
      setMachines(machinesRes.data);
    } catch (error) {
      toast.error("Erro ao carregar dados");
    } finally {
      setLoading(false);
    }
  };

  // Category CRUD
  const handleSaveCategory = async () => {
    if (!categoryForm.name.trim()) {
      toast.error("Digite o nome da categoria");
      return;
    }
    
    setFormLoading(true);
    try {
      if (editingCategory) {
        await axios.put(`${API}/categories/${editingCategory.id}`, categoryForm, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success("Categoria atualizada!");
      } else {
        await axios.post(`${API}/categories`, categoryForm, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success("Categoria criada!");
      }
      setShowCategoryModal(false);
      setEditingCategory(null);
      setCategoryForm({ name: "", description: "", color: "#E31A1A" });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao salvar categoria");
    } finally {
      setFormLoading(false);
    }
  };

  const handleDeleteCategory = async (category) => {
    if (!confirm(`Excluir a categoria "${category.name}"? As subcategorias também serão excluídas.`)) return;
    
    try {
      await axios.delete(`${API}/categories/${category.id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success("Categoria excluída!");
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao excluir categoria");
    }
  };

  // Subcategory CRUD
  const handleSaveSubcategory = async () => {
    if (!subcategoryForm.name.trim()) {
      toast.error("Digite o nome da subcategoria");
      return;
    }
    if (!subcategoryForm.category_id) {
      toast.error("Selecione uma categoria");
      return;
    }
    
    setFormLoading(true);
    try {
      if (editingSubcategory) {
        await axios.put(`${API}/subcategories/${editingSubcategory.id}`, {
          name: subcategoryForm.name,
          category_id: subcategoryForm.category_id,
          description: subcategoryForm.description
        }, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success("Subcategoria atualizada!");
      } else {
        await axios.post(`${API}/subcategories`, subcategoryForm, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success("Subcategoria criada!");
      }
      setShowSubcategoryModal(false);
      setEditingSubcategory(null);
      setSubcategoryForm({ name: "", category_id: "", description: "" });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao salvar subcategoria");
    } finally {
      setFormLoading(false);
    }
  };

  const handleDeleteSubcategory = async (subcategory) => {
    if (!confirm(`Excluir a subcategoria "${subcategory.name}"?`)) return;
    
    try {
      await axios.delete(`${API}/subcategories/${subcategory.id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success("Subcategoria excluída!");
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao excluir subcategoria");
    }
  };

  const openEditCategory = (category) => {
    setEditingCategory(category);
    setCategoryForm({ name: category.name, description: category.description || "", color: category.color || "#E31A1A" });
    setShowCategoryModal(true);
  };

  const openEditSubcategory = (subcategory) => {
    setEditingSubcategory(subcategory);
    setSubcategoryForm({ name: subcategory.name, category_id: subcategory.category_id, description: subcategory.description || "" });
    setShowSubcategoryModal(true);
  };

  const openNewSubcategory = (categoryId = "") => {
    setEditingSubcategory(null);
    setSubcategoryForm({ name: "", category_id: categoryId, description: "" });
    setShowSubcategoryModal(true);
  };

  const getMachinesByCategory = (categoryId) => machines.filter(m => m.category_id === categoryId);
  const getMachinesBySubcategory = (subcategoryId) => machines.filter(m => m.subcategory_id === subcategoryId);
  const getSubcategoriesByCategory = (categoryId) => subcategories.filter(s => s.category_id === categoryId);

  const filteredCategories = categories.filter(c => 
    c.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="animate-spin text-[#E31A1A]" size={48} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-black flex items-center gap-2">
            <Tags className="text-[#E31A1A]" />
            Categorias de Máquinas
          </h1>
          <p className="text-gray-500 text-sm mt-1">
            Organize suas máquinas em categorias e subcategorias
          </p>
        </div>
        <div className="flex gap-2">
          <Button onClick={() => { setEditingCategory(null); setCategoryForm({ name: "", description: "", color: "#E31A1A" }); setShowCategoryModal(true); }} className="bg-[#E31A1A] hover:bg-red-700">
            <Plus size={18} className="mr-2" />
            Nova Categoria
          </Button>
        </div>
      </div>

      {/* Search */}
      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
        <Input
          placeholder="Buscar categorias..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="pl-10"
        />
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-4 flex items-center gap-4">
            <div className="w-12 h-12 bg-red-100 rounded-lg flex items-center justify-center">
              <Tags className="text-[#E31A1A]" size={24} />
            </div>
            <div>
              <p className="text-2xl font-bold">{categories.length}</p>
              <p className="text-sm text-gray-500">Categorias</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 flex items-center gap-4">
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
              <ChevronRight className="text-blue-600" size={24} />
            </div>
            <div>
              <p className="text-2xl font-bold">{subcategories.length}</p>
              <p className="text-sm text-gray-500">Subcategorias</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 flex items-center gap-4">
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
              <Truck className="text-green-600" size={24} />
            </div>
            <div>
              <p className="text-2xl font-bold">{machines.length}</p>
              <p className="text-sm text-gray-500">Máquinas</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Categories Grid */}
      {filteredCategories.length === 0 ? (
        <Card>
          <CardContent className="p-12 text-center">
            <Tags size={48} className="mx-auto text-gray-300 mb-4" />
            <p className="text-gray-500">Nenhuma categoria cadastrada</p>
            <Button onClick={() => setShowCategoryModal(true)} className="mt-4 bg-[#E31A1A] hover:bg-red-700">
              <Plus size={18} className="mr-2" />
              Criar Primeira Categoria
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {filteredCategories.map((category) => {
            const categorySubcategories = getSubcategoriesByCategory(category.id);
            const categoryMachines = getMachinesByCategory(category.id);
            
            return (
              <Card key={category.id} className="overflow-hidden">
                <CardHeader className="bg-gray-50 border-b">
                  <div className="flex justify-between items-center">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-[#E31A1A] rounded-lg flex items-center justify-center">
                        <Tags className="text-white" size={20} />
                      </div>
                      <div>
                        <CardTitle className="text-lg">{category.name}</CardTitle>
                        {category.description && <p className="text-sm text-gray-500">{category.description}</p>}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-gray-500 mr-4">
                        {categorySubcategories.length} subcategorias • {categoryMachines.length} máquinas
                      </span>
                      <Button variant="outline" size="sm" onClick={() => openNewSubcategory(category.id)}>
                        <Plus size={14} className="mr-1" /> Subcategoria
                      </Button>
                      <Button variant="ghost" size="sm" onClick={() => openEditCategory(category)}>
                        <Edit size={14} />
                      </Button>
                      <Button variant="ghost" size="sm" className="text-red-500 hover:text-red-700" onClick={() => handleDeleteCategory(category)}>
                        <Trash2 size={14} />
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="p-4">
                  {categorySubcategories.length === 0 && categoryMachines.length === 0 ? (
                    <p className="text-gray-400 text-center py-4">Nenhuma subcategoria ou máquina nesta categoria</p>
                  ) : (
                    <div className="space-y-3">
                      {/* Subcategories */}
                      {categorySubcategories.map((subcategory) => {
                        const subMachines = getMachinesBySubcategory(subcategory.id);
                        return (
                          <div key={subcategory.id} className="border rounded-lg p-3 bg-gray-50">
                            <div className="flex justify-between items-center mb-2">
                              <div className="flex items-center gap-2">
                                <ChevronRight className="text-blue-500" size={18} />
                                <span className="font-medium">{subcategory.name}</span>
                                <span className="text-xs text-gray-400">({subMachines.length} máquinas)</span>
                              </div>
                              <div className="flex gap-1">
                                <Button variant="ghost" size="sm" onClick={() => openEditSubcategory(subcategory)}>
                                  <Edit size={12} />
                                </Button>
                                <Button variant="ghost" size="sm" className="text-red-500" onClick={() => handleDeleteSubcategory(subcategory)}>
                                  <Trash2 size={12} />
                                </Button>
                              </div>
                            </div>
                            {subMachines.length > 0 && (
                              <div className="flex flex-wrap gap-2 mt-2">
                                {subMachines.map((m) => (
                                  <span key={m.id} className="text-xs bg-white border px-2 py-1 rounded flex items-center gap-1">
                                    <Truck size={12} className="text-gray-400" />
                                    {m.name}
                                  </span>
                                ))}
                              </div>
                            )}
                          </div>
                        );
                      })}
                      
                      {/* Machines without subcategory */}
                      {categoryMachines.filter(m => !m.subcategory_id).length > 0 && (
                        <div className="border rounded-lg p-3">
                          <p className="text-sm text-gray-500 mb-2">Máquinas sem subcategoria:</p>
                          <div className="flex flex-wrap gap-2">
                            {categoryMachines.filter(m => !m.subcategory_id).map((m) => (
                              <span key={m.id} className="text-xs bg-gray-100 px-2 py-1 rounded flex items-center gap-1">
                                <Truck size={12} className="text-gray-400" />
                                {m.name}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Category Modal */}
      <Dialog open={showCategoryModal} onOpenChange={setShowCategoryModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editingCategory ? "Editar Categoria" : "Nova Categoria"}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>Nome da Categoria *</Label>
              <Input
                value={categoryForm.name}
                onChange={(e) => setCategoryForm({ ...categoryForm, name: e.target.value })}
                placeholder="Ex: Tratores"
              />
            </div>
            <div>
              <Label>Descrição (opcional)</Label>
              <Input
                value={categoryForm.description}
                onChange={(e) => setCategoryForm({ ...categoryForm, description: e.target.value })}
                placeholder="Descrição da categoria"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCategoryModal(false)}>Cancelar</Button>
            <Button onClick={handleSaveCategory} disabled={formLoading} className="bg-[#E31A1A] hover:bg-red-700">
              {formLoading ? <Loader2 className="animate-spin mr-2" size={16} /> : null}
              {editingCategory ? "Salvar" : "Criar"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Subcategory Modal */}
      <Dialog open={showSubcategoryModal} onOpenChange={setShowSubcategoryModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editingSubcategory ? "Editar Subcategoria" : "Nova Subcategoria"}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>Categoria *</Label>
              <Select 
                value={subcategoryForm.category_id} 
                onValueChange={(v) => setSubcategoryForm({ ...subcategoryForm, category_id: v })}
                disabled={!!editingSubcategory}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Selecione a categoria" />
                </SelectTrigger>
                <SelectContent>
                  {categories.map((c) => (
                    <SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Nome da Subcategoria *</Label>
              <Input
                value={subcategoryForm.name}
                onChange={(e) => setSubcategoryForm({ ...subcategoryForm, name: e.target.value })}
                placeholder="Ex: Tratores de Esteira"
              />
            </div>
            <div>
              <Label>Descrição (opcional)</Label>
              <Input
                value={subcategoryForm.description}
                onChange={(e) => setSubcategoryForm({ ...subcategoryForm, description: e.target.value })}
                placeholder="Descrição da subcategoria"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowSubcategoryModal(false)}>Cancelar</Button>
            <Button onClick={handleSaveSubcategory} disabled={formLoading} className="bg-[#E31A1A] hover:bg-red-700">
              {formLoading ? <Loader2 className="animate-spin mr-2" size={16} /> : null}
              {editingSubcategory ? "Salvar" : "Criar"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
