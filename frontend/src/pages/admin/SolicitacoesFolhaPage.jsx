import { useState, useEffect } from "react";
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
  FileText,
  Loader2,
  CheckCircle2,
  XCircle,
  Clock,
  Users,
  AlertCircle,
  Inbox,
} from "lucide-react";
import { toast } from "sonner";

const fmtBRL = (v) =>
  new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(v || 0);

const STATUS_CFG = {
  pendente: { label: "Pendente", color: "bg-amber-100 text-amber-800 border-amber-300", icon: Clock },
  aceita: { label: "Aceita", color: "bg-emerald-100 text-emerald-800 border-emerald-300", icon: CheckCircle2 },
  rejeitada: { label: "Rejeitada", color: "bg-red-100 text-red-800 border-red-300", icon: XCircle },
};

export default function SolicitacoesFolhaPage() {
  const [solicitacoes, setSolicitacoes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filtroStatus, setFiltroStatus] = useState("pendente");

  // Aceitar
  const [aceitarSol, setAceitarSol] = useState(null);
  const [planos, setPlanos] = useState([]);
  const [contasBancarias, setContasBancarias] = useState([]);
  const [formasPagamento, setFormasPagamento] = useState([]);
  const [aceitarForm, setAceitarForm] = useState({
    plano_contas_id: "",
    data_vencimento: "",
    conta_bancaria_id: "",
    forma_pagamento: "",
    observacao: "",
    modo_override: null, // permite trocar individual <-> cheio
  });
  const [aceitando, setAceitando] = useState(false);

  // Rejeitar
  const [rejeitarSol, setRejeitarSol] = useState(null);
  const [motivoRejeicao, setMotivoRejeicao] = useState("");
  const [rejeitando, setRejeitando] = useState(false);

  useEffect(() => {
    fetchSolicitacoes();
    fetchAuxiliares();
  }, [filtroStatus]);

  const fetchSolicitacoes = async () => {
    setLoading(true);
    try {
      const params = filtroStatus !== "todas" ? { status: filtroStatus } : {};
      const r = await axios.get(`${API}/financeiro/solicitacoes-folha`, { params });
      setSolicitacoes(r.data || []);
    } catch (e) {
      toast.error("Erro ao carregar solicitações");
    } finally {
      setLoading(false);
    }
  };

  const fetchAuxiliares = async () => {
    try {
      const [p, c, f] = await Promise.all([
        axios.get(`${API}/admin/plano-contas`),
        axios.get(`${API}/admin/contas-bancarias`),
        axios.get(`${API}/admin/formas-pagamento`),
      ]);
      // Sugere contas de despesa/folha
      setPlanos((p.data || []).filter((x) => x.tipo === "despesa" || !x.tipo));
      setContasBancarias(c.data || []);
      setFormasPagamento(f.data || []);
    } catch (e) {
      // silencioso — endpoints podem não existir, UI lida
    }
  };

  const abrirAceitar = (sol) => {
    // Auto-sugere data: 5º dia do próximo mês
    const hoje = new Date();
    const proxMes = new Date(hoje.getFullYear(), hoje.getMonth() + 1, 5);
    const sugDate = proxMes.toISOString().slice(0, 10);
    // Auto-sugere plano com nome contendo "folha", "salário" ou "pessoal"
    const sug =
      planos.find((p) => /folha|sal[áa]rio|pessoal/i.test(p.nome || ""))?.id || "";
    setAceitarForm({
      plano_contas_id: sug,
      data_vencimento: sugDate,
      conta_bancaria_id: "",
      forma_pagamento: "",
      observacao: "",
      modo_override: sol.modo,
    });
    setAceitarSol(sol);
  };

  const confirmarAceitar = async () => {
    if (!aceitarSol) return;
    if (!aceitarForm.plano_contas_id) {
      toast.error("Selecione o plano de contas");
      return;
    }
    if (!aceitarForm.data_vencimento) {
      toast.error("Informe a data de vencimento");
      return;
    }
    setAceitando(true);
    try {
      // Se o usuário trocou o modo, atualiza primeiro a solicitação no servidor
      if (aceitarForm.modo_override && aceitarForm.modo_override !== aceitarSol.modo) {
        // Reenvio rápido: chamamos o endpoint de envio para sobrescrever o modo
        await axios.post(
          `${API}/folha-pagamento/${aceitarSol.folha_id}/enviar-financeiro`,
          { modo: aceitarForm.modo_override },
        );
      }
      const r = await axios.post(
        `${API}/financeiro/solicitacoes-folha/${aceitarSol.id}/aceitar`,
        {
          plano_contas_id: aceitarForm.plano_contas_id,
          data_vencimento: aceitarForm.data_vencimento,
          conta_bancaria_id: aceitarForm.conta_bancaria_id || null,
          forma_pagamento: aceitarForm.forma_pagamento || null,
          observacao: aceitarForm.observacao || null,
        },
      );
      toast.success(`${r.data.total} conta(s) a pagar criadas`);
      setAceitarSol(null);
      fetchSolicitacoes();
    } catch (e) {
      toast.error(e.response?.data?.detail || "Erro ao aceitar");
    } finally {
      setAceitando(false);
    }
  };

  const confirmarRejeitar = async () => {
    if (!rejeitarSol) return;
    setRejeitando(true);
    try {
      await axios.post(
        `${API}/financeiro/solicitacoes-folha/${rejeitarSol.id}/rejeitar`,
        { motivo: motivoRejeicao },
      );
      toast.success("Solicitação rejeitada");
      setRejeitarSol(null);
      setMotivoRejeicao("");
      fetchSolicitacoes();
    } catch (e) {
      toast.error(e.response?.data?.detail || "Erro ao rejeitar");
    } finally {
      setRejeitando(false);
    }
  };

  const totalPendente = solicitacoes.filter((s) => s.status === "pendente").length;

  return (
    <div className="p-6 space-y-6" data-testid="solicitacoes-folha-page">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2 text-gray-900">
            <Inbox className="text-indigo-600" size={26} />
            Solicitações de Folha de Pagamento
            {totalPendente > 0 && (
              <span className="px-2 py-0.5 bg-red-100 text-red-700 rounded-full text-sm font-bold">
                {totalPendente} pendente{totalPendente > 1 ? "s" : ""}
              </span>
            )}
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Folhas enviadas pelo RH aguardando aprovação para gerar contas a pagar.
          </p>
        </div>
        <div className="flex gap-2">
          {["pendente", "aceita", "rejeitada", "todas"].map((s) => (
            <Button
              key={s}
              size="sm"
              variant={filtroStatus === s ? "default" : "outline"}
              onClick={() => setFiltroStatus(s)}
              className={filtroStatus === s ? "bg-indigo-600 hover:bg-indigo-700" : ""}
              data-testid={`filtro-${s}`}
            >
              {s.charAt(0).toUpperCase() + s.slice(1)}
            </Button>
          ))}
        </div>
      </div>

      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="p-12 text-center text-gray-500">
              <Loader2 className="animate-spin inline" size={20} />
            </div>
          ) : solicitacoes.length === 0 ? (
            <div className="p-12 text-center text-gray-400">
              <Inbox size={36} className="inline text-gray-300 mb-2" />
              <p>Nenhuma solicitação {filtroStatus !== "todas" ? `${filtroStatus}` : ""}.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 border-b">
                  <tr>
                    <th className="text-left p-3 font-medium text-gray-700">Competência</th>
                    <th className="text-left p-3 font-medium text-gray-700">Empresa</th>
                    <th className="text-center p-3 font-medium text-gray-700">Modo</th>
                    <th className="text-center p-3 font-medium text-gray-700">Func.</th>
                    <th className="text-right p-3 font-medium text-gray-700">Total</th>
                    <th className="text-center p-3 font-medium text-gray-700">Status</th>
                    <th className="text-center p-3 font-medium text-gray-700">Ações</th>
                  </tr>
                </thead>
                <tbody>
                  {solicitacoes.map((s) => {
                    const cfg = STATUS_CFG[s.status] || STATUS_CFG.pendente;
                    const Icon = cfg.icon;
                    return (
                      <tr
                        key={s.id}
                        className="border-b hover:bg-gray-50"
                        data-testid={`sol-row-${s.id}`}
                      >
                        <td className="p-3 font-medium">
                          {String(s.mes_competencia).padStart(2, "0")}/{s.ano_competencia}
                        </td>
                        <td className="p-3 text-gray-700">{s.empresa || "—"}</td>
                        <td className="p-3 text-center">
                          {s.modo === "cheio" ? (
                            <span className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded text-xs">
                              Folha cheia
                            </span>
                          ) : (
                            <span className="px-2 py-0.5 bg-purple-100 text-purple-700 rounded text-xs">
                              Individual
                            </span>
                          )}
                        </td>
                        <td className="p-3 text-center">{s.total_funcionarios}</td>
                        <td className="p-3 text-right font-bold text-emerald-700">
                          {fmtBRL(s.total_geral_liquido)}
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
                          {s.status === "pendente" ? (
                            <div className="flex gap-1 justify-center">
                              <Button
                                size="sm"
                                className="bg-emerald-600 hover:bg-emerald-700"
                                onClick={() => abrirAceitar(s)}
                                data-testid={`btn-aceitar-${s.id}`}
                              >
                                <CheckCircle2 size={14} className="mr-1" /> Aceitar
                              </Button>
                              <Button
                                size="sm"
                                variant="outline"
                                className="text-red-600 border-red-300 hover:bg-red-50"
                                onClick={() => setRejeitarSol(s)}
                                data-testid={`btn-rejeitar-${s.id}`}
                              >
                                <XCircle size={14} />
                              </Button>
                            </div>
                          ) : s.status === "aceita" ? (
                            <span className="text-xs text-emerald-700 font-medium">
                              {s.contas_pagar_ids?.length || 0} conta(s) criadas
                            </span>
                          ) : (
                            <span className="text-xs text-red-700">
                              {s.motivo_rejeicao || "Rejeitada"}
                            </span>
                          )}
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

      {/* Modal Aceitar */}
      <Dialog open={!!aceitarSol} onOpenChange={(o) => !aceitando && !o && setAceitarSol(null)}>
        <DialogContent className="max-w-2xl" data-testid="dialog-aceitar">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <CheckCircle2 size={20} className="text-emerald-600" />
              Aceitar Folha — gerar contas a pagar
            </DialogTitle>
            <DialogDescription>
              Confirme o modo de lançamento e os parâmetros financeiros.
            </DialogDescription>
          </DialogHeader>
          {aceitarSol && (
            <div className="space-y-4">
              <div className="p-3 bg-indigo-50 border border-indigo-200 rounded text-sm space-y-1">
                <p>
                  <strong>Competência:</strong>{" "}
                  {String(aceitarSol.mes_competencia).padStart(2, "0")}/
                  {aceitarSol.ano_competencia} — <strong>{aceitarSol.empresa || "—"}</strong>
                </p>
                <p>
                  <strong>Total:</strong> {fmtBRL(aceitarSol.total_geral_liquido)} ·{" "}
                  <strong>{aceitarSol.total_funcionarios}</strong> funcionário(s)
                </p>
              </div>

              {/* Modo (override permitido) */}
              <div>
                <Label className="text-xs">Modo de lançamento</Label>
                <div className="grid grid-cols-2 gap-2 mt-1">
                  <button
                    type="button"
                    onClick={() =>
                      setAceitarForm({ ...aceitarForm, modo_override: "cheio" })
                    }
                    className={`p-2 rounded border-2 text-sm transition ${
                      aceitarForm.modo_override === "cheio"
                        ? "border-indigo-500 bg-indigo-50 font-medium"
                        : "border-gray-200"
                    }`}
                    data-testid="aceitar-modo-cheio"
                  >
                    <FileText size={14} className="inline mr-1" />
                    1 conta cheia
                  </button>
                  <button
                    type="button"
                    onClick={() =>
                      setAceitarForm({ ...aceitarForm, modo_override: "individual" })
                    }
                    className={`p-2 rounded border-2 text-sm transition ${
                      aceitarForm.modo_override === "individual"
                        ? "border-indigo-500 bg-indigo-50 font-medium"
                        : "border-gray-200"
                    }`}
                    data-testid="aceitar-modo-individual"
                  >
                    <Users size={14} className="inline mr-1" />
                    {aceitarSol.total_funcionarios} contas individuais
                  </button>
                </div>
                {aceitarForm.modo_override !== aceitarSol.modo && (
                  <p className="text-xs text-amber-700 mt-1 flex items-center gap-1">
                    <AlertCircle size={10} /> Modo alterado em relação à solicitação do RH.
                  </p>
                )}
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <Label className="text-xs">Plano de Contas *</Label>
                  <Select
                    value={aceitarForm.plano_contas_id}
                    onValueChange={(v) =>
                      setAceitarForm({ ...aceitarForm, plano_contas_id: v })
                    }
                  >
                    <SelectTrigger data-testid="select-plano-contas">
                      <SelectValue placeholder="Selecione..." />
                    </SelectTrigger>
                    <SelectContent>
                      {planos.map((p) => (
                        <SelectItem key={p.id} value={p.id}>
                          {p.nome}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label className="text-xs">Data de Vencimento *</Label>
                  <Input
                    type="date"
                    value={aceitarForm.data_vencimento}
                    onChange={(e) =>
                      setAceitarForm({ ...aceitarForm, data_vencimento: e.target.value })
                    }
                    data-testid="input-vencimento"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <Label className="text-xs">Conta Bancária (opcional)</Label>
                  <Select
                    value={aceitarForm.conta_bancaria_id || "__none__"}
                    onValueChange={(v) =>
                      setAceitarForm({
                        ...aceitarForm,
                        conta_bancaria_id: v === "__none__" ? "" : v,
                      })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="—" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="__none__">— Nenhuma —</SelectItem>
                      {contasBancarias.map((c) => (
                        <SelectItem key={c.id} value={c.id}>
                          {c.nome || c.banco}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label className="text-xs">Forma de Pagamento (opcional)</Label>
                  <Select
                    value={aceitarForm.forma_pagamento || "__none__"}
                    onValueChange={(v) =>
                      setAceitarForm({
                        ...aceitarForm,
                        forma_pagamento: v === "__none__" ? "" : v,
                      })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="—" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="__none__">— Nenhuma —</SelectItem>
                      {formasPagamento.map((f) => (
                        <SelectItem key={f.id} value={f.nome}>
                          {f.nome}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div>
                <Label className="text-xs">Observação (opcional)</Label>
                <Textarea
                  rows={2}
                  value={aceitarForm.observacao}
                  onChange={(e) =>
                    setAceitarForm({ ...aceitarForm, observacao: e.target.value })
                  }
                />
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setAceitarSol(null)} disabled={aceitando}>
              Cancelar
            </Button>
            <Button
              onClick={confirmarAceitar}
              disabled={aceitando}
              className="bg-emerald-600 hover:bg-emerald-700"
              data-testid="btn-confirmar-aceitar"
            >
              {aceitando && <Loader2 size={14} className="animate-spin mr-2" />}
              Aceitar e Criar Contas
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Modal Rejeitar */}
      <Dialog open={!!rejeitarSol} onOpenChange={(o) => !rejeitando && !o && setRejeitarSol(null)}>
        <DialogContent className="max-w-md" data-testid="dialog-rejeitar">
          <DialogHeader>
            <DialogTitle>Rejeitar solicitação</DialogTitle>
            <DialogDescription>
              O RH receberá o motivo e poderá corrigir e reenviar.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-2">
            <Label className="text-xs">Motivo</Label>
            <Textarea
              rows={3}
              value={motivoRejeicao}
              onChange={(e) => setMotivoRejeicao(e.target.value)}
              placeholder="Ex.: Valor divergente, falta plano de contas, etc."
              data-testid="input-motivo-rejeicao"
            />
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setRejeitarSol(null)}
              disabled={rejeitando}
            >
              Cancelar
            </Button>
            <Button
              onClick={confirmarRejeitar}
              disabled={rejeitando}
              className="bg-red-600 hover:bg-red-700"
              data-testid="btn-confirmar-rejeitar"
            >
              {rejeitando && <Loader2 size={14} className="animate-spin mr-2" />}
              Rejeitar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
