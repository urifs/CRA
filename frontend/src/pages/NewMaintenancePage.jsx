import { useState, useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import axios from "axios";
import { API } from "@/App";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Calendar } from "@/components/ui/calendar";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { 
  ArrowLeft, 
  Calendar as CalendarIcon,
  Loader2,
  Shield,
  AlertTriangle,
  Truck,
  Droplet,
  Package,
  Plus,
  X,
  Minus
} from "lucide-react";
import { format } from "date-fns";
import { ptBR } from "date-fns/locale";
import { Checkbox } from "@/components/ui/checkbox";

export default function NewMaintenancePage() {
  const [searchParams] = useSearchParams();
  const preselectedMachine = searchParams.get("machine");
  
  const [machines, setMachines] = useState([]);
  const [stockItems, setStockItems] = useState([]);
  const [selectedParts, setSelectedParts] = useState([]); // {item_id, item_name, quantity, max_quantity, unit_price}
  const [laborCost, setLaborCost] = useState(""); // Valor de mão de obra
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [date, setDate] = useState(new Date());
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    machine_id: preselectedMachine || "",
    part_name: "",
    part_value: "",
    maintenance_type: "",
    description: "",
    is_oil_change: false
  });

  useEffect(() => {
    fetchMachines();
    fetchStockItems();
  }, []);

  const fetchMachines = async () => {
    try {
      const response = await axios.get(`${API}/machines`);
      setMachines(response.data);
    } catch (error) {
      toast.error("Erro ao carregar máquinas");
    } finally {
      setLoading(false);
    }
  };

  const fetchStockItems = async () => {
    try {
      const response = await axios.get(`${API}/stock/items`);
      setStockItems(response.data);
    } catch (error) {
      console.error("Erro ao carregar itens do estoque:", error);
    }
  };

  const addPart = (itemId) => {
    const item = stockItems.find(i => i.id === itemId);
    if (!item) return;
    
    // Verifica se já está selecionado
    if (selectedParts.find(p => p.item_id === itemId)) {
      toast.error("Esta peça já foi adicionada");
      return;
    }
    
    setSelectedParts([...selectedParts, {
      item_id: item.id,
      item_name: item.name,
      item_code: item.code,
      quantity: 1,
      max_quantity: item.quantity,
      unit: item.unit,
      unit_price: item.unit_price || 0
    }]);
  };

  const removePart = (itemId) => {
    setSelectedParts(selectedParts.filter(p => p.item_id !== itemId));
  };

  const updatePartQuantity = (itemId, quantity) => {
    setSelectedParts(selectedParts.map(p => 
      p.item_id === itemId 
        ? { ...p, quantity: Math.min(Math.max(1, quantity), p.max_quantity) }
        : p
    ));
  };

  // Atualiza o valor total automaticamente quando peças ou mão de obra mudam
  useEffect(() => {
    const total = calculateGrandTotal();
    if (total > 0) {
      setFormData(prev => ({ ...prev, part_value: total.toFixed(2) }));
    }
  }, [selectedParts, laborCost]);

  // Calcula o total das peças
  const calculatePartsTotal = () => {
    return selectedParts.reduce((total, part) => total + (part.unit_price * part.quantity), 0);
  };

  // Calcula o total geral (peças + mão de obra)
  const calculateGrandTotal = () => {
    const partsTotal = selectedParts.reduce((total, part) => total + (part.unit_price * part.quantity), 0);
    const labor = parseFloat(laborCost) || 0;
    return partsTotal + labor;
  };

  // Formata valor em BRL
  const formatCurrency = (value) => {
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value || 0);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.machine_id) {
      toast.error("Selecione uma máquina");
      return;
    }
    
    if (!formData.maintenance_type) {
      toast.error("Selecione o tipo de manutenção");
      return;
    }

    setSubmitting(true);

    try {
      // Calcular valor total (peças + mão de obra)
      const totalValue = calculateGrandTotal();
      
      const payload = {
        ...formData,
        part_value: totalValue > 0 ? totalValue : parseFloat(formData.part_value) || 0,
        labor_cost: parseFloat(laborCost) || 0,
        parts_cost: calculatePartsTotal(),
        replacement_date: format(date, "yyyy-MM-dd"),
        stock_parts: selectedParts.map(p => ({
          item_id: p.item_id,
          item_name: p.item_name,
          quantity: p.quantity,
          unit_price: p.unit_price,
          subtotal: p.unit_price * p.quantity
        }))
      };

      const response = await axios.post(`${API}/maintenances`, payload);
      
      // Dar baixa no estoque para cada peça selecionada
      let stockUpdateSuccess = true;
      for (const part of selectedParts) {
        try {
          await axios.post(`${API}/stock/movements`, {
            item_id: part.item_id,
            movement_type: "saida",
            quantity: part.quantity,
            reason: `Manutenção: ${formData.part_name}`,
            notes: `Usado na manutenção da máquina ${selectedMachine?.name || ''}`
          });
        } catch (err) {
          console.error(`Erro ao dar baixa no item ${part.item_name}:`, err);
          stockUpdateSuccess = false;
        }
      }
      
      if (selectedParts.length > 0 && stockUpdateSuccess) {
        toast.success("Manutenção registrada e estoque atualizado!");
      } else if (selectedParts.length > 0 && !stockUpdateSuccess) {
        toast.warning("Manutenção registrada, mas houve erro ao atualizar estoque");
      } else {
        toast.success("Manutenção registrada com sucesso!");
      }
      
      navigate(`/gerenciamento/maintenances/${response.data.id}`);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao registrar manutenção");
    } finally {
      setSubmitting(false);
    }
  };

  const selectedMachine = machines.find(m => m.id === formData.machine_id);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="spinner w-12 h-12"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in max-w-4xl" data-testid="new-maintenance-page">
      {/* Back button */}
      <Button
        variant="ghost"
        onClick={() => navigate("/gerenciamento/maintenances")}
        className="text-gray-600 hover:text-black"
        data-testid="back-btn"
      >
        <ArrowLeft size={18} className="mr-2" />
        Voltar para Manutenções
      </Button>

      {/* Page header */}
      <div>
        <h1 className="page-title font-heading">Nova Ficha de Manutenção</h1>
        <p className="text-gray-500 mt-1">Registre uma nova manutenção para sua máquina</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Form */}
        <Card className="lg:col-span-2">
          <CardHeader className="border-b border-gray-200">
            <CardTitle className="font-heading text-lg font-bold">
              Dados da Manutenção
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-6">
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Machine Selection */}
              <div className="space-y-2">
                <Label className="form-label">Máquina *</Label>
                <Select
                  value={formData.machine_id}
                  onValueChange={(value) => setFormData({...formData, machine_id: value})}
                >
                  <SelectTrigger className="form-input" data-testid="maintenance-machine-select">
                    <SelectValue placeholder="Selecione a máquina" />
                  </SelectTrigger>
                  <SelectContent>
                    {machines.map((machine) => (
                      <SelectItem key={machine.id} value={machine.id}>
                        <span className="font-mono">{machine.plate}</span> - {machine.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {machines.length === 0 && (
                  <p className="text-sm text-[#E31A1A]">
                    Nenhuma máquina cadastrada.{" "}
                    <button
                      type="button"
                      className="underline"
                      onClick={() => navigate("/gerenciamento/machines")}
                    >
                      Cadastrar máquina
                    </button>
                  </p>
                )}
              </div>

              {/* Part Name */}
              <div className="space-y-2">
                <Label className="form-label">Peça / Serviço *</Label>
                <Input
                  value={formData.part_name}
                  onChange={(e) => setFormData({...formData, part_name: e.target.value})}
                  placeholder="Ex: Filtro de óleo, Troca de pneu, Revisão completa..."
                  required
                  className="form-input"
                  data-testid="maintenance-part-input"
                />
              </div>

              {/* Stock Parts Selection */}
              <div className="space-y-3">
                <Label className="form-label flex items-center gap-2">
                  <Package size={16} className="text-blue-600" />
                  Peças do Estoque Utilizadas
                </Label>
                
                {/* Dropdown para selecionar peças */}
                <div className="flex gap-2">
                  <Select onValueChange={addPart}>
                    <SelectTrigger className="form-input" data-testid="stock-part-select">
                      <SelectValue placeholder="Selecionar peça do estoque..." />
                    </SelectTrigger>
                    <SelectContent>
                      {stockItems
                        .filter(item => item.quantity > 0)
                        .filter(item => !selectedParts.find(p => p.item_id === item.id))
                        .map((item) => (
                          <SelectItem key={item.id} value={item.id}>
                            <div className="flex items-center gap-2">
                              <span className="font-medium">{item.name}</span>
                              {item.code && <span className="text-xs text-gray-500">({item.code})</span>}
                              <span className="text-xs bg-gray-100 px-2 py-0.5 rounded">
                                {item.quantity} {item.unit} disponível
                              </span>
                            </div>
                          </SelectItem>
                        ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Lista de peças selecionadas */}
                {selectedParts.length > 0 && (
                  <div className="space-y-3 bg-blue-50 border border-blue-200 rounded-lg p-3">
                    <p className="text-xs font-medium text-blue-700 mb-2">Peças selecionadas (serão baixadas do estoque):</p>
                    {selectedParts.map((part) => (
                      <div key={part.item_id} className="flex items-center justify-between bg-white rounded-lg p-2 border border-blue-100">
                        <div className="flex items-center gap-2 flex-1">
                          <Package size={14} className="text-blue-600 flex-shrink-0" />
                          <div className="flex-1 min-w-0">
                            <span className="font-medium text-sm">{part.item_name}</span>
                            {part.item_code && <span className="text-xs text-gray-500 ml-1">({part.item_code})</span>}
                            <span className="text-xs text-green-600 ml-2 font-mono">{formatCurrency(part.unit_price)}/un</span>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <div className="flex items-center gap-1 bg-gray-100 rounded-lg">
                            <Button
                              type="button"
                              variant="ghost"
                              size="sm"
                              className="h-7 w-7 p-0"
                              onClick={() => updatePartQuantity(part.item_id, part.quantity - 1)}
                              disabled={part.quantity <= 1}
                            >
                              <Minus size={12} />
                            </Button>
                            <Input
                              type="number"
                              value={part.quantity}
                              onChange={(e) => updatePartQuantity(part.item_id, parseInt(e.target.value) || 1)}
                              className="w-12 h-7 text-center text-sm p-0 border-0 bg-transparent"
                              min={1}
                              max={part.max_quantity}
                            />
                            <Button
                              type="button"
                              variant="ghost"
                              size="sm"
                              className="h-7 w-7 p-0"
                              onClick={() => updatePartQuantity(part.item_id, part.quantity + 1)}
                              disabled={part.quantity >= part.max_quantity}
                            >
                              <Plus size={12} />
                            </Button>
                          </div>
                          <span className="text-xs text-gray-500 w-8">{part.unit}</span>
                          <span className="text-sm font-bold text-blue-700 w-24 text-right font-mono">
                            {formatCurrency(part.unit_price * part.quantity)}
                          </span>
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            className="h-7 w-7 p-0 text-red-500 hover:text-red-700 hover:bg-red-50"
                            onClick={() => removePart(part.item_id)}
                          >
                            <X size={14} />
                          </Button>
                        </div>
                      </div>
                    ))}
                    
                    {/* Subtotal de peças */}
                    <div className="flex justify-between items-center pt-2 border-t border-blue-200">
                      <span className="text-sm font-medium text-blue-700">Subtotal Peças:</span>
                      <span className="text-sm font-bold text-blue-800 font-mono">{formatCurrency(calculatePartsTotal())}</span>
                    </div>
                  </div>
                )}
                
                {stockItems.length === 0 && (
                  <p className="text-xs text-gray-500">
                    Nenhum item no estoque.{" "}
                    <button
                      type="button"
                      className="text-blue-600 underline"
                      onClick={() => navigate("/gerenciamento/stock")}
                    >
                      Ir para Estoque
                    </button>
                  </p>
                )}
              </div>

              {/* Mão de Obra */}
              <div className="space-y-2">
                <Label className="form-label">Valor Mão de Obra (opcional)</Label>
                <Input
                  type="number"
                  step="0.01"
                  min="0"
                  value={laborCost}
                  onChange={(e) => setLaborCost(e.target.value)}
                  placeholder="0,00"
                  className="form-input font-mono"
                  data-testid="maintenance-labor-input"
                />
                <p className="text-xs text-gray-500">Informe o valor do serviço/mão de obra, se houver</p>
              </div>

              {/* Total Geral */}
              {(selectedParts.length > 0 || laborCost) && (
                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <div className="space-y-2">
                    {selectedParts.length > 0 && (
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600">Peças ({selectedParts.length}):</span>
                        <span className="font-mono">{formatCurrency(calculatePartsTotal())}</span>
                      </div>
                    )}
                    {laborCost && parseFloat(laborCost) > 0 && (
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600">Mão de Obra:</span>
                        <span className="font-mono">{formatCurrency(parseFloat(laborCost))}</span>
                      </div>
                    )}
                    <div className="flex justify-between pt-2 border-t border-green-300">
                      <span className="font-bold text-green-800">TOTAL GERAL:</span>
                      <span className="font-bold text-green-800 text-lg font-mono">{formatCurrency(calculateGrandTotal())}</span>
                    </div>
                  </div>
                </div>
              )}

              {/* Date and Value */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label className="form-label">Data da Troca *</Label>
                  <Popover>
                    <PopoverTrigger asChild>
                      <Button
                        variant="outline"
                        className="w-full justify-start text-left font-normal form-input"
                        data-testid="maintenance-date-btn"
                      >
                        <CalendarIcon className="mr-2 h-4 w-4" />
                        {date ? format(date, "dd/MM/yyyy", { locale: ptBR }) : "Selecione"}
                      </Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-auto p-0" align="start">
                      <Calendar
                        mode="single"
                        selected={date}
                        onSelect={(d) => d && setDate(d)}
                        locale={ptBR}
                        initialFocus
                      />
                    </PopoverContent>
                  </Popover>
                </div>

                <div className="space-y-2">
                  <Label className="form-label">Valor (R$) *</Label>
                  <Input
                    type="number"
                    step="0.01"
                    min="0"
                    value={formData.part_value}
                    onChange={(e) => setFormData({...formData, part_value: e.target.value})}
                    placeholder="0,00"
                    required
                    className="form-input font-mono"
                    data-testid="maintenance-value-input"
                  />
                </div>
              </div>

              {/* Maintenance Type */}
              <div className="space-y-2">
                <Label className="form-label">Tipo de Manutenção *</Label>
                <div className="grid grid-cols-2 gap-4">
                  <button
                    type="button"
                    onClick={() => setFormData({...formData, maintenance_type: "preventiva"})}
                    className={`p-4 rounded-lg border-2 text-left transition-all ${
                      formData.maintenance_type === "preventiva"
                        ? "border-green-500 bg-green-50"
                        : "border-gray-200 hover:border-gray-300"
                    }`}
                    data-testid="maintenance-type-preventiva"
                  >
                    <div className="flex items-center gap-3">
                      <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                        formData.maintenance_type === "preventiva" ? "bg-green-100" : "bg-gray-100"
                      }`}>
                        <Shield className={`${
                          formData.maintenance_type === "preventiva" ? "text-green-600" : "text-gray-400"
                        }`} size={20} />
                      </div>
                      <div>
                        <p className="font-bold text-black">Preventiva</p>
                        <p className="text-xs text-gray-500">Manutenção programada</p>
                      </div>
                    </div>
                  </button>

                  <button
                    type="button"
                    onClick={() => setFormData({...formData, maintenance_type: "corretiva"})}
                    className={`p-4 rounded-lg border-2 text-left transition-all ${
                      formData.maintenance_type === "corretiva"
                        ? "border-[#E31A1A] bg-orange-50"
                        : "border-gray-200 hover:border-gray-300"
                    }`}
                    data-testid="maintenance-type-corretiva"
                  >
                    <div className="flex items-center gap-3">
                      <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                        formData.maintenance_type === "corretiva" ? "bg-orange-100" : "bg-gray-100"
                      }`}>
                        <AlertTriangle className={`${
                          formData.maintenance_type === "corretiva" ? "text-[#E31A1A]" : "text-gray-400"
                        }`} size={20} />
                      </div>
                      <div>
                        <p className="font-bold text-black">Corretiva</p>
                        <p className="text-xs text-gray-500">Reparo de problema</p>
                      </div>
                    </div>
                  </button>
                </div>
              </div>

              {/* Oil Change Checkbox */}
              <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg">
                <div className="flex items-center space-x-3">
                  <Checkbox
                    id="oil_change"
                    checked={formData.is_oil_change}
                    onCheckedChange={(checked) => setFormData({...formData, is_oil_change: checked})}
                    data-testid="oil-change-checkbox"
                  />
                  <div className="flex items-center gap-2">
                    <Droplet className="text-amber-600" size={20} />
                    <Label htmlFor="oil_change" className="text-sm font-bold text-amber-800 cursor-pointer">
                      Esta manutenção é uma TROCA DE ÓLEO
                    </Label>
                  </div>
                </div>
                <p className="text-xs text-amber-600 mt-2 ml-7">
                  Marque esta opção para reiniciar o contador de horas e tempo para esta máquina
                </p>
              </div>

              {/* Description */}
              <div className="space-y-2">
                <Label className="form-label">Descrição / Observações</Label>
                <Textarea
                  value={formData.description}
                  onChange={(e) => setFormData({...formData, description: e.target.value})}
                  placeholder="Detalhes adicionais sobre a manutenção..."
                  className="form-input min-h-[100px] resize-none"
                  data-testid="maintenance-description-input"
                />
              </div>

              {/* Submit */}
              <div className="flex gap-4 pt-4 border-t border-gray-200">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => navigate("/gerenciamento/maintenances")}
                  className="flex-1"
                >
                  Cancelar
                </Button>
                <Button
                  type="submit"
                  className="flex-1 bg-[#E31A1A] hover:bg-[#E31A1A]"
                  disabled={submitting || !formData.machine_id || machines.length === 0}
                  data-testid="maintenance-submit-btn"
                >
                  {submitting ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Salvando...
                    </>
                  ) : (
                    "Registrar Manutenção"
                  )}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>

        {/* Preview / Help */}
        <div className="space-y-6">
          {/* Selected Machine Preview */}
          {selectedMachine && (
            <Card className="bg-white">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-bold uppercase tracking-wider text-gray-500">
                  Máquina Selecionada
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 bg-gray-200 rounded-lg flex items-center justify-center">
                    <Truck className="text-gray-600" size={24} />
                  </div>
                  <div>
                    <p className="font-bold text-black">{selectedMachine.name}</p>
                    <p className="font-mono text-sm text-gray-500">{selectedMachine.plate}</p>
                  </div>
                </div>
                <div className="mt-4 pt-4 border-t border-gray-200 space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-500">Categoria:</span>
                    <span className="font-medium">{selectedMachine.category_name || "-"}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Marca:</span>
                    <span className="font-medium">{selectedMachine.brand || "-"}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Modelo:</span>
                    <span className="font-medium">{selectedMachine.model || "-"}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Help Card */}
          <Card className="bg-black text-white">
            <CardContent className="pt-6">
              <h3 className="font-bold text-lg mb-4">Dica</h3>
              <p className="text-sm text-gray-300 leading-relaxed">
                Após criar a ficha de manutenção, você poderá adicionar fotos 
                para documentar o serviço realizado. As fotos são importantes 
                para manter um histórico visual da manutenção.
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
