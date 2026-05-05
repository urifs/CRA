import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent } from "@/components/ui/card";
import {
  ArrowLeft,
  Upload,
  FileText,
  Loader2,
  Trash2,
  Download,
  BookOpen,
  Sparkles,
} from "lucide-react";

const API = process.env.REACT_APP_BACKEND_URL;

const SUGGESTIONS = [
  { name: "PCMSO", title: "PCMSO - Programa de Controle Médico de Saúde Ocupacional" },
  { name: "PGR", title: "PGR - Programa de Gerenciamento de Riscos" },
  { name: "LTCAT", title: "LTCAT - Laudo Técnico de Condições Ambientais do Trabalho" },
  { name: "CCT", title: "CCT - Convenção Coletiva de Trabalho" },
];

export default function ChatKnowledgeBasePage() {
  const navigate = useNavigate();
  const token = localStorage.getItem("token");
  const headers = { Authorization: `Bearer ${token}` };

  const [docs, setDocs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [name, setName] = useState("");
  const [title, setTitle] = useState("");
  const [file, setFile] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const r = await axios.get(`${API}/api/chatbot/knowledge-base`, { headers });
      setDocs(r.data || []);
    } catch (e) {
      toast.error("Falha ao carregar base de conhecimento");
    } finally {
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file || !name.trim() || !title.trim()) {
      toast.error("Preencha nome curto, título e selecione um PDF");
      return;
    }
    setUploading(true);
    try {
      const fd = new FormData();
      fd.append("name", name.trim());
      fd.append("title", title.trim());
      fd.append("file", file);
      const r = await axios.post(`${API}/api/chatbot/knowledge-base/upload`, fd, {
        headers: { ...headers, "Content-Type": "multipart/form-data" },
        timeout: 180000,
      });
      toast.success(
        `${r.data.name} carregado: ${r.data.pages || 0} páginas, ${
          r.data.extracted_chars || 0
        } caracteres extraídos.`,
      );
      setName("");
      setTitle("");
      setFile(null);
      const fi = document.getElementById("kb-file-input");
      if (fi) fi.value = "";
      load();
    } catch (e) {
      const detail = e.response?.data?.detail || e.message;
      toast.error(`Erro no upload: ${detail}`);
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (id, docName) => {
    if (!window.confirm(`Remover "${docName}" da base de conhecimento da IA?`)) return;
    try {
      await axios.delete(`${API}/api/chatbot/knowledge-base/${id}`, { headers });
      toast.success(`${docName} removido`);
      load();
    } catch (e) {
      toast.error("Falha ao remover");
    }
  };

  const handleDownload = async (id, docName) => {
    try {
      const r = await axios.get(`${API}/api/chatbot/knowledge-base/${id}/download`, {
        headers,
        responseType: "blob",
      });
      const url = window.URL.createObjectURL(new Blob([r.data], { type: "application/pdf" }));
      const a = document.createElement("a");
      a.href = url;
      a.download = `${docName}.pdf`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (e) {
      toast.error("Falha ao baixar PDF");
    }
  };

  const aplicarSugestao = (s) => {
    setName(s.name);
    setTitle(s.title);
  };

  const fmtSize = (b) => {
    if (!b) return "-";
    if (b < 1024) return `${b} B`;
    if (b < 1024 * 1024) return `${(b / 1024).toFixed(1)} KB`;
    return `${(b / (1024 * 1024)).toFixed(2)} MB`;
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-5xl mx-auto">
        <div className="flex items-center gap-3 mb-6">
          <Button
            variant="ghost"
            onClick={() => navigate(-1)}
            data-testid="kb-back-btn"
          >
            <ArrowLeft size={18} />
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
              <BookOpen size={22} className="text-emerald-600" />
              Base de Conhecimento do Chat IA
            </h1>
            <p className="text-sm text-gray-500 mt-1">
              Documentos normativos (PCMSO, PGR, LTCAT, CCT) que a IA do RH consulta para
              responder sobre exames, EPIs, riscos e jornadas. Atualize aqui sempre que
              houver nova versão.
            </p>
          </div>
        </div>

        {/* Upload form */}
        <Card className="mb-6 border-emerald-200">
          <CardContent className="p-6">
            <h2 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <Upload size={18} className="text-emerald-600" />
              Enviar / Substituir documento
            </h2>

            <div className="flex flex-wrap gap-2 mb-4">
              <span className="text-xs text-gray-500 self-center">Sugestões rápidas:</span>
              {SUGGESTIONS.map((s) => (
                <button
                  key={s.name}
                  type="button"
                  onClick={() => aplicarSugestao(s)}
                  className="px-3 py-1 bg-emerald-50 hover:bg-emerald-100 border border-emerald-200 text-emerald-700 rounded-full text-xs"
                  data-testid={`kb-suggestion-${s.name}`}
                >
                  <Sparkles size={12} className="inline mr-1" />
                  {s.name}
                </button>
              ))}
            </div>

            <form onSubmit={handleUpload} className="grid gap-4 md:grid-cols-2">
              <div className="md:col-span-1">
                <Label htmlFor="kb-name">Nome curto (ex: PCMSO, PGR)</Label>
                <Input
                  id="kb-name"
                  value={name}
                  onChange={(e) => setName(e.target.value.toUpperCase())}
                  placeholder="PCMSO"
                  maxLength={32}
                  required
                  data-testid="kb-name-input"
                />
              </div>
              <div className="md:col-span-1">
                <Label htmlFor="kb-title">Título descritivo</Label>
                <Input
                  id="kb-title"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="PCMSO - Programa de Controle Médico..."
                  required
                  data-testid="kb-title-input"
                />
              </div>
              <div className="md:col-span-2">
                <Label htmlFor="kb-file-input">Arquivo PDF</Label>
                <Input
                  id="kb-file-input"
                  type="file"
                  accept="application/pdf"
                  onChange={(e) => setFile(e.target.files?.[0] || null)}
                  required
                  data-testid="kb-file-input"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Se o PDF for escaneado, o sistema usa OCR via Gemini automaticamente
                  (pode levar até 2 minutos).
                </p>
              </div>
              <div className="md:col-span-2">
                <Button
                  type="submit"
                  disabled={uploading}
                  className="bg-emerald-600 hover:bg-emerald-700 text-white"
                  data-testid="kb-upload-submit"
                >
                  {uploading ? (
                    <>
                      <Loader2 className="animate-spin mr-2" size={16} />
                      Enviando e extraindo texto...
                    </>
                  ) : (
                    <>
                      <Upload size={16} className="mr-2" />
                      Enviar PDF
                    </>
                  )}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>

        {/* Lista de documentos */}
        <Card>
          <CardContent className="p-6">
            <h2 className="font-semibold text-gray-900 mb-4">
              Documentos atualmente disponíveis ({docs.length})
            </h2>
            {loading ? (
              <div className="text-center py-8">
                <Loader2 className="animate-spin inline" size={20} />
              </div>
            ) : docs.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                <FileText size={32} className="mx-auto mb-2 opacity-50" />
                <p className="text-sm">
                  Nenhum documento ainda. Use o formulário acima para enviar PCMSO, PGR,
                  LTCAT ou CCT.
                </p>
              </div>
            ) : (
              <div className="grid gap-3">
                {docs.map((d) => (
                  <div
                    key={d.id}
                    className="flex items-start gap-3 p-4 bg-white border border-gray-200 rounded-lg hover:border-emerald-300 transition-colors"
                    data-testid={`kb-doc-${d.name}`}
                  >
                    <div className="w-10 h-10 rounded bg-emerald-100 flex items-center justify-center flex-shrink-0">
                      <FileText size={18} className="text-emerald-700" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <strong className="text-gray-900">{d.name}</strong>
                        <span className="text-xs text-gray-500">
                          • {d.pages || 0} páginas • {fmtSize(d.pdf_size)}
                        </span>
                      </div>
                      <p className="text-sm text-gray-700 mt-0.5">{d.title}</p>
                      <p className="text-xs text-gray-400 mt-1">
                        Atualizado em {(d.created_at || "").slice(0, 10)}
                      </p>
                    </div>
                    <div className="flex gap-1 flex-shrink-0">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDownload(d.id, d.name)}
                        data-testid={`kb-download-${d.name}`}
                      >
                        <Download size={14} />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDelete(d.id, d.name)}
                        className="text-red-600 hover:text-red-700 hover:bg-red-50"
                        data-testid={`kb-delete-${d.name}`}
                      >
                        <Trash2 size={14} />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
