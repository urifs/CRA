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
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
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
  CheckCircle2,
  Trash2,
  Save,
  ShieldCheck,
  Paperclip,
  ExternalLink,
  CheckSquare,
  Square,
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
  const [observacaoDraft, setObservacaoDraft] = useState("");
  const [salvandoObs, setSalvandoObs] = useState(false);
  const [abonoForm, setAbonoForm] = useState(null); // { data, tipo, motivo }

  // Seleção em massa para abono
  const [modoSelecao, setModoSelecao] = useState(false);
  const [diasSelecionados, setDiasSelecionados] = useState([]); // array de "YYYY-MM-DD"
  const [abonoMassaForm, setAbonoMassaForm] = useState(null); // { tipo, motivo, arquivo }
  const [salvandoMassa, setSalvandoMassa] = useState(false);

  // Quando abre o modal, carrega rascunho da observação
  useEffect(() => {
    if (funcDetalhe) {
      setObservacaoDraft(funcDetalhe.observacao || "");
      setAbonoForm(null);
      setModoSelecao(false);
      setDiasSelecionados([]);
    }
  }, [funcDetalhe]);

  const recarregarFuncDetalhe = async () => {
    // Recarrega o dashboard e atualiza funcDetalhe com novos dados
    try {
      const { data } = await axios.get(
        `${API}/rh/ponto/dashboard-mensal?mes=${mes}&ano=${ano}`
      );
      setDashboard(data);
      if (funcDetalhe) {
        const novo = data.funcionarios.find(
          (f) => f.funcionario_id === funcDetalhe.funcionario_id
        );
        if (novo) setFuncDetalhe(novo);
      }
    } catch (e) {
      // silencioso
    }
  };

  const salvarObservacao = async () => {
    if (!funcDetalhe) return;
    setSalvandoObs(true);
    try {
      await axios.post(`${API}/rh/ponto/observacao`, {
        funcionario_id: funcDetalhe.funcionario_id,
        mes,
        ano,
        texto: observacaoDraft,
      });
      toast.success("Observação salva");
      await recarregarFuncDetalhe();
    } catch (e) {
      toast.error(e.response?.data?.detail || "Erro ao salvar observação");
    } finally {
      setSalvandoObs(false);
    }
  };

  const criarAbono = async () => {
    if (!abonoForm || !funcDetalhe) return;
    if (!abonoForm.tipo || !abonoForm.motivo?.trim()) {
      toast.error("Preencha tipo e motivo");
      return;
    }
    try {
      // Se tem arquivo, usa endpoint multipart; senão, JSON simples
      if (abonoForm.arquivo) {
        const fd = new FormData();
        fd.append("funcionario_id", funcDetalhe.funcionario_id);
        fd.append("data", abonoForm.data);
        fd.append("tipo", abonoForm.tipo);
        fd.append("motivo", abonoForm.motivo.trim());
        fd.append("arquivo", abonoForm.arquivo);
        await axios.post(`${API}/rh/ponto/abono-com-anexo`, fd, {
          headers: { "Content-Type": "multipart/form-data" },
        });
      } else {
        await axios.post(`${API}/rh/ponto/abono`, {
          funcionario_id: funcDetalhe.funcionario_id,
          data: abonoForm.data,
          tipo: abonoForm.tipo,
          motivo: abonoForm.motivo.trim(),
        });
      }
      toast.success(`Dia ${abonoForm.data.split("-").reverse().join("/")} abonado`);
      setAbonoForm(null);
      await recarregarFuncDetalhe();
    } catch (e) {
      toast.error(e.response?.data?.detail || "Erro ao criar abono");
    }
  };

  const baixarAnexoAbono = async (abonoId, filenameSugerido) => {
    try {
      const resp = await axios.get(`${API}/rh/ponto/abono/${abonoId}/anexo`, {
        responseType: "blob",
      });
      const blob = new Blob([resp.data], { type: resp.headers["content-type"] });
      const url = URL.createObjectURL(blob);
      // Abre em nova aba para o usuário visualizar (PDFs/imagens abrem inline)
      const win = window.open(url, "_blank");
      if (!win) {
        // Fallback: força download
        const a = document.createElement("a");
        a.href = url;
        a.download = filenameSugerido || "anexo";
        a.click();
      }
      setTimeout(() => URL.revokeObjectURL(url), 60000);
    } catch (e) {
      toast.error(e.response?.data?.detail || "Erro ao baixar anexo");
    }
  };

  const removerAbono = async (abonoId, data) => {
    if (!window.confirm(`Remover abono de ${data.split("-").reverse().join("/")}?`)) return;
    try {
      await axios.delete(`${API}/rh/ponto/abono/${abonoId}`);
      toast.success("Abono removido");
      await recarregarFuncDetalhe();
    } catch (e) {
      toast.error(e.response?.data?.detail || "Erro ao remover abono");
    }
  };

  // ===== Seleção em massa =====
  const podeAbonarDia = (d) =>
    !d.abono &&
    (d.status_dia === "sem_registro" ||
      d.status_dia === "incompleto" ||
      d.minutos_trabalhados < d.minutos_previstos);

  const toggleDiaSelecionado = (data) => {
    setDiasSelecionados((prev) =>
      prev.includes(data) ? prev.filter((x) => x !== data) : [...prev, data]
    );
  };

  const selecionarTodosFaltantes = () => {
    if (!funcDetalhe?.detalhe_dias) return;
    const datas = funcDetalhe.detalhe_dias.filter(podeAbonarDia).map((d) => d.data);
    setDiasSelecionados(datas);
  };

  const limparSelecao = () => setDiasSelecionados([]);

  const sairDoModoSelecao = () => {
    setModoSelecao(false);
    setDiasSelecionados([]);
  };

  const abrirModalMassa = () => {
    if (diasSelecionados.length === 0) {
      toast.error("Selecione ao menos um dia");
      return;
    }
    setAbonoMassaForm({ tipo: "atestado", motivo: "", arquivo: null });
  };

  const confirmarAbonoMassa = async () => {
    if (!abonoMassaForm || !funcDetalhe) return;
    if (!abonoMassaForm.tipo || !abonoMassaForm.motivo?.trim()) {
      toast.error("Preencha tipo e motivo");
      return;
    }
    if (diasSelecionados.length === 0) {
      toast.error("Nenhum dia selecionado");
      return;
    }

    setSalvandoMassa(true);
    try {
      if (abonoMassaForm.arquivo) {
        const fd = new FormData();
        fd.append("funcionario_id", funcDetalhe.funcionario_id);
        fd.append("datas", JSON.stringify(diasSelecionados));
        fd.append("tipo", abonoMassaForm.tipo);
        fd.append("motivo", abonoMassaForm.motivo.trim());
        fd.append("arquivo", abonoMassaForm.arquivo);
        await axios.post(`${API}/rh/ponto/abono-em-massa-com-anexo`, fd, {
          headers: { "Content-Type": "multipart/form-data" },
        });
      } else {
        await axios.post(`${API}/rh/ponto/abono-em-massa`, {
          funcionario_id: funcDetalhe.funcionario_id,
          datas: diasSelecionados,
          tipo: abonoMassaForm.tipo,
          motivo: abonoMassaForm.motivo.trim(),
        });
      }
      toast.success(
        `${diasSelecionados.length} dia(s) abonado(s) para ${funcDetalhe.nome}`
      );
      setAbonoMassaForm(null);
      setDiasSelecionados([]);
      setModoSelecao(false);
      await recarregarFuncDetalhe();
    } catch (e) {
      toast.error(e.response?.data?.detail || "Erro ao abonar em massa");
    } finally {
      setSalvandoMassa(false);
    }
  };

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
                        {f.jornada_nome && (
                          <p className="text-[10px] text-emerald-600 font-semibold mt-0.5">
                            ⏱ {f.jornada_nome}
                          </p>
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
                {/* Barra de ações em massa */}
                <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
                  {!modoSelecao ? (
                    <Button
                      size="sm"
                      variant="outline"
                      className="border-amber-300 text-amber-700 hover:bg-amber-50"
                      onClick={() => setModoSelecao(true)}
                      data-testid="btn-modo-selecao"
                    >
                      <CheckSquare size={14} className="mr-1" />
                      Abono em massa
                    </Button>
                  ) : (
                    <div className="flex flex-wrap items-center gap-2 w-full">
                      <span className="text-xs font-medium text-amber-800 bg-amber-100 px-2 py-1 rounded">
                        {diasSelecionados.length} dia(s) selecionado(s)
                      </span>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={selecionarTodosFaltantes}
                        data-testid="btn-selecionar-faltantes"
                      >
                        Selecionar todos faltantes
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={limparSelecao}
                        data-testid="btn-limpar-selecao"
                      >
                        Limpar
                      </Button>
                      <div className="ml-auto flex gap-2">
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={sairDoModoSelecao}
                          data-testid="btn-sair-selecao"
                        >
                          Sair do modo
                        </Button>
                        <Button
                          size="sm"
                          className="bg-amber-600 hover:bg-amber-700"
                          onClick={abrirModalMassa}
                          disabled={diasSelecionados.length === 0}
                          data-testid="btn-abrir-modal-massa"
                        >
                          <ShieldCheck size={14} className="mr-1" />
                          Abonar selecionados ({diasSelecionados.length})
                        </Button>
                      </div>
                    </div>
                  )}
                </div>

                <table className="w-full text-sm">
                  <thead className="bg-gray-100">
                    <tr>
                      {modoSelecao && (
                        <th className="text-center p-2 w-10">
                          <CheckSquare size={14} className="inline text-gray-500" />
                        </th>
                      )}
                      <th className="text-left p-2">Data</th>
                      <th className="text-center p-2">Dia</th>
                      <th className="text-left p-2">Batidas</th>
                      <th className="text-right p-2">Trabalhado</th>
                      <th className="text-right p-2">Previsto</th>
                      <th className="text-right p-2">Saldo</th>
                      <th className="text-center p-2 w-24">Ações</th>
                    </tr>
                  </thead>
                  <tbody>
                    {funcDetalhe.detalhe_dias?.map((d, i) => {
                      const isAbonado = !!d.abono;
                      const podeAbonar =
                        !isAbonado &&
                        (d.status_dia === "sem_registro" || d.status_dia === "incompleto" ||
                         d.minutos_trabalhados < d.minutos_previstos);
                      const selecionado = diasSelecionados.includes(d.data);
                      return (
                        <tr
                          key={i}
                          className={`border-b ${
                            isAbonado
                              ? "bg-amber-50"
                              : selecionado
                                ? "bg-amber-100/60"
                                : "hover:bg-gray-50"
                          } ${modoSelecao && podeAbonar ? "cursor-pointer" : ""}`}
                          onClick={() => {
                            if (modoSelecao && podeAbonar) toggleDiaSelecionado(d.data);
                          }}
                          data-testid={`row-dia-${d.data}`}
                        >
                          {modoSelecao && (
                            <td className="p-2 text-center">
                              {podeAbonar ? (
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    toggleDiaSelecionado(d.data);
                                  }}
                                  className="inline-flex"
                                  data-testid={`check-dia-${d.data}`}
                                >
                                  {selecionado ? (
                                    <CheckSquare
                                      size={18}
                                      className="text-amber-600"
                                    />
                                  ) : (
                                    <Square size={18} className="text-gray-400" />
                                  )}
                                </button>
                              ) : (
                                <span className="text-gray-300 text-xs">—</span>
                              )}
                            </td>
                          )}
                          <td className="p-2 font-mono">
                            {d.data?.split("-").reverse().join("/")}
                          </td>
                          <td className="p-2 text-center text-gray-600">
                            {DIAS_SEMANA[d.dia_semana]}
                          </td>
                          <td className="p-2 font-mono text-xs">
                            {isAbonado ? (
                              <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-amber-200 text-amber-900 rounded text-xs font-semibold">
                                <ShieldCheck size={12} />
                                {(d.abono.tipo || "").toUpperCase()}: {d.abono.motivo}
                                {d.abono.anexo?.storage_path && (
                                  <button
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      baixarAnexoAbono(d.abono.id, d.abono.anexo.filename_original);
                                    }}
                                    className="ml-1 inline-flex items-center gap-0.5 px-1 py-0.5 bg-amber-700 text-white rounded text-[10px] hover:bg-amber-800"
                                    title={`Abrir ${d.abono.anexo.filename_original}`}
                                    data-testid={`btn-anexo-${d.data}`}
                                  >
                                    <Paperclip size={10} />
                                    <ExternalLink size={9} />
                                  </button>
                                )}
                              </span>
                            ) : (
                              (d.batidas || []).join(" • ") || "—"
                            )}
                          </td>
                          <td className="p-2 text-right">
                            {fmtMin(d.minutos_trabalhados)}
                          </td>
                          <td className="p-2 text-right text-gray-500">
                            {fmtMin(d.minutos_previstos)}
                          </td>
                          <td
                            className={`p-2 text-right font-medium ${
                              isAbonado
                                ? "text-amber-700"
                                : d.saldo_minutos > 0
                                ? "text-emerald-600"
                                : d.saldo_minutos < 0
                                ? "text-rose-600"
                                : "text-gray-500"
                            }`}
                          >
                            {isAbonado ? (
                              "ABONADO"
                            ) : (
                              <>
                                {d.saldo_minutos > 0 ? "+" : ""}
                                {fmtMin(d.saldo_minutos)}
                              </>
                            )}
                          </td>
                          <td className="p-2 text-center">
                            {isAbonado ? (
                              <Button
                                size="sm"
                                variant="ghost"
                                className="text-rose-600 h-7 px-2"
                                onClick={() => removerAbono(d.abono.id, d.data)}
                                data-testid={`btn-remover-abono-${d.data}`}
                              >
                                <Trash2 size={12} />
                              </Button>
                            ) : podeAbonar ? (
                              <Button
                                size="sm"
                                variant="outline"
                                className="h-7 px-2 text-xs border-amber-300 text-amber-700 hover:bg-amber-50"
                                onClick={() =>
                                  setAbonoForm({
                                    data: d.data,
                                    tipo: "atestado",
                                    motivo: "",
                                  })
                                }
                                data-testid={`btn-abonar-${d.data}`}
                              >
                                Abonar
                              </Button>
                            ) : null}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              {/* Observações livres do mês */}
              <Card>
                <CardContent className="p-4 space-y-2">
                  <div className="flex items-center justify-between">
                    <Label className="font-semibold">Observações do mês</Label>
                    <Button
                      size="sm"
                      onClick={salvarObservacao}
                      disabled={salvandoObs || observacaoDraft === (funcDetalhe.observacao || "")}
                      className="bg-emerald-600 hover:bg-emerald-700"
                      data-testid="btn-salvar-observacao"
                    >
                      {salvandoObs ? (
                        <Loader2 size={12} className="animate-spin mr-1" />
                      ) : (
                        <Save size={12} className="mr-1" />
                      )}
                      Salvar
                    </Button>
                  </div>
                  <Textarea
                    placeholder="Anote informações relevantes do mês (ex: férias agendadas, treinamentos, atestados não apresentados...). Aparecerá no PDF."
                    value={observacaoDraft}
                    onChange={(e) => setObservacaoDraft(e.target.value)}
                    rows={3}
                    data-testid="textarea-observacao"
                  />
                </CardContent>
              </Card>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Dialog dedicado para criação/edição de Abono — fica em primeiro plano */}
      <Dialog open={!!abonoForm} onOpenChange={(o) => !o && setAbonoForm(null)}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-amber-900">
              <ShieldCheck size={18} />
              {abonoForm
                ? `Abonar dia ${abonoForm.data.split("-").reverse().join("/")}`
                : "Abonar dia"}
            </DialogTitle>
          </DialogHeader>
          {abonoForm && (
            <div className="space-y-3">
              <div className="grid grid-cols-1 gap-3">
                <div>
                  <Label className="text-xs">Tipo</Label>
                  <Select
                    value={abonoForm.tipo}
                    onValueChange={(v) => setAbonoForm({ ...abonoForm, tipo: v })}
                  >
                    <SelectTrigger data-testid="select-tipo-abono">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="atestado">Atestado médico</SelectItem>
                      <SelectItem value="justificativa">Justificativa</SelectItem>
                      <SelectItem value="folga">Folga compensada</SelectItem>
                      <SelectItem value="feriado">Feriado</SelectItem>
                      <SelectItem value="ferias">Férias</SelectItem>
                      <SelectItem value="outros">Outros</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label className="text-xs">Motivo / Justificativa</Label>
                  <Input
                    placeholder="Ex.: Atestado médico - clínica geral"
                    value={abonoForm.motivo}
                    onChange={(e) =>
                      setAbonoForm({ ...abonoForm, motivo: e.target.value })
                    }
                    onKeyDown={(e) => e.key === "Enter" && criarAbono()}
                    data-testid="input-motivo-abono"
                  />
                </div>
              </div>
              <div>
                <Label className="text-xs flex items-center gap-1">
                  <Paperclip size={12} />
                  Anexar atestado/justificativa (opcional)
                </Label>
                <Input
                  type="file"
                  accept=".pdf,.jpg,.jpeg,.png,.webp,.heic"
                  onChange={(e) =>
                    setAbonoForm({
                      ...abonoForm,
                      arquivo: e.target.files?.[0] || null,
                    })
                  }
                  className="cursor-pointer"
                  data-testid="input-arquivo-abono"
                />
                {abonoForm.arquivo && (
                  <p className="text-xs text-amber-700 mt-1">
                    {abonoForm.arquivo.name} ({(abonoForm.arquivo.size / 1024).toFixed(1)} KB)
                  </p>
                )}
                <p className="text-[10px] text-amber-600 mt-1">
                  Formatos: PDF, JPG, PNG, WEBP, HEIC. Máximo 10MB.
                </p>
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setAbonoForm(null)}
                  data-testid="btn-cancelar-abono"
                >
                  Cancelar
                </Button>
                <Button
                  size="sm"
                  className="bg-amber-600 hover:bg-amber-700"
                  onClick={criarAbono}
                  data-testid="btn-confirmar-abono"
                >
                  <CheckCircle2 size={14} className="mr-2" />
                  Confirmar abono
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Dialog de Abono em Massa (multi-data) */}
      <Dialog
        open={!!abonoMassaForm}
        onOpenChange={(o) => !o && !salvandoMassa && setAbonoMassaForm(null)}
      >
        <DialogContent className="max-w-lg" data-testid="dialog-abono-massa">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-amber-900">
              <ShieldCheck size={18} />
              Abonar {diasSelecionados.length} dia(s) em massa
            </DialogTitle>
          </DialogHeader>
          {abonoMassaForm && (
            <div className="space-y-3">
              <div className="bg-amber-50 border border-amber-200 rounded p-3 text-xs max-h-32 overflow-y-auto">
                <p className="font-semibold text-amber-900 mb-1">Datas selecionadas:</p>
                <div className="flex flex-wrap gap-1">
                  {diasSelecionados.sort().map((d) => (
                    <span
                      key={d}
                      className="px-2 py-0.5 bg-amber-200 text-amber-900 rounded font-mono text-[11px]"
                    >
                      {d.split("-").reverse().join("/")}
                    </span>
                  ))}
                </div>
              </div>

              <div>
                <Label className="text-xs">Tipo (aplicado em todas as datas)</Label>
                <Select
                  value={abonoMassaForm.tipo}
                  onValueChange={(v) =>
                    setAbonoMassaForm({ ...abonoMassaForm, tipo: v })
                  }
                >
                  <SelectTrigger data-testid="select-tipo-abono-massa">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="atestado">Atestado médico</SelectItem>
                    <SelectItem value="justificativa">Justificativa</SelectItem>
                    <SelectItem value="folga">Folga compensada</SelectItem>
                    <SelectItem value="feriado">Feriado</SelectItem>
                    <SelectItem value="ferias">Férias</SelectItem>
                    <SelectItem value="outros">Outros</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label className="text-xs">Motivo / Justificativa</Label>
                <Textarea
                  placeholder="Ex.: Atestado médico (5 dias) - clínica geral"
                  value={abonoMassaForm.motivo}
                  onChange={(e) =>
                    setAbonoMassaForm({
                      ...abonoMassaForm,
                      motivo: e.target.value,
                    })
                  }
                  rows={2}
                  data-testid="input-motivo-abono-massa"
                />
              </div>
              <div>
                <Label className="text-xs flex items-center gap-1">
                  <Paperclip size={12} />
                  Anexar atestado/justificativa (compartilhado entre todas as datas)
                </Label>
                <Input
                  type="file"
                  accept=".pdf,.jpg,.jpeg,.png,.webp,.heic"
                  onChange={(e) =>
                    setAbonoMassaForm({
                      ...abonoMassaForm,
                      arquivo: e.target.files?.[0] || null,
                    })
                  }
                  className="cursor-pointer"
                  data-testid="input-arquivo-abono-massa"
                />
                {abonoMassaForm.arquivo && (
                  <p className="text-xs text-amber-700 mt-1">
                    {abonoMassaForm.arquivo.name} (
                    {(abonoMassaForm.arquivo.size / 1024).toFixed(1)} KB)
                  </p>
                )}
                <p className="text-[10px] text-amber-600 mt-1">
                  Formatos: PDF, JPG, PNG, WEBP, HEIC. Máximo 10MB. O mesmo arquivo
                  será vinculado a todos os dias selecionados.
                </p>
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setAbonoMassaForm(null)}
                  disabled={salvandoMassa}
                  data-testid="btn-cancelar-abono-massa"
                >
                  Cancelar
                </Button>
                <Button
                  size="sm"
                  className="bg-amber-600 hover:bg-amber-700"
                  onClick={confirmarAbonoMassa}
                  disabled={salvandoMassa}
                  data-testid="btn-confirmar-abono-massa"
                >
                  {salvandoMassa ? (
                    <Loader2 size={14} className="animate-spin mr-2" />
                  ) : (
                    <CheckCircle2 size={14} className="mr-2" />
                  )}
                  Confirmar abono em massa
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
