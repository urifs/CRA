import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "@/App";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Wallet,
  Search,
  TrendingUp,
  TrendingDown,
  Loader2,
  FileDown,
  Calendar,
  Plus,
  Minus,
  Trash2,
} from "lucide-react";
import { toast } from "sonner";

const fmtMin = (min) => {
  if (min === 0 || min === null || min === undefined) return "0h";
  const sinal = min < 0 ? "-" : "";
  const abs = Math.abs(min);
  const h = Math.floor(abs / 60);
  const m = abs % 60;
  if (m === 0) return `${sinal}${h}h`;
  return `${sinal}${h}h ${m}min`;
};

const brDate = (s) => {
  if (!s) return "-";
  try {
    const [y, mo, d] = s.split("-");
    return `${d}/${mo}/${y}`;
  } catch {
    return s;
  }
};

const mesLabel = (s) => {
  if (!s) return "-";
  const meses = ["", "Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
                 "Jul", "Ago", "Set", "Out", "Nov", "Dez"];
  try {
    const [ano, mes] = s.split("-");
    return `${meses[parseInt(mes, 10)]}/${ano}`;
  } catch {
    return s;
  }
};

export default function BancoHorasPage() {
  const [resumo, setResumo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [busca, setBusca] = useState("");
  const [deData, setDeData] = useState("");
  const [ateData, setAteData] = useState(new Date().toISOString().slice(0, 10));
  const [extratoOpen, setExtratoOpen] = useState(false);
  const [extrato, setExtrato] = useState(null);
  const [loadingExtrato, setLoadingExtrato] = useState(false);

  // Modal de Ajuste Manual
  const [ajusteOpen, setAjusteOpen] = useState(false);
  const [ajusteFunc, setAjusteFunc] = useState(null);
  const [ajusteForm, setAjusteForm] = useState({
    operacao: "adicionar", // "adicionar" | "retirar"
    horas: "",
    minutos: "",
    data: new Date().toISOString().slice(0, 10),
    motivo: "",
    tipo: "ajuste",
  });
  const [savingAjuste, setSavingAjuste] = useState(false);

  useEffect(() => {
    fetchResumo();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ateData, deData]);

  const fetchResumo = async () => {
    setLoading(true);
    try {
      const params = { ate_data: ateData };
      if (deData) params.de_data = deData;
      const r = await axios.get(`${API}/rh/banco-horas/resumo`, { params });
      setResumo(r.data);
    } catch (e) {
      toast.error("Erro ao carregar banco de horas");
    } finally {
      setLoading(false);
    }
  };

  const aplicarPresetMes = (offset = 0) => {
    const hoje = new Date();
    const ref = new Date(hoje.getFullYear(), hoje.getMonth() + offset, 1);
    const ano = ref.getFullYear();
    const mes = String(ref.getMonth() + 1).padStart(2, "0");
    const ultimoDia = new Date(ref.getFullYear(), ref.getMonth() + 1, 0).getDate();
    setDeData(`${ano}-${mes}-01`);
    setAteData(`${ano}-${mes}-${String(ultimoDia).padStart(2, "0")}`);
  };

  const limparFiltro = () => {
    setDeData("");
    setAteData(new Date().toISOString().slice(0, 10));
  };

  const abrirAjuste = (func) => {
    setAjusteFunc(func);
    setAjusteForm({
      operacao: "adicionar",
      horas: "",
      minutos: "",
      data: new Date().toISOString().slice(0, 10),
      motivo: "",
      tipo: "ajuste",
    });
    setAjusteOpen(true);
  };

  const salvarAjuste = async () => {
    const horas = parseInt(ajusteForm.horas) || 0;
    const minutos = parseInt(ajusteForm.minutos) || 0;
    if (horas === 0 && minutos === 0) {
      toast.error("Informe horas e/ou minutos");
      return;
    }
    if (!ajusteForm.motivo.trim()) {
      toast.error("Motivo é obrigatório");
      return;
    }
    let total = horas * 60 + minutos;
    if (ajusteForm.operacao === "retirar") total = -total;

    setSavingAjuste(true);
    try {
      await axios.post(`${API}/rh/banco-horas/ajustes`, {
        funcionario_id: ajusteFunc.funcionario_id,
        minutos: total,
        data: ajusteForm.data,
        motivo: ajusteForm.motivo,
        tipo: ajusteForm.tipo,
      });
      toast.success(
        `${ajusteForm.operacao === "adicionar" ? "Adicionado" : "Retirado"} ${horas}h ${minutos}min do banco de ${ajusteFunc.nome}`,
      );
      setAjusteOpen(false);
      fetchResumo();
    } catch (e) {
      toast.error(e.response?.data?.detail || "Erro ao salvar ajuste");
    } finally {
      setSavingAjuste(false);
    }
  };

  const removerAjuste = async (ajusteId) => {
    if (!window.confirm("Remover este ajuste manual?")) return;
    try {
      await axios.delete(`${API}/rh/banco-horas/ajustes/${ajusteId}`);
      toast.success("Ajuste removido");
      // Recarrega o extrato se estiver aberto
      if (extrato) {
        abrirExtrato(extrato.funcionario.id);
      }
      fetchResumo();
    } catch (e) {
      toast.error("Erro ao remover ajuste");
    }
  };

  const abrirExtrato = async (funcId) => {
    setExtratoOpen(true);
    setExtrato(null);
    setLoadingExtrato(true);
    try {
      const params = { ate_data: ateData };
      if (deData) params.de_data = deData;
      const r = await axios.get(
        `${API}/rh/banco-horas/funcionarios/${funcId}/extrato`,
        { params },
      );
      setExtrato(r.data);
    } catch (e) {
      toast.error("Erro ao carregar extrato");
      setExtratoOpen(false);
    } finally {
      setLoadingExtrato(false);
    }
  };

  const baixarExtratoPDF = async (funcId, nome) => {
    try {
      const params = { ate_data: ateData };
      if (deData) params.de_data = deData;
      const r = await axios.get(
        `${API}/rh/banco-horas/funcionarios/${funcId}/extrato-pdf`,
        { params, responseType: "blob" },
      );
      const url = window.URL.createObjectURL(new Blob([r.data], { type: "application/pdf" }));
      const a = document.createElement("a");
      a.href = url;
      a.download = `BancoHoras_${(nome || "func").replace(/\s+/g, "_")}.pdf`;
      a.click();
      window.URL.revokeObjectURL(url);
      toast.success("Extrato exportado!");
    } catch (e) {
      toast.error("Erro ao exportar PDF");
    }
  };

  const funcionariosFiltrados = (resumo?.funcionarios || []).filter((f) => {
    if (!busca.trim()) return true;
    const q = busca.toLowerCase();
    return (
      f.nome?.toLowerCase().includes(q) ||
      f.cargo?.toLowerCase().includes(q) ||
      f.departamento?.toLowerCase().includes(q)
    );
  });

  return (
    <div className="p-6 space-y-6" data-testid="banco-horas-page">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2 text-gray-900">
            <Wallet className="text-emerald-600" size={26} />
            Banco de Horas
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Saldo acumulado por funcionário com base no Ponto Eletrônico (abonos
            já neutralizados).
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-2">
            <Calendar size={16} className="text-gray-500" />
            <Input
              type="date"
              value={ateData}
              onChange={(e) => setAteData(e.target.value)}
              className="w-44"
              data-testid="banco-horas-ate-data"
            />
          </div>
        </div>
      </div>

      {/* Cards de resumo */}
      {resumo && !loading && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4">
              <p className="text-xs text-gray-500 mb-1">Funcionários ativos</p>
              <p className="text-2xl font-bold text-gray-900">{resumo.total_funcionarios}</p>
            </CardContent>
          </Card>
          <Card className="border-emerald-200">
            <CardContent className="p-4">
              <p className="text-xs text-gray-500 mb-1 flex items-center gap-1">
                <TrendingUp size={14} className="text-emerald-600" />
                Crédito Total
              </p>
              <p className="text-2xl font-bold text-emerald-700">
                {fmtMin(resumo.total_credito_minutos)}
              </p>
            </CardContent>
          </Card>
          <Card className="border-red-200">
            <CardContent className="p-4">
              <p className="text-xs text-gray-500 mb-1 flex items-center gap-1">
                <TrendingDown size={14} className="text-red-600" />
                Débito Total
              </p>
              <p className="text-2xl font-bold text-red-700">
                -{fmtMin(resumo.total_debito_minutos)}
              </p>
            </CardContent>
          </Card>
          <Card
            className={
              resumo.saldo_liquido_minutos >= 0
                ? "border-emerald-300 bg-emerald-50"
                : "border-red-300 bg-red-50"
            }
          >
            <CardContent className="p-4">
              <p className="text-xs text-gray-500 mb-1">Saldo Líquido da Empresa</p>
              <p
                className={`text-2xl font-bold ${
                  resumo.saldo_liquido_minutos >= 0
                    ? "text-emerald-700"
                    : "text-red-700"
                }`}
                data-testid="banco-horas-saldo-liquido"
              >
                {resumo.saldo_liquido_minutos >= 0 ? "+" : ""}
                {fmtMin(resumo.saldo_liquido_minutos)}
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Busca */}
      <div className="relative max-w-md">
        <Search size={16} className="absolute left-3 top-3 text-gray-400" />
        <Input
          placeholder="Buscar por nome, cargo ou departamento..."
          value={busca}
          onChange={(e) => setBusca(e.target.value)}
          className="pl-9"
          data-testid="banco-horas-busca"
        />
      </div>

      {/* Tabela */}
      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="p-12 text-center text-gray-500">
              <Loader2 className="animate-spin inline" size={20} />
            </div>
          ) : funcionariosFiltrados.length === 0 ? (
            <div className="p-12 text-center text-gray-400">
              Nenhum funcionário encontrado.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 border-b">
                  <tr>
                    <th className="text-left p-3 font-medium text-gray-700">Funcionário</th>
                    <th className="text-left p-3 font-medium text-gray-700">Cargo</th>
                    <th className="text-center p-3 font-medium text-gray-700">Dias</th>
                    <th className="text-center p-3 font-medium text-gray-700">Período</th>
                    <th className="text-right p-3 font-medium text-gray-700">Saldo Acumulado</th>
                    <th className="text-center p-3 font-medium text-gray-700">Ações</th>
                  </tr>
                </thead>
                <tbody>
                  {funcionariosFiltrados.map((f) => (
                    <tr
                      key={f.funcionario_id}
                      className="border-b hover:bg-gray-50"
                      data-testid={`banco-horas-row-${f.funcionario_id}`}
                    >
                      <td className="p-3">
                        <div className="font-medium text-gray-900">{f.nome}</div>
                        <div className="text-xs text-gray-500">{f.departamento || "-"}</div>
                      </td>
                      <td className="p-3 text-gray-700">{f.cargo || "-"}</td>
                      <td className="p-3 text-center text-gray-700">
                        {f.dias_registrados || 0}
                      </td>
                      <td className="p-3 text-center text-xs text-gray-500">
                        {f.primeiro_registro ? (
                          <>
                            {brDate(f.primeiro_registro)}
                            <br />
                            até {brDate(f.ultimo_registro)}
                          </>
                        ) : (
                          "-"
                        )}
                      </td>
                      <td className="p-3 text-right">
                        <span
                          className={`inline-block px-3 py-1.5 rounded font-bold text-sm ${
                            f.saldo_minutos > 0
                              ? "bg-emerald-100 text-emerald-700"
                              : f.saldo_minutos < 0
                                ? "bg-red-100 text-red-700"
                                : "bg-gray-100 text-gray-600"
                          }`}
                          data-testid={`saldo-${f.funcionario_id}`}
                        >
                          {f.saldo_minutos > 0 ? "+" : ""}
                          {fmtMin(f.saldo_minutos)}
                        </span>
                      </td>
                      <td className="p-3 text-center">
                        <div className="flex gap-1 justify-center">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => abrirExtrato(f.funcionario_id)}
                            data-testid={`ver-extrato-${f.funcionario_id}`}
                          >
                            Ver Extrato
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => abrirAjuste(f)}
                            title="Adicionar/retirar horas manualmente"
                            data-testid={`ajuste-${f.funcionario_id}`}
                          >
                            <Plus size={14} />
                            <Minus size={14} className="-ml-1" />
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => baixarExtratoPDF(f.funcionario_id, f.nome)}
                            title="Exportar PDF"
                            data-testid={`pdf-extrato-${f.funcionario_id}`}
                          >
                            <FileDown size={14} />
                          </Button>
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

      {/* Modal Extrato */}
      <Dialog open={extratoOpen} onOpenChange={setExtratoOpen}>
        <DialogContent className="max-w-5xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              Extrato de Banco de Horas
              {extrato?.funcionario?.nome && ` — ${extrato.funcionario.nome}`}
            </DialogTitle>
          </DialogHeader>

          {loadingExtrato ? (
            <div className="p-12 text-center">
              <Loader2 className="animate-spin inline" size={24} />
            </div>
          ) : extrato ? (
            <div className="space-y-6">
              {/* Header */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                <div>
                  <p className="text-gray-500 text-xs">Cargo</p>
                  <p className="font-medium">{extrato.funcionario.cargo}</p>
                </div>
                <div>
                  <p className="text-gray-500 text-xs">Departamento</p>
                  <p className="font-medium">{extrato.funcionario.departamento}</p>
                </div>
                <div>
                  <p className="text-gray-500 text-xs">Jornada</p>
                  <p className="font-medium">{extrato.funcionario.jornada_nome}</p>
                </div>
                <div>
                  <p className="text-gray-500 text-xs">Apurado até</p>
                  <p className="font-medium">{brDate(extrato.ate_data)}</p>
                </div>
              </div>

              {/* Saldo destaque */}
              <div
                className={`rounded-lg p-6 text-center ${
                  extrato.saldo_total_minutos >= 0
                    ? "bg-emerald-50 border-2 border-emerald-300"
                    : "bg-red-50 border-2 border-red-300"
                }`}
              >
                <p className="text-xs text-gray-600 mb-1">SALDO TOTAL</p>
                <p
                  className={`text-4xl font-bold ${
                    extrato.saldo_total_minutos >= 0
                      ? "text-emerald-700"
                      : "text-red-700"
                  }`}
                >
                  {extrato.saldo_total_minutos >= 0 ? "+" : ""}
                  {fmtMin(extrato.saldo_total_minutos)}
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  {extrato.total_dias} dias registrados • {extrato.total_abonos} abono(s)
                </p>
              </div>

              {/* Evolução mensal */}
              <div>
                <h3 className="font-semibold mb-2 text-gray-900">Evolução mês a mês</h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="bg-gray-50 border-b">
                      <tr>
                        <th className="text-left p-2">Mês</th>
                        <th className="text-right p-2">Trabalhado</th>
                        <th className="text-right p-2">Previsto</th>
                        <th className="text-right p-2">Saldo Mês</th>
                        <th className="text-right p-2">Saldo Acum.</th>
                        <th className="text-center p-2">Dias</th>
                        <th className="text-center p-2">Abonos</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(extrato.evolucao_mensal || []).map((ev) => (
                        <tr key={ev.mes} className="border-b">
                          <td className="p-2 font-medium">{mesLabel(ev.mes)}</td>
                          <td className="p-2 text-right">{fmtMin(ev.minutos_trabalhados)}</td>
                          <td className="p-2 text-right">{fmtMin(ev.minutos_previstos)}</td>
                          <td
                            className={`p-2 text-right font-semibold ${
                              ev.saldo_minutos > 0
                                ? "text-emerald-700"
                                : ev.saldo_minutos < 0
                                  ? "text-red-700"
                                  : ""
                            }`}
                          >
                            {ev.saldo_minutos > 0 ? "+" : ""}
                            {fmtMin(ev.saldo_minutos)}
                          </td>
                          <td
                            className={`p-2 text-right font-bold ${
                              ev.saldo_acumulado_minutos >= 0
                                ? "text-emerald-700"
                                : "text-red-700"
                            }`}
                          >
                            {ev.saldo_acumulado_minutos >= 0 ? "+" : ""}
                            {fmtMin(ev.saldo_acumulado_minutos)}
                          </td>
                          <td className="p-2 text-center">{ev.dias}</td>
                          <td className="p-2 text-center">{ev.abonos}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Detalhe diário */}
              <div>
                <h3 className="font-semibold mb-2 text-gray-900">
                  Detalhe diário ({extrato.detalhe_dias?.length || 0} registros)
                </h3>
                <div className="max-h-96 overflow-y-auto border rounded">
                  <table className="w-full text-xs">
                    <thead className="bg-gray-50 border-b sticky top-0">
                      <tr>
                        <th className="text-left p-2">Data</th>
                        <th className="text-left p-2">Batidas</th>
                        <th className="text-right p-2">Trab.</th>
                        <th className="text-right p-2">Previsto</th>
                        <th className="text-right p-2">Saldo Dia</th>
                        <th className="text-right p-2">Acum.</th>
                        <th className="text-left p-2">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(extrato.detalhe_dias || []).map((d) => (
                        <tr key={d.data} className="border-b hover:bg-gray-50">
                          <td className="p-2">{brDate(d.data)}</td>
                          <td className="p-2 font-mono text-gray-600">
                            {(d.batidas || []).join(" ") || "-"}
                          </td>
                          <td className="p-2 text-right">{fmtMin(d.minutos_trabalhados)}</td>
                          <td className="p-2 text-right text-gray-500">
                            {fmtMin(d.minutos_previstos)}
                          </td>
                          <td
                            className={`p-2 text-right ${
                              d.saldo_dia_minutos > 0
                                ? "text-emerald-700"
                                : d.saldo_dia_minutos < 0
                                  ? "text-red-700"
                                  : "text-gray-500"
                            }`}
                          >
                            {d.saldo_dia_minutos > 0 ? "+" : ""}
                            {fmtMin(d.saldo_dia_minutos)}
                          </td>
                          <td
                            className={`p-2 text-right font-semibold ${
                              d.saldo_acumulado_minutos >= 0
                                ? "text-emerald-700"
                                : "text-red-700"
                            }`}
                          >
                            {d.saldo_acumulado_minutos >= 0 ? "+" : ""}
                            {fmtMin(d.saldo_acumulado_minutos)}
                          </td>
                          <td className="p-2">
                            {d.abono ? (
                              <span className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded text-[10px]">
                                Abono: {d.abono.tipo}
                              </span>
                            ) : (
                              d.status_dia || "-"
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="flex justify-end gap-2 border-t pt-4">
                <Button
                  variant="outline"
                  onClick={() =>
                    baixarExtratoPDF(extrato.funcionario.id, extrato.funcionario.nome)
                  }
                  data-testid="extrato-modal-pdf-btn"
                >
                  <FileDown size={16} className="mr-2" />
                  Exportar PDF
                </Button>
                <Button onClick={() => setExtratoOpen(false)}>Fechar</Button>
              </div>
            </div>
          ) : null}
        </DialogContent>
      </Dialog>
    </div>
  );
}
me="px-2 py-0.5 bg-blue-100 text-blue-700 rounded text-[10px]">
                                Abono: {d.abono.tipo}
                              </span>
                            ) : (
                              d.status_dia || "-"
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="flex justify-end gap-2 border-t pt-4">
                <Button
                  variant="outline"
                  onClick={() =>
                    baixarExtratoPDF(extrato.funcionario.id, extrato.funcionario.nome)
                  }
                  data-testid="extrato-modal-pdf-btn"
                >
                  <FileDown size={16} className="mr-2" />
                  Exportar PDF
                </Button>
                <Button onClick={() => setExtratoOpen(false)}>Fechar</Button>
              </div>
            </div>
          ) : null}
        </DialogContent>
      </Dialog>
    </div>
  );
}
