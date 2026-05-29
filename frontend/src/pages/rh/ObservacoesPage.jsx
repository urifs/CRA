import { useState, useEffect, useRef } from "react";
import axios from "axios";
import { API } from "@/App";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
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
  DialogDescription,
} from "@/components/ui/dialog";
import {
  Plus, StickyNote, User, Bell, BellOff, Calendar, Edit, Trash2, Search,
} from "lucide-react";
import { toast } from "sonner";
import AnexosManager from "@/components/AnexosManager";

const EMPTY = {
  titulo: "",
  descricao: "",
  funcionario_id: "",
  lembrete_ativo: false,
  lembrete_data: "",
};

const formatDateBR = (val) => {
  if (!val) return "-";
  const s = String(val).slice(0, 10);
  if (s.length === 10 && s[4] === "-") return `${s.slice(8, 10)}/${s.slice(5, 7)}/${s.slice(0, 4)}`;
  return s;
};

const formatDateTimeBR = (val) => {
  if (!val) return "-";
  try {
    const d = new Date(val);
    return d.toLocaleString("pt-BR", { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" });
  } catch {
    return formatDateBR(val);
  }
};

export default function ObservacoesPage() {
  const [observacoes, setObservacoes] = useState([]);
  const [funcionarios, setFuncionarios] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [saving, setSaving] = useState(false);
  const [formData, setFormData] = useState(EMPTY);
  const anexosRef = useRef(null);

  useEffect(() => {
    fetchAll();
  }, []);

  const fetchAll = async () => {
    setLoading(true);
    try {
      const [obsRes, funcRes] = await Promise.all([
        axios.get(`${API}/rh/observacoes`),
        axios.get(`${API}/rh/funcionarios`),
      ]);
      setObservacoes(obsRes.data || []);
      setFuncionarios(funcRes.data || []);
    } catch (error) {
      toast.error("Erro ao carregar observações");
    } finally {
      setLoading(false);
    }
  };

  const openModal = (obs = null) => {
    if (obs) {
      setEditing(obs);
      setFormData({
        titulo: obs.titulo || "",
        descricao: obs.descricao || "",
        funcionario_id: obs.funcionario_id || "",
        lembrete_ativo: !!obs.lembrete_ativo,
        lembrete_data: obs.lembrete_data || "",
      });
    } else {
      setEditing(null);
      setFormData(EMPTY);
    }
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setEditing(null);
    setFormData(EMPTY);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.titulo.trim()) return toast.error("Informe o título");
    if (!formData.descricao.trim()) return toast.error("Escreva a observação");
    if (formData.lembrete_ativo && !formData.lembrete_data) return toast.error("Informe a data do lembrete");

    setSaving(true);
    try {
      const payload = {
        titulo: formData.titulo,
        descricao: formData.descricao,
        funcionario_id: formData.funcionario_id || "",
        lembrete_ativo: formData.lembrete_ativo,
        lembrete_data: formData.lembrete_ativo ? formData.lembrete_data : "",
      };
      if (editing) {
        await axios.put(`${API}/rh/observacoes/${editing.id}`, payload);
        await anexosRef.current?.flushPending(editing.id);
        toast.success("Observação atualizada!");
      } else {
        const resp = await axios.post(`${API}/rh/observacoes`, payload);
        await anexosRef.current?.flushPending(resp.data?.id);
        toast.success("Observação criada!");
      }
      closeModal();
      fetchAll();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao salvar observação");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Excluir esta observação?")) return;
    try {
      await axios.delete(`${API}/rh/observacoes/${id}`);
      toast.success("Observação excluída!");
      fetchAll();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao excluir");
    }
  };

  const filtered = observacoes.filter((o) => {
    const q = search.toLowerCase();
    return (
      o.titulo?.toLowerCase().includes(q) ||
      o.descricao?.toLowerCase().includes(q) ||
      o.funcionario_nome?.toLowerCase().includes(q)
    );
  });

  const comLembrete = observacoes.filter((o) => o.lembrete_ativo).length;

  if (loading) {
    return <div className="flex items-center justify-center min-h-[400px]"><div className="spinner w-12 h-12"></div></div>;
  }

  return (
    <div data-testid="rh-observacoes-page">
      <div className="page-header">
        <div>
          <h1 className="page-title flex items-center gap-2">
            <StickyNote className="text-[#10B981]" size={26} /> Observações
          </h1>
          <p className="text-gray-500 mt-1">Notas e anotações vinculadas aos funcionários</p>
        </div>
        <Button onClick={() => openModal()} className="bg-[#10B981] hover:bg-[#0d9668]" data-testid="nova-observacao-btn">
          <Plus size={18} className="mr-2" />Nova Observação
        </Button>
      </div>

      {/* Resumo */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <Card className="stat-card">
          <CardContent className="p-4 flex items-center gap-3">
            <div className="w-10 h-10 bg-emerald-100 rounded-lg flex items-center justify-center">
              <StickyNote className="text-[#10B981]" size={20} />
            </div>
            <div>
              <p className="text-xs text-gray-500">Total de Observações</p>
              <p className="text-lg font-bold text-[#10B981]" data-testid="total-observacoes">{observacoes.length}</p>
            </div>
          </CardContent>
        </Card>
        <Card className="stat-card">
          <CardContent className="p-4 flex items-center gap-3">
            <div className="w-10 h-10 bg-amber-100 rounded-lg flex items-center justify-center">
              <Bell className="text-amber-600" size={20} />
            </div>
            <div>
              <p className="text-xs text-gray-500">Com Lembrete Agendado</p>
              <p className="text-lg font-bold text-amber-600">{comLembrete}</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Busca */}
      <div className="mb-6 relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={18} />
        <Input
          placeholder="Buscar por título, descrição ou funcionário..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pl-10"
          data-testid="busca-observacoes"
        />
      </div>

      {/* Quadro de Observações */}
      {filtered.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-gray-400">
            <StickyNote className="mx-auto mb-4" size={48} />
            <p>Nenhuma observação encontrada</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4" data-testid="quadro-observacoes">
          {filtered.map((o) => (
            <Card key={o.id} className="hover:shadow-lg transition-shadow border-l-4 border-l-[#10B981]" data-testid={`observacao-card-${o.id}`}>
              <CardContent className="p-4 flex flex-col h-full">
                <div className="flex items-start justify-between gap-2 mb-2">
                  <h3 className="font-semibold text-gray-900 leading-snug">{o.titulo}</h3>
                  <div className="flex gap-1 shrink-0">
                    <button
                      onClick={() => openModal(o)}
                      className="p-1.5 rounded-md text-gray-400 hover:text-[#10B981] hover:bg-emerald-50 transition-colors"
                      title="Editar"
                      data-testid={`editar-observacao-${o.id}`}
                    >
                      <Edit size={15} />
                    </button>
                    <button
                      onClick={() => handleDelete(o.id)}
                      className="p-1.5 rounded-md text-gray-400 hover:text-red-600 hover:bg-red-50 transition-colors"
                      title="Excluir"
                      data-testid={`excluir-observacao-${o.id}`}
                    >
                      <Trash2 size={15} />
                    </button>
                  </div>
                </div>

                <p className="text-sm text-gray-600 whitespace-pre-wrap mb-3 flex-1">{o.descricao}</p>

                <div className="space-y-1.5 text-xs border-t pt-3 mt-auto">
                  <div className="flex items-center gap-2 text-gray-600">
                    <User size={13} className="text-gray-400" />
                    <span className="font-medium">{o.funcionario_nome || "Geral (sem vínculo)"}</span>
                  </div>
                  {o.lembrete_ativo ? (
                    <div className="flex items-center gap-2 text-amber-700">
                      <Bell size={13} />
                      <span>Lembrete em {formatDateBR(o.lembrete_data)}</span>
                    </div>
                  ) : (
                    <div className="flex items-center gap-2 text-gray-400">
                      <BellOff size={13} />
                      <span>Sem lembrete</span>
                    </div>
                  )}
                  <div className="flex items-center gap-2 text-gray-400">
                    <Calendar size={13} />
                    <span>Criada em {formatDateTimeBR(o.created_at)}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Modal Form */}
      <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
        <DialogContent className="max-w-xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{editing ? "Editar Observação" : "Nova Observação"}</DialogTitle>
            <DialogDescription>
              Registre uma anotação, vincule a um funcionário e, se quiser, agende um lembrete.
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="form-label">Título *</label>
              <Input
                value={formData.titulo}
                onChange={(e) => setFormData({ ...formData, titulo: e.target.value })}
                placeholder="Ex: Advertência verbal, Elogio, Pendência de documento..."
                required
                data-testid="input-titulo"
              />
            </div>

            <div>
              <label className="form-label">Observação *</label>
              <Textarea
                value={formData.descricao}
                onChange={(e) => setFormData({ ...formData, descricao: e.target.value })}
                placeholder="Escreva a observação..."
                rows={4}
                required
                data-testid="input-descricao"
              />
            </div>

            <div>
              <label className="form-label">Funcionário</label>
              <Select
                value={formData.funcionario_id || "none"}
                onValueChange={(v) => setFormData({ ...formData, funcionario_id: v === "none" ? "" : v })}
              >
                <SelectTrigger className="w-full h-11" data-testid="select-funcionario">
                  <SelectValue placeholder="Selecione um funcionário (opcional)" />
                </SelectTrigger>
                <SelectContent className="z-[9999] max-h-72">
                  <SelectItem value="none">Geral (sem vínculo)</SelectItem>
                  {funcionarios.map((f) => (
                    <SelectItem key={f.id} value={f.id}>{f.nome}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Agendamento de aviso */}
            <div className="border rounded-lg p-3 bg-amber-50/40 space-y-3">
              <div className="flex items-center justify-between">
                <label htmlFor="lembrete-switch" className="text-sm font-medium flex items-center gap-2 cursor-pointer">
                  <Bell size={16} className="text-amber-600" />
                  Agendar aviso (lembrete)
                </label>
                <Switch
                  id="lembrete-switch"
                  checked={formData.lembrete_ativo}
                  onCheckedChange={(v) => setFormData({ ...formData, lembrete_ativo: v })}
                  data-testid="switch-lembrete"
                />
              </div>
              {formData.lembrete_ativo && (
                <div>
                  <label className="form-label">Data do lembrete *</label>
                  <Input
                    type="date"
                    value={formData.lembrete_data}
                    onChange={(e) => setFormData({ ...formData, lembrete_data: e.target.value })}
                    data-testid="input-lembrete-data"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Na data agendada, este aviso aparecerá nas Notificações do RH.
                  </p>
                </div>
              )}
            </div>

            {/* Anexos */}
            <AnexosManager
              ref={anexosRef}
              entityType="observacao_rh"
              entityId={editing?.id}
              title="Anexar arquivo"
            />

            <div className="flex gap-3 pt-2">
              <Button type="button" variant="outline" onClick={closeModal} className="flex-1" data-testid="cancelar-observacao-btn">
                Cancelar
              </Button>
              <Button type="submit" disabled={saving} className="flex-1 bg-[#10B981] hover:bg-[#0d9668]" data-testid="salvar-observacao-btn">
                {saving ? "Salvando..." : editing ? "Atualizar" : "Criar Observação"}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
