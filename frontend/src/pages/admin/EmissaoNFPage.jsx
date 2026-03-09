import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { API } from "@/App";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
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
  FileText, 
  Plus, 
  Trash2,
  Eye,
  Download,
  Send,
  Save,
  Building2,
  User,
  Package,
  Loader2,
  Search,
  FileDown,
  CheckCircle,
  XCircle,
  Clock,
  AlertTriangle
} from "lucide-react";
import { formatCPFouCNPJ, formatCEP, formatTelefone, formatCurrency, parseCurrency } from "@/utils/masks";

export default function EmissaoNFPage() {
  const [activeTab, setActiveTab] = useState("emitir");
  const [tipoNota, setTipoNota] = useState("nfe"); // "nfe" ou "nfse"
  const [certificados, setCertificados] = useState([]);
  const [notasEmitidas, setNotasEmitidas] = useState([]);
  const [produtos, setProdutos] = useState([]);
  const [cadastros, setCadastros] = useState([]);
  const [cfops, setCfops] = useState([]);
  const [codigosServico, setCodigosServico] = useState([]);
  const [loading, setLoading] = useState(true);
  const [emitindo, setEmitindo] = useState(false);
  const [showNotaDetail, setShowNotaDetail] = useState(null);
  
  // Filtros para notas emitidas
  const [filterCertificado, setFilterCertificado] = useState("todos");
  const [filterStatus, setFilterStatus] = useState("todos");
  const [filterTipo, setFilterTipo] = useState("todos");
  
  // Consulta CEP/CNPJ
  const [consultandoCep, setConsultandoCep] = useState(false);
  const [consultandoCnpj, setConsultandoCnpj] = useState(false);
  
  // Form NF-e
  const [nfeForm, setNfeForm] = useState({
    certificado_id: "",
    // Destinatário
    dest_cpf_cnpj: "",
    dest_razao_social: "",
    dest_ie: "",
    dest_email: "",
    dest_telefone: "",
    dest_cep: "",
    dest_logradouro: "",
    dest_numero: "",
    dest_complemento: "",
    dest_bairro: "",
    dest_cidade: "",
    dest_uf: "",
    dest_codigo_municipio: "",
    // Dados da nota
    natureza_operacao: "Venda de Mercadoria",
    tipo_operacao: "1",
    finalidade: "1",
    consumidor_final: "1",
    presenca_comprador: "1",
    forma_pagamento: "01",
    modalidade_frete: "9",
    transportador_cnpj: "",
    transportador_razao: "",
    // Totais
    valor_frete: "0",
    valor_seguro: "0",
    valor_desconto: "0",
    valor_outros: "0",
    info_complementar: ""
  });
  
  // Itens NF-e
  const [nfeItens, setNfeItens] = useState([]);
  const [showAddItem, setShowAddItem] = useState(false);
  const [itemForm, setItemForm] = useState({
    produto_id: "",
    codigo: "",
    descricao: "",
    ncm: "00000000",
    cfop: "5102",
    unidade: "UN",
    quantidade: "1",
    valor_unitario: "",
    origem: "0",
    cst_icms: "00",
    aliquota_icms: "0",
    cst_pis: "01",
    aliquota_pis: "0",
    cst_cofins: "01",
    aliquota_cofins: "0",
    cst_ipi: "50",
    aliquota_ipi: "0"
  });
  
  // Form NFS-e
  const [nfseForm, setNfseForm] = useState({
    certificado_id: "",
    // Tomador
    tomador_cpf_cnpj: "",
    tomador_razao_social: "",
    tomador_ie: "",
    tomador_im: "",
    tomador_email: "",
    tomador_telefone: "",
    tomador_cep: "",
    tomador_logradouro: "",
    tomador_numero: "",
    tomador_complemento: "",
    tomador_bairro: "",
    tomador_cidade: "",
    tomador_uf: "",
    tomador_codigo_municipio: "",
    // Serviço
    codigo_cnae: "",
    codigo_tributario_municipio: "",
    item_lista_servico: "",
    discriminacao: "",
    // Valores
    valor_servicos: "",
    valor_deducoes: "0",
    valor_pis: "0",
    valor_cofins: "0",
    valor_inss: "0",
    valor_ir: "0",
    valor_csll: "0",
    outras_retencoes: "0",
    aliquota_iss: "0",
    iss_retido: false,
    info_complementar: ""
  });
  
  const naturezasOperacao = [
    "Venda de Mercadoria",
    "Venda de Produção do Estabelecimento",
    "Venda de Mercadoria Adquirida",
    "Transferência de Mercadoria",
    "Devolução de Compra",
    "Remessa para Demonstração",
    "Remessa para Conserto",
    "Prestação de Serviço"
  ];
  
  const formasPagamento = [
    { value: "01", label: "Dinheiro" },
    { value: "02", label: "Cheque" },
    { value: "03", label: "Cartão de Crédito" },
    { value: "04", label: "Cartão de Débito" },
    { value: "05", label: "Crédito Loja" },
    { value: "10", label: "Vale Alimentação" },
    { value: "11", label: "Vale Refeição" },
    { value: "12", label: "Vale Presente" },
    { value: "13", label: "Vale Combustível" },
    { value: "14", label: "Duplicata Mercantil" },
    { value: "15", label: "Boleto Bancário" },
    { value: "16", label: "Depósito Bancário" },
    { value: "17", label: "PIX" },
    { value: "18", label: "Transferência Bancária" },
    { value: "90", label: "Sem Pagamento" },
    { value: "99", label: "Outros" }
  ];

  useEffect(() => {
    fetchData();
  }, []);
  
  useEffect(() => {
    fetchNotasEmitidas();
  }, [filterCertificado, filterStatus, filterTipo]);

  const fetchData = async () => {
    try {
      const [certsRes, produtosRes, cadastrosRes, cfopsRes, codigosRes] = await Promise.all([
        axios.get(`${API}/nfe/certificados`),
        axios.get(`${API}/admin/produtos`),
        axios.get(`${API}/admin/cadastros`),
        axios.get(`${API}/nfe/cfops`),
        axios.get(`${API}/nfse/codigos-servico`)
      ]);
      setCertificados(certsRes.data);
      setProdutos(produtosRes.data);
      setCadastros(cadastrosRes.data);
      setCfops(cfopsRes.data);
      setCodigosServico(codigosRes.data);
    } catch (error) {
      console.error("Erro ao carregar dados:", error);
      toast.error("Erro ao carregar dados");
    } finally {
      setLoading(false);
    }
  };
  
  const fetchNotasEmitidas = async () => {
    try {
      const params = new URLSearchParams();
      if (filterCertificado !== "todos") params.append("certificado_id", filterCertificado);
      if (filterStatus !== "todos") params.append("status", filterStatus);
      if (filterTipo !== "todos") params.append("tipo", filterTipo);
      
      const response = await axios.get(`${API}/notas-emitidas?${params.toString()}`);
      setNotasEmitidas(response.data);
    } catch (error) {
      console.error("Erro ao carregar notas:", error);
    }
  };
  
  // Consulta CEP
  const consultarCep = async (cep, isNfse = false) => {
    const cepLimpo = cep.replace(/\D/g, "");
    if (cepLimpo.length !== 8) return;
    
    setConsultandoCep(true);
    try {
      const response = await axios.get(`https://viacep.com.br/ws/${cepLimpo}/json/`);
      if (!response.data.erro) {
        const data = response.data;
        if (isNfse) {
          setNfseForm(prev => ({
            ...prev,
            tomador_logradouro: data.logradouro || "",
            tomador_bairro: data.bairro || "",
            tomador_cidade: data.localidade || "",
            tomador_uf: data.uf || "",
            tomador_codigo_municipio: data.ibge || ""
          }));
        } else {
          setNfeForm(prev => ({
            ...prev,
            dest_logradouro: data.logradouro || "",
            dest_bairro: data.bairro || "",
            dest_cidade: data.localidade || "",
            dest_uf: data.uf || "",
            dest_codigo_municipio: data.ibge || ""
          }));
        }
        toast.success("CEP encontrado!");
      }
    } catch (error) {
      toast.error("Erro ao consultar CEP");
    } finally {
      setConsultandoCep(false);
    }
  };
  
  // Consulta CNPJ
  const consultarCnpj = async (cnpj, isNfse = false) => {
    const cnpjLimpo = cnpj.replace(/\D/g, "");
    if (cnpjLimpo.length !== 14) return;
    
    setConsultandoCnpj(true);
    try {
      const response = await axios.get(`https://brasilapi.com.br/api/cnpj/v1/${cnpjLimpo}`);
      const data = response.data;
      
      if (isNfse) {
        setNfseForm(prev => ({
          ...prev,
          tomador_razao_social: data.razao_social || "",
          tomador_cep: data.cep || "",
          tomador_logradouro: data.logradouro || "",
          tomador_numero: data.numero || "",
          tomador_complemento: data.complemento || "",
          tomador_bairro: data.bairro || "",
          tomador_cidade: data.municipio || "",
          tomador_uf: data.uf || "",
          tomador_telefone: data.ddd_telefone_1 || ""
        }));
      } else {
        setNfeForm(prev => ({
          ...prev,
          dest_razao_social: data.razao_social || "",
          dest_cep: data.cep || "",
          dest_logradouro: data.logradouro || "",
          dest_numero: data.numero || "",
          dest_complemento: data.complemento || "",
          dest_bairro: data.bairro || "",
          dest_cidade: data.municipio || "",
          dest_uf: data.uf || "",
          dest_telefone: data.ddd_telefone_1 || ""
        }));
      }
      toast.success("CNPJ encontrado!");
    } catch (error) {
      toast.error("CNPJ não encontrado");
    } finally {
      setConsultandoCnpj(false);
    }
  };
  
  // Selecionar cliente/fornecedor do cadastro
  const selecionarCadastro = (cadastroId, isNfse = false) => {
    const cadastro = cadastros.find(c => c.id === cadastroId);
    if (!cadastro) return;
    
    if (isNfse) {
      setNfseForm(prev => ({
        ...prev,
        tomador_cpf_cnpj: cadastro.cpf_cnpj || "",
        tomador_razao_social: cadastro.nome_razao || "",
        tomador_ie: cadastro.rg_ie || "",
        tomador_email: cadastro.email || "",
        tomador_telefone: cadastro.telefone || cadastro.celular || "",
        tomador_cep: cadastro.cep || "",
        tomador_logradouro: cadastro.endereco || "",
        tomador_numero: cadastro.numero || "",
        tomador_complemento: cadastro.complemento || "",
        tomador_bairro: cadastro.bairro || "",
        tomador_cidade: cadastro.cidade || "",
        tomador_uf: cadastro.uf || ""
      }));
    } else {
      setNfeForm(prev => ({
        ...prev,
        dest_cpf_cnpj: cadastro.cpf_cnpj || "",
        dest_razao_social: cadastro.nome_razao || "",
        dest_ie: cadastro.rg_ie || "",
        dest_email: cadastro.email || "",
        dest_telefone: cadastro.telefone || cadastro.celular || "",
        dest_cep: cadastro.cep || "",
        dest_logradouro: cadastro.endereco || "",
        dest_numero: cadastro.numero || "",
        dest_complemento: cadastro.complemento || "",
        dest_bairro: cadastro.bairro || "",
        dest_cidade: cadastro.cidade || "",
        dest_uf: cadastro.uf || ""
      }));
    }
    toast.success("Dados do cadastro preenchidos!");
  };
  
  // Adicionar item à NF-e
  const adicionarItem = () => {
    const valorUnitario = parseCurrency(itemForm.valor_unitario);
    const quantidade = parseFloat(itemForm.quantidade) || 0;
    const valorTotal = valorUnitario * quantidade;
    
    // Calcular tributos
    const aliquotaIcms = parseFloat(itemForm.aliquota_icms) || 0;
    const aliquotaPis = parseFloat(itemForm.aliquota_pis) || 0;
    const aliquotaCofins = parseFloat(itemForm.aliquota_cofins) || 0;
    const aliquotaIpi = parseFloat(itemForm.aliquota_ipi) || 0;
    
    const novoItem = {
      ...itemForm,
      quantidade,
      valor_unitario: valorUnitario,
      valor_total: valorTotal,
      aliquota_icms: aliquotaIcms,
      valor_icms: valorTotal * (aliquotaIcms / 100),
      aliquota_pis: aliquotaPis,
      valor_pis: valorTotal * (aliquotaPis / 100),
      aliquota_cofins: aliquotaCofins,
      valor_cofins: valorTotal * (aliquotaCofins / 100),
      aliquota_ipi: aliquotaIpi,
      valor_ipi: valorTotal * (aliquotaIpi / 100)
    };
    
    setNfeItens([...nfeItens, novoItem]);
    setShowAddItem(false);
    setItemForm({
      produto_id: "",
      codigo: "",
      descricao: "",
      ncm: "00000000",
      cfop: "5102",
      unidade: "UN",
      quantidade: "1",
      valor_unitario: "",
      origem: "0",
      cst_icms: "00",
      aliquota_icms: "0",
      cst_pis: "01",
      aliquota_pis: "0",
      cst_cofins: "01",
      aliquota_cofins: "0",
      cst_ipi: "50",
      aliquota_ipi: "0"
    });
    toast.success("Item adicionado!");
  };
  
  // Selecionar produto
  const selecionarProduto = (produtoId) => {
    const produto = produtos.find(p => p.id === produtoId);
    if (!produto) return;
    
    setItemForm(prev => ({
      ...prev,
      produto_id: produtoId,
      codigo: produto.codigo_interno || produto.id.substring(0, 8),
      descricao: produto.descricao,
      ncm: produto.ncm || "00000000",
      unidade: produto.unidade_comercial || "UN",
      valor_unitario: formatCurrency(produto.preco_venda || produto.preco_custo || 0),
      origem: produto.origem || "0",
      aliquota_icms: String(produto.icms || 0),
      aliquota_pis: String(produto.pis || 0),
      aliquota_cofins: String(produto.cofins || 0),
      aliquota_ipi: String(produto.ipi || 0)
    }));
  };
  
  // Remover item
  const removerItem = (index) => {
    setNfeItens(nfeItens.filter((_, i) => i !== index));
  };
  
  // Calcular totais NF-e
  const calcularTotaisNfe = () => {
    const valorProdutos = nfeItens.reduce((acc, item) => acc + item.valor_total, 0);
    const valorFrete = parseCurrency(nfeForm.valor_frete);
    const valorSeguro = parseCurrency(nfeForm.valor_seguro);
    const valorDesconto = parseCurrency(nfeForm.valor_desconto);
    const valorOutros = parseCurrency(nfeForm.valor_outros);
    const valorTotal = valorProdutos + valorFrete + valorSeguro + valorOutros - valorDesconto;
    
    return { valorProdutos, valorTotal };
  };
  
  // Calcular totais NFS-e
  const calcularTotaisNfse = () => {
    const valorServicos = parseCurrency(nfseForm.valor_servicos);
    const valorDeducoes = parseCurrency(nfseForm.valor_deducoes);
    const valorPis = parseCurrency(nfseForm.valor_pis);
    const valorCofins = parseCurrency(nfseForm.valor_cofins);
    const valorInss = parseCurrency(nfseForm.valor_inss);
    const valorIr = parseCurrency(nfseForm.valor_ir);
    const valorCsll = parseCurrency(nfseForm.valor_csll);
    const outrasRetencoes = parseCurrency(nfseForm.outras_retencoes);
    const aliquotaIss = parseFloat(nfseForm.aliquota_iss) || 0;
    
    const baseCalculo = valorServicos - valorDeducoes;
    const valorIss = baseCalculo * (aliquotaIss / 100);
    const totalRetencoes = valorPis + valorCofins + valorInss + valorIr + valorCsll + outrasRetencoes;
    const valorLiquido = valorServicos - totalRetencoes - (nfseForm.iss_retido ? valorIss : 0);
    
    return { valorServicos, valorIss, valorLiquido };
  };
  
  // Emitir NF-e
  const emitirNfe = async () => {
    if (!nfeForm.certificado_id) {
      toast.error("Selecione o CNPJ emitente");
      return;
    }
    if (!nfeForm.dest_cpf_cnpj || !nfeForm.dest_razao_social) {
      toast.error("Preencha os dados do destinatário");
      return;
    }
    if (nfeItens.length === 0) {
      toast.error("Adicione pelo menos um item");
      return;
    }
    
    const { valorProdutos, valorTotal } = calcularTotaisNfe();
    
    setEmitindo(true);
    try {
      const response = await axios.post(`${API}/nfe/emitir`, {
        ...nfeForm,
        valor_frete: parseCurrency(nfeForm.valor_frete),
        valor_seguro: parseCurrency(nfeForm.valor_seguro),
        valor_desconto: parseCurrency(nfeForm.valor_desconto),
        valor_outros: parseCurrency(nfeForm.valor_outros),
        valor_produtos: valorProdutos,
        valor_total: valorTotal,
        valor_pagamento: valorTotal,
        itens: nfeItens
      });
      
      toast.success(response.data.mensagem || "NF-e criada com sucesso!");
      fetchNotasEmitidas();
      
      // Limpar formulário
      setNfeForm({
        certificado_id: nfeForm.certificado_id,
        dest_cpf_cnpj: "",
        dest_razao_social: "",
        dest_ie: "",
        dest_email: "",
        dest_telefone: "",
        dest_cep: "",
        dest_logradouro: "",
        dest_numero: "",
        dest_complemento: "",
        dest_bairro: "",
        dest_cidade: "",
        dest_uf: "",
        dest_codigo_municipio: "",
        natureza_operacao: "Venda de Mercadoria",
        tipo_operacao: "1",
        finalidade: "1",
        consumidor_final: "1",
        presenca_comprador: "1",
        forma_pagamento: "01",
        modalidade_frete: "9",
        transportador_cnpj: "",
        transportador_razao: "",
        valor_frete: "0",
        valor_seguro: "0",
        valor_desconto: "0",
        valor_outros: "0",
        info_complementar: ""
      });
      setNfeItens([]);
      setActiveTab("emitidas");
      
    } catch (error) {
      console.error("Erro ao emitir NF-e:", error);
      toast.error(error.response?.data?.detail || "Erro ao emitir NF-e");
    } finally {
      setEmitindo(false);
    }
  };
  
  // Emitir NFS-e
  const emitirNfse = async () => {
    if (!nfseForm.certificado_id) {
      toast.error("Selecione o CNPJ emitente");
      return;
    }
    if (!nfseForm.tomador_cpf_cnpj || !nfseForm.tomador_razao_social) {
      toast.error("Preencha os dados do tomador");
      return;
    }
    if (!nfseForm.item_lista_servico || !nfseForm.discriminacao) {
      toast.error("Preencha os dados do serviço");
      return;
    }
    if (!nfseForm.valor_servicos) {
      toast.error("Informe o valor dos serviços");
      return;
    }
    
    const { valorServicos, valorIss, valorLiquido } = calcularTotaisNfse();
    
    setEmitindo(true);
    try {
      const response = await axios.post(`${API}/nfse/emitir`, {
        ...nfseForm,
        valor_servicos: valorServicos,
        valor_deducoes: parseCurrency(nfseForm.valor_deducoes),
        valor_pis: parseCurrency(nfseForm.valor_pis),
        valor_cofins: parseCurrency(nfseForm.valor_cofins),
        valor_inss: parseCurrency(nfseForm.valor_inss),
        valor_ir: parseCurrency(nfseForm.valor_ir),
        valor_csll: parseCurrency(nfseForm.valor_csll),
        outras_retencoes: parseCurrency(nfseForm.outras_retencoes),
        valor_iss: valorIss,
        aliquota_iss: parseFloat(nfseForm.aliquota_iss) || 0,
        valor_liquido: valorLiquido,
        itens: []
      });
      
      toast.success(response.data.mensagem || "NFS-e criada com sucesso!");
      fetchNotasEmitidas();
      
      // Limpar formulário
      setNfseForm({
        certificado_id: nfseForm.certificado_id,
        tomador_cpf_cnpj: "",
        tomador_razao_social: "",
        tomador_ie: "",
        tomador_im: "",
        tomador_email: "",
        tomador_telefone: "",
        tomador_cep: "",
        tomador_logradouro: "",
        tomador_numero: "",
        tomador_complemento: "",
        tomador_bairro: "",
        tomador_cidade: "",
        tomador_uf: "",
        tomador_codigo_municipio: "",
        codigo_cnae: "",
        codigo_tributario_municipio: "",
        item_lista_servico: "",
        discriminacao: "",
        valor_servicos: "",
        valor_deducoes: "0",
        valor_pis: "0",
        valor_cofins: "0",
        valor_inss: "0",
        valor_ir: "0",
        valor_csll: "0",
        outras_retencoes: "0",
        aliquota_iss: "0",
        iss_retido: false,
        info_complementar: ""
      });
      setActiveTab("emitidas");
      
    } catch (error) {
      console.error("Erro ao emitir NFS-e:", error);
      toast.error(error.response?.data?.detail || "Erro ao emitir NFS-e");
    } finally {
      setEmitindo(false);
    }
  };
  
  // Download XML/PDF
  const handleDownload = async (notaId, tipo) => {
    try {
      const response = await axios.get(`${API}/notas-emitidas/${notaId}/download-${tipo}`, {
        responseType: 'blob'
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `nota_${notaId}.${tipo}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      toast.error(`Erro ao baixar ${tipo.toUpperCase()}`);
    }
  };
  
  // Excluir nota
  const excluirNota = async (notaId) => {
    if (!confirm("Tem certeza que deseja excluir esta nota?")) return;
    
    try {
      await axios.delete(`${API}/notas-emitidas/${notaId}`);
      toast.success("Nota excluída com sucesso!");
      fetchNotasEmitidas();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao excluir nota");
    }
  };
  
  // Status badge
  const getStatusBadge = (status) => {
    const badges = {
      autorizada: { color: "bg-green-100 text-green-800", icon: CheckCircle, label: "Autorizada" },
      rascunho: { color: "bg-yellow-100 text-yellow-800", icon: Clock, label: "Rascunho" },
      pendente: { color: "bg-blue-100 text-blue-800", icon: Loader2, label: "Pendente" },
      rejeitada: { color: "bg-red-100 text-red-800", icon: XCircle, label: "Rejeitada" }
    };
    const badge = badges[status] || badges.pendente;
    const Icon = badge.icon;
    
    return (
      <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${badge.color}`}>
        <Icon size={12} />
        {badge.label}
      </span>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  const { valorProdutos, valorTotal } = calcularTotaisNfe();
  const { valorServicos, valorIss, valorLiquido } = calcularTotaisNfse();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Emissão de Notas Fiscais</h1>
          <p className="text-gray-500 text-sm mt-1">Emita NF-e (Produtos) e NFS-e (Serviços)</p>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="emitir" className="flex items-center gap-2">
            <Plus size={16} />
            Emitir Nova Nota
          </TabsTrigger>
          <TabsTrigger value="emitidas" className="flex items-center gap-2">
            <FileText size={16} />
            Notas Emitidas
          </TabsTrigger>
        </TabsList>

        {/* Tab: Emitir Nova Nota */}
        <TabsContent value="emitir" className="space-y-6 mt-6">
          {/* Seleção do tipo de nota e CNPJ emitente */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Building2 size={20} />
                Configuração da Nota
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label>Tipo de Nota *</Label>
                  <Select value={tipoNota} onValueChange={setTipoNota}>
                    <SelectTrigger data-testid="select-tipo-nota">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="nfe">NF-e (Nota Fiscal de Produtos)</SelectItem>
                      <SelectItem value="nfse">NFS-e (Nota Fiscal de Serviços)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>CNPJ Emitente *</Label>
                  <Select 
                    value={tipoNota === "nfe" ? nfeForm.certificado_id : nfseForm.certificado_id}
                    onValueChange={(value) => {
                      if (tipoNota === "nfe") {
                        setNfeForm(prev => ({ ...prev, certificado_id: value }));
                      } else {
                        setNfseForm(prev => ({ ...prev, certificado_id: value }));
                      }
                    }}
                  >
                    <SelectTrigger data-testid="select-cnpj-emitente">
                      <SelectValue placeholder="Selecione o CNPJ" />
                    </SelectTrigger>
                    <SelectContent>
                      {certificados.filter(c => c.ativo).map(cert => (
                        <SelectItem key={cert.id} value={cert.id}>
                          {cert.razao_social} - {formatCPFouCNPJ(cert.cnpj)} ({cert.ambiente === "homologacao" ? "Homolog." : "Produção"})
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  {certificados.length === 0 && (
                    <p className="text-xs text-red-500 mt-1">Nenhum certificado cadastrado. Cadastre um certificado na página de Importação de NF.</p>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Formulário NF-e */}
          {tipoNota === "nfe" && (
            <>
              {/* Destinatário */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg flex items-center gap-2">
                    <User size={20} />
                    Destinatário
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Buscar do cadastro */}
                  <div className="flex gap-2 items-end">
                    <div className="flex-1">
                      <Label>Buscar do Cadastro</Label>
                      <Select onValueChange={(value) => selecionarCadastro(value, false)}>
                        <SelectTrigger>
                          <SelectValue placeholder="Selecione um cliente/fornecedor" />
                        </SelectTrigger>
                        <SelectContent>
                          {cadastros.map(c => (
                            <SelectItem key={c.id} value={c.id}>
                              {c.nome_razao} - {formatCPFouCNPJ(c.cpf_cnpj || "")}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <Label>CPF/CNPJ *</Label>
                      <div className="flex gap-2">
                        <Input
                          data-testid="input-dest-cpf-cnpj"
                          value={formatCPFouCNPJ(nfeForm.dest_cpf_cnpj)}
                          onChange={(e) => setNfeForm(prev => ({ ...prev, dest_cpf_cnpj: e.target.value.replace(/\D/g, "") }))}
                          placeholder="Digite o CPF ou CNPJ"
                        />
                        <Button 
                          type="button" 
                          variant="outline" 
                          size="icon"
                          onClick={() => consultarCnpj(nfeForm.dest_cpf_cnpj, false)}
                          disabled={consultandoCnpj}
                        >
                          {consultandoCnpj ? <Loader2 className="animate-spin" size={16} /> : <Search size={16} />}
                        </Button>
                      </div>
                    </div>
                    <div className="md:col-span-2">
                      <Label>Razão Social / Nome *</Label>
                      <Input
                        data-testid="input-dest-razao"
                        value={nfeForm.dest_razao_social}
                        onChange={(e) => setNfeForm(prev => ({ ...prev, dest_razao_social: e.target.value }))}
                        placeholder="Nome ou Razão Social"
                      />
                    </div>
                    <div>
                      <Label>Inscrição Estadual</Label>
                      <Input
                        value={nfeForm.dest_ie}
                        onChange={(e) => setNfeForm(prev => ({ ...prev, dest_ie: e.target.value }))}
                        placeholder="IE (se houver)"
                      />
                    </div>
                    <div>
                      <Label>E-mail</Label>
                      <Input
                        type="email"
                        value={nfeForm.dest_email}
                        onChange={(e) => setNfeForm(prev => ({ ...prev, dest_email: e.target.value }))}
                        placeholder="email@exemplo.com"
                      />
                    </div>
                    <div>
                      <Label>Telefone</Label>
                      <Input
                        value={formatTelefone(nfeForm.dest_telefone)}
                        onChange={(e) => setNfeForm(prev => ({ ...prev, dest_telefone: e.target.value.replace(/\D/g, "") }))}
                        placeholder="(00) 00000-0000"
                      />
                    </div>
                  </div>
                  
                  {/* Endereço */}
                  <div className="border-t pt-4 mt-4">
                    <h4 className="font-medium mb-3">Endereço</h4>
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                      <div>
                        <Label>CEP *</Label>
                        <div className="flex gap-2">
                          <Input
                            value={formatCEP(nfeForm.dest_cep)}
                            onChange={(e) => setNfeForm(prev => ({ ...prev, dest_cep: e.target.value.replace(/\D/g, "") }))}
                            onBlur={() => consultarCep(nfeForm.dest_cep, false)}
                            placeholder="00000-000"
                          />
                          {consultandoCep && <Loader2 className="animate-spin" size={16} />}
                        </div>
                      </div>
                      <div className="md:col-span-2">
                        <Label>Logradouro *</Label>
                        <Input
                          value={nfeForm.dest_logradouro}
                          onChange={(e) => setNfeForm(prev => ({ ...prev, dest_logradouro: e.target.value }))}
                          placeholder="Rua, Avenida, etc."
                        />
                      </div>
                      <div>
                        <Label>Número *</Label>
                        <Input
                          value={nfeForm.dest_numero}
                          onChange={(e) => setNfeForm(prev => ({ ...prev, dest_numero: e.target.value }))}
                          placeholder="Nº"
                        />
                      </div>
                      <div>
                        <Label>Complemento</Label>
                        <Input
                          value={nfeForm.dest_complemento}
                          onChange={(e) => setNfeForm(prev => ({ ...prev, dest_complemento: e.target.value }))}
                          placeholder="Apto, Sala, etc."
                        />
                      </div>
                      <div>
                        <Label>Bairro *</Label>
                        <Input
                          value={nfeForm.dest_bairro}
                          onChange={(e) => setNfeForm(prev => ({ ...prev, dest_bairro: e.target.value }))}
                        />
                      </div>
                      <div>
                        <Label>Cidade *</Label>
                        <Input
                          value={nfeForm.dest_cidade}
                          onChange={(e) => setNfeForm(prev => ({ ...prev, dest_cidade: e.target.value }))}
                        />
                      </div>
                      <div>
                        <Label>UF *</Label>
                        <Input
                          value={nfeForm.dest_uf}
                          onChange={(e) => setNfeForm(prev => ({ ...prev, dest_uf: e.target.value.toUpperCase() }))}
                          maxLength={2}
                          placeholder="UF"
                        />
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Dados da Nota */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg flex items-center gap-2">
                    <FileText size={20} />
                    Dados da Nota
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <Label>Natureza da Operação *</Label>
                      <Select 
                        value={nfeForm.natureza_operacao}
                        onValueChange={(value) => setNfeForm(prev => ({ ...prev, natureza_operacao: value }))}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {naturezasOperacao.map(nat => (
                            <SelectItem key={nat} value={nat}>{nat}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label>Forma de Pagamento *</Label>
                      <Select 
                        value={nfeForm.forma_pagamento}
                        onValueChange={(value) => setNfeForm(prev => ({ ...prev, forma_pagamento: value }))}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {formasPagamento.map(fp => (
                            <SelectItem key={fp.value} value={fp.value}>{fp.label}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label>Consumidor Final</Label>
                      <Select 
                        value={nfeForm.consumidor_final}
                        onValueChange={(value) => setNfeForm(prev => ({ ...prev, consumidor_final: value }))}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="0">Não</SelectItem>
                          <SelectItem value="1">Sim</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Itens */}
              <Card>
                <CardHeader className="flex flex-row items-center justify-between">
                  <CardTitle className="text-lg flex items-center gap-2">
                    <Package size={20} />
                    Itens da Nota
                  </CardTitle>
                  <Button onClick={() => setShowAddItem(true)} data-testid="btn-add-item">
                    <Plus size={16} className="mr-2" />
                    Adicionar Item
                  </Button>
                </CardHeader>
                <CardContent>
                  {nfeItens.length === 0 ? (
                    <p className="text-gray-500 text-center py-8">Nenhum item adicionado. Clique em "Adicionar Item" para começar.</p>
                  ) : (
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="text-left p-2">Código</th>
                            <th className="text-left p-2">Descrição</th>
                            <th className="text-center p-2">Qtd</th>
                            <th className="text-right p-2">V. Unit.</th>
                            <th className="text-right p-2">V. Total</th>
                            <th className="text-center p-2">Ações</th>
                          </tr>
                        </thead>
                        <tbody>
                          {nfeItens.map((item, index) => (
                            <tr key={index} className="border-b">
                              <td className="p-2">{item.codigo}</td>
                              <td className="p-2">{item.descricao}</td>
                              <td className="p-2 text-center">{item.quantidade}</td>
                              <td className="p-2 text-right">{formatCurrency(item.valor_unitario)}</td>
                              <td className="p-2 text-right font-medium">{formatCurrency(item.valor_total)}</td>
                              <td className="p-2 text-center">
                                <Button variant="ghost" size="sm" onClick={() => removerItem(index)}>
                                  <Trash2 size={14} className="text-red-500" />
                                </Button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Totais e Ações */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Totais e Valores Adicionais</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                    <div>
                      <Label>Frete (R$)</Label>
                      <Input
                        value={nfeForm.valor_frete}
                        onChange={(e) => setNfeForm(prev => ({ ...prev, valor_frete: e.target.value }))}
                      />
                    </div>
                    <div>
                      <Label>Seguro (R$)</Label>
                      <Input
                        value={nfeForm.valor_seguro}
                        onChange={(e) => setNfeForm(prev => ({ ...prev, valor_seguro: e.target.value }))}
                      />
                    </div>
                    <div>
                      <Label>Desconto (R$)</Label>
                      <Input
                        value={nfeForm.valor_desconto}
                        onChange={(e) => setNfeForm(prev => ({ ...prev, valor_desconto: e.target.value }))}
                      />
                    </div>
                    <div>
                      <Label>Outras Desp. (R$)</Label>
                      <Input
                        value={nfeForm.valor_outros}
                        onChange={(e) => setNfeForm(prev => ({ ...prev, valor_outros: e.target.value }))}
                      />
                    </div>
                    <div className="flex flex-col justify-end">
                      <Label className="text-xs text-gray-500">Total Produtos</Label>
                      <div className="text-xl font-bold text-gray-800">{formatCurrency(valorProdutos)}</div>
                    </div>
                  </div>
                  
                  <div className="border-t pt-4">
                    <Label>Informações Complementares</Label>
                    <Textarea
                      value={nfeForm.info_complementar}
                      onChange={(e) => setNfeForm(prev => ({ ...prev, info_complementar: e.target.value }))}
                      placeholder="Informações adicionais que aparecerão na nota fiscal..."
                      rows={3}
                    />
                  </div>
                  
                  <div className="flex items-center justify-between border-t pt-4">
                    <div className="text-2xl font-bold text-green-600">
                      Total da Nota: {formatCurrency(valorTotal)}
                    </div>
                    <Button 
                      onClick={emitirNfe} 
                      disabled={emitindo || nfeItens.length === 0}
                      className="bg-blue-600 hover:bg-blue-700"
                      data-testid="btn-emitir-nfe"
                    >
                      {emitindo ? (
                        <Loader2 className="animate-spin mr-2" size={16} />
                      ) : (
                        <Send className="mr-2" size={16} />
                      )}
                      Emitir NF-e
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </>
          )}

          {/* Formulário NFS-e */}
          {tipoNota === "nfse" && (
            <>
              {/* Tomador */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg flex items-center gap-2">
                    <User size={20} />
                    Tomador do Serviço
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Buscar do cadastro */}
                  <div className="flex gap-2 items-end">
                    <div className="flex-1">
                      <Label>Buscar do Cadastro</Label>
                      <Select onValueChange={(value) => selecionarCadastro(value, true)}>
                        <SelectTrigger>
                          <SelectValue placeholder="Selecione um cliente/fornecedor" />
                        </SelectTrigger>
                        <SelectContent>
                          {cadastros.map(c => (
                            <SelectItem key={c.id} value={c.id}>
                              {c.nome_razao} - {formatCPFouCNPJ(c.cpf_cnpj || "")}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <Label>CPF/CNPJ *</Label>
                      <div className="flex gap-2">
                        <Input
                          data-testid="input-tomador-cpf-cnpj"
                          value={formatCPFouCNPJ(nfseForm.tomador_cpf_cnpj)}
                          onChange={(e) => setNfseForm(prev => ({ ...prev, tomador_cpf_cnpj: e.target.value.replace(/\D/g, "") }))}
                          placeholder="Digite o CPF ou CNPJ"
                        />
                        <Button 
                          type="button" 
                          variant="outline" 
                          size="icon"
                          onClick={() => consultarCnpj(nfseForm.tomador_cpf_cnpj, true)}
                          disabled={consultandoCnpj}
                        >
                          {consultandoCnpj ? <Loader2 className="animate-spin" size={16} /> : <Search size={16} />}
                        </Button>
                      </div>
                    </div>
                    <div className="md:col-span-2">
                      <Label>Razão Social / Nome *</Label>
                      <Input
                        data-testid="input-tomador-razao"
                        value={nfseForm.tomador_razao_social}
                        onChange={(e) => setNfseForm(prev => ({ ...prev, tomador_razao_social: e.target.value }))}
                        placeholder="Nome ou Razão Social"
                      />
                    </div>
                    <div>
                      <Label>Inscrição Estadual</Label>
                      <Input
                        value={nfseForm.tomador_ie}
                        onChange={(e) => setNfseForm(prev => ({ ...prev, tomador_ie: e.target.value }))}
                      />
                    </div>
                    <div>
                      <Label>E-mail</Label>
                      <Input
                        type="email"
                        value={nfseForm.tomador_email}
                        onChange={(e) => setNfseForm(prev => ({ ...prev, tomador_email: e.target.value }))}
                      />
                    </div>
                    <div>
                      <Label>Telefone</Label>
                      <Input
                        value={formatTelefone(nfseForm.tomador_telefone)}
                        onChange={(e) => setNfseForm(prev => ({ ...prev, tomador_telefone: e.target.value.replace(/\D/g, "") }))}
                      />
                    </div>
                  </div>
                  
                  {/* Endereço */}
                  <div className="border-t pt-4 mt-4">
                    <h4 className="font-medium mb-3">Endereço</h4>
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                      <div>
                        <Label>CEP *</Label>
                        <div className="flex gap-2">
                          <Input
                            value={formatCEP(nfseForm.tomador_cep)}
                            onChange={(e) => setNfseForm(prev => ({ ...prev, tomador_cep: e.target.value.replace(/\D/g, "") }))}
                            onBlur={() => consultarCep(nfseForm.tomador_cep, true)}
                          />
                          {consultandoCep && <Loader2 className="animate-spin" size={16} />}
                        </div>
                      </div>
                      <div className="md:col-span-2">
                        <Label>Logradouro *</Label>
                        <Input
                          value={nfseForm.tomador_logradouro}
                          onChange={(e) => setNfseForm(prev => ({ ...prev, tomador_logradouro: e.target.value }))}
                        />
                      </div>
                      <div>
                        <Label>Número *</Label>
                        <Input
                          value={nfseForm.tomador_numero}
                          onChange={(e) => setNfseForm(prev => ({ ...prev, tomador_numero: e.target.value }))}
                        />
                      </div>
                      <div>
                        <Label>Complemento</Label>
                        <Input
                          value={nfseForm.tomador_complemento}
                          onChange={(e) => setNfseForm(prev => ({ ...prev, tomador_complemento: e.target.value }))}
                        />
                      </div>
                      <div>
                        <Label>Bairro *</Label>
                        <Input
                          value={nfseForm.tomador_bairro}
                          onChange={(e) => setNfseForm(prev => ({ ...prev, tomador_bairro: e.target.value }))}
                        />
                      </div>
                      <div>
                        <Label>Cidade *</Label>
                        <Input
                          value={nfseForm.tomador_cidade}
                          onChange={(e) => setNfseForm(prev => ({ ...prev, tomador_cidade: e.target.value }))}
                        />
                      </div>
                      <div>
                        <Label>UF *</Label>
                        <Input
                          value={nfseForm.tomador_uf}
                          onChange={(e) => setNfseForm(prev => ({ ...prev, tomador_uf: e.target.value.toUpperCase() }))}
                          maxLength={2}
                        />
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Dados do Serviço */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg flex items-center gap-2">
                    <FileText size={20} />
                    Dados do Serviço
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <Label>Código do Serviço (LC 116/2003) *</Label>
                      <Select 
                        value={nfseForm.item_lista_servico}
                        onValueChange={(value) => setNfseForm(prev => ({ 
                          ...prev, 
                          item_lista_servico: value,
                          codigo_tributario_municipio: value.replace(".", "")
                        }))}
                      >
                        <SelectTrigger data-testid="select-codigo-servico">
                          <SelectValue placeholder="Selecione o código do serviço" />
                        </SelectTrigger>
                        <SelectContent>
                          {codigosServico.map(cs => (
                            <SelectItem key={cs.codigo} value={cs.codigo}>
                              {cs.codigo} - {cs.descricao}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label>CNAE (opcional)</Label>
                      <Input
                        value={nfseForm.codigo_cnae}
                        onChange={(e) => setNfseForm(prev => ({ ...prev, codigo_cnae: e.target.value }))}
                        placeholder="Ex: 4120400"
                      />
                    </div>
                  </div>
                  
                  <div>
                    <Label>Discriminação do Serviço *</Label>
                    <Textarea
                      data-testid="textarea-discriminacao"
                      value={nfseForm.discriminacao}
                      onChange={(e) => setNfseForm(prev => ({ ...prev, discriminacao: e.target.value }))}
                      placeholder="Descreva detalhadamente o serviço prestado..."
                      rows={4}
                    />
                  </div>
                </CardContent>
              </Card>

              {/* Valores */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Valores</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div>
                      <Label>Valor dos Serviços *</Label>
                      <Input
                        data-testid="input-valor-servicos"
                        value={nfseForm.valor_servicos ? formatCurrency(parseCurrency(nfseForm.valor_servicos)) : ""}
                        onChange={(e) => setNfseForm(prev => ({ ...prev, valor_servicos: e.target.value }))}
                        placeholder="R$ 0,00"
                      />
                    </div>
                    <div>
                      <Label>Deduções (R$)</Label>
                      <Input
                        value={nfseForm.valor_deducoes}
                        onChange={(e) => setNfseForm(prev => ({ ...prev, valor_deducoes: e.target.value }))}
                      />
                    </div>
                    <div>
                      <Label>Alíquota ISS (%)</Label>
                      <Input
                        value={nfseForm.aliquota_iss}
                        onChange={(e) => setNfseForm(prev => ({ ...prev, aliquota_iss: e.target.value }))}
                        placeholder="Ex: 5"
                      />
                    </div>
                    <div className="flex items-end gap-2">
                      <div className="flex items-center gap-2">
                        <input
                          type="checkbox"
                          id="iss_retido"
                          checked={nfseForm.iss_retido}
                          onChange={(e) => setNfseForm(prev => ({ ...prev, iss_retido: e.target.checked }))}
                          className="h-4 w-4"
                        />
                        <Label htmlFor="iss_retido">ISS Retido</Label>
                      </div>
                    </div>
                  </div>
                  
                  <div className="border-t pt-4">
                    <h4 className="font-medium mb-3">Retenções (opcional)</h4>
                    <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
                      <div>
                        <Label className="text-xs">PIS (R$)</Label>
                        <Input
                          value={nfseForm.valor_pis}
                          onChange={(e) => setNfseForm(prev => ({ ...prev, valor_pis: e.target.value }))}
                        />
                      </div>
                      <div>
                        <Label className="text-xs">COFINS (R$)</Label>
                        <Input
                          value={nfseForm.valor_cofins}
                          onChange={(e) => setNfseForm(prev => ({ ...prev, valor_cofins: e.target.value }))}
                        />
                      </div>
                      <div>
                        <Label className="text-xs">INSS (R$)</Label>
                        <Input
                          value={nfseForm.valor_inss}
                          onChange={(e) => setNfseForm(prev => ({ ...prev, valor_inss: e.target.value }))}
                        />
                      </div>
                      <div>
                        <Label className="text-xs">IR (R$)</Label>
                        <Input
                          value={nfseForm.valor_ir}
                          onChange={(e) => setNfseForm(prev => ({ ...prev, valor_ir: e.target.value }))}
                        />
                      </div>
                      <div>
                        <Label className="text-xs">CSLL (R$)</Label>
                        <Input
                          value={nfseForm.valor_csll}
                          onChange={(e) => setNfseForm(prev => ({ ...prev, valor_csll: e.target.value }))}
                        />
                      </div>
                      <div>
                        <Label className="text-xs">Outras (R$)</Label>
                        <Input
                          value={nfseForm.outras_retencoes}
                          onChange={(e) => setNfseForm(prev => ({ ...prev, outras_retencoes: e.target.value }))}
                        />
                      </div>
                    </div>
                  </div>
                  
                  <div className="border-t pt-4">
                    <Label>Informações Complementares</Label>
                    <Textarea
                      value={nfseForm.info_complementar}
                      onChange={(e) => setNfseForm(prev => ({ ...prev, info_complementar: e.target.value }))}
                      placeholder="Informações adicionais..."
                      rows={3}
                    />
                  </div>
                  
                  <div className="flex items-center justify-between border-t pt-4">
                    <div>
                      <div className="text-sm text-gray-500">Valor ISS: {formatCurrency(valorIss)}</div>
                      <div className="text-2xl font-bold text-green-600">
                        Valor Líquido: {formatCurrency(valorLiquido)}
                      </div>
                    </div>
                    <Button 
                      onClick={emitirNfse} 
                      disabled={emitindo}
                      className="bg-green-600 hover:bg-green-700"
                      data-testid="btn-emitir-nfse"
                    >
                      {emitindo ? (
                        <Loader2 className="animate-spin mr-2" size={16} />
                      ) : (
                        <Send className="mr-2" size={16} />
                      )}
                      Emitir NFS-e
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </>
          )}
        </TabsContent>

        {/* Tab: Notas Emitidas */}
        <TabsContent value="emitidas" className="space-y-6 mt-6">
          {/* Filtros */}
          <Card>
            <CardContent className="pt-6">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div>
                  <Label>Tipo de Nota</Label>
                  <Select value={filterTipo} onValueChange={setFilterTipo}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="todos">Todas</SelectItem>
                      <SelectItem value="nfe">NF-e (Produtos)</SelectItem>
                      <SelectItem value="nfse">NFS-e (Serviços)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>CNPJ Emitente</Label>
                  <Select value={filterCertificado} onValueChange={setFilterCertificado}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="todos">Todos</SelectItem>
                      {certificados.map(cert => (
                        <SelectItem key={cert.id} value={cert.id}>
                          {cert.razao_social}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Status</Label>
                  <Select value={filterStatus} onValueChange={setFilterStatus}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="todos">Todos</SelectItem>
                      <SelectItem value="autorizada">Autorizada</SelectItem>
                      <SelectItem value="rascunho">Rascunho</SelectItem>
                      <SelectItem value="pendente">Pendente</SelectItem>
                      <SelectItem value="rejeitada">Rejeitada</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="flex items-end">
                  <Button variant="outline" onClick={fetchNotasEmitidas} className="w-full">
                    <Search size={16} className="mr-2" />
                    Buscar
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Lista de Notas */}
          <Card>
            <CardContent className="pt-6">
              {notasEmitidas.length === 0 ? (
                <p className="text-gray-500 text-center py-8">Nenhuma nota fiscal encontrada.</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="text-left p-3">Tipo</th>
                        <th className="text-left p-3">Número</th>
                        <th className="text-left p-3">Destinatário/Tomador</th>
                        <th className="text-right p-3">Valor</th>
                        <th className="text-center p-3">Status</th>
                        <th className="text-left p-3">Data</th>
                        <th className="text-center p-3">Ações</th>
                      </tr>
                    </thead>
                    <tbody>
                      {notasEmitidas.map(nota => (
                        <tr key={nota.id} className="border-b hover:bg-gray-50">
                          <td className="p-3">
                            <span className={`px-2 py-1 rounded text-xs font-medium ${nota.tipo === "nfe" ? "bg-blue-100 text-blue-800" : "bg-green-100 text-green-800"}`}>
                              {nota.tipo?.toUpperCase()}
                            </span>
                          </td>
                          <td className="p-3 font-mono">{nota.numero}</td>
                          <td className="p-3">
                            <div className="font-medium">{nota.dest_razao_social || nota.tomador_razao_social}</div>
                            <div className="text-xs text-gray-500">{formatCPFouCNPJ(nota.dest_cpf_cnpj || nota.tomador_cpf_cnpj || "")}</div>
                          </td>
                          <td className="p-3 text-right font-medium">
                            {formatCurrency(nota.valor_total || nota.valor_servicos || 0)}
                          </td>
                          <td className="p-3 text-center">
                            {getStatusBadge(nota.status)}
                          </td>
                          <td className="p-3 text-gray-500">
                            {nota.created_at?.substring(0, 10)}
                          </td>
                          <td className="p-3">
                            <div className="flex items-center justify-center gap-1">
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => setShowNotaDetail(nota)}
                                title="Ver detalhes"
                              >
                                <Eye size={14} />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleDownload(nota.id, "pdf")}
                                title="Download PDF"
                              >
                                <FileDown size={14} className="text-red-500" />
                              </Button>
                              {nota.xml_base64 && (
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => handleDownload(nota.id, "xml")}
                                  title="Download XML"
                                >
                                  <Download size={14} className="text-blue-500" />
                                </Button>
                              )}
                              {(nota.status === "rascunho" || nota.status === "rejeitada") && (
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => excluirNota(nota.id)}
                                  title="Excluir"
                                >
                                  <Trash2 size={14} className="text-red-500" />
                                </Button>
                              )}
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Modal: Adicionar Item NF-e */}
      <Dialog open={showAddItem} onOpenChange={setShowAddItem}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Adicionar Item</DialogTitle>
            <DialogDescription>Selecione um produto ou preencha manualmente</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>Selecionar Produto Cadastrado</Label>
              <Select onValueChange={selecionarProduto}>
                <SelectTrigger>
                  <SelectValue placeholder="Buscar produto..." />
                </SelectTrigger>
                <SelectContent>
                  {produtos.filter(p => p.status === "ativo").map(p => (
                    <SelectItem key={p.id} value={p.id}>
                      {p.codigo_interno ? `${p.codigo_interno} - ` : ""}{p.descricao} - {formatCurrency(p.preco_venda || 0)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Código *</Label>
                <Input
                  value={itemForm.codigo}
                  onChange={(e) => setItemForm(prev => ({ ...prev, codigo: e.target.value }))}
                />
              </div>
              <div>
                <Label>NCM *</Label>
                <Input
                  value={itemForm.ncm}
                  onChange={(e) => setItemForm(prev => ({ ...prev, ncm: e.target.value }))}
                  maxLength={8}
                />
              </div>
            </div>
            
            <div>
              <Label>Descrição *</Label>
              <Input
                value={itemForm.descricao}
                onChange={(e) => setItemForm(prev => ({ ...prev, descricao: e.target.value }))}
              />
            </div>
            
            <div className="grid grid-cols-3 gap-4">
              <div>
                <Label>CFOP *</Label>
                <Select value={itemForm.cfop} onValueChange={(value) => setItemForm(prev => ({ ...prev, cfop: value }))}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {cfops.map(cfop => (
                      <SelectItem key={cfop.codigo} value={cfop.codigo}>
                        {cfop.codigo} - {cfop.descricao.substring(0, 30)}...
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Unidade *</Label>
                <Input
                  value={itemForm.unidade}
                  onChange={(e) => setItemForm(prev => ({ ...prev, unidade: e.target.value.toUpperCase() }))}
                  maxLength={6}
                />
              </div>
              <div>
                <Label>Quantidade *</Label>
                <Input
                  type="number"
                  value={itemForm.quantidade}
                  onChange={(e) => setItemForm(prev => ({ ...prev, quantidade: e.target.value }))}
                  min="0.01"
                  step="0.01"
                />
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Valor Unitário *</Label>
                <Input
                  value={itemForm.valor_unitario}
                  onChange={(e) => setItemForm(prev => ({ ...prev, valor_unitario: e.target.value }))}
                  placeholder="R$ 0,00"
                />
              </div>
              <div className="flex flex-col justify-end">
                <Label className="text-xs text-gray-500">Valor Total</Label>
                <div className="text-lg font-bold">
                  {formatCurrency(parseCurrency(itemForm.valor_unitario) * (parseFloat(itemForm.quantidade) || 0))}
                </div>
              </div>
            </div>
            
            <div className="border-t pt-4">
              <h4 className="font-medium mb-3">Tributação</h4>
              <div className="grid grid-cols-4 gap-4">
                <div>
                  <Label className="text-xs">ICMS (%)</Label>
                  <Input
                    value={itemForm.aliquota_icms}
                    onChange={(e) => setItemForm(prev => ({ ...prev, aliquota_icms: e.target.value }))}
                  />
                </div>
                <div>
                  <Label className="text-xs">PIS (%)</Label>
                  <Input
                    value={itemForm.aliquota_pis}
                    onChange={(e) => setItemForm(prev => ({ ...prev, aliquota_pis: e.target.value }))}
                  />
                </div>
                <div>
                  <Label className="text-xs">COFINS (%)</Label>
                  <Input
                    value={itemForm.aliquota_cofins}
                    onChange={(e) => setItemForm(prev => ({ ...prev, aliquota_cofins: e.target.value }))}
                  />
                </div>
                <div>
                  <Label className="text-xs">IPI (%)</Label>
                  <Input
                    value={itemForm.aliquota_ipi}
                    onChange={(e) => setItemForm(prev => ({ ...prev, aliquota_ipi: e.target.value }))}
                  />
                </div>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowAddItem(false)}>Cancelar</Button>
            <Button 
              onClick={adicionarItem}
              disabled={!itemForm.codigo || !itemForm.descricao || !itemForm.valor_unitario}
            >
              Adicionar Item
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Modal: Detalhes da Nota */}
      <Dialog open={!!showNotaDetail} onOpenChange={() => setShowNotaDetail(null)}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {showNotaDetail?.tipo?.toUpperCase()} - Nº {showNotaDetail?.numero}
            </DialogTitle>
          </DialogHeader>
          {showNotaDetail && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-xs text-gray-500">Status</Label>
                  <div>{getStatusBadge(showNotaDetail.status)}</div>
                </div>
                <div>
                  <Label className="text-xs text-gray-500">Data de Emissão</Label>
                  <div>{showNotaDetail.created_at?.substring(0, 10)}</div>
                </div>
              </div>
              
              <div className="border-t pt-4">
                <h4 className="font-medium mb-2">Emitente</h4>
                <p>{showNotaDetail.razao_social_emitente}</p>
                <p className="text-sm text-gray-500">CNPJ: {formatCPFouCNPJ(showNotaDetail.cnpj_emitente)}</p>
              </div>
              
              <div className="border-t pt-4">
                <h4 className="font-medium mb-2">{showNotaDetail.tipo === "nfe" ? "Destinatário" : "Tomador"}</h4>
                <p>{showNotaDetail.dest_razao_social || showNotaDetail.tomador_razao_social}</p>
                <p className="text-sm text-gray-500">
                  CPF/CNPJ: {formatCPFouCNPJ(showNotaDetail.dest_cpf_cnpj || showNotaDetail.tomador_cpf_cnpj || "")}
                </p>
              </div>
              
              {showNotaDetail.tipo === "nfse" && showNotaDetail.discriminacao && (
                <div className="border-t pt-4">
                  <h4 className="font-medium mb-2">Discriminação do Serviço</h4>
                  <p className="text-sm whitespace-pre-wrap">{showNotaDetail.discriminacao}</p>
                </div>
              )}
              
              <div className="border-t pt-4">
                <h4 className="font-medium mb-2">Valor Total</h4>
                <p className="text-2xl font-bold text-green-600">
                  {formatCurrency(showNotaDetail.valor_total || showNotaDetail.valor_servicos || 0)}
                </p>
              </div>
              
              {showNotaDetail.mensagem && (
                <div className="border-t pt-4">
                  <h4 className="font-medium mb-2">Mensagem</h4>
                  <p className="text-sm text-gray-600">{showNotaDetail.mensagem}</p>
                </div>
              )}
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => handleDownload(showNotaDetail?.id, "pdf")}>
              <FileDown size={16} className="mr-2" />
              Download PDF
            </Button>
            {showNotaDetail?.xml_base64 && (
              <Button variant="outline" onClick={() => handleDownload(showNotaDetail?.id, "xml")}>
                <Download size={16} className="mr-2" />
                Download XML
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
