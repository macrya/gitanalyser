import Link from 'next/link';
import type { Repository } from '@/types';
import { formatDistanceToNow } from 'date-fns';

interface RepositoryCardProps {
  repository: Repository;
  onAnalyze: () => void;
}

export default function RepositoryCard({ repository, onAnalyze }: RepositoryCardProps) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 hover:shadow-xl transition-shadow">
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
            {repository.name}
          </h3>
          {repository.description && (
            <p className="text-gray-600 dark:text-gray-400 text-sm mb-3 line-clamp-2">
              {repository.description}
            </p>
          )}
        </div>
      </div>

      <div className="flex items-center gap-4 mb-4 text-sm text-gray-500 dark:text-gray-400">
        {repository.language && (
          <span className="flex items-center">
            <span className="w-3 h-3 rounded-full bg-primary-500 mr-1"></span>
            {repository.language}
          </span>
        )}
        <span>⭐ {repository.stars}</span>
        <span>🔱 {repository.forks}</span>
      </div>

      {repository.last_analyzed_at && (
        <p className="text-xs text-gray-500 dark:text-gray-400 mb-4">
          Last analyzed {formatDistanceToNow(new Date(repository.last_analyzed_at), { addSuffix: true })}
        </p>
      )}

      <div className="flex gap-2">
        <button
          onClick={onAnalyze}
          className="flex-1 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
        >
          Analyze
        </button>
        <Link
          href={`/repository/${repository.id}`}
          className="flex-1 px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors text-center"
        >
          View Details
        </Link>
      </div>
    </div>
  );
}
