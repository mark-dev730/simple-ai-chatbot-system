import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { sessionAPI } from '../services/api';

export const Sidebar = ({ currentSessionId, onSessionSelect, onNewChat }) => {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const { user, logout, isAdmin } = useAuth();
  const navigate = useNavigate();

  const loadSessions = async () => {
    try {
      const response = await sessionAPI.list(true);
      setSessions(response.data.sessions);
    } catch (error) {
      console.error('Failed to load sessions:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSessions();
  }, []);

  const handleNewChat = async () => {
    try {
      const response = await sessionAPI.create();
      const newSession = response.data;
      setSessions([newSession, ...sessions]);
      onNewChat(newSession);
    } catch (error) {
      console.error('Failed to create session:', error);
    }
  };

  const handleDeleteSession = async (sessionId, e) => {
    e.stopPropagation();
    
    if (!confirm('Delete this chat session?')) return;

    try {
      await sessionAPI.delete(sessionId);
      setSessions(sessions.filter(s => s.session_id !== sessionId));
      
      if (currentSessionId === sessionId) {
        onSessionSelect(null);
      }
    } catch (error) {
      console.error('Failed to delete session:', error);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="w-full lg:w-72 bg-gradient-to-b from-gray-900 to-gray-800 text-white flex flex-col h-screen shadow-2xl">
      {/* Header */}
      <div className="p-4 lg:p-5 border-b border-gray-700/50">
        <div className="mb-3 lg:mb-4">
          <h1 className="text-lg lg:text-xl font-bold bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
            McBOT
          </h1>
          <p className="text-xs text-gray-400 mt-1">Powered by Ollama</p>
        </div>
        <button
          onClick={handleNewChat}
          className="w-full bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white font-medium py-2.5 lg:py-3 px-4 rounded-xl transition-all duration-200 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 flex items-center justify-center space-x-2 text-sm lg:text-base"
        >
          <svg className="w-4 h-4 lg:w-5 lg:h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          <span>New Chat</span>
        </button>
      </div>

      {/* Sessions List */}
      <div className="flex-1 overflow-y-auto py-2">
        {loading ? (
          <div className="p-4 text-gray-400 flex items-center justify-center">
            <div className="animate-spin rounded-full h-6 w-6 border-2 border-indigo-400 border-t-transparent"></div>
            <span className="ml-2">Loading...</span>
          </div>
        ) : sessions.length === 0 ? (
          <div className="p-6 text-center">
            <svg className="mx-auto h-12 w-12 text-gray-600 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
            <p className="text-sm text-gray-400">No chats yet</p>
            <p className="text-xs text-gray-500 mt-1">Start a new conversation</p>
          </div>
        ) : (
          <div className="space-y-1 px-3">
            {sessions.map((session) => (
              <div
                key={session.session_id}
                onClick={() => onSessionSelect(session)}
                className={`group px-4 py-3 cursor-pointer rounded-xl transition-all duration-200 flex justify-between items-center ${
                  currentSessionId === session.session_id 
                    ? 'bg-gradient-to-r from-indigo-600/20 to-purple-600/20 border border-indigo-500/30' 
                    : 'hover:bg-gray-700/50'
                }`}
              >
                <div className="flex-1 truncate min-w-0">
                  <div className="flex items-center space-x-2 mb-1">
                    <svg className={`w-4 h-4 flex-shrink-0 ${
                      currentSessionId === session.session_id ? 'text-indigo-400' : 'text-gray-500'
                    }`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                    </svg>
                    <div className="text-sm font-medium truncate">
                      {session.session_name || 'Untitled Chat'}
                    </div>
                  </div>
                  <div className="text-xs text-gray-400 flex items-center space-x-3">
                    <span className="flex items-center">
                      <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                      </svg>
                      {session.message_count || 0}
                    </span>
                    {session.updated_at && (
                      <span className="flex items-center">
                        <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        {new Date(session.updated_at).toLocaleDateString()}
                      </span>
                    )}
                  </div>
                </div>
                <button
                  onClick={(e) => handleDeleteSession(session.session_id, e)}
                  className="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-400 ml-2 transition-all"
                  title="Delete session"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* User Info & Actions */}
      <div className="border-t border-gray-700/50 p-4 bg-gray-900/50">
        <div className="flex items-center justify-between mb-4 p-3 bg-gray-800/50 rounded-xl">
          <div className="flex items-center min-w-0">
            <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-full flex items-center justify-center text-sm font-bold shadow-lg">
              {user?.username?.charAt(0).toUpperCase()}
            </div>
            <div className="ml-3 min-w-0">
              <div className="text-sm font-medium truncate">{user?.username}</div>
              <div className={`text-xs px-2 py-0.5 rounded-full inline-block mt-1 ${
                user?.access_level === 2 
                  ? 'bg-purple-500/20 text-purple-300' 
                  : user?.access_level === 1 
                  ? 'bg-blue-500/20 text-blue-300' 
                  : 'bg-gray-500/20 text-gray-400'
              }`}>
                {user?.access_level === 2 ? 'Admin' : user?.access_level === 1 ? 'Moderator' : 'User'}
              </div>
            </div>
          </div>
        </div>
        
        <div className="space-y-2">
          {isAdmin() && (
            <button
              onClick={() => navigate('/admin')}
              className="w-full text-left text-sm py-2.5 px-4 rounded-lg hover:bg-gray-700/50 transition-all flex items-center space-x-2 group"
            >
              <svg className="w-4 h-4 text-gray-400 group-hover:text-purple-400 transition" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              <span className="text-gray-300 group-hover:text-white transition">Admin Dashboard</span>
            </button>
          )}
          <button
            onClick={handleLogout}
            className="w-full text-left text-sm py-2.5 px-4 rounded-lg hover:bg-red-500/10 transition-all flex items-center space-x-2 group"
          >
            <svg className="w-4 h-4 text-gray-400 group-hover:text-red-400 transition" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
            <span className="text-gray-300 group-hover:text-red-400 transition">Logout</span>
          </button>
        </div>
      </div>
    </div>
  );
};
