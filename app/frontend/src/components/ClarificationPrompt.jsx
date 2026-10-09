import { useState } from 'react';

export const ClarificationPrompt = ({ clarification, onSelect }) => {
  const [customInput, setCustomInput] = useState('');
  const [showCustom, setShowCustom] = useState(false);

  const handleOptionClick = (option) => {
    onSelect(option);
  };

  const handleCustomSubmit = () => {
    if (customInput.trim()) {
      onSelect(customInput.trim());
      setCustomInput('');
      setShowCustom(false);
    }
  };

  return (
    <div className="bg-gradient-to-br from-indigo-50 to-purple-50 border-2 border-indigo-200 rounded-xl p-4 sm:p-5 my-3 shadow-md">
      {/* Question */}
      <div className="flex items-start space-x-3 mb-4">
        <div className="flex-shrink-0">
          <svg className="w-6 h-6 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-800 mb-1">
            Need Clarification
          </h3>
          <p className="text-gray-700">
            {clarification.question}
          </p>
        </div>
      </div>

      {/* Options */}
      <div className="space-y-2 mb-4">
        <p className="text-sm font-medium text-gray-600 mb-2">Quick Options:</p>
        {clarification.options.map((option, index) => (
          <button
            key={index}
            onClick={() => handleOptionClick(option)}
            className="w-full text-left px-4 py-3 bg-white hover:bg-indigo-100 border border-indigo-200 rounded-lg transition-all duration-200 shadow-sm hover:shadow-md hover:border-indigo-400 group"
          >
            <div className="flex items-center justify-between">
              <span className="text-gray-800 group-hover:text-indigo-900 font-medium">
                {option}
              </span>
              <svg className="w-5 h-5 text-indigo-400 group-hover:text-indigo-600 transition-transform group-hover:translate-x-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </div>
          </button>
        ))}
      </div>

      {/* Custom Input Toggle */}
      {!showCustom && (
        <button
          onClick={() => setShowCustom(true)}
          className="w-full px-4 py-2 text-sm text-indigo-600 hover:text-indigo-800 border border-indigo-300 hover:border-indigo-500 rounded-lg transition-colors bg-white hover:bg-indigo-50"
        >
          💬 Or describe what you need...
        </button>
      )}

      {/* Custom Input */}
      {showCustom && (
        <div className="mt-3 space-y-2">
          <p className="text-sm font-medium text-gray-600">Or provide your own answer:</p>
          <div className="flex space-x-2">
            <input
              type="text"
              value={customInput}
              onChange={(e) => setCustomInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleCustomSubmit()}
              placeholder="Type your clarification..."
              className="flex-1 px-3 py-2 border-2 border-indigo-200 rounded-lg focus:outline-none focus:border-indigo-500 bg-white"
              autoFocus
            />
            <button
              onClick={handleCustomSubmit}
              disabled={!customInput.trim()}
              className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Send
            </button>
          </div>
          <button
            onClick={() => {
              setShowCustom(false);
              setCustomInput('');
            }}
            className="text-sm text-gray-500 hover:text-gray-700"
          >
            Cancel
          </button>
        </div>
      )}
    </div>
  );
};
