import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "@/App";
import { toast } from "sonner";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { 
  Tags, 
  Plus, 
  Trash2,
  Edit,
  Loader2,
  Construction,
  Search,
  X
} from "lucide-react";

export default function CategoriesPage() {
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [showDialog, setShowDialog] = useState(false);
  const [formLoading, setFormLoading] = useState(false);
  const [deleteId, setDeleteId] = useState(null);
  const [editingCategory, setEditingCategory] = useState(null);
  const [formData, setFormData] = useState({
    name: "",
    description: ""
  });

  useEffect(() => {
    fetchCategories();
  }, []);

  const fetchCategories = async () => {
    try {
      const response = await axios.get(`${API}/categories`);
      setCategories(response.data);
    } catch (error) {
      toast.error("Erro ao carregar categorias");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setFormLoading(true);

    try {
      if (editingCategory) {
        await axios.put(`${API}/categories/${editingCategory.id}`, formData);
        toast.success("Categoria atualizada com sucesso!");
      } else {
        await axios.post(`${API}/categories`, formData);
        toast.success("Categoria criada com sucesso!");
      }
      setShowDialog(false);
      resetForm();
      fetchCategories();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao salvar categoria");
    } finally {
      setFormLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteId) return;
    
    try {
      await axios.delete(`${API}/categories/${deleteId}`);
      toast.success("Categoria removida com sucesso!");
      setDeleteId(null);
      fetchCategories();
    } catch (error) {
      toast.error("Erro ao remover categoria");
    }
  };

  const openEditDialog = (category) => {
    setEditingCategory(category);
    setFormData({
      name: category.name,
      description: category.description || ""
    });
    setShowDialog(true);
  };

  const resetForm = () => {
    setFormData({ name: "", description: "" });
    setEditingCategory(null);
  };

  const defaultCategories = [
    { name: "Escavadeira", description: "Escavadeiras hidráulicas" },
    { name: "Retroescavadeira", description: "Retroescavadeiras e pás carregadeiras" },
    { name: "Trator", description: "Tratores agrícolas e de esteira" },
    { name: "Caminhão", description: "Caminhões de carga e basculantes" },
    { name: "Rolo Compactador", description: "Rolos compactadores" }
  ];

  const createDefaultCategory = async (cat) => {
    try {
      await axios.post(`${API}/categories`, cat);
      toast.success(`Categoria "${cat.name}" criada!`);
      fetchCategories();
    } catch (error) {
      toast.error(`Erro ao criar categoria "${cat.name}"`);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="spinner w-12 h-12"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in" data-testid="categories-page">
      {/* Page header */}
      <div className="page-header">
        <div>
          <h1 className="page-title font-heading">Categorias</h1>
          <p className="text-gray-500 mt-1">Gerencie os tipos de máquinas</p>
        </div>
        <Button
          className="bg-black hover:bg-gray-900 text-white font-bold"
          onClick={() => {
            resetForm();
            setShowDialog(true);
          }}
          data-testid="new-category-btn"
        >
          <Plus size={18} className="mr-2" />
          Nova Categoria
        </Button>
      </div>

      {/* Search Bar */}
      <div className="flex gap-4 max-w-lg">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
          <Input
            type="text"
            placeholder="Pesquisar categorias..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10 pr-10 h-10 bg-white border-gray-200"
            data-testid="search-categories"
          />
          {searchTerm && (
            <button
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
              onClick={() => setSearchTerm("")}
            >
              <X size={16} />
            </button>
          )}
        </div>
        <Button className="bg-[#E31A1A] hover:bg-[#c41616] text-white">
          <Search size={16} className="mr-2" />
          Buscar
        </Button>
      </div>

      {/* Categories List */}
      {categories.filter(c => 
        c.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (c.description || "").toLowerCase().includes(searchTerm.toLowerCase())
      ).length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {categories
            .filter(c => 
              c.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
              (c.description || "").toLowerCase().includes(searchTerm.toLowerCase())
            )
            .map((category) => (
            <Card 
              key={category.id} 
              className="stat-card group"
              data-testid={`category-card-${category.id}`}
            >
              <CardContent className="pt-6">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3 flex-1">
                    <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center group-hover:bg-orange-50 transition-colors">
                      <Tags className="text-gray-600 group-hover:text-[#E31A1A] transition-colors" size={24} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="font-bold text-black truncate">{category.name}</h3>
                      <p className="text-sm text-gray-500 truncate">{category.description || "Sem descrição"}</p>
                    </div>
                  </div>
                  <div className="flex gap-1">
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-gray-400 hover:text-gray-600 hover:bg-gray-100"
                      onClick={() => openEditDialog(category)}
                      data-testid={`edit-category-${category.id}`}
                    >
                      <Edit size={18} />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-gray-400 hover:text-red-600 hover:bg-red-50"
                      onClick={() => setDeleteId(category.id)}
                      data-testid={`delete-category-${category.id}`}
                    >
                      <Trash2 size={18} />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <Card>
          <CardContent className="py-12">
            <div className="empty-state">
              <Tags className="text-gray-300 mb-4" size={64} />
              <p className="text-lg font-medium text-gray-600">Nenhuma categoria cadastrada</p>
              <p className="text-gray-400 mb-6">
                Crie categorias para organizar suas máquinas
              </p>
              
              {/* Quick add default categories */}
              <div className="space-y-4">
                <p className="text-sm text-gray-500 font-medium">Sugestões rápidas:</p>
                <div className="flex flex-wrap gap-2 justify-center">
                  {defaultCategories.map((cat) => (
                    <Button
                      key={cat.name}
                      variant="outline"
                      size="sm"
                      onClick={() => createDefaultCategory(cat)}
                      className="hover:bg-orange-50 hover:border-[#E31A1A]"
                      data-testid={`quick-add-${cat.name.toLowerCase().replace(/\s+/g, '-')}`}
                    >
                      <Plus size={14} className="mr-1" />
                      {cat.name}
                    </Button>
                  ))}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Info Card */}
      <Card className="bg-white border-gray-200">
        <CardContent className="py-6">
          <div className="flex items-start gap-4">
            <div className="w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center flex-shrink-0">
              <Construction className="text-[#E31A1A]" size={20} />
            </div>
            <div>
              <h3 className="font-bold text-black">Sobre Categorias</h3>
              <p className="text-sm text-gray-600 mt-1">
                As categorias ajudam a organizar sua frota por tipo de máquina. 
                Você pode criar categorias personalizadas como "Escavadeira", "Retroescavadeira", 
                "Caminhão", ou qualquer outro tipo de equipamento.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Create/Edit Dialog */}
      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="font-heading text-xl font-bold">
              {editingCategory ? "Editar Categoria" : "Nova Categoria"}
            </DialogTitle>
            <DialogDescription>
              {editingCategory 
                ? "Atualize as informações da categoria"
                : "Crie uma nova categoria para organizar suas máquinas"
              }
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label className="form-label">Nome *</Label>
              <Input
                value={formData.name}
                onChange={(e) => setFormData({...formData, name: e.target.value})}
                placeholder="Ex: Escavadeira, Retroescavadeira..."
                required
                className="form-input"
                data-testid="category-name-input"
              />
            </div>

            <div className="space-y-2">
              <Label className="form-label">Descrição</Label>
              <Input
                value={formData.description}
                onChange={(e) => setFormData({...formData, description: e.target.value})}
                placeholder="Descrição opcional..."
                className="form-input"
                data-testid="category-description-input"
              />
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
                disabled={formLoading}
                data-testid="category-submit-btn"
              >
                {formLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    {editingCategory ? "Atualizando..." : "Criando..."}
                  </>
                ) : editingCategory ? (
                  "Atualizar"
                ) : (
                  "Criar Categoria"
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
              Tem certeza que deseja excluir esta categoria? Máquinas associadas a ela não serão excluídas, mas ficarão sem categoria.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteId(null)}>
              Cancelar
            </Button>
            <Button
              className="bg-red-600 hover:bg-red-700"
              onClick={handleDelete}
              data-testid="confirm-delete-category-btn"
            >
              Excluir
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
