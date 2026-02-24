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
  Droplet
} from "lucide-react";
import { format } from "date-fns";
import { ptBR } from "date-fns/locale";
import { Checkbox } from "@/components/ui/checkbox";

export default function NewMaintenancePage() {
  const [searchParams] = useSearchParams();
  const preselectedMachine = searchParams.get("machine");
  
  const [machines, setMachines] = useState([]);
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
      const payload = {
        ...formData,
        part_value: parseFloat(formData.part_value),
        replacement_date: format(date, "yyyy-MM-dd")
      };

      const response = await axios.post(`${API}/maintenances`, payload);
      toast.success("Manutenção registrada com sucesso!");
      navigate(`/maintenances/${response.data.id}`);
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
        onClick={() => navigate("/maintenances")}
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
                      onClick={() => navigate("/machines")}
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
                  onClick={() => navigate("/maintenances")}
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
