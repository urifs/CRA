import { useState, useEffect, createContext, useContext } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate, useNavigate, useLocation } from "react-router-dom";
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

// Axios interceptor for auth - use a flag to prevent multiple interceptors
let interceptorId = null;

const setupAxiosInterceptors = (token, logout) => {
  axios.defaults.headers.common["Authorization"] = token ? `Bearer ${token}` : "";
  
  // Remove existing interceptor if any
  if (interceptorId !== null) {
    axios.interceptors.response.eject(interceptorId);
  }
  
  interceptorId = axios.interceptors.response.use(
    (response) => response,
    (error) => {
      if (error.response?.status === 401) {
        logout();
        toast.error("Sessão expirada. Faça login novamente.");
      }
      return Promise.reject(error);
    }
  );
};

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem("token"));
  const [loading, setLoading] = useState(true);

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    delete axios.defaults.headers.common["Authorization"];
  };

  useEffect(() => {
    const initAuth = async () => {
      const savedToken = localStorage.getItem("token");
      const savedUser = localStorage.getItem("user");
      
      if (savedToken && savedUser) {
        setToken(savedToken);
        setUser(JSON.parse(savedUser));
        setupAxiosInterceptors(savedToken, logout);
        
        // Verify token
        try {
          const response = await axios.get(`${API}/auth/me`);
          setUser(response.data);
        } catch (error) {
          logout();
        }
      }
      setLoading(false);
    };
    
    initAuth();
  }, []);

  const login = (newToken, userData) => {
    setToken(newToken);
    setUser(userData);
    localStorage.setItem("token", newToken);
    localStorage.setItem("user", JSON.stringify(userData));
    setupAxiosInterceptors(newToken, logout);
  };

  return (
    <AuthContext.Provider value={{ user, token, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

// Protected Route
const ProtectedRoute = ({ children }) => {
  const { token, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="spinner w-12 h-12"></div>
      </div>
    );
  }

  if (!token) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
};

// Public Route (redirect to system select if logged in)
const PublicRoute = ({ children }) => {
  const { token, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-900">
        <div className="spinner w-12 h-12 border-t-orange-500"></div>
      </div>
    );
  }

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
