import { useState, useEffect, createContext, useContext } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import axios from "axios";
import { Toaster } from "@/components/ui/sonner";
import { toast } from "sonner";

// Pages
import LoginPage from "@/pages/LoginPage";
import RegisterPage from "@/pages/RegisterPage";
import DashboardPage from "@/pages/DashboardPage";
import MachinesPage from "@/pages/MachinesPage";
import MachineDetailPage from "@/pages/MachineDetailPage";
import CategoriesPage from "@/pages/CategoriesPage";
import MaintenancesPage from "@/pages/MaintenancesPage";
import NewMaintenancePage from "@/pages/NewMaintenancePage";
import MaintenanceDetailPage from "@/pages/MaintenanceDetailPage";
import StockPage from "@/pages/StockPage";
import UsagePage from "@/pages/UsagePage";
import NotificationsPage from "@/pages/NotificationsPage";
import BalancePage from "@/pages/BalancePage";
import ObrasPage from "@/pages/ObrasPage";
import ObraDetailPage from "@/pages/ObraDetailPage";
import AuditPage from "@/pages/AuditPage";
import MorePage from "@/pages/MorePage";
import SystemSelectPage from "@/pages/SystemSelectPage";
import Layout from "@/components/Layout";
import AdminLayout from "@/components/AdminLayout";

// Admin Pages
import AdminDashboardPage from "@/pages/admin/AdminDashboardPage";
import ContasPagarPage from "@/pages/admin/ContasPagarPage";
import ContasReceberPage from "@/pages/admin/ContasReceberPage";
import PlanoContasPage from "@/pages/admin/PlanoContasPage";
import NFEPage from "@/pages/admin/NFEPage";
import FornecedoresPage from "@/pages/admin/FornecedoresPage";
import ProdutosPage from "@/pages/admin/ProdutosPage";
import OrdensServicoPage from "@/pages/admin/OrdensServicoPage";
import AdminMorePage from "@/pages/admin/AdminMorePage";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND_URL}/api`;

// Auth Context
export const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
};

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem("user");
    return saved ? JSON.parse(saved) : null;
  });
  const [token, setToken] = useState(() => localStorage.getItem("token"));
  const [loading, setLoading] = useState(false);

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem("token");
    localStorage.removeItem("user");
  };

  const login = (newToken, userData) => {
    setToken(newToken);
    setUser(userData);
    localStorage.setItem("token", newToken);
    localStorage.setItem("user", JSON.stringify(userData));
  };

  // Set axios header when token changes
  useEffect(() => {
    if (token) {
      axios.defaults.headers.common["Authorization"] = `Bearer ${token}`;
    } else {
      delete axios.defaults.headers.common["Authorization"];
    }
  }, [token]);

  return (
    <AuthContext.Provider value={{ user, token, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

// Protected Route
const ProtectedRoute = ({ children }) => {
  const { token } = useAuth();

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  return children;
};

// Public Route (redirect to system select if logged in)
const PublicRoute = ({ children }) => {
  const { token } = useAuth();

  if (token) {
    return <Navigate to="/select-system" replace />;
  }

  return children;
};

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Toaster position="top-right" richColors />
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<PublicRoute><LoginPage /></PublicRoute>} />
          <Route path="/register" element={<PublicRoute><RegisterPage /></PublicRoute>} />
          
          {/* System selection */}
          <Route path="/select-system" element={<ProtectedRoute><SystemSelectPage /></ProtectedRoute>} />
          
          {/* Gerenciamento Geral routes */}
          <Route path="/" element={<ProtectedRoute><Layout /></ProtectedRoute>}>
            <Route index element={<Navigate to="/select-system" replace />} />
            <Route path="dashboard" element={<DashboardPage />} />
            <Route path="machines" element={<MachinesPage />} />
            <Route path="machines/:id" element={<MachineDetailPage />} />
            <Route path="categories" element={<CategoriesPage />} />
            <Route path="maintenances" element={<MaintenancesPage />} />
            <Route path="maintenances/new" element={<NewMaintenancePage />} />
            <Route path="maintenances/:id" element={<MaintenanceDetailPage />} />
            <Route path="balance" element={<BalancePage />} />
            <Route path="obras" element={<ObrasPage />} />
            <Route path="obras/:id" element={<ObraDetailPage />} />
            <Route path="stock" element={<StockPage />} />
            <Route path="usage" element={<UsagePage />} />
            <Route path="notifications" element={<NotificationsPage />} />
            <Route path="audit" element={<AuditPage />} />
            <Route path="more" element={<MorePage />} />
          </Route>

          {/* Administrativo routes */}
          <Route path="/administrativo" element={<ProtectedRoute><AdminLayout /></ProtectedRoute>}>
            <Route index element={<Navigate to="/administrativo/dashboard" replace />} />
            <Route path="dashboard" element={<AdminDashboardPage />} />
            <Route path="a-pagar" element={<ContasPagarPage />} />
            <Route path="a-receber" element={<ContasReceberPage />} />
            <Route path="plano-contas" element={<PlanoContasPage />} />
            <Route path="nfe" element={<NFEPage />} />
            <Route path="fornecedores" element={<FornecedoresPage />} />
            <Route path="produtos" element={<ProdutosPage />} />
            <Route path="ordens-servico" element={<OrdensServicoPage />} />
            <Route path="more" element={<AdminMorePage />} />
          </Route>
          
          {/* Catch all */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
