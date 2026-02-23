import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "@/App";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { 
  Plus, 
  Search, 
  Package,
  Edit,
  Trash2,
  Tag,
  DollarSign
} from "lucide-react";
import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

export default function ProdutosPage() {
  const [produtos, setProdutos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingProduto, setEditingProduto] = useState(null);
  const [formData, setFormData] = useState({
    nome: "",
    codigo: "",
    descricao: "",
    unidade: "UN",
    preco_custo: "",
    preco_venda: "",
    categoria: "",
    ncm: ""
  });

  useEffect(() => {
    fetchProdutos();
  }, []);

  const fetchProdutos = async () => {
    try {
      const response = await axios.get(`${API}/admin/produtos`);
      setProdutos(response.data);
    } catch (error) {
      console.error("Erro ao carregar produtos:", error);
      toast.error("Erro ao carregar produtos");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingProduto) {
        await axios.put(`${API}/admin/produtos/${editingProduto.id}`, formData);
        toast.success("Produto atualizado com sucesso!");
      } else {
        await axios.post(`${API}/admin/produtos`, formData);
        toast.success("Produto cadastrado com sucesso!");
      }
      fetchProdutos();
      closeModal();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao salvar produto");
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Deseja realmente excluir este produto?")) return;
    try {
      await axios.delete(`${API}/admin/produtos/${id}`);
      toast.success("Produto excluído com sucesso!");
      fetchProdutos();
    } catch (error) {
      toast.error("Erro ao excluir produto");
    }
  };

  const openModal = (produto = null) => {
    if (produto) {
      setEditingProduto(produto);
      setFormData({
        nome: produto.nome,
        codigo: produto.codigo || "",
        descricao: produto.descricao || "",
        unidade: produto.unidade || "UN",
        preco_custo: produto.preco_custo?.toString() || "",
        preco_venda: produto.preco_venda?.toString() || "",
        categoria: produto.categoria || "",
        ncm: produto.ncm || ""
      });
    } else {
      setEditingProduto(null);
      setFormData({
        nome: "",
        codigo: "",
        descricao: "",
        unidade: "UN",
        preco_custo: "",
        preco_venda: "",
        categoria: "",
        ncm: ""
      });
    }
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setEditingProduto(null);
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(value || 0);
  };

  const filteredProdutos = produtos.filter(p =>
    p.nome.toLowerCase().includes(search.toLowerCase()) ||
    (p.codigo && p.codigo.toLowerCase().includes(search.toLowerCase())) ||
    (p.categoria && p.categoria.toLowerCase().includes(search.toLowerCase()))
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="spinner w-12 h-12"></div>
      </div>
    );
  }

  return (
    <div data-testid="produtos-page">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Produtos</h1>
          <p className="text-slate-500 mt-1">Cadastro de produtos e serviços</p>
        </div>
        <Button onClick={() => openModal()} className="bg-blue-600 hover:bg-blue-700" data-testid="new-produto-btn">
          <Plus size={18} className="mr-2" />
          Novo Produto
        </Button>
      </div>

      {/* Search */}
      <div className="relative mb-6">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400" size={20} />
        <Input
          placeholder="Buscar por nome, código ou categoria..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pl-10"
          data-testid="search-produtos"
        />
      </div>

      {/* Lista */}
      {filteredProdutos.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-slate-400">
            <Package className="mx-auto mb-4" size={48} />
            <p className="font-medium">Nenhum produto encontrado</p>
            <p className="text-sm">Cadastre um novo produto</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filteredProdutos.map((produto) => (
            <Card key={produto.id} className="hover:shadow-md transition-shadow" data-testid={`produto-${produto.id}`}>
              <CardContent className="p-4">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                      <Package className="text-purple-600" size={20} />
                    </div>
                    <div>
                      <h3 className="font-medium text-slate-900">{produto.nome}</h3>
                      {produto.codigo && (
                        <p className="text-xs text-slate-500">Cód: {produto.codigo}</p>
                      )}
                    </div>
                  </div>
                  <span className="text-xs bg-slate-100 px-2 py-1 rounded">{produto.unidade}</span>
                </div>
                
                {produto.categoria && (
                  <div className="flex items-center gap-1 text-xs text-slate-500 mb-2">
                    <Tag size={12} />
                    <span>{produto.categoria}</span>
                  </div>
                )}

                <div className="flex items-center justify-between text-sm mb-3">
                  <div>
                    <p className="text-slate-500">Custo</p>
                    <p className="font-medium">{formatCurrency(produto.preco_custo)}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-slate-500">Venda</p>
                    <p className="font-medium text-green-600">{formatCurrency(produto.preco_venda)}</p>
                  </div>
                </div>

                <div className="flex gap-2 pt-2 border-t">
                  <Button size="sm" variant="outline" className="flex-1" onClick={() => openModal(produto)}>
                    <Edit size={14} className="mr-1" /> Editar
                  </Button>
                  <Button 
                    size="sm" 
                    variant="outline" 
                    className="text-red-600 hover:bg-red-50"
                    onClick={() => handleDelete(produto.id)}
                  >
                    <Trash2 size={14} />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Modal */}
      <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>{editingProduto ? "Editar Produto" : "Novo Produto"}</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="col-span-2">
                <label className="form-label">Nome *</label>
                <Input
                  value={formData.nome}
                  onChange={(e) => setFormData({...formData, nome: e.target.value})}
                  placeholder="Nome do produto"
                  required
                  data-testid="input-nome-produto"
                />
              </div>
              <div>
                <label className="form-label">Código</label>
                <Input
                  value={formData.codigo}
                  onChange={(e) => setFormData({...formData, codigo: e.target.value})}
                  placeholder="SKU / Código"
                  data-testid="input-codigo-produto"
                />
              </div>
              <div>
                <label className="form-label">Unidade</label>
                <select
                  className="form-select"
                  value={formData.unidade}
                  onChange={(e) => setFormData({...formData, unidade: e.target.value})}
                  data-testid="select-unidade"
                >
                  <option value="UN">UN - Unidade</option>
                  <option value="KG">KG - Quilograma</option>
                  <option value="L">L - Litro</option>
                  <option value="M">M - Metro</option>
                  <option value="M2">M² - Metro quadrado</option>
                  <option value="M3">M³ - Metro cúbico</option>
                  <option value="CX">CX - Caixa</option>
                  <option value="PC">PC - Peça</option>
                  <option value="HR">HR - Hora</option>
                  <option value="SV">SV - Serviço</option>
                </select>
              </div>
              <div>
                <label className="form-label">Preço de Custo</label>
                <Input
                  type="number"
                  step="0.01"
                  value={formData.preco_custo}
                  onChange={(e) => setFormData({...formData, preco_custo: e.target.value})}
                  placeholder="0,00"
                  data-testid="input-preco-custo"
                />
              </div>
              <div>
                <label className="form-label">Preço de Venda</label>
                <Input
                  type="number"
                  step="0.01"
                  value={formData.preco_venda}
                  onChange={(e) => setFormData({...formData, preco_venda: e.target.value})}
                  placeholder="0,00"
                  data-testid="input-preco-venda"
                />
              </div>
              <div>
                <label className="form-label">Categoria</label>
                <Input
                  value={formData.categoria}
                  onChange={(e) => setFormData({...formData, categoria: e.target.value})}
                  placeholder="Ex: Peças, Serviços..."
                  data-testid="input-categoria-produto"
                />
              </div>
              <div>
                <label className="form-label">NCM</label>
                <Input
                  value={formData.ncm}
                  onChange={(e) => setFormData({...formData, ncm: e.target.value})}
                  placeholder="00000000"
                  maxLength={8}
                  data-testid="input-ncm"
                />
              </div>
              <div className="col-span-2">
                <label className="form-label">Descrição</label>
                <Input
                  value={formData.descricao}
                  onChange={(e) => setFormData({...formData, descricao: e.target.value})}
                  placeholder="Descrição detalhada do produto"
                  data-testid="input-desc-produto"
                />
              </div>
            </div>
            <div className="flex gap-3 pt-2">
              <Button type="button" variant="outline" onClick={closeModal} className="flex-1">
                Cancelar
              </Button>
              <Button type="submit" className="flex-1 bg-blue-600 hover:bg-blue-700" data-testid="submit-produto">
                {editingProduto ? "Atualizar" : "Cadastrar"}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
