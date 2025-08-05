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
  Phone
} from 'lucide-react';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

function App() {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(false);
  const [deliveries, setDeliveries] = useState([]);
  const [rankings, setRankings] = useState([]);
  const [activeTab, setActiveTab] = useState('dashboard');

  // Cities served
  const CITIES = ["Araçariguama", "São Roque", "Mairinque", "Alumínio", "Ibiúna"];

  useEffect(() => {
    if (token) {
      fetchUserProfile();
      fetchDeliveries();
      fetchRankings();
    }
  }, [token]);

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

  if (!user) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
        {/* Hero Section */}
        <div className="relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-r from-blue-600/20 to-purple-600/20"></div>
          <div className="relative max-w-7xl mx-auto px-4 py-20">
            <div className="text-center">
              <div className="flex justify-center mb-8">
                <div className="bg-gradient-to-r from-blue-500 to-purple-600 p-4 rounded-2xl">
                  <Motorcycle className="h-16 w-16 text-white" />
                </div>
              </div>
              <h1 className="text-6xl font-bold text-white mb-6">
                SrBoy
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
                    onClick={() => handleGoogleAuth('motoboy')}
                    disabled={loading}
                    className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-6 text-lg rounded-xl flex items-center gap-3"
                  >
                    <Motorcycle className="h-6 w-6" />
                    {loading ? 'Carregando...' : 'Entrar como Motoboy'}
                  </Button>
                  <Button 
                    onClick={() => handleGoogleAuth('lojista')}
                    disabled={loading}
                    className="bg-purple-600 hover:bg-purple-700 text-white px-8 py-6 text-lg rounded-xl flex items-center gap-3"
                  >
                    <Store className="h-6 w-6" />
                    {loading ? 'Carregando...' : 'Entrar como Lojista'}
                  </Button>
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
              <div className="bg-gradient-to-r from-blue-500 to-purple-600 p-2 rounded-lg">
                <Motorcycle className="h-6 w-6 text-white" />
              </div>
              <h1 className="text-2xl font-bold text-slate-900">SrBoy</h1>
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
          <TabsList className="grid w-full max-w-md mx-auto grid-cols-3 bg-slate-100">
            <TabsTrigger value="dashboard" className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4" />
              Dashboard
            </TabsTrigger>
            <TabsTrigger value="deliveries" className="flex items-center gap-2">
              <Truck className="h-4 w-4" />
              Entregas
            </TabsTrigger>
            <TabsTrigger value="rankings" className="flex items-center gap-2">
              <Star className="h-4 w-4" />
              Rankings
            </TabsTrigger>
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
        </Tabs>
      </div>
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
                onClick={() => onUpdateStatus(delivery.id, 'delivered')}
                className="bg-green-600 hover:bg-green-700"
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
                onClick={() => onUpdateStatus(delivery.id, 'delivered')}
                className="bg-green-600 hover:bg-green-700"
              >
                Entregar
              </Button>
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

export default App;