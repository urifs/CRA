import { useState, useEffect, useRef } from "react";
import axios from "axios";
import { API } from "@/App";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Plus, Search, Package, Edit, Trash2, AlertTriangle, ExternalLink, Paperclip, Eye, Download, FileText, Image as ImageIcon, Loader2, X } from "lucide-react";
import { toast } from "sonner";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";

const unidades = [
  { value: "UN", label: "UN - Unidade" },
  { value: "KG", label: "KG - Quilograma" },
  { value: "L", label: "L - Litro" },
  { value: "M", label: "M - Metro" },
  { value: "M2", label: "M² - Metro quadrado" },
  { value: "M3", label: "M³ - Metro cúbico" },
  { value: "CX", label: "CX - Caixa" },
  { value: "PC", label: "PC - Peça" },
  { value: "HR", label: "HR - Hora" },
  { value: "SV", label: "SV - Serviço" },
];

const tiposItem = [
  { value: "00", label: "00 - Mercadoria p/ Revenda" },
  { value: "01", label: "01 - Matéria-Prima" },
  { value: "02", label: "02 - Embalagem" },
  { value: "03", label: "03 - Produto em Processo" },
  { value: "04", label: "04 - Produto Acabado" },
  { value: "05", label: "05 - Subproduto" },
  { value: "06", label: "06 - Produto Intermediário" },
  { value: "07", label: "07 - Material de Uso e Consumo" },
  { value: "08", label: "08 - Ativo Imobilizado" },
  { value: "09", label: "09 - Serviços" },
  { value: "10", label: "10 - Outros insumos" },
];

