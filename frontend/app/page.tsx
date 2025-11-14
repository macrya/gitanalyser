'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { authApi } from '@/lib/api';

export default function Home() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('access_token');
      if (token) {
        router.push('/dashboard');
      } else {
        setLoading(false);
      }
    };
    checkAuth();
  }, [router]);

  const handleGitHubLogin = async () => {
    try {
      const { url } = await authApi.getGitHubAuthUrl();
      window.location.href = url;
    } catch (error) {
      console.error('Failed to get GitHub auth URL:', error);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800">
      <div className="container mx-auto px-4 py-16">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-5xl font-bold text-gray-900 dark:text-white mb-6">
            GitHub Technical Debt Analyzer
          </h1>
          <p className="text-xl text-gray-600 dark:text-gray-300 mb-12">
            Automatically analyze your repositories for technical debt, get specific code improvements,
            and generate automated refactoring pull requests.
          </p>

          <div className="grid md:grid-cols-3 gap-8 mb-12">
            <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-lg">
              <div className="text-primary-600 text-4xl mb-4">📊</div>
              <h3 className="text-lg font-semibold mb-2">Code Analysis</h3>
              <p className="text-gray-600 dark:text-gray-400">
                Deep analysis of code quality, complexity, and technical debt patterns
              </p>
            </div>

            <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-lg">
              <div className="text-primary-600 text-4xl mb-4">💡</div>
              <h3 className="text-lg font-semibold mb-2">Smart Suggestions</h3>
              <p className="text-gray-600 dark:text-gray-400">
                Get specific, actionable code improvement suggestions
              </p>
            </div>

            <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-lg">
              <div className="text-primary-600 text-4xl mb-4">🔧</div>
              <h3 className="text-lg font-semibold mb-2">Auto Refactoring</h3>
              <p className="text-gray-600 dark:text-gray-400">
                Generate automated pull requests with refactoring improvements
              </p>
            </div>
          </div>

          <button
            onClick={handleGitHubLogin}
            className="inline-flex items-center px-8 py-4 bg-gray-900 dark:bg-white text-white dark:text-gray-900 font-semibold rounded-lg hover:bg-gray-800 dark:hover:bg-gray-100 transition-colors"
          >
            <svg className="w-6 h-6 mr-2" fill="currentColor" viewBox="0 0 24 24">
              <path fillRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clipRule="evenodd" />
            </svg>
            Sign in with GitHub
          </button>
        </div>
      </div>
    </main>
  );
}
