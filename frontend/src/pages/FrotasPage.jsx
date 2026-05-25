import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { toast } from "sonner";
import { API } from "@/App";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import AnexosManager from "@/components/AnexosManager";
import { 
  Plus, 
  Edit, 
  Trash2, 
  Truck, 
  FolderTree, 
  ChevronRight,
  Users,
  Loader2,
  Search
} from "lucide-react";

export default function FrotasPage() {
  const navigate = useNavigate();
  const [fleets, setFleets] = useState([]);
  const [subfleets, setSubfleets] = useState([]);
  const [machines, setMachines] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  
  // Modal states
  const [showFleetModal, setShowFleetModal] = useState(false);
  const [showSubfleetModal, setShowSubfleetModal] = useState(false);
  const [editingFleet, setEditingFleet] = useState(null);
  const anexosRef = useRef(null);
  const [editingSubfleet, setEditingSubfleet] = useState(null);
  
  // Form states
  const [fleetForm, setFleetForm] = useState({ name: "", description: "" });
  const [subfleetForm, setSubfleetForm] = useState({ name: "", fleet_id: "", description: "" });
  
  const [selectedFleet, setSelectedFleet] = useState(null);
  const [formLoading, setFormLoading] = useState(false);

  const token = localStorage.getItem("token");

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [fleetsRes, subfleetsRes, machinesRes] = await Promise.all([
        axios.get(`${API}/fleets`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API}/subfleets`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API}/machines`, { headers: { Authorization: `Bearer ${token}` } })
      ]);
      setFleets(fleetsRes.data);
      setSubfleets(subfleetsRes.data);
      setMachines(machinesRes.data);
    } catch (error) {
      toast.error("Erro ao carregar dados");
    } finally {
      setLoading(false);
    }
  };

  // Fleet CRUD
  const handleSaveFleet = async () => {
    if (!fleetForm.name.trim()) {
      toast.error("Digite o nome da frota");
      return;
    }
    
    setFormLoading(true);
    try {
      if (editingFleet) {
        await axios.put(`${API}/fleets/${editingFleet.id}`, fleetForm, {
          headers: { Authorization: `Bearer ${token}` }
        });
        await anexosRef.current?.flushPending(editingFleet.id);
        toast.success("Frota atualizada!");
      } else {
        const _resp = await axios.post(`${API}/fleets`, fleetForm, {
          headers: { Authorization: `Bearer ${token}` }
        });
        await anexosRef.current?.flushPending(_resp.data?.id);
        toast.success("Frota criada!");
      }
      setShowFleetModal(false);
      setEditingFleet(null);
      setFleetForm({ name: "", description: "" });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao salvar frota");
    } finally {
      setFormLoading(false);
    }
  };

  const handleDeleteFleet = async (fleet) => {
    if (!confirm(`Excluir a frota "${fleet.name}"? As subfrotas também serão excluídas.`)) return;
    
    try {
      await axios.delete(`${API}/fleets/${fleet.id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success("Frota excluída!");
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao excluir frota");
    }
  };

  // Subfleet CRUD
  const handleSaveSubfleet = async () => {
    if (!subfleetForm.name.trim()) {
      toast.error("Digite o nome da subfrota");
      return;
    }
    if (!subfleetForm.fleet_id) {
      toast.error("Selecione uma frota");
      return;
    }
    
    setFormLoading(true);
    try {
      if (editingSubfleet) {
        await axios.put(`${API}/subfleets/${editingSubfleet.id}`, {
          name: subfleetForm.name,
          description: subfleetForm.description
        }, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success("Subfrota atualizada!");
      } else {
        await axios.post(`${API}/subfleets`, subfleetForm, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success("Subfrota criada!");
      }
      setShowSubfleetModal(false);
      setEditingSubfleet(null);
      setSubfleetForm({ name: "", fleet_id: "", description: "" });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao salvar subfrota");
    } finally {
      setFormLoading(false);
    }
  };

  const handleDeleteSubfleet = async (subfleet) => {
    if (!confirm(`Excluir a subfrota "${subfleet.name}"?`)) return;
    
    try {
      await axios.delete(`${API}/subfleets/${subfleet.id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success("Subfrota excluída!");
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao excluir subfrota");
    }
  };

  const openEditFleet = (fleet) => {
    setEditingFleet(fleet);
    setFleetForm({ name: fleet.name, description: fleet.description });
    setShowFleetModal(true);
  };

  const openEditSubfleet = (subfleet) => {
    setEditingSubfleet(subfleet);
    setSubfleetForm({ name: subfleet.name, fleet_id: subfleet.fleet_id, description: subfleet.description });
    setShowSubfleetModal(true);
  };

  const openNewSubfleet = (fleetId = "") => {
    setEditingSubfleet(null);
    setSubfleetForm({ name: "", fleet_id: fleetId, description: "" });
    setShowSubfleetModal(true);
  };

  const getMachinesByFleet = (fleetId) => machines.filter(m => m.fleet_id === fleetId);
  const getMachinesBySubfleet = (subfleetId) => machines.filter(m => m.subfleet_id === subfleetId);
  const getSubfleetsByFleet = (fleetId) => subfleets.filter(s => s.fleet_id === fleetId);

  const filteredFleets = fleets.filter(f => 
    f.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="animate-spin text-[#E31A1A]" size={48} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-black flex items-center gap-2">
            <FolderTree className="text-[#E31A1A]" />
            Gerenciamento de Frotas
          </h1>
          <p className="text-gray-500 text-sm mt-1">
            Organize suas máquinas em frotas e subfrotas
          </p>
        </div>
        <div className="flex gap-2">
          <Button onClick={() => { setEditingFleet(null); setFleetForm({ name: "", description: "" }); setShowFleetModal(true); }} className="bg-[#E31A1A] hover:bg-red-700">
            <Plus size={18} className="mr-2" />
            Nova Frota
          </Button>
        </div>
      </div>

      {/* Search */}
      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
        <Input
          placeholder="Buscar frotas..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="pl-10"
        />
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-4 flex items-center gap-4">
            <div className="w-12 h-12 bg-red-100 rounded-lg flex items-center justify-center">
              <FolderTree className="text-[#E31A1A]" size={24} />
            </div>
            <div>
              <p className="text-2xl font-bold">{fleets.length}</p>
              <p className="text-sm text-gray-500">Frotas</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 flex items-center gap-4">
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
              <ChevronRight className="text-blue-600" size={24} />
            </div>
            <div>
              <p className="text-2xl font-bold">{subfleets.length}</p>
              <p className="text-sm text-gray-500">Subfrotas</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 flex items-center gap-4">
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
              <Truck className="text-green-600" size={24} />
            </div>
            <div>
              <p className="text-2xl font-bold">{machines.filter(m => m.fleet_id).length}</p>
              <p className="text-sm text-gray-500">Máquinas em Frotas</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Fleets Grid */}
      {filteredFleets.length === 0 ? (
        <Card>
          <CardContent className="p-12 text-center">
            <FolderTree size={48} className="mx-auto text-gray-300 mb-4" />
            <p className="text-gray-500">Nenhuma frota cadastrada</p>
            <Button onClick={() => setShowFleetModal(true)} className="mt-4 bg-[#E31A1A] hover:bg-red-700">
              <Plus size={18} className="mr-2" />
              Criar Primeira Frota
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {filteredFleets.map((fleet) => {
            const fleetSubfleets = getSubfleetsByFleet(fleet.id);
            const fleetMachines = getMachinesByFleet(fleet.id);
            
            return (
              <Card key={fleet.id} className="overflow-hidden">
                <CardHeader className="bg-gray-50 border-b">
                  <div className="flex justify-between items-center">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-[#E31A1A] rounded-lg flex items-center justify-center">
                        <FolderTree className="text-white" size={20} />
                      </div>
                      <div>
                        <CardTitle className="text-lg">{fleet.name}</CardTitle>
                        {fleet.description && <p className="text-sm text-gray-500">{fleet.description}</p>}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-gray-500 mr-4">
                        {fleetSubfleets.length} subfrotas • {fleetMachines.length} máquinas
                      </span>
                      <Button variant="outline" size="sm" onClick={() => openNewSubfleet(fleet.id)}>
                        <Plus size={14} className="mr-1" /> Subfrota
                      </Button>
                      <Button variant="ghost" size="sm" onClick={() => openEditFleet(fleet)}>
                        <Edit size={14} />
                      </Button>
                      <Button variant="ghost" size="sm" className="text-red-500 hover:text-red-700" onClick={() => handleDeleteFleet(fleet)}>
                        <Trash2 size={14} />
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="p-4">
                  {fleetSubfleets.length === 0 && fleetMachines.length === 0 ? (
                    <p className="text-gray-400 text-center py-4">Nenhuma subfrota ou máquina nesta frota</p>
                  ) : (
                    <div className="space-y-3">
                      {/* Subfleets */}
                      {fleetSubfleets.map((subfleet) => {
                        const subMachines = getMachinesBySubfleet(subfleet.id);
                        return (
                          <div key={subfleet.id} className="border rounded-lg p-3 bg-gray-50">
                            <div className="flex justify-between items-center mb-2">
                              <div className="flex items-center gap-2">
                                <ChevronRight className="text-blue-500" size={18} />
                                <span className="font-medium">{subfleet.name}</span>
                                <span className="text-xs text-gray-400">({subMachines.length} máquinas)</span>
                              </div>
                              <div className="flex gap-1">
                                <Button variant="ghost" size="sm" onClick={() => openEditSubfleet(subfleet)}>
                                  <Edit size={12} />
                                </Button>
                                <Button variant="ghost" size="sm" className="text-red-500" onClick={() => handleDeleteSubfleet(subfleet)}>
                                  <Trash2 size={12} />
                                </Button>
                              </div>
                            </div>
                            {subMachines.length > 0 && (
                              <div className="flex flex-wrap gap-2 mt-2">
                                {subMachines.map((m) => (
                                  <span key={m.id} className="text-xs bg-white border px-2 py-1 rounded flex items-center gap-1">
                                    <Truck size={12} className="text-gray-400" />
                                    {m.name}
                                  </span>
                                ))}
                              </div>
                            )}
                          </div>
                        );
                      })}
                      
                      {/* Machines without subfleet */}
                      {fleetMachines.filter(m => !m.subfleet_id).length > 0 && (
                        <div className="border rounded-lg p-3">
                          <p className="text-sm text-gray-500 mb-2">Máquinas sem subfrota:</p>
                          <div className="flex flex-wrap gap-2">
                            {fleetMachines.filter(m => !m.subfleet_id).map((m) => (
                              <span key={m.id} className="text-xs bg-gray-100 px-2 py-1 rounded flex items-center gap-1">
                                <Truck size={12} className="text-gray-400" />
                                {m.name}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Fleet Modal */}
      <Dialog open={showFleetModal} onOpenChange={setShowFleetModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editingFleet ? "Editar Frota" : "Nova Frota"}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>Nome da Frota *</Label>
              <Input
                value={fleetForm.name}
                onChange={(e) => setFleetForm({ ...fleetForm, name: e.target.value })}
                placeholder="Ex: Frota Região Norte"
              />
            </div>
            <div>
              <Label>Descrição (opcional)</Label>
              <Input
                value={fleetForm.description}
                onChange={(e) => setFleetForm({ ...fleetForm, description: e.target.value })}
                placeholder="Descrição da frota"
              />
            </div>
          </div>
          <AnexosManager
            ref={anexosRef}
            entityType="fleet"
            entityId={editingFleet?.id}
          />
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowFleetModal(false)}>Cancelar</Button>
            <Button onClick={handleSaveFleet} disabled={formLoading} className="bg-[#E31A1A] hover:bg-red-700">
              {formLoading ? <Loader2 className="animate-spin mr-2" size={16} /> : null}
              {editingFleet ? "Salvar" : "Criar"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Subfleet Modal */}
      <Dialog open={showSubfleetModal} onOpenChange={setShowSubfleetModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editingSubfleet ? "Editar Subfrota" : "Nova Subfrota"}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>Frota *</Label>
              <Select 
                value={subfleetForm.fleet_id} 
                onValueChange={(v) => setSubfleetForm({ ...subfleetForm, fleet_id: v })}
                disabled={!!editingSubfleet}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Selecione a frota" />
                </SelectTrigger>
                <SelectContent>
                  {fleets.map((f) => (
                    <SelectItem key={f.id} value={f.id}>{f.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Nome da Subfrota *</Label>
              <Input
                value={subfleetForm.name}
                onChange={(e) => setSubfleetForm({ ...subfleetForm, name: e.target.value })}
                placeholder="Ex: Equipamentos de Escavação"
              />
            </div>
            <div>
              <Label>Descrição (opcional)</Label>
              <Input
                value={subfleetForm.description}
                onChange={(e) => setSubfleetForm({ ...subfleetForm, description: e.target.value })}
                placeholder="Descrição da subfrota"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowSubfleetModal(false)}>Cancelar</Button>
            <Button onClick={handleSaveSubfleet} disabled={formLoading} className="bg-[#E31A1A] hover:bg-red-700">
              {formLoading ? <Loader2 className="animate-spin mr-2" size={16} /> : null}
              {editingSubfleet ? "Salvar" : "Criar"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