export default function ProdutosPage() {
  const [produtos, setProdutos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [filterGrupo, setFilterGrupo] = useState("");
  const [filterStatus, setFilterStatus] = useState("");
  const [filterEstoqueBaixo, setFilterEstoqueBaixo] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingProduto, setEditingProduto] = useState(null);
  
  // Anexos
  const [anexos, setAnexos] = useState([]);
  const [uploadingAnexo, setUploadingAnexo] = useState(false);
  const [previewModal, setPreviewModal] = useState({ open: false, url: null, name: null, type: null });
  const fileInputRef = useRef(null);
  
  const [formData, setFormData] = useState({
    codigo_interno: "", codigo_fabricante: "", codigo_barras: "", descricao: "",
    fabricante: "", aplicacao: "", grupo: "", subgrupo: "",
    unidade_comercial: "UN", unidade_tributada: "", multiplo: "1",
    preco_custo: "", preco_venda: "",
    estoque_atual: "0", estoque_minimo: "0", estoque_maximo: "0", localizacao: "",
    ncm: "", cst: "", cest: "", origem: "0", ipi: "0", icms: "0", pis: "0", cofins: "0",
    tipo_item: "00", status: "ativo", em_promocao: false, preco_promocao: "", observacoes: ""
  });

  useEffect(() => { fetchProdutos(); }, [filterGrupo, filterStatus, filterEstoqueBaixo]);

  const fetchProdutos = async () => {
    try {
      let url = `${API}/admin/produtos`;
      const params = new URLSearchParams();
      if (filterGrupo) params.append("grupo", filterGrupo);
      if (filterStatus) params.append("status", filterStatus);
      if (filterEstoqueBaixo) params.append("estoque_baixo", "true");
      if (params.toString()) url += `?${params.toString()}`;
      const response = await axios.get(url);
      setProdutos(response.data);
    } catch (error) { toast.error("Erro ao carregar produtos"); }
    finally { setLoading(false); }
  };

  const handleUploadAnexo = async (e) => {
    const files = e.target.files;
    if (!files?.length || !editingProduto?.id) return;
    
    setUploadingAnexo(true);
    try {
      for (const file of files) {
        const formDataFile = new FormData();
        formDataFile.append("file", file);
        await axios.post(`${API}/admin/produtos/${editingProduto.id}/anexos`, formDataFile, {
          headers: { "Content-Type": "multipart/form-data" }
        });
      }
      toast.success("Anexo(s) adicionado(s)!");
      const response = await axios.get(`${API}/admin/produtos/${editingProduto.id}`);
      setAnexos(response.data.anexos || []);
    } catch (error) {
      toast.error("Erro ao anexar arquivo");
    } finally {
      setUploadingAnexo(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const handleDeleteAnexo = async (anexoId) => {
    if (!confirm("Excluir este anexo?")) return;
    try {
      await axios.delete(`${API}/admin/produtos/${editingProduto.id}/anexos/${anexoId}`);
      setAnexos(anexos.filter(a => a.id !== anexoId));
      toast.success("Anexo excluído!");
    } catch (error) {
      toast.error("Erro ao excluir anexo");
    }
  };

  const handleViewAnexo = (anexo) => {
    const url = `${API.replace('/api', '')}/uploads/produtos/${anexo.filename}`;
    const ext = anexo.filename.split('.').pop().toLowerCase();
    const isImage = ['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(ext);
    const isPdf = ext === 'pdf';
    setPreviewModal({ open: true, url, name: anexo.original_name || anexo.filename, type: isImage ? 'image' : isPdf ? 'pdf' : 'other' });
  };

  const handleDownloadAnexo = async (anexo) => {
    try {
      const response = await axios.get(`${API}/admin/produtos/${editingProduto.id}/anexos/${anexo.id}/download`, {
        responseType: 'blob'
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', anexo.original_name || anexo.filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      toast.error("Erro ao baixar anexo");
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const dataToSend = {
        ...formData,
        multiplo: parseFloat(formData.multiplo) || 1,
        preco_custo: parseFloat(formData.preco_custo) || 0,
        preco_venda: parseFloat(formData.preco_venda) || 0,
        estoque_atual: parseFloat(formData.estoque_atual) || 0,
        estoque_minimo: parseFloat(formData.estoque_minimo) || 0,
        estoque_maximo: parseFloat(formData.estoque_maximo) || 0,
        ipi: parseFloat(formData.ipi) || 0,
        icms: parseFloat(formData.icms) || 0,
        pis: parseFloat(formData.pis) || 0,
        cofins: parseFloat(formData.cofins) || 0,
        preco_promocao: formData.preco_promocao ? parseFloat(formData.preco_promocao) : null,
      };
      if (editingProduto) {
        await axios.put(`${API}/admin/produtos/${editingProduto.id}`, dataToSend);
        toast.success("Produto atualizado!");
      } else {
        await axios.post(`${API}/admin/produtos`, dataToSend);
        toast.success("Produto cadastrado!");
      }
      fetchProdutos(); closeModal();
    } catch (error) { toast.error(error.response?.data?.detail || "Erro ao salvar"); }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Excluir este produto?")) return;
    try {
      await axios.delete(`${API}/admin/produtos/${id}`);
      toast.success("Produto excluído!"); fetchProdutos();
    } catch (error) { toast.error("Erro ao excluir"); }
  };

  const openModal = (produto = null) => {
    if (produto) {
      setEditingProduto(produto);
      setAnexos(produto.anexos || []);
      setFormData({
        codigo_interno: produto.codigo_interno || "",
        codigo_fabricante: produto.codigo_fabricante || "",
        codigo_barras: produto.codigo_barras || "",
        descricao: produto.descricao || "",
        fabricante: produto.fabricante || "",
        aplicacao: produto.aplicacao || "",
        grupo: produto.grupo || "",
        subgrupo: produto.subgrupo || "",
        unidade_comercial: produto.unidade_comercial || "UN",
        unidade_tributada: produto.unidade_tributada || "",
        multiplo: produto.multiplo?.toString() || "1",
        preco_custo: produto.preco_custo?.toString() || "",
        preco_venda: produto.preco_venda?.toString() || "",
        estoque_atual: produto.estoque_atual?.toString() || "0",
        estoque_minimo: produto.estoque_minimo?.toString() || "0",
        estoque_maximo: produto.estoque_maximo?.toString() || "0",
        localizacao: produto.localizacao || "",
        ncm: produto.ncm || "",
        cst: produto.cst || "",
        cest: produto.cest || "",
        origem: produto.origem || "0",
        ipi: produto.ipi?.toString() || "0",
        icms: produto.icms?.toString() || "0",
        pis: produto.pis?.toString() || "0",
        cofins: produto.cofins?.toString() || "0",
        tipo_item: produto.tipo_item || "00",
        status: produto.status || "ativo",
        em_promocao: produto.em_promocao || false,
        preco_promocao: produto.preco_promocao?.toString() || "",
        observacoes: produto.observacoes || ""
      });
    } else {
      setEditingProduto(null);
      setAnexos([]);
      setFormData({
        codigo_interno: "", codigo_fabricante: "", codigo_barras: "", descricao: "",
        fabricante: "", aplicacao: "", grupo: "", subgrupo: "",
        unidade_comercial: "UN", unidade_tributada: "", multiplo: "1",
        preco_custo: "", preco_venda: "",
        estoque_atual: "0", estoque_minimo: "0", estoque_maximo: "0", localizacao: "",
        ncm: "", cst: "", cest: "", origem: "0", ipi: "0", icms: "0", pis: "0", cofins: "0",
        tipo_item: "00", status: "ativo", em_promocao: false, preco_promocao: "", observacoes: ""
      });
    }
    setIsModalOpen(true);
  };

  const closeModal = () => { setIsModalOpen(false); setEditingProduto(null); };

  const formatCurrency = (v) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(v || 0);

  const handleGoogleSearch = (produto) => {
    const query = encodeURIComponent(produto.descricao || produto.codigo_fabricante || produto.codigo_interno);
    window.open(`https://www.google.com/search?q=${query}`, '_blank');
  };

  const filteredProdutos = produtos.filter(p =>
    p.descricao?.toLowerCase().includes(search.toLowerCase()) ||
    p.codigo_interno?.toLowerCase().includes(search.toLowerCase()) ||
    p.codigo_fabricante?.toLowerCase().includes(search.toLowerCase()) ||
    p.fabricante?.toLowerCase().includes(search.toLowerCase())
  );

  // Grupos únicos
  const grupos = [...new Set(produtos.map(p => p.grupo).filter(Boolean))];

  if (loading) return <div className="flex items-center justify-center min-h-[400px]"><div className="spinner w-12 h-12"></div></div>;

  return (
    <div data-testid="produtos-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Produtos</h1>
          <p className="text-gray-500 mt-1">Cadastro de produtos e serviços</p>
        </div>
        <Button onClick={() => openModal()} className="bg-purple-600 hover:bg-purple-700"><Plus size={18} className="mr-2" />Novo Produto</Button>
      </div>

      {/* Filtros */}
      <div className="grid grid-cols-1 md:grid-cols-6 gap-4 mb-6">
        <div className="relative md:col-span-2">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
          <Input placeholder="Buscar por descrição, código, fabricante..." value={search} onChange={(e) => setSearch(e.target.value)} className="pl-10" />
        </div>
        <Select value={filterGrupo || "all"} onValueChange={(v) => setFilterGrupo(v === "all" ? "" : v)}>
          <SelectTrigger className="h-11"><SelectValue placeholder="Todos os Grupos" /></SelectTrigger>
          <SelectContent className="z-[9999]">
            <SelectItem value="all">Todos os Grupos</SelectItem>
            {grupos.map(g => <SelectItem key={g} value={g}>{g}</SelectItem>)}
          </SelectContent>
        </Select>
        <Select value={filterStatus || "all"} onValueChange={(v) => setFilterStatus(v === "all" ? "" : v)}>
          <SelectTrigger className="h-11"><SelectValue placeholder="Todos Status" /></SelectTrigger>
          <SelectContent className="z-[9999]">
            <SelectItem value="all">Todos Status</SelectItem>
            <SelectItem value="ativo">Ativos</SelectItem>
            <SelectItem value="inativo">Inativos</SelectItem>
          </SelectContent>
        </Select>
        <label className="flex items-center gap-2 cursor-pointer">
          <input type="checkbox" checked={filterEstoqueBaixo} onChange={(e) => setFilterEstoqueBaixo(e.target.checked)} className="rounded" />
          <span className="text-sm">Estoque Baixo</span>
        </label>
        <Button className="h-11 bg-[#D4A000] hover:bg-[#b38900] text-black">
          <Search size={16} className="mr-2" />
          Buscar
        </Button>
      </div>

      {/* Legenda */}
      <div className="flex flex-wrap gap-4 mb-4 text-xs">
        <span className="flex items-center gap-1"><span className="w-3 h-3 bg-yellow-400 rounded"></span>Alterou preço</span>
        <span className="flex items-center gap-1"><span className="w-3 h-3 bg-green-400 rounded"></span>Em promoção</span>
        <span className="flex items-center gap-1"><span className="w-3 h-3 bg-red-400 rounded"></span>Estoque mínimo</span>
      </div>

      {/* Tabela */}
      {filteredProdutos.length === 0 ? (
        <Card><CardContent className="py-12 text-center text-gray-400"><Package className="mx-auto mb-4" size={48} /><p>Nenhum produto encontrado</p></CardContent></Card>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full border-collapse bg-white rounded-lg overflow-hidden shadow text-sm">
            <thead className="bg-gray-100">
              <tr>
                <th className="text-left p-3 font-medium text-gray-600">Cód. Int.</th>
                <th className="text-left p-3 font-medium text-gray-600">Cód. Fab.</th>
                <th className="text-left p-3 font-medium text-gray-600">Descrição</th>
                <th className="text-left p-3 font-medium text-gray-600">UN</th>
                <th className="text-right p-3 font-medium text-gray-600">Estoque</th>
                <th className="text-right p-3 font-medium text-gray-600">Custo R$</th>
                <th className="text-right p-3 font-medium text-gray-600">Venda R$</th>
                <th className="text-right p-3 font-medium text-gray-600">M.Lucro %</th>
                <th className="text-left p-3 font-medium text-gray-600">Fabricante</th>
                <th className="text-left p-3 font-medium text-gray-600">NCM</th>
                <th className="text-center p-3 font-medium text-gray-600">Ações</th>
              </tr>
            </thead>
            <tbody>
              {filteredProdutos.map((p) => {
                const estoqueBaixo = p.estoque_atual <= p.estoque_minimo;
                return (
                  <tr 
                    key={p.id} 
                    className={`border-t hover:bg-gray-50 cursor-pointer transition-colors ${estoqueBaixo ? 'bg-red-50' : ''} ${p.em_promocao ? 'bg-green-50' : ''}`}
                    onClick={() => openModal(p)}
                  >
                    <td className="p-3 font-mono text-xs">{p.codigo_interno || "-"}</td>
                    <td className="p-3 font-mono text-xs">{p.codigo_fabricante || "-"}</td>
                    <td className="p-3 max-w-[200px] truncate font-medium">
                      {p.descricao}
                      {estoqueBaixo && <AlertTriangle className="inline ml-1 text-red-500" size={14} />}
                    </td>
                    <td className="p-3">{p.unidade_comercial}</td>
                    <td className={`p-3 text-right ${estoqueBaixo ? 'text-red-600 font-bold' : ''}`}>{p.estoque_atual || 0}</td>
                    <td className="p-3 text-right">{formatCurrency(p.preco_custo)}</td>
                    <td className="p-3 text-right font-medium text-green-600">{formatCurrency(p.em_promocao && p.preco_promocao ? p.preco_promocao : p.preco_venda)}</td>
                    <td className="p-3 text-right">{p.margem_lucro?.toFixed(1) || 0}%</td>
                    <td className="p-3 text-xs">{p.fabricante || "-"}</td>
                    <td className="p-3 font-mono text-xs">{p.ncm || "-"}</td>
                    <td className="p-3 text-center" onClick={(e) => e.stopPropagation()}>
                      <div className="flex justify-center gap-1">
                        <Button size="sm" variant="outline" onClick={() => handleGoogleSearch(p)} title="Buscar no Google" className="text-[#D4A000]">
                          <ExternalLink size={14} />
                        </Button>
                        <Button size="sm" variant="outline" onClick={() => openModal(p)}><Edit size={14} /></Button>
                        <Button size="sm" variant="outline" className="text-red-600" onClick={() => handleDelete(p.id)}><Trash2 size={14} /></Button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Modal */}
      <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
        <DialogContent className="max-w-5xl max-h-[90vh] overflow-y-auto">
          <DialogHeader><DialogTitle>{editingProduto ? "Editar Produto" : "Novo Produto"}</DialogTitle></DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Identificação */}
            <div className="border-b pb-2 mb-2"><h3 className="font-medium text-gray-700">Identificação</h3></div>
            <div className="grid grid-cols-4 gap-4">
              <div><label className="form-label">Código Interno</label><Input value={formData.codigo_interno} onChange={(e) => setFormData({...formData, codigo_interno: e.target.value})} placeholder="Auto" /></div>
              <div><label className="form-label">Código Fabricante</label><Input value={formData.codigo_fabricante} onChange={(e) => setFormData({...formData, codigo_fabricante: e.target.value})} /></div>
              <div><label className="form-label">Código de Barras</label><Input value={formData.codigo_barras} onChange={(e) => setFormData({...formData, codigo_barras: e.target.value})} /></div>
              <div><label className="form-label">Status</label>
                <Select value={formData.status} onValueChange={(v) => setFormData({...formData, status: v})}>
                  <SelectTrigger className="w-full h-11"><SelectValue /></SelectTrigger>
                  <SelectContent className="z-[9999]">
                    <SelectItem value="ativo">Ativo</SelectItem>
                    <SelectItem value="inativo">Inativo</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div><label className="form-label">Descrição *</label><Input value={formData.descricao} onChange={(e) => setFormData({...formData, descricao: e.target.value})} required /></div>
            
            {/* Classificação */}
            <div className="border-b pb-2 mb-2 mt-4"><h3 className="font-medium text-gray-700">Classificação</h3></div>
            <div className="grid grid-cols-4 gap-4">
              <div><label className="form-label">Fabricante</label><Input value={formData.fabricante} onChange={(e) => setFormData({...formData, fabricante: e.target.value})} /></div>
              <div><label className="form-label">Aplicação</label><Input value={formData.aplicacao} onChange={(e) => setFormData({...formData, aplicacao: e.target.value})} /></div>
              <div><label className="form-label">Grupo</label><Input value={formData.grupo} onChange={(e) => setFormData({...formData, grupo: e.target.value})} /></div>
              <div><label className="form-label">Sub-Grupo</label><Input value={formData.subgrupo} onChange={(e) => setFormData({...formData, subgrupo: e.target.value})} /></div>
            </div>

            {/* Unidades e Preços */}
            <div className="border-b pb-2 mb-2 mt-4"><h3 className="font-medium text-gray-700">Unidades e Preços</h3></div>
            <div className="grid grid-cols-6 gap-4">
              <div><label className="form-label">Un. Comercial</label>
                <Select value={formData.unidade_comercial} onValueChange={(v) => setFormData({...formData, unidade_comercial: v})}>
                  <SelectTrigger className="w-full h-11"><SelectValue /></SelectTrigger>
                  <SelectContent className="z-[9999]">
                    {unidades.map(u => <SelectItem key={u.value} value={u.value}>{u.label}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <div><label className="form-label">Un. Tributada</label><Input value={formData.unidade_tributada} onChange={(e) => setFormData({...formData, unidade_tributada: e.target.value})} /></div>
              <div><label className="form-label">Múltiplo</label><Input type="number" step="0.01" value={formData.multiplo} onChange={(e) => setFormData({...formData, multiplo: e.target.value})} /></div>
              <div><label className="form-label">Preço Custo</label><Input type="number" step="0.01" value={formData.preco_custo} onChange={(e) => setFormData({...formData, preco_custo: e.target.value})} /></div>
              <div><label className="form-label">Preço Venda</label><Input type="number" step="0.01" value={formData.preco_venda} onChange={(e) => setFormData({...formData, preco_venda: e.target.value})} /></div>
              <div><label className="form-label">Localização</label><Input value={formData.localizacao} onChange={(e) => setFormData({...formData, localizacao: e.target.value})} placeholder="Prateleira" /></div>
            </div>

            {/* Estoque */}
            <div className="border-b pb-2 mb-2 mt-4"><h3 className="font-medium text-gray-700">Estoque</h3></div>
            <div className="grid grid-cols-3 gap-4">
              <div><label className="form-label">Estoque Atual</label><Input type="number" step="0.01" value={formData.estoque_atual} onChange={(e) => setFormData({...formData, estoque_atual: e.target.value})} /></div>
              <div><label className="form-label">Estoque Mínimo</label><Input type="number" step="0.01" value={formData.estoque_minimo} onChange={(e) => setFormData({...formData, estoque_minimo: e.target.value})} /></div>
              <div><label className="form-label">Estoque Máximo</label><Input type="number" step="0.01" value={formData.estoque_maximo} onChange={(e) => setFormData({...formData, estoque_maximo: e.target.value})} /></div>
            </div>

            {/* Dados Fiscais */}
            <div className="border-b pb-2 mb-2 mt-4"><h3 className="font-medium text-gray-700">Dados Fiscais</h3></div>
            <div className="grid grid-cols-6 gap-4">
              <div><label className="form-label">NCM</label><Input value={formData.ncm} onChange={(e) => setFormData({...formData, ncm: e.target.value})} maxLength={8} /></div>
              <div><label className="form-label">CST</label><Input value={formData.cst} onChange={(e) => setFormData({...formData, cst: e.target.value})} /></div>
              <div><label className="form-label">CEST</label><Input value={formData.cest} onChange={(e) => setFormData({...formData, cest: e.target.value})} /></div>
              <div><label className="form-label">Origem</label><Input value={formData.origem} onChange={(e) => setFormData({...formData, origem: e.target.value})} placeholder="0 = Nacional" /></div>
              <div className="col-span-2"><label className="form-label">Tipo do Item (NF-e)</label>
                <Select value={formData.tipo_item} onValueChange={(v) => setFormData({...formData, tipo_item: v})}>
                  <SelectTrigger className="w-full h-11"><SelectValue /></SelectTrigger>
                  <SelectContent className="z-[9999]">
                    {tiposItem.map(t => <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="grid grid-cols-4 gap-4">
              <div><label className="form-label">IPI %</label><Input type="number" step="0.01" value={formData.ipi} onChange={(e) => setFormData({...formData, ipi: e.target.value})} /></div>
              <div><label className="form-label">ICMS %</label><Input type="number" step="0.01" value={formData.icms} onChange={(e) => setFormData({...formData, icms: e.target.value})} /></div>
              <div><label className="form-label">PIS %</label><Input type="number" step="0.01" value={formData.pis} onChange={(e) => setFormData({...formData, pis: e.target.value})} /></div>
              <div><label className="form-label">COFINS %</label><Input type="number" step="0.01" value={formData.cofins} onChange={(e) => setFormData({...formData, cofins: e.target.value})} /></div>
            </div>

            {/* Promoção */}
            <div className="border-b pb-2 mb-2 mt-4"><h3 className="font-medium text-gray-700">Promoção</h3></div>
            <div className="grid grid-cols-3 gap-4">
              <label className="flex items-center gap-2">
                <input type="checkbox" checked={formData.em_promocao} onChange={(e) => setFormData({...formData, em_promocao: e.target.checked})} className="rounded" />
                <span>Em Promoção</span>
              </label>
              <div><label className="form-label">Preço Promoção</label><Input type="number" step="0.01" value={formData.preco_promocao} onChange={(e) => setFormData({...formData, preco_promocao: e.target.value})} disabled={!formData.em_promocao} /></div>
            </div>

            <div><label className="form-label">Observações</label><Input value={formData.observacoes} onChange={(e) => setFormData({...formData, observacoes: e.target.value})} /></div>

            <div className="flex gap-3 pt-4">
              <Button type="button" variant="outline" onClick={closeModal} className="flex-1">Cancelar</Button>
              <Button type="submit" className="flex-1 bg-purple-600 hover:bg-purple-700">{editingProduto ? "Atualizar" : "Cadastrar"}</Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
