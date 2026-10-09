import { useState } from 'react';
import { ChatLayout } from '../components/ChatLayout';
import { ChatInterface } from '../components/ChatInterface';
import { ModelSelector } from '../components/ModelSelector';

export const Chat = () => {
  const [selectedModel, setSelectedModel] = useState('gemma2:2b');

  return (
    <ChatLayout>
      {({ currentSession }) => (
        <div className="flex-1 flex flex-col h-full">
          {/* Top Bar with Model Selector */}
          {currentSession && (
            <div className="bg-white border-b border-gray-200 p-3 lg:p-4 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 sm:gap-0 flex-shrink-0">
              <div className="flex-1 min-w-0">
                <h2 className="text-base lg:text-lg font-semibold text-gray-800 truncate">
                  {currentSession.session_name}
                </h2>
                <p className="text-xs lg:text-sm text-gray-500">
                  {currentSession.message_count || 0} messages
                </p>
              </div>
              <div className="w-full sm:w-auto">
                <ModelSelector
                  selectedModel={selectedModel}
                  onModelChange={setSelectedModel}
                />
              </div>
            </div>
          )}
          
          {/* Chat Interface */}
          <div className="flex-1 min-h-0">
            <ChatInterface session={currentSession} selectedModel={selectedModel} />
          </div>
        </div>
      )}
    </ChatLayout>
  );
};
