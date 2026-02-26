import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "@/App";
import { Card, CardContent } from "@/components/ui/card";
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
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { 
  Calculator, Users, DollarSign, TrendingUp, TrendingDown, 
  AlertTriangle, Search, BarChart3, PieChart, Loader2
} from "lucide-react";
import { toast } from "sonner";

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

  useEffect(() => {
    fetchFuncionarios();
    fetchCustos();
  }, []);

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

      {/* Explicação do Custo Real */}
      <Card className="mb-6">
        <CardContent className="p-4">
          <h3 className="font-semibold mb-3 flex items-center gap-2">
            <Calculator size={18} className="text-[#10B981]" />
            Cálculo do Custo Real por Funcionário
          </h3>
          <div className="bg-gray-50 p-4 rounded-lg text-sm">
            <p className="font-mono">
              <strong>Custo Real = </strong>Salário + FGTS (8%) + INSS Patronal (~20%) + Vale Transporte + Vale Alimentação + Plano de Saúde + EPIs
            </p>
            <p className="text-gray-500 mt-2">
              <strong>Custo/Hora = </strong>Custo Real Mensal ÷ Horas Trabalhadas (220h CLT)
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
              <Input 
                type="number" 
                min="0" 
                max="100"
                step="0.5"
                value={percentualDissidio} 
                onChange={(e) => setPercentualDissidio(parseFloat(e.target.value) || 0)} 
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
    </div>
  );
}
