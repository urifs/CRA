import { useState, useEffect } from "react";
import { useAuth, API } from "@/App";
import axios from "axios";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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
  HardHat,
  Landmark,
  Search,
  X as XIcon
} from "lucide-react";
import { Input } from "@/components/ui/input";

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
  'contas_pagar', 'contas_pagar_pendente', 'contas_pagar_quitada', 'contas_pagar_quitadas', 'contas_pagar_vencidas',
  'contas_receber', 'contas_receber_pendente', 'contas_receber_quitada', 'contas_receber_recebidas', 'contas_receber_vencidas',
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
  const [itemSearch, setItemSearch] = useState({});
  
  // Estado para seleção múltipla de itens individuais
  const [selectedIndividualItems, setSelectedIndividualItems] = useState({});  // {subcategoryId: [itemIds]}

  // Contagem de itens por subcategoria (respeitando filtro global)
  const [subcategoryCounts, setSubcategoryCounts] = useState({}); // {sub_id: number}
  const [loadingCounts, setLoadingCounts] = useState(false);

  const accentColor = module === "gerenciamento" ? "#E31A1A" : "#D4A000";

  // Categorias que suportam recibo/duplicata
  const RECEIPT_CATEGORIES = ['contas_pagar', 'contas_pagar_pendente', 'contas_pagar_quitada', 'contas_pagar_quitadas', 'contas_pagar_vencidas',
    'contas_receber', 'contas_receber_pendente', 'contas_receber_quitada', 'contas_receber_recebidas', 'contas_receber_vencidas',
    'alugueis', 'imoveis', 'imoveis_ativo', 'imoveis_pendente'];

  // State para extrato bancário
  const [selectedContaBancaria, setSelectedContaBancaria] = useState(null);
  const [contasBancarias, setContasBancarias] = useState([]);

  // State para relatório por conta bancária
  const [relContaBancaria, setRelContaBancaria] = useState("");
  const [relTipoConta, setRelTipoConta] = useState("pagar");
  const [relStatusConta, setRelStatusConta] = useState("todas");
  const [exportingRelatorio, setExportingRelatorio] = useState(false);

  // State para filtro de Centro de Custo
  const [centrosCusto, setCentrosCusto] = useState([]);
  const [selectedCentroCusto, setSelectedCentroCusto] = useState(null); // null=não selecionado, "todos"=todos, ou nome string
  const [ccSelectorOpen, setCcSelectorOpen] = useState(false);

  // State para modal de seleção de empresa (Recibo/Duplicata)
  const [empresaModal, setEmpresaModal] = useState({
    open: false,
    type: null, // 'recibo' ou 'duplicata'
    subcategoryId: null,
    itemId: null,
    itemName: null
  });

  // State para extrato plano de contas (export por período)
  const [planosContas, setPlanosContas] = useState([]);
  const [extratoPlanoConta, setExtratoPlanoConta] = useState("todos");
  const [extratoDataInicio, setExtratoDataInicio] = useState("");
  const [extratoDataFim, setExtratoDataFim] = useState("");
  const [extratoTipo, setExtratoTipo] = useState("ambos");
  const [extratoStatus, setExtratoStatus] = useState("todas");
  const [exportingExtratoPC, setExportingExtratoPC] = useState(false);

  // Filtro GLOBAL de período (aplica a TODAS as exportações)
  const [globalDataInicio, setGlobalDataInicio] = useState("");
  const [globalDataFim, setGlobalDataFim] = useState("");
  // Filtro GLOBAL de forma de pagamento (aplica a contas_pagar/receber em qualquer export)
  const [globalFormaPagamento, setGlobalFormaPagamento] = useState("todas");
  const [formasPagamento, setFormasPagamento] = useState([]);

  // Helper: monta query string com período (e centro de custo opcional)
  const buildPeriodQuery = (extra = {}) => {
    const params = new URLSearchParams();
    if (globalDataInicio) params.append("data_inicio", globalDataInicio);
    if (globalDataFim) params.append("data_fim", globalDataFim);
    if (globalFormaPagamento && globalFormaPagamento !== "todas") {
      params.append("forma_pagamento", globalFormaPagamento);
    }
    Object.entries(extra).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== "") params.append(k, v);
    });
    const s = params.toString();
    return s ? `?${s}` : "";
  };

  useEffect(() => {
    fetchCategories();
    if (module === "administrativo") {
      fetchContasBancarias();
      fetchCentrosCusto();
      fetchPlanosContas();
    }
    fetchFormasPagamento();
  }, [module]);

  // Busca contagem de itens por subcategoria (respeitando filtro global de período)
  const fetchSubcategoryCounts = async () => {
    if (!categories || categories.length === 0) return;
    // Coleta todos os sub.id que são "expandable" (têm itens contáveis)
    const ids = new Set();
    categories.forEach((cat) => {
      (cat.subcategories || []).forEach((sub) => {
        if (EXPANDABLE_SUBCATEGORIES.includes(sub.id)) ids.add(sub.id);
      });
    });
    if (ids.size === 0) return;
    setLoadingCounts(true);
    try {
      const params = new URLSearchParams();
      params.append("collections", Array.from(ids).join(","));
      if (globalDataInicio) params.append("data_inicio", globalDataInicio);
      if (globalDataFim) params.append("data_fim", globalDataFim);
      if (selectedCentroCusto && selectedCentroCusto !== "todos") {
        params.append("centro_custo", selectedCentroCusto);
      }
      const r = await axios.get(`${API}/export/items-count?${params.toString()}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setSubcategoryCounts(r.data || {});
    } catch (e) {
      // silencioso — contador é informativo, não bloqueia exportação
      console.warn("Falha ao buscar contagens:", e?.message);
    } finally {
      setLoadingCounts(false);
    }
  };

  // Quando o período global ou centro de custo mudam, invalida cache de itens
  // já carregados e re-busca para subcategorias atualmente expandidas.
  useEffect(() => {
    const expandedIds = Object.keys(expandedSubcategories).filter(
      (id) => expandedSubcategories[id]
    );
    if (expandedIds.length === 0) return;
    // Limpa seleções para evitar exportar item filtrado que não está mais visível
    setSelectedItems({});
    expandedIds.forEach((id) => {
      fetchSubcategoryItems(id);
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [globalDataInicio, globalDataFim, selectedCentroCusto]);

  // Atualiza contagens de itens por subcategoria sempre que categorias carregam
  // ou o filtro global de período / centro de custo é alterado.
  useEffect(() => {
    fetchSubcategoryCounts();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [categories, globalDataInicio, globalDataFim, selectedCentroCusto]);

  const fetchFormasPagamento = async () => {
    try {
      const response = await axios.get(`${API}/formas-pagamento`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setFormasPagamento(response.data || []);
    } catch (error) {
      console.error("Erro ao carregar formas de pagamento:", error);
    }
  };

  const fetchPlanosContas = async () => {
    try {
      const response = await axios.get(`${API}/admin/plano-contas`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setPlanosContas(response.data || []);
    } catch (error) {
      console.error("Erro ao carregar planos de contas:", error);
    }
  };

  const exportExtratoPlanoContas = async () => {
    setExportingExtratoPC(true);
    try {
      const params = new URLSearchParams();
      if (extratoPlanoConta && extratoPlanoConta !== "todos") {
        params.append("plano_conta_id", extratoPlanoConta);
      }
      if (extratoDataInicio) params.append("data_inicio", extratoDataInicio);
      if (extratoDataFim) params.append("data_fim", extratoDataFim);
      params.append("tipo", extratoTipo);
      params.append("status", extratoStatus);
      params.append("incluir_detalhes", "true");

      const response = await axios.get(
        `${API}/export/extrato-plano-contas?${params.toString()}`,
        {
          headers: { Authorization: `Bearer ${token}` },
          responseType: 'blob'
        }
      );

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `CRA_Extrato_PlanoContas_${new Date().toISOString().split('T')[0]}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      toast.success("Extrato do plano de contas exportado!");
    } catch (error) {
      console.error("Erro ao exportar extrato:", error);
      toast.error("Erro ao exportar extrato do plano de contas");
    } finally {
      setExportingExtratoPC(false);
    }
  };

  const fetchCentrosCusto = async () => {
    try {
      const response = await axios.get(`${API}/admin/centros-custo`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setCentrosCusto(response.data || []);
    } catch (error) {
      console.error("Erro ao carregar centros de custo:", error);
    }
  };

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

  // Exportar relatório por conta bancária
  const exportRelatorioPorContaBancaria = async () => {
    if (!relContaBancaria) {
      toast.error("Selecione uma conta bancária");
      return;
    }
    
    setExportingRelatorio(true);
    try {
      const qs = buildPeriodQuery({
        conta_bancaria_id: relContaBancaria,
        tipo: relTipoConta,
        status: relStatusConta,
      });
      const response = await axios.get(
        `${API}/export/relatorio-conta-bancaria${qs}`,
        {
          headers: { Authorization: `Bearer ${token}` },
          responseType: 'blob'
        }
      );
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      const tipoLabel = relTipoConta === "pagar" ? "Pagar" : relTipoConta === "receber" ? "Receber" : "Geral";
      link.setAttribute('download', `CRA_Relatorio_${tipoLabel}_${new Date().toISOString().split('T')[0]}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      toast.success("Relatório exportado com sucesso!");
    } catch (error) {
      console.error("Erro ao exportar relatório:", error);
      toast.error("Erro ao exportar relatório");
    } finally {
      setExportingRelatorio(false);
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
      const params = new URLSearchParams();
      if (globalDataInicio) params.append("data_inicio", globalDataInicio);
      if (globalDataFim) params.append("data_fim", globalDataFim);
      if (selectedCentroCusto && selectedCentroCusto !== "todos") {
        params.append("centro_custo", selectedCentroCusto);
      }
      const qs = params.toString();
      const url = `${API}/export/items/${collection}${qs ? `?${qs}` : ""}`;
      const response = await axios.get(url, {
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
        const response = await axios.get(`${API}/export/extrato-bancario/${itemId}${buildPeriodQuery()}`, {
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

  // Selecionar/desselecionar todos os itens VISÍVEIS (após filtro de busca) de uma subcategoria
  const toggleAllIndividualItems = (subcategoryId, visibleItems = null) => {
    const items = visibleItems !== null
      ? visibleItems
      : (subcategoryItems[subcategoryId] || []);
    const selected = selectedIndividualItems[subcategoryId] || [];
    const visibleIds = items.map(item => item.id);
    const allVisibleSelected = visibleIds.length > 0 && visibleIds.every(id => selected.includes(id));

    setSelectedIndividualItems(prev => {
      const prevSelected = prev[subcategoryId] || [];
      if (allVisibleSelected) {
        // Desmarcar apenas os IDs visíveis (mantém seleções anteriores fora do filtro)
        return {
          ...prev,
          [subcategoryId]: prevSelected.filter(id => !visibleIds.includes(id)),
        };
      }
      // Marcar todos os IDs visíveis sem duplicar
      return {
        ...prev,
        [subcategoryId]: Array.from(new Set([...prevSelected, ...visibleIds])),
      };
    });
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
        item_ids: selectedIds,
        data_inicio: globalDataInicio || null,
        data_fim: globalDataFim || null,
        forma_pagamento: globalFormaPagamento && globalFormaPagamento !== "todas" ? globalFormaPagamento : null,
        centro_custo: selectedCentroCusto && selectedCentroCusto !== "todos" ? selectedCentroCusto : null,
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
    if (!canExport()) {
      setCcSelectorOpen(true);
      return;
    }
    
    setExporting('all-combined');
    try {
      const ccParam = getCentroCustoParam();
      const response = await axios.post(`${API}/export/combined`, {
        categories: selectedItems,
        format: 'pdf',
        centro_custo: ccParam || null,
        data_inicio: globalDataInicio || null,
        data_fim: globalDataFim || null,
        forma_pagamento: globalFormaPagamento && globalFormaPagamento !== "todas" ? globalFormaPagamento : null,
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

  // Helper: retorna o nome do CC selecionado para incluir na URL
  const getCentroCustoParam = () => {
    if (module !== "administrativo") return null;
    if (!selectedCentroCusto || selectedCentroCusto === "todos") return null;
    return selectedCentroCusto;
  };

  // Helper: verifica se pode exportar (CC selecionado ou módulo gerenciamento)
  const canExport = () => {
    if (module !== "administrativo") return true;
    return selectedCentroCusto !== null;
  };

  const exportPDF = async (itemId) => {
    if (!canExport()) {
      setCcSelectorOpen(true);
      return;
    }
    setExporting(`pdf-${itemId}`);
    try {
      const ccParam = getCentroCustoParam();
      const apiUrl = `${API}/export/pdf/${itemId}${buildPeriodQuery(ccParam ? { centro_custo: ccParam } : {})}`;
      const response = await axios.get(apiUrl, {
        headers: { Authorization: `Bearer ${token}` },
        responseType: 'blob'
      });
      
      const blobUrl = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = blobUrl;
      
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
      window.URL.revokeObjectURL(blobUrl);
      
      toast.success("PDF exportado!");
    } catch (error) {
      console.error("Erro ao exportar:", error);
      toast.error("Erro ao exportar PDF");
    } finally {
      setExporting(null);
    }
  };

  const exportExcel = async (itemId) => {
    if (!canExport()) {
      setCcSelectorOpen(true);
      return;
    }
    setExporting(`excel-${itemId}`);
    try {
      const ccParam = getCentroCustoParam();
      const apiUrl = `${API}/export/excel/${itemId}${buildPeriodQuery(ccParam ? { centro_custo: ccParam } : {})}`;
      const response = await axios.get(apiUrl, {
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
    if (!canExport()) {
      setCcSelectorOpen(true);
      return;
    }
    setExporting(`ofx-${itemId}`);
    try {
      const ccParam = getCentroCustoParam();
      const apiUrl = `${API}/export/ofx/${itemId}${buildPeriodQuery(ccParam ? { centro_custo: ccParam } : {})}`;
      const response = await axios.get(apiUrl, {
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
      const response = await axios.get(`${API}/export/extrato-bancario/${selectedContaBancaria}${buildPeriodQuery()}`, {
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

      {/* Banner GLOBAL de Período + Forma de Pagamento — aplica a TODAS as exportações */}
      <div className="mb-6 rounded-xl border-2 border-indigo-200 bg-indigo-50 p-4">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div className="flex items-center gap-3 shrink-0">
            <div className="w-10 h-10 rounded-lg flex items-center justify-center bg-indigo-100">
              <Clock size={18} className="text-indigo-600" />
            </div>
            <div>
              <p className="font-semibold text-sm text-indigo-900">Filtros globais de exportação</p>
              <p className="text-xs text-indigo-600">
                {globalDataInicio || globalDataFim || (globalFormaPagamento && globalFormaPagamento !== "todas")
                  ? `Aplicando: ${globalDataInicio || "início"} até ${globalDataFim || "hoje"}` +
                    (globalFormaPagamento && globalFormaPagamento !== "todas" ? ` • Forma: ${globalFormaPagamento}` : "")
                  : "Sem filtros — exporta todos os registros. Configure abaixo para limitar."}
              </p>
            </div>
          </div>
          <div className="flex flex-wrap items-end gap-3">
            <div>
              <label className="text-xs text-indigo-700 font-medium block mb-1">Data Início</label>
              <Input
                type="date"
                value={globalDataInicio}
                onChange={(e) => setGlobalDataInicio(e.target.value)}
                className="h-9 w-40 bg-white"
                data-testid="export-global-data-inicio"
              />
            </div>
            <div>
              <label className="text-xs text-indigo-700 font-medium block mb-1">Data Fim</label>
              <Input
                type="date"
                value={globalDataFim}
                onChange={(e) => setGlobalDataFim(e.target.value)}
                className="h-9 w-40 bg-white"
                data-testid="export-global-data-fim"
              />
            </div>
            <div>
              <label className="text-xs text-indigo-700 font-medium block mb-1">Forma de Pagamento</label>
              <select
                value={globalFormaPagamento}
                onChange={(e) => setGlobalFormaPagamento(e.target.value)}
                className="h-9 w-48 bg-white rounded-md border border-input px-3 text-sm"
                data-testid="export-global-forma-pagamento"
              >
                <option value="todas">Todas as formas</option>
                {formasPagamento.map((fp) => (
                  <option key={fp.id} value={fp.nome}>{fp.nome}</option>
                ))}
              </select>
            </div>
            {(globalDataInicio || globalDataFim || (globalFormaPagamento && globalFormaPagamento !== "todas")) && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  setGlobalDataInicio("");
                  setGlobalDataFim("");
                  setGlobalFormaPagamento("todas");
                }}
                className="border-indigo-300 text-indigo-700 hover:bg-indigo-100 h-9"
                data-testid="export-global-clear-period"
              >
                <XIcon size={14} className="mr-1" />
                Limpar
              </Button>
            )}
          </div>
        </div>
        <p className="text-[11px] text-indigo-500 mt-2 italic">
          Filtro de Forma de Pagamento aplica-se apenas às coleções de Contas a Pagar / Receber.
        </p>
      </div>

      {/* Centro de Custo Filter Banner - apenas módulo administrativo */}
      {module === "administrativo" && (
        <div className={`mb-6 rounded-xl border-2 p-4 transition-all ${
          selectedCentroCusto === null
            ? 'border-amber-300 bg-amber-50'
            : selectedCentroCusto === "todos"
            ? 'border-blue-200 bg-blue-50'
            : 'border-green-300 bg-green-50'
        }`}>
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className={`w-10 h-10 rounded-lg flex items-center justify-center shrink-0 ${
                selectedCentroCusto === null ? 'bg-amber-200' :
                selectedCentroCusto === "todos" ? 'bg-blue-100' : 'bg-green-100'
              }`}>
                <Filter size={18} className={
                  selectedCentroCusto === null ? 'text-amber-700' :
                  selectedCentroCusto === "todos" ? 'text-blue-600' : 'text-green-700'
                } />
              </div>
              <div>
                <p className={`font-semibold text-sm ${
                  selectedCentroCusto === null ? 'text-amber-800' :
                  selectedCentroCusto === "todos" ? 'text-blue-800' : 'text-green-800'
                }`}>
                  {selectedCentroCusto === null
                    ? 'Selecione o Centro de Custo para exportar'
                    : selectedCentroCusto === "todos"
                    ? 'Exportando: Todos os Centros de Custo'
                    : `Exportando: ${selectedCentroCusto}`
                  }
                </p>
                <p className={`text-xs ${
                  selectedCentroCusto === null ? 'text-amber-600' :
                  selectedCentroCusto === "todos" ? 'text-blue-500' : 'text-green-600'
                }`}>
                  {selectedCentroCusto === null
                    ? 'Os botões de exportação ficam bloqueados até a seleção ser feita'
                    : 'Dados financeiros filtrados por este centro de custo'
                  }
                </p>
              </div>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCcSelectorOpen(true)}
              className={`shrink-0 ${
                selectedCentroCusto === null
                  ? 'border-amber-400 text-amber-700 hover:bg-amber-100'
                  : 'border-gray-300 text-gray-600 hover:bg-gray-100'
              }`}
              data-testid="cc-selector-btn"
            >
              {selectedCentroCusto === null ? 'Selecionar Centro de Custo' : 'Alterar'}
            </Button>
          </div>
        </div>
      )}

      {/* Categories */}
      <div className={`space-y-3 ${module === "administrativo" && selectedCentroCusto === null ? 'opacity-50 pointer-events-none' : ''}`}>
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
                            <p className={`text-sm flex items-center gap-2 ${isSubSelected ? 'font-medium text-gray-900' : 'text-gray-700'}`}>
                              {sub.label}
                              {canExpand && subcategoryCounts[sub.id] !== undefined && subcategoryCounts[sub.id] >= 0 && (
                                <span
                                  className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                                    (globalDataInicio || globalDataFim)
                                      ? subcategoryCounts[sub.id] === 0
                                        ? "bg-gray-100 text-gray-400"
                                        : "bg-indigo-100 text-indigo-700"
                                      : "bg-gray-100 text-gray-600"
                                  }`}
                                  title={
                                    (globalDataInicio || globalDataFim)
                                      ? `${subcategoryCounts[sub.id]} item(ns) no período selecionado`
                                      : `${subcategoryCounts[sub.id]} item(ns) no total`
                                  }
                                  data-testid={`count-${sub.id}`}
                                >
                                  {subcategoryCounts[sub.id]}
                                </span>
                              )}
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
                            {/* Barra de pesquisa */}
                            {items.length > 0 && (
                              <div className="relative mb-3">
                                <Search
                                  size={14}
                                  className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none"
                                />
                                <Input
                                  type="text"
                                  placeholder="Buscar por descrição, fornecedor, cliente, Nº NF, valor, placa..."
                                  value={itemSearch[sub.id] || ""}
                                  onChange={(e) =>
                                    setItemSearch({ ...itemSearch, [sub.id]: e.target.value })
                                  }
                                  className="pl-9 pr-9 h-9 text-sm bg-white"
                                  data-testid={`search-${sub.id}`}
                                />
                                {itemSearch[sub.id] && (
                                  <button
                                    type="button"
                                    onClick={() =>
                                      setItemSearch({ ...itemSearch, [sub.id]: "" })
                                    }
                                    className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                                    aria-label="Limpar busca"
                                  >
                                    <XIcon size={14} />
                                  </button>
                                )}
                              </div>
                            )}

                            {/* Header com ações em lote + lista filtrada (compartilham `filteredItems`) */}
                            {(() => {
                              const searchTerm = (itemSearch[sub.id] || "").trim().toLowerCase();
                              const filteredItems = !searchTerm
                                ? items
                                : items.filter((item) => {
                                    const haystack = [
                                      item.name,
                                      item.fornecedor_nome,
                                      item.cliente_nome,
                                      item.numero_doc,
                                      item.model,
                                      item.plate,
                                      item.banco,
                                      item.data_vencimento,
                                      item.valor !== undefined ? String(item.valor) : "",
                                      item.valor !== undefined
                                        ? Number(item.valor).toLocaleString("pt-BR", {
                                            minimumFractionDigits: 2,
                                          })
                                        : "",
                                    ]
                                      .filter(Boolean)
                                      .join(" ")
                                      .toLowerCase();
                                    return haystack.includes(searchTerm);
                                  });
                              const selectedIds = selectedIndividualItems[sub.id] || [];
                              const visibleIds = filteredItems.map(i => i.id);
                              const allVisibleSelected = visibleIds.length > 0 && visibleIds.every(id => selectedIds.includes(id));
                              return (
                                <>
                                  <div className="flex items-center justify-between mb-3">
                                    <div className="flex items-center gap-2">
                                      <Checkbox 
                                        checked={allVisibleSelected}
                                        onCheckedChange={() => toggleAllIndividualItems(sub.id, filteredItems)}
                                        className="shrink-0"
                                        data-testid={`select-all-${sub.id}`}
                                      />
                                      <p className="text-xs text-purple-700 font-medium">
                                        {searchTerm
                                          ? `Selecionar visíveis (${visibleIds.filter(id => selectedIds.includes(id)).length}/${visibleIds.length}) — ${selectedIds.length} no total`
                                          : `Itens individuais (${selectedIds.length} selecionados)`}
                                      </p>
                                    </div>
                                    {selectedIds.length > 0 && (
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
                                    filteredItems.length === 0 ? (
                                      <p className="text-sm text-gray-500 py-3 text-center">
                                        Nenhum item encontrado para "{searchTerm}"
                                      </p>
                                    ) : (
                                      <>
                                        {searchTerm && (
                                          <p className="text-xs text-purple-600 mb-2">
                                            Mostrando {filteredItems.length} de {items.length} itens
                                          </p>
                                        )}
                                        <div className="space-y-2 max-h-80 overflow-y-auto">
                                          {filteredItems.map(item => {
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
                                          {item.numero_doc && (
                                            <span className="font-mono text-blue-600" title="Nº Documento/NF">NF {item.numero_doc}</span>
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
                                          {/* Indicador de pagamentos parciais (parcelas pagas) */}
                                          {(item.pagamentos?.length || item.recebimentos?.length) > 0 && (
                                            <span
                                              className="font-medium text-emerald-700 cursor-pointer hover:underline"
                                              title="Ver parcelas pagas"
                                              onClick={(e) => {
                                                e.preventDefault();
                                                e.stopPropagation();
                                                const el = document.getElementById(`parcelas-${item.id}`);
                                                if (el) el.classList.toggle('hidden');
                                              }}
                                            >
                                              ▾ {(item.pagamentos?.length || item.recebimentos?.length)} pagamento(s)
                                            </span>
                                          )}
                                        </div>
                                        {/* Dropdown FIXO com as parcelas pagas (oculto por padrão) */}
                                        {(item.pagamentos?.length || item.recebimentos?.length) > 0 && (
                                          <div
                                            id={`parcelas-${item.id}`}
                                            className="hidden mt-2 ml-4 pl-3 border-l-2 border-emerald-300 space-y-1"
                                          >
                                            {(item.pagamentos || item.recebimentos || []).map((p, idx) => {
                                              const [y, m, d] = String(p.data || '').split('-');
                                              const dataFmt = (y && m && d) ? `${d}/${m}/${y}` : (p.data || '-');
                                              return (
                                                <div key={p.id || idx} className="flex items-center gap-2 text-xs text-gray-700 bg-emerald-50 rounded px-2 py-1">
                                                  <span className="font-medium text-emerald-800">{dataFmt}</span>
                                                  <span className="font-semibold text-emerald-700">
                                                    R$ {Number(p.valor || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                                                  </span>
                                                  {p.forma_pagamento && (
                                                    <span className="text-gray-500">• {p.forma_pagamento}</span>
                                                  )}
                                                  {p.observacao && (
                                                    <span className="text-gray-400 truncate" title={p.observacao}>
                                                      • {p.observacao}
                                                    </span>
                                                  )}
                                                </div>
                                              );
                                            })}
                                          </div>
                                        )}
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
                                      </>
                                    )
                                  ) : (
                                    <p className="text-sm text-gray-500">Nenhum item cadastrado nesta categoria</p>
                                  )}
                                </>
                              );
                            })()}
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

      {/* Relatório por Conta Bancária - apenas no módulo administrativo */}
      {module === "administrativo" && (
        <Card className="mt-6 border-2 border-amber-200">
          <CardHeader className="bg-amber-50 border-b border-amber-200 pb-3">
            <CardTitle className="text-lg flex items-center gap-2">
              <Landmark className="text-amber-600" size={20} />
              Relatório por Conta Bancária
            </CardTitle>
          </CardHeader>
          <CardContent className="p-4">
            <p className="text-sm text-gray-600 mb-4">
              Exporte um relatório de contas a pagar ou receber filtrado por conta bancária e status.
            </p>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              {/* Seleção de Conta Bancária */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
                  <Building2 size={14} className="text-gray-500" />
                  Conta Bancária *
                </label>
                <Select value={relContaBancaria} onValueChange={setRelContaBancaria}>
                  <SelectTrigger>
                    <SelectValue placeholder="Selecione a conta..." />
                  </SelectTrigger>
                  <SelectContent>
                    {contasBancarias.map(conta => (
                      <SelectItem key={conta.id} value={conta.id}>
                        {conta.banco} - Ag: {conta.agencia} / CC: {conta.conta}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              
              {/* Tipo de Conta */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
                  <DollarSign size={14} className="text-gray-500" />
                  Tipo de Conta
                </label>
                <Select value={relTipoConta} onValueChange={setRelTipoConta}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="todas">
                      <div className="flex items-center gap-2">
                        <FileText size={14} className="text-blue-500" />
                        Todas (Pagar e Receber)
                      </div>
                    </SelectItem>
                    <SelectItem value="pagar">
                      <div className="flex items-center gap-2">
                        <TrendingDown size={14} className="text-red-500" />
                        Contas a Pagar
                      </div>
                    </SelectItem>
                    <SelectItem value="receber">
                      <div className="flex items-center gap-2">
                        <TrendingUp size={14} className="text-green-500" />
                        Contas a Receber
                      </div>
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              {/* Status */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
                  <Filter size={14} className="text-gray-500" />
                  Status
                </label>
                <Select value={relStatusConta} onValueChange={setRelStatusConta}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="todas">Todas</SelectItem>
                    <SelectItem value="pendente">Pendentes / Em Aberto</SelectItem>
                    <SelectItem value="quitada">Quitadas</SelectItem>
                    <SelectItem value="parcial">Parcialmente Pagas</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            
            <Button
              onClick={exportRelatorioPorContaBancaria}
              disabled={!relContaBancaria || exportingRelatorio}
              style={{ backgroundColor: accentColor }}
              className="text-white"
            >
              {exportingRelatorio ? (
                <Loader2 size={18} className="animate-spin mr-2" />
              ) : (
                <FileDown size={18} className="mr-2" />
              )}
              Exportar Relatório PDF
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Extrato do Plano de Contas — apenas no módulo administrativo */}
      {module === "administrativo" && (
        <Card className="mt-6 border-2 border-emerald-200" data-testid="export-extrato-plano-contas-card">
          <CardHeader className="bg-emerald-50 border-b border-emerald-200 pb-3">
            <CardTitle className="text-lg flex items-center gap-2">
              <List className="text-emerald-600" size={20} />
              Extrato do Plano de Contas
            </CardTitle>
          </CardHeader>
          <CardContent className="p-4">
            <p className="text-sm text-gray-600 mb-4">
              Gere o extrato consolidado e detalhado de movimentações por plano de contas em um período específico.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-4">
              {/* Plano de Contas */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
                  <FileText size={14} className="text-gray-500" />
                  Plano de Contas
                </label>
                <Select value={extratoPlanoConta} onValueChange={setExtratoPlanoConta}>
                  <SelectTrigger data-testid="select-plano-extrato">
                    <SelectValue placeholder="Todos os planos" />
                  </SelectTrigger>
                  <SelectContent className="z-[9999]">
                    <SelectItem value="todos">Todos os planos</SelectItem>
                    {planosContas.map((p) => (
                      <SelectItem key={p.id} value={p.id}>
                        {p.codigo ? `${p.codigo} - ` : ""}{p.nome}
                        {p.nivel === 2 ? "  (subconta)" : ""}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Data Início */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
                  <Clock size={14} className="text-gray-500" />
                  Data Início
                </label>
                <Input
                  type="date"
                  value={extratoDataInicio}
                  onChange={(e) => setExtratoDataInicio(e.target.value)}
                  data-testid="input-data-inicio-extrato"
                />
              </div>

              {/* Data Fim */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
                  <Clock size={14} className="text-gray-500" />
                  Data Fim
                </label>
                <Input
                  type="date"
                  value={extratoDataFim}
                  onChange={(e) => setExtratoDataFim(e.target.value)}
                  data-testid="input-data-fim-extrato"
                />
              </div>

              {/* Tipo */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
                  <Filter size={14} className="text-gray-500" />
                  Tipo
                </label>
                <Select value={extratoTipo} onValueChange={setExtratoTipo}>
                  <SelectTrigger data-testid="select-tipo-extrato">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="z-[9999]">
                    <SelectItem value="ambos">
                      <div className="flex items-center gap-2">
                        <FileText size={14} className="text-blue-500" />
                        Pagar e Receber
                      </div>
                    </SelectItem>
                    <SelectItem value="pagar">
                      <div className="flex items-center gap-2">
                        <TrendingDown size={14} className="text-red-500" />
                        Apenas a Pagar
                      </div>
                    </SelectItem>
                    <SelectItem value="receber">
                      <div className="flex items-center gap-2">
                        <TrendingUp size={14} className="text-green-500" />
                        Apenas a Receber
                      </div>
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Status */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
                  <CheckSquare size={14} className="text-gray-500" />
                  Status
                </label>
                <Select value={extratoStatus} onValueChange={setExtratoStatus}>
                  <SelectTrigger data-testid="select-status-extrato">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="z-[9999]">
                    <SelectItem value="todas">Todas</SelectItem>
                    <SelectItem value="em_aberto">Em Aberto</SelectItem>
                    <SelectItem value="quitada">Quitadas</SelectItem>
                    <SelectItem value="parcial">Parcialmente Pagas</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <p className="text-xs text-gray-500 mb-3">
              📅 Sem filtro de período → traz todos os lançamentos cadastrados.<br/>
              📋 O PDF inclui o resumo consolidado por plano e o detalhamento de cada lançamento.
            </p>

            <Button
              onClick={exportExtratoPlanoContas}
              disabled={exportingExtratoPC}
              className="bg-emerald-600 hover:bg-emerald-700 text-white"
              data-testid="btn-exportar-extrato-plano-contas"
            >
              {exportingExtratoPC ? (
                <Loader2 size={18} className="animate-spin mr-2" />
              ) : (
                <FileDown size={18} className="mr-2" />
              )}
              Exportar Extrato PDF
            </Button>
          </CardContent>
        </Card>
      )}

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

      {/* Modal de Seleção de Centro de Custo */}
      <Dialog open={ccSelectorOpen} onOpenChange={setCcSelectorOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Filter className="text-amber-500" size={20} />
              Selecionar Centro de Custo para Exportação
            </DialogTitle>
          </DialogHeader>
          <div className="py-2">
            <p className="text-sm text-gray-600 mb-4">
              Selecione o centro de custo. Os dados financeiros (Contas a Pagar/Receber) serão filtrados de acordo com a seleção.
            </p>
            <div className="space-y-2 max-h-80 overflow-y-auto pr-1">
              {/* Opção Todos */}
              <button
                onClick={() => { setSelectedCentroCusto("todos"); setCcSelectorOpen(false); }}
                className={`w-full text-left px-4 py-3 rounded-lg border-2 transition-all flex items-center gap-3 ${
                  selectedCentroCusto === "todos"
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-blue-300 hover:bg-blue-50'
                }`}
                data-testid="cc-option-todos"
              >
                <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center shrink-0">
                  <FileDown size={14} className="text-blue-600" />
                </div>
                <div>
                  <p className="font-semibold text-gray-900 text-sm">Todos os Centros de Custo</p>
                  <p className="text-xs text-gray-500">Exportar sem filtro de centro de custo</p>
                </div>
                {selectedCentroCusto === "todos" && (
                  <div className="ml-auto w-5 h-5 rounded-full bg-blue-500 flex items-center justify-center">
                    <CheckSquare size={12} className="text-white" />
                  </div>
                )}
              </button>

              {/* Lista de Centros de Custo */}
              {centrosCusto.length === 0 ? (
                <p className="text-sm text-gray-400 text-center py-4">Nenhum centro de custo cadastrado</p>
              ) : (
                centrosCusto.map((cc) => (
                  <button
                    key={cc.id}
                    onClick={() => { setSelectedCentroCusto(cc.nome); setCcSelectorOpen(false); }}
                    className={`w-full text-left px-4 py-3 rounded-lg border-2 transition-all flex items-center gap-3 ${
                      selectedCentroCusto === cc.nome
                        ? 'border-green-500 bg-green-50'
                        : 'border-gray-200 hover:border-green-300 hover:bg-green-50'
                    }`}
                    data-testid={`cc-option-${cc.id}`}
                  >
                    <div className="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center shrink-0">
                      <Building2 size={14} className="text-green-600" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-semibold text-gray-900 text-sm truncate">{cc.nome}</p>
                      {cc.codigo && <p className="text-xs text-gray-500">Código: {cc.codigo}</p>}
                    </div>
                    {selectedCentroCusto === cc.nome && (
                      <div className="ml-auto w-5 h-5 rounded-full bg-green-500 flex items-center justify-center shrink-0">
                        <CheckSquare size={12} className="text-white" />
                      </div>
                    )}
                  </button>
                ))
              )}
            </div>
          </div>
        </DialogContent>
      </Dialog>

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
