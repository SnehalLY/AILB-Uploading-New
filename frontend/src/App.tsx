import { useState, useEffect } from 'react';
import { QuestionForm } from './components/QuestionForm'

function App() {
  const [showInstructions, setShowInstructions] = useState(false);
  const [isDarkMode, setIsDarkMode] = useState(false);

  // Apply dark mode classes to body
  useEffect(() => {
    if (isDarkMode) {
      document.body.classList.add('dark');
    } else {
      document.body.classList.remove('dark');
    }
  }, [isDarkMode]);

  const toggleDarkMode = () => {
    setIsDarkMode(!isDarkMode);
  };

  const instructions = [
    "1. There must not be 'Scenario' present while uploading the question in Question field",
    "2. Each instruction must start with 'At Blank X:' in the instructions section, where 'X' indicated the instruction number.",
    "3. There must be no special character like '//' or '#' or 'At' before the placeholder 'Blank X: Enter your code here' in the sample script.",
    "4. In Question Bank field, make sure that the QB exists and matches exactly same as of present on platform along with the case sensitivity.",
    "5. The word 'Sample Script' must be followed by a colon ':'.",
    "6. There must not be a space after the placeholder 'Blank X: Enter your code here' in the sample script. And add a new line after it.",
    "7. No space before the colon ':' at any place like 'At Blank X:', 'Sample Script:' or 'Complete the code as per the given instructions:'.",
    "8. If there is any type of bulleting in the scenario of the question, that must be done manually in the 'Question' field itself."
  ];

  return (
    <div className={`min-h-screen transition-colors duration-200 ${isDarkMode ? 'bg-gray-900' : 'bg-gray-100'}`}>
      <header className={`shadow transition-colors duration-200 ${isDarkMode ? 'bg-gray-800' : 'bg-white'}`}>
        <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8 flex justify-between items-center">
          <div className="flex items-center space-x-3">
            <img src="/images/imocha.png" alt="iMocha Logo" className="w-8 h-8" />
            <h1 className={`text-3xl font-bold transition-colors duration-200 ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
              AI-LogicBox Uploading
            </h1>
          </div>
          <div className="flex items-center space-x-4">
            <button
              onClick={toggleDarkMode}
              className={`p-2 rounded-md transition-colors duration-200 ${isDarkMode
                  ? 'bg-gray-700 hover:bg-gray-600 text-yellow-400'
                  : 'bg-gray-200 hover:bg-gray-300 text-gray-700'
                }`}
              aria-label="Toggle dark mode"
            >
              {isDarkMode ? (
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
                </svg>
              ) : (
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                </svg>
              )}
            </button>
            <button
              onClick={() => setShowInstructions(true)}
              className={`px-4 py-2 rounded-md transition-colors duration-200 ${isDarkMode
                  ? 'bg-blue-600 hover:bg-blue-700 text-white'
                  : 'bg-blue-500 hover:bg-blue-600 text-white'
                }`}
            >
              Instructions
            </button>
          </div>
        </div>
      </header>
      <main>
        <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
          <QuestionForm isDarkMode={isDarkMode} />
        </div>
      </main>

      {/* Instructions Modal */}
      {showInstructions && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className={`rounded-lg p-6 max-w-2xl w-full mx-4 relative transition-colors duration-200 ${isDarkMode ? 'bg-gray-800 text-white' : 'bg-white text-gray-900'
            }`}>
            <button
              onClick={() => setShowInstructions(false)}
              className={`absolute top-4 right-4 hover:text-gray-700 transition-colors duration-200 ${isDarkMode ? 'text-gray-400 hover:text-gray-200' : 'text-gray-500'
                }`}
              aria-label="Close instructions"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
            <h2 className="text-2xl font-bold mb-4">Instructions</h2>
            <div className="space-y-2">
              {instructions.map((instruction, index) => (
                <p key={index} className={isDarkMode ? 'text-gray-300' : 'text-gray-700'}>{instruction}</p>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default App;