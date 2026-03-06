import { useState, useEffect, useCallback } from "react";
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
  Ban
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
  const [formLoading, setFormLoading] = useState(false);
  const [selectedCertificado, setSelectedCertificado] = useState("todos");
  const [selectedStatus, setSelectedStatus] = useState("todos");

  const [certForm, setCertForm] = useState({
    cnpj: "",
    razao_social: "",
    uf: "SP",
    ambiente: "producao",
    certificado_base64: "",
    senha_certificado: "",
    certificado_nome: ""
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
      const [certsRes, nfesRes, nfsesRes] = await Promise.all([
        axios.get(`${API}/nfe/certificados`),
        axios.get(`${API}/nfe/importadas`, {
          params: {
            certificado_id: selectedCertificado !== "todos" ? selectedCertificado : undefined,
            status: selectedStatus !== "todos" ? selectedStatus : undefined
          }
        }),
        axios.get(`${API}/nfse/importadas`, {
          params: {
            certificado_id: selectedCertificado !== "todos" ? selectedCertificado : undefined,
            status: selectedStatus !== "todos" ? selectedStatus : undefined
          }
        }).catch(() => ({ data: [] }))
      ]);
      setCertificados(certsRes.data);
      setNfesImportadas(nfesRes.data);
      setNfsesImportadas(nfsesRes.data || []);
    } catch (error) {
      console.error("Erro ao carregar dados:", error);
    } finally {
      setLoading(false);
    }
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
        senha_certificado: certForm.senha_certificado
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
        certificado_nome: ""
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

  const handleImportarNotas = async (certificadoId) => {
    const cert = certificados.find(c => c.id === certificadoId);
    
    // Verificar bloqueio
    if (cert && isCertificadoBloqueado(cert)) {
      toast.error("Este certificado está bloqueado. Aguarde o cronômetro zerar.");
      return;
    }
    
    // Verificar limite diário
    if (cert && getConsultasRestantes(cert) <= 0) {
      toast.error("Limite diário de 3 consultas atingido. Tente novamente amanhã.");
      return;
    }
    
    setImportando(true);
    setImportandoCertId(certificadoId);
    try {
      const response = await axios.post(`${API}/nfe/importar/${certificadoId}`);
      
      // Verificar se há aviso especial (bloqueio da SEFAZ)
      if (response.data.aviso) {
        toast.warning(response.data.aviso, { duration: 8000 });
      } else {
        toast.success(response.data.message);
        if (response.data.novas_nfes > 0) {
          toast.info(`${response.data.novas_nfes} nova(s) NF-e encontrada(s)!`);
        } else if (response.data.total_novas === 0) {
          toast.info("Nenhuma nova NF-e encontrada na SEFAZ");
        }
      }
      fetchData();
    } catch (error) {
      const detail = error.response?.data?.detail || "Erro ao importar notas";
      toast.error(detail);
      // Recarregar dados para atualizar estado de bloqueio
      fetchData();
    } finally {
      setImportando(false);
      setImportandoCertId(null);
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
          <h1 className="page-title font-heading">Importação de NF-e</h1>
          <p className="text-gray-500 mt-1">Importe notas fiscais eletrônicas da SEFAZ</p>
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
              onClick={() => handleImportarNotas(certificados[0]?.id)}
              disabled={importando}
            >
              {importando ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Importando...
                </>
              ) : (
                <>
                  <Download size={18} className="mr-2" />
                  Importar Notas
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
            Notas Importadas ({nfesImportadas.length})
          </TabsTrigger>
          <TabsTrigger value="config" data-testid="tab-config">
            <Settings size={16} className="mr-2" />
            CNPJs/Certificados ({certificados.length})
          </TabsTrigger>
        </TabsList>

        {/* Notas Importadas Tab */}
        <TabsContent value="notas" className="space-y-4">
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

          {/* Lista de NF-e */}
          {nfesImportadas.length > 0 ? (
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
                              onClick={() => window.open(`${API}/nfe/importadas/${nfe.id}/download-xml`, '_blank')}
                              title="Download XML"
                              className="text-blue-600 hover:bg-blue-50"
                            >
                              <FileDown size={16} />
                            </Button>
                            <Button 
                              variant="ghost" 
                              size="sm"
                              onClick={() => window.open(`${API}/nfe/importadas/${nfe.id}/download-pdf`, '_blank')}
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
                    : "Clique em 'Importar Notas' para buscar NF-e da SEFAZ"
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
          )}
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
                    
                    <div className="mt-4 pt-4 border-t border-gray-200 flex gap-2">
                      <Button 
                        variant="outline" 
                        size="sm" 
                        className="flex-1"
                        onClick={() => handleImportarNotas(cert.id)}
                        disabled={importando || bloqueado || semConsultas}
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
              Cadastre um CNPJ com certificado digital A1 para importar NF-e
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
                  onClick={() => window.open(`${API}/nfe/importadas/${showNFeDetail.id}/download-xml`, '_blank')}
                  className="flex-1"
                >
                  <FileDown size={16} className="mr-2" />
                  Download XML
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => window.open(`${API}/nfe/importadas/${showNFeDetail.id}/download-pdf`, '_blank')}
                  className="flex-1"
                >
                  <FileText size={16} className="mr-2" />
                  Download DANFE (PDF)
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
    </div>
  );
}
