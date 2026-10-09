import { useState } from 'react';
import { Sidebar } from './Sidebar';

export const ChatLayout = ({ children }) => {
  const [currentSession, setCurrentSession] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleSessionSelect = (session) => {
    setCurrentSession(session);
    setSidebarOpen(false); // Close sidebar on mobile after selecting
  };

  const handleNewChat = (session) => {
    setCurrentSession(session);
    setSidebarOpen(false); // Close sidebar on mobile after creating
  };

  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden">
      {/* Mobile menu button */}
      <button
        onClick={() => setSidebarOpen(!sidebarOpen)}
        className="lg:hidden fixed top-4 left-4 z-50 p-2 bg-gray-900 text-white rounded-lg shadow-lg"
      >
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          {sidebarOpen ? (
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          ) : (
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          )}
        </svg>
      </button>

      {/* Sidebar - hidden on mobile by default, shown when sidebarOpen is true */}
      <div className={`
        fixed lg:static inset-y-0 left-0 z-40 
        transform ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'} 
        lg:translate-x-0 transition-transform duration-300 ease-in-out
      `}>
        <Sidebar
          currentSessionId={currentSession?.session_id}
          onSessionSelect={handleSessionSelect}
          onNewChat={handleNewChat}
        />
      </div>

      {/* Overlay for mobile when sidebar is open */}
      {sidebarOpen && (
        <div
          className="lg:hidden fixed inset-0 bg-black bg-opacity-50 z-30"
          onClick={() => setSidebarOpen(false)}
        />
      )}
      
      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden w-full">
        {children({ currentSession, setCurrentSession })}
      </div>
    </div>
  );
};
