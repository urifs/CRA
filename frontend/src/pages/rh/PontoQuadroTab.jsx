import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "@/App";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
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
} from "@/components/ui/dialog";
import {
  TrendingUp,
  TrendingDown,
  Clock,
  AlertCircle,
  Calendar,
  Users,
  Loader2,
  Briefcase,
  FileDown,
} from "lucide-react";
import { toast } from "sonner";

function fmtMin(min) {
  if (min === 0) return "0h";
  const sign = min < 0 ? "-" : "";
  const abs = Math.abs(min);
  const h = Math.floor(abs / 60);
  const m = abs % 60;
  return `${sign}${h}h${m > 0 ? ` ${m}min` : ""}`;
}

const DIAS_SEMANA = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"];

export default function PontoQuadroTab({ refreshKey }) {
  const today = new Date();
  const [mes, setMes] = useState(today.getMonth() + 1);
  const [ano, setAno] = useState(today.getFullYear());
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(false);
  const [funcDetalhe, setFuncDetalhe] = useState(null);

  const fetchDashboard = async () => {
    setLoading(true);
    try {
      const { data } = await axios.get(
        `${API}/rh/ponto/dashboard-mensal?mes=${mes}&ano=${ano}`
      );
      setDashboard(data);
    } catch (e) {
      toast.error(e.response?.data?.detail || "Erro ao carregar quadro mensal");
    } finally {
      setLoading(false);
    }
  };

  const baixarPdf = async (funcionarioId, nome) => {
    try {
      const url = funcionarioId
        ? `${API}/rh/ponto/relatorio-pdf?mes=${mes}&ano=${ano}&funcionario_id=${encodeURIComponent(funcionarioId)}`
        : `${API}/rh/ponto/relatorio-pdf?mes=${mes}&ano=${ano}`;
      const resp = await axios.get(url, { responseType: "blob" });
      const blob = new Blob([resp.data], { type: "application/pdf" });
      const link = document.createElement("a");
      link.href = URL.createObjectURL(blob);
      const nomeArq = nome
        ? `EspelhoPonto_${nome.replace(/\s+/g, "_")}_${String(mes).padStart(2, "0")}_${ano}.pdf`
        : `EspelhoPonto_TODOS_${String(mes).padStart(2, "0")}_${ano}.pdf`;
      link.download = nomeArq;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(link.href);
      toast.success("PDF gerado!");
    } catch (e) {
      toast.error(e.response?.data?.detail || "Erro ao gerar PDF");
    }
  };

  useEffect(() => {
    fetchDashboard();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mes, ano, refreshKey]);

  const meses = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
  ];
  const anos = [2024, 2025, 2026, 2027];

  return (
    <div className="space-y-6" data-testid="ponto-quadro-tab">
      {/* Filtros */}
      <Card>
        <CardContent className="p-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <Label>Mês</Label>
              <Select value={String(mes)} onValueChange={(v) => setMes(Number(v))}>
                <SelectTrigger data-testid="select-mes-quadro">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {meses.map((nome, i) => (
                    <SelectItem key={i + 1} value={String(i + 1)}>
                      {nome}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Ano</Label>
              <Select value={String(ano)} onValueChange={(v) => setAno(Number(v))}>
                <SelectTrigger data-testid="select-ano-quadro">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {anos.map((a) => (
                    <SelectItem key={a} value={String(a)}>
                      {a}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-end gap-2">
              <Button
                onClick={fetchDashboard}
                disabled={loading}
                className="flex-1 bg-emerald-600 hover:bg-emerald-700"
              >
                {loading ? (
                  <Loader2 className="animate-spin mr-2" size={16} />
                ) : (
                  <Calendar className="mr-2" size={16} />
                )}
                Atualizar
              </Button>
              <Button
                onClick={() => baixarPdf(null)}
                disabled={loading || !dashboard?.funcionarios?.length}
                variant="outline"
                title="Exportar espelho de ponto consolidado de todos os funcionários"
                data-testid="btn-pdf-todos"
              >
                <FileDown size={16} className="mr-2" />
                PDF (todos)
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Resumo geral */}
      {dashboard && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card className="bg-blue-50 border-blue-200">
            <CardContent className="p-4 flex items-center gap-3">
              <Users className="text-blue-600" size={32} />
              <div>
                <p className="text-2xl font-bold text-blue-700">
                  {dashboard.total_funcionarios}
                </p>
                <p className="text-sm text-blue-600">Funcionários no mês</p>
              </div>
            </CardContent>
          </Card>
          <Card className="bg-emerald-50 border-emerald-200">
            <CardContent className="p-4 flex items-center gap-3">
              <TrendingUp className="text-emerald-600" size={32} />
              <div>
                <p className="text-2xl font-bold text-emerald-700">
                  {fmtMin(dashboard.total_extras_minutos)}
                </p>
                <p className="text-sm text-emerald-600">Total de horas extras</p>
              </div>
            </CardContent>
          </Card>
          <Card className="bg-rose-50 border-rose-200">
            <CardContent className="p-4 flex items-center gap-3">
              <TrendingDown className="text-rose-600" size={32} />
              <div>
                <p className="text-2xl font-bold text-rose-700">
                  {fmtMin(dashboard.total_devidas_minutos)}
                </p>
                <p className="text-sm text-rose-600">Total de horas devidas</p>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Cards por funcionário */}
      {loading ? (
        <div className="flex justify-center py-12">
          <Loader2 className="animate-spin text-emerald-600" size={48} />
        </div>
      ) : dashboard?.funcionarios?.length === 0 ? (
        <Card>
          <CardContent className="p-12 text-center">
            <Calendar className="mx-auto text-gray-300 mb-3" size={48} />
            <p className="text-gray-500">
              Nenhum registro de ponto para {meses[mes - 1]}/{ano}.
            </p>
            <p className="text-sm text-gray-400 mt-1">
              Use a aba "Importar Planilha" para subir o arquivo do relógio.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {dashboard?.funcionarios?.map((f) => {
            const saldoPositivo = f.saldo_mes_minutos > 0;
            const saldoZero = f.saldo_mes_minutos === 0;
            const bancoPositivo = f.banco_horas_acumulado_minutos > 0;
            const pctTrabalhado =
              f.minutos_previstos > 0
                ? Math.min(100, (f.minutos_trabalhados / f.minutos_previstos) * 100)
                : 0;

            return (
              <Card
                key={f.funcionario_id}
                className={`hover:shadow-md transition-shadow cursor-pointer ${
                  !f.cadastrado ? "border-amber-300 bg-amber-50/40" : ""
                }`}
                onClick={() => setFuncDetalhe(f)}
                data-testid={`card-func-${f.funcionario_id}`}
              >
                <CardContent className="p-4">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div className="w-12 h-12 rounded-full bg-emerald-100 flex items-center justify-center">
                        <Briefcase className="text-emerald-600" size={20} />
                      </div>
                      <div>
                        <h3 className="font-bold text-gray-800 leading-tight">
                          {f.nome}
                        </h3>
                        <p className="text-xs text-gray-500">{f.cargo}</p>
                        {f.departamento && (
                          <p className="text-xs text-gray-400">{f.departamento}</p>
                        )}
                      </div>
                    </div>
                    {!f.cadastrado && (
                      <span
                        className="text-amber-600 flex items-center gap-1 text-xs"
                        title="Funcionário não cadastrado na plataforma"
                      >
                        <AlertCircle size={14} />
                      </span>
                    )}
                  </div>

                  {/* Barra de progresso horas */}
                  <div className="mb-3">
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-gray-600">Horas trabalhadas</span>
                      <span className="font-semibold text-gray-800">
                        {fmtMin(f.minutos_trabalhados)} / {fmtMin(f.minutos_previstos)}
                      </span>
                    </div>
                    <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                      <div
                        className={`h-full transition-all ${
                          pctTrabalhado >= 100
                            ? "bg-emerald-500"
                            : pctTrabalhado >= 80
                            ? "bg-blue-500"
                            : "bg-amber-500"
                        }`}
                        style={{ width: `${Math.min(pctTrabalhado, 100)}%` }}
                      />
                    </div>
                  </div>

                  {/* Saldo do mês */}
                  <div
                    className={`rounded-lg p-2 mb-2 ${
                      saldoZero
                        ? "bg-gray-100"
                        : saldoPositivo
                        ? "bg-emerald-100"
                        : "bg-rose-100"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-medium text-gray-600">
                        Saldo do mês
                      </span>
                      <span
                        className={`font-bold flex items-center gap-1 ${
                          saldoZero
                            ? "text-gray-700"
                            : saldoPositivo
                            ? "text-emerald-700"
                            : "text-rose-700"
                        }`}
                      >
                        {saldoPositivo ? (
                          <TrendingUp size={14} />
                        ) : !saldoZero ? (
                          <TrendingDown size={14} />
                        ) : null}
                        {saldoPositivo ? "+" : ""}
                        {fmtMin(f.saldo_mes_minutos)}
                      </span>
                    </div>
                  </div>

                  {/* Banco de horas acumulado */}
                  <div
                    className={`rounded-lg p-2 mb-3 border ${
                      bancoPositivo
                        ? "bg-blue-50 border-blue-200"
                        : f.banco_horas_acumulado_minutos < 0
                        ? "bg-orange-50 border-orange-200"
                        : "bg-gray-50 border-gray-200"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-medium text-gray-600 flex items-center gap-1">
                        <Clock size={12} />
                        Banco acumulado
                      </span>
                      <span
                        className={`font-bold ${
                          bancoPositivo
                            ? "text-blue-700"
                            : f.banco_horas_acumulado_minutos < 0
                            ? "text-orange-700"
                            : "text-gray-700"
                        }`}
                      >
                        {bancoPositivo ? "+" : ""}
                        {fmtMin(f.banco_horas_acumulado_minutos)}
                      </span>
                    </div>
                  </div>

                  {/* Stats grid */}
                  <div className="grid grid-cols-3 gap-1 text-center text-xs">
                    <div className="bg-emerald-50 rounded p-1">
                      <p className="font-bold text-emerald-700">{f.dias_com_registro}</p>
                      <p className="text-emerald-600 text-[10px]">Trabalhados</p>
                    </div>
                    <div className="bg-amber-50 rounded p-1">
                      <p className="font-bold text-amber-700">{f.dias_incompletos}</p>
                      <p className="text-amber-600 text-[10px]">Incompletos</p>
                    </div>
                    <div className="bg-rose-50 rounded p-1">
                      <p className="font-bold text-rose-700">{f.dias_falta}</p>
                      <p className="text-rose-600 text-[10px]">Faltas</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Modal de detalhamento por dia */}
      <Dialog open={!!funcDetalhe} onOpenChange={(o) => !o && setFuncDetalhe(null)}>
        <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center justify-between gap-3">
              <span>{funcDetalhe?.nome} — {meses[mes - 1]}/{ano}</span>
              {funcDetalhe && (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => baixarPdf(funcDetalhe.funcionario_id, funcDetalhe.nome)}
                  data-testid="btn-pdf-individual"
                >
                  <FileDown size={14} className="mr-2" />
                  Baixar PDF
                </Button>
              )}
            </DialogTitle>
          </DialogHeader>
          {funcDetalhe && (
            <div className="space-y-4">
              <div className="grid grid-cols-4 gap-3 text-center">
                <div className="bg-emerald-50 rounded p-2">
                  <p className="text-xs text-emerald-600">Trabalhadas</p>
                  <p className="font-bold text-emerald-700">
                    {fmtMin(funcDetalhe.minutos_trabalhados)}
                  </p>
                </div>
                <div className="bg-blue-50 rounded p-2">
                  <p className="text-xs text-blue-600">Previstas</p>
                  <p className="font-bold text-blue-700">
                    {fmtMin(funcDetalhe.minutos_previstos)}
                  </p>
                </div>
                <div
                  className={`rounded p-2 ${
                    funcDetalhe.saldo_mes_minutos >= 0 ? "bg-emerald-100" : "bg-rose-100"
                  }`}
                >
                  <p className="text-xs text-gray-600">Saldo mês</p>
                  <p
                    className={`font-bold ${
                      funcDetalhe.saldo_mes_minutos >= 0
                        ? "text-emerald-700"
                        : "text-rose-700"
                    }`}
                  >
                    {funcDetalhe.saldo_mes_minutos >= 0 ? "+" : ""}
                    {fmtMin(funcDetalhe.saldo_mes_minutos)}
                  </p>
                </div>
                <div className="bg-purple-50 rounded p-2">
                  <p className="text-xs text-purple-600">Banco acum.</p>
                  <p className="font-bold text-purple-700">
                    {funcDetalhe.banco_horas_acumulado_minutos >= 0 ? "+" : ""}
                    {fmtMin(funcDetalhe.banco_horas_acumulado_minutos)}
                  </p>
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gray-100">
                    <tr>
                      <th className="text-left p-2">Data</th>
                      <th className="text-center p-2">Dia</th>
                      <th className="text-left p-2">Batidas</th>
                      <th className="text-right p-2">Trabalhado</th>
                      <th className="text-right p-2">Previsto</th>
                      <th className="text-right p-2">Saldo</th>
                    </tr>
                  </thead>
                  <tbody>
                    {funcDetalhe.detalhe_dias?.map((d, i) => (
                      <tr key={i} className="border-b hover:bg-gray-50">
                        <td className="p-2 font-mono">
                          {d.data?.split("-").reverse().join("/")}
                        </td>
                        <td className="p-2 text-center text-gray-600">
                          {DIAS_SEMANA[d.dia_semana]}
                        </td>
                        <td className="p-2 font-mono text-xs">
                          {(d.batidas || []).join(" • ") || "—"}
                        </td>
                        <td className="p-2 text-right">
                          {fmtMin(d.minutos_trabalhados)}
                        </td>
                        <td className="p-2 text-right text-gray-500">
                          {fmtMin(d.minutos_previstos)}
                        </td>
                        <td
                          className={`p-2 text-right font-medium ${
                            d.saldo_minutos > 0
                              ? "text-emerald-600"
                              : d.saldo_minutos < 0
                              ? "text-rose-600"
                              : "text-gray-500"
                          }`}
                        >
                          {d.saldo_minutos > 0 ? "+" : ""}
                          {fmtMin(d.saldo_minutos)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
