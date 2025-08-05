import React, { useState, useEffect } from 'react';
import './App.css';
import { Button } from './components/ui/button';
import { Card, CardHeader, CardTitle, CardContent } from './components/ui/card';
import { Input } from './components/ui/input';
import { Textarea } from './components/ui/textarea';
import { Badge } from './components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Avatar, AvatarFallback, AvatarImage } from './components/ui/avatar';
import { Alert, AlertDescription } from './components/ui/alert';
import { 
  MapPin, 
  Clock, 
  Star, 
  Truck, 
  CreditCard, 
  Users, 
  TrendingUp,
  Shield,
  MessageCircle,
  HelpCircle,
  LogIn,
  Plus,
  Bike as Motorcycle,
  Store,
  Award,
  Navigation,
  Receipt,
  Timer,
  CheckCircle,
  AlertCircle,
  FileText,
  Wallet,
  Phone,
  Camera,
  Heart,
  UserPlus,
  UserMinus,
  Edit,
  Image,
  Send,
  Eye
} from 'lucide-react';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

function App() {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(false);
  const [deliveries, setDeliveries] = useState([]);
  const [rankings, setRankings] = useState([]);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [showRegistration, setShowRegistration] = useState(false);
  const [registrationType, setRegistrationType] = useState('');

  // Social profile states
  const [userProfile, setUserProfile] = useState(null);
  const [viewingProfile, setViewingProfile] = useState(null);
  const [profilePosts, setProfilePosts] = useState([]);
  const [profileStories, setProfileStories] = useState([]);
  const [feedPosts, setFeedPosts] = useState([]);
  const [feedStories, setFeedStories] = useState([]);
  const [isFollowing, setIsFollowing] = useState(false);
  const [showEditProfile, setShowEditProfile] = useState(false);
  const [showCreatePost, setShowCreatePost] = useState(false);
  const [showCreateStory, setShowCreateStory] = useState(false);

  // Admin dashboard states
  const [adminDashboard, setAdminDashboard] = useState(null);
  const [adminUsers, setAdminUsers] = useState([]);
  const [adminDeliveries, setAdminDeliveries] = useState([]);
  const [adminAnalytics, setAdminAnalytics] = useState(null);
  const [adminFinancial, setAdminFinancial] = useState(null);
  const [adminActiveSection, setAdminActiveSection] = useState('overview');

  // Cities served
  const CITIES = ["Araçariguama", "São Roque", "Mairinque", "Alumínio", "Ibiúna"];

  useEffect(() => {
    if (token) {
      fetchUserProfile();
      fetchDeliveries();
      fetchRankings();
      fetchProfile(); // Load user's social profile
      fetchFeedPosts(); // Load social feed
      fetchFeedStories(); // Load stories feed
      
      // Load admin data if admin user
      if (user?.user_type === 'admin') {
        fetchAdminDashboard();
        fetchAdminUsers();
        fetchAdminDeliveries();
        fetchAdminAnalytics();
        fetchAdminFinancial();
      }
    }
  }, [token, user?.user_type]);

  const fetchUserProfile = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/users/profile`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
      } else {
        handleLogout();
      }
    } catch (error) {
      console.error('Error fetching profile:', error);
    }
  };

  const fetchDeliveries = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/deliveries`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setDeliveries(data.deliveries || []);
      }
    } catch (error) {
      console.error('Error fetching deliveries:', error);
    }
  };

  const fetchRankings = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/rankings`);
      if (response.ok) {
        const data = await response.json();
        setRankings(data.rankings || []);
      }
    } catch (error) {
      console.error('Error fetching rankings:', error);
    }
  };

  const handleShowRegistration = (userType) => {
    setRegistrationType(userType);
    setShowRegistration(true);
  };

  const handleBackToLogin = () => {
    setShowRegistration(false);
    setRegistrationType('');
  };

  const handleGoogleAuth = async (userType) => {
    setLoading(true);
    try {
      const authData = {
        email: `demo.${userType}@srboy.com`,
        name: `Demo ${userType.charAt(0).toUpperCase() + userType.slice(1)}`,
        user_type: userType
      };

      const response = await fetch(`${API_BASE_URL}/api/auth/google`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(authData)
      });

      if (response.ok) {
        const data = await response.json();
        setToken(data.token);
        setUser(data.user);
        localStorage.setItem('token', data.token);
      }
    } catch (error) {
      console.error('Auth error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAdminLogin = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/admin/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          email: 'admin@srboy.com',
          name: 'Naldino - Admin'
        })
      });

      const data = await response.json();
      if (response.ok) {
        localStorage.setItem('token', data.token);
        setToken(data.token);
        setUser(data.admin);
        setUser(prev => ({...prev, user_type: 'admin'}));
      } else {
        alert('Erro no login admin: ' + data.detail);
      }
    } catch (error) {
      alert('Erro de conexão admin');
      console.error('Admin login error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('token');
    setActiveTab('dashboard');
  };

  const createDelivery = async (deliveryData) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/deliveries`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(deliveryData)
      });

      if (response.ok) {
        const data = await response.json();
        fetchDeliveries();
        fetchUserProfile(); // Update wallet balance
        return data;
      } else {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to create delivery');
      }
    } catch (error) {
      throw error;
    }
  };

  const updateDeliveryStatus = async (deliveryId, status) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/deliveries/${deliveryId}/status`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ status })
      });

      if (response.ok) {
        fetchDeliveries();
        fetchUserProfile(); // Update wallet balance
      }
    } catch (error) {
      console.error('Error updating status:', error);
    }
  };

  const updateWaitingTime = async (deliveryId, waitingMinutes) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/deliveries/${deliveryId}/waiting`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ waiting_minutes: waitingMinutes })
      });

      if (response.ok) {
        fetchDeliveries();
        fetchUserProfile();
      }
    } catch (error) {
      console.error('Error updating waiting time:', error);
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      pending: 'bg-yellow-100 text-yellow-800',
      matched: 'bg-blue-100 text-blue-800',
      pickup_confirmed: 'bg-indigo-100 text-indigo-800',
      in_transit: 'bg-purple-100 text-purple-800',
      waiting: 'bg-orange-100 text-orange-800',
      delivered: 'bg-green-100 text-green-800',
      cancelled: 'bg-red-100 text-red-800',
      client_not_found: 'bg-gray-100 text-gray-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  // Social Profile Functions
  const fetchProfile = async (userId = null) => {
    try {
      const targetUserId = userId || user?.id;
      const response = await fetch(`${API_BASE_URL}/api/profile/${targetUserId}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        if (userId && userId !== user?.id) {
          setViewingProfile(data);
          setIsFollowing(data.is_following);
        } else {
          setUserProfile(data);
        }
        setProfilePosts(data.recent_posts || []);
        setProfileStories(data.active_stories || []);
      }
    } catch (error) {
      console.error('Error fetching profile:', error);
    }
  };

  const updateProfile = async (profileData) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/profile`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(profileData)
      });

      if (response.ok) {
        fetchProfile(); // Refresh profile
        setShowEditProfile(false);
      }
    } catch (error) {
      console.error('Error updating profile:', error);
    }
  };

  const toggleFollow = async (userId) => {
    try {
      const method = isFollowing ? 'DELETE' : 'POST';
      const response = await fetch(`${API_BASE_URL}/api/follow/${userId}`, {
        method,
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        setIsFollowing(!isFollowing);
        fetchProfile(userId); // Refresh profile to update counts
      }
    } catch (error) {
      console.error('Error toggling follow:', error);
    }
  };

  const createPost = async (postData) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/posts`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(postData)
      });

      if (response.ok) {
        fetchProfile(); // Refresh to show new post
        fetchFeedPosts(); // Refresh feed
        setShowCreatePost(false);
      } else {
        const error = await response.json();
        alert(error.detail);
      }
    } catch (error) {
      console.error('Error creating post:', error);
    }
  };

  const createStory = async (storyData) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/stories`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(storyData)
      });

      if (response.ok) {
        fetchProfile(); // Refresh to show new story
        fetchFeedStories(); // Refresh feed
        setShowCreateStory(false);
      } else {
        const error = await response.json();
        alert(error.detail);
      }
    } catch (error) {
      console.error('Error creating story:', error);
    }
  };

  const fetchFeedPosts = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/feed/posts`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setFeedPosts(data.posts || []);
      }
    } catch (error) {
      console.error('Error fetching feed posts:', error);
    }
  };

  const fetchFeedStories = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/feed/stories`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setFeedStories(data.stories || []);
      }
    } catch (error) {
      console.error('Error fetching feed stories:', error);
    }
  };

  const convertToBase64 = (file) => {
    return new Promise((resolve, reject) => {
      const fileReader = new FileReader();
      fileReader.readAsDataURL(file);
      fileReader.onload = () => {
        resolve(fileReader.result);
      };
      fileReader.onerror = (error) => {
        reject(error);
      };
    });
  };

  const renderStars = (rating) => {
    const stars = [];
    for (let i = 1; i <= 5; i++) {
      stars.push(
        <Star
          key={i}
          className={`w-4 h-4 ${i <= rating ? 'fill-yellow-400 text-yellow-400' : 'text-gray-300'}`}
        />
      );
    }
    return stars;
  };

  // Admin Dashboard Functions
  const fetchAdminDashboard = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/admin/dashboard`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setAdminDashboard(data);
      }
    } catch (error) {
      console.error('Error fetching admin dashboard:', error);
    }
  };

  const fetchAdminUsers = async (userType = '', city = '') => {
    try {
      const params = new URLSearchParams();
      if (userType) params.append('user_type', userType);
      if (city) params.append('city', city);
      
      const response = await fetch(`${API_BASE_URL}/api/admin/users?${params}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setAdminUsers(data.users);
      }
    } catch (error) {
      console.error('Error fetching admin users:', error);
    }
  };

  const fetchAdminDeliveries = async (status = '', city = '') => {
    try {
      const params = new URLSearchParams();
      if (status) params.append('status', status);
      if (city) params.append('city', city);
      
      const response = await fetch(`${API_BASE_URL}/api/admin/deliveries?${params}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setAdminDeliveries(data.deliveries);
      }
    } catch (error) {
      console.error('Error fetching admin deliveries:', error);
    }
  };

  const fetchAdminAnalytics = async (period = '7d') => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/admin/analytics?period=${period}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setAdminAnalytics(data);
      }
    } catch (error) {
      console.error('Error fetching admin analytics:', error);
    }
  };

  const fetchAdminFinancial = async (period = '30d') => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/admin/financial-report?period=${period}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setAdminFinancial(data);
      }
    } catch (error) {
      console.error('Error fetching admin financial:', error);
    }
  };

  const performAdminAction = async (userId, action, reason = '') => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/admin/user/${userId}/action`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ action, reason })
      });

      if (response.ok) {
        fetchAdminUsers(); // Refresh users list
        alert(`Ação '${action}' executada com sucesso!`);
      } else {
        const error = await response.json();
        alert(`Erro: ${error.detail}`);
      }
    } catch (error) {
      console.error('Error performing admin action:', error);
      alert('Erro ao executar ação administrativa');
    }
  };

  const getStatusText = (status) => {
    const texts = {
      pending: 'Pendente',
      matched: 'Pareado',
      pickup_confirmed: 'Coleta Confirmada',
      in_transit: 'Em Trânsito',
      waiting: 'Aguardando Cliente',
      delivered: 'Entregue',
      cancelled: 'Cancelado',
      client_not_found: 'Cliente Não Encontrado'
    };
    return texts[status] || status;
  };

  if (!user && showRegistration) {
    if (registrationType === 'motoboy') {
      return <MotoboyRegistration onBack={handleBackToLogin} onRegister={handleGoogleAuth} />;
    } else if (registrationType === 'lojista') {
      return <LojistaRegistration onBack={handleBackToLogin} onRegister={handleGoogleAuth} />;
    }
  }

  if (!user) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
        {/* Hero Section */}
        <div className="relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-r from-blue-600/20 to-purple-600/20"></div>
          <div className="relative max-w-7xl mx-auto px-4 py-20">
            <div className="text-center">
              <div className="flex justify-center mb-8">
                <img 
                  src="/srboy-logo.png" 
                  alt="SrBoy Logo" 
                  className="h-32 w-auto"
                />
              </div>
              <h1 className="text-6xl font-bold text-white mb-6">
                <span translate="no">SrBoy</span>
              </h1>
              <p className="text-xl text-slate-300 mb-8 max-w-3xl mx-auto">
                Sistema inteligente de entregas regionais baseado em <span className="text-blue-400 font-semibold">mérito e transparência</span>.
                Preços justos com <span className="text-green-400 font-semibold">R$ 10,00 base</span> e taxa fixa de <span className="text-purple-400 font-semibold">R$ 2,00</span>.
              </p>
              
              {/* Updated Key Features */}
              <div className="grid md:grid-cols-3 gap-6 mb-12 max-w-4xl mx-auto">
                <div className="bg-slate-800/50 backdrop-blur-sm p-6 rounded-xl border border-slate-700">
                  <Award className="h-10 w-10 text-blue-400 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-white mb-2">Sistema de Mérito</h3>
                  <p className="text-slate-400 text-sm">Ranking transparente baseado em desempenho, não privilégios</p>
                </div>
                <div className="bg-slate-800/50 backdrop-blur-sm p-6 rounded-xl border border-slate-700">
                  <CreditCard className="h-10 w-10 text-green-400 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-white mb-2">Preços Justos</h3>
                  <p className="text-slate-400 text-sm">R$ 10,00 base + R$ 2,00/km. Taxa fixa de R$ 2,00</p>
                </div>
                <div className="bg-slate-800/50 backdrop-blur-sm p-6 rounded-xl border border-slate-700">
                  <Timer className="h-10 w-10 text-orange-400 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-white mb-2">Sistema de Espera</h3>
                  <p className="text-slate-400 text-sm">10 min grátis, depois R$ 1,00/min</p>
                </div>
              </div>

              {/* Additional Features */}
              <div className="grid md:grid-cols-2 gap-6 mb-12 max-w-3xl mx-auto">
                <div className="bg-slate-800/30 backdrop-blur-sm p-4 rounded-lg border border-slate-600">
                  <Receipt className="h-8 w-8 text-cyan-400 mx-auto mb-2" />
                  <h4 className="text-sm font-semibold text-white mb-1">Comprovante Digital</h4>
                  <p className="text-slate-400 text-xs">Checkout duplo com informações completas</p>
                </div>
                <div className="bg-slate-800/30 backdrop-blur-sm p-4 rounded-lg border border-slate-600">
                  <Shield className="h-8 w-8 text-emerald-400 mx-auto mb-2" />
                  <h4 className="text-sm font-semibold text-white mb-1">Segurança Avançada</h4>
                  <p className="text-slate-400 text-xs">Dados do motoboy e cliente protegidos</p>
                </div>
              </div>

              {/* Cities Served */}
              <div className="mb-12">
                <h3 className="text-lg font-semibold text-white mb-4">Cidades Atendidas</h3>
                <div className="flex flex-wrap justify-center gap-3">
                  {CITIES.map(city => (
                    <Badge key={city} variant="outline" className="bg-slate-800/50 border-slate-600 text-slate-300">
                      <MapPin className="h-3 w-3 mr-1" />
                      {city}
                    </Badge>
                  ))}
                </div>
              </div>

              {/* Login Options */}
              <div className="space-y-4">
                <h3 className="text-2xl font-semibold text-white mb-6">Escolha seu perfil</h3>
                <div className="flex flex-col sm:flex-row gap-4 justify-center">
                  <Button 
                    onClick={() => handleShowRegistration('motoboy')}
                    className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-6 text-lg rounded-xl flex items-center gap-3"
                  >
                    <Motorcycle className="h-6 w-6" />
                    Cadastrar como Motoboy
                  </Button>
                  <Button 
                    onClick={() => handleShowRegistration('lojista')}
                    className="bg-purple-600 hover:bg-purple-700 text-white px-8 py-6 text-lg rounded-xl flex items-center gap-3"
                  >
                    <Store className="h-6 w-6" />
                    Cadastrar como Lojista
                  </Button>
                </div>
                
                {/* Demo Login Section */}
                <div className="mt-8 pt-8 border-t border-slate-600">
                  <p className="text-slate-400 text-sm mb-4">🎭 Entre com perfis de demonstração:</p>
                  <div className="flex flex-col sm:flex-row gap-3 justify-center">
                    <Button 
                      onClick={() => handleGoogleAuth('motoboy')}
                      disabled={loading}
                      variant="outline"
                      className="border-blue-500 text-blue-300 hover:bg-blue-800/20 px-6 py-3"
                    >
                      {loading ? 'Carregando...' : '🏍️ Carlos - Motoboy'}
                    </Button>
                    <Button 
                      onClick={() => handleGoogleAuth('lojista')}
                      disabled={loading}
                      variant="outline"
                      className="border-purple-500 text-purple-300 hover:bg-purple-800/20 px-6 py-3"
                    >
                      {loading ? 'Carregando...' : '🏪 Maria - Farmácia'}
                    </Button>
                    <Button 
                      onClick={() => handleAdminLogin()}
                      disabled={loading}
                      variant="outline"
                      className="border-red-500 text-red-300 hover:bg-red-800/20 px-6 py-3"
                    >
                      {loading ? 'Carregando...' : '🛡️ Admin - Naldino'}
                    </Button>
                  </div>
                  <p className="text-slate-500 text-xs mt-2 text-center">
                    * Perfis com dados reais de demonstração incluindo posts, stories e seguidores
                  </p>
                </div>
                
                <p className="text-slate-400 text-sm mt-4">
                  * Login via Google OAuth será integrado em produção
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <img 
                src="/srboy-logo.png" 
                alt="SrBoy Logo" 
                className="h-8 w-auto"
              />
              <h1 className="text-2xl font-bold text-slate-900">
                <span translate="no">SrBoy</span>
              </h1>
              <Badge variant="outline" className="text-xs bg-green-50 text-green-700 border-green-200">
                v2.0
              </Badge>
            </div>
            
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <Wallet className="h-4 w-4 text-slate-500" />
                <span className="text-sm font-medium text-slate-700">
                  R$ {((user.wallet_balance || user.loja_wallet_balance) || 0).toFixed(2)}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <Avatar className="h-8 w-8">
                  <AvatarImage src={user.photo_url} />
                  <AvatarFallback className="bg-slate-700 text-white">
                    {user.name.charAt(0).toUpperCase()}
                  </AvatarFallback>
                </Avatar>
                <div className="text-sm">
                  <div className="font-medium text-slate-900">{user.name}</div>
                  <div className="text-slate-500 capitalize">{user.user_type}</div>
                </div>
              </div>
              <Button 
                variant="outline" 
                size="sm" 
                onClick={handleLogout}
                className="text-slate-600 hover:text-slate-900"
              >
                Sair
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 py-8">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full max-w-3xl mx-auto grid-cols-5 bg-slate-100">
            <TabsTrigger value="dashboard" className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4" />
              Dashboard
            </TabsTrigger>
            <TabsTrigger value="deliveries" className="flex items-center gap-2">
              <Truck className="h-4 w-4" />
              Entregas
            </TabsTrigger>
            <TabsTrigger value="social" className="flex items-center gap-2">
              <Users className="h-4 w-4" />
              Social
            </TabsTrigger>
            <TabsTrigger value="rankings" className="flex items-center gap-2">
              <Star className="h-4 w-4" />
              Rankings
            </TabsTrigger>
            {user?.user_type === 'admin' && (
              <TabsTrigger value="admin" className="flex items-center gap-2">
                <Shield className="h-4 w-4" />
                Admin
              </TabsTrigger>
            )}
          </TabsList>

          {/* Dashboard Tab */}
          <TabsContent value="dashboard" className="space-y-6">
            {/* Stats Cards */}
            <div className="grid md:grid-cols-3 gap-6">
              {user.user_type === 'lojista' && (
                <>
                  <Card>
                    <CardHeader className="pb-3">
                      <CardTitle className="text-sm font-medium text-slate-600">Saldo da Carteira</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-3xl font-bold text-green-600">
                        R$ {(user.loja_wallet_balance || 0).toFixed(2)}
                      </div>
                      <p className="text-sm text-slate-500 mt-1">Disponível para entregas</p>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardHeader className="pb-3">
                      <CardTitle className="text-sm font-medium text-slate-600">Entregas Hoje</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-3xl font-bold text-blue-600">
                        {deliveries.filter(d => 
                          new Date(d.created_at).toDateString() === new Date().toDateString()
                        ).length}
                      </div>
                      <p className="text-sm text-slate-500 mt-1">Pedidos realizados</p>
                    </CardContent>
                  </Card>
                </>
              )}
              
              {user.user_type === 'motoboy' && (
                <>
                  <Card>
                    <CardHeader className="pb-3">
                      <CardTitle className="text-sm font-medium text-slate-600">Score de Ranking</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-3xl font-bold text-purple-600">
                        {user.ranking_score || 100}
                      </div>
                      <p className="text-sm text-slate-500 mt-1">Pontuação atual</p>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardHeader className="pb-3">
                      <CardTitle className="text-sm font-medium text-slate-600">Saldo Carteira</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-3xl font-bold text-green-600">
                        R$ {(user.wallet_balance || 0).toFixed(2)}
                      </div>
                      <p className="text-sm text-slate-500 mt-1">Disponível para saque</p>
                    </CardContent>
                  </Card>
                </>
              )}
              
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium text-slate-600">Total de Entregas</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold text-indigo-600">
                    {user.total_deliveries || deliveries.length}
                  </div>
                  <p className="text-sm text-slate-500 mt-1">Concluídas com sucesso</p>
                </CardContent>
              </Card>
            </div>

            {/* New Features Highlight */}
            <Card className="bg-gradient-to-r from-blue-50 to-purple-50 border-blue-200">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-blue-800">
                  <Star className="h-5 w-5" />
                  Novidades SrBoy v2.0
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid md:grid-cols-3 gap-4">
                  <div className="flex items-center gap-3">
                    <Receipt className="h-8 w-8 text-blue-600" />
                    <div>
                      <div className="font-semibold text-blue-800">Comprovante Digital</div>
                      <div className="text-sm text-blue-600">Checkout duplo completo</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <Timer className="h-8 w-8 text-orange-600" />
                    <div>
                      <div className="font-semibold text-orange-800">Sistema de Espera</div>
                      <div className="text-sm text-orange-600">R$ 1,00/min após 10 min</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <CreditCard className="h-8 w-8 text-green-600" />
                    <div>
                      <div className="font-semibold text-green-800">Preços Atualizados</div>
                      <div className="text-sm text-green-600">R$ 10,00 base + R$ 2,00/km</div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Recent Activity */}
            <Card>
              <CardHeader>
                <CardTitle>Atividade Recente</CardTitle>
              </CardHeader>
              <CardContent>
                {deliveries.length === 0 ? (
                  <div className="text-center py-8 text-slate-500">
                    <Truck className="h-12 w-12 mx-auto mb-4 text-slate-300" />
                    <p>Nenhuma entrega encontrada</p>
                    {user.user_type === 'lojista' && (
                      <p className="text-sm mt-2">Crie sua primeira entrega na aba "Entregas"</p>
                    )}
                  </div>
                ) : (
                  <div className="space-y-4">
                    {deliveries.slice(0, 5).map(delivery => (
                      <div key={delivery.id} className="flex items-center justify-between p-4 bg-slate-50 rounded-lg">
                        <div className="flex items-center gap-4">
                          <div className="p-2 bg-white rounded-lg">
                            <MapPin className="h-5 w-5 text-slate-600" />
                          </div>
                          <div>
                            <div className="font-medium text-slate-900">
                              {delivery.pickup_address.city} → {delivery.delivery_address.city}
                            </div>
                            <div className="text-sm text-slate-500">
                              R$ {delivery.total_price.toFixed(2)} • {delivery.distance_km}km
                              {delivery.waiting_fee > 0 && (
                                <span className="ml-2 text-orange-600">
                                  + R$ {delivery.waiting_fee.toFixed(2)} espera
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                        <Badge className={getStatusColor(delivery.status)}>
                          {getStatusText(delivery.status)}
                        </Badge>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Deliveries Tab */}
          <TabsContent value="deliveries" className="space-y-6">
            {user.user_type === 'lojista' && <CreateDeliveryForm onCreateDelivery={createDelivery} />}
            
            <Card>
              <CardHeader>
                <CardTitle>Suas Entregas</CardTitle>
              </CardHeader>
              <CardContent>
                {deliveries.length === 0 ? (
                  <div className="text-center py-8 text-slate-500">
                    <Truck className="h-12 w-12 mx-auto mb-4 text-slate-300" />
                    <p>Nenhuma entrega encontrada</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {deliveries.map(delivery => (
                      <DeliveryCard 
                        key={delivery.id} 
                        delivery={delivery} 
                        userType={user.user_type}
                        onUpdateStatus={updateDeliveryStatus}
                        onUpdateWaiting={updateWaitingTime}
                      />
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Rankings Tab */}
          <TabsContent value="rankings" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Award className="h-5 w-5 text-yellow-500" />
                  Ranking de Motoboys - SrBoy
                </CardTitle>
                <p className="text-sm text-slate-600">
                  Sistema transparente baseado em desempenho e confiabilidade
                </p>
              </CardHeader>
              <CardContent>
                {rankings.length === 0 ? (
                  <div className="text-center py-8 text-slate-500">
                    <Users className="h-12 w-12 mx-auto mb-4 text-slate-300" />
                    <p>Nenhum motoboy encontrado</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {rankings.map(ranking => (
                      <div key={ranking.id} className="flex items-center justify-between p-4 bg-slate-50 rounded-lg hover:bg-slate-100 transition-colors">
                        <div className="flex items-center gap-4">
                          <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm ${
                            ranking.position <= 3 
                              ? 'bg-gradient-to-r from-yellow-400 to-yellow-600 text-white' 
                              : 'bg-slate-200 text-slate-700'
                          }`}>
                            {ranking.position}
                          </div>
                          <div>
                            <div className="font-medium text-slate-900">{ranking.name}</div>
                            <div className="text-sm text-slate-500">
                              {ranking.base_city} • {ranking.total_deliveries} entregas
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-4">
                          <div className="text-right">
                            <div className="font-semibold text-purple-600">{ranking.ranking_score}</div>
                            <div className="text-sm text-slate-500">pontos</div>
                          </div>
                          <div className="text-right">
                            <div className="font-semibold text-green-600">R$ {ranking.wallet_balance.toFixed(2)}</div>
                            <div className="text-sm text-slate-500">carteira</div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Social Tab */}
          <TabsContent value="social" className="space-y-6">
            {user && (
              <div className="grid md:grid-cols-3 gap-6">
                {/* Profile Card */}
                <Card className="md:col-span-2">
                  <CardHeader>
                    <CardTitle className="flex items-center justify-between">
                      <span className="flex items-center gap-2">
                        <Users className="h-5 w-5 text-blue-500" />
                        Meu Perfil Social
                      </span>
                      <Button 
                        variant="outline" 
                        size="sm" 
                        onClick={() => {
                          fetchProfile();
                          setShowEditProfile(true);
                        }}
                      >
                        <Edit className="h-4 w-4 mr-2" />
                        Editar
                      </Button>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {userProfile ? (
                      <div className="space-y-4">
                        {/* Profile Header */}
                        <div className="flex items-start gap-4">
                          <div className="relative">
                            <Avatar className="w-20 h-20">
                              <AvatarImage 
                                src={userProfile.profile?.profile_photo} 
                                alt={userProfile.user?.name} 
                              />
                              <AvatarFallback className="text-2xl font-semibold bg-gradient-to-r from-purple-500 to-pink-500 text-white">
                                {userProfile.user?.name?.charAt(0)}
                              </AvatarFallback>
                            </Avatar>
                          </div>
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-2">
                              <h3 className="text-xl font-bold">{userProfile.user?.name}</h3>
                              <Badge variant="outline" className="text-xs">
                                {userProfile.user?.user_type}
                              </Badge>
                            </div>
                            
                            {/* Star Rating */}
                            <div className="flex items-center gap-1 mb-2">
                              {renderStars(userProfile.user?.star_rating || 3)}
                              <span className="text-sm text-slate-600 ml-2">
                                {userProfile.user?.star_rating || 3}/5 estrelas
                              </span>
                            </div>
                            
                            {/* Stats */}
                            <div className="flex items-center gap-6 text-sm">
                              <div className="flex items-center gap-1">
                                <strong>{userProfile.profile?.followers_count || 0}</strong>
                                <span className="text-slate-600">seguidores</span>
                              </div>
                              <div className="flex items-center gap-1">
                                <strong>{userProfile.profile?.following_count || 0}</strong>
                                <span className="text-slate-600">seguindo</span>
                              </div>
                              <div className="flex items-center gap-1">
                                <strong>{userProfile.recent_posts?.length || 0}</strong>
                                <span className="text-slate-600">posts</span>
                              </div>
                            </div>
                          </div>
                        </div>
                        
                        {/* Bio */}
                        <div>
                          <p className="text-slate-700">
                            {userProfile.profile?.bio || "Nenhuma bio adicionada ainda."}
                          </p>
                        </div>
                        
                        {/* Gallery Photos */}
                        {userProfile.profile?.gallery_photos && userProfile.profile.gallery_photos.length > 0 && (
                          <div>
                            <h4 className="text-sm font-medium text-slate-600 mb-2">Galeria</h4>
                            <div className="flex gap-2">
                              {userProfile.profile.gallery_photos.map((photo, index) => (
                                <img 
                                  key={index}
                                  src={photo}
                                  alt={`Galeria ${index + 1}`}
                                  className="w-16 h-16 rounded-lg object-cover"
                                />
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    ) : (
                      <div className="text-center py-8">
                        <Users className="h-12 w-12 mx-auto mb-4 text-slate-300" />
                        <p className="text-slate-500">Carregando perfil...</p>
                        <Button 
                          onClick={() => fetchProfile()} 
                          className="mt-4"
                          variant="outline"
                        >
                          Carregar Perfil
                        </Button>
                      </div>
                    )}
                  </CardContent>
                </Card>

                {/* Quick Actions */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm font-medium text-slate-600">Ações Rápidas</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <Button 
                      className="w-full flex items-center gap-2" 
                      onClick={() => {
                        fetchProfile();
                        setShowCreatePost(true);
                      }}
                    >
                      <Plus className="h-4 w-4" />
                      Criar Post
                    </Button>
                    <Button 
                      variant="outline" 
                      className="w-full flex items-center gap-2"
                      onClick={() => {
                        fetchProfile();
                        setShowCreateStory(true);
                      }}
                    >
                      <Image className="h-4 w-4" />
                      Criar Story
                    </Button>
                    <Button 
                      variant="outline" 
                      className="w-full flex items-center gap-2"
                      onClick={() => {
                        fetchFeedPosts();
                        fetchFeedStories();
                      }}
                    >
                      <Eye className="h-4 w-4" />
                      Ver Feed
                    </Button>
                  </CardContent>
                </Card>
              </div>
            )}

            {/* Posts Feed */}
            {feedPosts.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <MessageCircle className="h-5 w-5 text-blue-500" />
                    Feed de Posts
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {feedPosts.slice(0, 5).map(post => (
                    <div key={post.id} className="border-b border-slate-200 pb-4 last:border-b-0">
                      <div className="flex items-center gap-3 mb-3">
                        <Avatar className="w-8 h-8">
                          <AvatarImage src={post.author?.profile_photo} alt={post.author?.name} />
                          <AvatarFallback className="text-xs bg-gradient-to-r from-purple-500 to-pink-500 text-white">
                            {post.author?.name?.charAt(0)}
                          </AvatarFallback>
                        </Avatar>
                        <div>
                          <p className="font-medium text-sm">{post.author?.name}</p>
                          <p className="text-xs text-slate-500">
                            {new Date(post.created_at).toLocaleDateString()}
                          </p>
                        </div>
                      </div>
                      <p className="text-slate-700 text-sm">{post.content}</p>
                      {post.image && (
                        <img 
                          src={post.image} 
                          alt="Post" 
                          className="mt-2 rounded-lg max-h-48 object-cover"
                        />
                      )}
                    </div>
                  ))}
                </CardContent>
              </Card>
            )}

            {/* Stories Feed */}
            {feedStories.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Image className="h-5 w-5 text-purple-500" />
                    Stories Ativos
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex gap-3 overflow-x-auto pb-2">
                    {feedStories.slice(0, 10).map(story => (
                      <div key={story.id} className="flex-shrink-0 text-center">
                        <Avatar className="w-12 h-12 ring-2 ring-purple-500 ring-offset-2 mb-1">
                          <AvatarImage src={story.author?.profile_photo} alt={story.author?.name} />
                          <AvatarFallback className="text-xs bg-gradient-to-r from-purple-500 to-pink-500 text-white">
                            {story.author?.name?.charAt(0)}
                          </AvatarFallback>
                        </Avatar>
                        <p className="text-xs text-slate-600 max-w-[60px] truncate">
                          {story.author?.name}
                        </p>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* Admin Tab */}
          {user?.user_type === 'admin' && (
            <TabsContent value="admin" className="space-y-6">
              <div className="grid lg:grid-cols-4 gap-6">
                {/* Admin Navigation */}
                <Card className="lg:col-span-1">
                  <CardHeader>
                    <CardTitle className="text-sm">Painel Administrativo</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      <Button 
                        variant={adminActiveSection === 'overview' ? 'default' : 'ghost'}
                        className="w-full justify-start"
                        onClick={() => setAdminActiveSection('overview')}
                      >
                        <TrendingUp className="h-4 w-4 mr-2" />
                        Visão Geral
                      </Button>
                      <Button 
                        variant={adminActiveSection === 'users' ? 'default' : 'ghost'}
                        className="w-full justify-start"
                        onClick={() => setAdminActiveSection('users')}
                      >
                        <Users className="h-4 w-4 mr-2" />
                        Usuários
                      </Button>
                      <Button 
                        variant={adminActiveSection === 'deliveries' ? 'default' : 'ghost'}
                        className="w-full justify-start"
                        onClick={() => setAdminActiveSection('deliveries')}
                      >
                        <Truck className="h-4 w-4 mr-2" />
                        Entregas
                      </Button>
                      <Button 
                        variant={adminActiveSection === 'financial' ? 'default' : 'ghost'}
                        className="w-full justify-start"
                        onClick={() => setAdminActiveSection('financial')}
                      >
                        <CreditCard className="h-4 w-4 mr-2" />
                        Financeiro
                      </Button>
                      <Button 
                        variant={adminActiveSection === 'security' ? 'default' : 'ghost'}
                        className="w-full justify-start"
                        onClick={() => setAdminActiveSection('security')}
                      >
                        <Shield className="h-4 w-4 mr-2" />
                        Segurança
                      </Button>
                      <Button 
                        variant={adminActiveSection === 'analytics' ? 'default' : 'ghost'}
                        className="w-full justify-start"
                        onClick={() => setAdminActiveSection('analytics')}
                      >
                        <TrendingUp className="h-4 w-4 mr-2" />
                        Analytics
                      </Button>
                    </div>
                  </CardContent>
                </Card>

                {/* Admin Content */}
                <div className="lg:col-span-3">
                  {adminActiveSection === 'overview' && adminDashboard && (
                    <div className="space-y-6">
                      {/* Overview Stats */}
                      <div className="grid md:grid-cols-4 gap-4">
                        <Card>
                          <CardContent className="p-4">
                            <div className="flex items-center justify-between">
                              <div>
                                <p className="text-sm text-slate-600">Total Usuários</p>
                                <p className="text-2xl font-bold">{adminDashboard.overview?.total_users}</p>
                              </div>
                              <Users className="h-8 w-8 text-blue-500" />
                            </div>
                          </CardContent>
                        </Card>
                        
                        <Card>
                          <CardContent className="p-4">
                            <div className="flex items-center justify-between">
                              <div>
                                <p className="text-sm text-slate-600">Entregas Concluídas</p>
                                <p className="text-2xl font-bold">{adminDashboard.overview?.completed_deliveries}</p>
                              </div>
                              <CheckCircle className="h-8 w-8 text-green-500" />
                            </div>
                          </CardContent>
                        </Card>
                        
                        <Card>
                          <CardContent className="p-4">
                            <div className="flex items-center justify-between">
                              <div>
                                <p className="text-sm text-slate-600">Receita Total</p>
                                <p className="text-2xl font-bold">R$ {adminDashboard.financial?.total_revenue?.toFixed(2)}</p>
                              </div>
                              <CreditCard className="h-8 w-8 text-purple-500" />
                            </div>
                          </CardContent>
                        </Card>
                        
                        <Card>
                          <CardContent className="p-4">
                            <div className="flex items-center justify-between">
                              <div>
                                <p className="text-sm text-slate-600">Taxa de Sucesso</p>
                                <p className="text-2xl font-bold">{adminDashboard.overview?.completion_rate}%</p>
                              </div>
                              <Award className="h-8 w-8 text-yellow-500" />
                            </div>
                          </CardContent>
                        </Card>
                      </div>

                      {/* City Statistics */}
                      <Card>
                        <CardHeader>
                          <CardTitle>Estatísticas por Cidade</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <div className="space-y-4">
                            {adminDashboard.city_statistics && Object.entries(adminDashboard.city_statistics).map(([city, stats]) => (
                              <div key={city} className="flex items-center justify-between p-3 bg-slate-50 rounded">
                                <div>
                                  <p className="font-medium">{city}</p>
                                  <p className="text-sm text-slate-600">{stats.motoboys} motoboys • {stats.deliveries} entregas</p>
                                </div>
                                <div className="text-right">
                                  <span className={`px-2 py-1 rounded-full text-xs ${
                                    stats.demand_level === 'high' ? 'bg-red-100 text-red-700' :
                                    stats.demand_level === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                                    'bg-green-100 text-green-700'
                                  }`}>
                                    {stats.demand_level} demanda
                                  </span>
                                </div>
                              </div>
                            ))}
                          </div>
                        </CardContent>
                      </Card>

                      {/* Security Alerts */}
                      <Card>
                        <CardHeader>
                          <CardTitle className="flex items-center gap-2">
                            <Shield className="h-5 w-5 text-red-500" />
                            Alertas de Segurança
                          </CardTitle>
                        </CardHeader>
                        <CardContent>
                          {adminDashboard.security?.recent_alerts?.length > 0 ? (
                            <div className="space-y-3">
                              {adminDashboard.security.recent_alerts.map((alert) => (
                                <div key={alert.id} className="flex items-center justify-between p-3 bg-red-50 border border-red-200 rounded">
                                  <div>
                                    <p className="font-medium text-red-700">{alert.name}</p>
                                    <p className="text-sm text-red-600">Ranking: {alert.ranking_score} pontos</p>
                                  </div>
                                  <Badge variant="destructive">Risco {alert.risk_level}</Badge>
                                </div>
                              ))}
                            </div>
                          ) : (
                            <p className="text-slate-500">Nenhum alerta de segurança ativo</p>
                          )}
                        </CardContent>
                      </Card>
                    </div>
                  )}

                  {adminActiveSection === 'users' && (
                    <div className="space-y-6">
                      <div className="flex gap-4">
                        <Button onClick={() => fetchAdminUsers('motoboy')}>
                          Motoboys
                        </Button>
                        <Button onClick={() => fetchAdminUsers('lojista')}>
                          Lojistas
                        </Button>
                        <Button onClick={() => fetchAdminUsers()}>
                          Todos
                        </Button>
                      </div>

                      <Card>
                        <CardHeader>
                          <CardTitle>Gestão de Usuários</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <div className="space-y-4">
                            {adminUsers.map((user) => (
                              <div key={user.id} className="flex items-center justify-between p-4 border rounded">
                                <div>
                                  <p className="font-medium">{user.name}</p>
                                  <p className="text-sm text-slate-600">
                                    {user.user_type} • {user.email} • {user.base_city || 'N/A'}
                                  </p>
                                  {user.total_deliveries && (
                                    <p className="text-sm text-slate-500">
                                      {user.total_deliveries} entregas realizadas
                                    </p>
                                  )}
                                </div>
                                <div className="flex gap-2">
                                  <Button 
                                    size="sm" 
                                    variant="outline"
                                    onClick={() => performAdminAction(user.id, 'flag_for_review', 'Revisão administrativa')}
                                  >
                                    Sinalizar
                                  </Button>
                                  <Button 
                                    size="sm" 
                                    variant="destructive"
                                    onClick={() => performAdminAction(user.id, 'suspend', 'Suspensão administrativa')}
                                  >
                                    Suspender
                                  </Button>
                                </div>
                              </div>
                            ))}
                          </div>
                        </CardContent>
                      </Card>
                    </div>
                  )}

                  {adminActiveSection === 'deliveries' && (
                    <Card>
                      <CardHeader>
                        <CardTitle>Gestão de Entregas</CardTitle>
                        <div className="flex gap-4">
                          <Button size="sm" onClick={() => fetchAdminDeliveries('pending')}>
                            Pendentes
                          </Button>
                          <Button size="sm" onClick={() => fetchAdminDeliveries('in_transit')}>
                            Em Trânsito
                          </Button>
                          <Button size="sm" onClick={() => fetchAdminDeliveries('delivered')}>
                            Entregues
                          </Button>
                          <Button size="sm" onClick={() => fetchAdminDeliveries()}>
                            Todas
                          </Button>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-4">
                          {adminDeliveries.map((delivery) => (
                            <div key={delivery.id} className="p-4 border rounded">
                              <div className="flex justify-between items-start mb-2">
                                <div>
                                  <p className="font-medium">#{delivery.id.substring(0, 8)}</p>
                                  <p className="text-sm text-slate-600">
                                    {delivery.lojista_name} → {delivery.recipient_info?.name}
                                  </p>
                                </div>
                                <Badge className={getStatusColor(delivery.status)}>
                                  {getStatusText(delivery.status)}
                                </Badge>
                              </div>
                              
                              <div className="grid md:grid-cols-2 gap-4 text-sm">
                                <div>
                                  <p><strong>Valor:</strong> R$ {delivery.total_price?.toFixed(2)}</p>
                                  <p><strong>Distância:</strong> {delivery.distance_km}km</p>
                                </div>
                                <div>
                                  {delivery.pin_confirmacao && (
                                    <p><strong>PIN:</strong> {delivery.pin_confirmacao} 
                                      {delivery.pin_validado_com_sucesso && 
                                        <span className="ml-1 text-green-600">✓ Validado</span>
                                      }
                                    </p>
                                  )}
                                  <p><strong>Data:</strong> {new Date(delivery.created_at).toLocaleDateString()}</p>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </CardContent>
                    </Card>
                  )}

                  {adminActiveSection === 'financial' && adminFinancial && (
                    <div className="space-y-6">
                      <div className="grid md:grid-cols-3 gap-4">
                        <Card>
                          <CardContent className="p-4">
                            <p className="text-sm text-slate-600">Receita Total</p>
                            <p className="text-2xl font-bold text-green-600">R$ {adminFinancial.summary?.total_revenue}</p>
                          </CardContent>
                        </Card>
                        <Card>
                          <CardContent className="p-4">
                            <p className="text-sm text-slate-600">Taxa da Plataforma</p>
                            <p className="text-2xl font-bold text-purple-600">R$ {adminFinancial.summary?.total_platform_fees}</p>
                          </CardContent>
                        </Card>
                        <Card>
                          <CardContent className="p-4">
                            <p className="text-sm text-slate-600">Margem de Lucro</p>
                            <p className="text-2xl font-bold text-blue-600">{adminFinancial.summary?.profit_margin}%</p>
                          </CardContent>
                        </Card>
                      </div>

                      <Card>
                        <CardHeader>
                          <CardTitle>Breakdown por Cidade</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <div className="space-y-3">
                            {adminFinancial.city_breakdown && Object.entries(adminFinancial.city_breakdown).map(([city, data]) => (
                              <div key={city} className="flex justify-between items-center p-3 bg-slate-50 rounded">
                                <div>
                                  <p className="font-medium">{city}</p>
                                  <p className="text-sm text-slate-600">{data.deliveries} entregas</p>
                                </div>
                                <div className="text-right">
                                  <p className="font-bold">R$ {data.revenue}</p>
                                  <p className="text-sm text-slate-600">Avg: R$ {data.avg_delivery_value}</p>
                                </div>
                              </div>
                            ))}
                          </div>
                        </CardContent>
                      </Card>
                    </div>
                  )}

                  {adminActiveSection === 'security' && (
                    <div className="space-y-6">
                      <Card>
                        <CardHeader>
                          <CardTitle className="flex items-center gap-2">
                            <Shield className="h-5 w-5 text-red-500" />
                            Sistema de Segurança PIN
                          </CardTitle>
                        </CardHeader>
                        <CardContent>
                          <div className="grid md:grid-cols-2 gap-4 mb-4">
                            <div className="p-3 bg-blue-50 rounded">
                              <p className="text-sm text-blue-600">Entregas com PIN</p>
                              <p className="text-xl font-bold text-blue-800">
                                {adminDashboard?.security?.pin_system?.deliveries_with_pin || 0}
                              </p>
                            </div>
                            <div className="p-3 bg-green-50 rounded">
                              <p className="text-sm text-green-600">PINs Validados</p>
                              <p className="text-xl font-bold text-green-800">
                                {adminDashboard?.security?.pin_system?.pin_validations_success || 0}
                              </p>
                            </div>
                          </div>
                          
                          <div className="p-3 bg-red-50 rounded mb-4">
                            <p className="text-sm text-red-600">PINs Bloqueados</p>
                            <p className="text-xl font-bold text-red-800">
                              {adminDashboard?.security?.pin_system?.pin_blocked || 0}
                            </p>
                            <p className="text-xs text-red-600 mt-1">
                              (Após 3 tentativas incorretas)
                            </p>
                          </div>
                          
                          <p className="text-sm text-slate-600">
                            💡 O sistema de PIN de confirmação garante que apenas o destinatário correto receba a encomenda,
                            adicionando uma camada extra de segurança às entregas.
                          </p>
                        </CardContent>
                      </Card>

                      <Card>
                        <CardHeader>
                          <CardTitle>Análise de Risco de Motoboys</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <div className="space-y-3">
                            {adminDashboard?.security?.recent_alerts?.map((alert) => (
                              <div key={alert.id} className="p-3 border border-orange-200 bg-orange-50 rounded">
                                <div className="flex justify-between items-start">
                                  <div>
                                    <p className="font-medium">{alert.name}</p>
                                    <p className="text-sm text-orange-700">
                                      Score: {alert.ranking_score} • Nível de risco: {alert.risk_level}
                                    </p>
                                  </div>
                                  <Button size="sm" variant="outline">
                                    Analisar
                                  </Button>
                                </div>
                              </div>
                            ))}
                          </div>
                        </CardContent>
                      </Card>
                    </div>
                  )}

                  {adminActiveSection === 'analytics' && adminAnalytics && (
                    <div className="space-y-6">
                      <Card>
                        <CardHeader>
                          <CardTitle>Métricas de Performance</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <div className="grid md:grid-cols-3 gap-4">
                            <div className="p-3 bg-blue-50 rounded">
                              <p className="text-sm text-blue-600">Tempo Médio de Entrega</p>
                              <p className="text-xl font-bold text-blue-800">
                                {adminAnalytics.performance_metrics?.avg_delivery_time_minutes} min
                              </p>
                            </div>
                            <div className="p-3 bg-green-50 rounded">
                              <p className="text-sm text-green-600">Satisfação Cliente</p>
                              <p className="text-xl font-bold text-green-800">
                                {adminAnalytics.performance_metrics?.customer_satisfaction}/5 ⭐
                              </p>
                            </div>
                            <div className="p-3 bg-purple-50 rounded">
                              <p className="text-sm text-purple-600">Taxa de Sucesso</p>
                              <p className="text-xl font-bold text-purple-800">
                                {adminAnalytics.performance_metrics?.success_rate}%
                              </p>
                            </div>
                          </div>
                        </CardContent>
                      </Card>

                      <Card>
                        <CardHeader>
                          <CardTitle>Top Performers</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <div className="grid md:grid-cols-2 gap-6">
                            <div>
                              <h4 className="font-medium mb-3">🏍️ Top Motoboys</h4>
                              <div className="space-y-2">
                                {adminAnalytics.top_performers?.motoboys?.slice(0, 5).map((motoboy) => (
                                  <div key={motoboy.id} className="flex justify-between p-2 bg-slate-50 rounded">
                                    <span className="text-sm">{motoboy.name}</span>
                                    <span className="text-sm font-medium">{motoboy.total_deliveries} entregas</span>
                                  </div>
                                ))}
                              </div>
                            </div>
                            
                            <div>
                              <h4 className="font-medium mb-3">🏪 Top Lojistas</h4>
                              <div className="space-y-2">
                                {adminAnalytics.top_performers?.lojistas?.slice(0, 5).map((lojista) => (
                                  <div key={lojista.id} className="flex justify-between p-2 bg-slate-50 rounded">
                                    <span className="text-sm">{lojista.name}</span>
                                    <span className="text-sm font-medium">{lojista.total_deliveries} pedidos</span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    </div>
                  )}
                </div>
              </div>
            </TabsContent>
          )}
        </Tabs>
      </div>

      {/* Modals */}
      {showEditProfile && (
        <EditProfileModal 
          profile={userProfile}
          onClose={() => setShowEditProfile(false)}
          onUpdate={updateProfile}
          convertToBase64={convertToBase64}
        />
      )}

      {showCreatePost && (
        <CreatePostModal 
          onClose={() => setShowCreatePost(false)}
          onCreate={createPost}
          convertToBase64={convertToBase64}
        />
      )}

      {showCreateStory && (
        <CreateStoryModal 
          onClose={() => setShowCreateStory(false)}
          onCreate={createStory}
          convertToBase64={convertToBase64}
        />
      )}
    </div>
  );
}

// Edit Profile Modal Component
function EditProfileModal({ profile, onClose, onUpdate, convertToBase64 }) {
  const [formData, setFormData] = useState({
    bio: profile?.profile?.bio || '',
    profile_photo: '',
    cover_photo: '',
    gallery_photos: profile?.profile?.gallery_photos || []
  });
  const [loading, setLoading] = useState(false);

  const handleFileChange = async (field, file) => {
    if (file) {
      try {
        const base64 = await convertToBase64(file);
        if (field === 'gallery_photos') {
          if (formData.gallery_photos.length < 2) {
            setFormData(prev => ({
              ...prev,
              gallery_photos: [...prev.gallery_photos, base64]
            }));
          } else {
            alert('Máximo 2 fotos na galeria');
          }
        } else {
          setFormData(prev => ({
            ...prev,
            [field]: base64
          }));
        }
      } catch (error) {
        console.error('Erro ao converter imagem:', error);
      }
    }
  };

  const removeGalleryPhoto = (index) => {
    setFormData(prev => ({
      ...prev,
      gallery_photos: prev.gallery_photos.filter((_, i) => i !== index)
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (formData.bio.length > 300) {
      alert('Bio não pode exceder 300 caracteres');
      return;
    }

    setLoading(true);
    await onUpdate(formData);
    setLoading(false);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <Card className="w-full max-w-md max-h-[90vh] overflow-y-auto">
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>Editar Perfil</span>
            <Button variant="ghost" size="sm" onClick={onClose}>
              ×
            </Button>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">Bio (máx. 300 caracteres)</label>
              <Textarea
                value={formData.bio}
                onChange={(e) => setFormData(prev => ({ ...prev, bio: e.target.value }))}
                placeholder="Conte um pouco sobre você..."
                maxLength={300}
                rows={3}
              />
              <p className="text-xs text-slate-500 mt-1">
                {formData.bio.length}/300 caracteres
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Foto de Perfil</label>
              <Input
                type="file"
                accept="image/*"
                onChange={(e) => handleFileChange('profile_photo', e.target.files[0])}
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Foto de Capa</label>
              <Input
                type="file"
                accept="image/*"
                onChange={(e) => handleFileChange('cover_photo', e.target.files[0])}
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">
                Galeria ({formData.gallery_photos.length}/2 fotos)
              </label>
              {formData.gallery_photos.length < 2 && (
                <Input
                  type="file"
                  accept="image/*"
                  onChange={(e) => handleFileChange('gallery_photos', e.target.files[0])}
                />
              )}
              
              {formData.gallery_photos.length > 0 && (
                <div className="flex gap-2 mt-2">
                  {formData.gallery_photos.map((photo, index) => (
                    <div key={index} className="relative">
                      <img 
                        src={photo}
                        alt={`Galeria ${index + 1}`}
                        className="w-16 h-16 rounded object-cover"
                      />
                      <Button
                        type="button"
                        variant="destructive"
                        size="sm"
                        className="absolute -top-1 -right-1 w-5 h-5 p-0"
                        onClick={() => removeGalleryPhoto(index)}
                      >
                        ×
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="flex gap-2">
              <Button type="submit" disabled={loading} className="flex-1">
                {loading ? 'Salvando...' : 'Salvar'}
              </Button>
              <Button type="button" variant="outline" onClick={onClose}>
                Cancelar
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}

// Create Post Modal Component
function CreatePostModal({ onClose, onCreate, convertToBase64 }) {
  const [content, setContent] = useState('');
  const [image, setImage] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleFileChange = async (file) => {
    if (file) {
      try {
        const base64 = await convertToBase64(file);
        setImage(base64);
      } catch (error) {
        console.error('Erro ao converter imagem:', error);
      }
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!content.trim() && !image) {
      alert('Adicione um texto ou uma imagem');
      return;
    }

    if (content.length > 500) {
      alert('Post não pode exceder 500 caracteres');
      return;
    }

    setLoading(true);
    await onCreate({ content: content.trim(), image });
    setLoading(false);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>Criar Post</span>
            <Button variant="ghost" size="sm" onClick={onClose}>
              ×
            </Button>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">Conteúdo (máx. 500 caracteres)</label>
              <Textarea
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder="O que está acontecendo?"
                maxLength={500}
                rows={4}
              />
              <p className="text-xs text-slate-500 mt-1">
                {content.length}/500 caracteres
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Imagem (opcional)</label>
              <Input
                type="file"
                accept="image/*"
                onChange={(e) => handleFileChange(e.target.files[0])}
              />
              {image && (
                <img 
                  src={image}
                  alt="Preview"
                  className="mt-2 w-full max-h-48 object-cover rounded"
                />
              )}
            </div>

            <div className="flex gap-2">
              <Button type="submit" disabled={loading} className="flex-1">
                <Send className="h-4 w-4 mr-2" />
                {loading ? 'Publicando...' : 'Publicar'}
              </Button>
              <Button type="button" variant="outline" onClick={onClose}>
                Cancelar
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}

// Create Story Modal Component  
function CreateStoryModal({ onClose, onCreate, convertToBase64 }) {
  const [content, setContent] = useState('');
  const [image, setImage] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleFileChange = async (file) => {
    if (file) {
      try {
        const base64 = await convertToBase64(file);
        setImage(base64);
      } catch (error) {
        console.error('Erro ao converter imagem:', error);
      }
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!content.trim() && !image) {
      alert('Adicione um texto ou uma imagem');
      return;
    }

    if (content.length > 200) {
      alert('Story não pode exceder 200 caracteres');
      return;
    }

    setLoading(true);
    await onCreate({ content: content.trim(), image });
    setLoading(false);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>Criar Story</span>
            <Button variant="ghost" size="sm" onClick={onClose}>
              ×
            </Button>
          </CardTitle>
          <p className="text-sm text-slate-600">Expira em 24 horas</p>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">Conteúdo (máx. 200 caracteres)</label>
              <Textarea
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder="Compartilhe um momento..."
                maxLength={200}
                rows={3}
              />
              <p className="text-xs text-slate-500 mt-1">
                {content.length}/200 caracteres
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Imagem (opcional)</label>
              <Input
                type="file"
                accept="image/*"
                onChange={(e) => handleFileChange(e.target.files[0])}
              />
              {image && (
                <img 
                  src={image}
                  alt="Preview"
                  className="mt-2 w-full max-h-48 object-cover rounded"
                />
              )}
            </div>

            <div className="flex gap-2">
              <Button type="submit" disabled={loading} className="flex-1">
                <Send className="h-4 w-4 mr-2" />
                {loading ? 'Publicando...' : 'Publicar Story'}
              </Button>
              <Button type="button" variant="outline" onClick={onClose}>
                Cancelar
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}

// Enhanced Create Delivery Form Component
function CreateDeliveryForm({ onCreateDelivery }) {
  const [formData, setFormData] = useState({
    pickup_address: { city: '', address: '', lat: -23.5505, lng: -46.6333 },
    delivery_address: { city: '', address: '', lat: -23.5505, lng: -46.6333 },
    recipient_info: { name: '', rg: '', alternative_recipient: '' },
    description: '',
    product_description: ''
  });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  const CITIES = ["Araçariguama", "São Roque", "Mairinque", "Alumínio", "Ibiúna"];

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');

    try {
      const result = await onCreateDelivery(formData);
      setMessage({
        type: 'success',
        text: result.matched_motoboy 
          ? `Entrega criada! Pareado com ${result.matched_motoboy.name} (${result.matched_motoboy.moto_info.color} ${result.matched_motoboy.moto_info.model} - ${result.matched_motoboy.moto_info.plate})`
          : 'Entrega criada! Procurando motoboy disponível...'
      });
      
      // Reset form
      setFormData({
        pickup_address: { city: '', address: '', lat: -23.5505, lng: -46.6333 },
        delivery_address: { city: '', address: '', lat: -23.5505, lng: -46.6333 },
        recipient_info: { name: '', rg: '', alternative_recipient: '' },
        description: '',
        product_description: ''
      });
    } catch (error) {
      setMessage({
        type: 'error',
        text: error.message || 'Erro ao criar entrega'
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Plus className="h-5 w-5" />
          Criar Nova Entrega - SrBoy
        </CardTitle>
        <p className="text-sm text-slate-600">
          Nova tarifa: R$ 10,00 base + R$ 2,00/km | Taxa de espera: R$ 1,00/min após 10 min
        </p>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid md:grid-cols-2 gap-6">
            {/* Pickup Address */}
            <div className="space-y-4">
              <h3 className="font-medium text-slate-900">Endereço de Coleta</h3>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Cidade</label>
                <select
                  value={formData.pickup_address.city}
                  onChange={(e) => setFormData({
                    ...formData,
                    pickup_address: { ...formData.pickup_address, city: e.target.value }
                  })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  required
                >
                  <option value="">Selecione a cidade</option>
                  {CITIES.map(city => (
                    <option key={city} value={city}>{city}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Endereço</label>
                <Input
                  value={formData.pickup_address.address}
                  onChange={(e) => setFormData({
                    ...formData,
                    pickup_address: { ...formData.pickup_address, address: e.target.value }
                  })}
                  placeholder="Rua, número, bairro"
                  required
                />
              </div>
            </div>

            {/* Delivery Address */}
            <div className="space-y-4">
              <h3 className="font-medium text-slate-900">Endereço de Entrega</h3>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Cidade</label>
                <select
                  value={formData.delivery_address.city}
                  onChange={(e) => setFormData({
                    ...formData,
                    delivery_address: { ...formData.delivery_address, city: e.target.value }
                  })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  required
                >
                  <option value="">Selecione a cidade</option>
                  {CITIES.map(city => (
                    <option key={city} value={city}>{city}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Endereço</label>
                <Input
                  value={formData.delivery_address.address}
                  onChange={(e) => setFormData({
                    ...formData,
                    delivery_address: { ...formData.delivery_address, address: e.target.value }
                  })}
                  placeholder="Rua, número, bairro"
                  required
                />
              </div>
            </div>
          </div>

          {/* Recipient Information */}
          <div className="space-y-4">
            <h3 className="font-medium text-slate-900">Informações do Destinatário</h3>
            <div className="grid md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Nome Completo</label>
                <Input
                  value={formData.recipient_info.name}
                  onChange={(e) => setFormData({
                    ...formData,
                    recipient_info: { ...formData.recipient_info, name: e.target.value }
                  })}
                  placeholder="Nome do destinatário"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">RG</label>
                <Input
                  value={formData.recipient_info.rg}
                  onChange={(e) => setFormData({
                    ...formData,
                    recipient_info: { ...formData.recipient_info, rg: e.target.value }
                  })}
                  placeholder="000.000.000-0"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Autorizado Alternativo (opcional)</label>
                <Input
                  value={formData.recipient_info.alternative_recipient}
                  onChange={(e) => setFormData({
                    ...formData,
                    recipient_info: { ...formData.recipient_info, alternative_recipient: e.target.value }
                  })}
                  placeholder="Nome alternativo"
                />
              </div>
            </div>
          </div>

          {/* Product Information */}
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Descrição do Produto</label>
              <Input
                value={formData.product_description}
                onChange={(e) => setFormData({ ...formData, product_description: e.target.value })}
                placeholder="Ex: Documento, Remédio, Produto frágil..."
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Observações (opcional)</label>
              <Input
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="Instruções especiais..."
              />
            </div>
          </div>

          {/* Message */}
          {message && (
            <Alert className={message.type === 'success' ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'}>
              <AlertDescription className={message.type === 'success' ? 'text-green-800' : 'text-red-800'}>
                {message.text}
              </AlertDescription>
            </Alert>
          )}

          <Button type="submit" disabled={loading} className="w-full bg-blue-600 hover:bg-blue-700">
            {loading ? 'Criando...' : 'Criar Entrega - SrBoy'}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}

// Enhanced Delivery Card Component
function DeliveryCard({ delivery, userType, onUpdateStatus, onUpdateWaiting }) {
  const [waitingMinutes, setWaitingMinutes] = useState(delivery.waiting_minutes || 0);
  const [showWaitingInput, setShowWaitingInput] = useState(false);
  const [showPinModal, setShowPinModal] = useState(false);
  const [pin, setPin] = useState('');
  const [pinError, setPinError] = useState('');
  const [pinLoading, setPinLoading] = useState(false);
  const [pinAttempts, setPinAttempts] = useState(0);

  const getStatusColor = (status) => {
    const colors = {
      pending: 'bg-yellow-100 text-yellow-800',
      matched: 'bg-blue-100 text-blue-800',
      pickup_confirmed: 'bg-indigo-100 text-indigo-800',
      in_transit: 'bg-purple-100 text-purple-800',
      waiting: 'bg-orange-100 text-orange-800',
      delivered: 'bg-green-100 text-green-800',
      cancelled: 'bg-red-100 text-red-800',
      client_not_found: 'bg-gray-100 text-gray-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const getStatusText = (status) => {
    const texts = {
      pending: 'Pendente',
      matched: 'Pareado',
      pickup_confirmed: 'Coleta Confirmada',
      in_transit: 'Em Trânsito',
      waiting: 'Aguardando Cliente',
      delivered: 'Entregue',
      cancelled: 'Cancelado',
      client_not_found: 'Cliente Não Encontrado'
    };
    return texts[status] || status;
  };

  const handleWaitingUpdate = () => {
    onUpdateWaiting(delivery.id, waitingMinutes);
    setShowWaitingInput(false);
  };

  const handlePinValidation = async () => {
    if (!pin || pin.length !== 4) {
      setPinError('PIN deve ter 4 dígitos');
      return;
    }

    setPinLoading(true);
    setPinError('');

    try {
      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || process.env.REACT_APP_BACKEND_URL}/api/deliveries/${delivery.id}/validate-pin`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({ pin })
      });

      const data = await response.json();

      if (data.success) {
        // PIN validado com sucesso, agora pode finalizar entrega
        setShowPinModal(false);
        setPin('');
        setPinError('');
        setPinAttempts(0);
        await onUpdateStatus(delivery.id, 'delivered');
      } else {
        setPinError(data.message);
        setPinAttempts(data.attempts || 0);
        if (data.code === 'PIN_BLOCKED') {
          setShowPinModal(false);
        }
      }
    } catch (error) {
      setPinError('Erro ao validar PIN. Tente novamente.');
    } finally {
      setPinLoading(false);
    }
  };

  const handleDeliveryAttempt = () => {
    if (delivery.pin_confirmacao && userType === 'motoboy') {
      setShowPinModal(true);
    } else {
      onUpdateStatus(delivery.id, 'delivered');
    }
  };

  return (
    <div className="border border-slate-200 rounded-lg p-6 bg-white hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-blue-50 rounded-lg">
            <Navigation className="h-5 w-5 text-blue-600" />
          </div>
          <div>
            <div className="font-semibold text-slate-900">
              {delivery.pickup_address.city} → {delivery.delivery_address.city}
            </div>
            <div className="text-sm text-slate-500">
              {new Date(delivery.created_at).toLocaleDateString('pt-BR')}
            </div>
          </div>
        </div>
        <Badge className={getStatusColor(delivery.status)}>
          {getStatusText(delivery.status)}
        </Badge>
      </div>

      <div className="grid md:grid-cols-2 gap-4 mb-4">
        <div>
          <div className="text-sm font-medium text-slate-700 mb-1">Coleta</div>
          <div className="text-sm text-slate-600">{delivery.pickup_address.address}</div>
        </div>
        <div>
          <div className="text-sm font-medium text-slate-700 mb-1">Entrega</div>
          <div className="text-sm text-slate-600">{delivery.delivery_address.address}</div>
        </div>
      </div>

      {/* Recipient Information */}
      {delivery.recipient_info && (
        <div className="mb-4 p-3 bg-slate-50 rounded-lg">
          <div className="text-sm font-medium text-slate-700 mb-1">Destinatário</div>
          <div className="text-sm text-slate-600">
            {delivery.recipient_info.name} • RG: {delivery.recipient_info.rg}
            {delivery.recipient_info.alternative_recipient && (
              <span className="ml-2 text-slate-500">
                (Alt: {delivery.recipient_info.alternative_recipient})
              </span>
            )}
          </div>
        </div>
      )}

      {/* PIN Information for Lojista */}
      {delivery.pin_confirmacao && userType === 'lojista' && (
        <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <Shield className="h-4 w-4 text-blue-600" />
            <div className="text-sm font-medium text-blue-700">PIN de Segurança</div>
          </div>
          <div className="text-lg font-mono font-bold text-blue-800 mb-1">
            {delivery.pin_confirmacao}
          </div>
          <div className="text-xs text-blue-600">
            📞 Informe este código de 4 dígitos ao seu cliente. O motoboy irá solicitar para confirmar a entrega.
          </div>
          {delivery.pin_tentativas > 0 && (
            <div className="text-xs text-orange-600 mt-1">
              ⚠️ {delivery.pin_tentativas} tentativa(s) de validação realizadas
            </div>
          )}
          {delivery.pin_bloqueado && (
            <div className="text-xs text-red-600 mt-1">
              🔒 PIN bloqueado após 3 tentativas. Entre em contato com o suporte.
            </div>
          )}
        </div>
      )}

      {/* PIN Status for Motoboy */}
      {delivery.pin_confirmacao && userType === 'motoboy' && (
        <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
          <div className="flex items-center gap-2 mb-1">
            <Shield className="h-4 w-4 text-yellow-600" />
            <div className="text-sm font-medium text-yellow-700">Validação PIN Necessária</div>
          </div>
          <div className="text-xs text-yellow-700">
            Solicite o PIN de 4 dígitos ao cliente para confirmar a entrega.
          </div>
          {delivery.pin_tentativas > 0 && (
            <div className="text-xs text-orange-600 mt-1">
              ⚠️ {delivery.pin_tentativas} tentativa(s) realizadas - {3 - delivery.pin_tentativas} restantes
            </div>
          )}
          {delivery.pin_bloqueado && (
            <div className="text-xs text-red-600 mt-1">
              🔒 PIN bloqueado. Entre em contato com o suporte.
            </div>
          )}
        </div>
      )}

      {/* Product Information */}
      {delivery.product_description && (
        <div className="mb-4">
          <div className="text-sm font-medium text-slate-700 mb-1">Produto</div>
          <div className="text-sm text-slate-600">{delivery.product_description}</div>
        </div>
      )}

      {/* Pricing Information */}
      <div className="flex items-center justify-between pt-4 border-t border-slate-100">
        <div className="flex items-center gap-4 text-sm text-slate-600">
          <span>{delivery.distance_km}km</span>
          <span>R$ {delivery.total_price.toFixed(2)}</span>
          {delivery.waiting_fee > 0 && (
            <span className="text-orange-600">+ R$ {delivery.waiting_fee.toFixed(2)} espera</span>
          )}
          {userType === 'motoboy' && (
            <span className="text-green-600">Ganho: R$ {(delivery.motoboy_earnings || 0).toFixed(2)}</span>
          )}
        </div>
        
        <div className="flex gap-2">
          {/* Motoboy Action Buttons */}
          {userType === 'motoboy' && delivery.status === 'matched' && (
            <Button 
              size="sm" 
              onClick={() => onUpdateStatus(delivery.id, 'pickup_confirmed')}
              className="bg-indigo-600 hover:bg-indigo-700"
            >
              Confirmar Coleta
            </Button>
          )}
          
          {userType === 'motoboy' && delivery.status === 'pickup_confirmed' && (
            <Button 
              size="sm" 
              onClick={() => onUpdateStatus(delivery.id, 'in_transit')}
              className="bg-purple-600 hover:bg-purple-700"
            >
              Iniciar Entrega
            </Button>
          )}
          
          {userType === 'motoboy' && delivery.status === 'in_transit' && (
            <>
              <Button 
                size="sm" 
                onClick={() => onUpdateStatus(delivery.id, 'waiting')}
                className="bg-orange-600 hover:bg-orange-700"
              >
                <Timer className="h-4 w-4 mr-1" />
                Aguardando
              </Button>
              <Button 
                size="sm" 
                onClick={handleDeliveryAttempt}
                className="bg-green-600 hover:bg-green-700"
                disabled={delivery.pin_bloqueado}
              >
                <CheckCircle className="h-4 w-4 mr-1" />
                Entregar
              </Button>
            </>
          )}
          
          {userType === 'motoboy' && delivery.status === 'waiting' && (
            <div className="flex gap-2 items-center">
              {!showWaitingInput ? (
                <Button 
                  size="sm" 
                  onClick={() => setShowWaitingInput(true)}
                  className="bg-orange-600 hover:bg-orange-700"
                >
                  Atualizar Espera
                </Button>
              ) : (
                <>
                  <Input
                    type="number"
                    value={waitingMinutes}
                    onChange={(e) => setWaitingMinutes(parseInt(e.target.value) || 0)}
                    placeholder="Min"
                    className="w-16 h-8"
                    min="0"
                  />
                  <Button size="sm" onClick={handleWaitingUpdate} className="bg-orange-600 h-8">
                    OK
                  </Button>
                </>
              )}
              <Button 
                size="sm" 
                onClick={handleDeliveryAttempt}
                className="bg-green-600 hover:bg-green-700"
                disabled={delivery.pin_bloqueado}
              >
                Entregar
              </Button>
            </div>
          )}

          {/* PIN Validation Modal */}
          {showPinModal && (
            <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
              <div className="bg-white rounded-lg p-6 w-full max-w-md">
                <div className="flex items-center gap-2 mb-4">
                  <Shield className="h-6 w-6 text-blue-600" />
                  <h3 className="text-lg font-semibold">Validar PIN de Entrega</h3>
                </div>
                
                <p className="text-sm text-slate-600 mb-4">
                  Solicite ao cliente o PIN de 4 dígitos para confirmar a entrega:
                </p>
                
                <div className="mb-4">
                  <Input
                    type="text"
                    value={pin}
                    onChange={(e) => {
                      const value = e.target.value.replace(/[^A-Za-z0-9]/g, '').substring(0, 4);
                      setPin(value.toUpperCase());
                      setPinError('');
                    }}
                    placeholder="Digite o PIN"
                    className="text-center text-lg font-mono tracking-wider"
                    maxLength="4"
                    autoFocus
                  />
                  {pinError && (
                    <p className="text-red-500 text-sm mt-1">{pinError}</p>
                  )}
                  {pinAttempts > 0 && (
                    <p className="text-orange-600 text-sm mt-1">
                      {pinAttempts} tentativa(s) - {3 - pinAttempts} restantes
                    </p>
                  )}
                </div>
                
                <div className="flex gap-2">
                  <Button
                    onClick={handlePinValidation}
                    disabled={pinLoading || pin.length !== 4}
                    className="flex-1"
                  >
                    {pinLoading ? 'Validando...' : 'Validar PIN'}
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => {
                      setShowPinModal(false);
                      setPin('');
                      setPinError('');
                    }}
                    disabled={pinLoading}
                  >
                    Cancelar
                  </Button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {delivery.description && (
        <div className="mt-4 pt-4 border-t border-slate-100">
          <div className="text-sm font-medium text-slate-700 mb-1">Observações</div>
          <div className="text-sm text-slate-600">{delivery.description}</div>
        </div>
      )}
    </div>
  );
}

// Motoboy Registration Component
function MotoboyRegistration({ onBack, onRegister }) {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    cnh: '',
    moto_model: '',
    moto_color: '',
    license_plate: '',
    base_city: '',
    bank_info: {
      bank: '',
      agency: '',
      account: '',
      pix_key: ''
    },
    profile_photo: null,
    moto_photo: null,
    cnh_photo: null,
    moto_document: null
  });
  
  const [loading, setLoading] = useState(false);
  const [currentStep, setCurrentStep] = useState(1);
  const [message, setMessage] = useState('');

  const CITIES = ["Araçariguama", "São Roque", "Mairinque", "Alumínio", "Ibiúna"];
  const BANKS = ["Banco do Brasil", "Caixa", "Bradesco", "Itaú", "Santander", "Nubank", "Inter", "C6 Bank", "PicPay"];
  const MOTO_MODELS = ["Honda CG 160", "Honda CB 600F", "Yamaha YBR 150", "Suzuki Intruder 125", "Honda PCX 150", "Yamaha Fazer 250", "Outro"];
  const COLORS = ["Branca", "Preta", "Vermelha", "Azul", "Prata", "Amarela", "Verde", "Outra"];

  const handleInputChange = (field, value) => {
    if (field.includes('.')) {
      const [parent, child] = field.split('.');
      setFormData(prev => ({
        ...prev,
        [parent]: {
          ...prev[parent],
          [child]: value
        }
      }));
    } else {
      setFormData(prev => ({
        ...prev,
        [field]: value
      }));
    }
  };

  const handleFileUpload = (field, file) => {
    setFormData(prev => ({
      ...prev,
      [field]: file
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');

    try {
      // Simulate registration process
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      setMessage({
        type: 'success',
        text: 'Cadastro realizado com sucesso! Aguarde análise dos documentos.'
      });

      // Auto login after successful registration
      setTimeout(() => {
        onRegister('motoboy');
      }, 2000);
      
    } catch (error) {
      setMessage({
        type: 'error',
        text: 'Erro ao realizar cadastro. Tente novamente.'
      });
    } finally {
      setLoading(false);
    }
  };

  const nextStep = () => {
    if (currentStep < 4) setCurrentStep(currentStep + 1);
  };

  const prevStep = () => {
    if (currentStep > 1) setCurrentStep(currentStep - 1);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 via-blue-800 to-blue-900">
      <div className="relative max-w-4xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-3 mb-6">
            <Button 
              onClick={onBack}
              variant="outline" 
              className="absolute left-4 top-4 border-white/20 text-white hover:bg-white/10"
            >
              ← Voltar
            </Button>
            <div className="bg-gradient-to-r from-blue-500 to-purple-600 p-3 rounded-2xl">
              <Motorcycle className="h-12 w-12 text-white" />
            </div>
          </div>
          <h1 className="text-4xl font-bold text-white mb-4">Cadastro de Motoboy</h1>
          <p className="text-blue-200">Junte-se ao <span translate="no">SrBoy</span> e faça parte do sistema de entregas mais justo da região</p>
          
          {/* Progress Steps */}
          <div className="flex justify-center mt-8 mb-8">
            <div className="flex items-center space-x-4">
              {[1, 2, 3, 4].map((step) => (
                <div key={step} className="flex items-center">
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold ${
                    step <= currentStep 
                      ? 'bg-green-500 text-white' 
                      : 'bg-blue-700 text-blue-200'
                  }`}>
                    {step}
                  </div>
                  {step < 4 && (
                    <div className={`w-16 h-1 mx-2 ${
                      step < currentStep ? 'bg-green-500' : 'bg-blue-700'
                    }`}></div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Form */}
        <Card className="bg-white/10 backdrop-blur-sm border-white/20">
          <CardContent className="p-8">
            <form onSubmit={handleSubmit}>
              
              {/* Step 1: Personal Information */}
              {currentStep === 1 && (
                <div className="space-y-6">
                  <h2 className="text-2xl font-semibold text-white mb-6">Informações Pessoais</h2>
                  
                  <div className="grid md:grid-cols-2 gap-6">
                    <div>
                      <label className="block text-sm font-medium text-blue-100 mb-2">Nome Completo *</label>
                      <Input
                        value={formData.name}
                        onChange={(e) => handleInputChange('name', e.target.value)}
                        placeholder="Seu nome completo"
                        className="bg-white/20 border-white/30 text-white placeholder-blue-200"
                        required
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-blue-100 mb-2">Email *</label>
                      <Input
                        type="email"
                        value={formData.email}
                        onChange={(e) => handleInputChange('email', e.target.value)}
                        placeholder="seu@email.com"
                        className="bg-white/20 border-white/30 text-white placeholder-blue-200"
                        required
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-blue-100 mb-2">Telefone/WhatsApp *</label>
                      <Input
                        value={formData.phone}
                        onChange={(e) => handleInputChange('phone', e.target.value)}
                        placeholder="(11) 99999-9999"
                        className="bg-white/20 border-white/30 text-white placeholder-blue-200"
                        required
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-blue-100 mb-2">CNH *</label>
                      <Input
                        value={formData.cnh}
                        onChange={(e) => handleInputChange('cnh', e.target.value)}
                        placeholder="Número da CNH"
                        className="bg-white/20 border-white/30 text-white placeholder-blue-200"
                        required
                      />
                    </div>
                    
                    <div className="md:col-span-2">
                      <label className="block text-sm font-medium text-blue-100 mb-2">Cidade Base *</label>
                      <select
                        value={formData.base_city}
                        onChange={(e) => handleInputChange('base_city', e.target.value)}
                        className="w-full px-3 py-2 bg-white/20 border border-white/30 rounded-lg text-white focus:ring-2 focus:ring-blue-500"
                        required
                      >
                        <option value="" className="text-slate-800">Selecione sua cidade</option>
                        {CITIES.map(city => (
                          <option key={city} value={city} className="text-slate-800">{city}</option>
                        ))}
                      </select>
                    </div>
                  </div>
                </div>
              )}

              {/* Step 2: Motorcycle Information */}
              {currentStep === 2 && (
                <div className="space-y-6">
                  <h2 className="text-2xl font-semibold text-white mb-6">Informações da Moto</h2>
                  
                  <div className="grid md:grid-cols-2 gap-6">
                    <div>
                      <label className="block text-sm font-medium text-blue-100 mb-2">Modelo da Moto *</label>
                      <select
                        value={formData.moto_model}
                        onChange={(e) => handleInputChange('moto_model', e.target.value)}
                        className="w-full px-3 py-2 bg-white/20 border border-white/30 rounded-lg text-white focus:ring-2 focus:ring-blue-500"
                        required
                      >
                        <option value="" className="text-slate-800">Selecione o modelo</option>
                        {MOTO_MODELS.map(model => (
                          <option key={model} value={model} className="text-slate-800">{model}</option>
                        ))}
                      </select>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-blue-100 mb-2">Cor da Moto *</label>
                      <select
                        value={formData.moto_color}
                        onChange={(e) => handleInputChange('moto_color', e.target.value)}
                        className="w-full px-3 py-2 bg-white/20 border border-white/30 rounded-lg text-white focus:ring-2 focus:ring-blue-500"
                        required
                      >
                        <option value="" className="text-slate-800">Selecione a cor</option>
                        {COLORS.map(color => (
                          <option key={color} value={color} className="text-slate-800">{color}</option>
                        ))}
                      </select>
                    </div>
                    
                    <div className="md:col-span-2">
                      <label className="block text-sm font-medium text-blue-100 mb-2">Placa da Moto *</label>
                      <Input
                        value={formData.license_plate}
                        onChange={(e) => handleInputChange('license_plate', e.target.value.toUpperCase())}
                        placeholder="ABC-1234"
                        className="bg-white/20 border-white/30 text-white placeholder-blue-200"
                        maxLength={8}
                        required
                      />
                    </div>
                  </div>
                </div>
              )}

              {/* Step 3: Documents Upload */}
              {currentStep === 3 && (
                <div className="space-y-6">
                  <h2 className="text-2xl font-semibold text-white mb-6">Documentos</h2>
                  <p className="text-blue-200 mb-6">Faça upload dos documentos necessários. Todos os arquivos são seguros e criptografados.</p>
                  
                  <div className="grid md:grid-cols-2 gap-6">
                    <div className="space-y-4">
                      <label className="block text-sm font-medium text-blue-100">Foto de Perfil *</label>
                      <div className="border-2 border-dashed border-white/30 rounded-lg p-6 text-center bg-white/5">
                        <input
                          type="file"
                          accept="image/*"
                          onChange={(e) => handleFileUpload('profile_photo', e.target.files[0])}
                          className="hidden"
                          id="profile_photo"
                        />
                        <label htmlFor="profile_photo" className="cursor-pointer">
                          <div className="text-blue-200 mb-2">
                            <Users className="h-12 w-12 mx-auto mb-2" />
                            <p>Clique para fazer upload</p>
                            <p className="text-sm">Selfie nítida</p>
                          </div>
                        </label>
                        {formData.profile_photo && (
                          <p className="text-green-400 text-sm mt-2">✓ {formData.profile_photo.name}</p>
                        )}
                      </div>
                    </div>

                    <div className="space-y-4">
                      <label className="block text-sm font-medium text-blue-100">Foto da CNH *</label>
                      <div className="border-2 border-dashed border-white/30 rounded-lg p-6 text-center bg-white/5">
                        <input
                          type="file"
                          accept="image/*"
                          onChange={(e) => handleFileUpload('cnh_photo', e.target.files[0])}
                          className="hidden"
                          id="cnh_photo"
                        />
                        <label htmlFor="cnh_photo" className="cursor-pointer">
                          <div className="text-blue-200 mb-2">
                            <FileText className="h-12 w-12 mx-auto mb-2" />
                            <p>Clique para fazer upload</p>
                            <p className="text-sm">CNH frente e verso</p>
                          </div>
                        </label>
                        {formData.cnh_photo && (
                          <p className="text-green-400 text-sm mt-2">✓ {formData.cnh_photo.name}</p>
                        )}
                      </div>
                    </div>

                    <div className="space-y-4">
                      <label className="block text-sm font-medium text-blue-100">Foto da Moto *</label>
                      <div className="border-2 border-dashed border-white/30 rounded-lg p-6 text-center bg-white/5">
                        <input
                          type="file"
                          accept="image/*"
                          onChange={(e) => handleFileUpload('moto_photo', e.target.files[0])}
                          className="hidden"
                          id="moto_photo"
                        />
                        <label htmlFor="moto_photo" className="cursor-pointer">
                          <div className="text-blue-200 mb-2">
                            <Motorcycle className="h-12 w-12 mx-auto mb-2" />
                            <p>Clique para fazer upload</p>
                            <p className="text-sm">Foto lateral da moto</p>
                          </div>
                        </label>
                        {formData.moto_photo && (
                          <p className="text-green-400 text-sm mt-2">✓ {formData.moto_photo.name}</p>
                        )}
                      </div>
                    </div>

                    <div className="space-y-4">
                      <label className="block text-sm font-medium text-blue-100">Documento da Moto *</label>
                      <div className="border-2 border-dashed border-white/30 rounded-lg p-6 text-center bg-white/5">
                        <input
                          type="file"
                          accept="image/*,.pdf"
                          onChange={(e) => handleFileUpload('moto_document', e.target.files[0])}
                          className="hidden"
                          id="moto_document"
                        />
                        <label htmlFor="moto_document" className="cursor-pointer">
                          <div className="text-blue-200 mb-2">
                            <Receipt className="h-12 w-12 mx-auto mb-2" />
                            <p>Clique para fazer upload</p>
                            <p className="text-sm">CRLV atualizado</p>
                          </div>
                        </label>
                        {formData.moto_document && (
                          <p className="text-green-400 text-sm mt-2">✓ {formData.moto_document.name}</p>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Step 4: Banking Information */}
              {currentStep === 4 && (
                <div className="space-y-6">
                  <h2 className="text-2xl font-semibold text-white mb-6">Dados Bancários</h2>
                  <p className="text-blue-200 mb-6">Para receber seus pagamentos via PIX no final do dia</p>
                  
                  <div className="grid md:grid-cols-2 gap-6">
                    <div>
                      <label className="block text-sm font-medium text-blue-100 mb-2">Banco *</label>
                      <select
                        value={formData.bank_info.bank}
                        onChange={(e) => handleInputChange('bank_info.bank', e.target.value)}
                        className="w-full px-3 py-2 bg-white/20 border border-white/30 rounded-lg text-white focus:ring-2 focus:ring-blue-500"
                        required
                      >
                        <option value="" className="text-slate-800">Selecione o banco</option>
                        {BANKS.map(bank => (
                          <option key={bank} value={bank} className="text-slate-800">{bank}</option>
                        ))}
                      </select>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-blue-100 mb-2">Agência</label>
                      <Input
                        value={formData.bank_info.agency}
                        onChange={(e) => handleInputChange('bank_info.agency', e.target.value)}
                        placeholder="0001"
                        className="bg-white/20 border-white/30 text-white placeholder-blue-200"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-blue-100 mb-2">Conta</label>
                      <Input
                        value={formData.bank_info.account}
                        onChange={(e) => handleInputChange('bank_info.account', e.target.value)}
                        placeholder="12345-6"
                        className="bg-white/20 border-white/30 text-white placeholder-blue-200"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-blue-100 mb-2">Chave PIX *</label>
                      <Input
                        value={formData.bank_info.pix_key}
                        onChange={(e) => handleInputChange('bank_info.pix_key', e.target.value)}
                        placeholder="CPF, email ou telefone"
                        className="bg-white/20 border-white/30 text-white placeholder-blue-200"
                        required
                      />
                    </div>
                  </div>

                  <div className="bg-blue-900/50 p-4 rounded-lg border border-blue-700">
                    <h3 className="text-white font-semibold mb-2">💰 Como funciona o pagamento no <span translate="no">SrBoy</span>:</h3>
                    <ul className="text-blue-200 text-sm space-y-1">
                      <li>• Você recebe automaticamente via PIX no final de cada dia</li>
                      <li>• Ganho por entrega: Valor total - Taxa fixa de R$ 2,00</li>
                      <li>• Acima de 4km: Você recebe R$ 8,00 + R$ 2,00 por km</li>
                      <li>• Taxa de espera: R$ 1,00/min após 10 minutos (integral para você)</li>
                    </ul>
                  </div>
                </div>
              )}

              {/* Message Display */}
              {message && (
                <Alert className={`mb-6 ${message.type === 'success' ? 'border-green-500 bg-green-900/20' : 'border-red-500 bg-red-900/20'}`}>
                  <AlertDescription className={message.type === 'success' ? 'text-green-200' : 'text-red-200'}>
                    {message.text}
                  </AlertDescription>
                </Alert>
              )}

              {/* Navigation Buttons */}
              <div className="flex justify-between mt-8">
                <Button
                  type="button"
                  onClick={prevStep}
                  disabled={currentStep === 1}
                  variant="outline"
                  className="border-white/30 text-white hover:bg-white/10"
                >
                  ← Anterior
                </Button>

                {currentStep < 4 ? (
                  <Button
                    type="button"
                    onClick={nextStep}
                    className="bg-green-600 hover:bg-green-700 text-white"
                  >
                    Próximo →
                  </Button>
                ) : (
                  <Button
                    type="submit"
                    disabled={loading}
                    className="bg-green-600 hover:bg-green-700 text-white"
                  >
                    {loading ? 'Cadastrando...' : 'Finalizar Cadastro'}
                  </Button>
                )}
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

// Lojista Registration Component
function LojistaRegistration({ onBack, onRegister }) {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    fantasy_name: '',
    cnpj: '',
    phone: '',
    address: {
      street: '',
      number: '',
      neighborhood: '',
      city: '',
      zipcode: ''
    },
    category: '',
    business_hours: {
      monday: { open: '08:00', close: '18:00', closed: false },
      tuesday: { open: '08:00', close: '18:00', closed: false },
      wednesday: { open: '08:00', close: '18:00', closed: false },
      thursday: { open: '08:00', close: '18:00', closed: false },
      friday: { open: '08:00', close: '18:00', closed: false },
      saturday: { open: '08:00', close: '18:00', closed: false },
      sunday: { open: '08:00', close: '18:00', closed: true }
    },
    description: '',
    instagram: '',
    logo: null
  });
  
  const [loading, setLoading] = useState(false);
  const [currentStep, setCurrentStep] = useState(1);
  const [message, setMessage] = useState('');

  const CITIES = ["Araçariguama", "São Roque", "Mairinque", "Alumínio", "Ibiúna"];
  const CATEGORIES = [
    "Farmácia", "Restaurante", "Loja de Roupas", "Eletrônicos", "Supermercado",
    "Petshop", "Perfumaria", "Livraria", "Loja de Presentes", "Açougue",
    "Padaria", "Floricultura", "Ótica", "Casa de Construção", "Outro"
  ];

  const WEEKDAYS = {
    monday: 'Segunda-feira',
    tuesday: 'Terça-feira', 
    wednesday: 'Quarta-feira',
    thursday: 'Quinta-feira',
    friday: 'Sexta-feira',
    saturday: 'Sábado',
    sunday: 'Domingo'
  };

  const handleInputChange = (field, value) => {
    if (field.includes('.')) {
      const parts = field.split('.');
      if (parts.length === 2) {
        const [parent, child] = parts;
        setFormData(prev => ({
          ...prev,
          [parent]: {
            ...prev[parent],
            [child]: value
          }
        }));
      } else if (parts.length === 3) {
        const [parent, child, grandchild] = parts;
        setFormData(prev => ({
          ...prev,
          [parent]: {
            ...prev[parent],
            [child]: {
              ...prev[parent][child],
              [grandchild]: value
            }
          }
        }));
      }
    } else {
      setFormData(prev => ({
        ...prev,
        [field]: value
      }));
    }
  };

  const handleFileUpload = (field, file) => {
    setFormData(prev => ({
      ...prev,
      [field]: file
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');

    try {
      // Simulate registration process
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      setMessage({
        type: 'success',
        text: 'Cadastro realizado com sucesso! Sua loja será analisada em até 24h.'
      });

      // Auto login after successful registration
      setTimeout(() => {
        onRegister('lojista');
      }, 2000);
      
    } catch (error) {
      setMessage({
        type: 'error',
        text: 'Erro ao realizar cadastro. Tente novamente.'
      });
    } finally {
      setLoading(false);
    }
  };

  const nextStep = () => {
    if (currentStep < 3) setCurrentStep(currentStep + 1);
  };

  const prevStep = () => {
    if (currentStep > 1) setCurrentStep(currentStep - 1);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-purple-800 to-purple-900">
      <div className="relative max-w-4xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-3 mb-6">
            <Button 
              onClick={onBack}
              variant="outline" 
              className="absolute left-4 top-4 border-white/20 text-white hover:bg-white/10"
            >
              ← Voltar
            </Button>
            <div className="bg-gradient-to-r from-purple-500 to-pink-600 p-3 rounded-2xl">
              <Store className="h-12 w-12 text-white" />
            </div>
          </div>
          <h1 className="text-4xl font-bold text-white mb-4">Cadastro de Lojista</h1>
          <p className="text-purple-200">Cadastre sua loja no <span translate="no">SrBoy</span> e tenha acesso a entregas rápidas e seguras</p>
          
          {/* Progress Steps */}
          <div className="flex justify-center mt-8 mb-8">
            <div className="flex items-center space-x-4">
              {[1, 2, 3].map((step) => (
                <div key={step} className="flex items-center">
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold ${
                    step <= currentStep 
                      ? 'bg-green-500 text-white' 
                      : 'bg-purple-700 text-purple-200'
                  }`}>
                    {step}
                  </div>
                  {step < 3 && (
                    <div className={`w-16 h-1 mx-2 ${
                      step < currentStep ? 'bg-green-500' : 'bg-purple-700'
                    }`}></div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Form */}
        <Card className="bg-white/10 backdrop-blur-sm border-white/20">
          <CardContent className="p-8">
            <form onSubmit={handleSubmit}>
              
              {/* Step 1: Business Information */}
              {currentStep === 1 && (
                <div className="space-y-6">
                  <h2 className="text-2xl font-semibold text-white mb-6">Informações da Loja</h2>
                  
                  <div className="grid md:grid-cols-2 gap-6">
                    <div>
                      <label className="block text-sm font-medium text-purple-100 mb-2">Nome do Responsável *</label>
                      <Input
                        value={formData.name}
                        onChange={(e) => handleInputChange('name', e.target.value)}
                        placeholder="Seu nome completo"
                        className="bg-white/20 border-white/30 text-white placeholder-purple-200"
                        required
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-purple-100 mb-2">Email *</label>
                      <Input
                        type="email"
                        value={formData.email}
                        onChange={(e) => handleInputChange('email', e.target.value)}
                        placeholder="contato@loja.com"
                        className="bg-white/20 border-white/30 text-white placeholder-purple-200"
                        required
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-purple-100 mb-2">Nome Fantasia *</label>
                      <Input
                        value={formData.fantasy_name}
                        onChange={(e) => handleInputChange('fantasy_name', e.target.value)}
                        placeholder="Nome da sua loja"
                        className="bg-white/20 border-white/30 text-white placeholder-purple-200"
                        required
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-purple-100 mb-2">CNPJ *</label>
                      <Input
                        value={formData.cnpj}
                        onChange={(e) => handleInputChange('cnpj', e.target.value)}
                        placeholder="00.000.000/0001-00"
                        className="bg-white/20 border-white/30 text-white placeholder-purple-200"
                        required
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-purple-100 mb-2">Telefone/WhatsApp *</label>
                      <Input
                        value={formData.phone}
                        onChange={(e) => handleInputChange('phone', e.target.value)}
                        placeholder="(11) 99999-9999"
                        className="bg-white/20 border-white/30 text-white placeholder-purple-200"
                        required
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-purple-100 mb-2">Categoria *</label>
                      <select
                        value={formData.category}
                        onChange={(e) => handleInputChange('category', e.target.value)}
                        className="w-full px-3 py-2 bg-white/20 border border-white/30 rounded-lg text-white focus:ring-2 focus:ring-purple-500"
                        required
                      >
                        <option value="" className="text-slate-800">Selecione a categoria</option>
                        {CATEGORIES.map(category => (
                          <option key={category} value={category} className="text-slate-800">{category}</option>
                        ))}
                      </select>
                    </div>
                    
                    <div className="md:col-span-2">
                      <label className="block text-sm font-medium text-purple-100 mb-2">Instagram (opcional)</label>
                      <Input
                        value={formData.instagram}
                        onChange={(e) => handleInputChange('instagram', e.target.value)}
                        placeholder="@nomedaloja"
                        className="bg-white/20 border-white/30 text-white placeholder-purple-200"
                      />
                    </div>
                    
                    <div className="md:col-span-2">
                      <label className="block text-sm font-medium text-purple-100 mb-2">Descrição da Loja</label>
                      <Textarea
                        value={formData.description}
                        onChange={(e) => handleInputChange('description', e.target.value)}
                        placeholder="Conte um pouco sobre sua loja, produtos, diferenciais..."
                        className="bg-white/20 border-white/30 text-white placeholder-purple-200"
                        rows={3}
                      />
                    </div>
                  </div>
                </div>
              )}

              {/* Step 2: Address Information */}
              {currentStep === 2 && (
                <div className="space-y-6">
                  <h2 className="text-2xl font-semibold text-white mb-6">Endereço da Loja</h2>
                  
                  <div className="grid md:grid-cols-2 gap-6">
                    <div>
                      <label className="block text-sm font-medium text-purple-100 mb-2">CEP *</label>
                      <Input
                        value={formData.address.zipcode}
                        onChange={(e) => handleInputChange('address.zipcode', e.target.value)}
                        placeholder="00000-000"
                        className="bg-white/20 border-white/30 text-white placeholder-purple-200"
                        required
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-purple-100 mb-2">Cidade *</label>
                      <select
                        value={formData.address.city}
                        onChange={(e) => handleInputChange('address.city', e.target.value)}
                        className="w-full px-3 py-2 bg-white/20 border border-white/30 rounded-lg text-white focus:ring-2 focus:ring-purple-500"
                        required
                      >
                        <option value="" className="text-slate-800">Selecione a cidade</option>
                        {CITIES.map(city => (
                          <option key={city} value={city} className="text-slate-800">{city}</option>
                        ))}
                      </select>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-purple-100 mb-2">Rua *</label>
                      <Input
                        value={formData.address.street}
                        onChange={(e) => handleInputChange('address.street', e.target.value)}
                        placeholder="Nome da rua"
                        className="bg-white/20 border-white/30 text-white placeholder-purple-200"
                        required
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-purple-100 mb-2">Número *</label>
                      <Input
                        value={formData.address.number}
                        onChange={(e) => handleInputChange('address.number', e.target.value)}
                        placeholder="123"
                        className="bg-white/20 border-white/30 text-white placeholder-purple-200"
                        required
                      />
                    </div>
                    
                    <div className="md:col-span-2">
                      <label className="block text-sm font-medium text-purple-100 mb-2">Bairro *</label>
                      <Input
                        value={formData.address.neighborhood}
                        onChange={(e) => handleInputChange('address.neighborhood', e.target.value)}
                        placeholder="Nome do bairro"
                        className="bg-white/20 border-white/30 text-white placeholder-purple-200"
                        required
                      />
                    </div>
                  </div>
                </div>
              )}

              {/* Step 3: Business Hours & Logo */}
              {currentStep === 3 && (
                <div className="space-y-6">
                  <h2 className="text-2xl font-semibold text-white mb-6">Horário de Funcionamento</h2>
                  
                  <div className="space-y-4">
                    {Object.entries(WEEKDAYS).map(([day, dayName]) => (
                      <div key={day} className="flex items-center gap-4 p-4 bg-white/5 rounded-lg">
                        <div className="w-32">
                          <span className="text-purple-100 font-medium">{dayName}</span>
                        </div>
                        
                        <div className="flex items-center gap-4">
                          <label className="flex items-center gap-2">
                            <input
                              type="checkbox"
                              checked={formData.business_hours[day].closed}
                              onChange={(e) => handleInputChange(`business_hours.${day}.closed`, e.target.checked)}
                              className="rounded"
                            />
                            <span className="text-purple-200 text-sm">Fechado</span>
                          </label>
                          
                          {!formData.business_hours[day].closed && (
                            <>
                              <div className="flex items-center gap-2">
                                <span className="text-purple-200 text-sm">Das</span>
                                <input
                                  type="time"
                                  value={formData.business_hours[day].open}
                                  onChange={(e) => handleInputChange(`business_hours.${day}.open`, e.target.value)}
                                  className="bg-white/20 border border-white/30 rounded px-2 py-1 text-white"
                                />
                              </div>
                              
                              <div className="flex items-center gap-2">
                                <span className="text-purple-200 text-sm">às</span>
                                <input
                                  type="time"
                                  value={formData.business_hours[day].close}
                                  onChange={(e) => handleInputChange(`business_hours.${day}.close`, e.target.value)}
                                  className="bg-white/20 border border-white/30 rounded px-2 py-1 text-white"
                                />
                              </div>
                            </>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Logo Upload */}
                  <div className="mt-8">
                    <h3 className="text-xl font-semibold text-white mb-4">Logo da Loja (opcional)</h3>
                    <div className="border-2 border-dashed border-white/30 rounded-lg p-8 text-center bg-white/5">
                      <input
                        type="file"
                        accept="image/*"
                        onChange={(e) => handleFileUpload('logo', e.target.files[0])}
                        className="hidden"
                        id="logo"
                      />
                      <label htmlFor="logo" className="cursor-pointer">
                        <div className="text-purple-200 mb-4">
                          <Store className="h-16 w-16 mx-auto mb-4" />
                          <p className="text-lg">Clique para fazer upload do logo</p>
                          <p className="text-sm">PNG, JPG até 5MB</p>
                        </div>
                      </label>
                      {formData.logo && (
                        <p className="text-green-400 text-sm mt-4">✓ {formData.logo.name}</p>
                      )}
                    </div>
                  </div>

                  <div className="bg-purple-900/50 p-6 rounded-lg border border-purple-700">
                    <h3 className="text-white font-semibold mb-3">💼 Como funciona para lojistas no <span translate="no">SrBoy</span>:</h3>
                    <ul className="text-purple-200 text-sm space-y-2">
                      <li>• <strong>Cadastro gratuito</strong> - sem mensalidades ou taxas de adesão</li>
                      <li>• <strong>Recarregue sua carteira</strong> via PIX ou cartão (Mercado Pago)</li>
                      <li>• <strong>Preços transparentes:</strong> R$ 10,00 base + R$ 2,00/km</li>
                      <li>• <strong>Matching automático</strong> com o melhor motoboy disponível</li>
                      <li>• <strong>Comprovante digital</strong> de todas as entregas</li>
                      <li>• <strong>Acompanhamento em tempo real</strong> via mapa</li>
                    </ul>
                  </div>
                </div>
              )}

              {/* Message Display */}
              {message && (
                <Alert className={`mb-6 ${message.type === 'success' ? 'border-green-500 bg-green-900/20' : 'border-red-500 bg-red-900/20'}`}>
                  <AlertDescription className={message.type === 'success' ? 'text-green-200' : 'text-red-200'}>
                    {message.text}
                  </AlertDescription>
                </Alert>
              )}

              {/* Navigation Buttons */}
              <div className="flex justify-between mt-8">
                <Button
                  type="button"
                  onClick={prevStep}
                  disabled={currentStep === 1}
                  variant="outline"
                  className="border-white/30 text-white hover:bg-white/10"
                >
                  ← Anterior
                </Button>

                {currentStep < 3 ? (
                  <Button
                    type="button"
                    onClick={nextStep}
                    className="bg-green-600 hover:bg-green-700 text-white"
                  >
                    Próximo →
                  </Button>
                ) : (
                  <Button
                    type="submit"
                    disabled={loading}
                    className="bg-green-600 hover:bg-green-700 text-white"
                  >
                    {loading ? 'Cadastrando...' : 'Finalizar Cadastro'}
                  </Button>
                )}
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default App;