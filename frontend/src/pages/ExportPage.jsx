import { useState, useEffect } from "react";
import { useAuth, API } from "@/App";
import axios from "axios";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { 
  FileDown, 
  Loader2, 
  FileText,
  Truck,
  Wrench,
  Package,
  Building2,
  DollarSign,
  Users,
  ClipboardList,
  CreditCard,
  Download,
  ChevronDown,
  ChevronRight,
  Clock,
  TrendingDown,
  TrendingUp,
  FileSpreadsheet,
  FileCode,
  Filter,
  List,
  Receipt,
  FileCheck,
  CheckSquare,
  HardHat
} from "lucide-react";

const ICONS = {
  truck: Truck,
  wrench: Wrench,
  package: Package,
  building: Building2,
  dollar: DollarSign,
  users: Users,
  clipboard: ClipboardList,
  "trending-down": TrendingDown,
  "trending-up": TrendingUp,
  clock: Clock,
};

// Subcategorias que suportam expansão para itens individuais
const EXPANDABLE_SUBCATEGORIES = [
  'contas_pagar', 'contas_pagar_pendente', 'contas_pagar_quitadas', 'contas_pagar_vencidas',
  'contas_receber', 'contas_receber_pendente', 'contas_receber_recebidas', 'contas_receber_vencidas',
  'machines', 'maintenances', 'stock_items', 'obras', 'alugueis', 'imoveis', 'imoveis_ativo', 'imoveis_pendente',
  'plano_contas', 'centros_custo', 'cadastros', 'contas_bancarias', 'formas_pagamento',
  'fleets', 'extrato_bancario'
];

