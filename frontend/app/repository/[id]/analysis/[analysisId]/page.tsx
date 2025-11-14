'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { analysisApi, pullRequestApi, repositoryApi } from '@/lib/api';
import type { AnalysisDetail, Repository } from '@/types';
import MetricsOverview from '@/components/MetricsOverview';
import DebtList from '@/components/DebtList';
import SuggestionsList from '@/components/SuggestionsList';

export default function AnalysisPage() {
  const params = useParams();
  const router = useRouter();
  const analysisId = parseInt(params.analysisId as string);
  const repoId = parseInt(params.id as string);

  const [analysis, setAnalysis] = useState<AnalysisDetail | null>(null);
  const [repository, setRepository] = useState<Repository | null>(null);
  const [loading, setLoading] = useState(true);
  const [creatingPR, setCreatingPR] = useState(false);

  useEffect(() => {
    loadData();
  }, [analysisId, repoId]);

  const loadData = async () => {
    try {
      const [analysisData, repoData] = await Promise.all([
        analysisApi.get(analysisId),
        repositoryApi.get(repoId),
      ]);
      setAnalysis(analysisData);
      setRepository(repoData);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreatePR = async () => {
    if (!analysis) return;

    setCreatingPR(true);
    try {
      const pr = await pullRequestApi.create(analysis.id);
      alert(`Pull request created successfully! View it at: ${pr.github_pr_url}`);
      if (pr.github_pr_url) {
        window.open(pr.github_pr_url, '_blank');
      }
    } catch (error) {
      console.error('Failed to create PR:', error);
      alert('Failed to create pull request. Please try again.');
    } finally {
      setCreatingPR(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (!analysis || !repository) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Analysis not found</h2>
          <button
            onClick={() => router.push('/dashboard')}
            className="px-4 py-2 bg-primary-600 text-white rounded-lg"
          >
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <nav className="bg-white dark:bg-gray-800 shadow">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div>
              <button
                onClick={() => router.push('/dashboard')}
                className="text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white mb-2"
              >
                ← Back to Dashboard
              </button>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                {repository.full_name}
              </h1>
            </div>
            <button
              onClick={handleCreatePR}
              disabled={creatingPR || analysis.suggestions.length === 0}
              className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {creatingPR ? 'Creating PR...' : 'Create Refactoring PR'}
            </button>
          </div>
        </div>
      </nav>

      <main className="container mx-auto px-4 py-8">
        <MetricsOverview analysis={analysis} />

        <div className="grid lg:grid-cols-2 gap-6 mt-6">
          <DebtList debtItems={analysis.debt_items} />
          <SuggestionsList suggestions={analysis.suggestions} />
        </div>
      </main>
    </div>
  );
}
