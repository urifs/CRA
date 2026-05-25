import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "@/App";
import AnexosManager from "@/components/AnexosManager";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { MoneyInput } from "@/components/MoneyInput";
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
  DollarSign, Users, Calculator, FileText, Download, 
  Search, Plus, Edit, Trash2, Calendar, Loader2, Eye
} from "lucide-react";
import { toast } from "sonner";

export default function FolhaPagamentoPage() {
  const [funcionarios, setFuncionarios] = useState([]);
  const [folhas, setFolhas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedMes, setSelectedMes] = useState(new Date().getMonth() + 1);
  const [selectedAno, setSelectedAno] = useState(new Date().getFullYear());
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [viewingFolha, setViewingFolha] = useState(null);
  const [calculando, setCalculando] = useState(false);
  
  const [formData, setFormData] = useState({
    funcionario_id: "",
    mes: new Date().getMonth() + 1,
    ano: new Date().getFullYear(),
    salario_base: 0,
    horas_extras: 0,
    valor_hora_extra: 0,
    adicional_noturno: 0,
    comissoes: 0,
    vale_transporte: 0,
    vale_alimentacao: 0,
    plano_saude: 0,
    outros_descontos: 0,
    observacoes: ""
  });

  // Tabelas de alíquotas atuais (2024/2025)
  const TABELA_INSS_2025 = [
    { ate: 1518.00, aliquota: 7.5 },
    { ate: 2793.88, aliquota: 9.0 },
    { ate: 4190.83, aliquota: 12.0 },
    { ate: 8157.41, aliquota: 14.0 }
  ];

  const TABELA_IRPF_2025 = [
    { ate: 2259.20, aliquota: 0, deducao: 0 },
    { ate: 2826.65, aliquota: 7.5, deducao: 169.44 },
    { ate: 3751.05, aliquota: 15.0, deducao: 381.44 },
    { ate: 4664.68, aliquota: 22.5, deducao: 662.77 },
    { ate: Infinity, aliquota: 27.5, deducao: 896.00 }
  ];

  const FGTS_ALIQUOTA = 8.0;

  useEffect(() => {
    fetchFuncionarios();
    fetchFolhas();
  }, [selectedMes, selectedAno]);

  const fetchFuncionarios = async () => {
    try {
      const response = await axios.get(`${API}/rh/funcionarios?status=ativo`);
      setFuncionarios(response.data);
    } catch (error) {
      console.error("Erro ao carregar funcionários:", error);
    }
  };

  const fetchFolhas = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/rh/folha-pagamento?mes=${selectedMes}&ano=${selectedAno}`);
      setFolhas(response.data);
    } catch (error) {
      toast.error("Erro ao carregar folhas");
    } finally {
      setLoading(false);
    }
  };

  const calcularINSS = (salarioBruto) => {
    let inss = 0;
    let salarioRestante = salarioBruto;
    let faixaAnterior = 0;

    for (const faixa of TABELA_INSS_2025) {
      if (salarioRestante <= 0) break;
      
      const base = Math.min(salarioRestante, faixa.ate - faixaAnterior);
      inss += base * (faixa.aliquota / 100);
      salarioRestante -= base;
      faixaAnterior = faixa.ate;
    }

    return Math.min(inss, 951.01); // Teto INSS 2025
  };

  const calcularIRPF = (baseCalculo) => {
    for (const faixa of TABELA_IRPF_2025) {
      if (baseCalculo <= faixa.ate) {
        return Math.max(0, (baseCalculo * faixa.aliquota / 100) - faixa.deducao);
      }
    }
    return 0;
  };

  const calcularFolha = () => {
    const salarioBruto = parseFloat(formData.salario_base) + 
      parseFloat(formData.horas_extras || 0) * parseFloat(formData.valor_hora_extra || 0) +
      parseFloat(formData.adicional_noturno || 0) +
      parseFloat(formData.comissoes || 0);

    const inss = calcularINSS(salarioBruto);
    const baseIRPF = salarioBruto - inss;
    const irpf = calcularIRPF(baseIRPF);
    const fgts = salarioBruto * (FGTS_ALIQUOTA / 100);

    const totalDescontos = inss + irpf + 
      parseFloat(formData.vale_transporte || 0) +
      parseFloat(formData.vale_alimentacao || 0) +
      parseFloat(formData.plano_saude || 0) +
      parseFloat(formData.outros_descontos || 0);

    const salarioLiquido = salarioBruto - totalDescontos;

    return {
      salario_bruto: salarioBruto,
      inss,
      irpf,
      fgts,
      total_descontos: totalDescontos,
      salario_liquido: salarioLiquido
    };
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setCalculando(true);
    try {
      const calculos = calcularFolha();
      const dataToSend = {
        ...formData,
        ...calculos
      };
      
      await axios.post(`${API}/rh/folha-pagamento`, dataToSend);
      toast.success("Folha de pagamento gerada!");
      fetchFolhas();
      closeModal();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao gerar folha");
    } finally {
      setCalculando(false);
    }
  };

  const handleGerarHolerite = async (folhaId) => {
    try {
      const response = await axios.get(`${API}/rh/folha-pagamento/${folhaId}/holerite`, {
        responseType: 'blob'
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `holerite_${folhaId}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      toast.success("Holerite gerado!");
    } catch (error) {
      toast.error("Erro ao gerar holerite");
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Deseja excluir esta folha?")) return;
    try {
      await axios.delete(`${API}/rh/folha-pagamento/${id}`);
      toast.success("Folha excluída!");
      fetchFolhas();
    } catch (error) {
      toast.error("Erro ao excluir");
    }
  };

  const handleGerarContasPagar = async () => {
    try {
      await axios.post(`${API}/rh/folha-pagamento/gerar-contas-pagar`, {
        mes: selectedMes,
        ano: selectedAno
      });
      toast.success("Contas a pagar geradas!");
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao gerar contas");
    }
  };

  const openModal = (funcionarioId = null) => {
    const func = funcionarios.find(f => f.id === funcionarioId);
    setFormData({
      funcionario_id: funcionarioId || "",
      mes: selectedMes,
      ano: selectedAno,
      salario_base: func?.salario || 0,
      horas_extras: 0,
      valor_hora_extra: func ? (func.salario / 220) * 1.5 : 0,
      adicional_noturno: 0,
      comissoes: 0,
      vale_transporte: 0,
      vale_alimentacao: 0,
      plano_saude: 0,
      outros_descontos: 0,
      observacoes: ""
    });
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setViewingFolha(null);
  };

  const getFuncionarioNome = (id) => {
    const func = funcionarios.find(f => f.id === id);
    return func?.nome || "-";
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat("pt-BR", {
      style: "currency",
      currency: "BRL"
    }).format(value || 0);
  };

  const meses = [
    { value: 1, label: "Janeiro" },
    { value: 2, label: "Fevereiro" },
    { value: 3, label: "Março" },
    { value: 4, label: "Abril" },
    { value: 5, label: "Maio" },
    { value: 6, label: "Junho" },
    { value: 7, label: "Julho" },
    { value: 8, label: "Agosto" },
    { value: 9, label: "Setembro" },
    { value: 10, label: "Outubro" },
    { value: 11, label: "Novembro" },
    { value: 12, label: "Dezembro" }
  ];

  if (loading && funcionarios.length === 0) {
    return <div className="flex items-center justify-center min-h-[400px]"><div className="spinner w-12 h-12"></div></div>;
  }

  // Totais
  const totalBruto = folhas.reduce((sum, f) => sum + (f.salario_bruto || 0), 0);
  const totalLiquido = folhas.reduce((sum, f) => sum + (f.salario_liquido || 0), 0);
  const totalINSS = folhas.reduce((sum, f) => sum + (f.inss || 0), 0);
  const totalFGTS = folhas.reduce((sum, f) => sum + (f.fgts || 0), 0);

  return (
    <div data-testid="folha-pagamento-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Folha de Pagamento</h1>
          <p className="text-gray-500 mt-1">Gestão de salários e benefícios</p>
        </div>
        <div className="flex gap-2">
          <Button onClick={handleGerarContasPagar} variant="outline" className="border-[#10B981] text-[#10B981]">
            <FileText size={18} className="mr-2" />Gerar Contas a Pagar
          </Button>
          <Button onClick={() => openModal()} className="bg-[#10B981] hover:bg-[#059669]">
            <Plus size={18} className="mr-2" />Nova Folha
          </Button>
        </div>
      </div>

      {/* Filtros */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div>
          <Label>Mês</Label>
          <Select value={selectedMes.toString()} onValueChange={(v) => setSelectedMes(parseInt(v))}>
            <SelectTrigger><SelectValue /></SelectTrigger>
            <SelectContent className="z-[9999]">
              {meses.map(m => (
                <SelectItem key={m.value} value={m.value.toString()}>{m.label}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div>
          <Label>Ano</Label>
          <Select value={selectedAno.toString()} onValueChange={(v) => setSelectedAno(parseInt(v))}>
            <SelectTrigger><SelectValue /></SelectTrigger>
            <SelectContent className="z-[9999]">
              {[2024, 2025, 2026].map(a => (
                <SelectItem key={a} value={a.toString()}>{a}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="flex items-end">
          <Button onClick={fetchFolhas} className="w-full bg-[#10B981] hover:bg-[#059669]">
            <Search size={16} className="mr-2" />Buscar
          </Button>
        </div>
      </div>

      {/* Cards de resumo */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-xl font-bold text-green-600">{formatCurrency(totalBruto)}</p>
            <p className="text-sm text-gray-500">Total Bruto</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-xl font-bold text-blue-600">{formatCurrency(totalLiquido)}</p>
            <p className="text-sm text-gray-500">Total Líquido</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-xl font-bold text-orange-600">{formatCurrency(totalINSS)}</p>
            <p className="text-sm text-gray-500">Total INSS</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-xl font-bold text-purple-600">{formatCurrency(totalFGTS)}</p>
            <p className="text-sm text-gray-500">Total FGTS</p>
          </CardContent>
        </Card>
      </div>

      {/* Tabela de alíquotas */}
      <Card className="mb-6">
        <CardContent className="p-4">
          <h3 className="font-semibold mb-3 flex items-center gap-2">
            <Calculator size={18} className="text-[#10B981]" />
            Tabelas de Alíquotas 2025
          </h3>
          <div className="grid md:grid-cols-2 gap-4 text-sm">
            <div className="p-3 bg-gray-50 rounded-lg">
              <p className="font-medium mb-2">INSS</p>
              <div className="space-y-1 text-gray-600">
                <p>Até R$ 1.518,00: 7,5%</p>
                <p>R$ 1.518,01 a R$ 2.793,88: 9%</p>
                <p>R$ 2.793,89 a R$ 4.190,83: 12%</p>
                <p>R$ 4.190,84 a R$ 8.157,41: 14%</p>
              </div>
            </div>
            <div className="p-3 bg-gray-50 rounded-lg">
              <p className="font-medium mb-2">IRPF</p>
              <div className="space-y-1 text-gray-600">
                <p>Até R$ 2.259,20: Isento</p>
                <p>R$ 2.259,21 a R$ 2.826,65: 7,5%</p>
                <p>R$ 2.826,66 a R$ 3.751,05: 15%</p>
                <p>R$ 3.751,06 a R$ 4.664,68: 22,5%</p>
                <p>Acima de R$ 4.664,68: 27,5%</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Lista de folhas */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <div className="spinner w-12 h-12"></div>
        </div>
      ) : folhas.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-gray-400">
            <DollarSign className="mx-auto mb-4" size={48} />
            <p>Nenhuma folha gerada para este período</p>
            <p className="text-sm mt-2">Clique em "Nova Folha" para adicionar</p>
          </CardContent>
        </Card>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full border-collapse bg-white rounded-lg overflow-hidden shadow">
            <thead className="bg-gray-100">
              <tr>
                <th className="text-left p-3 text-sm font-medium text-gray-600">Funcionário</th>
                <th className="text-right p-3 text-sm font-medium text-gray-600">Sal. Bruto</th>
                <th className="text-right p-3 text-sm font-medium text-gray-600">INSS</th>
                <th className="text-right p-3 text-sm font-medium text-gray-600">IRPF</th>
                <th className="text-right p-3 text-sm font-medium text-gray-600">FGTS</th>
                <th className="text-right p-3 text-sm font-medium text-gray-600">Descontos</th>
                <th className="text-right p-3 text-sm font-medium text-gray-600">Sal. Líquido</th>
                <th className="text-center p-3 text-sm font-medium text-gray-600">Ações</th>
              </tr>
            </thead>
            <tbody>
              {folhas.map((f) => (
                <tr key={f.id} className="border-t hover:bg-gray-50">
                  <td className="p-3 text-sm font-medium">{getFuncionarioNome(f.funcionario_id)}</td>
                  <td className="p-3 text-sm text-right">{formatCurrency(f.salario_bruto)}</td>
                  <td className="p-3 text-sm text-right text-orange-600">{formatCurrency(f.inss)}</td>
                  <td className="p-3 text-sm text-right text-red-600">{formatCurrency(f.irpf)}</td>
                  <td className="p-3 text-sm text-right text-purple-600">{formatCurrency(f.fgts)}</td>
                  <td className="p-3 text-sm text-right text-gray-600">{formatCurrency(f.total_descontos)}</td>
                  <td className="p-3 text-sm text-right font-bold text-green-600">{formatCurrency(f.salario_liquido)}</td>
                  <td className="p-3 text-center">
                    <div className="flex justify-center gap-1">
                      <Button size="sm" variant="outline" onClick={() => setViewingFolha(f)} title="Ver detalhes">
                        <Eye size={14} />
                      </Button>
                      <Button size="sm" variant="outline" className="text-[#10B981]" onClick={() => handleGerarHolerite(f.id)} title="Baixar Holerite">
                        <Download size={14} />
                      </Button>
                      <Button size="sm" variant="outline" className="text-red-600" onClick={() => handleDelete(f.id)}>
                        <Trash2 size={14} />
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
            <tfoot className="bg-gray-100 font-bold">
              <tr>
                <td className="p-3 text-sm">TOTAL</td>
                <td className="p-3 text-sm text-right">{formatCurrency(totalBruto)}</td>
                <td className="p-3 text-sm text-right text-orange-600">{formatCurrency(totalINSS)}</td>
                <td className="p-3 text-sm text-right text-red-600">{formatCurrency(folhas.reduce((sum, f) => sum + (f.irpf || 0), 0))}</td>
                <td className="p-3 text-sm text-right text-purple-600">{formatCurrency(totalFGTS)}</td>
                <td className="p-3 text-sm text-right text-gray-600">{formatCurrency(folhas.reduce((sum, f) => sum + (f.total_descontos || 0), 0))}</td>
                <td className="p-3 text-sm text-right text-green-600">{formatCurrency(totalLiquido)}</td>
                <td className="p-3"></td>
              </tr>
            </tfoot>
          </table>
        </div>
      )}

      {/* Modal Nova Folha */}
      <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Gerar Folha de Pagamento</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-3 gap-4">
              <div>
                <Label>Funcionário *</Label>
                <Select 
                  value={formData.funcionario_id} 
                  onValueChange={(v) => {
                    const func = funcionarios.find(f => f.id === v);
                    setFormData({
                      ...formData, 
                      funcionario_id: v,
                      salario_base: func?.salario || 0,
                      valor_hora_extra: func ? (func.salario / 220) * 1.5 : 0
                    });
                  }}
                >
                  <SelectTrigger><SelectValue placeholder="Selecione" /></SelectTrigger>
                  <SelectContent className="z-[9999]">
                    {funcionarios.map(f => (
                      <SelectItem key={f.id} value={f.id}>{f.nome}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Mês</Label>
                <Select value={formData.mes.toString()} onValueChange={(v) => setFormData({...formData, mes: parseInt(v)})}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent className="z-[9999]">
                    {meses.map(m => (
                      <SelectItem key={m.value} value={m.value.toString()}>{m.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Ano</Label>
                <Input type="number" value={formData.ano} onChange={(e) => setFormData({...formData, ano: parseInt(e.target.value)})} />
              </div>
            </div>

            <div className="border-t pt-4">
              <h4 className="font-medium mb-3 text-green-600">Proventos</h4>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Salário Base</Label>
                  <MoneyInput value={formData.salario_base} onChange={(v) => setFormData({...formData, salario_base: v})} />
                </div>
                <div>
                  <Label>Horas Extras (qtd)</Label>
                  <DecimalInput value={formData.horas_extras} onChange={(v) => setFormData({...formData, horas_extras: v})} />
                </div>
                <div>
                  <Label>Valor Hora Extra (50%)</Label>
                  <MoneyInput value={formData.valor_hora_extra} onChange={(v) => setFormData({...formData, valor_hora_extra: v})} />
                </div>
                <div>
                  <Label>Adicional Noturno</Label>
                  <MoneyInput value={formData.adicional_noturno} onChange={(v) => setFormData({...formData, adicional_noturno: v})} />
                </div>
                <div>
                  <Label>Comissões</Label>
                  <MoneyInput value={formData.comissoes} onChange={(v) => setFormData({...formData, comissoes: v})} />
                </div>
              </div>
            </div>

            <div className="border-t pt-4">
              <h4 className="font-medium mb-3 text-red-600">Descontos</h4>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Vale Transporte (6%)</Label>
                  <MoneyInput value={formData.vale_transporte} onChange={(v) => setFormData({...formData, vale_transporte: v})} />
                </div>
                <div>
                  <Label>Vale Alimentação</Label>
                  <MoneyInput value={formData.vale_alimentacao} onChange={(v) => setFormData({...formData, vale_alimentacao: v})} />
                </div>
                <div>
                  <Label>Plano de Saúde</Label>
                  <MoneyInput value={formData.plano_saude} onChange={(v) => setFormData({...formData, plano_saude: v})} />
                </div>
                <div>
                  <Label>Outros Descontos</Label>
                  <MoneyInput value={formData.outros_descontos} onChange={(v) => setFormData({...formData, outros_descontos: v})} />
                </div>
              </div>
            </div>

            <div>
              <Label>Observações</Label>
              <Input value={formData.observacoes} onChange={(e) => setFormData({...formData, observacoes: e.target.value})} />
            </div>

            {/* Preview dos cálculos */}
            {formData.funcionario_id && (
              <div className="border-t pt-4">
                <h4 className="font-medium mb-3">Preview dos Cálculos</h4>
                {(() => {
                  const calc = calcularFolha();
                  return (
                    <div className="grid grid-cols-3 gap-2 text-sm">
                      <div className="p-2 bg-green-50 rounded">
                        <p className="text-gray-500">Salário Bruto</p>
                        <p className="font-bold text-green-600">{formatCurrency(calc.salario_bruto)}</p>
                      </div>
                      <div className="p-2 bg-orange-50 rounded">
                        <p className="text-gray-500">INSS</p>
                        <p className="font-bold text-orange-600">{formatCurrency(calc.inss)}</p>
                      </div>
                      <div className="p-2 bg-red-50 rounded">
                        <p className="text-gray-500">IRPF</p>
                        <p className="font-bold text-red-600">{formatCurrency(calc.irpf)}</p>
                      </div>
                      <div className="p-2 bg-purple-50 rounded">
                        <p className="text-gray-500">FGTS (empresa)</p>
                        <p className="font-bold text-purple-600">{formatCurrency(calc.fgts)}</p>
                      </div>
                      <div className="p-2 bg-gray-100 rounded">
                        <p className="text-gray-500">Total Descontos</p>
                        <p className="font-bold text-gray-600">{formatCurrency(calc.total_descontos)}</p>
                      </div>
                      <div className="p-2 bg-blue-50 rounded">
                        <p className="text-gray-500">Salário Líquido</p>
                        <p className="font-bold text-blue-600">{formatCurrency(calc.salario_liquido)}</p>
                      </div>
                    </div>
                  );
                })()}
              </div>
            )}

            <DialogFooter className="gap-2">
              <Button type="button" variant="outline" onClick={closeModal}>Cancelar</Button>
              <Button type="submit" className="bg-[#10B981] hover:bg-[#059669]" disabled={calculando}>
                {calculando ? <Loader2 className="animate-spin mr-2" size={16} /> : null}
                Gerar Folha
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Modal Detalhes da Folha */}
      <Dialog open={!!viewingFolha} onOpenChange={() => setViewingFolha(null)}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Detalhes da Folha</DialogTitle>
          </DialogHeader>
          {viewingFolha && (
            <div className="space-y-4">
              <div className="p-4 bg-gray-50 rounded-lg">
                <h4 className="font-bold text-lg">{getFuncionarioNome(viewingFolha.funcionario_id)}</h4>
                <p className="text-sm text-gray-500">
                  {meses.find(m => m.value === viewingFolha.mes)?.label} / {viewingFolha.ano}
                </p>
              </div>
              
              <div className="space-y-2">
                <div className="flex justify-between p-2 border-b">
                  <span>Salário Bruto</span>
                  <span className="font-medium text-green-600">{formatCurrency(viewingFolha.salario_bruto)}</span>
                </div>
                <div className="flex justify-between p-2 border-b">
                  <span>INSS</span>
                  <span className="font-medium text-orange-600">- {formatCurrency(viewingFolha.inss)}</span>
                </div>
                <div className="flex justify-between p-2 border-b">
                  <span>IRPF</span>
                  <span className="font-medium text-red-600">- {formatCurrency(viewingFolha.irpf)}</span>
                </div>
                <div className="flex justify-between p-2 border-b">
                  <span>Vale Transporte</span>
                  <span className="font-medium text-gray-600">- {formatCurrency(viewingFolha.vale_transporte)}</span>
                </div>
                <div className="flex justify-between p-2 border-b">
                  <span>Vale Alimentação</span>
                  <span className="font-medium text-gray-600">- {formatCurrency(viewingFolha.vale_alimentacao)}</span>
                </div>
                <div className="flex justify-between p-2 border-b">
                  <span>Plano de Saúde</span>
                  <span className="font-medium text-gray-600">- {formatCurrency(viewingFolha.plano_saude)}</span>
                </div>
                <div className="flex justify-between p-2 bg-blue-50 rounded font-bold">
                  <span>Salário Líquido</span>
                  <span className="text-blue-600">{formatCurrency(viewingFolha.salario_liquido)}</span>
                </div>
                <div className="flex justify-between p-2 bg-purple-50 rounded">
                  <span>FGTS (encargo empresa)</span>
                  <span className="text-purple-600">{formatCurrency(viewingFolha.fgts)}</span>
                </div>
              </div>

              <div className="pt-4 border-t">
                <AnexosManager
                  entityType="folha_pagamento"
                  entityId={viewingFolha.id}
                  title="Anexos da Folha"
                />
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setViewingFolha(null)}>Fechar</Button>
            {viewingFolha && (
              <Button className="bg-[#10B981] hover:bg-[#059669]" onClick={() => handleGerarHolerite(viewingFolha.id)}>
                <Download size={16} className="mr-2" />Baixar Holerite
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