export default function ExportPage({ module = "gerenciamento" }) {
  const { token } = useAuth();
  const [categories, setCategories] = useState([]);
  const [expandedCategories, setExpandedCategories] = useState({});
  const [selectedItems, setSelectedItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(null);
  
  // Estado para subcategorias expandidas e seus itens
  const [expandedSubcategories, setExpandedSubcategories] = useState({});
  const [subcategoryItems, setSubcategoryItems] = useState({});
  const [loadingSubcategory, setLoadingSubcategory] = useState({});
  
  // Estado para seleção múltipla de itens individuais
  const [selectedIndividualItems, setSelectedIndividualItems] = useState({});  // {subcategoryId: [itemIds]}

  const accentColor = module === "gerenciamento" ? "#E31A1A" : "#D4A000";

  // Categorias que suportam recibo/duplicata
  const RECEIPT_CATEGORIES = ['contas_pagar', 'contas_pagar_pendente', 'contas_pagar_quitadas', 'contas_pagar_vencidas',
    'contas_receber', 'contas_receber_pendente', 'contas_receber_recebidas', 'contas_receber_vencidas',
    'alugueis', 'imoveis', 'imoveis_ativo', 'imoveis_pendente'];

  // State para extrato bancário
  const [selectedContaBancaria, setSelectedContaBancaria] = useState(null);
  const [contasBancarias, setContasBancarias] = useState([]);

  // State para modal de seleção de empresa (Recibo/Duplicata)
  const [empresaModal, setEmpresaModal] = useState({
    open: false,
    type: null, // 'recibo' ou 'duplicata'
    subcategoryId: null,
    itemId: null,
    itemName: null
  });

  useEffect(() => {
    fetchCategories();
    if (module === "administrativo") {
      fetchContasBancarias();
    }
  }, [module]);

  const fetchContasBancarias = async () => {
    try {
      const response = await axios.get(`${API}/admin/contas-bancarias?ativo=true`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setContasBancarias(response.data);
    } catch (error) {
      console.error("Erro ao carregar contas bancárias:", error);
    }
  };

  // Buscar itens individuais de uma subcategoria
  const fetchSubcategoryItems = async (subcategoryId) => {
    // Mapear subcategoria para coleção correta
    const collectionMap = {
      'extrato_bancario': 'contas_bancarias',
    };
    const collection = collectionMap[subcategoryId] || subcategoryId;
    
    setLoadingSubcategory(prev => ({...prev, [subcategoryId]: true}));
    try {
      const response = await axios.get(`${API}/export/items/${collection}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSubcategoryItems(prev => ({
        ...prev,
        [subcategoryId]: response.data
      }));
    } catch (error) {
      console.error("Erro ao carregar itens:", error);
      toast.error("Erro ao carregar itens da subcategoria");
    } finally {
      setLoadingSubcategory(prev => ({...prev, [subcategoryId]: false}));
    }
  };

  // Toggle expansão de subcategoria
  const toggleSubcategoryExpand = (subcategoryId) => {
    const isExpanded = expandedSubcategories[subcategoryId];
    
    // Se vai expandir e não tem itens carregados, buscar
    if (!isExpanded && !subcategoryItems[subcategoryId]) {
      fetchSubcategoryItems(subcategoryId);
    }
    
    setExpandedSubcategories(prev => ({
      ...prev,
      [subcategoryId]: !prev[subcategoryId]
    }));
  };

  // Exportar item individual
  const exportIndividualItem = async (subcategoryId, itemId, itemName) => {
    // Para extrato bancário, usar endpoint específico
    if (subcategoryId === 'extrato_bancario') {
      setExporting(`individual-${itemId}`);
      try {
        const response = await axios.get(`${API}/export/extrato-bancario/${itemId}`, {
          headers: { Authorization: `Bearer ${token}` },
          responseType: 'blob'
        });
        
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `CRA_Extrato_${itemName.replace(/\s/g, '_')}.pdf`);
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);
        
        toast.success(`Extrato de "${itemName}" exportado!`);
      } catch (error) {
        console.error("Erro ao exportar extrato:", error);
        toast.error("Erro ao exportar extrato");
      } finally {
        setExporting(null);
      }
      return;
    }
    
    // Para outros tipos, usar endpoint genérico de item individual
    setExporting(`individual-${itemId}`);
    try {
      const response = await axios.get(`${API}/export/individual/${subcategoryId}/${itemId}`, {
        headers: { Authorization: `Bearer ${token}` },
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      
      const contentDisposition = response.headers['content-disposition'];
      let filename = `CRA_${subcategoryId}_${itemId.slice(0, 8)}.pdf`;
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename=(.+)/);
        if (filenameMatch) {
          filename = filenameMatch[1].replace(/"/g, '');
        }
      }
      
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      toast.success(`"${itemName}" exportado com sucesso!`);
    } catch (error) {
      console.error("Erro ao exportar:", error);
      toast.error(error.response?.data?.detail || "Erro ao exportar item");
    } finally {
      setExporting(null);
    }
  };

  // Toggle seleção de item individual
  const toggleIndividualItem = (subcategoryId, itemId) => {
    setSelectedIndividualItems(prev => {
      const current = prev[subcategoryId] || [];
      const isSelected = current.includes(itemId);
      return {
        ...prev,
        [subcategoryId]: isSelected 
          ? current.filter(id => id !== itemId)
          : [...current, itemId]
      };
    });
  };

  // Selecionar/desselecionar todos os itens de uma subcategoria
  const toggleAllIndividualItems = (subcategoryId) => {
    const items = subcategoryItems[subcategoryId] || [];
    const selected = selectedIndividualItems[subcategoryId] || [];
    const allSelected = items.length > 0 && items.every(item => selected.includes(item.id));
    
    setSelectedIndividualItems(prev => ({
      ...prev,
      [subcategoryId]: allSelected ? [] : items.map(item => item.id)
    }));
  };

  // Exportar múltiplos itens selecionados
  const exportSelectedIndividualItems = async (subcategoryId) => {
    const selectedIds = selectedIndividualItems[subcategoryId] || [];
    if (selectedIds.length === 0) {
      toast.error("Selecione pelo menos um item");
      return;
    }
    
    setExporting(`multi-${subcategoryId}`);
    try {
      const response = await axios.post(`${API}/export/individual-multiple`, {
        category: subcategoryId,
        item_ids: selectedIds
      }, {
        headers: { Authorization: `Bearer ${token}` },
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `CRA_${subcategoryId}_${selectedIds.length}_itens.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      toast.success(`${selectedIds.length} itens exportados!`);
      // Limpar seleção após exportar
      setSelectedIndividualItems(prev => ({...prev, [subcategoryId]: []}));
    } catch (error) {
      console.error("Erro ao exportar:", error);
      toast.error(error.response?.data?.detail || "Erro ao exportar itens");
    } finally {
      setExporting(null);
    }
  };

  // Abrir modal de seleção de empresa para Recibo
  const openReciboModal = (subcategoryId, itemId, itemName) => {
    setEmpresaModal({
      open: true,
      type: 'recibo',
      subcategoryId,
      itemId,
      itemName
    });
  };

  // Abrir modal de seleção de empresa para Duplicata
  const openDuplicataModal = (subcategoryId, itemId, itemName) => {
    setEmpresaModal({
      open: true,
      type: 'duplicata',
      subcategoryId,
      itemId,
      itemName
    });
  };

  // Fechar modal
  const closeEmpresaModal = () => {
    setEmpresaModal({
      open: false,
      type: null,
      subcategoryId: null,
      itemId: null,
      itemName: null
    });
  };

  // Gerar documento com empresa selecionada
  const generateWithEmpresa = async (empresa) => {
    const { type, subcategoryId, itemId, itemName } = empresaModal;
    closeEmpresaModal();
    
    if (type === 'recibo') {
      await exportRecibo(subcategoryId, itemId, itemName, empresa);
    } else {
      await exportDuplicata(subcategoryId, itemId, itemName, empresa);
    }
  };

  // Exportar Recibo
  const exportRecibo = async (subcategoryId, itemId, itemName, empresa = 'locadora') => {
    setExporting(`recibo-${itemId}`);
    try {
      const response = await axios.get(`${API}/export/recibo/${subcategoryId}/${itemId}?empresa=${empresa}`, {
        headers: { Authorization: `Bearer ${token}` },
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `CRA_Recibo_${empresa === 'construtora' ? 'Construtora' : 'Locadora'}_${itemId.slice(0, 8)}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      toast.success(`Recibo de "${itemName}" gerado!`);
    } catch (error) {
      console.error("Erro ao gerar recibo:", error);
      toast.error(error.response?.data?.detail || "Erro ao gerar recibo");
    } finally {
      setExporting(null);
    }
  };

  // Exportar Duplicata/Recibo Fatura
  const exportDuplicata = async (subcategoryId, itemId, itemName, empresa = 'locadora') => {
    setExporting(`duplicata-${itemId}`);
    try {
      const response = await axios.get(`${API}/export/duplicata/${subcategoryId}/${itemId}?empresa=${empresa}`, {
        headers: { Authorization: `Bearer ${token}` },
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `CRA_Duplicata_${empresa === 'construtora' ? 'Construtora' : 'Locadora'}_${itemId.slice(0, 8)}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      toast.success(`Duplicata de "${itemName}" gerada!`);
    } catch (error) {
      console.error("Erro ao gerar duplicata:", error);
      toast.error(error.response?.data?.detail || "Erro ao gerar duplicata");
    } finally {
      setExporting(null);
    }
  };

  const fetchCategories = async () => {
    try {
      const response = await axios.get(`${API}/export/categories/${module}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setCategories(response.data);
      // Expandir todas as categorias por padrão
      const expanded = {};
      response.data.forEach(cat => {
        expanded[cat.id] = true;
      });
      setExpandedCategories(expanded);
    } catch (error) {
      console.error("Erro ao carregar categorias:", error);
      toast.error("Erro ao carregar categorias");
    } finally {
      setLoading(false);
    }
  };

  const toggleExpand = (categoryId) => {
    setExpandedCategories(prev => ({
      ...prev,
      [categoryId]: !prev[categoryId]
    }));
  };

  const toggleItem = (itemId) => {
    setSelectedItems(prev => 
      prev.includes(itemId) 
        ? prev.filter(id => id !== itemId)
        : [...prev, itemId]
    );
  };

  const toggleCategory = (category) => {
    const subcategoryIds = category.subcategories.map(s => s.id);
    const allSelected = subcategoryIds.every(id => selectedItems.includes(id));
    
    if (allSelected) {
      // Desmarcar todos
      setSelectedItems(prev => prev.filter(id => !subcategoryIds.includes(id)));
    } else {
      // Marcar todos
      setSelectedItems(prev => [...new Set([...prev, ...subcategoryIds])]);
    }
  };

  const isCategorySelected = (category) => {
    const subcategoryIds = category.subcategories.map(s => s.id);
    return subcategoryIds.every(id => selectedItems.includes(id));
  };

  const isCategoryPartiallySelected = (category) => {
    const subcategoryIds = category.subcategories.map(s => s.id);
    const selectedCount = subcategoryIds.filter(id => selectedItems.includes(id)).length;
    return selectedCount > 0 && selectedCount < subcategoryIds.length;
  };

  const selectAll = () => {
    const allIds = categories.flatMap(cat => cat.subcategories.map(s => s.id));
    if (selectedItems.length === allIds.length) {
      setSelectedItems([]);
    } else {
      setSelectedItems(allIds);
    }
  };

  // Exportar todos os itens selecionados em um único PDF
  const exportAllSelected = async () => {
    if (selectedItems.length === 0) {
      toast.error("Selecione pelo menos um item para exportar");
      return;
    }
    
    setExporting('all-combined');
    try {
      // Construir filtros específicos
      const filters = {};
      Object.keys(specificFilters).forEach(key => {
        const filter = specificFilters[key];
        if (filter?.selectedIds?.length > 0 && selectedItems.includes(key)) {
          filters[key] = { ids: filter.selectedIds };
        }
      });

      const response = await axios.post(`${API}/export/combined`, {
        categories: selectedItems,
        format: 'pdf',
        filters: Object.keys(filters).length > 0 ? filters : null
      }, {
        headers: { Authorization: `Bearer ${token}` },
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `CRA_Relatorio_Combinado_${new Date().toISOString().slice(0,10)}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      toast.success(`${selectedItems.length} categorias exportadas em um único PDF!`);
    } catch (error) {
      console.error("Erro ao exportar:", error);
      toast.error("Erro ao exportar relatório combinado");
    } finally {
      setExporting(null);
    }
  };

  const exportPDF = async (itemId) => {
    setExporting(`pdf-${itemId}`);
    try {
      const response = await axios.get(`${API}/export/pdf/${itemId}`, {
        headers: { Authorization: `Bearer ${token}` },
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      
      const contentDisposition = response.headers['content-disposition'];
      let filename = `CRA_Relatorio_${itemId}.pdf`;
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename=(.+)/);
        if (filenameMatch) {
          filename = filenameMatch[1].replace(/"/g, '');
        }
      }
      
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      toast.success("PDF exportado!");
    } catch (error) {
      console.error("Erro ao exportar:", error);
      toast.error("Erro ao exportar PDF");
    } finally {
      setExporting(null);
    }
  };

  const exportExcel = async (itemId) => {
    setExporting(`excel-${itemId}`);
    try {
      const response = await axios.get(`${API}/export/excel/${itemId}`, {
        headers: { Authorization: `Bearer ${token}` },
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      
      const contentDisposition = response.headers['content-disposition'];
      let filename = `CRA_${itemId}.xlsx`;
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename=(.+)/);
        if (filenameMatch) {
          filename = filenameMatch[1].replace(/"/g, '');
        }
      }
      
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      toast.success("Excel exportado!");
    } catch (error) {
      console.error("Erro ao exportar Excel:", error);
      toast.error(error.response?.data?.detail || "Erro ao exportar Excel");
    } finally {
      setExporting(null);
    }
  };

  const exportOFX = async (itemId) => {
    setExporting(`ofx-${itemId}`);
    try {
      const response = await axios.get(`${API}/export/ofx/${itemId}`, {
        headers: { Authorization: `Bearer ${token}` },
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      
      const contentDisposition = response.headers['content-disposition'];
      let filename = `CRA_${itemId}.ofx`;
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename=(.+)/);
        if (filenameMatch) {
          filename = filenameMatch[1].replace(/"/g, '');
        }
      }
      
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      toast.success("OFX exportado!");
    } catch (error) {
      console.error("Erro ao exportar OFX:", error);
      toast.error(error.response?.data?.detail || "OFX só disponível para contas financeiras");
    } finally {
      setExporting(null);
    }
  };

  // Função para exportar extrato bancário
  const exportExtratoBancario = async () => {
    if (!selectedContaBancaria) {
      toast.error("Selecione uma conta bancária");
      return;
    }
    
    setExporting('extrato_bancario');
    try {
      const response = await axios.get(`${API}/export/extrato-bancario/${selectedContaBancaria}`, {
        headers: { Authorization: `Bearer ${token}` },
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      
      const contentDisposition = response.headers['content-disposition'];
      let filename = `CRA_Extrato_Bancario.pdf`;
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename=(.+)/);
        if (filenameMatch) {
          filename = filenameMatch[1].replace(/"/g, '');
        }
      }
      
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      toast.success("Extrato bancário exportado!");
    } catch (error) {
      console.error("Erro ao exportar extrato:", error);
      toast.error(error.response?.data?.detail || "Erro ao exportar extrato bancário");
    } finally {
      setExporting(null);
    }
  };

  // Categorias que suportam Excel
  const excelCategories = ["machines", "maintenances", "stock_items", "obras", "contas_pagar", "contas_pagar_pendente", "contas_receber", "contas_receber_pendente", "cadastros", "cadastros_clientes", "cadastros_fornecedores", "produtos_admin", "alugueis", "medicoes"];
  
  // Categorias que suportam OFX
  const ofxCategories = ["contas_pagar", "contas_pagar_pendente", "contas_receber", "contas_receber_pendente"];

  // Substituído: agora exporta tudo em um único arquivo
  const exportSelected = exportAllSelected;

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="w-8 h-8 animate-spin" style={{ color: accentColor }} />
      </div>
    );
  }

  const totalSubcategories = categories.reduce((acc, cat) => acc + cat.subcategories.length, 0);

  return (
    <div className="p-4 md:p-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
        <div className="flex items-center gap-3">
          <div 
            className="w-12 h-12 rounded-lg flex items-center justify-center"
            style={{ backgroundColor: `${accentColor}20` }}
          >
            <FileDown size={24} style={{ color: accentColor }} />
          </div>
          <div>
            <h1 className="text-xl font-bold text-gray-900">Exportação de Relatórios</h1>
            <p className="text-sm text-gray-500">{totalSubcategories} opções disponíveis</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            onClick={selectAll}
            className="border-gray-300"
          >
            {selectedItems.length === totalSubcategories ? "Desmarcar Todos" : "Selecionar Todos"}
          </Button>
          <Button
            onClick={exportSelected}
            disabled={selectedItems.length === 0 || exporting}
            style={{ backgroundColor: accentColor }}
            className="text-white"
          >
            {exporting ? (
              <Loader2 size={18} className="animate-spin mr-2" />
            ) : (
              <Download size={18} className="mr-2" />
            )}
            Exportar ({selectedItems.length})
          </Button>
        </div>
      </div>

      {/* Categories */}
      <div className="space-y-3">
        {categories.map((category) => {
          const Icon = ICONS[category.icon] || FileText;
          const isExpanded = expandedCategories[category.id];
          const isSelected = isCategorySelected(category);
          const isPartial = isCategoryPartiallySelected(category);

          return (
            <Card key={category.id} className="overflow-hidden border-gray-200">
              {/* Category Header */}
              <div 
                className={`flex items-center gap-3 p-4 cursor-pointer transition-colors ${
                  isSelected ? 'bg-gray-100' : 'hover:bg-gray-50'
                }`}
                style={{ borderLeft: `4px solid ${isSelected || isPartial ? accentColor : 'transparent'}` }}
              >
                <Checkbox 
                  checked={isSelected}
                  ref={(el) => {
                    if (el && isPartial && !isSelected) {
                      el.dataset.state = "indeterminate";
                    }
                  }}
                  onCheckedChange={() => toggleCategory(category)}
                  className="shrink-0"
                  style={{ 
                    borderColor: isSelected || isPartial ? accentColor : undefined,
                    backgroundColor: isSelected ? accentColor : undefined
                  }}
                />
                <div 
                  className="w-10 h-10 rounded-lg flex items-center justify-center shrink-0"
                  style={{ 
                    backgroundColor: `${accentColor}15`,
                    color: accentColor
                  }}
                >
                  <Icon size={20} />
                </div>
                <div className="flex-1 min-w-0" onClick={() => toggleExpand(category.id)}>
                  <h3 className="font-semibold text-gray-900">{category.label}</h3>
                  <p className="text-sm text-gray-500">
                    {category.subcategories.filter(s => selectedItems.includes(s.id)).length} de {category.subcategories.length} selecionados
                  </p>
                </div>
                <Button 
                  variant="ghost" 
                  size="sm" 
                  className="shrink-0"
                  onClick={() => toggleExpand(category.id)}
                >
                  {isExpanded ? <ChevronDown size={20} /> : <ChevronRight size={20} />}
                </Button>
              </div>

              {/* Subcategories */}
              {isExpanded && (
                <div className="border-t border-gray-100 bg-gray-50">
                  {category.subcategories.map((sub, index) => {
                    const isSubSelected = selectedItems.includes(sub.id);
                    const isSubExpanded = expandedSubcategories[sub.id];
                    const items = subcategoryItems[sub.id] || [];
                    const isLoadingItems = loadingSubcategory[sub.id];
                    const canExpand = EXPANDABLE_SUBCATEGORIES.includes(sub.id);

                    return (
                      <div key={sub.id}>
                        <div 
                          className={`flex items-center gap-3 px-4 py-3 pl-16 ${
                            index !== category.subcategories.length - 1 && !isSubExpanded ? 'border-b border-gray-100' : ''
                          } ${isSubSelected ? 'bg-white' : 'hover:bg-white'}`}
                        >
                          <Checkbox 
                            checked={isSubSelected}
                            onCheckedChange={() => toggleItem(sub.id)}
                            className="shrink-0"
                            style={{ 
                              borderColor: isSubSelected ? accentColor : undefined,
                              backgroundColor: isSubSelected ? accentColor : undefined
                            }}
                          />
                          <div className="flex-1 min-w-0">
                            <p className={`text-sm ${isSubSelected ? 'font-medium text-gray-900' : 'text-gray-700'}`}>
                              {sub.label}
                            </p>
                            <p className="text-xs text-gray-500">{sub.description}</p>
                          </div>
                          
                          {/* Botão para expandir e ver itens individuais */}
                          {canExpand && (
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => toggleSubcategoryExpand(sub.id)}
                              className="text-purple-500 hover:text-purple-700 hover:bg-purple-50"
                              title="Ver itens individuais"
                              data-testid={`expand-${sub.id}`}
                            >
                              {isLoadingItems ? (
                                <Loader2 size={14} className="animate-spin" />
                              ) : isSubExpanded ? (
                                <ChevronDown size={14} />
                              ) : (
                                <List size={14} />
                              )}
                            </Button>
                          )}

                          <div className="flex items-center gap-1 shrink-0">
                            {/* PDF */}
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => exportPDF(sub.id)}
                              disabled={exporting === `pdf-${sub.id}`}
                              className="text-red-500 hover:text-red-700 hover:bg-red-50"
                              title="Exportar PDF (todos)"
                            >
                              {exporting === `pdf-${sub.id}` ? (
                                <Loader2 size={14} className="animate-spin" />
                              ) : (
                                <FileText size={14} />
                              )}
                            </Button>
                            {/* Excel */}
                            {excelCategories.includes(sub.id) && (
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => exportExcel(sub.id)}
                                disabled={exporting === `excel-${sub.id}`}
                                className="text-green-600 hover:text-green-700 hover:bg-green-50"
                                title="Exportar Excel (todos)"
                              >
                                {exporting === `excel-${sub.id}` ? (
                                  <Loader2 size={14} className="animate-spin" />
                                ) : (
                                  <FileSpreadsheet size={14} />
                                )}
                              </Button>
                            )}
                            {/* OFX */}
                            {ofxCategories.includes(sub.id) && (
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => exportOFX(sub.id)}
                              disabled={exporting === `ofx-${sub.id}`}
                              className="text-blue-600 hover:text-blue-700 hover:bg-blue-50"
                              title="Exportar OFX (Bancos)"
                            >
                              {exporting === `ofx-${sub.id}` ? (
                                <Loader2 size={14} className="animate-spin" />
                              ) : (
                                <FileCode size={14} />
                              )}
                            </Button>
                          )}
                        </div>
                      </div>
                        
                        {/* Lista de itens individuais expandida */}
                        {isSubExpanded && (
                          <div className="bg-purple-50 border-t border-purple-100 px-4 py-3 pl-20">
                            {/* Header com ações em lote */}
                            <div className="flex items-center justify-between mb-3">
                              <div className="flex items-center gap-2">
                                <Checkbox 
                                  checked={items.length > 0 && (selectedIndividualItems[sub.id] || []).length === items.length}
                                  onCheckedChange={() => toggleAllIndividualItems(sub.id)}
                                  className="shrink-0"
                                />
                                <p className="text-xs text-purple-700 font-medium">
                                  Itens individuais ({(selectedIndividualItems[sub.id] || []).length} selecionados)
                                </p>
                              </div>
                              {(selectedIndividualItems[sub.id] || []).length > 0 && (
                                <Button
                                  size="sm"
                                  onClick={() => exportSelectedIndividualItems(sub.id)}
                                  disabled={exporting === `multi-${sub.id}`}
                                  className="bg-purple-600 hover:bg-purple-700 text-white"
                                >
                                  {exporting === `multi-${sub.id}` ? (
                                    <Loader2 size={14} className="animate-spin mr-1" />
                                  ) : (
                                    <Download size={14} className="mr-1" />
                                  )}
                                  Exportar Selecionados
                                </Button>
                              )}
                            </div>
                            
                            {isLoadingItems ? (
                              <div className="flex items-center gap-2 text-purple-600">
                                <Loader2 size={14} className="animate-spin" />
                                <span className="text-sm">Carregando itens...</span>
                              </div>
                            ) : items.length > 0 ? (
                              <div className="space-y-2 max-h-80 overflow-y-auto">
                                {items.map(item => {
                                  const isItemSelected = (selectedIndividualItems[sub.id] || []).includes(item.id);
                                  const supportsReceipt = RECEIPT_CATEGORIES.includes(sub.id);
                                  
                                  return (
                                    <div
                                      key={item.id}
                                      className={`flex items-center gap-3 bg-white rounded-lg px-3 py-2 border transition-colors ${
                                        isItemSelected ? 'border-purple-500 bg-purple-50' : 'border-purple-200 hover:border-purple-400'
                                      }`}
                                    >
                                      <Checkbox 
                                        checked={isItemSelected}
                                        onCheckedChange={() => toggleIndividualItem(sub.id, item.id)}
                                        className="shrink-0"
                                      />
                                      <div className="flex-1 min-w-0">
                                        <p className="text-sm font-medium text-gray-900" title={item.name}>
                                          {item.name || "Sem descrição"}
                                        </p>
                                        {/* Informações extras dependendo do tipo */}
                                        <div className="flex flex-wrap gap-x-3 gap-y-1 text-xs text-gray-500">
                                          {item.valor !== undefined && (
                                            <span className="font-medium text-green-600">R$ {Number(item.valor || 0).toLocaleString('pt-BR', {minimumFractionDigits: 2})}</span>
                                          )}
                                          {item.data_vencimento && (
                                            <span>Venc: {item.data_vencimento}</span>
                                          )}
                                          {item.fornecedor_nome && (
                                            <span title={item.fornecedor_nome}>{item.fornecedor_nome}</span>
                                          )}
                                          {item.cliente_nome && (
                                            <span title={item.cliente_nome}>{item.cliente_nome}</span>
                                          )}
                                          {item.model && (
                                            <span>{item.model}</span>
                                          )}
                                          {item.plate && (
                                            <span>{item.plate}</span>
                                          )}
                                          {item.banco && (
                                            <span>{item.banco}</span>
                                          )}
                                        </div>
                                      </div>
                                      <div className="flex items-center gap-1 shrink-0">
                                        {/* Botão Recibo - apenas para categorias que suportam */}
                                        {supportsReceipt && (
                                          <Button
                                            size="sm"
                                            variant="outline"
                                            onClick={() => openReciboModal(sub.id, item.id, item.name)}
                                            disabled={exporting === `recibo-${item.id}`}
                                            className="text-green-600 border-green-300 hover:bg-green-50"
                                            title="Gerar Recibo"
                                          >
                                            {exporting === `recibo-${item.id}` ? (
                                              <Loader2 size={14} className="animate-spin" />
                                            ) : (
                                              <Receipt size={14} />
                                            )}
                                          </Button>
                                        )}
                                        {/* Botão Duplicata/Recibo Fatura - apenas para categorias que suportam */}
                                        {supportsReceipt && (
                                          <Button
                                            size="sm"
                                            variant="outline"
                                            onClick={() => openDuplicataModal(sub.id, item.id, item.name)}
                                            disabled={exporting === `duplicata-${item.id}`}
                                            className="text-amber-600 border-amber-300 hover:bg-amber-50"
                                            title="Gerar Duplicata/Recibo Fatura"
                                          >
                                            {exporting === `duplicata-${item.id}` ? (
                                              <Loader2 size={14} className="animate-spin" />
                                            ) : (
                                              <FileCheck size={14} />
                                            )}
                                          </Button>
                                        )}
                                        {/* Botão PDF */}
                                        <Button
                                          size="sm"
                                          variant="outline"
                                          onClick={() => exportIndividualItem(sub.id, item.id, item.name)}
                                          disabled={exporting === `individual-${item.id}`}
                                          className="text-purple-600 border-purple-300 hover:bg-purple-100"
                                          data-testid={`export-individual-${item.id}`}
                                          title="Exportar PDF"
                                        >
                                          {exporting === `individual-${item.id}` ? (
                                            <Loader2 size={14} className="animate-spin" />
                                          ) : (
                                            <FileText size={14} />
                                          )}
                                        </Button>
                                      </div>
                                    </div>
                                  );
                                })}
                              </div>
                            ) : (
                              <p className="text-sm text-gray-500">Nenhum item cadastrado nesta categoria</p>
                            )}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </Card>
          );
        })}
      </div>

      {/* Info */}
      <Card className="mt-6 bg-gray-50 border-gray-200">
        <CardContent className="p-4">
          <h3 className="font-semibold text-gray-900 mb-2 flex items-center gap-2">
            <FileText size={16} style={{ color: accentColor }} />
            Sobre a Exportação
          </h3>
          <p className="text-sm text-gray-600 mb-3">
            Selecione as categorias ou subcategorias desejadas e clique em "Exportar". 
            Os relatórios são gerados com a identidade visual do Sistema de Gerenciamento.
          </p>
          <div className="flex flex-wrap gap-4 text-xs">
            <div className="flex items-center gap-1 text-red-600">
              <FileText size={14} /> PDF - Relatório formatado
            </div>
            <div className="flex items-center gap-1 text-green-600">
              <FileSpreadsheet size={14} /> Excel - Planilha editável
            </div>
            <div className="flex items-center gap-1 text-blue-600">
              <FileCode size={14} /> OFX - Importar em bancos/sistemas financeiros
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Modal de Seleção de Empresa para Recibo/Duplicata */}
      <Dialog open={empresaModal.open} onOpenChange={(open) => !open && closeEmpresaModal()}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              {empresaModal.type === 'recibo' ? <Receipt className="text-green-500" /> : <FileCheck className="text-amber-500" />}
              Selecionar Empresa
            </DialogTitle>
          </DialogHeader>
          <div className="py-4">
            <p className="text-sm text-gray-600 mb-4">
              Selecione a empresa para gerar o {empresaModal.type === 'recibo' ? 'recibo' : 'duplicata/recibo fatura'}:
            </p>
            <div className="space-y-3">
              {/* CRA Construtora */}
              <Button
                variant="outline"
                className="w-full h-auto py-4 flex flex-col items-start gap-1 hover:bg-amber-50 hover:border-amber-300"
                onClick={() => generateWithEmpresa('construtora')}
                disabled={exporting}
              >
                <div className="flex items-center gap-2 font-semibold text-amber-700">
                  <HardHat size={20} />
                  CRA CONSTRUTORA
                </div>
                <div className="text-xs text-gray-500 text-left">
                  CNPJ: 04.887.879/0001-96<br/>
                  Tel: (63) 98407-1513
                </div>
              </Button>
              
              {/* CRA Locadora */}
              <Button
                variant="outline"
                className="w-full h-auto py-4 flex flex-col items-start gap-1 hover:bg-blue-50 hover:border-blue-300"
                onClick={() => generateWithEmpresa('locadora')}
                disabled={exporting}
              >
                <div className="flex items-center gap-2 font-semibold text-blue-700">
                  <Truck size={20} />
                  CRA LOCADORA
                </div>
                <div className="text-xs text-gray-500 text-left">
                  CNPJ: 39.543.761/0001-25<br/>
                  Tel: (63) 98407-1513
                </div>
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
