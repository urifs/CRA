import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "@/App";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Clock,
  Plus,
  Edit,
  Trash2,
  Users,
  ShieldCheck,
  X,
  Save,
} from "lucide-react";
import { toast } from "sonner";

const DIAS_SEMANA = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"];

function fmtMin(min) {
  if (!min || min === 0) return "0h";
  const h = Math.floor(min / 60);
  const m = min % 60;
  return m > 0 ? `${h}h ${m}min` : `${h}h`;
}

const DIAS_VAZIOS = Object.fromEntries(
  Array.from({ length: 7 }, (_, i) => [
    String(i),
    {
      ativo: i <= 4,
      entrada: i <= 4 ? "08:00" : "",
      saida_almoco: i <= 4 ? "12:00" : "",
      retorno_almoco: i <= 4 ? "13:00" : "",
      saida: i <= 4 ? "17:00" : "",
    },
  ])
);

export default function JornadasQuadro() {
  const [jornadas, setJornadas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(null); // null | 'new' | jornada_obj
  const [form, setForm] = useState({ nome: "", descricao: "", dias: DIAS_VAZIOS });
  const [atribuirJornada, setAtribuirJornada] = useState(null);

  const fetchJornadas = async () => {
    try {
      const { data } = await axios.get(`${API}/rh/jornadas`);
      setJornadas(data);
    } catch (e) {
      toast.error("Erro ao carregar jornadas");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJornadas();
  }, []);

  const abrirNova = () => {
    setForm({ nome: "", descricao: "", dias: JSON.parse(JSON.stringify(DIAS_VAZIOS)) });
    setEditing("new");
  };

  const abrirEdicao = (j) => {
    setForm({
      nome: j.nome,
      descricao: j.descricao || "",
      dias: { ...DIAS_VAZIOS, ...(j.dias || {}) },
    });
    setEditing(j);
  };

  const salvar = async () => {
    if (!form.nome.trim()) {
      toast.error("Nome é obrigatório");
      return;
    }
    try {
      if (editing === "new") {
        await axios.post(`${API}/rh/jornadas`, form);
        toast.success("Jornada criada");
      } else {
        await axios.put(`${API}/rh/jornadas/${editing.id}`, form);
        toast.success("Jornada atualizada");
      }
      setEditing(null);
      await fetchJornadas();
    } catch (e) {
      toast.error(e.response?.data?.detail || "Erro ao salvar");
    }
  };

  const excluir = async (j) => {
    if (!window.confirm(`Excluir a jornada "${j.nome}"?`)) return;
    try {
      await axios.delete(`${API}/rh/jornadas/${j.id}`);
      toast.success("Jornada excluída");
      await fetchJornadas();
    } catch (e) {
      toast.error(e.response?.data?.detail || "Erro ao excluir");
    }
  };

  const atualizarDia = (dia, campo, valor) => {
    setForm({
      ...form,
      dias: {
        ...form.dias,
        [dia]: { ...(form.dias[dia] || {}), [campo]: valor },
      },
    });
  };

  return (
    <Card className="mb-6">
      <CardContent className="p-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-semibold flex items-center gap-2">
            <Clock size={18} className="text-[#10B981]" />
            Jornadas de Trabalho
          </h3>
          <Button
            size="sm"
            onClick={abrirNova}
            className="bg-[#10B981] hover:bg-[#059669]"
            data-testid="btn-nova-jornada"
          >
            <Plus size={14} className="mr-1" />
            Nova jornada
          </Button>
        </div>

        {loading ? (
          <div className="text-center py-6 text-gray-400 text-sm">Carregando...</div>
        ) : jornadas.length === 0 ? (
          <div className="text-center py-6 text-gray-400 text-sm">
            Nenhuma jornada cadastrada. Crie a primeira clicando em "Nova jornada".
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
            {jornadas.map((j) => {
              const totalH = Math.floor((j.total_semanal_minutos || 0) / 60);
              const totalM = (j.total_semanal_minutos || 0) % 60;
              return (
                <div
                  key={j.id}
                  className="border rounded-lg p-3 bg-white hover:shadow-md transition"
                  data-testid={`card-jornada-${j.id}`}
                >
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <div className="flex items-center gap-1">
                        <h4 className="font-bold text-gray-800">{j.nome}</h4>
                        {j.is_padrao && (
                          <span className="text-[10px] bg-emerald-100 text-emerald-700 px-1.5 py-0.5 rounded font-semibold">
                            PADRÃO
                          </span>
                        )}
                      </div>
                      {j.descricao && (
                        <p className="text-xs text-gray-500">{j.descricao}</p>
                      )}
                    </div>
                    <div className="flex gap-1">
                      <Button
                        size="sm"
                        variant="ghost"
                        className="h-7 w-7 p-0"
                        onClick={() => abrirEdicao(j)}
                        data-testid={`btn-editar-jornada-${j.id}`}
                      >
                        <Edit size={12} />
                      </Button>
                      {!j.is_padrao && (
                        <Button
                          size="sm"
                          variant="ghost"
                          className="h-7 w-7 p-0 text-rose-600"
                          onClick={() => excluir(j)}
                          data-testid={`btn-excluir-jornada-${j.id}`}
                        >
                          <Trash2 size={12} />
                        </Button>
                      )}
                    </div>
                  </div>

                  {/* Resumo dos dias */}
                  <div className="space-y-1 mb-3">
                    {DIAS_SEMANA.map((nome, i) => {
                      const cfg = (j.dias || {})[String(i)] || {};
                      if (!cfg.ativo) return null;
                      const semAlmoco = !cfg.saida_almoco || !cfg.retorno_almoco;
                      return (
                        <div
                          key={i}
                          className="flex items-center justify-between text-xs bg-gray-50 rounded px-2 py-1"
                        >
                          <span className="font-medium text-gray-700 w-16">{nome.slice(0, 3)}</span>
                          <span className="font-mono text-gray-600">
                            {cfg.entrada}
                            {!semAlmoco && (
                              <>
                                {" - "}
                                <span className="text-orange-600">{cfg.saida_almoco}</span>
                                {" / "}
                                <span className="text-blue-600">{cfg.retorno_almoco}</span>
                              </>
                            )}
                            {" - "}
                            {cfg.saida}
                          </span>
                        </div>
                      );
                    })}
                  </div>

                  <div className="flex items-center justify-between border-t pt-2">
                    <div className="text-xs text-gray-500">
                      <strong className="text-gray-800">{totalH}h{totalM > 0 && ` ${totalM}min`}</strong> / semana
                    </div>
                    <Button
                      size="sm"
                      variant="outline"
                      className="h-7 text-xs"
                      onClick={() => setAtribuirJornada(j)}
                      data-testid={`btn-atribuir-jornada-${j.id}`}
                    >
                      <Users size={12} className="mr-1" />
                      {j.funcionarios_count || 0} func.
                    </Button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </CardContent>

      {/* Dialog de criar/editar jornada */}
      <Dialog open={!!editing} onOpenChange={(o) => !o && setEditing(null)}>
        <DialogContent className="max-w-3xl max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {editing === "new" ? "Nova Jornada" : `Editar: ${editing?.nome}`}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div>
                <Label>Nome*</Label>
                <Input
                  placeholder="Ex: Comercial 8h, Diarista 6h, 12x36..."
                  value={form.nome}
                  onChange={(e) => setForm({ ...form, nome: e.target.value })}
                  disabled={editing?.is_padrao}
                  data-testid="input-jornada-nome"
                />
              </div>
              <div>
                <Label>Descrição</Label>
                <Input
                  placeholder="Opcional"
                  value={form.descricao}
                  onChange={(e) => setForm({ ...form, descricao: e.target.value })}
                  data-testid="input-jornada-descricao"
                />
              </div>
            </div>

            <div className="border rounded-lg overflow-hidden">
              <table className="w-full text-sm">
                <thead className="bg-gray-100">
                  <tr>
                    <th className="text-left p-2 w-24">Dia</th>
                    <th className="text-center p-2 w-20">Ativo</th>
                    <th className="text-center p-2">Entrada</th>
                    <th className="text-center p-2">Saída almoço</th>
                    <th className="text-center p-2">Retorno almoço</th>
                    <th className="text-center p-2">Saída</th>
                    <th className="text-right p-2 w-20">Total</th>
                  </tr>
                </thead>
                <tbody>
                  {DIAS_SEMANA.map((nome, i) => {
                    const cfg = form.dias[String(i)] || {};
                    const ativo = cfg.ativo;
                    // Calc preview
                    const toMin = (s) => {
                      if (!s) return 0;
                      const [h, m] = s.split(":").map(Number);
                      return (h || 0) * 60 + (m || 0);
                    };
                    let mins = 0;
                    if (ativo) {
                      const e = toMin(cfg.entrada);
                      const s = toMin(cfg.saida);
                      const sa = toMin(cfg.saida_almoco);
                      const ra = toMin(cfg.retorno_almoco);
                      if (e > 0 && s > e) {
                        if (sa > 0 && ra > 0 && sa < ra) mins = (sa - e) + (s - ra);
                        else mins = s - e;
                      }
                    }
                    return (
                      <tr key={i} className={ativo ? "" : "bg-gray-50 text-gray-400"}>
                        <td className="p-2 font-medium">{nome}</td>
                        <td className="p-2 text-center">
                          <input
                            type="checkbox"
                            checked={!!ativo}
                            onChange={(e) => atualizarDia(String(i), "ativo", e.target.checked)}
                            data-testid={`check-dia-${i}`}
                          />
                        </td>
                        <td className="p-2">
                          <Input
                            type="time"
                            value={cfg.entrada || ""}
                            onChange={(e) => atualizarDia(String(i), "entrada", e.target.value)}
                            disabled={!ativo}
                            className="h-8"
                          />
                        </td>
                        <td className="p-2">
                          <Input
                            type="time"
                            value={cfg.saida_almoco || ""}
                            onChange={(e) => atualizarDia(String(i), "saida_almoco", e.target.value)}
                            disabled={!ativo}
                            className="h-8"
                          />
                        </td>
                        <td className="p-2">
                          <Input
                            type="time"
                            value={cfg.retorno_almoco || ""}
                            onChange={(e) => atualizarDia(String(i), "retorno_almoco", e.target.value)}
                            disabled={!ativo}
                            className="h-8"
                          />
                        </td>
                        <td className="p-2">
                          <Input
                            type="time"
                            value={cfg.saida || ""}
                            onChange={(e) => atualizarDia(String(i), "saida", e.target.value)}
                            disabled={!ativo}
                            className="h-8"
                          />
                        </td>
                        <td className="p-2 text-right font-mono text-xs">{fmtMin(mins)}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            <p className="text-xs text-gray-500">
              💡 Para jornadas sem horário de almoço (ex: meio-período), deixe os campos
              "Saída almoço" e "Retorno almoço" vazios.
            </p>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditing(null)}>
              Cancelar
            </Button>
            <Button onClick={salvar} className="bg-[#10B981] hover:bg-[#059669]" data-testid="btn-salvar-jornada">
              <Save size={14} className="mr-1" />
              Salvar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Dialog de atribuição de funcionários */}
      <DialogAtribuirFuncionarios
        jornada={atribuirJornada}
        onClose={() => setAtribuirJornada(null)}
        onSaved={fetchJornadas}
      />
    </Card>
  );
}

function DialogAtribuirFuncionarios({ jornada, onClose, onSaved }) {
  const [funcionarios, setFuncionarios] = useState([]);
  const [selecionados, setSelecionados] = useState(new Set());
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!jornada) return;
    (async () => {
      setLoading(true);
      try {
        const [resAll, resAtuais] = await Promise.all([
          axios.get(`${API}/rh/funcionarios?status=ativo`),
          axios.get(`${API}/rh/jornadas/${jornada.id}/funcionarios`),
        ]);
        setFuncionarios(resAll.data || []);
        setSelecionados(new Set((resAtuais.data || []).map((f) => f.id)));
      } catch (e) {
        toast.error("Erro ao carregar funcionários");
      } finally {
        setLoading(false);
      }
    })();
  }, [jornada]);

  const toggle = (fid) => {
    const novo = new Set(selecionados);
    if (novo.has(fid)) novo.delete(fid);
    else novo.add(fid);
    setSelecionados(novo);
  };

  const salvar = async () => {
    try {
      await axios.post(`${API}/rh/jornadas/${jornada.id}/atribuir`, {
        funcionario_ids: Array.from(selecionados),
      });
      toast.success("Atribuição salva");
      onSaved();
      onClose();
    } catch (e) {
      toast.error(e.response?.data?.detail || "Erro ao atribuir");
    }
  };

  return (
    <Dialog open={!!jornada} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Atribuir funcionários — {jornada?.nome}</DialogTitle>
        </DialogHeader>
        <div className="space-y-2">
          {loading ? (
            <p className="text-center py-6 text-gray-400">Carregando...</p>
          ) : funcionarios.length === 0 ? (
            <p className="text-center py-6 text-gray-400">
              Nenhum funcionário ativo cadastrado.
            </p>
          ) : (
            <>
              <p className="text-sm text-gray-500 mb-2">
                Marque os funcionários que devem usar esta jornada. Marcar aqui sobrepõe
                qualquer jornada anterior do funcionário.
              </p>
              <div className="border rounded-lg divide-y max-h-96 overflow-y-auto">
                {funcionarios.map((f) => (
                  <label
                    key={f.id}
                    className="flex items-center gap-3 p-2 hover:bg-gray-50 cursor-pointer"
                  >
                    <input
                      type="checkbox"
                      checked={selecionados.has(f.id)}
                      onChange={() => toggle(f.id)}
                      data-testid={`check-func-${f.id}`}
                    />
                    <div className="flex-1">
                      <p className="font-medium text-sm">{f.nome}</p>
                      <p className="text-xs text-gray-500">
                        {f.cargo} {f.departamento && `• ${f.departamento}`}
                      </p>
                    </div>
                  </label>
                ))}
              </div>
              <p className="text-xs text-gray-500 mt-2">
                {selecionados.size} de {funcionarios.length} selecionado(s)
              </p>
            </>
          )}
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Cancelar
          </Button>
          <Button
            onClick={salvar}
            className="bg-[#10B981] hover:bg-[#059669]"
            disabled={loading}
            data-testid="btn-salvar-atribuicao"
          >
            <Save size={14} className="mr-1" />
            Salvar atribuição
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
