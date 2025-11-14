'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { analysisApi } from '@/lib/api';
import type { Repository, Analysis } from '@/types';

interface AnalysisModalProps {
  repository: Repository;
  onClose: () => void;
}

export default function AnalysisModal({ repository, onClose }: AnalysisModalProps) {
  const router = useRouter();
  const [analyzing, setAnalyzing] = useState(false);
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [error, setError] = useState<string | null>(null);

  const startAnalysis = async () => {
    setAnalyzing(true);
    setError(null);

    try {
      const newAnalysis = await analysisApi.create(repository.id);
      setAnalysis(newAnalysis);

      // Poll for completion
      const pollInterval = setInterval(async () => {
        try {
          const updated = await analysisApi.get(newAnalysis.id);
          setAnalysis(updated);

          if (updated.status === 'completed') {
            clearInterval(pollInterval);
            setTimeout(() => {
              router.push(`/repository/${repository.id}/analysis/${updated.id}`);
            }, 1500);
          } else if (updated.status === 'failed') {
            clearInterval(pollInterval);
            setError('Analysis failed. Please try again.');
            setAnalyzing(false);
          }
        } catch (err) {
          clearInterval(pollInterval);
          setError('Failed to check analysis status');
          setAnalyzing(false);
        }
      }, 3000);

    } catch (err) {
      setError('Failed to start analysis');
      setAnalyzing(false);
    }
  };

  useEffect(() => {
    startAnalysis();
  }, []);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-8 max-w-md w-full mx-4">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
          Analyzing Repository
        </h2>

        <p className="text-gray-600 dark:text-gray-400 mb-6">
          {repository.full_name}
        </p>

        {error ? (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 mb-4">
            <p className="text-red-800 dark:text-red-200">{error}</p>
          </div>
        ) : (
          <div className="mb-6">
            {analysis?.status === 'pending' && (
              <div className="flex items-center text-gray-600 dark:text-gray-400">
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-primary-600 mr-3"></div>
                Preparing analysis...
              </div>
            )}
            {analysis?.status === 'in_progress' && (
              <div className="flex items-center text-primary-600">
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-primary-600 mr-3"></div>
                Analyzing code...
              </div>
            )}
            {analysis?.status === 'completed' && (
              <div className="flex items-center text-green-600">
                <svg className="w-5 h-5 mr-3" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                Analysis complete! Redirecting...
              </div>
            )}
          </div>
        )}

        <button
          onClick={onClose}
          disabled={analyzing && !error}
          className="w-full px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {error ? 'Close' : 'Cancel'}
        </button>
      </div>
    </div>
  );
}
