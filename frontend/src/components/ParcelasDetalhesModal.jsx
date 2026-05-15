import { useState, useEffect } from "react";
import axios from "axios";
import { API, useAuth } from "@/App";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Loader2, CheckCircle2, Clock, AlertCircle, CircleDot } from "lucide-react";
import { formatDateBR } from "@/utils/dateFormat";

const formatCurrency = (value) =>
  new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(value || 0);

const statusMap = {
  quitada: { label: "Quitada", color: "bg-green-100 text-green-700", Icon: CheckCircle2 },
  parcial: { label: "Parcial", color: "bg-amber-100 text-amber-700", Icon: CircleDot },
  em_aberto: { label: "Em Aberto", color: "bg-blue-100 text-blue-700", Icon: Clock },
  pendente: { label: "Pendente", color: "bg-blue-100 text-blue-700", Icon: Clock },
  cancelada: { label: "Cancelada", color: "bg-gray-200 text-gray-700", Icon: AlertCircle },
};

/**
 * Modal de Detalhes do Parcelamento.
 *
 * Props:
 *  - open: bool
 *  - onOpenChange: fn
 *  - parcelaOrigemId: string
 *  - tipo: "pagar" | "receber"
 *  - onSelectParcela?: fn(conta) - opcional, clique em uma linha
 */
export default function ParcelasDetalhesModal({
  open,
  onOpenChange,
  parcelaOrigemId,
  tipo = "pagar",
  onSelectParcela,
}) {
  const { token } = useAuth();
  const [loading, setLoading] = useState(false);
  const [grupo, setGrupo] = useState(null);

  useEffect(() => {
    if (!open || !parcelaOrigemId) return;
    const fetchGrupo = async () => {
      setLoading(true);
      try {
        const endpoint = tipo === "receber"
          ? `${API}/admin/contas-receber/grupo/${parcelaOrigemId}`
          : `${API}/admin/contas-pagar/grupo/${parcelaOrigemId}`;
        const { data } = await axios.get(endpoint, {
          headers: { Authorization: `Bearer ${token}` },
        });
        setGrupo(data);
      } catch (e) {
        console.error("Falha ao carregar grupo de parcelas", e);
        setGrupo(null);
      } finally {
        setLoading(false);
      }
    };
    fetchGrupo();
  }, [open, parcelaOrigemId, tipo, token]);

  const tituloSaldo = tipo === "receber" ? "Saldo Restante a Receber" : "Saldo Restante a Pagar";
  const tituloPago = tipo === "receber" ? "Total Recebido" : "Total Pago";
  const corValor = tipo === "receber" ? "text-emerald-700" : "text-red-600";

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        className="max-w-4xl max-h-[90vh] overflow-y-auto"
        data-testid="modal-parcelas-detalhes"
      >
        <DialogHeader>
          <DialogTitle>Detalhes do Parcelamento</DialogTitle>
        </DialogHeader>

        {loading ? (
          <div className="py-16 flex justify-center items-center text-gray-500">
            <Loader2 className="animate-spin mr-2" /> Carregando parcelas...
          </div>
        ) : !grupo ? (
          <div className="py-12 text-center text-gray-400">
            Não foi possível carregar as parcelas deste grupo.
          </div>
        ) : (
          <div className="space-y-4">
            {/* Resumo */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <div className="border rounded-lg p-3 bg-gray-50">
                <p className="text-xs text-gray-500">Total Geral</p>
                <p className={`text-lg font-bold ${corValor}`} data-testid="resumo-total-geral">
                  {formatCurrency(grupo.resumo?.total_geral)}
                </p>
              </div>
              <div className="border rounded-lg p-3 bg-green-50">
                <p className="text-xs text-gray-500">{tituloPago}</p>
                <p className="text-lg font-bold text-green-700" data-testid="resumo-total-pago">
                  {formatCurrency(grupo.resumo?.total_pago)}
                </p>
              </div>
              <div className="border rounded-lg p-3 bg-amber-50">
                <p className="text-xs text-gray-500">{tituloSaldo}</p>
                <p className="text-lg font-bold text-amber-700" data-testid="resumo-saldo-restante">
                  {formatCurrency(grupo.resumo?.saldo_restante)}
                </p>
              </div>
              <div className="border rounded-lg p-3 bg-blue-50">
                <p className="text-xs text-gray-500">Parcelas</p>
                <p className="text-lg font-bold text-blue-700" data-testid="resumo-parcelas">
                  {grupo.resumo?.qtd_quitadas}/{grupo.resumo?.qtd_parcelas}
                </p>
              </div>
            </div>

            {/* Tabela de parcelas */}
            <div className="overflow-x-auto border rounded-lg">
              <table className="w-full text-sm">
                <thead className="bg-gray-100">
                  <tr>
                    <th className="text-left p-2">Parcela</th>
                    <th className="text-left p-2">Vencimento</th>
                    <th className="text-right p-2">Valor</th>
                    <th className="text-right p-2">{tipo === "receber" ? "Recebido" : "Pago"}</th>
                    <th className="text-right p-2">Saldo</th>
                    <th className="text-left p-2">Status</th>
                    <th className="text-left p-2">
                      {tipo === "receber" ? "Recebido em" : "Pago em"}
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {grupo.parcelas.map((p) => {
                    const st = statusMap[p.status] || statusMap.em_aberto;
                    const StIcon = st.Icon;
                    const valorFinal = p.valor_final || p.valor || 0;
                    const pago = (p.status === "quitada" && (p.valor_pago || 0) < valorFinal)
                      ? valorFinal
                      : (p.valor_pago || 0);
                    const saldo = Math.max(0, valorFinal - pago);
                    return (
                      <tr
                        key={p.id}
                        className={`border-t hover:bg-gray-50 transition-colors ${
                          onSelectParcela ? "cursor-pointer" : ""
                        }`}
                        onClick={() => onSelectParcela && onSelectParcela(p)}
                        data-testid={`parcela-row-${p.numero_parcela}`}
                      >
                        <td className="p-2 font-mono">
                          {p.numero_parcela}/{p.total_parcelas}
                        </td>
                        <td className="p-2">{formatDateBR(p.data_vencimento)}</td>
                        <td className="p-2 text-right font-medium">{formatCurrency(valorFinal)}</td>
                        <td className="p-2 text-right text-green-700">{formatCurrency(pago)}</td>
                        <td className="p-2 text-right text-amber-700 font-medium">
                          {formatCurrency(saldo)}
                        </td>
                        <td className="p-2">
                          <span className={`px-2 py-1 rounded text-xs inline-flex items-center gap-1 ${st.color}`}>
                            <StIcon size={12} /> {st.label}
                          </span>
                        </td>
                        <td className="p-2 text-gray-600">
                          {p.data_pagamento ? formatDateBR(p.data_pagamento)
                            : (p.data_ultimo_pagamento ? formatDateBR(p.data_ultimo_pagamento)
                              : <span className="text-gray-300">—</span>)}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            <p className="text-xs text-gray-500">
              Clique em uma parcela para abrir seus detalhes.
            </p>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
