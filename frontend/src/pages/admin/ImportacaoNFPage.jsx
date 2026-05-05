import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { API } from "@/App";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { MaskedDateInput } from "@/components/MaskedDateInput";
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
  FileText, 
  Plus, 
  Settings,
  Download,
  RefreshCw,
  Trash2,
  Eye,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Upload,
  Building2,
  ShieldCheck,
  Loader2,
  FileDown,
  CreditCard,
  Clock,
  Timer,
  Ban,
  Pencil,
  Plug
} from "lucide-react";
import { formatCPFouCNPJ } from "@/utils/masks";

// Componente de Cronômetro
function Cronometro({ bloqueadoAte, onExpire }) {
  const [tempoRestante, setTempoRestante] = useState(null);

  useEffect(() => {
    if (!bloqueadoAte) {
      setTempoRestante(null);
      return;
    }

    const calcularTempo = () => {
      const agora = new Date();
      const fim = new Date(bloqueadoAte);
      const diff = fim - agora;
      
      if (diff <= 0) {
        setTempoRestante(null);
        if (onExpire) onExpire();
        return null;
      }
      
      const minutos = Math.floor(diff / 60000);
      const segundos = Math.floor((diff % 60000) / 1000);
      return { minutos, segundos, total: diff };
    };

    setTempoRestante(calcularTempo());
    
    const interval = setInterval(() => {
      const tempo = calcularTempo();
      if (!tempo) {
        clearInterval(interval);
      } else {
        setTempoRestante(tempo);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [bloqueadoAte, onExpire]);

  if (!tempoRestante) return null;

  return (
    <div className="flex items-center gap-2 px-3 py-2 bg-red-100 border border-red-300 rounded-lg text-red-800">
      <Timer size={16} className="animate-pulse" />
      <span className="font-mono font-bold">
        {String(tempoRestante.minutos).padStart(2, '0')}:{String(tempoRestante.segundos).padStart(2, '0')}
      </span>
      <span className="text-xs">para desbloquear</span>
    </div>
  );
}

export default function ImportacaoNFPage() {
  const [activeTab, setActiveTab] = useState("notas");
  const [tipoNota, setTipoNota] = useState("nfe"); // "nfe" ou "nfse"
  const [certificados, setCertificados] = useState([]);
  const [nfesImportadas, setNfesImportadas] = useState([]);
  const [nfsesImportadas, setNfsesImportadas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [importando, setImportando] = useState(false);
  const [importandoCertId, setImportandoCertId] = useState(null);
  const [showAddCertificado, setShowAddCertificado] = useState(false);
  const [showNFeDetail, setShowNFeDetail] = useState(null);
  const [deleteCertificadoId, setDeleteCertificadoId] = useState(null);
  const [editCertificado, setEditCertificado] = useState(null);
  const [editForm, setEditForm] = useState({
    razao_social: "",
    uf: "SP",
    ambiente: "producao",
    inscricao_municipal: "",
    url_nfse: "",
  });
  const [editLoading, setEditLoading] = useState(false);
  const [formLoading, setFormLoading] = useState(false);
  const [testandoConexaoId, setTestandoConexaoId] = useState(null);
  const [selectedCertificado, setSelectedCertificado] = useState("todos");
  const [selectedStatus, setSelectedStatus] = useState("todos");
  
  // Estados para importação manual
  const [centrosCusto, setCentrosCusto] = useState([]);
  const [planoContas, setPlanoContas] = useState([]);
  const [importandoManual, setImportandoManual] = useState(false);
  const [manualForm, setManualForm] = useState({
    tipo_nota: "nfe",
    numero_nota: "",
    serie: "1",
    chave_acesso: "",
    data_emissao: new Date().toISOString().split("T")[0],
    cnpj_emitente: "",
    razao_social_emitente: "",
    uf_emitente: "",
    cnpj_destinatario: "",
    razao_social_destinatario: "",
    valor_total: "",
    valor_produtos: "",
    valor_servicos: "",
    valor_frete: "",
    valor_desconto: "",
    centro_custo_id: "",
    centro_custo_nome: "",
    plano_conta_id: "",
    plano_conta_nome: "",
    xml_base64: "",
    pdf_base64: "",
    observacoes: ""
  });
  const [xmlFileName, setXmlFileName] = useState("");
  const [pdfFileName, setPdfFileName] = useState("");
  const [extractingXml, setExtractingXml] = useState(false);
  const [xmlItens, setXmlItens] = useState([]);

  const [certForm, setCertForm] = useState({
    cnpj: "",
    razao_social: "",
    uf: "SP",
    ambiente: "producao",
    certificado_base64: "",
    senha_certificado: "",
    certificado_nome: "",
    inscricao_municipal: "",
    url_nfse: ""
  });

  const ufs = [
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", 
    "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", 
    "SP", "SE", "TO"
  ];

  useEffect(() => {
    fetchData();
  }, [selectedCertificado, selectedStatus, tipoNota]);

  const fetchData = async () => {
    try {
      const [certsRes, nfesRes, nfsesRes, centrosRes, planoRes] = await Promise.all([
        axios.get(`${API}/nfe/certificados`).catch((e) => { console.error("Erro certificados:", e); return { data: [] }; }),
        axios.get(`${API}/nfe/importadas`, {
          params: {
            certificado_id: selectedCertificado !== "todos" ? selectedCertificado : undefined,
            status: selectedStatus !== "todos" ? selectedStatus : undefined
          }
        }).catch((e) => { console.error("Erro NF-e:", e); return { data: [] }; }),
        axios.get(`${API}/nfse/importadas`, {
          params: {
            certificado_id: selectedCertificado !== "todos" ? selectedCertificado : undefined,
            status: selectedStatus !== "todos" ? selectedStatus : undefined
          }
        }).catch(() => ({ data: [] })),
        axios.get(`${API}/admin/centros-custo`).catch(() => ({ data: [] })),
        axios.get(`${API}/admin/plano-contas`).catch(() => ({ data: [] }))
      ]);
      setCertificados(certsRes.data);
      setNfesImportadas(nfesRes.data);
      setNfsesImportadas(nfsesRes.data || []);
      setCentrosCusto(centrosRes.data || []);
      setPlanoContas(planoRes.data || []);
    } catch (error) {
      console.error("Erro ao carregar dados:", error);
    } finally {
      setLoading(false);
    }
  };

  // Função para extrair dados do XML automaticamente
  const handleXmlExtract = async (file) => {
    if (!file) return;
    
    setExtractingXml(true);
    setXmlFileName(file.name);
    
    const reader = new FileReader();
    reader.onload = async (ev) => {
      const base64 = ev.target.result.split(",")[1];
      
      try {
        // Chamar API para extrair dados
        const response = await axios.post(`${API}/nf/extrair-xml`, {
          xml_base64: base64
        });
        
        const dados = response.data;
        
        if (dados.sucesso) {
          // Preencher o formulário com os dados extraídos
          setManualForm(prev => ({
            ...prev,
            tipo_nota: dados.tipo_nota || "nfe",
            numero_nota: dados.numero_nota || "",
            serie: dados.serie || "1",
            chave_acesso: dados.chave_acesso || "",
            data_emissao: dados.data_emissao || new Date().toISOString().split("T")[0],
            cnpj_emitente: dados.cnpj_emitente || "",
            razao_social_emitente: dados.razao_social_emitente || "",
            uf_emitente: dados.uf_emitente || "",
            cnpj_destinatario: dados.cnpj_destinatario || "",
            razao_social_destinatario: dados.razao_social_destinatario || "",
            valor_total: dados.valor_total ? dados.valor_total.toFixed(2) : "",
            valor_produtos: dados.valor_produtos ? dados.valor_produtos.toFixed(2) : "",
            valor_frete: dados.valor_frete ? dados.valor_frete.toFixed(2) : "0",
            valor_desconto: dados.valor_desconto ? dados.valor_desconto.toFixed(2) : "0",
            xml_base64: base64
          }));
          
          // Salvar itens extraídos
          if (dados.itens && dados.itens.length > 0) {
            setXmlItens(dados.itens);
          }
          
          toast.success(`Dados extraídos com sucesso! ${dados.itens?.length || 0} itens encontrados.`);
        } else {
          // Se falhou na extração, só salva o XML
          setManualForm(prev => ({...prev, xml_base64: base64}));
          toast.error(dados.erro || "Não foi possível extrair os dados do XML. Preencha manualmente.");
        }
      } catch (error) {
        console.error("Erro ao extrair XML:", error);
        // Mesmo com erro, salva o XML
        setManualForm(prev => ({...prev, xml_base64: base64}));
        toast.error("Erro ao processar XML. Preencha os campos manualmente.");
      } finally {
        setExtractingXml(false);
      }
    };
    reader.readAsDataURL(file);
  };

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    if (!file.name.endsWith('.pfx') && !file.name.endsWith('.p12')) {
      toast.error("Arquivo inválido. Selecione um certificado .pfx ou .p12");
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      const base64 = e.target.result.split(',')[1];
      setCertForm(prev => ({
        ...prev,
        certificado_base64: base64,
        certificado_nome: file.name
      }));
      toast.success("Certificado carregado!");
    };
    reader.readAsDataURL(file);
  };

  const handleAddCertificado = async (e) => {
    e.preventDefault();
    
    if (!certForm.certificado_base64) {
      toast.error("Selecione o arquivo do certificado");
      return;
    }

    setFormLoading(true);
    try {
      await axios.post(`${API}/nfe/certificados`, {
        cnpj: certForm.cnpj.replace(/\D/g, ''),
        razao_social: certForm.razao_social,
        uf: certForm.uf,
        ambiente: certForm.ambiente,
        certificado_base64: certForm.certificado_base64,
        senha_certificado: certForm.senha_certificado,
        inscricao_municipal: certForm.inscricao_municipal || null,
        url_nfse: certForm.url_nfse || null
      });
      toast.success("Certificado cadastrado com sucesso!");
      setShowAddCertificado(false);
      setCertForm({
        cnpj: "",
        razao_social: "",
        uf: "SP",
        ambiente: "producao",
        certificado_base64: "",
        senha_certificado: "",
        certificado_nome: "",
        inscricao_municipal: "",
        url_nfse: ""
      });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao cadastrar certificado");
    } finally {
      setFormLoading(false);
    }
  };

  const handleDeleteCertificado = async () => {
    if (!deleteCertificadoId) return;
    
    try {
      await axios.delete(`${API}/nfe/certificados/${deleteCertificadoId}`);
      toast.success("Certificado removido!");
      setDeleteCertificadoId(null);
      fetchData();
    } catch (error) {
      toast.error("Erro ao remover certificado");
    }
  };

  const openEditCertificado = (cert) => {
    setEditForm({
      razao_social: cert.razao_social || "",
      uf: cert.uf || "SP",
      ambiente: cert.ambiente || "producao",
      inscricao_municipal: cert.inscricao_municipal || "",
      url_nfse: cert.url_nfse || "",
    });
    setEditCertificado(cert);
  };

  const handleUpdateCertificado = async (e) => {
    e.preventDefault();
    if (!editCertificado) return;
    setEditLoading(true);
    try {
      await axios.patch(`${API}/nfe/certificados/${editCertificado.id}`, {
        razao_social: editForm.razao_social,
        uf: editForm.uf,
        ambiente: editForm.ambiente,
        inscricao_municipal: editForm.inscricao_municipal,
        url_nfse: editForm.url_nfse,
      });
      toast.success("Certificado atualizado com sucesso!");
      setEditCertificado(null);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao atualizar certificado");
    } finally {
      setEditLoading(false);
    }
  };

  // Verificar se certificado está bloqueado ou atingiu limite
  const isCertificadoBloqueado = (cert) => {
    if (cert.bloqueado_ate) {
      const bloqueio = new Date(cert.bloqueado_ate);
      if (bloqueio > new Date()) {
        return true;
      }
    }
    return false;
  };

  const getConsultasRestantes = (cert) => {
    const LIMITE_DIARIO = 3;
    const consultasHoje = cert.consultas_hoje || 0;
    return Math.max(0, LIMITE_DIARIO - consultasHoje);
  };

  const handleImportarNotas = async (certificadoId, desdeInicio = false) => {
    const cert = certificados.find(c => c.id === certificadoId);
    
    if (cert && isCertificadoBloqueado(cert)) {
      toast.error("Este certificado está bloqueado. Aguarde o cronômetro zerar.");
      return;
    }
    if (cert && getConsultasRestantes(cert) <= 0) {
      toast.error("Limite diário de 3 consultas atingido. Tente novamente amanhã.");
      return;
    }
    
    setImportando(true);
    setImportandoCertId(certificadoId);
    try {
      // Importar NF-e (SEFAZ) e NFS-e (prefeitura) em paralelo.
      // Se desdeInicio=true, NF-e ignora o cursor NSU e re-varre o histórico todo.
      const nfeUrl = desdeInicio
        ? `${API}/nfe/importar/${certificadoId}?desde_inicio=true`
        : `${API}/nfe/importar/${certificadoId}`;
      const [nfeResult, nfseResult] = await Promise.allSettled([
        axios.post(nfeUrl),
        axios.post(`${API}/nfse/importar/${certificadoId}`)
      ]);

      const empresaNome = cert?.razao_social || "Empresa";
      const sufixo = desdeInicio ? " [varredura completa]" : "";

      // Tratar resultado NF-e
      if (nfeResult.status === 'fulfilled') {
        const d = nfeResult.value.data;
        if (d.aviso) {
          toast.warning(`NF-e ${empresaNome}${sufixo}: ${d.aviso}`, { duration: 8000 });
        } else if (d.novas_nfes > 0) {
          toast.success(`${empresaNome}${sufixo}: ${d.novas_nfes} nova(s) NF-e importada(s)!`);
        } else {
          toast.info(`NF-e ${empresaNome}${sufixo}: nenhuma nova nota encontrada na SEFAZ`);
        }
      } else {
        toast.error(`NF-e ${empresaNome}: ${nfeResult.reason?.response?.data?.detail || "Erro"}`);
      }

      // Tratar resultado NFS-e (mais visível: warning/error em vez de info)
      if (nfseResult.status === 'fulfilled') {
        const d = nfseResult.value.data;
        if (d.aviso) {
          toast.warning(`NFS-e ${empresaNome}: ${d.aviso}`, { duration: 12000 });
        } else if (d.novas_nfses > 0) {
          toast.success(`${empresaNome}: ${d.novas_nfses} nova(s) NFS-e importada(s)!`);
        } else if ((d.erros || []).length > 0) {
          toast.warning(`NFS-e ${empresaNome}: ${d.erros.join(' | ')}`, { duration: 12000 });
        } else {
          toast.info(`NFS-e ${empresaNome}: nenhuma nova nota encontrada no histórico (5 anos)`);
        }
      } else {
        const errMsg = nfseResult.reason?.response?.data?.detail;
        toast.error(`NFS-e ${empresaNome}: ${errMsg || "falha na consulta ao webservice"}`);
      }

      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao importar notas");
      fetchData();
    } finally {
      setImportando(false);
      setImportandoCertId(null);
    }
  };

  // Importa NFS-e de TODOS os certificados que têm URL do webservice configurada
  const handleImportarNFSeTodos = async () => {
    const certsComUrl = certificados.filter(c => c.ativo && (c.url_nfse || "").trim());
    if (certsComUrl.length === 0) {
      toast.error("Nenhum CNPJ tem URL do webservice NFS-e configurada. Edite o cadastro do certificado para adicionar a URL.");
      return;
    }
    setImportando(true);
    let totalNovas = 0;
    let temErro = false;
    try {
      for (const cert of certsComUrl) {
        if (isCertificadoBloqueado(cert)) {
          toast.warning(`${cert.razao_social}: certificado bloqueado, ignorando.`);
          continue;
        }
        setImportandoCertId(cert.id);
        try {
          const { data } = await axios.post(`${API}/nfse/importar/${cert.id}`);
          if (data.aviso) {
            temErro = true;
            toast.warning(`${cert.razao_social}: ${data.aviso}`, { duration: 12000 });
          } else if (data.novas_nfses > 0) {
            totalNovas += data.novas_nfses;
            toast.success(`${cert.razao_social}: ${data.novas_nfses} NFS-e importada(s)!`);
          } else if ((data.erros || []).length > 0) {
            temErro = true;
            toast.warning(`${cert.razao_social}: ${data.erros.join(' | ')}`, { duration: 12000 });
          } else {
            toast.info(`${cert.razao_social}: nenhuma NFS-e nova nos últimos 90 dias`);
          }
        } catch (e) {
          temErro = true;
          toast.error(`${cert.razao_social}: ${e.response?.data?.detail || "falha na consulta"}`);
        }
      }
      if (totalNovas === 0 && !temErro) {
        toast.info("Importação concluída — nenhuma NFS-e nova encontrada para os CNPJs ativos.");
      } else if (totalNovas === 0 && temErro) {
        toast.warning("Importação concluída com avisos. Use o botão 'Testar Conexão' (ícone de plug) em cada CNPJ para diagnóstico detalhado.", { duration: 14000 });
      } else {
        toast.success(`Total: ${totalNovas} NFS-e importada(s) ao todo.`);
      }
      await fetchData();
    } finally {
      setImportando(false);
      setImportandoCertId(null);
    }
  };

  const handleTestarConexaoNfse = async (certificadoId) => {
    setTestandoConexaoId(certificadoId);
    try {
      const { data } = await axios.post(`${API}/nfse/testar-conexao/${certificadoId}`);
      if (data.ok) {
        toast.success(data.mensagem, { duration: 8000 });
      } else {
        const prefix = {
          configuracao: "Configuração",
          certificado: "Certificado",
          ssl: "SSL",
          timeout: "Timeout",
          conexao: "Conexão",
          http: "HTTP",
          soap_fault: "SOAP Fault",
          negocio: "Regra de Negócio",
          parse: "Resposta Inválida",
          mtls_rejeitado: "Certificado Rejeitado",
          inesperado: "Erro",
        }[data.etapa] || "Erro";
        toast.error(`${prefix}: ${data.mensagem}`, { duration: 12000 });
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || "Falha ao testar conexão NFS-e");
    } finally {
      setTestandoConexaoId(null);
    }
  };

  const handleCriarContaPagar = async (nfeId) => {
    try {
      const response = await axios.post(`${API}/nfe/importadas/${nfeId}/criar-conta-pagar`);
      toast.success("Conta a pagar criada com sucesso!");
      fetchData();
      setShowNFeDetail(null);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao criar conta a pagar");
    }
  };

  const handleCriarContaPagarNFSe = async (nfseId) => {
    try {
      const response = await axios.post(`${API}/nfse/importadas/${nfseId}/criar-conta-pagar`);
      toast.success("Conta a pagar criada com sucesso!");
      fetchData();
      setShowNFeDetail(null);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao criar conta a pagar");
    }
  };

  // Função para download autenticado de arquivos
  const handleDownload = async (url, filename, tipo = "application/pdf") => {
    try {
      const response = await axios.get(url, {
        responseType: 'blob',
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`
        }
      });
      
      const blob = new Blob([response.data], { type: tipo });
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);
    } catch (error) {
      console.error("Erro no download:", error);
      toast.error("Erro ao fazer download do arquivo");
    }
  };

  const handleDownloadNFeXML = (nfeId, numeroNfe) => {
    handleDownload(`${API}/nfe/importadas/${nfeId}/download-xml`, `NFe_${numeroNfe}.xml`, "application/xml");
  };

  const handleDownloadNFePDF = (nfeId, numeroNfe) => {
    handleDownload(`${API}/nfe/importadas/${nfeId}/download-pdf`, `DANFE_NFe_${numeroNfe}.pdf`, "application/pdf");
  };

  const handleDownloadNFSeXML = (nfseId, numeroNfse) => {
    handleDownload(`${API}/nfse/importadas/${nfseId}/download-xml`, `NFSe_${numeroNfse}.xml`, "application/xml");
  };

  const handleDownloadNFSePDF = (nfseId, numeroNfse) => {
    handleDownload(`${API}/nfse/importadas/${nfseId}/download-pdf`, `NFSe_${numeroNfse}.pdf`, "application/pdf");
  };

  const handleUpdateStatus = async (nfeId, status) => {
    try {
      await axios.patch(`${API}/nfe/importadas/${nfeId}/status`, { status });
      toast.success("Status atualizado!");
      fetchData();
    } catch (error) {
      toast.error("Erro ao atualizar status");
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat("pt-BR", {
      style: "currency",
      currency: "BRL"
    }).format(value || 0);
  };

  const formatDate = (dateString) => {
    if (!dateString) return "-";
    return new Date(dateString).toLocaleDateString("pt-BR");
  };

  const getStatusBadge = (status) => {
    const config = {
      nova: { label: "Nova", color: "bg-blue-100 text-blue-800 border-blue-300", icon: Clock },
      processada: { label: "Processada", color: "bg-green-100 text-green-800 border-green-300", icon: CheckCircle },
      ignorada: { label: "Ignorada", color: "bg-gray-100 text-gray-800 border-gray-300", icon: XCircle }
    };
    const { label, color, icon: Icon } = config[status] || config.nova;
    return (
      <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium border ${color}`}>
        <Icon size={12} />
        {label}
      </span>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="spinner w-12 h-12"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in" data-testid="importacao-nf-page">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title font-heading">Importação de Notas Fiscais</h1>
          <p className="text-gray-500 mt-1">Importe NF-e (Compras) e NFS-e (Serviços) da SEFAZ</p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => setActiveTab("config")}
          >
            <Settings size={18} className="mr-2" />
            Configurações
          </Button>
          {certificados.length > 0 && (
            <Button
              className="bg-[#D4A000] hover:bg-[#b88f00] text-black font-bold"
              onClick={() => {
                if (tipoNota === "nfse") {
                  handleImportarNFSeTodos();
                } else {
                  handleImportarNotas(certificados[0]?.id);
                }
              }}
              disabled={importando}
              data-testid="btn-importar-topo"
            >
              {importando ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Importando...
                </>
              ) : (
                <>
                  <Download size={18} className="mr-2" />
                  Importar {tipoNota === "nfe" ? "NF-e" : "NFS-e"}
                </>
              )}
            </Button>
          )}
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="notas" data-testid="tab-notas">
            <FileText size={16} className="mr-2" />
            Notas Importadas ({nfesImportadas.length + nfsesImportadas.length})
          </TabsTrigger>
          <TabsTrigger value="manual" data-testid="tab-manual">
            <Upload size={16} className="mr-2" />
            Importação Manual
          </TabsTrigger>
          <TabsTrigger value="config" data-testid="tab-config">
            <Settings size={16} className="mr-2" />
            CNPJs/Certificados ({certificados.length})
          </TabsTrigger>
        </TabsList>

        {/* Notas Importadas Tab */}
        <TabsContent value="notas" className="space-y-4">
          {/* Cards de Resumo */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card 
              className={`cursor-pointer transition-all ${tipoNota === "nfe" ? "ring-2 ring-blue-500 bg-blue-50" : "hover:bg-gray-50"}`}
              onClick={() => setTipoNota("nfe")}
            >
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                      <FileText className="text-blue-600" size={24} />
                    </div>
                    <div>
                      <h3 className="font-semibold text-lg">NF-e (Compras)</h3>
                      <p className="text-sm text-gray-500">Notas Fiscais de Produtos</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-3xl font-bold text-blue-600">{nfesImportadas.length}</p>
                    <p className="text-xs text-gray-500">notas importadas</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            
            <Card 
              className={`cursor-pointer transition-all ${tipoNota === "nfse" ? "ring-2 ring-green-500 bg-green-50" : "hover:bg-gray-50"}`}
              onClick={() => setTipoNota("nfse")}
            >
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                      <Building2 className="text-green-600" size={24} />
                    </div>
                    <div>
                      <h3 className="font-semibold text-lg">NFS-e (Serviços)</h3>
                      <p className="text-sm text-gray-500">Notas Fiscais de Serviços</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-3xl font-bold text-green-600">{nfsesImportadas.length}</p>
                    <p className="text-xs text-gray-500">notas importadas</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Filtros */}
          <div className="flex gap-4 items-center">
            <div className="flex-1 max-w-xs">
              <Select value={selectedCertificado} onValueChange={setSelectedCertificado}>
                <SelectTrigger>
                  <SelectValue placeholder="Filtrar por CNPJ" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="todos">Todos os CNPJs</SelectItem>
                  {certificados.map((cert) => (
                    <SelectItem key={cert.id} value={cert.id}>
                      {cert.razao_social} ({formatCPFouCNPJ(cert.cnpj)})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex-1 max-w-xs">
              <Select value={selectedStatus} onValueChange={setSelectedStatus}>
                <SelectTrigger>
                  <SelectValue placeholder="Filtrar por status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="todos">Todos os status</SelectItem>
                  <SelectItem value="nova">Novas</SelectItem>
                  <SelectItem value="processada">Processadas</SelectItem>
                  <SelectItem value="ignorada">Ignoradas</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Button variant="outline" onClick={fetchData}>
              <RefreshCw size={16} className="mr-2" />
              Atualizar
            </Button>
          </div>

          {/* Lista de NF-e ou NFS-e baseado no tipo selecionado */}
          {tipoNota === "nfe" ? (
            // Lista de NF-e (Compras)
            nfesImportadas.length > 0 ? (
            <Card>
              <CardContent className="p-0">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">NF-e</th>
                      <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Emitente</th>
                      <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Data</th>
                      <th className="px-4 py-3 text-right text-sm font-semibold text-gray-700">Valor</th>
                      <th className="px-4 py-3 text-center text-sm font-semibold text-gray-700">Status</th>
                      <th className="px-4 py-3 text-center text-sm font-semibold text-gray-700">Ações</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {nfesImportadas.map((nfe) => (
                      <tr key={nfe.id} className="hover:bg-gray-50">
                        <td className="px-4 py-3">
                          <div>
                            <span className="font-bold text-black">Nº {nfe.numero_nf}</span>
                            <p className="text-xs text-gray-500 font-mono">{nfe.chave_acesso?.slice(0, 20)}...</p>
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <div>
                            <span className="font-medium">{nfe.razao_social_emitente}</span>
                            <p className="text-xs text-gray-500">{formatCPFouCNPJ(nfe.cnpj_emitente)}</p>
                          </div>
                        </td>
                        <td className="px-4 py-3 text-gray-600">{formatDate(nfe.data_emissao)}</td>
                        <td className="px-4 py-3 text-right font-bold text-black">{formatCurrency(nfe.valor_total)}</td>
                        <td className="px-4 py-3 text-center">{getStatusBadge(nfe.status)}</td>
                        <td className="px-4 py-3">
                          <div className="flex justify-center gap-1">
                            <Button 
                              variant="ghost" 
                              size="sm"
                              onClick={() => setShowNFeDetail(nfe)}
                              title="Ver detalhes"
                            >
                              <Eye size={16} />
                            </Button>
                            <Button 
                              variant="ghost" 
                              size="sm"
                              onClick={() => handleDownloadNFeXML(nfe.id, nfe.numero_nf)}
                              title="Download XML"
                              className="text-blue-600 hover:bg-blue-50"
                            >
                              <FileDown size={16} />
                            </Button>
                            <Button 
                              variant="ghost" 
                              size="sm"
                              onClick={() => handleDownloadNFePDF(nfe.id, nfe.numero_nf)}
                              title="Download DANFE (PDF)"
                              className="text-red-600 hover:bg-red-50"
                            >
                              <FileText size={16} />
                            </Button>
                            {!nfe.conta_pagar_id && nfe.status !== "ignorada" && (
                              <Button 
                                variant="ghost" 
                                size="sm"
                                className="text-green-600 hover:bg-green-50"
                                onClick={() => handleCriarContaPagar(nfe.id)}
                                title="Criar conta a pagar"
                              >
                                <CreditCard size={16} />
                              </Button>
                            )}
                            {nfe.status === "nova" && (
                              <Button 
                                variant="ghost" 
                                size="sm"
                                className="text-gray-600 hover:bg-gray-100"
                                onClick={() => handleUpdateStatus(nfe.id, "ignorada")}
                                title="Ignorar"
                              >
                                <XCircle size={16} />
                              </Button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="py-16 text-center">
                <FileText className="mx-auto text-gray-300 mb-4" size={64} />
                <h3 className="text-lg font-bold text-gray-600 mb-2">Nenhuma NF-e importada</h3>
                <p className="text-gray-500 mb-4">
                  {certificados.length === 0 
                    ? "Configure um CNPJ com certificado para começar a importar"
                    : "Clique em 'Importar NF-e' para buscar notas de compra da SEFAZ"
                  }
                </p>
                {certificados.length === 0 && (
                  <Button 
                    className="bg-[#D4A000] hover:bg-[#b88f00] text-black"
                    onClick={() => {
                      setActiveTab("config");
                      setShowAddCertificado(true);
                    }}
                  >
                    <Plus size={18} className="mr-2" />
                    Adicionar CNPJ
                  </Button>
                )}
              </CardContent>
            </Card>
          )
          ) : (
            // Lista de NFS-e (Serviços)
            nfsesImportadas.length > 0 ? (
              <Card>
                <CardContent className="p-0">
                  <table className="w-full">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">NFS-e</th>
                        <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Prestador</th>
                        <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Serviço</th>
                        <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Data</th>
                        <th className="px-4 py-3 text-right text-sm font-semibold text-gray-700">Valor</th>
                        <th className="px-4 py-3 text-center text-sm font-semibold text-gray-700">Status</th>
                        <th className="px-4 py-3 text-center text-sm font-semibold text-gray-700">Ações</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {nfsesImportadas.map((nfse) => (
                        <tr key={nfse.id} className="hover:bg-gray-50">
                          <td className="px-4 py-3">
                            <div className="font-medium text-gray-900">Nº {nfse.numero_nfse || "-"}</div>
                            <div className="text-xs text-gray-500">Série {nfse.serie || "U"}</div>
                          </td>
                          <td className="px-4 py-3">
                            <div className="font-medium">{nfse.prestador_nome || nfse.razao_social_prestador || "-"}</div>
                            <div className="text-xs text-gray-500">
                              CNPJ: {formatCPFouCNPJ(nfse.prestador_cnpj || nfse.cnpj_prestador || "")}
                            </div>
                          </td>
                          <td className="px-4 py-3">
                            <div className="text-sm max-w-[200px] truncate" title={nfse.descricao_servico}>
                              {nfse.descricao_servico || nfse.discriminacao || "-"}
                            </div>
                          </td>
                          <td className="px-4 py-3 text-sm">
                            {nfse.data_emissao 
                              ? new Date(nfse.data_emissao).toLocaleDateString("pt-BR")
                              : "-"
                            }
                          </td>
                          <td className="px-4 py-3 text-right font-mono font-medium text-green-700">
                            {new Intl.NumberFormat("pt-BR", {
                              style: "currency",
                              currency: "BRL"
                            }).format(nfse.valor_servico || nfse.valor_total || 0)}
                          </td>
                          <td className="px-4 py-3 text-center">
                            <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${
                              nfse.status === "nova" ? "bg-blue-100 text-blue-700" :
                              nfse.status === "processada" ? "bg-green-100 text-green-700" :
                              "bg-gray-100 text-gray-700"
                            }`}>
                              {nfse.status === "nova" && <AlertTriangle size={12} />}
                              {nfse.status === "processada" && <CheckCircle size={12} />}
                              {nfse.status === "ignorada" && <XCircle size={12} />}
                              {nfse.status === "nova" ? "Nova" : nfse.status === "processada" ? "Processada" : "Ignorada"}
                            </span>
                          </td>
                          <td className="px-4 py-3">
                            <div className="flex justify-center gap-1">
                              <Button 
                                variant="ghost" 
                                size="sm"
                                onClick={() => setShowNFeDetail({ ...nfse, tipo: "nfse" })}
                                title="Ver detalhes"
                              >
                                <Eye size={16} />
                              </Button>
                              <Button 
                                variant="ghost" 
                                size="sm"
                                onClick={() => handleDownloadNFSeXML(nfse.id, nfse.numero_nfse)}
                                title="Download XML"
                                className="text-blue-600 hover:bg-blue-50"
                              >
                                <FileDown size={16} />
                              </Button>
                              <Button 
                                variant="ghost" 
                                size="sm"
                                onClick={() => handleDownloadNFSePDF(nfse.id, nfse.numero_nfse)}
                                title="Download PDF"
                                className="text-red-600 hover:bg-red-50"
                              >
                                <FileText size={16} />
                              </Button>
                              {!nfse.conta_pagar_id && nfse.status !== "ignorada" && (
                                <Button 
                                  variant="ghost" 
                                  size="sm"
                                  className="text-green-600 hover:bg-green-50"
                                  onClick={() => handleCriarContaPagarNFSe(nfse.id)}
                                  title="Criar conta a pagar"
                                >
                                  <CreditCard size={16} />
                                </Button>
                              )}
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </CardContent>
              </Card>
            ) : (
              <Card>
                <CardContent className="py-16 text-center">
                  <Building2 className="mx-auto text-gray-300 mb-4" size={64} />
                  <h3 className="text-lg font-bold text-gray-600 mb-2">Nenhuma NFS-e importada</h3>
                  <p className="text-gray-500 mb-4">
                    {certificados.length === 0 
                      ? "Configure um CNPJ com certificado para começar a importar"
                      : "Clique em 'Importar NFS-e' para buscar notas de serviço"
                    }
                  </p>
                  {certificados.length === 0 && (
                    <Button 
                      className="bg-[#D4A000] hover:bg-[#b88f00] text-black"
                      onClick={() => {
                        setActiveTab("config");
                        setShowAddCertificado(true);
                      }}
                    >
                      <Plus size={18} className="mr-2" />
                      Adicionar CNPJ
                    </Button>
                  )}
                </CardContent>
              </Card>
            )
          )}
        </TabsContent>

        {/* Importação Manual Tab */}
        <TabsContent value="manual" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Upload size={20} />
                Importação Manual de NF
              </CardTitle>
              <p className="text-sm text-gray-500">
                Utilize esta opção quando a importação automática da SEFAZ falhar
              </p>
            </CardHeader>
            <CardContent className="space-y-4">
              
              {/* SEÇÃO PRIORITÁRIA: Upload de XML com extração automática */}
              <div className="border-2 border-dashed border-blue-400 rounded-lg p-6 bg-gradient-to-r from-blue-50 to-indigo-50">
                <div className="text-center mb-4">
                  <FileText className="mx-auto h-12 w-12 text-blue-500 mb-2" />
                  <h3 className="text-lg font-semibold text-blue-700">📥 Importar via XML</h3>
                  <p className="text-sm text-gray-600">
                    Faça upload do arquivo XML da nota fiscal e os campos serão preenchidos automaticamente
                  </p>
                </div>
                
                <div className="flex justify-center">
                  <label className="cursor-pointer">
                    <div className={`flex items-center gap-2 px-6 py-3 rounded-lg font-medium transition-colors ${
                      extractingXml 
                        ? 'bg-gray-300 text-gray-500 cursor-not-allowed' 
                        : 'bg-blue-600 text-white hover:bg-blue-700'
                    }`}>
                      {extractingXml ? (
                        <>
                          <Loader2 className="animate-spin" size={18} />
                          Processando XML...
                        </>
                      ) : (
                        <>
                          <Upload size={18} />
                          Selecionar Arquivo XML
                        </>
                      )}
                    </div>
                    <input
                      type="file"
                      accept=".xml"
                      className="hidden"
                      disabled={extractingXml}
                      onChange={(e) => {
                        const file = e.target.files[0];
                        if (file) handleXmlExtract(file);
                      }}
                    />
                  </label>
                </div>
                
                {xmlFileName && (
                  <div className="mt-3 text-center">
                    <span className="inline-flex items-center gap-2 px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm">
                      <CheckCircle size={14} />
                      {xmlFileName}
                    </span>
                  </div>
                )}
                
                {/* Mostrar itens extraídos */}
                {xmlItens.length > 0 && (
                  <div className="mt-4 p-3 bg-white rounded-lg border border-blue-200">
                    <h4 className="text-sm font-medium text-gray-700 mb-2">
                      📦 {xmlItens.length} Itens extraídos do XML:
                    </h4>
                    <div className="max-h-32 overflow-y-auto">
                      <table className="w-full text-xs">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="p-1 text-left">Descrição</th>
                            <th className="p-1 text-right">Qtd</th>
                            <th className="p-1 text-right">Valor</th>
                          </tr>
                        </thead>
                        <tbody>
                          {xmlItens.slice(0, 5).map((item, idx) => (
                            <tr key={idx} className="border-t">
                              <td className="p-1 truncate max-w-[200px]" title={item.descricao}>{item.descricao}</td>
                              <td className="p-1 text-right">{item.quantidade}</td>
                              <td className="p-1 text-right">R$ {item.valor_total?.toFixed(2)}</td>
                            </tr>
                          ))}
                          {xmlItens.length > 5 && (
                            <tr className="border-t bg-gray-50">
                              <td colSpan={3} className="p-1 text-center text-gray-500">
                                ... e mais {xmlItens.length - 5} itens
                              </td>
                            </tr>
                          )}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>
              
              <div className="flex items-center gap-4">
                <div className="flex-1 h-px bg-gray-200"></div>
                <span className="text-sm text-gray-500 font-medium">ou preencha manualmente</span>
                <div className="flex-1 h-px bg-gray-200"></div>
              </div>
              
              {/* Tipo de Nota */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Tipo de Nota *</Label>
                  <Select 
                    value={manualForm.tipo_nota} 
                    onValueChange={(value) => setManualForm({...manualForm, tipo_nota: value})}
                  >
                    <SelectTrigger data-testid="select-tipo-nota-manual">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="nfe">NF-e (Nota Fiscal de Produtos)</SelectItem>
                      <SelectItem value="nfse">NFS-e (Nota Fiscal de Serviços)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Número da Nota *</Label>
                  <Input
                    value={manualForm.numero_nota}
                    onChange={(e) => setManualForm({...manualForm, numero_nota: e.target.value})}
                    placeholder="Ex: 12345"
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <Label>Série</Label>
                  <Input
                    value={manualForm.serie}
                    onChange={(e) => setManualForm({...manualForm, serie: e.target.value})}
                    placeholder="1"
                  />
                </div>
                <div>
                  <Label>Chave de Acesso (44 dígitos)</Label>
                  <Input
                    value={manualForm.chave_acesso}
                    onChange={(e) => setManualForm({...manualForm, chave_acesso: e.target.value.replace(/\D/g, "")})}
                    placeholder="Opcional"
                    maxLength={44}
                  />
                </div>
                <div>
                  <Label>Data de Emissão *</Label>
                  <MaskedDateInput
                    value={manualForm.data_emissao}
                    onChange={(v) => setManualForm({...manualForm, data_emissao: v})}
                  />
                </div>
              </div>

              {/* Emitente */}
              <div className="border rounded-lg p-4 bg-gray-50">
                <h4 className="font-medium mb-3">Dados do Emitente</h4>
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <Label>CNPJ Emitente *</Label>
                    <Input
                      value={formatCPFouCNPJ(manualForm.cnpj_emitente)}
                      onChange={(e) => setManualForm({...manualForm, cnpj_emitente: e.target.value.replace(/\D/g, "")})}
                      placeholder="00.000.000/0000-00"
                    />
                  </div>
                  <div className="col-span-2">
                    <Label>Razão Social Emitente *</Label>
                    <Input
                      value={manualForm.razao_social_emitente}
                      onChange={(e) => setManualForm({...manualForm, razao_social_emitente: e.target.value})}
                      placeholder="Nome do fornecedor"
                    />
                  </div>
                </div>
              </div>

              {/* Valores */}
              <div className="border rounded-lg p-4 bg-gray-50">
                <h4 className="font-medium mb-3">Valores</h4>
                <div className="grid grid-cols-4 gap-4">
                  <div>
                    <Label>Valor Total *</Label>
                    <Input
                      value={manualForm.valor_total}
                      onChange={(e) => setManualForm({...manualForm, valor_total: e.target.value})}
                      placeholder="R$ 0,00"
                    />
                  </div>
                  <div>
                    <Label>Valor {manualForm.tipo_nota === "nfe" ? "Produtos" : "Serviços"}</Label>
                    <Input
                      value={manualForm.tipo_nota === "nfe" ? manualForm.valor_produtos : manualForm.valor_servicos}
                      onChange={(e) => setManualForm({
                        ...manualForm, 
                        [manualForm.tipo_nota === "nfe" ? "valor_produtos" : "valor_servicos"]: e.target.value
                      })}
                      placeholder="R$ 0,00"
                    />
                  </div>
                  <div>
                    <Label>Frete</Label>
                    <Input
                      value={manualForm.valor_frete}
                      onChange={(e) => setManualForm({...manualForm, valor_frete: e.target.value})}
                      placeholder="R$ 0,00"
                    />
                  </div>
                  <div>
                    <Label>Desconto</Label>
                    <Input
                      value={manualForm.valor_desconto}
                      onChange={(e) => setManualForm({...manualForm, valor_desconto: e.target.value})}
                      placeholder="R$ 0,00"
                    />
                  </div>
                </div>
              </div>

              {/* Classificação */}
              <div className="border rounded-lg p-4 bg-blue-50">
                <h4 className="font-medium mb-3 text-blue-700">Classificação Contábil</h4>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Centro de Custo</Label>
                    <Select 
                      value={manualForm.centro_custo_id} 
                      onValueChange={(value) => {
                        const centro = centrosCusto.find(c => c.id === value);
                        setManualForm({
                          ...manualForm, 
                          centro_custo_id: value,
                          centro_custo_nome: centro?.nome || ""
                        });
                      }}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Selecione..." />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="none">Nenhum</SelectItem>
                        {centrosCusto.map(c => (
                          <SelectItem key={c.id} value={c.id}>{c.nome}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label>Plano de Contas</Label>
                    <Select 
                      value={manualForm.plano_conta_id} 
                      onValueChange={(value) => {
                        const plano = planoContas.find(p => p.id === value);
                        setManualForm({
                          ...manualForm, 
                          plano_conta_id: value,
                          plano_conta_nome: plano?.nome || ""
                        });
                      }}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Selecione..." />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="none">Nenhum</SelectItem>
                        {planoContas.map(p => (
                          <SelectItem key={p.id} value={p.id}>{p.codigo} - {p.nome}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </div>

              {/* Upload de PDF (opcional) */}
              <div className="border rounded-lg p-4 bg-green-50">
                <h4 className="font-medium mb-3 text-green-700">Arquivo PDF - DANFE (Opcional)</h4>
                <div className="flex gap-2">
                  <Input
                    type="file"
                    accept=".pdf"
                    onChange={(e) => {
                      const file = e.target.files[0];
                      if (file) {
                        setPdfFileName(file.name);
                        const reader = new FileReader();
                        reader.onload = (ev) => {
                          const base64 = ev.target.result.split(",")[1];
                          setManualForm({...manualForm, pdf_base64: base64});
                        };
                        reader.readAsDataURL(file);
                      }
                    }}
                    className="flex-1"
                  />
                </div>
                {pdfFileName && <p className="text-xs text-gray-500 mt-1">✓ {pdfFileName}</p>}
              </div>

              {/* Observações */}
              <div>
                <Label>Observações</Label>
                <Input
                  value={manualForm.observacoes}
                  onChange={(e) => setManualForm({...manualForm, observacoes: e.target.value})}
                  placeholder="Informações adicionais sobre a nota..."
                />
              </div>

              {/* Botões */}
              <div className="flex justify-end gap-2 pt-4 border-t">
                <Button 
                  variant="outline" 
                  onClick={() => {
                    setManualForm({
                      tipo_nota: "nfe",
                      numero_nota: "",
                      serie: "1",
                      chave_acesso: "",
                      data_emissao: new Date().toISOString().split("T")[0],
                      cnpj_emitente: "",
                      razao_social_emitente: "",
                      uf_emitente: "",
                      cnpj_destinatario: "",
                      razao_social_destinatario: "",
                      valor_total: "",
                      valor_produtos: "",
                      valor_servicos: "",
                      valor_frete: "",
                      valor_desconto: "",
                      centro_custo_id: "",
                      centro_custo_nome: "",
                      plano_conta_id: "",
                      plano_conta_nome: "",
                      xml_base64: "",
                      pdf_base64: "",
                      observacoes: ""
                    });
                    setXmlFileName("");
                    setPdfFileName("");
                    setXmlItens([]);
                  }}
                >
                  Limpar
                </Button>
                <Button 
                  onClick={async () => {
                    if (!manualForm.numero_nota || !manualForm.cnpj_emitente || !manualForm.razao_social_emitente || !manualForm.valor_total) {
                      toast.error("Preencha os campos obrigatórios: Número, CNPJ, Razão Social e Valor Total");
                      return;
                    }
                    
                    setImportandoManual(true);
                    try {
                      const valorTotal = parseFloat(manualForm.valor_total.replace(/[^\d,.-]/g, "").replace(",", ".")) || 0;
                      const valorProdutos = parseFloat((manualForm.valor_produtos || "").replace(/[^\d,.-]/g, "").replace(",", ".")) || valorTotal;
                      const valorServicos = parseFloat((manualForm.valor_servicos || "").replace(/[^\d,.-]/g, "").replace(",", ".")) || 0;
                      const valorFrete = parseFloat((manualForm.valor_frete || "").replace(/[^\d,.-]/g, "").replace(",", ".")) || 0;
                      const valorDesconto = parseFloat((manualForm.valor_desconto || "").replace(/[^\d,.-]/g, "").replace(",", ".")) || 0;
                      
                      await axios.post(`${API}/nf/importar-manual`, {
                        ...manualForm,
                        valor_total: valorTotal,
                        valor_produtos: manualForm.tipo_nota === "nfe" ? valorProdutos : null,
                        valor_servicos: manualForm.tipo_nota === "nfse" ? valorServicos : null,
                        valor_frete: valorFrete,
                        valor_desconto: valorDesconto
                      });
                      
                      toast.success("NF importada manualmente com sucesso!");
                      fetchData();
                      setActiveTab("notas");
                      
                      // Limpar formulário
                      setManualForm({
                        tipo_nota: "nfe",
                        numero_nota: "",
                        serie: "1",
                        chave_acesso: "",
                        data_emissao: new Date().toISOString().split("T")[0],
                        cnpj_emitente: "",
                        razao_social_emitente: "",
                        uf_emitente: "",
                        cnpj_destinatario: "",
                        razao_social_destinatario: "",
                        valor_total: "",
                        valor_produtos: "",
                        valor_servicos: "",
                        valor_frete: "",
                        valor_desconto: "",
                        centro_custo_id: "",
                        centro_custo_nome: "",
                        plano_conta_id: "",
                        plano_conta_nome: "",
                        xml_base64: "",
                        pdf_base64: "",
                        observacoes: ""
                      });
                      setXmlFileName("");
                      setPdfFileName("");
                      setXmlItens([]);
                    } catch (error) {
                      toast.error(error.response?.data?.detail || "Erro ao importar NF manualmente");
                    } finally {
                      setImportandoManual(false);
                    }
                  }}
                  disabled={importandoManual}
                  className="bg-green-600 hover:bg-green-700"
                  data-testid="btn-importar-manual"
                >
                  {importandoManual ? <Loader2 className="animate-spin mr-2" size={16} /> : <Upload className="mr-2" size={16} />}
                  Importar Nota
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Configurações Tab */}
        <TabsContent value="config" className="space-y-4">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-lg font-bold">CNPJs Cadastrados</h2>
              <p className="text-sm text-gray-500">Gerencie os CNPJs e certificados para importação</p>
            </div>
            <Button 
              className="bg-[#D4A000] hover:bg-[#b88f00] text-black font-bold"
              onClick={() => setShowAddCertificado(true)}
            >
              <Plus size={18} className="mr-2" />
              Adicionar CNPJ
            </Button>
          </div>

          {certificados.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {certificados.map((cert) => {
                const bloqueado = isCertificadoBloqueado(cert);
                const consultasRestantes = getConsultasRestantes(cert);
                const semConsultas = consultasRestantes <= 0;
                
                return (
                <Card key={cert.id} className={`relative ${bloqueado ? 'border-red-300 bg-red-50/30' : ''}`}>
                  <CardContent className="pt-6">
                    <div className="flex items-start gap-4">
                      <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${
                        bloqueado ? 'bg-red-100' : 'bg-green-100'
                      }`}>
                        {bloqueado ? (
                          <Ban className="text-red-600" size={24} />
                        ) : (
                          <ShieldCheck className="text-green-600" size={24} />
                        )}
                      </div>
                      <div className="flex-1">
                        <h3 className="font-bold text-black">{cert.razao_social}</h3>
                        <p className="text-sm text-gray-500 font-mono">{formatCPFouCNPJ(cert.cnpj)}</p>
                        <div className="flex items-center gap-2 mt-2 flex-wrap">
                          <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                            cert.ambiente === "producao" 
                              ? "bg-green-100 text-green-800" 
                              : "bg-yellow-100 text-yellow-800"
                          }`}>
                            {cert.ambiente === "producao" ? "Produção" : "Homologação"}
                          </span>
                          <span className="text-xs text-gray-500">UF: {cert.uf}</span>
                        </div>
                      </div>
                    </div>
                    
                    {/* Cronômetro de bloqueio */}
                    {bloqueado && (
                      <div className="mt-3">
                        <Cronometro 
                          bloqueadoAte={cert.bloqueado_ate} 
                          onExpire={() => fetchData()}
                        />
                      </div>
                    )}
                    
                    {/* Consultas restantes */}
                    <div className={`mt-3 flex items-center gap-2 px-3 py-2 rounded-lg ${
                      semConsultas ? 'bg-orange-100 border border-orange-300' : 'bg-blue-50 border border-blue-200'
                    }`}>
                      <Clock size={14} className={semConsultas ? 'text-orange-600' : 'text-blue-600'} />
                      <span className={`text-xs font-medium ${semConsultas ? 'text-orange-700' : 'text-blue-700'}`}>
                        {semConsultas 
                          ? 'Limite diário atingido' 
                          : `${consultasRestantes} consulta(s) restante(s) hoje`
                        }
                      </span>
                    </div>
                    
                    <div className="mt-4 pt-4 border-t border-gray-200 flex flex-wrap gap-2">
                      <Button 
                        variant="outline" 
                        size="sm" 
                        className="flex-1 min-w-[120px]"
                        onClick={() => handleImportarNotas(cert.id)}
                        disabled={importando || bloqueado || semConsultas}
                        data-testid={`btn-importar-incremental-${cert.id}`}
                        title="Importa apenas as NF-e novas desde a última sincronização"
                      >
                        {importandoCertId === cert.id ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : bloqueado ? (
                          <>
                            <Ban size={14} className="mr-1" />
                            Bloqueado
                          </>
                        ) : semConsultas ? (
                          <>
                            <AlertTriangle size={14} className="mr-1" />
                            Sem consultas
                          </>
                        ) : (
                          <>
                            <Download size={14} className="mr-1" />
                            Importar
                          </>
                        )}
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        className="text-amber-700 border-amber-300 hover:bg-amber-50"
                        onClick={() => {
                          if (window.confirm(
                            `Importação COMPLETA: re-varre todo o histórico de NF-e (NSU=0) e busca todas as NFS-e dos últimos 5 anos. ` +
                            `Pode demorar mais que o normal (até ~30s). Duplicatas serão ignoradas. Deseja continuar?`
                          )) {
                            handleImportarNotas(cert.id, true);
                          }
                        }}
                        disabled={importando || bloqueado || semConsultas}
                        data-testid={`btn-importar-completo-${cert.id}`}
                        title="Re-varre TODO o histórico (NF-e desde NSU=0 e NFS-e dos últimos 5 anos)"
                      >
                        <FileDown size={14} className="mr-1" />
                        Histórico Completo
                      </Button>
                      <Button 
                        variant="outline" 
                        size="sm"
                        className="text-blue-600 hover:bg-blue-50"
                        onClick={() => openEditCertificado(cert)}
                        data-testid={`edit-cnpj-${cert.id}`}
                        title="Editar dados fiscais (Inscrição Municipal, URL NFS-e)"
                      >
                        <Pencil size={14} />
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        className="text-purple-600 hover:bg-purple-50"
                        onClick={() => handleTestarConexaoNfse(cert.id)}
                        disabled={testandoConexaoId === cert.id || !cert.url_nfse}
                        data-testid={`test-nfse-${cert.id}`}
                        title={cert.url_nfse ? "Testar conexão NFS-e" : "Configure a URL do webservice NFS-e primeiro"}
                      >
                        {testandoConexaoId === cert.id ? (
                          <Loader2 size={14} className="animate-spin" />
                        ) : (
                          <Plug size={14} />
                        )}
                      </Button>
                      <Button 
                        variant="outline" 
                        size="sm"
                        className="text-red-600 hover:bg-red-50"
                        onClick={() => setDeleteCertificadoId(cert.id)}
                      >
                        <Trash2 size={14} />
                      </Button>
                    </div>

                    <p className="text-xs text-gray-400 mt-3">
                      Cadastrado em: {formatDate(cert.created_at)}
                    </p>
                  </CardContent>
                </Card>
              );
              })}
            </div>
          ) : (
            <Card>
              <CardContent className="py-16 text-center">
                <Building2 className="mx-auto text-gray-300 mb-4" size={64} />
                <h3 className="text-lg font-bold text-gray-600 mb-2">Nenhum CNPJ cadastrado</h3>
                <p className="text-gray-500 mb-4">
                  Cadastre um CNPJ com certificado A1 para começar a importar NF-e
                </p>
                <Button 
                  className="bg-[#D4A000] hover:bg-[#b88f00] text-black"
                  onClick={() => setShowAddCertificado(true)}
                >
                  <Plus size={18} className="mr-2" />
                  Adicionar CNPJ
                </Button>
              </CardContent>
            </Card>
          )}

          {/* Instruções */}
          <Card className="bg-blue-50 border-blue-200">
            <CardContent className="py-4">
              <h3 className="font-bold text-blue-800 mb-2">Como funciona?</h3>
              <ol className="text-sm text-blue-700 space-y-1 list-decimal list-inside">
                <li>Cadastre o CNPJ da empresa com o certificado digital A1 (.pfx)</li>
                <li>O sistema consultará a SEFAZ em busca de NF-e destinadas ao CNPJ</li>
                <li>As notas encontradas serão listadas e podem ser convertidas em Contas a Pagar</li>
                <li><strong>Limite:</strong> 3 consultas por dia por empresa</li>
                <li>Se a SEFAZ bloquear, aguarde o cronômetro de 1 hora</li>
              </ol>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Modal Adicionar Certificado */}
      <Dialog open={showAddCertificado} onOpenChange={setShowAddCertificado}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <ShieldCheck className="text-green-600" size={24} />
              Adicionar CNPJ/Certificado
            </DialogTitle>
            <DialogDescription>
              Cadastre um CNPJ com certificado digital A1 para importar NF-e e NFS-e automaticamente
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleAddCertificado} className="space-y-4">
            <div className="space-y-2">
              <Label>CNPJ *</Label>
              <Input
                value={certForm.cnpj}
                onChange={(e) => setCertForm({...certForm, cnpj: formatCPFouCNPJ(e.target.value)})}
                placeholder="00.000.000/0000-00"
                required
                className="font-mono"
              />
            </div>

            <div className="space-y-2">
              <Label>Razão Social *</Label>
              <Input
                value={certForm.razao_social}
                onChange={(e) => setCertForm({...certForm, razao_social: e.target.value})}
                placeholder="Nome da empresa"
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>UF</Label>
                <Select value={certForm.uf} onValueChange={(v) => setCertForm({...certForm, uf: v})}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {ufs.map((uf) => (
                      <SelectItem key={uf} value={uf}>{uf}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Ambiente</Label>
                <Select value={certForm.ambiente} onValueChange={(v) => setCertForm({...certForm, ambiente: v})}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="producao">Produção</SelectItem>
                    <SelectItem value="homologacao">Homologação</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="space-y-2">
              <Label>Certificado Digital A1 (.pfx) *</Label>
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-4 text-center hover:border-[#D4A000] transition-colors">
                <input
                  type="file"
                  accept=".pfx,.p12"
                  onChange={handleFileUpload}
                  className="hidden"
                  id="cert-upload"
                />
                <label htmlFor="cert-upload" className="cursor-pointer">
                  {certForm.certificado_nome ? (
                    <div className="flex items-center justify-center gap-2 text-green-600">
                      <CheckCircle size={20} />
                      <span className="font-medium">{certForm.certificado_nome}</span>
                    </div>
                  ) : (
                    <div className="text-gray-500">
                      <Upload className="mx-auto mb-2" size={32} />
                      <p className="text-sm">Clique para selecionar o certificado</p>
                      <p className="text-xs text-gray-400">Arquivos .pfx ou .p12</p>
                    </div>
                  )}
                </label>
              </div>
            </div>

            <div className="space-y-2">
              <Label>Senha do Certificado *</Label>
              <Input
                type="password"
                value={certForm.senha_certificado}
                onChange={(e) => setCertForm({...certForm, senha_certificado: e.target.value})}
                placeholder="Digite a senha do certificado"
                required
              />
            </div>

            <div className="border-t pt-4">
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">Configuração NFS-e (Nota Fiscal de Serviço)</p>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Inscrição Municipal</Label>
                  <Input
                    value={certForm.inscricao_municipal}
                    onChange={(e) => setCertForm({...certForm, inscricao_municipal: e.target.value})}
                    placeholder="Ex: 123456"
                  />
                </div>
                <div className="space-y-2">
                  <Label className="flex items-center gap-1">
                    URL Webservice NFS-e
                  </Label>
                  <Input
                    value={certForm.url_nfse}
                    onChange={(e) => setCertForm({...certForm, url_nfse: e.target.value})}
                    placeholder="https://palmasto.webiss.com.br/ws/nfse.asmx"
                    data-testid="cert-url-nfse"
                  />
                </div>
              </div>
              <p className="text-xs text-gray-400 mt-1">
                Preencha para habilitar a importação automática de NFS-e (padrão ABRASF v2 — WebISS).
                Para Palmas-TO use: <code className="bg-gray-100 px-1 rounded">https://palmasto.webiss.com.br/ws/nfse.asmx</code>
              </p>
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setShowAddCertificado(false)}>
                Cancelar
              </Button>
              <Button 
                type="submit" 
                className="bg-[#D4A000] hover:bg-[#b88f00] text-black"
                disabled={formLoading}
              >
                {formLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Salvando...
                  </>
                ) : (
                  "Cadastrar"
                )}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Modal Detalhes NF-e */}
      <Dialog open={!!showNFeDetail} onOpenChange={() => setShowNFeDetail(null)}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <FileText className="text-[#D4A000]" size={24} />
              NF-e Nº {showNFeDetail?.numero_nf}
            </DialogTitle>
          </DialogHeader>

          {showNFeDetail && (
            <div className="space-y-4">
              {/* Info Principal */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-xs text-gray-500 uppercase">Emitente</p>
                  <p className="font-bold">{showNFeDetail.razao_social_emitente}</p>
                  <p className="text-sm text-gray-600 font-mono">{formatCPFouCNPJ(showNFeDetail.cnpj_emitente)}</p>
                </div>
                <div className="text-right">
                  <p className="text-xs text-gray-500 uppercase">Valor Total</p>
                  <p className="text-2xl font-bold text-green-600">{formatCurrency(showNFeDetail.valor_total)}</p>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4 bg-gray-50 rounded-lg p-4">
                <div>
                  <p className="text-xs text-gray-500">Data Emissão</p>
                  <p className="font-medium">{formatDate(showNFeDetail.data_emissao)}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Série</p>
                  <p className="font-medium">{showNFeDetail.serie || "-"}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Status</p>
                  {getStatusBadge(showNFeDetail.status)}
                </div>
              </div>

              {/* Chave de Acesso */}
              <div className="bg-gray-100 rounded-lg p-3">
                <p className="text-xs text-gray-500 mb-1">Chave de Acesso</p>
                <p className="font-mono text-xs break-all">{showNFeDetail.chave_acesso}</p>
              </div>

              {/* Botões de Download */}
              <div className="flex gap-2 pt-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    if (showNFeDetail.tipo === "nfse") {
                      handleDownloadNFSeXML(showNFeDetail.id, showNFeDetail.numero_nfse);
                    } else {
                      handleDownloadNFeXML(showNFeDetail.id, showNFeDetail.numero_nf);
                    }
                  }}
                  className="flex-1"
                >
                  <FileDown size={16} className="mr-2" />
                  Download XML
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    if (showNFeDetail.tipo === "nfse") {
                      handleDownloadNFSePDF(showNFeDetail.id, showNFeDetail.numero_nfse);
                    } else {
                      handleDownloadNFePDF(showNFeDetail.id, showNFeDetail.numero_nf);
                    }
                  }}
                  className="flex-1"
                >
                  <FileText size={16} className="mr-2" />
                  Download {showNFeDetail.tipo === "nfse" ? "NFS-e" : "DANFE"} (PDF)
                </Button>
              </div>

              {/* Itens */}
              {showNFeDetail.itens?.length > 0 && (
                <div>
                  <p className="font-bold mb-2">Itens ({showNFeDetail.itens.length})</p>
                  <div className="border rounded-lg overflow-hidden">
                    <table className="w-full text-sm">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-3 py-2 text-left">Descrição</th>
                          <th className="px-3 py-2 text-right">Qtd</th>
                          <th className="px-3 py-2 text-right">Unit.</th>
                          <th className="px-3 py-2 text-right">Total</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y">
                        {showNFeDetail.itens.map((item, idx) => (
                          <tr key={idx}>
                            <td className="px-3 py-2">{item.descricao}</td>
                            <td className="px-3 py-2 text-right">{item.quantidade} {item.unidade}</td>
                            <td className="px-3 py-2 text-right">{formatCurrency(item.valor_unitario)}</td>
                            <td className="px-3 py-2 text-right font-medium">{formatCurrency(item.valor_total)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Ações */}
              {!showNFeDetail.conta_pagar_id && showNFeDetail.status !== "ignorada" && (
                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <p className="font-medium text-green-800 mb-2">Criar Conta a Pagar</p>
                  <p className="text-sm text-green-700 mb-3">
                    Deseja criar uma conta a pagar automaticamente a partir desta NF-e?
                  </p>
                  <Button 
                    className="bg-green-600 hover:bg-green-700"
                    onClick={() => handleCriarContaPagar(showNFeDetail.id)}
                  >
                    <CreditCard size={16} className="mr-2" />
                    Criar Conta a Pagar
                  </Button>
                </div>
              )}

              {showNFeDetail.conta_pagar_id && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 flex items-center gap-3">
                  <CheckCircle className="text-blue-600" size={24} />
                  <div>
                    <p className="font-medium text-blue-800">Conta a Pagar Vinculada</p>
                    <p className="text-sm text-blue-700">Esta NF-e já possui uma conta a pagar criada.</p>
                  </div>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Modal Confirmar Exclusão */}
      <Dialog open={!!deleteCertificadoId} onOpenChange={() => setDeleteCertificadoId(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="text-red-600">Remover Certificado</DialogTitle>
            <DialogDescription>
              Tem certeza que deseja remover este CNPJ/Certificado? As NF-e já importadas serão mantidas.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteCertificadoId(null)}>
              Cancelar
            </Button>
            <Button className="bg-red-600 hover:bg-red-700" onClick={handleDeleteCertificado}>
              Remover
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Modal Editar CNPJ/Certificado */}
      <Dialog open={!!editCertificado} onOpenChange={(open) => !open && setEditCertificado(null)}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Editar CNPJ/Certificado</DialogTitle>
            <DialogDescription>
              Atualize os dados fiscais do CNPJ. O certificado digital (.pfx) e CNPJ não podem ser alterados.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleUpdateCertificado} data-testid="edit-cnpj-form">
            <div className="grid gap-4 py-2">
              {editCertificado && (
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
                  <p className="text-xs text-gray-500 mb-0.5">CNPJ</p>
                  <p className="font-mono text-sm font-bold">{formatCPFouCNPJ(editCertificado.cnpj)}</p>
                </div>
              )}

              <div>
                <Label htmlFor="edit-razao">Razão Social</Label>
                <Input
                  id="edit-razao"
                  data-testid="edit-razao-social"
                  value={editForm.razao_social}
                  onChange={(e) => setEditForm({ ...editForm, razao_social: e.target.value })}
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>UF</Label>
                  <Select
                    value={editForm.uf}
                    onValueChange={(v) => setEditForm({ ...editForm, uf: v })}
                  >
                    <SelectTrigger data-testid="edit-uf">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {ufs.map((uf) => (
                        <SelectItem key={uf} value={uf}>{uf}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Ambiente</Label>
                  <Select
                    value={editForm.ambiente}
                    onValueChange={(v) => setEditForm({ ...editForm, ambiente: v })}
                  >
                    <SelectTrigger data-testid="edit-ambiente">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="producao">Produção</SelectItem>
                      <SelectItem value="homologacao">Homologação</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="border-t border-gray-200 pt-4 mt-1">
                <h4 className="text-sm font-bold text-gray-700 mb-3">NFS-e (Nota Fiscal de Serviço)</h4>
                <div className="grid gap-3">
                  <div>
                    <Label htmlFor="edit-im">Inscrição Municipal</Label>
                    <Input
                      id="edit-im"
                      data-testid="edit-inscricao-municipal"
                      placeholder="Ex.: 1234567"
                      value={editForm.inscricao_municipal}
                      onChange={(e) => setEditForm({ ...editForm, inscricao_municipal: e.target.value })}
                    />
                  </div>
                  <div>
                    <Label htmlFor="edit-url">URL Webservice NFS-e</Label>
                    <Input
                      id="edit-url"
                      data-testid="edit-url-nfse"
                      placeholder="https://palmasto.webiss.com.br/ws/nfse.asmx"
                      value={editForm.url_nfse}
                      onChange={(e) => setEditForm({ ...editForm, url_nfse: e.target.value })}
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      Use a URL SOAP do webservice da prefeitura. Obtenha-a no portal da sua prefeitura do seu município.
                    </p>
                  </div>
                </div>
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setEditCertificado(null)}>
                Cancelar
              </Button>
              <Button type="submit" disabled={editLoading} data-testid="edit-cnpj-save">
                {editLoading ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Salvando...
                  </>
                ) : (
                  "Salvar alterações"
                )}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
