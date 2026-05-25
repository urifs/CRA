import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "@/App";
import AnexosManager from "@/components/AnexosManager";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { DecimalInput } from "@/components/DecimalInput";
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
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { 
  Calculator, Users, DollarSign, TrendingUp, TrendingDown, 
  AlertTriangle, Search, BarChart3, PieChart, Loader2, Settings, Save, Plus
} from "lucide-react";
import { toast } from "sonner";

// Botão reutilizável para mostrar a quantos funcionários um campo se aplica
function BotaoAplicaA({ fids, onClick, testId }) {
  const total = (fids || []).length;
  return (
    <Button
      type="button"
      variant="outline"
      size="sm"
      className="w-full mt-1 h-7 text-[11px] justify-start text-gray-600 hover:bg-emerald-50"
      onClick={onClick}
      data-testid={testId}
    >
      <Users size={11} className="mr-1" />
      {total === 0 ? "Aplica a todos os ativos" : `Aplica a ${total} func.`}
    </Button>
  );
}

export default function CustosPage() {
  const [funcionarios, setFuncionarios] = useState([]);
  const [loading, setLoading] = useState(true);
  const [custos, setCustos] = useState([]);
  const [resumo, setResumo] = useState({
    total_salarios: 0,
    total_encargos: 0,
    total_beneficios: 0,
    total_epis: 0,
    custo_total: 0
  });
  const [isDissidioModalOpen, setIsDissidioModalOpen] = useState(false);
  const [isRescisaoModalOpen, setIsRescisaoModalOpen] = useState(false);
  const [selectedFuncionario, setSelectedFuncionario] = useState("");
  const [percentualDissidio, setPercentualDissidio] = useState(5);
  const [simulacaoDissidio, setSimulacaoDissidio] = useState(null);
  const [simulacaoRescisao, setSimulacaoRescisao] = useState(null);
  const [calculando, setCalculando] = useState(false);
  
  // Configuração editável de custos
  const [configCustos, setConfigCustos] = useState({
    fgts_aliquota: 8.0,
    fgts_funcionario_ids: [],
    inss_patronal_aliquota: 20.0,
    inss_patronal_funcionario_ids: [],
    vale_transporte: 0,
    vale_transporte_funcionario_ids: [],
    vale_alimentacao: 0,
    vale_alimentacao_funcionario_ids: [],
    plano_saude: 0,
    plano_saude_funcionario_ids: [],
    outros_beneficios: 150,
    outros_beneficios_funcionario_ids: [],
    epis_custo_mensal: 50,
    epis_custo_mensal_funcionario_ids: [],
    horas_mes: 220,
    custos_extras: [],
  });
  const [isConfigModalOpen, setIsConfigModalOpen] = useState(false);
  const [salvandoConfig, setSalvandoConfig] = useState(false);
  const [extraEditandoFuncs, setExtraEditandoFuncs] = useState(null); // { extra_id }
  const [campoPadraoEditandoFuncs, setCampoPadraoEditandoFuncs] = useState(null); // string nome do campo

  useEffect(() => {
    fetchFuncionarios();
    fetchCustos();
    fetchConfig();
  }, []);

  const fetchConfig = async () => {
    try {
      const { data } = await axios.get(`${API}/rh/custos/config`);
      setConfigCustos({
        fgts_aliquota: data.fgts_aliquota ?? 8,
        fgts_funcionario_ids: data.fgts_funcionario_ids ?? [],
        inss_patronal_aliquota: data.inss_patronal_aliquota ?? 20,
        inss_patronal_funcionario_ids: data.inss_patronal_funcionario_ids ?? [],
        vale_transporte: data.vale_transporte ?? 0,
        vale_transporte_funcionario_ids: data.vale_transporte_funcionario_ids ?? [],
        vale_alimentacao: data.vale_alimentacao ?? 0,
        vale_alimentacao_funcionario_ids: data.vale_alimentacao_funcionario_ids ?? [],
        plano_saude: data.plano_saude ?? 0,
        plano_saude_funcionario_ids: data.plano_saude_funcionario_ids ?? [],
        outros_beneficios: data.outros_beneficios ?? 0,
        outros_beneficios_funcionario_ids: data.outros_beneficios_funcionario_ids ?? [],
        epis_custo_mensal: data.epis_custo_mensal ?? 0,
        epis_custo_mensal_funcionario_ids: data.epis_custo_mensal_funcionario_ids ?? [],
        horas_mes: data.horas_mes ?? 220,
        custos_extras: data.custos_extras ?? [],
      });
    } catch (e) {
      console.error("Erro ao carregar config", e);
    }
  };

  const adicionarCustoExtra = () => {
    setConfigCustos({
      ...configCustos,
      custos_extras: [
        ...(configCustos.custos_extras || []),
        {
          id: `temp_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`,
          nome: "",
          tipo: "fixo",
          valor: 0,
          funcionario_ids: [],
        },
      ],
    });
  };

  const atualizarCustoExtra = (idx, campo, valor) => {
    const novos = [...(configCustos.custos_extras || [])];
    novos[idx] = { ...novos[idx], [campo]: valor };
    setConfigCustos({ ...configCustos, custos_extras: novos });
  };

  const removerCustoExtra = (idx) => {
    const novos = [...(configCustos.custos_extras || [])];
    novos.splice(idx, 1);
    setConfigCustos({ ...configCustos, custos_extras: novos });
  };

  const salvarConfig = async () => {
    setSalvandoConfig(true);
    try {
      await axios.put(`${API}/rh/custos/config`, configCustos);
      toast.success("Configuração de custos salva. Valores recalculados.");
      setIsConfigModalOpen(false);
      await fetchCustos();
    } catch (e) {
      toast.error(e.response?.data?.detail || "Erro ao salvar configuração");
    } finally {
      setSalvandoConfig(false);
    }
  };

  const fetchFuncionarios = async () => {
    try {
      const response = await axios.get(`${API}/rh/funcionarios?status=ativo`);
      setFuncionarios(response.data);
    } catch (error) {
      console.error("Erro ao carregar funcionários:", error);
    }
  };

  const fetchCustos = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/rh/custos`);
      setCustos(response.data.funcionarios || []);
      setResumo(response.data.resumo || {
        total_salarios: 0,
        total_encargos: 0,
        total_beneficios: 0,
        total_epis: 0,
        custo_total: 0
      });
    } catch (error) {
      toast.error("Erro ao carregar custos");
    } finally {
      setLoading(false);
    }
  };

  const handleSimularDissidio = async () => {
    setCalculando(true);
    try {
      const response = await axios.post(`${API}/rh/custos/simular-dissidio`, {
        percentual: percentualDissidio
      });
      setSimulacaoDissidio(response.data);
    } catch (error) {
      toast.error("Erro ao simular dissídio");
    } finally {
      setCalculando(false);
    }
  };

  const handleSimularRescisao = async () => {
    if (!selectedFuncionario) {
      toast.error("Selecione um funcionário");
      return;
    }
    
    setCalculando(true);
    try {
      const response = await axios.post(`${API}/rh/custos/simular-rescisao`, {
        funcionario_id: selectedFuncionario
      });
      setSimulacaoRescisao(response.data);
    } catch (error) {
      toast.error("Erro ao simular rescisão");
    } finally {
      setCalculando(false);
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat("pt-BR", {
      style: "currency",
      currency: "BRL"
    }).format(value || 0);
  };

  const getFuncionarioNome = (id) => {
    const func = funcionarios.find(f => f.id === id);
    return func?.nome || "-";
  };

  if (loading) {
    return <div className="flex items-center justify-center min-h-[400px]"><div className="spinner w-12 h-12"></div></div>;
  }

  return (
    <div data-testid="custos-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Gestão de Custos RH</h1>
          <p className="text-gray-500 mt-1">Análise de custos com pessoal</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => setIsConfigModalOpen(true)} className="border-emerald-500 text-emerald-600">
            <Settings size={18} className="mr-2" />Configurar Custos
          </Button>
          <Button variant="outline" onClick={() => setIsDissidioModalOpen(true)} className="border-orange-500 text-orange-500">
            <TrendingUp size={18} className="mr-2" />Simular Dissídio
          </Button>
          <Button variant="outline" onClick={() => setIsRescisaoModalOpen(true)} className="border-red-500 text-red-500">
            <AlertTriangle size={18} className="mr-2" />Provisão Rescisão
          </Button>
        </div>
      </div>

      {/* Cards de Resumo */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
        <Card>
          <CardContent className="p-4 text-center">
            <DollarSign className="mx-auto text-green-600 mb-2" size={24} />
            <p className="text-xl font-bold text-green-600">{formatCurrency(resumo.total_salarios)}</p>
            <p className="text-sm text-gray-500">Salários</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <Calculator className="mx-auto text-orange-600 mb-2" size={24} />
            <p className="text-xl font-bold text-orange-600">{formatCurrency(resumo.total_encargos)}</p>
            <p className="text-sm text-gray-500">Encargos</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <Users className="mx-auto text-blue-600 mb-2" size={24} />
            <p className="text-xl font-bold text-blue-600">{formatCurrency(resumo.total_beneficios)}</p>
            <p className="text-sm text-gray-500">Benefícios</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <BarChart3 className="mx-auto text-purple-600 mb-2" size={24} />
            <p className="text-xl font-bold text-purple-600">{formatCurrency(resumo.total_epis)}</p>
            <p className="text-sm text-gray-500">EPIs</p>
          </CardContent>
        </Card>
        <Card className="bg-gray-900">
          <CardContent className="p-4 text-center">
            <PieChart className="mx-auto text-white mb-2" size={24} />
            <p className="text-xl font-bold text-white">{formatCurrency(resumo.custo_total)}</p>
            <p className="text-sm text-gray-400">Custo Total</p>
          </CardContent>
        </Card>
      </div>

      {/* Explicação do Custo Real (com valores atuais) */}
      <Card className="mb-6">
        <CardContent className="p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold flex items-center gap-2">
              <Calculator size={18} className="text-[#10B981]" />
              Cálculo do Custo Real por Funcionário
            </h3>
            <Button size="sm" variant="ghost" onClick={() => setIsConfigModalOpen(true)} className="text-emerald-600">
              <Settings size={14} className="mr-1" />
              Editar valores
            </Button>
          </div>
          <div className="bg-gray-50 p-4 rounded-lg text-sm">
            <p className="font-mono">
              <strong>Custo Real = </strong>Salário 
              + FGTS ({configCustos.fgts_aliquota}%) 
              + INSS Patronal ({configCustos.inss_patronal_aliquota}%) 
              + VT ({formatCurrency(configCustos.vale_transporte)}) 
              + VA ({formatCurrency(configCustos.vale_alimentacao)}) 
              + Plano Saúde ({formatCurrency(configCustos.plano_saude)})
              + Outros ({formatCurrency(configCustos.outros_beneficios)})
              + EPIs ({formatCurrency(configCustos.epis_custo_mensal)}/mês)
            </p>
            <p className="text-gray-500 mt-2">
              <strong>Custo/Hora = </strong>Custo Real Mensal ÷ {configCustos.horas_mes}h (jornada-base)
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Tabela de Custos por Funcionário */}
      <Card>
        <CardContent className="p-4">
          <h3 className="font-semibold mb-4">Custo Real por Funcionário</h3>
          
          {custos.length === 0 ? (
            <p className="text-center text-gray-400 py-8">Nenhum funcionário ativo</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-100">
                  <tr>
                    <th className="text-left p-3 font-medium text-gray-600">Funcionário</th>
                    <th className="text-right p-3 font-medium text-gray-600">Salário</th>
                    <th className="text-right p-3 font-medium text-gray-600">FGTS</th>
                    <th className="text-right p-3 font-medium text-gray-600">INSS Patr.</th>
                    <th className="text-right p-3 font-medium text-gray-600">Benefícios</th>
                    <th className="text-right p-3 font-medium text-gray-600">EPIs</th>
                    <th className="text-right p-3 font-medium text-gray-600">Custo Total</th>
                    <th className="text-right p-3 font-medium text-gray-600">Custo/Hora</th>
                  </tr>
                </thead>
                <tbody>
                  {custos.map((c) => (
                    <tr key={c.funcionario_id} className="border-t hover:bg-gray-50">
                      <td className="p-3 font-medium">{c.nome}</td>
                      <td className="p-3 text-right">{formatCurrency(c.salario)}</td>
                      <td className="p-3 text-right text-orange-600">{formatCurrency(c.fgts)}</td>
                      <td className="p-3 text-right text-red-600">{formatCurrency(c.inss_patronal)}</td>
                      <td className="p-3 text-right text-blue-600">{formatCurrency(c.beneficios)}</td>
                      <td className="p-3 text-right text-purple-600">{formatCurrency(c.epis)}</td>
                      <td className="p-3 text-right font-bold">{formatCurrency(c.custo_total)}</td>
                      <td className="p-3 text-right font-bold text-[#10B981]">{formatCurrency(c.custo_hora)}/h</td>
                    </tr>
                  ))}
                </tbody>
                <tfoot className="bg-gray-100 font-bold">
                  <tr>
                    <td className="p-3">TOTAL ({custos.length} funcionários)</td>
                    <td className="p-3 text-right">{formatCurrency(resumo.total_salarios)}</td>
                    <td className="p-3 text-right text-orange-600">{formatCurrency(custos.reduce((s, c) => s + (c.fgts || 0), 0))}</td>
                    <td className="p-3 text-right text-red-600">{formatCurrency(custos.reduce((s, c) => s + (c.inss_patronal || 0), 0))}</td>
                    <td className="p-3 text-right text-blue-600">{formatCurrency(resumo.total_beneficios)}</td>
                    <td className="p-3 text-right text-purple-600">{formatCurrency(resumo.total_epis)}</td>
                    <td className="p-3 text-right">{formatCurrency(resumo.custo_total)}</td>
                    <td className="p-3 text-right text-[#10B981]">-</td>
                  </tr>
                </tfoot>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Modal Simulação Dissídio */}
      <Dialog open={isDissidioModalOpen} onOpenChange={setIsDissidioModalOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <TrendingUp className="text-orange-500" size={20} />
              Simulação de Dissídio
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4">
            <div>
              <Label>Percentual de Aumento (%)</Label>
              <DecimalInput
                value={percentualDissidio}
                onChange={(v) => setPercentualDissidio(v)}
                placeholder="0,00"
              />
            </div>
            
            <Button 
              onClick={handleSimularDissidio} 
              className="w-full bg-orange-500 hover:bg-orange-600"
              disabled={calculando}
            >
              {calculando ? <Loader2 className="animate-spin mr-2" size={16} /> : null}
              Calcular Impacto
            </Button>
            
            {simulacaoDissidio && (
              <div className="space-y-3 pt-4 border-t">
                <h4 className="font-semibold">Resultado da Simulação</h4>
                
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 bg-gray-50 rounded-lg">
                    <p className="text-sm text-gray-500">Folha Atual</p>
                    <p className="text-lg font-bold">{formatCurrency(simulacaoDissidio.folha_atual)}</p>
                  </div>
                  <div className="p-3 bg-orange-50 rounded-lg">
                    <p className="text-sm text-gray-500">Folha com Dissídio</p>
                    <p className="text-lg font-bold text-orange-600">{formatCurrency(simulacaoDissidio.folha_com_dissidio)}</p>
                  </div>
                </div>
                
                <div className="p-4 bg-red-50 rounded-lg text-center">
                  <p className="text-sm text-gray-500">Impacto Mensal no Caixa</p>
                  <p className="text-2xl font-bold text-red-600">+ {formatCurrency(simulacaoDissidio.impacto_mensal)}</p>
                  <p className="text-sm text-gray-500 mt-2">Impacto Anual</p>
                  <p className="text-lg font-bold text-red-600">+ {formatCurrency(simulacaoDissidio.impacto_anual)}</p>
                </div>
              </div>
            )}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setIsDissidioModalOpen(false)}>Fechar</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Modal Provisão Rescisão */}
      <Dialog open={isRescisaoModalOpen} onOpenChange={setIsRescisaoModalOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <AlertTriangle className="text-red-500" size={20} />
              Provisão de Rescisão
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4">
            <div>
              <Label>Funcionário</Label>
              <Select value={selectedFuncionario} onValueChange={setSelectedFuncionario}>
                <SelectTrigger><SelectValue placeholder="Selecione um funcionário" /></SelectTrigger>
                <SelectContent className="z-[9999]">
                  {funcionarios.map(f => (
                    <SelectItem key={f.id} value={f.id}>{f.nome}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <Button 
              onClick={handleSimularRescisao} 
              className="w-full bg-red-500 hover:bg-red-600"
              disabled={calculando || !selectedFuncionario}
            >
              {calculando ? <Loader2 className="animate-spin mr-2" size={16} /> : null}
              Calcular Rescisão
            </Button>
            
            {simulacaoRescisao && (
              <div className="space-y-3 pt-4 border-t">
                <h4 className="font-semibold">Valores de Rescisão (sem justa causa)</h4>
                
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between p-2 bg-gray-50 rounded">
                    <span>Saldo de Salário</span>
                    <span className="font-medium">{formatCurrency(simulacaoRescisao.saldo_salario)}</span>
                  </div>
                  <div className="flex justify-between p-2 bg-gray-50 rounded">
                    <span>Aviso Prévio ({simulacaoRescisao.dias_aviso_previo} dias)</span>
                    <span className="font-medium">{formatCurrency(simulacaoRescisao.aviso_previo)}</span>
                  </div>
                  <div className="flex justify-between p-2 bg-gray-50 rounded">
                    <span>Férias Vencidas + 1/3</span>
                    <span className="font-medium">{formatCurrency(simulacaoRescisao.ferias_vencidas)}</span>
                  </div>
                  <div className="flex justify-between p-2 bg-gray-50 rounded">
                    <span>Férias Proporcionais + 1/3</span>
                    <span className="font-medium">{formatCurrency(simulacaoRescisao.ferias_proporcionais)}</span>
                  </div>
                  <div className="flex justify-between p-2 bg-gray-50 rounded">
                    <span>13º Proporcional</span>
                    <span className="font-medium">{formatCurrency(simulacaoRescisao.decimo_terceiro)}</span>
                  </div>
                  <div className="flex justify-between p-2 bg-orange-50 rounded">
                    <span>Saldo FGTS</span>
                    <span className="font-medium text-orange-600">{formatCurrency(simulacaoRescisao.fgts_saldo)}</span>
                  </div>
                  <div className="flex justify-between p-2 bg-red-50 rounded">
                    <span>Multa FGTS (40%)</span>
                    <span className="font-medium text-red-600">{formatCurrency(simulacaoRescisao.multa_fgts)}</span>
                  </div>
                </div>
                
                <div className="p-4 bg-red-100 rounded-lg text-center">
                  <p className="text-sm text-gray-600">Custo Total da Rescisão</p>
                  <p className="text-3xl font-bold text-red-600">{formatCurrency(simulacaoRescisao.total)}</p>
                </div>
                
                <p className="text-xs text-gray-500">
                  * Tempo de empresa: {simulacaoRescisao.meses_trabalhados} meses
                </p>
              </div>
            )}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => {
              setIsRescisaoModalOpen(false);
              setSimulacaoRescisao(null);
              setSelectedFuncionario("");
            }}>Fechar</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      {/* Modal de Configuração de Custos */}
      <Dialog open={isConfigModalOpen} onOpenChange={setIsConfigModalOpen}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Settings className="text-emerald-600" size={20} />
              Configurar valores de Custos RH
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <p className="text-sm text-gray-500">
              Estes valores são aplicados automaticamente a todos os funcionários ativos no cálculo do custo real e nas simulações.
            </p>
            <div className="grid grid-cols-2 gap-4">
              {/* FGTS */}
              <div>
                <Label>FGTS (%)</Label>
                <DecimalInput
                  value={configCustos.fgts_aliquota}
                  onChange={(v) => setConfigCustos({ ...configCustos, fgts_aliquota: v })}
                  placeholder="8,00"
                  data-testid="input-config-fgts"
                />
                <BotaoAplicaA
                  fids={configCustos.fgts_funcionario_ids}
                  onClick={() => setCampoPadraoEditandoFuncs("fgts_funcionario_ids")}
                  testId="btn-aplica-fgts"
                />
              </div>
              {/* INSS */}
              <div>
                <Label>INSS Patronal (%)</Label>
                <DecimalInput
                  value={configCustos.inss_patronal_aliquota}
                  onChange={(v) => setConfigCustos({ ...configCustos, inss_patronal_aliquota: v })}
                  placeholder="20,00"
                  data-testid="input-config-inss"
                />
                <BotaoAplicaA
                  fids={configCustos.inss_patronal_funcionario_ids}
                  onClick={() => setCampoPadraoEditandoFuncs("inss_patronal_funcionario_ids")}
                  testId="btn-aplica-inss"
                />
              </div>
              {/* VT */}
              <div>
                <Label>Vale Transporte (R$/mês)</Label>
                <DecimalInput
                  value={configCustos.vale_transporte}
                  onChange={(v) => setConfigCustos({ ...configCustos, vale_transporte: v })}
                  placeholder="0,00"
                  data-testid="input-config-vt"
                />
                <BotaoAplicaA
                  fids={configCustos.vale_transporte_funcionario_ids}
                  onClick={() => setCampoPadraoEditandoFuncs("vale_transporte_funcionario_ids")}
                  testId="btn-aplica-vt"
                />
              </div>
              {/* VA */}
              <div>
                <Label>Vale Alimentação (R$/mês)</Label>
                <DecimalInput
                  value={configCustos.vale_alimentacao}
                  onChange={(v) => setConfigCustos({ ...configCustos, vale_alimentacao: v })}
                  placeholder="0,00"
                  data-testid="input-config-va"
                />
                <BotaoAplicaA
                  fids={configCustos.vale_alimentacao_funcionario_ids}
                  onClick={() => setCampoPadraoEditandoFuncs("vale_alimentacao_funcionario_ids")}
                  testId="btn-aplica-va"
                />
              </div>
              {/* Plano Saúde */}
              <div>
                <Label>Plano de Saúde (R$/mês)</Label>
                <DecimalInput
                  value={configCustos.plano_saude}
                  onChange={(v) => setConfigCustos({ ...configCustos, plano_saude: v })}
                  placeholder="0,00"
                  data-testid="input-config-saude"
                />
                <BotaoAplicaA
                  fids={configCustos.plano_saude_funcionario_ids}
                  onClick={() => setCampoPadraoEditandoFuncs("plano_saude_funcionario_ids")}
                  testId="btn-aplica-saude"
                />
              </div>
              {/* Outros */}
              <div>
                <Label>Outros Benefícios (R$/mês)</Label>
                <DecimalInput
                  value={configCustos.outros_beneficios}
                  onChange={(v) => setConfigCustos({ ...configCustos, outros_beneficios: v })}
                  placeholder="0,00"
                  data-testid="input-config-outros"
                />
                <BotaoAplicaA
                  fids={configCustos.outros_beneficios_funcionario_ids}
                  onClick={() => setCampoPadraoEditandoFuncs("outros_beneficios_funcionario_ids")}
                  testId="btn-aplica-outros"
                />
              </div>
              {/* EPIs */}
              <div>
                <Label>EPIs (R$/mês)</Label>
                <DecimalInput
                  value={configCustos.epis_custo_mensal}
                  onChange={(v) => setConfigCustos({ ...configCustos, epis_custo_mensal: v })}
                  placeholder="0,00"
                  data-testid="input-config-epis"
                />
                <BotaoAplicaA
                  fids={configCustos.epis_custo_mensal_funcionario_ids}
                  onClick={() => setCampoPadraoEditandoFuncs("epis_custo_mensal_funcionario_ids")}
                  testId="btn-aplica-epis"
                />
              </div>
              <div>
                <Label>Horas/mês (jornada-base)</Label>
                <Input
                  type="number"
                  min="1"
                  value={configCustos.horas_mes}
                  onChange={(e) => setConfigCustos({ ...configCustos, horas_mes: parseInt(e.target.value) || 220 })}
                  data-testid="input-config-horas"
                />
              </div>
            </div>

            {/* Custos Extras Personalizáveis */}
            <div className="border-t pt-4">
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-semibold flex items-center gap-2">
                  <Plus size={16} className="text-emerald-600" />
                  Custos Extras Personalizados
                </h4>
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  onClick={adicionarCustoExtra}
                  className="border-emerald-500 text-emerald-600"
                  data-testid="btn-add-custo-extra"
                >
                  <Plus size={14} className="mr-1" />
                  Adicionar custo
                </Button>
              </div>
              <p className="text-xs text-gray-500 mb-3">
                Adicione custos personalizados (cesta básica, comissão, PLR, convênio etc). Por padrão aplica a TODOS os funcionários ativos. Click em "Aplicar a..." para escolher quem recebe.
              </p>
              {(configCustos.custos_extras || []).length === 0 ? (
                <p className="text-sm text-gray-400 italic text-center py-3 bg-gray-50 rounded">
                  Nenhum custo extra cadastrado.
                </p>
              ) : (
                <div className="space-y-2">
                  {configCustos.custos_extras.map((ce, idx) => (
                    <div key={ce.id || idx} className="border rounded-lg p-3 bg-emerald-50/30">
                      <div className="grid grid-cols-12 gap-2 items-end">
                        <div className="col-span-4">
                          <Label className="text-xs">Descrição*</Label>
                          <Input
                            placeholder="Ex: Cesta básica, PLR, Convênio odonto..."
                            value={ce.nome || ""}
                            onChange={(e) => atualizarCustoExtra(idx, "nome", e.target.value)}
                            className="h-9"
                            data-testid={`input-extra-nome-${idx}`}
                          />
                        </div>
                        <div className="col-span-2">
                          <Label className="text-xs">Tipo</Label>
                          <Select value={ce.tipo || "fixo"} onValueChange={(v) => atualizarCustoExtra(idx, "tipo", v)}>
                            <SelectTrigger className="h-9" data-testid={`select-extra-tipo-${idx}`}>
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="fixo">R$ fixo</SelectItem>
                              <SelectItem value="percentual">% salário</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                        <div className="col-span-2">
                          <Label className="text-xs">Valor</Label>
                          <DecimalInput
                            value={ce.valor || 0}
                            onChange={(v) => atualizarCustoExtra(idx, "valor", v)}
                            placeholder="0,00"
                            data-testid={`input-extra-valor-${idx}`}
                          />
                        </div>
                        <div className="col-span-3">
                          <Label className="text-xs">Aplica a</Label>
                          <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            className="w-full h-9 justify-start text-xs"
                            onClick={() => setExtraEditandoFuncs(idx)}
                            data-testid={`btn-extra-funcs-${idx}`}
                          >
                            <Users size={12} className="mr-1" />
                            {(ce.funcionario_ids || []).length === 0
                              ? "Todos os ativos"
                              : `${ce.funcionario_ids.length} funcionário(s)`}
                          </Button>
                        </div>
                        <div className="col-span-1">
                          <Button
                            type="button"
                            size="sm"
                            variant="ghost"
                            className="text-rose-600 h-9 w-full"
                            onClick={() => removerCustoExtra(idx)}
                            data-testid={`btn-remover-extra-${idx}`}
                          >
                            ✕
                          </Button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="bg-emerald-50 border border-emerald-200 rounded p-3 text-xs text-emerald-700">
              💡 Valores típicos no Brasil: FGTS 8%, INSS Patronal 20% (Anexo IV pode variar 7,5%–27,5%). Salve para recalcular toda a tabela.
            </div>

            <div className="pt-2 border-t border-gray-200">
              <AnexosManager
                entityType="custo_rh"
                entityId="config-global"
                title="Documentos / Tabelas oficiais (INSS, FGTS, CCT)"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsConfigModalOpen(false)}>Cancelar</Button>
            <Button
              onClick={salvarConfig}
              disabled={salvandoConfig}
              className="bg-emerald-600 hover:bg-emerald-700"
              data-testid="btn-salvar-config-custos"
            >
              {salvandoConfig ? <Loader2 className="animate-spin mr-2" size={16} /> : <Save size={16} className="mr-2" />}
              Salvar e recalcular
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      {/* Mini-dialog: selecionar funcionários para um custo extra */}
      <Dialog open={extraEditandoFuncs !== null} onOpenChange={(o) => !o && setExtraEditandoFuncs(null)}>
        <DialogContent className="max-w-xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              Aplicar custo a quais funcionários?
            </DialogTitle>
          </DialogHeader>
          {extraEditandoFuncs !== null && configCustos.custos_extras?.[extraEditandoFuncs] && (() => {
            const ce = configCustos.custos_extras[extraEditandoFuncs];
            const fids = ce.funcionario_ids || [];
            const todos = fids.length === 0;
            const toggleFunc = (id) => {
              const novo = fids.includes(id)
                ? fids.filter(x => x !== id)
                : [...fids, id];
              atualizarCustoExtra(extraEditandoFuncs, "funcionario_ids", novo);
            };
            return (
              <div className="space-y-3">
                <p className="text-sm text-gray-600">
                  Custo: <strong>{ce.nome || "(sem nome)"}</strong>
                </p>
                <label className="flex items-center gap-2 p-2 bg-emerald-50 rounded cursor-pointer">
                  <input
                    type="checkbox"
                    checked={todos}
                    onChange={() => atualizarCustoExtra(extraEditandoFuncs, "funcionario_ids", todos ? [funcionarios[0]?.id || ""].filter(Boolean) : [])}
                    data-testid="check-todos-funcs-extra"
                  />
                  <span className="text-sm font-semibold text-emerald-700">
                    Aplicar a todos os funcionários ativos
                  </span>
                </label>
                {!todos && (
                  <div className="border rounded divide-y max-h-80 overflow-y-auto">
                    {funcionarios.length === 0 ? (
                      <p className="p-4 text-center text-sm text-gray-400">Nenhum funcionário ativo</p>
                    ) : funcionarios.map((f) => (
                      <label key={f.id} className="flex items-center gap-2 p-2 hover:bg-gray-50 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={fids.includes(f.id)}
                          onChange={() => toggleFunc(f.id)}
                          data-testid={`check-func-extra-${f.id}`}
                        />
                        <div className="flex-1">
                          <p className="text-sm font-medium">{f.nome}</p>
                          <p className="text-xs text-gray-500">{f.cargo}</p>
                        </div>
                      </label>
                    ))}
                  </div>
                )}
              </div>
            );
          })()}
          <DialogFooter>
            <Button onClick={() => setExtraEditandoFuncs(null)} className="bg-emerald-600 hover:bg-emerald-700">
              OK
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      {/* Mini-dialog: selecionar funcionários para um CAMPO PADRÃO */}
      <Dialog open={!!campoPadraoEditandoFuncs} onOpenChange={(o) => !o && setCampoPadraoEditandoFuncs(null)}>
        <DialogContent className="max-w-xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              Aplicar este custo a quais funcionários?
            </DialogTitle>
          </DialogHeader>
          {campoPadraoEditandoFuncs && (() => {
            const campo = campoPadraoEditandoFuncs;
            const fids = configCustos[campo] || [];
            const todos = fids.length === 0;
            const setFids = (novo) => setConfigCustos({ ...configCustos, [campo]: novo });
            const labelMap = {
              fgts_funcionario_ids: "FGTS",
              inss_patronal_funcionario_ids: "INSS Patronal",
              vale_transporte_funcionario_ids: "Vale Transporte",
              vale_alimentacao_funcionario_ids: "Vale Alimentação",
              plano_saude_funcionario_ids: "Plano de Saúde",
              outros_beneficios_funcionario_ids: "Outros Benefícios",
              epis_custo_mensal_funcionario_ids: "EPIs",
            };
            const toggleFunc = (id) => {
              const novo = fids.includes(id) ? fids.filter(x => x !== id) : [...fids, id];
              setFids(novo);
            };
            return (
              <div className="space-y-3">
                <p className="text-sm text-gray-600">
                  Custo: <strong>{labelMap[campo]}</strong>
                </p>
                <label className="flex items-center gap-2 p-2 bg-emerald-50 rounded cursor-pointer">
                  <input
                    type="checkbox"
                    checked={todos}
                    onChange={() => setFids(todos ? [funcionarios[0]?.id || ""].filter(Boolean) : [])}
                    data-testid="check-todos-funcs-padrao"
                  />
                  <span className="text-sm font-semibold text-emerald-700">
                    Aplicar a todos os funcionários ativos
                  </span>
                </label>
                {!todos && (
                  <div className="border rounded divide-y max-h-80 overflow-y-auto">
                    {funcionarios.length === 0 ? (
                      <p className="p-4 text-center text-sm text-gray-400">Nenhum funcionário ativo</p>
                    ) : funcionarios.map((f) => (
                      <label key={f.id} className="flex items-center gap-2 p-2 hover:bg-gray-50 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={fids.includes(f.id)}
                          onChange={() => toggleFunc(f.id)}
                          data-testid={`check-func-padrao-${f.id}`}
                        />
                        <div className="flex-1">
                          <p className="text-sm font-medium">{f.nome}</p>
                          <p className="text-xs text-gray-500">{f.cargo}</p>
                        </div>
                      </label>
                    ))}
                  </div>
                )}
              </div>
            );
          })()}
          <DialogFooter>
            <Button onClick={() => setCampoPadraoEditandoFuncs(null)} className="bg-emerald-600 hover:bg-emerald-700">
              OK
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
