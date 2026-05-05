import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "@/App";
import { Card, CardContent } from "@/components/ui/card";
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
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Checkbox } from "@/components/ui/checkbox";
import { 
  HardHat, Users, Plus, Search, Download, AlertTriangle, 
  Check, Loader2, Sparkles, FileText, Shield, AlertCircle, BookOpen
} from "lucide-react";
import { toast } from "sonner";

export default function EPIPage() {
  const [funcionarios, setFuncionarios] = useState([]);
  const [fichasEPI, setFichasEPI] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedFuncionario, setSelectedFuncionario] = useState("");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [consultandoCBO, setConsultandoCBO] = useState(false);
  const [consultandoEPIs, setConsultandoEPIs] = useState(false);
  const [episSugeridos, setEpisSugeridos] = useState([]);
  const [episSelecionados, setEpisSelecionados] = useState([]);
  const [mapaRisco, setMapaRisco] = useState([]);
  const [cboInfo, setCboInfo] = useState(null);
  const [cboSearch, setCboSearch] = useState("");
  const [cboResults, setCboResults] = useState([]);
  const [cboNotFound, setCboNotFound] = useState(false);
  const [manualCbo, setManualCbo] = useState({ codigo: "", ocupacao: "" });
  
  const [formData, setFormData] = useState({
    funcionario_id: "",
    codigo_cbo: "",
    ocupacao_cbo: "",
    data_entrega: new Date().toISOString().split('T')[0],
    observacoes: ""
  });

  useEffect(() => {
    fetchFuncionarios();
    fetchFichasEPI();
  }, []);

  const fetchFuncionarios = async () => {
    try {
      const response = await axios.get(`${API}/rh/funcionarios?status=ativo`);
      setFuncionarios(response.data);
    } catch (error) {
      console.error("Erro ao carregar funcionários:", error);
    }
  };

  const fetchFichasEPI = async () => {
    setLoading(true);
    try {
      let url = `${API}/rh/epi/fichas`;
      if (selectedFuncionario) url += `?funcionario_id=${selectedFuncionario}`;
      const response = await axios.get(url);
      setFichasEPI(response.data);
    } catch (error) {
      toast.error("Erro ao carregar fichas de EPI");
    } finally {
      setLoading(false);
    }
  };

  const handleSearchCBO = async () => {
    if (!cboSearch.trim()) {
      toast.error("Digite um código ou nome de ocupação");
      return;
    }
    
    setConsultandoCBO(true);
    setCboResults([]);
    setCboNotFound(false);
    try {
      const response = await axios.get(`${API}/rh/epi/cbo/buscar?q=${encodeURIComponent(cboSearch)}`);
      setCboResults(response.data || []);
      if (response.data.length === 0) {
        setCboNotFound(true);
        toast.info("CBO não encontrado em nossa base. Você pode cadastrá-lo manualmente abaixo.");
      }
    } catch (error) {
      toast.error("Erro ao buscar CBO");
    } finally {
      setConsultandoCBO(false);
    }
  };

  const handleAddManualCBO = () => {
    if (!manualCbo.codigo.trim() || !manualCbo.ocupacao.trim()) {
      toast.error("Informe o código CBO e a descrição da ocupação");
      return;
    }
    const cbo = {
      codigo: manualCbo.codigo.trim(),
      ocupacao: manualCbo.ocupacao.trim(),
      descricao: "Cadastrado manualmente",
      familia: "—",
    };
    handleSelectCBO(cbo);
    setManualCbo({ codigo: "", ocupacao: "" });
    setCboNotFound(false);
    toast.success("Ocupação adicionada manualmente");
  };

  const handleSelectCBO = (cbo) => {
    setFormData({
      ...formData,
      codigo_cbo: cbo.codigo,
      ocupacao_cbo: cbo.ocupacao
    });
    setCboInfo(cbo);
    setCboResults([]);
    setCboSearch("");
  };

  const handleConsultarEPIs = async () => {
    if (!formData.codigo_cbo) {
      toast.error("Selecione uma ocupação CBO primeiro");
      return;
    }
    
    setConsultandoEPIs(true);
    try {
      const response = await axios.post(`${API}/rh/epi/consultar-epis-cbo`, {
        codigo_cbo: formData.codigo_cbo,
        ocupacao: formData.ocupacao_cbo
      });
      
      const epis = response.data.epis || [];
      setEpisSugeridos(epis);
      setMapaRisco(response.data.mapa_risco || []);
      // Pré-seleciona EPIs de fontes oficiais da empresa (PGR, PCMSO, LTCAT)
      // ou os marcados como Alta prioridade quando não há fonte específica.
      const fontesOficiais = ["PGR", "PCMSO", "LTCAT", "CCT"];
      const preMarcados = epis.filter((e) =>
        fontesOficiais.includes((e.fonte || "").toUpperCase()) ||
        (e.prioridade === "Alta" && !e.fonte)
      );
      setEpisSelecionados(preMarcados);

      const fontePrincipal = (response.data.fonte_principal || "").toUpperCase();
      if (fontesOficiais.includes(fontePrincipal)) {
        toast.success(
          `EPIs carregados — ${preMarcados.length} pré-marcado(s) com base no ${fontePrincipal} da CRA`,
        );
      } else {
        toast.success(
          `EPIs carregados (fonte: ${fontePrincipal || "NRs gerais"}) — revise as sugestões`,
        );
      }
    } catch (error) {
      toast.error("Erro ao consultar EPIs");
    } finally {
      setConsultandoEPIs(false);
    }
  };

  const handleToggleEPI = (epi) => {
    setEpisSelecionados(prev => {
      const exists = prev.find(e => e.nome === epi.nome);
      if (exists) {
        return prev.filter(e => e.nome !== epi.nome);
      } else {
        return [...prev, epi];
      }
    });
  };

  const handleSalvarFichaEPI = async () => {
    if (!formData.funcionario_id || episSelecionados.length === 0) {
      toast.error("Selecione o funcionário e pelo menos um EPI");
      return;
    }
    
    try {
      await axios.post(`${API}/rh/epi/fichas`, {
        ...formData,
        epis: episSelecionados
      });
      toast.success("Ficha de EPI salva!");
      fetchFichasEPI();
      closeModal();
    } catch (error) {
      // Pydantic v2 retorna um array em error.response.data.detail.
      // Renderizar um array no toast quebra o React (Objects are not valid as a React child).
      const raw = error?.response?.data?.detail;
      let msg = "Erro ao salvar ficha";
      if (typeof raw === "string") {
        msg = raw;
      } else if (Array.isArray(raw)) {
        msg = raw
          .map((d) => d?.msg || d?.detail || JSON.stringify(d))
          .join(", ");
      } else if (raw) {
        msg = JSON.stringify(raw);
      }
      toast.error(msg);
    }
  };

  const handleExportarFicha = async (fichaId) => {
    try {
      const response = await axios.get(`${API}/rh/epi/fichas/${fichaId}/exportar`, {
        responseType: 'blob'
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `ficha_epi_${fichaId}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      toast.success("Ficha exportada!");
    } catch (error) {
      toast.error("Erro ao exportar ficha");
    }
  };

  const handleExportarTermo = async (fichaId) => {
    try {
      const response = await axios.get(`${API}/rh/epi/fichas/${fichaId}/termo-responsabilidade`, {
        responseType: 'blob'
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `termo_responsabilidade_${fichaId}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      toast.success("Termo exportado!");
    } catch (error) {
      toast.error("Erro ao exportar termo");
    }
  };

  const openModal = () => {
    setFormData({
      funcionario_id: "",
      codigo_cbo: "",
      ocupacao_cbo: "",
      data_entrega: new Date().toISOString().split('T')[0],
      observacoes: ""
    });
    setEpisSugeridos([]);
    setEpisSelecionados([]);
    setMapaRisco([]);
    setCboInfo(null);
    setCboSearch("");
    setCboResults([]);
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
  };

  const getFuncionarioNome = (id) => {
    const func = funcionarios.find(f => f.id === id);
    return func?.nome || "-";
  };

  const getPrioridadeCor = (prioridade) => {
    switch (prioridade?.toLowerCase()) {
      case 'alta': return 'bg-red-500 text-white';
      case 'media': case 'média': return 'bg-yellow-500 text-black';
      case 'baixa': return 'bg-green-500 text-white';
      default: return 'bg-gray-500 text-white';
    }
  };

  if (loading && funcionarios.length === 0) {
    return <div className="flex items-center justify-center min-h-[400px]"><div className="spinner w-12 h-12"></div></div>;
  }

  return (
    <div data-testid="epi-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Gestão de EPI/EPC</h1>
          <p className="text-gray-500 mt-1">Fichas baseadas na Classificação Brasileira de Ocupações (CBO)</p>
        </div>
        <Button onClick={openModal} className="bg-[#10B981] hover:bg-[#059669]">
          <Plus size={18} className="mr-2" />Nova Ficha EPI
        </Button>
      </div>

      {/* Info sobre CBO */}
      <Card className="mb-6 border-blue-200 bg-blue-50">
        <CardContent className="p-4">
          <div className="flex items-start gap-3">
            <BookOpen className="text-blue-600 mt-1" size={24} />
            <div>
              <h3 className="font-semibold text-blue-800">Sobre a CBO</h3>
              <p className="text-sm text-blue-600">
                A Classificação Brasileira de Ocupações (CBO) é o documento que reconhece, nomeia e codifica 
                as ocupações do mercado de trabalho brasileiro. Pesquise pelo código (ex: 7152-10) ou nome 
                da ocupação para obter os EPIs recomendados.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Filtros */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div>
          <Label>Filtrar por Funcionário</Label>
          <Select value={selectedFuncionario || "all"} onValueChange={(v) => {
            setSelectedFuncionario(v === "all" ? "" : v);
            setTimeout(fetchFichasEPI, 100);
          }}>
            <SelectTrigger><SelectValue placeholder="Todos" /></SelectTrigger>
            <SelectContent className="z-[9999]">
              <SelectItem value="all">Todos</SelectItem>
              {funcionarios.map(f => (
                <SelectItem key={f.id} value={f.id}>{f.nome}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="flex items-end">
          <Button onClick={fetchFichasEPI} className="w-full bg-[#10B981] hover:bg-[#059669]">
            <Search size={16} className="mr-2" />Buscar
          </Button>
        </div>
      </div>

      {/* Mapa de Risco - Legenda */}
      <Card className="mb-6">
        <CardContent className="p-4">
          <h3 className="font-semibold mb-3 flex items-center gap-2">
            <Shield size={18} className="text-[#10B981]" />
            Legenda do Mapa de Risco
          </h3>
          <div className="flex gap-4 text-sm">
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-red-500 rounded"></div>
              <span>Alta Prioridade - Obrigatório</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-yellow-500 rounded"></div>
              <span>Média Prioridade - Recomendado</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-green-500 rounded"></div>
              <span>Baixa Prioridade - Opcional</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Lista de Fichas */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <div className="spinner w-12 h-12"></div>
        </div>
      ) : fichasEPI.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-gray-400">
            <HardHat className="mx-auto mb-4" size={48} />
            <p>Nenhuma ficha de EPI encontrada</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {fichasEPI.map((ficha) => (
            <Card key={ficha.id}>
              <CardContent className="p-4">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h4 className="font-bold text-lg">{getFuncionarioNome(ficha.funcionario_id)}</h4>
                    <p className="text-sm text-gray-500">
                      CBO: <span className="font-mono font-medium text-blue-600">{ficha.codigo_cbo || "-"}</span>
                      {ficha.ocupacao_cbo && <span className="ml-2">- {ficha.ocupacao_cbo}</span>}
                    </p>
                    <p className="text-sm text-gray-500">Data de Entrega: {new Date(ficha.data_entrega).toLocaleDateString('pt-BR')}</p>
                  </div>
                  <div className="flex gap-2">
                    <Button size="sm" variant="outline" onClick={() => handleExportarFicha(ficha.id)} title="Exportar Ficha">
                      <Download size={14} className="mr-1" />Ficha
                    </Button>
                    <Button size="sm" variant="outline" onClick={() => handleExportarTermo(ficha.id)} title="Exportar Termo">
                      <FileText size={14} className="mr-1" />Termo
                    </Button>
                  </div>
                </div>
                
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="bg-gray-100">
                      <tr>
                        <th className="text-left p-2">EPI</th>
                        <th className="text-center p-2">CA</th>
                        <th className="text-center p-2">Validade</th>
                        <th className="text-center p-2">Prioridade</th>
                        <th className="text-center p-2">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {ficha.epis?.map((epi, idx) => {
                        const vencido = epi.validade && new Date(epi.validade) < new Date();
                        const venceEm30Dias = epi.validade && new Date(epi.validade) < new Date(Date.now() + 30 * 24 * 60 * 60 * 1000);
                        
                        return (
                          <tr key={idx} className="border-t">
                            <td className="p-2">{epi.nome}</td>
                            <td className="p-2 text-center font-mono">{epi.ca || "-"}</td>
                            <td className="p-2 text-center">{epi.validade ? new Date(epi.validade).toLocaleDateString('pt-BR') : "-"}</td>
                            <td className="p-2 text-center">
                              <span className={`px-2 py-1 rounded text-xs ${getPrioridadeCor(epi.prioridade)}`}>
                                {epi.prioridade || 'Média'}
                              </span>
                            </td>
                            <td className="p-2 text-center">
                              {vencido ? (
                                <span className="px-2 py-1 bg-red-100 text-red-700 rounded text-xs flex items-center gap-1 justify-center">
                                  <AlertTriangle size={12} />Vencido
                                </span>
                              ) : venceEm30Dias ? (
                                <span className="px-2 py-1 bg-yellow-100 text-yellow-700 rounded text-xs flex items-center gap-1 justify-center">
                                  <AlertCircle size={12} />Próx. Venc.
                                </span>
                              ) : (
                                <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs flex items-center gap-1 justify-center">
                                  <Check size={12} />OK
                                </span>
                              )}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Modal Nova Ficha EPI */}
      <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Nova Ficha de EPI (CBO)</DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4">
            {/* Seleção de Funcionário */}
            <div>
              <Label>Funcionário *</Label>
              <Select value={formData.funcionario_id} onValueChange={(v) => {
                setFormData({...formData, funcionario_id: v});
              }}>
                <SelectTrigger><SelectValue placeholder="Selecione o funcionário" /></SelectTrigger>
                <SelectContent className="z-[9999]">
                  {funcionarios.map(f => (
                    <SelectItem key={f.id} value={f.id}>{f.nome} - {f.cargo}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Busca por CBO */}
            <div className="border rounded-lg p-4 bg-gray-50">
              <Label className="flex items-center gap-2 mb-3">
                <BookOpen size={16} className="text-blue-600" />
                Buscar Ocupação (CBO)
              </Label>
              
              <div className="flex gap-2 mb-3">
                <Input 
                  placeholder="Digite o código CBO (ex: 7152-10) ou nome da ocupação"
                  value={cboSearch}
                  onChange={(e) => setCboSearch(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSearchCBO()}
                  className="flex-1"
                />
                <Button 
                  onClick={handleSearchCBO}
                  disabled={consultandoCBO}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  {consultandoCBO ? <Loader2 size={16} className="animate-spin" /> : <Search size={16} />}
                  <span className="ml-2">Buscar</span>
                </Button>
              </div>

              {/* Resultados da busca CBO */}
              {cboResults.length > 0 && (
                <div className="space-y-2 max-h-48 overflow-y-auto bg-white rounded border p-2">
                  {cboResults.map((cbo, idx) => (
                    <div 
                      key={idx}
                      className="flex items-center justify-between p-2 rounded hover:bg-blue-50 cursor-pointer border"
                      onClick={() => handleSelectCBO(cbo)}
                    >
                      <div>
                        <span className="font-mono font-bold text-blue-600">{cbo.codigo}</span>
                        <span className="ml-2">{cbo.ocupacao}</span>
                      </div>
                      <Button size="sm" variant="outline">Selecionar</Button>
                    </div>
                  ))}
                </div>
              )}

              {/* CBO não encontrado: oferecer cadastro manual */}
              {cboNotFound && cboResults.length === 0 && (
                <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 mt-2">
                  <p className="text-sm text-amber-800 mb-2">
                    <strong>CBO não encontrado em nossa base.</strong> Cadastre manualmente abaixo —
                    o código e a ocupação serão usados na ficha de EPI deste funcionário.
                  </p>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
                    <Input
                      placeholder="Código CBO (ex: 7152-10)"
                      value={manualCbo.codigo}
                      onChange={(e) => setManualCbo({ ...manualCbo, codigo: e.target.value })}
                      data-testid="input-manual-cbo-codigo"
                    />
                    <Input
                      placeholder="Descrição da ocupação"
                      value={manualCbo.ocupacao}
                      onChange={(e) => setManualCbo({ ...manualCbo, ocupacao: e.target.value })}
                      className="md:col-span-1"
                      data-testid="input-manual-cbo-ocupacao"
                    />
                    <Button
                      onClick={handleAddManualCBO}
                      className="bg-amber-600 hover:bg-amber-700 text-white"
                      data-testid="btn-add-manual-cbo"
                    >
                      Adicionar manualmente
                    </Button>
                  </div>
                </div>
              )}

              {/* CBO Selecionado */}
              {cboInfo && (
                <div className="mt-3 p-3 bg-blue-100 rounded-lg">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-600">Ocupação Selecionada:</p>
                      <p className="font-bold text-blue-800">
                        <span className="font-mono">{cboInfo.codigo}</span> - {cboInfo.ocupacao}
                      </p>
                      {cboInfo.descricao && (
                        <p className="text-sm text-gray-600 mt-1">{cboInfo.descricao}</p>
                      )}
                    </div>
                    <Button 
                      onClick={handleConsultarEPIs}
                      disabled={consultandoEPIs}
                      className="bg-purple-600 hover:bg-purple-700"
                    >
                      {consultandoEPIs ? (
                        <Loader2 size={16} className="animate-spin" />
                      ) : (
                        <Sparkles size={16} />
                      )}
                      <span className="ml-2">Carregar EPIs</span>
                    </Button>
                  </div>
                </div>
              )}
            </div>

            <div>
              <Label>Data de Entrega</Label>
              <Input type="date" value={formData.data_entrega} onChange={(e) => setFormData({...formData, data_entrega: e.target.value})} />
            </div>

            {/* Mapa de Risco */}
            {mapaRisco.length > 0 && (
              <Card className="border-purple-200 bg-purple-50">
                <CardContent className="p-4">
                  <h4 className="font-semibold mb-3 flex items-center gap-2 text-purple-600">
                    <Shield size={18} />
                    Mapa de Risco para CBO {formData.codigo_cbo}
                  </h4>
                  <div className="space-y-2">
                    {mapaRisco.map((risco, idx) => (
                      <div key={idx} className="flex items-center gap-2 p-2 bg-white rounded">
                        <span className={`px-2 py-1 rounded text-xs ${getPrioridadeCor(risco.prioridade)}`}>
                          {risco.prioridade}
                        </span>
                        <span className="font-medium">{risco.risco}</span>
                        <span className="text-gray-500">→</span>
                        <span className="text-sm text-gray-600">{risco.epi_recomendado}</span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* EPIs Sugeridos */}
            {episSugeridos.length > 0 && (
              <div>
                <h4 className="font-semibold mb-3">EPIs Recomendados para esta Ocupação</h4>
                <div className="grid gap-2 max-h-60 overflow-y-auto">
                  {episSugeridos.map((epi, idx) => (
                    <div 
                      key={idx} 
                      className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                        episSelecionados.find(e => e.nome === epi.nome) 
                          ? 'bg-green-50 border-green-500' 
                          : 'bg-white border-gray-200 hover:bg-gray-50'
                      }`}
                      onClick={() => handleToggleEPI(epi)}
                    >
                      <Checkbox 
                        checked={!!episSelecionados.find(e => e.nome === epi.nome)}
                        onCheckedChange={() => handleToggleEPI(epi)}
                      />
                      <div className="flex-1">
                        <p className="font-medium">{epi.nome}</p>
                        <p className="text-sm text-gray-500">
                          CA: {epi.ca || 'A definir'} | Validade: {epi.validade_meses || 12} meses
                        </p>
                      </div>
                      <div className="flex items-center gap-1 flex-shrink-0">
                        {epi.fonte && (
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                              ["PGR", "PCMSO", "LTCAT", "CCT"].includes(
                                (epi.fonte || "").toUpperCase()
                              )
                                ? "bg-emerald-100 text-emerald-700 border border-emerald-300"
                                : "bg-gray-100 text-gray-600 border border-gray-200"
                            }`}
                            title={`Fonte: ${epi.fonte}`}
                            data-testid={`epi-fonte-${idx}`}
                          >
                            {epi.fonte.toUpperCase()}
                          </span>
                        )}
                        <span className={`px-2 py-1 rounded text-xs ${getPrioridadeCor(epi.prioridade)}`}>
                          {epi.prioridade}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
                
                <p className="text-sm text-gray-500 mt-2">
                  {episSelecionados.length} EPI(s) selecionado(s)
                </p>
              </div>
            )}

            <div>
              <Label>Observações</Label>
              <Textarea 
                value={formData.observacoes} 
                onChange={(e) => setFormData({...formData, observacoes: e.target.value})}
                rows={2}
              />
            </div>
          </div>

          <DialogFooter className="gap-2">
            <Button type="button" variant="outline" onClick={closeModal}>Cancelar</Button>
            <Button 
              onClick={handleSalvarFichaEPI} 
              className="bg-[#10B981] hover:bg-[#059669]"
              disabled={!formData.funcionario_id || episSelecionados.length === 0}
            >
              Salvar Ficha
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
