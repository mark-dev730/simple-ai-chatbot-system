import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { chatAPI, adminAPI } from '../services/api';

export const Admin = () => {
  const [activeTab, setActiveTab] = useState('users');
  const [users, setUsers] = useState([]);
  const [usersList, setUsersList] = useState([]);
  const [models, setModels] = useState([]);
  const [stats, setStats] = useState({ 
    totalUsers: 0, 
    activeUsers: 0,
    totalSessions: 0, 
    totalMessages: 0,
    totalModels: 0 
  });
  const [loading, setLoading] = useState(true);
  const [ollamaStatus, setOllamaStatus] = useState(false);
  
  const { user: currentUser, logout } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      await Promise.all([
        loadUsers(),
        loadModels(),
        loadStats(),
        checkOllamaStatus(),
      ]);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadUsers = async () => {
    try {
      const [countResponse, listResponse] = await Promise.all([
        adminAPI.getUsersCount(),
        adminAPI.listUsers(0, 100)
      ]);
      
      setStats(prev => ({ 
        ...prev, 
        totalUsers: countResponse.data.total,
        activeUsers: countResponse.data.active
      }));
      setUsersList(listResponse.data.users);
    } catch (error) {
      console.error('Failed to load users:', error);
    }
  };

  const loadModels = async () => {
    try {
      const response = await chatAPI.listModels();
      setModels(response.data.models);
    } catch (error) {
      console.error('Failed to load models:', error);
    }
  };

  const loadStats = async () => {
    try {
      const response = await adminAPI.getStats();
      setStats(prev => ({
        ...prev,
        totalUsers: response.data.users,
        totalSessions: response.data.sessions,
        totalMessages: response.data.messages,
        totalModels: response.data.models
      }));
    } catch (error) {
      console.error('Failed to load stats:', error);
    }
  };

  const checkOllamaStatus = async () => {
    try {
      const response = await chatAPI.checkOllamaStatus();
      setOllamaStatus(response.data.connected);
    } catch (error) {
      setOllamaStatus(false);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const handleToggleUser = async (userId) => {
    try {
      await adminAPI.toggleUserStatus(userId);
      await loadUsers();
    } catch (error) {
      alert(error.response?.data?.detail || 'Failed to update user status');
    }
  };

  const handleAccessChange = async (userId, level) => {
    try {
      await adminAPI.updateUserAccess(userId, Number(level));
      await loadUsers();
    } catch (error) {
      alert(error.response?.data?.detail || 'Failed to update access level');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Admin Dashboard</h1>
              <p className="text-sm text-gray-500">Manage your AI Chatbot System</p>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={() => navigate('/chat')}
                className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-md transition"
              >
                Back to Chat
              </button>
              <button
                onClick={handleLogout}
                className="px-4 py-2 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-md transition"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Stats Overview */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500">Total Users</p>
                <p className="text-3xl font-bold text-gray-900">{stats.totalUsers}</p>
              </div>
              <div className="w-12 h-12 bg-indigo-100 rounded-full flex items-center justify-center">
                <svg className="w-6 h-6 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                </svg>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500">Total Messages</p>
                <p className="text-3xl font-bold text-gray-900">{stats.totalMessages}</p>
              </div>
              <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500">Available Models</p>
                <p className="text-3xl font-bold text-gray-900">{stats.totalModels}</p>
              </div>
              <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
                <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
                </svg>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500">Ollama Status</p>
                <p className={`text-xl font-bold ${ollamaStatus ? 'text-green-600' : 'text-red-600'}`}>
                  {ollamaStatus ? 'Connected' : 'Offline'}
                </p>
              </div>
              <div className={`w-12 h-12 ${ollamaStatus ? 'bg-green-100' : 'bg-red-100'} rounded-full flex items-center justify-center`}>
                <div className={`w-3 h-3 rounded-full ${ollamaStatus ? 'bg-green-600' : 'bg-red-600'}`}></div>
              </div>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="bg-white rounded-lg shadow">
          <div className="border-b border-gray-200">
            <nav className="flex -mb-px">
              <button
                onClick={() => setActiveTab('users')}
                className={`px-6 py-3 text-sm font-medium border-b-2 transition ${
                  activeTab === 'users'
                    ? 'border-indigo-600 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Users
              </button>
              <button
                onClick={() => setActiveTab('models')}
                className={`px-6 py-3 text-sm font-medium border-b-2 transition ${
                  activeTab === 'models'
                    ? 'border-indigo-600 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Models
              </button>
              <button
                onClick={() => setActiveTab('system')}
                className={`px-6 py-3 text-sm font-medium border-b-2 transition ${
                  activeTab === 'system'
                    ? 'border-indigo-600 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                System Info
              </button>
            </nav>
          </div>

          <div className="p-6">
            {loading ? (
              <div className="text-center py-12">
                <div className="text-gray-500">Loading...</div>
              </div>
            ) : (
              <>
                {activeTab === 'users' && (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">User Management</h3>
                    <div className="mb-6 flex gap-4">
                      <div className="px-4 py-2 bg-gray-100 rounded-lg">
                        <span className="text-sm text-gray-600">Total: </span>
                        <span className="font-semibold text-gray-900">{stats.totalUsers}</span>
                      </div>
                      <div className="px-4 py-2 bg-green-100 rounded-lg">
                        <span className="text-sm text-gray-600">Active: </span>
                        <span className="font-semibold text-green-900">{stats.activeUsers}</span>
                      </div>
                    </div>
                    
                    {usersList.length === 0 ? (
                      <p className="text-gray-500">No users found</p>
                    ) : (
                      <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-200">
                          <thead className="bg-gray-50">
                            <tr>
                              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ID</th>
                              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Username</th>
                              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Email</th>
                              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Access Level</th>
                              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Created</th>
                              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                            </tr>
                          </thead>
                          <tbody className="bg-white divide-y divide-gray-200">
                            {usersList.map((user) => (
                              <tr key={user.user_id}>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{user.user_id}</td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{user.username}</td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{user.email}</td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm">
                                  <select
                                    value={user.access_level}
                                    disabled={user.user_id === currentUser?.user_id}
                                    onChange={(e) => handleAccessChange(user.user_id, e.target.value)}
                                    className="border border-gray-300 rounded-md px-2 py-1 text-xs disabled:opacity-50"
                                  >
                                    <option value={0}>User</option>
                                    <option value={1}>Moderator</option>
                                    <option value={2}>Admin</option>
                                  </select>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm">
                                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                                    user.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                                  }`}>
                                    {user.is_active ? 'Active' : 'Inactive'}
                                  </span>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                  {user.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm">
                                  <button
                                    onClick={() => handleToggleUser(user.user_id)}
                                    disabled={user.user_id === currentUser?.user_id}
                                    className="px-3 py-1 text-xs rounded-md bg-gray-100 hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed transition"
                                  >
                                    {user.is_active ? 'Deactivate' : 'Activate'}
                                  </button>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </div>
                )}

                {activeTab === 'models' && (
                  <div>
                    <div className="flex justify-between items-center mb-4">
                      <h3 className="text-lg font-semibold text-gray-900">AI Models</h3>
                      <button
                        onClick={loadModels}
                        className="px-4 py-2 text-sm bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition"
                      >
                        Refresh
                      </button>
                    </div>
                    
                    {models.length === 0 ? (
                      <p className="text-gray-500">No models available</p>
                    ) : (
                      <div className="space-y-4">
                        {models.map((model) => (
                          <div
                            key={model.name}
                            className="flex items-center justify-between p-4 border border-gray-200 rounded-lg"
                          >
                            <div>
                              <h4 className="font-medium text-gray-900">{model.name}</h4>
                              <p className="text-sm text-gray-500">
                                Size: {model.size ? `${(model.size / 1024 / 1024 / 1024).toFixed(2)} GB` : 'Unknown'}
                              </p>
                            </div>
                            <span className="px-3 py-1 bg-green-100 text-green-800 text-xs font-medium rounded-full">
                              Active
                            </span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {activeTab === 'system' && (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">System Information</h3>
                    <div className="space-y-4">
                      <div className="flex justify-between py-3 border-b border-gray-200">
                        <span className="text-gray-600">Admin User</span>
                        <span className="font-medium text-gray-900">{currentUser?.username}</span>
                      </div>
                      <div className="flex justify-between py-3 border-b border-gray-200">
                        <span className="text-gray-600">Access Level</span>
                        <span className="font-medium text-gray-900">
                          {currentUser?.access_level === 2 ? 'Admin' : 'Unknown'}
                        </span>
                      </div>
                      <div className="flex justify-between py-3 border-b border-gray-200">
                        <span className="text-gray-600">Ollama URL</span>
                        <span className="font-medium text-gray-900">http://localhost:11434</span>
                      </div>
                      <div className="flex justify-between py-3 border-b border-gray-200">
                        <span className="text-gray-600">API URL</span>
                        <span className="font-medium text-gray-900">http://localhost:8000</span>
                      </div>
                      <div className="flex justify-between py-3">
                        <span className="text-gray-600">Frontend Version</span>
                        <span className="font-medium text-gray-900">1.0.0</span>
                      </div>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
