import { useState, useEffect } from 'react';
import { chatAPI } from '../services/api';

export const ModelSelector = ({ selectedModel, onModelChange }) => {
  const [models, setModels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isOpen, setIsOpen] = useState(false);
  const [ollamaStatus, setOllamaStatus] = useState(false);

  useEffect(() => {
    loadModels();
    checkOllamaStatus();
  }, []);

  const loadModels = async () => {
    try {
      const response = await chatAPI.listModels();
      setModels(response.data.models);
    } catch (error) {
      console.error('Failed to load models:', error);
    } finally {
      setLoading(false);
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

  const handleModelSelect = (modelName) => {
    onModelChange(modelName);
    setIsOpen(false);
  };

  return (
    <div className="relative z-50">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center space-x-2 px-3 sm:px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition shadow-sm w-full sm:w-auto justify-between sm:justify-start"
      >
        <svg className="w-4 h-4 sm:w-5 sm:h-5 text-gray-600 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
        <span className="text-xs sm:text-sm font-medium text-gray-700 truncate max-w-[120px] sm:max-w-none">
          {selectedModel}
        </span>
        <svg className={`w-3 h-3 sm:w-4 sm:h-4 text-gray-500 transition-transform flex-shrink-0 ${isOpen ? 'transform rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-40"
            onClick={() => setIsOpen(false)}
          />
          
          {/* Dropdown */}
          <div className="absolute right-0 top-full mt-2 w-screen max-w-xs sm:w-72 bg-white rounded-xl shadow-2xl border border-gray-200 z-50 overflow-hidden">
            <div className="p-4 bg-gradient-to-r from-indigo-50 to-purple-50 border-b border-gray-200">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-semibold text-gray-800">Select Model</span>
                <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${ollamaStatus ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                  {ollamaStatus ? '● Connected' : '● Offline'}
                </span>
              </div>
            </div>

            <div className="p-2 max-h-80 overflow-y-auto">
              {loading ? (
                <div className="p-6 text-center">
                  <div className="inline-block animate-spin rounded-full h-8 w-8 border-2 border-indigo-200 border-t-indigo-600 mb-2"></div>
                  <p className="text-sm text-gray-500">Loading models...</p>
                </div>
              ) : models.length === 0 ? (
                <div className="p-6 text-center">
                  <svg className="mx-auto h-12 w-12 text-gray-400 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
                  </svg>
                  <p className="text-sm text-gray-500">No models available</p>
                  <p className="text-xs text-gray-400 mt-1">Make sure Ollama is running</p>
                </div>
              ) : (
                <div className="space-y-1">
                  {models.map((model) => (
                    <button
                      key={model.name}
                      onClick={() => handleModelSelect(model.name)}
                      className={`w-full text-left px-4 py-3 rounded-lg transition-all ${
                        selectedModel === model.name 
                          ? 'bg-gradient-to-r from-indigo-500 to-purple-500 text-white shadow-md' 
                          : 'text-gray-700 hover:bg-gray-100'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="font-medium text-sm">{model.name}</div>
                          {model.size && (
                            <div className={`text-xs mt-0.5 ${selectedModel === model.name ? 'text-indigo-100' : 'text-gray-500'}`}>
                              {(model.size / 1024 / 1024 / 1024).toFixed(2)} GB
                            </div>
                          )}
                        </div>
                        {selectedModel === model.name && (
                          <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                          </svg>
                        )}
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>

            <div className="p-3 bg-gray-50 border-t border-gray-200">
              <button
                onClick={() => {
                  loadModels();
                  checkOllamaStatus();
                }}
                className="w-full flex items-center justify-center space-x-2 px-4 py-2 text-sm text-indigo-600 hover:bg-indigo-50 font-medium rounded-lg transition"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                <span>Refresh Models</span>
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
};
