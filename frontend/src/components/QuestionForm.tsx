import { useState } from 'react';
import { api } from '../services/api';
import { encryptData } from '../utils/encryption';
import { Loader } from './ui/Loader';

interface QuestionFormProps {
  isDarkMode: boolean;
}

export const QuestionForm = ({ isDarkMode }: QuestionFormProps) => {
    const [formData, setFormData] = useState({
        username: '',
        password: '',
        question: '',
        answer_sets: '',
        difficulty: 1,
        overall_marks: 10,
        author: '',
        topic: '',
        question_bank: ''
    });

    // State for managing alternative answers for each blank
    const [numBlanks, setNumBlanks] = useState(5);

    const [blankAnswers, setBlankAnswers] = useState<{ [key: number]: string[] }>({
        1: [''],
        2: [''],
        3: [''],
        4: [''],
        5: ['']
    });

    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);

    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: name === 'difficulty' || name === 'overall_marks' ? parseInt(value) : value
        }));
    };

    const handleNumBlanksChange = (
    e: React.ChangeEvent<HTMLSelectElement>
) => {
        const newNum = Math.min(10, Math.max(1, parseInt(e.target.value) || 1));
        setNumBlanks(newNum);
        setBlankAnswers(prev => {
            const updated = { ...prev };
            for (let i = 1; i <= newNum; i++) {
                if (!updated[i]) updated[i] = [''];
            }
            return updated;
        });
    };

    const handleAnswerChange = (blankNumber: number, index: number, value: string) => {
        setBlankAnswers(prev => ({
            ...prev,
            [blankNumber]: prev[blankNumber].map((answer, i) => 
                i === index ? value : answer
            )
        }));
    };

    const addAlternativeAnswer = (blankNumber: number) => {
        setBlankAnswers(prev => ({
            ...prev,
            [blankNumber]: [...prev[blankNumber], '']
        }));
    };

    const removeAlternativeAnswer = (blankNumber: number, index: number) => {
        setBlankAnswers(prev => ({
            ...prev,
            [blankNumber]: prev[blankNumber].filter((_, i) => i !== index)
        }));
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        setSuccess(null);

        try {
            // Validate marks vs blanks before doing anything expensive
            if (formData.overall_marks < numBlanks) {
                setError(`Overall marks (${formData.overall_marks}) must be at least equal to the number of blanks (${numBlanks}).`);
                setLoading(false);
                return;
            }

            // Format answer sets from blankAnswers (only up to numBlanks)
            const formattedAnswerSets = Array.from({ length: numBlanks }, (_, i) => i + 1)
                .map((blankNum) => {
                    const answers = blankAnswers[blankNum] ?? [''];
                    // Filter out empty answers and format each answer
                    const validAnswers = answers
                        .filter(answer => answer.trim() !== '')
                        .map((answer, index) => `${index + 1}. ${answer.trim()}`)
                        .join('\n');

                    // Only include blanks that have valid answers
                    return validAnswers ? `Blank ${blankNum}:\n${validAnswers}` : '';
                })
                .filter(blankSection => blankSection !== '') // Remove empty sections
                .join('\n\n');

            if (!formattedAnswerSets.trim()) {
                setError('At least one blank must have a non-empty answer before uploading.');
                setLoading(false);
                return;
            }

            // Encrypt username and password using RSA
            const encryptedUsername = await encryptData(formData.username);
            const encryptedPassword = await encryptData(formData.password);

            const submissionData = {
                ...formData,
                username: encryptedUsername,
                password: encryptedPassword,
                answer_sets: formattedAnswerSets,
                difficulty: Number(formData.difficulty),
                overall_marks: Number(formData.overall_marks),
                num_blanks: numBlanks
            };
            
            const response = await api.login(submissionData);
            setSuccess(response.message || 'Question uploaded successfully!');
            
            // Reset form after successful submission
            setFormData({
                username: '',
                password: '',
                question: '',
                answer_sets: '',
                difficulty: 1,
                overall_marks: 10,
                author: '',
                topic: '',
                question_bank: ''
            });
            setNumBlanks(5);
            setBlankAnswers({
                1: [''],
                2: [''],
                3: [''],
                4: [''],
                5: ['']
            });
        } catch (err) {
            setError(err instanceof Error ? err.message : 'An error occurred');
        } finally {
            setLoading(false);
        }
    };

    return (
        <>
            {loading && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className={`p-4 rounded-lg shadow-lg flex flex-col items-center transition-colors duration-200 ${
                        isDarkMode ? 'bg-gray-800' : 'bg-white'
                    }`}>
                        {/* Loader component only */}
                        <Loader/>

                        {/* Text below */}
                        <p className={`mt-4 font-medium transition-colors duration-200 ${
                            isDarkMode ? 'text-gray-300' : 'text-gray-700'
                        }`}>Uploading Question...</p>
                    </div>
                </div>
            )}
            <div className={`max-w-2xl mx-auto p-6 rounded-lg shadow-md transition-colors duration-200 ${
                isDarkMode ? 'bg-gray-800' : 'bg-white'
            }`}>
                <h2 className={`text-2xl font-bold mb-6 transition-colors duration-200 ${
                    isDarkMode ? 'text-white' : 'text-gray-800'
                }`}>Upload Question</h2>
                
                {error && (
                    <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
                        {error}
                    </div>
                )}
                
                {success && (
                    <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded mb-4">
                        {success}
                    </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-6">
                    <div>
                        <label className={`block text-sm font-medium mb-1 transition-colors duration-200 ${
                            isDarkMode ? 'text-gray-300' : 'text-gray-700'
                        }`}>Username</label>
                        <input
                            type="text"
                            name="username"
                            value={formData.username}
                            onChange={handleChange}
                            required
                            className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors duration-200 ${
                                isDarkMode 
                                    ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' 
                                    : 'border-gray-300 text-gray-900 placeholder-gray-500'
                            }`}
                            placeholder="Enter your username"
                        />
                    </div>

                    <div>
                        <label className={`block text-sm font-medium mb-1 transition-colors duration-200 ${
                            isDarkMode ? 'text-gray-300' : 'text-gray-700'
                        }`}>Password</label>
                        <input
                            type="password"
                            name="password"
                            value={formData.password}
                            onChange={handleChange}
                            required
                            className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors duration-200 ${
                                isDarkMode 
                                    ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' 
                                    : 'border-gray-300 text-gray-900 placeholder-gray-500'
                            }`}
                            placeholder="Enter your password"
                        />
                    </div>

                    <div>
                        <label className={`block text-sm font-medium mb-1 transition-colors duration-200 ${
                            isDarkMode ? 'text-gray-300' : 'text-gray-700'
                        }`}>Question Bank</label>
                        <textarea
                            name="question_bank"
                            value={formData.question_bank}
                            onChange={handleChange}
                            required
                            rows={2}
                            className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors duration-200 ${
                                isDarkMode 
                                    ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' 
                                    : 'border-gray-300 text-gray-900 placeholder-gray-500'
                            }`}
                            placeholder="Enter question bank name"
                        />
                    </div>

                    <div>
                        <label className={`block text-sm font-medium mb-1 transition-colors duration-200 ${
                            isDarkMode ? 'text-gray-300' : 'text-gray-700'
                        }`}>Question</label>
                        <textarea
                            name="question"
                            value={formData.question}
                            onChange={handleChange}
                            required
                            rows={4}
                            className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors duration-200 ${
                                isDarkMode 
                                    ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' 
                                    : 'border-gray-300 text-gray-900 placeholder-gray-500'
                            }`}
                            placeholder="Enter your question"
                        />
                    </div>

                    <div>
                        <label className={`block text-sm font-medium mb-1 transition-colors duration-200 ${
                            isDarkMode ? 'text-gray-300' : 'text-gray-700'
                        }`}>Number of Blanks</label>
                        {/* <input
                            type="number"
                            value={numBlanks}
                            onChange={handleNumBlanksChange}
                            min={1}
                            max={10}
                            required
                            title="Number of blank answer boxes in this question (1–10)"
                            className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors duration-200 ${
                                isDarkMode
                                    ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400'
                                    : 'border-gray-300 text-gray-900 placeholder-gray-500'
                            }`}
                            placeholder="Enter number of blanks (1–10)"
                        /> */}
                        <select
                            value={numBlanks}
                            onChange={handleNumBlanksChange}
                            required
                            title="Select number of blanks"
                            className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors duration-200 ${
                            isDarkMode
                            ? 'bg-gray-700 border-gray-600 text-white'
                            : 'border-gray-300 text-gray-900'
    }`}
>
    {Array.from({ length: 10 }, (_, i) => i + 1).map((number) => (
        <option key={number} value={number}>
            {number}
        </option>
    ))}
</select>
                    </div>

                    {/* Answer sections for each blank */}
                    {Array.from({ length: numBlanks }, (_, i) => i + 1).map((blankNumber) => (
                        <div key={blankNumber} className={`border rounded-lg p-4 transition-colors duration-200 ${
                            isDarkMode ? 'border-gray-600' : 'border-gray-200'
                        }`}>
                            <h3 className={`text-lg font-medium mb-3 transition-colors duration-200 ${
                                isDarkMode ? 'text-white' : 'text-gray-900'
                            }`}>Blank {blankNumber} Answers</h3>
                            {(blankAnswers[blankNumber] ?? ['']).map((answer, index) => (
                                <div key={index} className="mb-3">
                                    <div className="flex items-center space-x-2">
                                        <textarea
                                            value={answer}
                                            onChange={(e) => handleAnswerChange(blankNumber, index, e.target.value)}
                                            required
                                            rows={2}
                                            className={`flex-1 px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors duration-200 ${
                                                isDarkMode 
                                                    ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' 
                                                    : 'border-gray-300 text-gray-900 placeholder-gray-500'
                                            }`}
                                            placeholder={`Alternative answer ${index + 1} for Blank ${blankNumber}`}
                                        />
                                        {(blankAnswers[blankNumber] ?? ['']).length > 1 && (
                                            <button
                                                type="button"
                                                onClick={() => removeAlternativeAnswer(blankNumber, index)}
                                                className="inline-flex items-center px-3 py-1 border border-transparent text-sm font-medium rounded-md text-blue-700 bg-blue-100 hover:bg-blue-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                                                aria-label="Remove alternative answer"
                                            >
                                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                                </svg>
                                            </button>
                                        )}
                                    </div>
                                </div>
                            ))}
                            <button
                                type="button"
                                onClick={() => addAlternativeAnswer(blankNumber)}
                                className="mt-2 inline-flex items-center px-3 py-1 border border-transparent text-sm font-medium rounded-md text-blue-700 bg-blue-100 hover:bg-blue-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                            >
                                Add Alternative Answer
                            </button>
                        </div>
                    ))}

                    <div>
                        <label className={`block text-sm font-medium mb-1 transition-colors duration-200 ${
                            isDarkMode ? 'text-gray-300' : 'text-gray-700'
                        }`}>Difficulty</label>
                        <select
                            name="difficulty"
                            value={formData.difficulty}
                            onChange={handleChange}
                            required
                            title="Select difficulty level"
                            className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors duration-200 ${
                                isDarkMode 
                                    ? 'bg-gray-700 border-gray-600 text-white' 
                                    : 'border-gray-300 text-gray-900'
                            }`}
                        >
                            <option value={1}>Easy</option>
                            <option value={2}>Medium</option>
                            <option value={3}>Hard</option>
                        </select>
                    </div>

                    <div>
                        <label className={`block text-sm font-medium mb-1 transition-colors duration-200 ${
                            isDarkMode ? 'text-gray-300' : 'text-gray-700'
                        }`}>Overall Marks</label>
                        <input
                            type="number"
                            name="overall_marks"
                            value={formData.overall_marks}
                            onChange={handleChange}
                            required
                            step={1}
                            min={1}
                            title="Overall marks for the question (divided among blanks)"
                            className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors duration-200 ${
                                isDarkMode 
                                    ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' 
                                    : 'border-gray-300 text-gray-900 placeholder-gray-500'
                            }`}
                            placeholder="Enter overall marks"
                        />
                    </div>

                    <div>
                        <label className={`block text-sm font-medium mb-1 transition-colors duration-200 ${
                            isDarkMode ? 'text-gray-300' : 'text-gray-700'
                        }`}>Author</label>
                        <input
                            type="text"
                            name="author"
                            value={formData.author}
                            onChange={handleChange}
                            required
                            className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors duration-200 ${
                                isDarkMode 
                                    ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' 
                                    : 'border-gray-300 text-gray-900 placeholder-gray-500'
                            }`}
                            placeholder="Enter author name"
                        />
                    </div>

                    <div>
                        <label className={`block text-sm font-medium mb-1 transition-colors duration-200 ${
                            isDarkMode ? 'text-gray-300' : 'text-gray-700'
                        }`}>Topic</label>
                        <input
                            type="text"
                            name="topic"
                            value={formData.topic}
                            onChange={handleChange}
                            required
                            className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors duration-200 ${
                                isDarkMode 
                                    ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' 
                                    : 'border-gray-300 text-gray-900 placeholder-gray-500'
                            }`}
                            placeholder="Enter topic"
                        />
                    </div>

                    <button
                        type="submit"
                        disabled={loading}
                        className={`w-full py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 ${
                            loading ? 'opacity-50 cursor-not-allowed' : ''
                        }`}
                    >
                        {loading ? 'Uploading...' : 'Upload Question'}
                    </button>
                </form>
            </div>
        </>
    );
};