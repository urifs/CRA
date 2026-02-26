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
  Filter
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

export default function ExportPage({ module = "gerenciamento" }) {
  const { token } = useAuth();
  const [categories, setCategories] = useState([]);
  const [expandedCategories, setExpandedCategories] = useState({});
  const [selectedItems, setSelectedItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(null);
  const [specificFilters, setSpecificFilters] = useState({}); // {plano_contas: {expanded: true, selectedIds: [], items: []}}
  const [loadingFilters, setLoadingFilters] = useState({});

  const accentColor = module === "gerenciamento" ? "#E31A1A" : "#D4A000";

  // Subcategorias que suportam seleção específica
  const filterableCategories = {
    'plano_contas': 'plano_contas',
    'centros_custo': 'centros_custo',
    'fleets': 'fleets',
    'cadastros': 'cadastros',
    'formas_pagamento': 'formas_pagamento',
    'contas_bancarias': 'contas_bancarias',
    'extrato_bancario': 'contas_bancarias'  // Para extrato, busca contas bancárias
  };

  // State para extrato bancário
  const [selectedContaBancaria, setSelectedContaBancaria] = useState(null);
  const [contasBancarias, setContasBancarias] = useState([]);

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

  const fetchFilterItems = async (subcategoryId) => {
    const collection = filterableCategories[subcategoryId];
    if (!collection) return;
    
    setLoadingFilters(prev => ({...prev, [subcategoryId]: true}));
    try {
      const response = await axios.get(`${API}/export/items/${collection}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSpecificFilters(prev => ({
        ...prev,
        [subcategoryId]: {
          expanded: prev[subcategoryId]?.expanded || false,
          selectedIds: prev[subcategoryId]?.selectedIds || [],
          items: response.data
        }
      }));
    } catch (error) {
      console.error("Erro ao carregar itens:", error);
    } finally {
      setLoadingFilters(prev => ({...prev, [subcategoryId]: false}));
    }
  };

  const toggleFilterExpand = (subcategoryId) => {
    const current = specificFilters[subcategoryId];
    if (!current?.items?.length) {
      fetchFilterItems(subcategoryId);
    }
    setSpecificFilters(prev => ({
      ...prev,
      [subcategoryId]: {
        ...prev[subcategoryId],
        expanded: !prev[subcategoryId]?.expanded
      }
    }));
  };

  const toggleFilterItem = (subcategoryId, itemId) => {
    setSpecificFilters(prev => {
      const current = prev[subcategoryId] || { expanded: false, selectedIds: [], items: [] };
      const isSelected = current.selectedIds.includes(itemId);
      return {
        ...prev,
        [subcategoryId]: {
          ...current,
          selectedIds: isSelected 
            ? current.selectedIds.filter(id => id !== itemId)
            : [...current.selectedIds, itemId]
        }
      };
    });
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
                    const isSubExporting = exporting === sub.id;
                    const hasFilter = filterableCategories[sub.id];
                    const filterData = specificFilters[sub.id];

                    return (
                      <div key={sub.id}>
                        <div 
                          className={`flex items-center gap-3 px-4 py-3 pl-16 ${
                            index !== category.subcategories.length - 1 && !filterData?.expanded ? 'border-b border-gray-100' : ''
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
                            {filterData?.selectedIds?.length > 0 && (
                              <p className="text-xs text-blue-600 mt-1">
                                {filterData.selectedIds.length} item(s) específico(s) selecionado(s)
                              </p>
                            )}
                          </div>
                          
                          {/* Botão de filtro para subcategorias que suportam */}
                          {hasFilter && isSubSelected && (
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => toggleFilterExpand(sub.id)}
                              className="text-blue-500 hover:text-blue-700 hover:bg-blue-50"
                              title="Filtrar itens específicos"
                            >
                              {loadingFilters[sub.id] ? (
                                <Loader2 size={14} className="animate-spin" />
                              ) : (
                                <Filter size={14} />
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
                              title="Exportar PDF"
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
                                title="Exportar Excel"
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
                        
                        {/* Área de filtros expandíveis */}
                        {hasFilter && filterData?.expanded && (
                          <div className="bg-blue-50 border-t border-blue-100 px-4 py-3 pl-20">
                            <p className="text-xs text-blue-700 font-medium mb-2">
                              Selecione itens específicos para exportar (deixe vazio para exportar todos):
                            </p>
                            {loadingFilters[sub.id] ? (
                              <div className="flex items-center gap-2 text-blue-600">
                                <Loader2 size={14} className="animate-spin" />
                                <span className="text-sm">Carregando itens...</span>
                              </div>
                            ) : filterData?.items?.length > 0 ? (
                              <div className="flex flex-wrap gap-2">
                                {filterData.items.map(item => (
                                  <label
                                    key={item.id}
                                    className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-sm cursor-pointer transition-colors ${
                                      filterData.selectedIds.includes(item.id)
                                        ? 'bg-blue-600 text-white'
                                        : 'bg-white border border-blue-200 text-blue-700 hover:bg-blue-100'
                                    }`}
                                  >
                                    <input
                                      type="checkbox"
                                      className="sr-only"
                                      checked={filterData.selectedIds.includes(item.id)}
                                      onChange={() => toggleFilterItem(sub.id, item.id)}
                                    />
                                    {item.name}
                                  </label>
                                ))}
                              </div>
                            ) : (
                              <p className="text-sm text-gray-500">Nenhum item cadastrado</p>
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
    </div>
  );
}
