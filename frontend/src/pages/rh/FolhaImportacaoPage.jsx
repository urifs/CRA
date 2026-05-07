import { useState, useEffect, useRef } from "react";
import axios from "axios";
import { API } from "@/App";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Upload,
  FileText,
  Loader2,
  Send,
  Trash2,
  Eye,
  CheckCircle2,
  AlertCircle,
  Clock,
  XCircle,
  Users,
  Download,
  HelpCircle,
} from "lucide-react";
import { toast } from "sonner";

const fmtBRL = (v) =>
  new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(v || 0);

const STATUS_CFG = {
  em_revisao: { label: "Em revisão", color: "bg-amber-100 text-amber-800 border-amber-300", icon: Clock },
  enviada: { label: "Enviada ao financeiro", color: "bg-blue-100 text-blue-800 border-blue-300", icon: Send },
  aceita: { label: "Aceita / Lançada", color: "bg-emerald-100 text-emerald-800 border-emerald-300", icon: CheckCircle2 },
  rejeitada: { label: "Rejeitada", color: "bg-red-100 text-red-800 border-red-300", icon: XCircle },
};

export default function FolhaImportacaoPage() {
  const [folhas, setFolhas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef(null);

  // Visualização / mapeamento manual
  const [folhaAtual, setFolhaAtual] = useState(null);
  const [funcionarios, setFuncionarios] = useState([]);
  const [mapping, setMapping] = useState({}); // {linha_id: funcionario_id}
  const [salvandoMapping, setSalvandoMapping] = useState(false);

  // Envio para financeiro
  const [enviarOpen, setEnviarOpen] = useState(false);
  const [envioModo, setEnvioModo] = useState("cheio");
  const [envioObs, setEnvioObs] = useState("");
  const [enviando, setEnviando] = useState(false);

  useEffect(() => {
    fetchFolhas();
    fetchFuncionarios();
  }, []);

  const fetchFolhas = async () => {
    setLoading(true);
    try {
      const r = await axios.get(`${API}/folha-pagamento`);
      setFolhas(r.data || []);
    } catch (e) {
      toast.error("Erro ao carregar folhas importadas");
    } finally {
      setLoading(false);
    }
  };

  const fetchFuncionarios = async () => {
    try {
      const r = await axios.get(`${API}/rh/funcionarios`);
      setFuncionarios((r.data || []).filter((f) => f.status === "ativo"));
    } catch (e) {
      // silencioso
    }
  };

  const onFilePick = () => fileInputRef.current?.click();

  const onFileChange = async (e) => {
    const f = e.target.files?.[0];
    e.target.value = "";
    if (!f) return;
    if (!f.name.toLowerCase().endsWith(".pdf")) {
      toast.error("Envie um PDF");
      return;
    }
    if (f.size > 30 * 1024 * 1024) {
      toast.error("Arquivo muito grande (máx 30MB)");
      return;
    }
    setUploading(true);
    const fd = new FormData();
    fd.append("arquivo", f);
    try {
      const r = await axios.post(`${API}/folha-pagamento/importar`, fd, {
        headers: { "Content-Type": "multipart/form-data" },
        timeout: 180000,
      });
      toast.success(
        `Folha importada: ${r.data.total_funcionarios} funcionário(s) — ${fmtBRL(r.data.total_geral_liquido)}`,
      );
      fetchFolhas();
      // Abre detalhe imediatamente para o RH revisar
      setFolhaAtual(r.data);
      const initial = {};
      (r.data.funcionarios || []).forEach((linha) => {
        if (linha.funcionario_id) initial[linha.linha_id] = linha.funcionario_id;
      });
      setMapping(initial);
    } catch (err) {
      toast.error(err.response?.data?.detail || "Erro ao importar folha");
    } finally {
      setUploading(false);
    }
  };

  const abrirFolha = async (id) => {
    try {
      const r = await axios.get(`${API}/folha-pagamento/${id}`);
      setFolhaAtual(r.data);
      const initial = {};
      (r.data.funcionarios || []).forEach((linha) => {
        if (linha.funcionario_id) initial[linha.linha_id] = linha.funcionario_id;
      });
      setMapping(initial);
    } catch (e) {
      toast.error("Erro ao abrir folha");
    }
  };

  const salvarMapping = async () => {
    if (!folhaAtual) return;
    setSalvandoMapping(true);
    try {
      const payload = {
        funcionarios: Object.entries(mapping).map(([linha_id, funcionario_id]) => ({
          linha_id,
          funcionario_id,
        })),
      };
      await axios.post(
        `${API}/folha-pagamento/${folhaAtual.id}/resolver-matches`,
        payload,
      );
      toast.success("Vínculos salvos");
      const r = await axios.get(`${API}/folha-pagamento/${folhaAtual.id}`);
      setFolhaAtual(r.data);
      fetchFolhas();
    } catch (e) {
      toast.error(e.response?.data?.detail || "Erro ao salvar");
    } finally {
      setSalvandoMapping(false);
    }
  };

  const enviarParaFinanceiro = async () => {
    if (!folhaAtual) return;
    setEnviando(true);
    try {
      await axios.post(`${API}/folha-pagamento/${folhaAtual.id}/enviar-financeiro`, {
        modo: envioModo,
        observacao: envioObs,
      });
      toast.success("Folha enviada ao Financeiro");
      setEnviarOpen(false);
      setEnvioObs("");
      const r = await axios.get(`${API}/folha-pagamento/${folhaAtual.id}`);
      setFolhaAtual(r.data);
      fetchFolhas();
    } catch (e) {
      toast.error(e.response?.data?.detail || "Erro ao enviar");
    } finally {
      setEnviando(false);
    }
  };

  const excluirFolha = async (id) => {
    if (!window.confirm("Excluir esta folha importada? PDFs anexados serão removidos.")) return;
    try {
      await axios.delete(`${API}/folha-pagamento/${id}`);
      toast.success("Folha excluída");
      fetchFolhas();
      if (folhaAtual?.id === id) setFolhaAtual(null);
    } catch (e) {
      toast.error(e.response?.data?.detail || "Erro ao excluir");
    }
  };

  const baixarMaster = async (id) => {
    try {
      const r = await axios.get(`${API}/folha-pagamento/${id}/master-pdf`, {
        responseType: "blob",
      });
      const url = URL.createObjectURL(new Blob([r.data], { type: "application/pdf" }));
      const a = document.createElement("a");
      a.href = url;
      a.download = `folha_${id.slice(0, 8)}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      toast.error("Erro ao baixar PDF");
    }
  };

  const baixarHolerite = async (folhaId, linhaId, nome) => {
    try {
      const r = await axios.get(
        `${API}/folha-pagamento/${folhaId}/holerite/${linhaId}`,
        { responseType: "blob" },
      );
      const url = URL.createObjectURL(new Blob([r.data], { type: "application/pdf" }));
      const a = document.createElement("a");
      a.href = url;
      a.download = `holerite_${(nome || "func").replace(/\s+/g, "_")}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      toast.error("Erro ao baixar holerite");
    }
  };

  const semMatchCount = (folhaAtual?.funcionarios || []).filter(
    (f) => !mapping[f.linha_id] && !f.funcionario_id,
  ).length;

  const podeEnviar =
    folhaAtual &&
    ["em_revisao", "rejeitada"].includes(folhaAtual.status) &&
    semMatchCount === 0;

  return (
    <div className="p-6 space-y-6" data-testid="folha-importacao-page">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2 text-gray-900">
            <FileText className="text-indigo-600" size={26} />
            Importação de Folha de Pagamento
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Importe a folha consolidada (PDF), revise os funcionários reconhecidos e envie ao
            Financeiro como folha cheia ou individual.
          </p>
        </div>
        <Button
          onClick={onFilePick}
          disabled={uploading}
          className="bg-indigo-600 hover:bg-indigo-700"
          data-testid="btn-importar-folha"
        >
          {uploading ? (
            <Loader2 size={16} className="animate-spin mr-2" />
          ) : (
            <Upload size={16} className="mr-2" />
          )}
          {uploading ? "Processando PDF..." : "Importar Folha (PDF)"}
        </Button>
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,application/pdf"
          className="hidden"
          onChange={onFileChange}
        />
      </div>

      {/* Lista de folhas */}
      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="p-12 text-center text-gray-500">
              <Loader2 className="animate-spin inline" size={20} />
            </div>
          ) : folhas.length === 0 ? (
            <div className="p-12 text-center text-gray-400 space-y-2">
              <FileText size={36} className="inline text-gray-300" />
              <p>Nenhuma folha importada ainda.</p>
              <p className="text-xs">
                Clique em "Importar Folha (PDF)" para começar. Cada página do PDF deve conter o
                holerite de um funcionário.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 border-b">
                  <tr>
                    <th className="text-left p-3 font-medium text-gray-700">Competência</th>
                    <th className="text-left p-3 font-medium text-gray-700">Empresa</th>
                    <th className="text-center p-3 font-medium text-gray-700">Funcionários</th>
                    <th className="text-right p-3 font-medium text-gray-700">Total Líquido</th>
                    <th className="text-center p-3 font-medium text-gray-700">Status</th>
                    <th className="text-center p-3 font-medium text-gray-700">Ações</th>
                  </tr>
                </thead>
                <tbody>
                  {folhas.map((f) => {
                    const cfg = STATUS_CFG[f.status] || STATUS_CFG.em_revisao;
                    const Icon = cfg.icon;
                    return (
                      <tr
                        key={f.id}
                        className="border-b hover:bg-gray-50"
                        data-testid={`folha-row-${f.id}`}
                      >
                        <td className="p-3 font-medium">
                          {String(f.mes_competencia).padStart(2, "0")}/{f.ano_competencia}
                        </td>
                        <td className="p-3 text-gray-700">
                          {f.empresa || "—"}
                          <div className="text-xs text-gray-400">{f.cnpj}</div>
                        </td>
                        <td className="p-3 text-center">
                          <span className="px-2 py-0.5 bg-indigo-100 text-indigo-700 rounded font-semibold">
                            {f.total_funcionarios}
                          </span>
                        </td>
                        <td className="p-3 text-right font-bold text-emerald-700">
                          {fmtBRL(f.total_geral_liquido)}
                        </td>
                        <td className="p-3 text-center">
                          <span
                            className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium border ${cfg.color}`}
                          >
                            <Icon size={12} />
                            {cfg.label}
                          </span>
                        </td>
                        <td className="p-3 text-center">
                          <div className="flex gap-1 justify-center">
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => abrirFolha(f.id)}
                              data-testid={`btn-abrir-folha-${f.id}`}
                            >
                              <Eye size={14} />
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => baixarMaster(f.id)}
                              title="Baixar PDF original"
                            >
                              <Download size={14} />
                            </Button>
                            {f.status !== "aceita" && (
                              <Button
                                size="sm"
                                variant="outline"
                                className="text-red-600 hover:bg-red-50"
                                onClick={() => excluirFolha(f.id)}
                              >
                                <Trash2 size={14} />
                              </Button>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Modal de detalhe / mapeamento */}
      <Dialog open={!!folhaAtual} onOpenChange={(o) => !o && setFolhaAtual(null)}>
        <DialogContent className="max-w-6xl max-h-[90vh] overflow-y-auto" data-testid="folha-detalhe-modal">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <FileText size={20} className="text-indigo-600" />
              Folha de {folhaAtual && String(folhaAtual.mes_competencia).padStart(2, "0")}/
              {folhaAtual?.ano_competencia} — {folhaAtual?.empresa || "—"}
            </DialogTitle>
            <DialogDescription>
              Revise o vínculo de cada linha com um funcionário cadastrado e envie ao Financeiro.
            </DialogDescription>
          </DialogHeader>

          {folhaAtual && (
            <div className="space-y-4">
              {/* Resumo */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                <div className="p-3 bg-gray-50 rounded">
                  <p className="text-xs text-gray-500">CNPJ</p>
                  <p className="font-medium">{folhaAtual.cnpj || "—"}</p>
                </div>
                <div className="p-3 bg-gray-50 rounded">
                  <p className="text-xs text-gray-500">Funcionários</p>
                  <p className="font-bold text-indigo-700">{folhaAtual.total_funcionarios}</p>
                </div>
                <div className="p-3 bg-gray-50 rounded">
                  <p className="text-xs text-gray-500">Total Líquido</p>
                  <p className="font-bold text-emerald-700">
                    {fmtBRL(folhaAtual.total_geral_liquido)}
                  </p>
                </div>
                <div className="p-3 bg-gray-50 rounded">
                  <p className="text-xs text-gray-500">Páginas no PDF</p>
                  <p className="font-medium">{folhaAtual.total_paginas}</p>
                </div>
              </div>

              {semMatchCount > 0 && (
                <div className="p-3 bg-amber-50 border border-amber-200 rounded text-sm flex items-center gap-2 text-amber-800">
                  <AlertCircle size={16} />
                  <span>
                    {semMatchCount} funcionário(s) sem vínculo definido. Selecione no dropdown
                    abaixo antes de enviar ao financeiro.
                  </span>
                </div>
              )}

              {/* Tabela de funcionários */}
              <div className="overflow-x-auto border rounded">
                <table className="w-full text-sm">
                  <thead className="bg-gray-100 border-b">
                    <tr>
                      <th className="text-left p-2">Nome no PDF</th>
                      <th className="text-left p-2">Função</th>
                      <th className="text-right p-2">Vencim.</th>
                      <th className="text-right p-2">Descontos</th>
                      <th className="text-right p-2">Líquido</th>
                      <th className="text-left p-2 min-w-[260px]">Vínculo Funcionário</th>
                      <th className="text-center p-2">Holerite</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(folhaAtual.funcionarios || []).map((linha) => {
                      const corMatch =
                        linha.match_status === "high" || linha.match_status === "manual"
                          ? "bg-emerald-50/60"
                          : linha.match_status === "medium"
                            ? "bg-amber-50/40"
                            : !mapping[linha.linha_id]
                              ? "bg-red-50/40"
                              : "";
                      return (
                        <tr
                          key={linha.linha_id}
                          className={`border-b ${corMatch}`}
                          data-testid={`linha-${linha.linha_id}`}
                        >
                          <td className="p-2">
                            <p className="font-medium">{linha.nome_pdf}</p>
                            {linha.codigo_pdf && (
                              <p className="text-xs text-gray-500">Cód: {linha.codigo_pdf}</p>
                            )}
                          </td>
                          <td className="p-2 text-xs text-gray-600">{linha.funcao_pdf || "—"}</td>
                          <td className="p-2 text-right">{fmtBRL(linha.total_vencimentos)}</td>
                          <td className="p-2 text-right text-red-600">
                            {fmtBRL(linha.total_descontos)}
                          </td>
                          <td className="p-2 text-right font-bold text-emerald-700">
                            {fmtBRL(linha.valor_liquido)}
                          </td>
                          <td className="p-2">
                            <Select
                              value={mapping[linha.linha_id] || "__nao_mapear__"}
                              onValueChange={(v) =>
                                setMapping((prev) => ({
                                  ...prev,
                                  [linha.linha_id]: v === "__nao_mapear__" ? "" : v,
                                }))
                              }
                            >
                              <SelectTrigger
                                className="h-8 text-xs"
                                data-testid={`select-func-${linha.linha_id}`}
                              >
                                <SelectValue placeholder="Selecione..." />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="__nao_mapear__">— Sem vínculo —</SelectItem>
                                {funcionarios.map((f) => (
                                  <SelectItem key={f.id} value={f.id}>
                                    {f.nome}
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                            {linha.match_score > 0 && (
                              <p className="text-[10px] text-gray-500 mt-0.5 flex items-center gap-1">
                                {linha.match_status === "high" && (
                                  <CheckCircle2 size={10} className="text-emerald-600" />
                                )}
                                {linha.match_status === "medium" && (
                                  <HelpCircle size={10} className="text-amber-600" />
                                )}
                                {linha.match_status === "manual" && (
                                  <CheckCircle2 size={10} className="text-blue-600" />
                                )}
                                Sugestão: {linha.match_nome_db} ({linha.match_score}%)
                              </p>
                            )}
                          </td>
                          <td className="p-2 text-center">
                            {linha.anexo_holerite_path && (
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() =>
                                  baixarHolerite(folhaAtual.id, linha.linha_id, linha.nome_pdf)
                                }
                                title="Baixar holerite individual"
                              >
                                <Download size={14} />
                              </Button>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              <div className="flex flex-wrap justify-end gap-2 pt-3 border-t">
                {folhaAtual.status === "em_revisao" && (
                  <Button
                    variant="outline"
                    onClick={salvarMapping}
                    disabled={salvandoMapping}
                    data-testid="btn-salvar-mapping"
                  >
                    {salvandoMapping && (
                      <Loader2 size={14} className="animate-spin mr-2" />
                    )}
                    Salvar vínculos
                  </Button>
                )}
                {folhaAtual.status === "aceita" && (
                  <span className="px-3 py-2 bg-emerald-50 border border-emerald-200 rounded text-sm text-emerald-800 flex items-center gap-2">
                    <CheckCircle2 size={14} />
                    Folha já lançada no Financeiro
                  </span>
                )}
                {folhaAtual.status === "enviada" && (
                  <span className="px-3 py-2 bg-blue-50 border border-blue-200 rounded text-sm text-blue-800 flex items-center gap-2">
                    <Send size={14} />
                    Aguardando aprovação no Financeiro
                  </span>
                )}
                {podeEnviar && (
                  <Button
                    onClick={async () => {
                      // Salva mapping antes para não perder
                      await salvarMapping();
                      setEnviarOpen(true);
                    }}
                    className="bg-emerald-600 hover:bg-emerald-700"
                    data-testid="btn-enviar-financeiro"
                  >
                    <Send size={14} className="mr-2" />
                    Enviar ao Financeiro
                  </Button>
                )}
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Modal de envio (escolha do modo) */}
      <Dialog open={enviarOpen} onOpenChange={(o) => !enviando && setEnviarOpen(o)}>
        <DialogContent className="max-w-md" data-testid="dialog-enviar-financeiro">
          <DialogHeader>
            <DialogTitle>Enviar ao Financeiro</DialogTitle>
            <DialogDescription>
              Como deseja que o Financeiro lance esta folha?
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3">
            <button
              type="button"
              onClick={() => setEnvioModo("cheio")}
              className={`w-full text-left p-3 rounded border-2 transition ${
                envioModo === "cheio"
                  ? "border-indigo-500 bg-indigo-50"
                  : "border-gray-200 hover:border-gray-300"
              }`}
              data-testid="btn-modo-cheio"
            >
              <div className="flex items-center gap-2">
                <FileText size={16} className="text-indigo-600" />
                <span className="font-medium">Folha cheia (1 conta única)</span>
              </div>
              <p className="text-xs text-gray-500 mt-1">
                Cria 1 lançamento agrupado com o valor total. Ideal quando todos recebem na mesma
                data e por uma única transferência.
              </p>
            </button>
            <button
              type="button"
              onClick={() => setEnvioModo("individual")}
              className={`w-full text-left p-3 rounded border-2 transition ${
                envioModo === "individual"
                  ? "border-indigo-500 bg-indigo-50"
                  : "border-gray-200 hover:border-gray-300"
              }`}
              data-testid="btn-modo-individual"
            >
              <div className="flex items-center gap-2">
                <Users size={16} className="text-indigo-600" />
                <span className="font-medium">
                  Individual ({folhaAtual?.total_funcionarios || 0} contas, 1 por funcionário)
                </span>
              </div>
              <p className="text-xs text-gray-500 mt-1">
                Cria 1 conta a pagar para cada funcionário com seu próprio holerite anexado.
              </p>
            </button>
            <div>
              <Label className="text-xs">Observação ao Financeiro (opcional)</Label>
              <Textarea
                value={envioObs}
                onChange={(e) => setEnvioObs(e.target.value)}
                rows={2}
                placeholder="Ex.: Pagamento via PIX no dia 5..."
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEnviarOpen(false)} disabled={enviando}>
              Cancelar
            </Button>
            <Button
              onClick={enviarParaFinanceiro}
              disabled={enviando}
              className="bg-emerald-600 hover:bg-emerald-700"
              data-testid="btn-confirmar-envio"
            >
              {enviando && <Loader2 size={14} className="animate-spin mr-2" />}
              Enviar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
