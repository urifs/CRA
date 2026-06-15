import { useState } from "react";
import axios from "axios";
import { API } from "@/App";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { toast } from "sonner";
import { Wrench, Loader2, AlertTriangle, CheckCircle2, RefreshCw } from "lucide-react";

const fmtBRL = (v) =>
  new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(v || 0);

export default function ValoresCorrigirCard() {
  const [loading, setLoading] = useState(false);
  const [applying, setApplying] = useState(false);
  const [scanned, setScanned] = useState(false);
  const [data, setData] = useState({ corrigiveis: [], manuais: [], total_corrigiveis: 0, total_manuais: 0 });

  const token = typeof localStorage !== "undefined" ? localStorage.getItem("token") : null;
  const authHeaders = { headers: { Authorization: `Bearer ${token}` } };

  const verificar = async () => {
    setLoading(true);
    try {
      const { data: res } = await axios.get(`${API}/admin/valores-corrompidos`, authHeaders);
      setData(res);
      setScanned(true);
      if (res.total_corrigiveis === 0 && res.total_manuais === 0) {
        toast.success("Nenhum valor incorreto encontrado! Tudo certo.");
      } else {
        toast.info(`${res.total_corrigiveis} corrigível(is) · ${res.total_manuais} para revisão manual`);
      }
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Erro ao verificar valores");
    } finally {
      setLoading(false);
    }
  };

  const aplicar = async () => {
    if (!window.confirm(
      `Aplicar correção em ${data.total_corrigiveis} registro(s)?\n\n` +
      "Os valores serão reconstruídos para o valor original (ex: R$ 1.138.130.000.000,00 → R$ 1.138,13). " +
      "Esta ação é registrada na auditoria."
    )) return;
    setApplying(true);
    try {
      const { data: res } = await axios.post(`${API}/admin/valores-corrompidos/corrigir`, {}, authHeaders);
      toast.success(`${res.total_corrigidos} registro(s) corrigido(s) com sucesso!`);
      await verificar();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Erro ao aplicar correções");
    } finally {
      setApplying(false);
    }
  };

  return (
    <Card className="mb-4 border-gray-800 bg-gray-900/60" data-testid="valores-corrigir-card">
      <CardContent className="py-4">
        <div className="flex items-start justify-between gap-3 flex-wrap">
          <div className="flex items-start gap-3">
            <div className="w-10 h-10 rounded-lg bg-amber-500/10 flex items-center justify-center shrink-0">
              <Wrench size={20} className="text-amber-500" />
            </div>
            <div>
              <h4 className="text-white font-semibold">Correção de Valores Incorretos</h4>
              <p className="text-sm text-gray-400 max-w-xl">
                Detecta e corrige contas com valores absurdos gerados por um bug antigo de
                arredondamento (ex: R$ 1.138.130.000.000,00). Só corrige automaticamente quando
                é seguro reconstruir o valor original.
              </p>
            </div>
          </div>
          <div className="flex gap-2 shrink-0">
            <Button
              variant="outline"
              onClick={verificar}
              disabled={loading || applying}
              data-testid="verificar-valores-btn"
            >
              {loading ? <Loader2 size={16} className="mr-2 animate-spin" /> : <RefreshCw size={16} className="mr-2" />}
              Verificar
            </Button>
            {data.total_corrigiveis > 0 && (
              <Button
                onClick={aplicar}
                disabled={applying || loading}
                className="bg-amber-600 hover:bg-amber-700 text-white"
                data-testid="aplicar-correcao-btn"
              >
                {applying ? <Loader2 size={16} className="mr-2 animate-spin" /> : <CheckCircle2 size={16} className="mr-2" />}
                Aplicar correção ({data.total_corrigiveis})
              </Button>
            )}
          </div>
        </div>

        {scanned && (
          <div className="mt-4 space-y-4">
            {/* Corrigíveis */}
            {data.corrigiveis.length > 0 && (
              <div data-testid="lista-corrigiveis">
                <p className="text-sm font-semibold text-emerald-400 mb-2 flex items-center gap-1">
                  <CheckCircle2 size={14} /> {data.corrigiveis.length} corrigível(is) automaticamente
                </p>
                <div className="overflow-x-auto rounded-lg border border-gray-800">
                  <table className="w-full text-sm">
                    <thead className="bg-gray-800/60 text-gray-400">
                      <tr>
                        <th className="text-left p-2">Nº</th>
                        <th className="text-left p-2">Descrição</th>
                        <th className="text-left p-2">Origem</th>
                        <th className="text-right p-2">Valor atual</th>
                        <th className="text-right p-2">Valor corrigido</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.corrigiveis.map((it) => (
                        <tr key={`${it.collection}-${it.id}`} className="border-t border-gray-800 text-gray-200">
                          <td className="p-2 font-mono">{it.numero}</td>
                          <td className="p-2 max-w-[220px] truncate" title={it.descricao}>{it.descricao}</td>
                          <td className="p-2 text-gray-400 max-w-[160px] truncate">{it.nome || "-"}</td>
                          <td className="p-2 text-right text-red-400">{fmtBRL(it.valor_atual)}</td>
                          <td className="p-2 text-right text-emerald-400 font-semibold">{fmtBRL(it.valor_final_sugerido)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Manuais */}
            {data.manuais.length > 0 && (
              <div data-testid="lista-manuais">
                <p className="text-sm font-semibold text-amber-400 mb-2 flex items-center gap-1">
                  <AlertTriangle size={14} /> {data.manuais.length} precisam de revisão manual
                </p>
                <p className="text-xs text-gray-500 mb-2">
                  Estes não puderam ser reconstruídos com 100% de segurança. Edite-os manualmente
                  digitando o valor correto (após este conserto, salvar não corrompe mais).
                </p>
                <div className="overflow-x-auto rounded-lg border border-gray-800">
                  <table className="w-full text-sm">
                    <thead className="bg-gray-800/60 text-gray-400">
                      <tr>
                        <th className="text-left p-2">Nº</th>
                        <th className="text-left p-2">Descrição</th>
                        <th className="text-right p-2">Valor atual</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.manuais.map((it) => (
                        <tr key={`${it.collection}-${it.id}`} className="border-t border-gray-800 text-gray-200">
                          <td className="p-2 font-mono">{it.numero}</td>
                          <td className="p-2 max-w-[260px] truncate" title={it.descricao}>{it.descricao}</td>
                          <td className="p-2 text-right text-red-400">{fmtBRL(it.valor_atual)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {data.corrigiveis.length === 0 && data.manuais.length === 0 && (
              <p className="text-sm text-emerald-400 flex items-center gap-1">
                <CheckCircle2 size={14} /> Nenhum valor incorreto encontrado.
              </p>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
