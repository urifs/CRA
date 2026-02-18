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
  Filter
} from "lucide-react";

export default function StockPage() {
  const [items, setItems] = useState([]);
  const [movements, setMovements] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [showLowStockOnly, setShowLowStockOnly] = useState(false);
  const [showItemDialog, setShowItemDialog] = useState(false);
  const [showMovementDialog, setShowMovementDialog] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [selectedItem, setSelectedItem] = useState(null);
  const [formLoading, setFormLoading] = useState(false);
  const [deleteId, setDeleteId] = useState(null);
  const [activeTab, setActiveTab] = useState("items");

  const [itemForm, setItemForm] = useState({
    name: "",
    code: "",
    category: "",
    unit: "un",
    quantity: "",
    min_quantity: "",
    unit_price: "",
    location: "",
    notes: ""
  });

  const [movementForm, setMovementForm] = useState({
    item_id: "",
    movement_type: "",
    quantity: "",
    reason: "",
    notes: ""
  });

  const categories = [
    "Filtro",
    "Óleo",
    "Correia",
    "Rolamento",
    "Parafuso",
    "Pneu",
    "Bateria",
    "Lâmpada",
    "Outros"
  ];

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
    try {
      const [itemsRes, movementsRes] = await Promise.all([
        axios.get(`${API}/stock/items?low_stock_only=${showLowStockOnly}`),
        axios.get(`${API}/stock/movements`)
      ]);
      setItems(itemsRes.data);
      setMovements(movementsRes.data);
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
        unit_price: parseFloat(itemForm.unit_price) || 0
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
      unit: item.unit,
      quantity: item.quantity.toString(),
      min_quantity: item.min_quantity.toString(),
      unit_price: item.unit_price.toString(),
      location: item.location,
      notes: item.notes
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
      unit: "un",
      quantity: "",
      min_quantity: "",
      unit_price: "",
      location: "",
      notes: ""
    });
    setEditingItem(null);
  };

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
          <p className="text-slate-500 mt-1">Gerencie peças e materiais de reposição</p>
        </div>
        <Button
          className="bg-slate-900 hover:bg-slate-800 text-white font-bold"
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

      {/* Low stock alert */}
      {lowStockCount > 0 && (
        <Card className="bg-orange-50 border-orange-200">
          <CardContent className="py-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center">
                <AlertTriangle className="text-orange-600" size={20} />
              </div>
              <div className="flex-1">
                <p className="font-bold text-orange-800">Atenção: Estoque Baixo</p>
                <p className="text-sm text-orange-600">
                  {lowStockCount} {lowStockCount === 1 ? "item está" : "itens estão"} abaixo do estoque mínimo
                </p>
              </div>
              <Button
                variant="outline"
                className="border-orange-300 text-orange-700 hover:bg-orange-100"
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
        </TabsList>

        {/* Items Tab */}
        <TabsContent value="items" className="space-y-4">
          {/* Search */}
          <div className="flex gap-4">
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={20} />
              <Input
                placeholder="Buscar por nome, código ou categoria..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 form-input"
                data-testid="stock-search-input"
              />
            </div>
            <Button
              variant={showLowStockOnly ? "default" : "outline"}
              onClick={() => setShowLowStockOnly(!showLowStockOnly)}
              className={showLowStockOnly ? "bg-orange-500 hover:bg-orange-600" : ""}
            >
              <Filter size={16} className="mr-2" />
              Estoque Baixo
            </Button>
          </div>

          {/* Items Grid */}
          {filteredItems.length > 0 ? (
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
                          item.is_low_stock ? "bg-orange-100" : "bg-slate-100"
                        }`}>
                          <Package className={item.is_low_stock ? "text-orange-600" : "text-slate-600"} size={24} />
                        </div>
                        <div>
                          <h3 className="font-bold text-slate-900">{item.name}</h3>
                          {item.code && (
                            <p className="font-mono text-xs text-slate-500">{item.code}</p>
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
                        <span className="text-slate-500">Quantidade:</span>
                        <span className={`font-bold ${item.is_low_stock ? "text-orange-600" : "text-slate-900"}`}>
                          {item.quantity} {item.unit}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-500">Mínimo:</span>
                        <span className="font-medium text-slate-700">{item.min_quantity} {item.unit}</span>
                      </div>
                      {item.category && (
                        <div className="flex justify-between">
                          <span className="text-slate-500">Categoria:</span>
                          <span className="font-medium text-slate-700">{item.category}</span>
                        </div>
                      )}
                      {item.unit_price > 0 && (
                        <div className="flex justify-between">
                          <span className="text-slate-500">Preço Unit.:</span>
                          <span className="font-medium text-slate-700">{formatCurrency(item.unit_price)}</span>
                        </div>
                      )}
                      {item.location && (
                        <div className="flex justify-between">
                          <span className="text-slate-500">Local:</span>
                          <span className="font-medium text-slate-700">{item.location}</span>
                        </div>
                      )}
                    </div>

                    {/* Actions */}
                    <div className="flex gap-2 mt-4 pt-4 border-t border-slate-200">
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
          ) : (
            <div className="empty-state">
              <Package className="text-slate-300 mb-4" size={64} />
              <p className="text-lg font-medium text-slate-600">Nenhum item encontrado</p>
              <p className="text-slate-400 mb-4">
                {searchTerm || showLowStockOnly ? "Tente ajustar os filtros" : "Cadastre seu primeiro item"}
              </p>
              {!searchTerm && !showLowStockOnly && (
                <Button
                  className="bg-orange-500 hover:bg-orange-600"
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
                          <td className="font-medium text-slate-900">{mov.item_name}</td>
                          <td className={`font-bold ${
                            mov.movement_type === "entrada" ? "text-green-600" : "text-red-600"
                          }`}>
                            {mov.movement_type === "entrada" ? "+" : "-"}{mov.quantity}
                          </td>
                          <td className="font-mono text-slate-500">{mov.previous_quantity}</td>
                          <td className="font-mono text-slate-900">{mov.new_quantity}</td>
                          <td className="text-slate-600">{mov.reason || "-"}</td>
                          <td className="text-sm text-slate-500">{formatDate(mov.created_at)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          ) : (
            <div className="empty-state">
              <History className="text-slate-300 mb-4" size={64} />
              <p className="text-lg font-medium text-slate-600">Nenhuma movimentação registrada</p>
              <p className="text-slate-400">As movimentações aparecerão aqui</p>
            </div>
          )}
        </TabsContent>
      </Tabs>

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
                  onValueChange={(value) => setItemForm({...itemForm, category: value})}
                >
                  <SelectTrigger className="form-input" data-testid="item-category-select">
                    <SelectValue placeholder="Selecione" />
                  </SelectTrigger>
                  <SelectContent>
                    {categories.map((cat) => (
                      <SelectItem key={cat} value={cat}>{cat}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
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
                className="bg-slate-900 hover:bg-slate-800"
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

      {/* Delete Confirmation Dialog */}
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
    </div>
  );
}
