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
  MotorbikeFill as Motorcycle,
  Store,
  Award,
  Navigation
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
      // Demo authentication - replace with Google OAuth integration
      const authData = {
        email: `demo.${userType}@superboy.com`,
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
        fetchDeliveries(); // Refresh deliveries
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
      }
    } catch (error) {
      console.error('Error updating status:', error);
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      pending: 'bg-yellow-100 text-yellow-800',
      matched: 'bg-blue-100 text-blue-800',
      in_progress: 'bg-purple-100 text-purple-800',
      completed: 'bg-green-100 text-green-800',
      cancelled: 'bg-red-100 text-red-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const getStatusText = (status) => {
    const texts = {
      pending: 'Pendente',
      matched: 'Pareado',
      in_progress: 'Em Andamento',
      completed: 'Concluído',
      cancelled: 'Cancelado'
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
                Super Boy
              </h1>
              <p className="text-xl text-slate-300 mb-8 max-w-3xl mx-auto">
                Sistema inteligente de entregas regionais baseado em <span className="text-blue-400 font-semibold">mérito e transparência</span>.
                Conectando lojistas e motoboys de forma justa e eficiente.
              </p>
              
              {/* Key Features */}
              <div className="grid md:grid-cols-3 gap-6 mb-12 max-w-4xl mx-auto">
                <div className="bg-slate-800/50 backdrop-blur-sm p-6 rounded-xl border border-slate-700">
                  <Award className="h-10 w-10 text-blue-400 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-white mb-2">Sistema de Mérito</h3>
                  <p className="text-slate-400 text-sm">Ranking transparente baseado em desempenho, não privilégios</p>
                </div>
                <div className="bg-slate-800/50 backdrop-blur-sm p-6 rounded-xl border border-slate-700">
                  <CreditCard className="h-10 w-10 text-green-400 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-white mb-2">Preços Justos</h3>
                  <p className="text-slate-400 text-sm">R$ 9,00 + R$ 2,50/km. Taxa fixa de R$ 2,00</p>
                </div>
                <div className="bg-slate-800/50 backdrop-blur-sm p-6 rounded-xl border border-slate-700">
                  <Shield className="h-10 w-10 text-purple-400 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-white mb-2">Segurança Ética</h3>
                  <p className="text-slate-400 text-sm">Rastreamento para proteção, não vigilância</p>
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
              <h1 className="text-2xl font-bold text-slate-900">Super Boy</h1>
            </div>
            
            <div className="flex items-center gap-4">
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
                        R$ {(user.wallet_balance || 0).toFixed(2)}
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
                      <CardTitle className="text-sm font-medium text-slate-600">Total de Entregas</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-3xl font-bold text-blue-600">
                        {user.total_deliveries || 0}
                      </div>
                      <p className="text-sm text-slate-500 mt-1">Concluídas com sucesso</p>
                    </CardContent>
                  </Card>
                </>
              )}
              
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium text-slate-600">Status</CardTitle>
                </CardHeader>
                <CardContent>
                  <Badge 
                    className={`${user.user_type === 'motoboy' && user.is_available 
                      ? 'bg-green-100 text-green-800' 
                      : 'bg-slate-100 text-slate-800'
                    }`}
                  >
                    {user.user_type === 'motoboy' 
                      ? (user.is_available ? 'Disponível' : 'Ocupado')
                      : 'Ativo'
                    }
                  </Badge>
                </CardContent>
              </Card>
            </div>

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
                  Ranking de Motoboys
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
                        <div className="text-right">
                          <div className="font-semibold text-purple-600">{ranking.ranking_score}</div>
                          <div className="text-sm text-slate-500">pontos</div>
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

// Create Delivery Form Component
function CreateDeliveryForm({ onCreateDelivery }) {
  const [formData, setFormData] = useState({
    pickup_address: { city: '', address: '', lat: -23.5505, lng: -46.6333 },
    delivery_address: { city: '', address: '', lat: -23.5505, lng: -46.6333 },
    description: ''
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
          ? `Entrega criada! Pareado com ${result.matched_motoboy.name} (Ranking: ${result.matched_motoboy.ranking_score})`
          : 'Entrega criada! Procurando motoboy disponível...'
      });
      
      // Reset form
      setFormData({
        pickup_address: { city: '', address: '', lat: -23.5505, lng: -46.6333 },
        delivery_address: { city: '', address: '', lat: -23.5505, lng: -46.6333 },
        description: ''
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
          Criar Nova Entrega
        </CardTitle>
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

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Descrição (opcional)</label>
            <Textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="Detalhes sobre o produto, instruções especiais..."
              rows={3}
            />
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
            {loading ? 'Criando...' : 'Criar Entrega'}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}

// Delivery Card Component
function DeliveryCard({ delivery, userType, onUpdateStatus }) {
  const getStatusColor = (status) => {
    const colors = {
      pending: 'bg-yellow-100 text-yellow-800',
      matched: 'bg-blue-100 text-blue-800',
      in_progress: 'bg-purple-100 text-purple-800',
      completed: 'bg-green-100 text-green-800',
      cancelled: 'bg-red-100 text-red-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const getStatusText = (status) => {
    const texts = {
      pending: 'Pendente',
      matched: 'Pareado',
      in_progress: 'Em Andamento',
      completed: 'Concluído',
      cancelled: 'Cancelado'
    };
    return texts[status] || status;
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

      <div className="flex items-center justify-between pt-4 border-t border-slate-100">
        <div className="flex items-center gap-4 text-sm text-slate-600">
          <span>{delivery.distance_km}km</span>
          <span>R$ {delivery.total_price.toFixed(2)}</span>
          {delivery.motoboy_id && (
            <span className="text-blue-600">Pareado</span>
          )}
        </div>
        
        {userType === 'motoboy' && delivery.status === 'matched' && (
          <Button 
            size="sm" 
            onClick={() => onUpdateStatus(delivery.id, 'in_progress')}
            className="bg-purple-600 hover:bg-purple-700"
          >
            Iniciar Entrega
          </Button>
        )}
        
        {userType === 'motoboy' && delivery.status === 'in_progress' && (
          <Button 
            size="sm" 
            onClick={() => onUpdateStatus(delivery.id, 'completed')}
            className="bg-green-600 hover:bg-green-700"
          >
            Concluir
          </Button>
        )}
      </div>

      {delivery.description && (
        <div className="mt-4 pt-4 border-t border-slate-100">
          <div className="text-sm font-medium text-slate-700 mb-1">Descrição</div>
          <div className="text-sm text-slate-600">{delivery.description}</div>
        </div>
      )}
    </div>
  );
}

export default App;