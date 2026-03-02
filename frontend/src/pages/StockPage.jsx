import { useState, useEffect } from "react";
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
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";
import { 
  Package, 
  Plus, 
  Search,
  Edit,
  Trash2,
  AlertTriangle,
  ArrowUpCircle,
  ArrowDownCircle,
  Loader2,
  History,
  Filter,
  Tags,
  Settings,
  ChevronRight,
  ChevronDown,
  LayoutGrid,
  List,
  Wrench,
  X
} from "lucide-react";

export default function StockPage() {
  const [items, setItems] = useState([]);
  const [movements, setMovements] = useState([]);
  const [categories, setCategories] = useState([]);
  const [subcategories, setSubcategories] = useState([]);
  const [machines, setMachines] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [showLowStockOnly, setShowLowStockOnly] = useState(false);
  const [showItemDialog, setShowItemDialog] = useState(false);
  const [showMovementDialog, setShowMovementDialog] = useState(false);
  const [showCategoryDialog, setShowCategoryDialog] = useState(false);
  const [showSubcategoryDialog, setShowSubcategoryDialog] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [selectedItem, setSelectedItem] = useState(null);
  const [formLoading, setFormLoading] = useState(false);
  const [deleteId, setDeleteId] = useState(null);
  const [deleteCategoryId, setDeleteCategoryId] = useState(null);
  const [deleteSubcategoryId, setDeleteSubcategoryId] = useState(null);
  const [activeTab, setActiveTab] = useState("items");
  const [viewMode, setViewMode] = useState("list"); // list como padrão
  const [newCategoryName, setNewCategoryName] = useState("");
  const [newSubcategoryForm, setNewSubcategoryForm] = useState({ name: "", category_id: "" });
  const [expandedItemId, setExpandedItemId] = useState(null); // Para expandir e mostrar máquinas

  const [itemForm, setItemForm] = useState({
    name: "",
    code: "",
    category: "",
    subcategory_id: "",
    unit: "un",
    quantity: "",
    min_quantity: "",
    unit_price: "",
    location: "",
    notes: "",
    machine_ids: []
  });

  const [movementForm, setMovementForm] = useState({
    item_id: "",
    movement_type: "",
    quantity: "",
    reason: "",
    notes: ""
  });

  const units = [
    { value: "un", label: "Unidade (un)" },
    { value: "L", label: "Litro (L)" },
    { value: "kg", label: "Quilograma (kg)" },
    { value: "m", label: "Metro (m)" },
    { value: "cx", label: "Caixa (cx)" },
    { value: "pc", label: "Peça (pc)" }
  ];

  useEffect(() => {
    fetchData();
  }, [showLowStockOnly]);

  const fetchData = async () => {
    const token = localStorage.getItem("token");
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    
    try {
      const [itemsRes, movementsRes, categoriesRes, subcategoriesRes, machinesRes] = await Promise.all([
        axios.get(`${API}/stock/items?low_stock_only=${showLowStockOnly}`, { headers }),
        axios.get(`${API}/stock/movements`, { headers }),
        axios.get(`${API}/stock/categories`, { headers }),
        axios.get(`${API}/stock/subcategories`, { headers }),
        axios.get(`${API}/machines`, { headers })
      ]);
      setItems(itemsRes.data);
      setMovements(movementsRes.data);
      setCategories(categoriesRes.data);
      setSubcategories(subcategoriesRes.data);
      setMachines(machinesRes.data || []);
    } catch (error) {
      toast.error("Erro ao carregar dados do estoque");
    } finally {
      setLoading(false);
    }
  };

  const handleItemSubmit = async (e) => {
    e.preventDefault();
    setFormLoading(true);

    try {
      const payload = {
        ...itemForm,
        quantity: parseFloat(itemForm.quantity) || 0,
        min_quantity: parseFloat(itemForm.min_quantity) || 0,
        unit_price: parseFloat(itemForm.unit_price) || 0,
        subcategory_id: itemForm.subcategory_id || null,
        machine_ids: itemForm.machine_ids || []
      };

      if (editingItem) {
        await axios.put(`${API}/stock/items/${editingItem.id}`, payload);
        toast.success("Item atualizado com sucesso!");
      } else {
        await axios.post(`${API}/stock/items`, payload);
        toast.success("Item cadastrado com sucesso!");
      }
      
      setShowItemDialog(false);
      resetItemForm();
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao salvar item");
    } finally {
      setFormLoading(false);
    }
  };

  const handleMovementSubmit = async (e) => {
    e.preventDefault();
    setFormLoading(true);

    try {
      const payload = {
        ...movementForm,
        quantity: parseFloat(movementForm.quantity)
      };

      await axios.post(`${API}/stock/movements`, payload);
      toast.success(`${movementForm.movement_type === "entrada" ? "Entrada" : "Saída"} registrada com sucesso!`);
      
      setShowMovementDialog(false);
      resetMovementForm();
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao registrar movimentação");
    } finally {
      setFormLoading(false);
    }
  };

  const handleCreateCategory = async (e) => {
    e.preventDefault();
    if (!newCategoryName.trim()) return;
    
    setFormLoading(true);
    try {
      await axios.post(`${API}/stock/categories`, { name: newCategoryName.trim() });
      toast.success("Categoria criada com sucesso!");
      setNewCategoryName("");
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao criar categoria");
    } finally {
      setFormLoading(false);
    }
  };

  const handleDeleteCategory = async () => {
    if (!deleteCategoryId) return;
    
    try {
      await axios.delete(`${API}/stock/categories/${deleteCategoryId}`);
      toast.success("Categoria removida com sucesso!");
      setDeleteCategoryId(null);
      fetchData();
    } catch (error) {
      toast.error("Erro ao remover categoria");
    }
  };

  const handleDelete = async () => {
    if (!deleteId) return;
    
    try {
      await axios.delete(`${API}/stock/items/${deleteId}`);
      toast.success("Item removido com sucesso!");
      setDeleteId(null);
      fetchData();
    } catch (error) {
      toast.error("Erro ao remover item");
    }
  };

  const openEditDialog = (item) => {
    setEditingItem(item);
    setItemForm({
      name: item.name,
      code: item.code,
      category: item.category,
      subcategory_id: item.subcategory_id || "",
      unit: item.unit,
      quantity: item.quantity.toString(),
      min_quantity: item.min_quantity.toString(),
      unit_price: item.unit_price.toString(),
      location: item.location,
      notes: item.notes,
      machine_ids: item.machine_ids || []
    });
    setShowItemDialog(true);
  };

  const openMovementDialog = (item, type) => {
    setSelectedItem(item);
    setMovementForm({
      item_id: item.id,
      movement_type: type,
      quantity: "",
      reason: "",
      notes: ""
    });
    setShowMovementDialog(true);
  };

  const resetItemForm = () => {
    setItemForm({
      name: "",
      code: "",
      category: "",
      subcategory_id: "",
      unit: "un",
      quantity: "",
      min_quantity: "",
      unit_price: "",
      location: "",
      notes: "",
      machine_ids: []
    });
    setEditingItem(null);
  };

  // Subcategory functions
  const handleSubcategorySubmit = async () => {
    if (!newSubcategoryForm.name.trim() || !newSubcategoryForm.category_id) {
      toast.error("Preencha todos os campos");
      return;
    }
    setFormLoading(true);
    try {
      await axios.post(`${API}/stock/subcategories`, newSubcategoryForm);
      toast.success("Subcategoria criada!");
      setShowSubcategoryDialog(false);
      setNewSubcategoryForm({ name: "", category_id: "" });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao criar subcategoria");
    } finally {
      setFormLoading(false);
    }
  };

  const handleDeleteSubcategory = async () => {
    if (!deleteSubcategoryId) return;
    try {
      await axios.delete(`${API}/stock/subcategories/${deleteSubcategoryId}`);
      toast.success("Subcategoria excluída!");
      setDeleteSubcategoryId(null);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao excluir subcategoria");
    }
  };

  // Filtrar subcategorias baseado na categoria selecionada
  const filteredSubcategories = itemForm.category 
    ? subcategories.filter(s => {
        const cat = categories.find(c => c.name === itemForm.category);
        return cat && s.category_id === cat.id;
      })
    : [];

  const resetMovementForm = () => {
    setMovementForm({
      item_id: "",
      movement_type: "",
      quantity: "",
      reason: "",
      notes: ""
    });
    setSelectedItem(null);
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat("pt-BR", {
      style: "currency",
      currency: "BRL"
    }).format(value);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString("pt-BR");
  };

  const filteredItems = items.filter(
    (item) =>
      item.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.code.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.category.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const lowStockCount = items.filter(i => i.is_low_stock).length;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="spinner w-12 h-12"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in" data-testid="stock-page">
      {/* Page header */}
      <div className="page-header">
        <div>
          <h1 className="page-title font-heading">Controle de Estoque</h1>
          <p className="text-gray-500 mt-1">Gerencie peças e materiais de reposição</p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => setShowCategoryDialog(true)}
            data-testid="manage-categories-btn"
          >
            <Settings size={18} className="mr-2" />
            Categorias
          </Button>
          <Button
            className="bg-black hover:bg-gray-900 text-white font-bold"
            onClick={() => {
              resetItemForm();
              setShowItemDialog(true);
            }}
            data-testid="new-item-btn"
          >
            <Plus size={18} className="mr-2" />
            Novo Item
          </Button>
        </div>
      </div>

      {/* Low stock alert */}
      {lowStockCount > 0 && (
        <Card className="bg-orange-50 border-orange-200">
          <CardContent className="py-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center">
                <AlertTriangle className="text-[#E31A1A]" size={20} />
              </div>
              <div className="flex-1">
                <p className="font-bold text-orange-800">Atenção: Estoque Baixo</p>
                <p className="text-sm text-[#E31A1A]">
                  {lowStockCount} {lowStockCount === 1 ? "item está" : "itens estão"} abaixo do estoque mínimo
                </p>
              </div>
              <Button
                variant="outline"
                className="border-orange-300 text-[#E31A1A] hover:bg-orange-100"
                onClick={() => setShowLowStockOnly(!showLowStockOnly)}
              >
                {showLowStockOnly ? "Ver Todos" : "Ver Itens"}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="items" data-testid="tab-items">
            <Package size={16} className="mr-2" />
            Itens ({items.length})
          </TabsTrigger>
          <TabsTrigger value="movements" data-testid="tab-movements">
            <History size={16} className="mr-2" />
            Movimentações ({movements.length})
          </TabsTrigger>
          <TabsTrigger value="categories" data-testid="tab-categories">
            <Tags size={16} className="mr-2" />
            Categorias ({categories.length})
          </TabsTrigger>
        </TabsList>

        {/* Items Tab */}
        <TabsContent value="items" className="space-y-4">
          {/* Search and View Toggle */}
          <div className="flex gap-4 items-center">
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
              <Input
                placeholder="Buscar por nome, código ou categoria..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 h-11 bg-white border border-gray-300 rounded-md focus:border-[#E31A1A] focus:ring-2 focus:ring-[#E31A1A] focus:outline-none"
                data-testid="stock-search-input"
              />
            </div>
            <Button className="bg-[#E31A1A] hover:bg-[#c41616] text-white">
              <Search size={16} className="mr-2" />
              Buscar
            </Button>
            <Button
              variant={showLowStockOnly ? "default" : "outline"}
              onClick={() => setShowLowStockOnly(!showLowStockOnly)}
              className={showLowStockOnly ? "bg-[#E31A1A] hover:bg-[#E31A1A]" : ""}
            >
              <Filter size={16} className="mr-2" />
              Estoque Baixo
            </Button>
            <div className="flex border rounded-lg overflow-hidden">
              <Button 
                variant={viewMode === "list" ? "default" : "ghost"} 
                size="sm" 
                onClick={() => setViewMode("list")}
                className={viewMode === "list" ? "bg-[#E31A1A] hover:bg-red-700" : ""}
                data-testid="stock-view-list"
              >
                <List size={18} />
              </Button>
              <Button 
                variant={viewMode === "grid" ? "default" : "ghost"} 
                size="sm" 
                onClick={() => setViewMode("grid")}
                className={viewMode === "grid" ? "bg-[#E31A1A] hover:bg-red-700" : ""}
                data-testid="stock-view-grid"
              >
                <LayoutGrid size={18} />
              </Button>
            </div>
          </div>

          {/* Items List/Grid */}
          {filteredItems.length > 0 ? (
            viewMode === "list" ? (
              /* Lista (Tabela) */
              <div className="border rounded-lg overflow-hidden">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Item</th>
                      <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Código</th>
                      <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Categoria</th>
                      <th className="px-4 py-3 text-right text-sm font-semibold text-gray-700">Quantidade</th>
                      <th className="px-4 py-3 text-right text-sm font-semibold text-gray-700">Mínimo</th>
                      <th className="px-4 py-3 text-right text-sm font-semibold text-gray-700">Preço Unit.</th>
                      <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Local</th>
                      <th className="px-4 py-3 text-center text-sm font-semibold text-gray-700">Ações</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {filteredItems.map((item) => (
                      <>
                      <tr 
                        key={item.id} 
                        className={`hover:bg-gray-50 cursor-pointer ${item.is_low_stock ? "bg-orange-50" : ""} ${expandedItemId === item.id ? "bg-blue-50" : ""}`} 
                        data-testid={`stock-item-row-${item.id}`}
                        onClick={() => setExpandedItemId(expandedItemId === item.id ? null : item.id)}
                      >
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            {item.machine_ids && item.machine_ids.length > 0 ? (
                              expandedItemId === item.id ? 
                                <ChevronDown className="text-blue-500" size={18} /> : 
                                <ChevronRight className="text-blue-500" size={18} />
                            ) : (
                              <Package className={`${item.is_low_stock ? "text-orange-500" : "text-gray-400"}`} size={18} />
                            )}
                            <span className="font-medium">{item.name}</span>
                            {item.is_low_stock && (
                              <span className="text-xs bg-orange-100 text-orange-700 px-2 py-0.5 rounded">Baixo</span>
                            )}
                            {item.machine_ids && item.machine_ids.length > 0 && (
                              <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded flex items-center gap-1">
                                <Wrench size={10} />
                                {item.machine_ids.length}
                              </span>
                            )}
                          </div>
                        </td>
                        <td className="px-4 py-3 text-gray-600 font-mono text-sm">{item.code || "-"}</td>
                        <td className="px-4 py-3 text-gray-600">{item.category || "-"}</td>
                        <td className={`px-4 py-3 text-right font-bold ${item.is_low_stock ? "text-orange-600" : "text-gray-900"}`}>
                          {item.quantity} {item.unit}
                        </td>
                        <td className="px-4 py-3 text-right text-gray-600">{item.min_quantity} {item.unit}</td>
                        <td className="px-4 py-3 text-right text-gray-600">{item.unit_price > 0 ? formatCurrency(item.unit_price) : "-"}</td>
                        <td className="px-4 py-3 text-gray-600">{item.location || "-"}</td>
                        <td className="px-4 py-3" onClick={(e) => e.stopPropagation()}>
                          <div className="flex justify-center gap-1">
                            <Button size="sm" variant="ghost" className="h-8 w-8 p-0 text-green-600 hover:bg-green-50" onClick={() => openMovementDialog(item, "entrada")} title="Entrada">
                              <ArrowUpCircle size={16} />
                            </Button>
                            <Button size="sm" variant="ghost" className="h-8 w-8 p-0 text-red-600 hover:bg-red-50" onClick={() => openMovementDialog(item, "saida")} title="Saída">
                              <ArrowDownCircle size={16} />
                            </Button>
                            <Button size="sm" variant="ghost" className="h-8 w-8 p-0" onClick={() => openEditDialog(item)} title="Editar">
                              <Edit size={16} />
                            </Button>
                            <Button size="sm" variant="ghost" className="h-8 w-8 p-0 text-red-600 hover:bg-red-50" onClick={() => setDeleteId(item.id)} title="Excluir">
                              <Trash2 size={16} />
                            </Button>
                          </div>
                        </td>
                      </tr>
                      {/* Linha expandida com máquinas */}
                      {expandedItemId === item.id && item.machine_ids && item.machine_ids.length > 0 && (
                        <tr key={`${item.id}-machines`} className="bg-blue-50/50">
                          <td colSpan={8} className="px-4 py-3">
                            <div className="pl-8">
                              <div className="flex items-center gap-2 mb-2">
                                <Wrench size={14} className="text-blue-600" />
                                <span className="text-sm font-medium text-blue-700">Máquinas Associadas:</span>
                              </div>
                              <div className="flex flex-wrap gap-2">
                                {item.machine_ids.map(machineId => {
                                  const machine = machines.find(m => m.id === machineId);
                                  return machine ? (
                                    <span key={machineId} className="inline-flex items-center gap-1 px-3 py-1 bg-white border border-blue-200 rounded-full text-sm text-blue-700">
                                      <Wrench size={12} />
                                      {machine.name}
                                      {machine.plate && <span className="text-blue-500 text-xs">({machine.plate})</span>}
                                    </span>
                                  ) : null;
                                })}
                              </div>
                            </div>
                          </td>
                        </tr>
                      )}
                      </>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              /* Grid de Cards */
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredItems.map((item) => (
                <Card 
                  key={item.id} 
                  className={`stat-card ${item.is_low_stock ? "border-orange-300 bg-orange-50/50" : ""}`}
                  data-testid={`stock-item-${item.id}`}
                >
                  <CardContent className="pt-6">
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${
                          item.is_low_stock ? "bg-orange-100" : "bg-gray-100"
                        }`}>
                          <Package className={item.is_low_stock ? "text-[#E31A1A]" : "text-gray-600"} size={24} />
                        </div>
                        <div>
                          <h3 className="font-bold text-black">{item.name}</h3>
                          {item.code && (
                            <p className="font-mono text-xs text-gray-500">{item.code}</p>
                          )}
                        </div>
                      </div>
                      {item.is_low_stock && (
                        <span className="status-badge badge-maintenance">
                          Baixo
                        </span>
                      )}
                    </div>

                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-500">Quantidade:</span>
                        <span className={`font-bold ${item.is_low_stock ? "text-[#E31A1A]" : "text-black"}`}>
                          {item.quantity} {item.unit}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500">Mínimo:</span>
                        <span className="font-medium text-gray-700">{item.min_quantity} {item.unit}</span>
                      </div>
                      {item.category && (
                        <div className="flex justify-between">
                          <span className="text-gray-500">Categoria:</span>
                          <span className="font-medium text-gray-700">{item.category}</span>
                        </div>
                      )}
                      {item.unit_price > 0 && (
                        <div className="flex justify-between">
                          <span className="text-gray-500">Preço Unit.:</span>
                          <span className="font-medium text-gray-700">{formatCurrency(item.unit_price)}</span>
                        </div>
                      )}
                      {item.location && (
                        <div className="flex justify-between">
                          <span className="text-gray-500">Local:</span>
                          <span className="font-medium text-gray-700">{item.location}</span>
                        </div>
                      )}
                    </div>

                    {/* Actions */}
                    <div className="flex gap-2 mt-4 pt-4 border-t border-gray-200">
                      <Button
                        size="sm"
                        className="flex-1 bg-green-600 hover:bg-green-700"
                        onClick={() => openMovementDialog(item, "entrada")}
                        data-testid={`entry-btn-${item.id}`}
                      >
                        <ArrowUpCircle size={16} className="mr-1" />
                        Entrada
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        className="flex-1 text-red-600 border-red-200 hover:bg-red-50"
                        onClick={() => openMovementDialog(item, "saida")}
                        data-testid={`exit-btn-${item.id}`}
                      >
                        <ArrowDownCircle size={16} className="mr-1" />
                        Saída
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => openEditDialog(item)}
                        data-testid={`edit-item-${item.id}`}
                      >
                        <Edit size={16} />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-red-600 hover:bg-red-50"
                        onClick={() => setDeleteId(item.id)}
                        data-testid={`delete-item-${item.id}`}
                      >
                        <Trash2 size={16} />
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
            )
          ) : (
            <div className="empty-state">
              <Package className="text-gray-300 mb-4" size={64} />
              <p className="text-lg font-medium text-gray-600">Nenhum item encontrado</p>
              <p className="text-gray-400 mb-4">
                {searchTerm || showLowStockOnly ? "Tente ajustar os filtros" : "Cadastre seu primeiro item"}
              </p>
              {!searchTerm && !showLowStockOnly && (
                <Button
                  className="bg-[#E31A1A] hover:bg-[#E31A1A]"
                  onClick={() => setShowItemDialog(true)}
                >
                  <Plus size={18} className="mr-2" />
                  Cadastrar Item
                </Button>
              )}
            </div>
          )}
        </TabsContent>

        {/* Movements Tab */}
        <TabsContent value="movements">
          {movements.length > 0 ? (
            <Card>
              <CardContent className="p-0">
                <div className="overflow-x-auto">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Tipo</th>
                        <th>Item</th>
                        <th>Quantidade</th>
                        <th>Anterior</th>
                        <th>Novo</th>
                        <th>Motivo</th>
                        <th>Data</th>
                      </tr>
                    </thead>
                    <tbody>
                      {movements.map((mov) => (
                        <tr key={mov.id} data-testid={`movement-row-${mov.id}`}>
                          <td>
                            <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                              mov.movement_type === "entrada" ? "bg-green-50" : "bg-red-50"
                            }`}>
                              {mov.movement_type === "entrada" ? (
                                <ArrowUpCircle className="text-green-600" size={16} />
                              ) : (
                                <ArrowDownCircle className="text-red-600" size={16} />
                              )}
                            </div>
                          </td>
                          <td className="font-medium text-black">{mov.item_name}</td>
                          <td className={`font-bold ${
                            mov.movement_type === "entrada" ? "text-green-600" : "text-red-600"
                          }`}>
                            {mov.movement_type === "entrada" ? "+" : "-"}{mov.quantity}
                          </td>
                          <td className="font-mono text-gray-500">{mov.previous_quantity}</td>
                          <td className="font-mono text-black">{mov.new_quantity}</td>
                          <td className="text-gray-600">{mov.reason || "-"}</td>
                          <td className="text-sm text-gray-500">{formatDate(mov.created_at)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          ) : (
            <div className="empty-state">
              <History className="text-gray-300 mb-4" size={64} />
              <p className="text-lg font-medium text-gray-600">Nenhuma movimentação registrada</p>
              <p className="text-gray-400">As movimentações aparecerão aqui</p>
            </div>
          )}
        </TabsContent>

        {/* Categories Tab */}
        <TabsContent value="categories" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Categories Section */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Tags className="text-[#E31A1A]" size={20} />
                  Categorias
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <form onSubmit={handleCreateCategory} className="flex gap-2">
                  <Input
                    value={newCategoryName}
                    onChange={(e) => setNewCategoryName(e.target.value)}
                    placeholder="Nova categoria..."
                    className="form-input flex-1"
                  />
                  <Button type="submit" className="bg-[#E31A1A] hover:bg-red-700" disabled={!newCategoryName.trim()}>
                    <Plus size={18} />
                  </Button>
                </form>
                <div className="space-y-2 max-h-[300px] overflow-y-auto">
                  {categories.map((cat) => (
                    <div key={cat.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-center gap-2">
                        <Tags className="text-gray-400" size={16} />
                        <span className="font-medium">{cat.name}</span>
                        <span className="text-xs text-gray-400">
                          ({subcategories.filter(s => s.category_id === cat.id).length} subcategorias)
                        </span>
                      </div>
                      <Button variant="ghost" size="sm" className="text-red-600 hover:bg-red-50" onClick={() => setDeleteCategoryId(cat.id)}>
                        <Trash2 size={16} />
                      </Button>
                    </div>
                  ))}
                  {categories.length === 0 && (
                    <p className="text-gray-400 text-center py-4">Nenhuma categoria</p>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Subcategories Section */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <ChevronRight className="text-blue-500" size={20} />
                  Subcategorias
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex gap-2">
                  <Select value={newSubcategoryForm.category_id} onValueChange={(v) => setNewSubcategoryForm({...newSubcategoryForm, category_id: v})}>
                    <SelectTrigger className="w-1/2">
                      <SelectValue placeholder="Categoria" />
                    </SelectTrigger>
                    <SelectContent>
                      {categories.map((cat) => (
                        <SelectItem key={cat.id} value={cat.id}>{cat.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Input
                    value={newSubcategoryForm.name}
                    onChange={(e) => setNewSubcategoryForm({...newSubcategoryForm, name: e.target.value})}
                    placeholder="Nova subcategoria..."
                    className="flex-1"
                  />
                  <Button onClick={handleSubcategorySubmit} className="bg-blue-600 hover:bg-blue-700" disabled={!newSubcategoryForm.name.trim() || !newSubcategoryForm.category_id}>
                    <Plus size={18} />
                  </Button>
                </div>
                <div className="space-y-2 max-h-[300px] overflow-y-auto">
                  {subcategories.map((sub) => (
                    <div key={sub.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-center gap-2">
                        <ChevronRight className="text-blue-400" size={16} />
                        <span className="font-medium">{sub.name}</span>
                        <span className="text-xs text-gray-400">({sub.category_name})</span>
                      </div>
                      <Button variant="ghost" size="sm" className="text-red-600 hover:bg-red-50" onClick={() => setDeleteSubcategoryId(sub.id)}>
                        <Trash2 size={16} />
                      </Button>
                    </div>
                  ))}
                  {subcategories.length === 0 && (
                    <p className="text-gray-400 text-center py-4">Nenhuma subcategoria</p>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>

      {/* Manage Categories Dialog */}
      <Dialog open={showCategoryDialog} onOpenChange={setShowCategoryDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="font-heading text-xl font-bold flex items-center gap-2">
              <Tags className="text-[#E31A1A]" size={24} />
              Gerenciar Categorias
            </DialogTitle>
            <DialogDescription>
              Crie e gerencie as categorias de itens do estoque
            </DialogDescription>
          </DialogHeader>

          {/* Create new category */}
          <form onSubmit={handleCreateCategory} className="flex gap-2">
            <Input
              value={newCategoryName}
              onChange={(e) => setNewCategoryName(e.target.value)}
              placeholder="Nome da nova categoria..."
              className="form-input flex-1"
              data-testid="new-category-input"
            />
            <Button
              type="submit"
              className="bg-[#E31A1A] hover:bg-[#E31A1A]"
              disabled={formLoading || !newCategoryName.trim()}
              data-testid="create-category-btn"
            >
              {formLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus size={18} />}
            </Button>
          </form>

          {/* Categories list */}
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {categories.length > 0 ? (
              categories.map((cat) => (
                <div
                  key={cat.id}
                  className="flex items-center justify-between p-3 bg-white rounded-lg"
                  data-testid={`category-item-${cat.id}`}
                >
                  <div className="flex items-center gap-2">
                    <Tags className="text-gray-400" size={16} />
                    <span className="font-medium text-black">{cat.name}</span>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-red-600 hover:bg-red-50"
                    onClick={() => setDeleteCategoryId(cat.id)}
                    data-testid={`delete-category-${cat.id}`}
                  >
                    <Trash2 size={16} />
                  </Button>
                </div>
              ))
            ) : (
              <div className="text-center py-8 text-gray-400">
                <Tags className="mx-auto mb-2" size={32} />
                <p>Nenhuma categoria cadastrada</p>
              </div>
            )}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCategoryDialog(false)}>
              Fechar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Create/Edit Item Dialog */}
      <Dialog open={showItemDialog} onOpenChange={setShowItemDialog}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="font-heading text-xl font-bold">
              {editingItem ? "Editar Item" : "Novo Item de Estoque"}
            </DialogTitle>
            <DialogDescription>
              {editingItem 
                ? "Atualize as informações do item"
                : "Cadastre uma nova peça ou material"
              }
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleItemSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label className="form-label">Nome *</Label>
                <Input
                  value={itemForm.name}
                  onChange={(e) => setItemForm({...itemForm, name: e.target.value})}
                  placeholder="Ex: Filtro de Óleo"
                  required
                  className="form-input"
                  data-testid="item-name-input"
                />
              </div>
              <div className="space-y-2">
                <Label className="form-label">Código</Label>
                <Input
                  value={itemForm.code}
                  onChange={(e) => setItemForm({...itemForm, code: e.target.value.toUpperCase()})}
                  placeholder="Ex: FO-001"
                  className="form-input font-mono"
                  data-testid="item-code-input"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label className="form-label">Categoria</Label>
                <Select
                  value={itemForm.category}
                  onValueChange={(value) => setItemForm({...itemForm, category: value, subcategory_id: ""})}
                >
                  <SelectTrigger className="form-input" data-testid="item-category-select">
                    <SelectValue placeholder="Selecione" />
                  </SelectTrigger>
                  <SelectContent>
                    {categories.map((cat) => (
                      <SelectItem key={cat.id} value={cat.name}>{cat.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {categories.length === 0 && (
                  <p className="text-xs text-[#E31A1A]">
                    Nenhuma categoria.{" "}
                    <button
                      type="button"
                      className="underline"
                      onClick={() => {
                        setShowItemDialog(false);
                        setShowCategoryDialog(true);
                      }}
                    >
                      Criar categoria
                    </button>
                  </p>
                )}
              </div>
              <div className="space-y-2">
                <Label className="form-label">Subcategoria (opcional)</Label>
                <Select
                  value={itemForm.subcategory_id}
                  onValueChange={(value) => setItemForm({...itemForm, subcategory_id: value === "__none__" ? "" : value})}
                  disabled={!itemForm.category || filteredSubcategories.length === 0}
                >
                  <SelectTrigger className="form-input" data-testid="item-subcategory-select">
                    <SelectValue placeholder={!itemForm.category ? "Selecione categoria" : filteredSubcategories.length === 0 ? "Sem subcategorias" : "Selecione"} />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="__none__">Nenhuma</SelectItem>
                    {filteredSubcategories.map((sub) => (
                      <SelectItem key={sub.id} value={sub.id}>{sub.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="space-y-2">
              <Label className="form-label">Unidade</Label>
              <Select
                value={itemForm.unit}
                onValueChange={(value) => setItemForm({...itemForm, unit: value})}
              >
                <SelectTrigger className="form-input" data-testid="item-unit-select">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {units.map((u) => (
                    <SelectItem key={u.value} value={u.value}>{u.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {!editingItem && (
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label className="form-label">Quantidade Inicial</Label>
                  <Input
                    type="number"
                    step="0.01"
                    min="0"
                    value={itemForm.quantity}
                    onChange={(e) => setItemForm({...itemForm, quantity: e.target.value})}
                    placeholder="0"
                    className="form-input font-mono"
                    data-testid="item-quantity-input"
                  />
                </div>
                <div className="space-y-2">
                  <Label className="form-label">Estoque Mínimo</Label>
                  <Input
                    type="number"
                    step="0.01"
                    min="0"
                    value={itemForm.min_quantity}
                    onChange={(e) => setItemForm({...itemForm, min_quantity: e.target.value})}
                    placeholder="0"
                    className="form-input font-mono"
                    data-testid="item-min-quantity-input"
                  />
                </div>
              </div>
            )}

            {editingItem && (
              <div className="space-y-2">
                <Label className="form-label">Estoque Mínimo</Label>
                <Input
                  type="number"
                  step="0.01"
                  min="0"
                  value={itemForm.min_quantity}
                  onChange={(e) => setItemForm({...itemForm, min_quantity: e.target.value})}
                  placeholder="0"
                  className="form-input font-mono"
                  data-testid="item-min-quantity-input"
                />
              </div>
            )}

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label className="form-label">Preço Unitário (R$)</Label>
                <Input
                  type="number"
                  step="0.01"
                  min="0"
                  value={itemForm.unit_price}
                  onChange={(e) => setItemForm({...itemForm, unit_price: e.target.value})}
                  placeholder="0,00"
                  className="form-input font-mono"
                  data-testid="item-price-input"
                />
              </div>
              <div className="space-y-2">
                <Label className="form-label">Localização</Label>
                <Input
                  value={itemForm.location}
                  onChange={(e) => setItemForm({...itemForm, location: e.target.value})}
                  placeholder="Ex: Prateleira A1"
                  className="form-input"
                  data-testid="item-location-input"
                />
              </div>
            </div>

            {/* Vinculação de Máquinas */}
            <div className="space-y-2">
              <Label className="form-label flex items-center gap-2">
                <Wrench size={14} />
                Vincular a Máquinas (opcional)
              </Label>
              <div className="flex gap-2">
                <Select
                  onValueChange={(value) => {
                    if (value && !itemForm.machine_ids.includes(value)) {
                      setItemForm({...itemForm, machine_ids: [...itemForm.machine_ids, value]});
                    }
                  }}
                >
                  <SelectTrigger className="form-input flex-1" data-testid="item-machine-select">
                    <SelectValue placeholder={machines.length === 0 ? "Nenhuma máquina cadastrada" : "Selecione uma máquina"} />
                  </SelectTrigger>
                  <SelectContent>
                    {machines.filter(m => !itemForm.machine_ids.includes(m.id)).map((machine) => (
                      <SelectItem key={machine.id} value={machine.id}>
                        {machine.name} {machine.plate ? `(${machine.plate})` : ''}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              {itemForm.machine_ids.length > 0 && (
                <div className="flex flex-wrap gap-2 mt-2">
                  {itemForm.machine_ids.map(machineId => {
                    const machine = machines.find(m => m.id === machineId);
                    return machine ? (
                      <span key={machineId} className="inline-flex items-center gap-1 px-2 py-1 bg-gray-100 rounded-md text-sm">
                        <Wrench size={12} />
                        {machine.name}
                        <button
                          type="button"
                          onClick={() => setItemForm({...itemForm, machine_ids: itemForm.machine_ids.filter(id => id !== machineId)})}
                          className="text-gray-500 hover:text-red-500"
                        >
                          <X size={14} />
                        </button>
                      </span>
                    ) : null;
                  })}
                </div>
              )}
              <p className="text-xs text-gray-500">Selecione as máquinas que utilizam este item de estoque</p>
            </div>

            <div className="space-y-2">
              <Label className="form-label">Observações</Label>
              <Input
                value={itemForm.notes}
                onChange={(e) => setItemForm({...itemForm, notes: e.target.value})}
                placeholder="Notas adicionais..."
                className="form-input"
                data-testid="item-notes-input"
              />
            </div>

            <DialogFooter className="gap-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => setShowItemDialog(false)}
              >
                Cancelar
              </Button>
              <Button
                type="submit"
                className="bg-black hover:bg-gray-900"
                disabled={formLoading}
                data-testid="item-submit-btn"
              >
                {formLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Salvando...
                  </>
                ) : editingItem ? (
                  "Atualizar"
                ) : (
                  "Cadastrar"
                )}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Movement Dialog */}
      <Dialog open={showMovementDialog} onOpenChange={setShowMovementDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="font-heading text-xl font-bold flex items-center gap-2">
              {movementForm.movement_type === "entrada" ? (
                <>
                  <ArrowUpCircle className="text-green-600" size={24} />
                  Entrada de Estoque
                </>
              ) : (
                <>
                  <ArrowDownCircle className="text-red-600" size={24} />
                  Saída de Estoque
                </>
              )}
            </DialogTitle>
            {selectedItem && (
              <DialogDescription>
                Item: <strong>{selectedItem.name}</strong> | Estoque atual: <strong>{selectedItem.quantity} {selectedItem.unit}</strong>
              </DialogDescription>
            )}
          </DialogHeader>

          <form onSubmit={handleMovementSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label className="form-label">Quantidade *</Label>
              <Input
                type="number"
                step="0.01"
                min="0.01"
                value={movementForm.quantity}
                onChange={(e) => setMovementForm({...movementForm, quantity: e.target.value})}
                placeholder="0"
                required
                className="form-input font-mono text-lg"
                data-testid="movement-quantity-input"
              />
            </div>

            <div className="space-y-2">
              <Label className="form-label">Motivo</Label>
              <Select
                value={movementForm.reason}
                onValueChange={(value) => setMovementForm({...movementForm, reason: value})}
              >
                <SelectTrigger className="form-input" data-testid="movement-reason-select">
                  <SelectValue placeholder="Selecione um motivo" />
                </SelectTrigger>
                <SelectContent>
                  {movementForm.movement_type === "entrada" ? (
                    <>
                      <SelectItem value="Compra">Compra</SelectItem>
                      <SelectItem value="Devolução">Devolução</SelectItem>
                      <SelectItem value="Transferência">Transferência</SelectItem>
                      <SelectItem value="Ajuste de inventário">Ajuste de inventário</SelectItem>
                      <SelectItem value="Outro">Outro</SelectItem>
                    </>
                  ) : (
                    <>
                      <SelectItem value="Uso em manutenção">Uso em manutenção</SelectItem>
                      <SelectItem value="Defeito/Descarte">Defeito/Descarte</SelectItem>
                      <SelectItem value="Transferência">Transferência</SelectItem>
                      <SelectItem value="Ajuste de inventário">Ajuste de inventário</SelectItem>
                      <SelectItem value="Outro">Outro</SelectItem>
                    </>
                  )}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label className="form-label">Observações</Label>
              <Input
                value={movementForm.notes}
                onChange={(e) => setMovementForm({...movementForm, notes: e.target.value})}
                placeholder="Notas adicionais..."
                className="form-input"
                data-testid="movement-notes-input"
              />
            </div>

            <DialogFooter className="gap-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => setShowMovementDialog(false)}
              >
                Cancelar
              </Button>
              <Button
                type="submit"
                className={movementForm.movement_type === "entrada" 
                  ? "bg-green-600 hover:bg-green-700" 
                  : "bg-red-600 hover:bg-red-700"
                }
                disabled={formLoading}
                data-testid="movement-submit-btn"
              >
                {formLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Registrando...
                  </>
                ) : (
                  `Registrar ${movementForm.movement_type === "entrada" ? "Entrada" : "Saída"}`
                )}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Delete Item Confirmation Dialog */}
      <Dialog open={!!deleteId} onOpenChange={() => setDeleteId(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="text-red-600">Confirmar Exclusão</DialogTitle>
            <DialogDescription>
              Tem certeza que deseja excluir este item? Todo o histórico de movimentações será perdido. Esta ação não pode ser desfeita.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteId(null)}>
              Cancelar
            </Button>
            <Button
              className="bg-red-600 hover:bg-red-700"
              onClick={handleDelete}
              data-testid="confirm-delete-item-btn"
            >
              Excluir
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Category Confirmation Dialog */}
      <Dialog open={!!deleteCategoryId} onOpenChange={() => setDeleteCategoryId(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="text-red-600">Excluir Categoria</DialogTitle>
            <DialogDescription>
              Tem certeza que deseja excluir esta categoria? Os itens que usam esta categoria não serão afetados.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteCategoryId(null)}>
              Cancelar
            </Button>
            <Button
              className="bg-red-600 hover:bg-red-700"
              onClick={handleDeleteCategory}
              data-testid="confirm-delete-category-btn"
            >
              Excluir
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Subcategory Confirmation Dialog */}
      <Dialog open={!!deleteSubcategoryId} onOpenChange={() => setDeleteSubcategoryId(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="text-red-600">Excluir Subcategoria</DialogTitle>
            <DialogDescription>
              Tem certeza que deseja excluir esta subcategoria? Os itens que usam esta subcategoria não serão afetados.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteSubcategoryId(null)}>
              Cancelar
            </Button>
            <Button
              className="bg-red-600 hover:bg-red-700"
              onClick={handleDeleteSubcategory}
              data-testid="confirm-delete-subcategory-btn"
            >
              Excluir
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
