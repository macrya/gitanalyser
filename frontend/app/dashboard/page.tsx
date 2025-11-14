'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { repositoryApi, analysisApi } from '@/lib/api';
import type { Repository, Analysis } from '@/types';
import RepositoryCard from '@/components/RepositoryCard';
import AnalysisModal from '@/components/AnalysisModal';

export default function Dashboard() {
  const router = useRouter();
  const [repositories, setRepositories] = useState<Repository[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [selectedRepo, setSelectedRepo] = useState<Repository | null>(null);
  const [showAnalysisModal, setShowAnalysisModal] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      router.push('/');
      return;
    }

    loadRepositories();
  }, [router]);

  const loadRepositories = async () => {
    try {
      const { repositories } = await repositoryApi.list();
      setRepositories(repositories);
    } catch (error) {
      console.error('Failed to load repositories:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSync = async () => {
    setSyncing(true);
    try {
      await repositoryApi.sync();
      await loadRepositories();
    } catch (error) {
      console.error('Failed to sync repositories:', error);
    } finally {
      setSyncing(false);
    }
  };

  const handleAnalyze = (repo: Repository) => {
    setSelectedRepo(repo);
    setShowAnalysisModal(true);
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    router.push('/');
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <nav className="bg-white dark:bg-gray-800 shadow">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              GitHub Debt Analyzer
            </h1>
            <button
              onClick={handleLogout}
              className="px-4 py-2 text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white"
            >
              Logout
            </button>
          </div>
        </div>
      </nav>

      <main className="container mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-3xl font-bold text-gray-900 dark:text-white">
            Your Repositories
          </h2>
          <button
            onClick={handleSync}
            disabled={syncing}
            className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {syncing ? 'Syncing...' : 'Sync Repositories'}
          </button>
        </div>

        {repositories.length === 0 ? (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-12 text-center">
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              No repositories found. Click "Sync Repositories" to import your GitHub repos.
            </p>
          </div>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {repositories.map((repo) => (
              <RepositoryCard
                key={repo.id}
                repository={repo}
                onAnalyze={() => handleAnalyze(repo)}
              />
            ))}
          </div>
        )}
      </main>

      {showAnalysisModal && selectedRepo && (
        <AnalysisModal
          repository={selectedRepo}
          onClose={() => {
            setShowAnalysisModal(false);
            setSelectedRepo(null);
          }}
        />
      )}
    </div>
  );
}
