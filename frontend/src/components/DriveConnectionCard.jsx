import { useEffect, useState, useCallback } from "react";
import axios from "axios";
import { useSearchParams } from "react-router-dom";
import { API } from "@/App";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { toast } from "sonner";
import { Cloud, CloudOff, Check, Loader2, ExternalLink } from "lucide-react";

const fmtDate = (iso) => {
  if (!iso) return "";
  try {
    return new Date(iso).toLocaleString("pt-BR");
  } catch {
    return iso;
  }
};

export default function DriveConnectionCard() {
  const [status, setStatus] = useState({ connected: false });
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [searchParams, setSearchParams] = useSearchParams();

  const token = typeof localStorage !== "undefined" ? localStorage.getItem("token") : null;
  const authHeaders = { headers: { Authorization: `Bearer ${token}` } };

  const fetchStatus = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await axios.get(`${API}/drive/status`, authHeaders);
      setStatus(data || { connected: false });
    } catch (e) {
      setStatus({ connected: false });
    } finally {
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  // Handle ?drive=connected / ?drive=error after OAuth redirect
  useEffect(() => {
    const driveFlag = searchParams.get("drive");
    if (driveFlag === "connected") {
      toast.success("Google Drive conectado com sucesso!");
      searchParams.delete("drive");
      setSearchParams(searchParams, { replace: true });
    } else if (driveFlag === "error") {
      const detail = searchParams.get("detail") || "Erro ao conectar";
      toast.error(`Falha na conexão com Drive: ${detail}`);
      searchParams.delete("drive");
      searchParams.delete("detail");
      setSearchParams(searchParams, { replace: true });
    }
    fetchStatus();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleConnect = async () => {
    setBusy(true);
    try {
      const { data } = await axios.get(`${API}/drive/connect`, authHeaders);
      if (data?.authorization_url) {
        window.location.href = data.authorization_url;
      }
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Erro ao iniciar conexão");
      setBusy(false);
    }
  };

  const handleDisconnect = async () => {
    if (!window.confirm("Desconectar Google Drive?\n\nNovos uploads voltarão a ser salvos no armazenamento local.")) return;
    setBusy(true);
    try {
      await axios.post(`${API}/drive/disconnect`, {}, authHeaders);
      toast.success("Google Drive desconectado.");
      await fetchStatus();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Erro ao desconectar");
    } finally {
      setBusy(false);
    }
  };

  const handleTest = async () => {
    setBusy(true);
    try {
      const { data } = await axios.get(`${API}/drive/test`, authHeaders);
      toast.success(`Conexão OK · ${data.items} item(ns) na pasta ${data.root_folder}`);
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Falha no teste de conexão");
    } finally {
      setBusy(false);
    }
  };

  if (loading) {
    return (
      <Card className="mb-4 border-gray-800 bg-gray-900/60">
        <CardContent className="flex items-center gap-3 py-4">
          <Loader2 className="w-4 h-4 animate-spin text-gray-400" />
          <span className="text-sm text-gray-400">Verificando conexão com Google Drive…</span>
        </CardContent>
      </Card>
    );
  }

  if (!status.connected) {
    return (
      <Card className="mb-4 border-amber-500/40 bg-amber-500/10" data-testid="drive-card-disconnected">
        <CardContent className="flex flex-col md:flex-row md:items-center gap-4 py-4">
          <div className="flex items-center gap-3 flex-1">
            <div className="p-2 rounded-full bg-amber-500/20">
              <CloudOff className="w-5 h-5 text-amber-400" />
            </div>
            <div>
              <p className="text-sm font-semibold text-amber-100">Google Drive não conectado</p>
              <p className="text-xs text-amber-200/80">
                Conecte uma conta Google para armazenar todos os arquivos no Drive. Sem conexão, os uploads continuam no armazenamento local.
              </p>
            </div>
          </div>
          <Button
            onClick={handleConnect}
            disabled={busy}
            className="bg-amber-600 hover:bg-amber-700 text-white"
            data-testid="btn-conectar-drive"
          >
            {busy ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Cloud className="w-4 h-4 mr-2" />}
            Conectar Google Drive
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="mb-4 border-emerald-500/40 bg-emerald-500/10" data-testid="drive-card-connected">
      <CardContent className="flex flex-col md:flex-row md:items-center gap-4 py-4">
        <div className="flex items-center gap-3 flex-1">
          <div className="p-2 rounded-full bg-emerald-500/20">
            <Check className="w-5 h-5 text-emerald-400" />
          </div>
          <div className="min-w-0">
            <p className="text-sm font-semibold text-emerald-100 flex items-center gap-2 flex-wrap">
              Google Drive conectado
              <span className="text-emerald-200/80 font-normal">— pasta raiz <code className="text-xs bg-white/10 px-1 py-0.5 rounded">CRA-ERP</code></span>
            </p>
            <p className="text-xs text-emerald-200/80 truncate">
              Conta: <strong className="text-emerald-100">{status.email || "—"}</strong>
              {status.connected_at && <> · desde {fmtDate(status.connected_at)}</>}
            </p>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleTest}
            disabled={busy}
            className="border-emerald-500/40 text-emerald-100 hover:bg-emerald-500/10"
            data-testid="btn-testar-drive"
          >
            {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <ExternalLink className="w-4 h-4" />}
            <span className="ml-1">Testar conexão</span>
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={handleDisconnect}
            disabled={busy}
            className="text-red-300 hover:text-red-200 hover:bg-red-500/10 border-red-500/40"
            data-testid="btn-desconectar-drive"
          >
            <CloudOff className="w-4 h-4 mr-1" />
            Desconectar
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
