import React from 'react';
import { Link } from 'react-router-dom';
import { Menu, BookOpen } from 'lucide-react';

export const Header: React.FC = () => {
  const [isMenuOpen, setIsMenuOpen] = React.useState(false);

  return (
    <header className="sticky top-0 z-10 bg-white border-b border-gray-200">
      <div className="container mx-auto px-4">
        <div className="flex h-16 items-center justify-between">
          <div className="flex items-center">
            <Link to="/" className="flex items-center space-x-2">
              <BookOpen className="h-6 w-6 text-blue-600" />
              <span className="text-xl font-semibold text-gray-900">Question Uploading</span>
            </Link>
          </div>

          <nav className="hidden md:flex items-center space-x-4">
            <Link 
              to="/" 
              className="text-gray-700 hover:text-blue-600 px-3 py-2 text-sm font-medium"
            >
              Dashboard
            </Link>
            <Link 
              to="/question-banks/new" 
              className="text-gray-700 hover:text-blue-600 px-3 py-2 text-sm font-medium"
            >
              New Question Bank
            </Link>
            <Link 
              to="/questions/new" 
              className="text-gray-700 hover:text-blue-600 px-3 py-2 text-sm font-medium"
            >
              New Question
            </Link>
          </nav>

          <div className="md:hidden flex items-center">
            <button
              type="button"
              className="inline-flex items-center justify-center p-2 rounded-md text-gray-700 hover:text-blue-600 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
              onClick={() => setIsMenuOpen(!isMenuOpen)}
            >
              <span className="sr-only">Open main menu</span>
              <Menu className="h-6 w-6" />
            </button>
          </div>
        </div>
      </div>

      {/* Mobile menu */}
      {isMenuOpen && (
        <div className="md:hidden">
          <div className="space-y-1 px-2 pb-3 pt-2">
            <Link
              to="/"
              className="block px-3 py-2 text-base font-medium text-gray-700 hover:bg-gray-100 hover:text-blue-600 rounded-md"
              onClick={() => setIsMenuOpen(false)}
            >
              Dashboard
            </Link>
            <Link
              to="/question-banks/new"
              className="block px-3 py-2 text-base font-medium text-gray-700 hover:bg-gray-100 hover:text-blue-600 rounded-md"
              onClick={() => setIsMenuOpen(false)}
            >
              New Question Bank
            </Link>
            <Link
              to="/questions/new"
              className="block px-3 py-2 text-base font-medium text-gray-700 hover:bg-gray-100 hover:text-blue-600 rounded-md"
              onClick={() => setIsMenuOpen(false)}
            >
              New Question
            </Link>
          </div>
        </div>
      )}
    </header>
  );
};
