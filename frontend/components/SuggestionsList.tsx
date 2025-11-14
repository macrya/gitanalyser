import type { CodeSuggestion } from '@/types';
import { useState } from 'react';

interface SuggestionsListProps {
  suggestions: CodeSuggestion[];
}

export default function SuggestionsList({ suggestions }: SuggestionsListProps) {
  const [expandedId, setExpandedId] = useState<number | null>(null);

  const getImpactColor = (impact?: string) => {
    switch (impact) {
      case 'high': return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
      case 'medium': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
      case 'low': return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
      default: return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200';
    }
  };

  const sortedSuggestions = [...suggestions].sort((a, b) => b.priority - a.priority);

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
      <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
        Code Suggestions ({suggestions.length})
      </h3>

      <div className="space-y-3 max-h-[600px] overflow-y-auto">
        {sortedSuggestions.length === 0 ? (
          <p className="text-gray-500 dark:text-gray-400 text-center py-8">
            No suggestions available
          </p>
        ) : (
          sortedSuggestions.map((suggestion) => (
            <div
              key={suggestion.id}
              className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
              onClick={() => setExpandedId(expandedId === suggestion.id ? null : suggestion.id)}
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex-1">
                  <h4 className="font-semibold text-gray-900 dark:text-white">
                    {suggestion.title}
                  </h4>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    {suggestion.file_path}
                    {suggestion.line_start && `:${suggestion.line_start}`}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  {suggestion.impact && (
                    <span className={`px-2 py-1 rounded text-xs font-semibold ${getImpactColor(suggestion.impact)}`}>
                      {suggestion.impact}
                    </span>
                  )}
                  <span className="text-xs text-gray-500 dark:text-gray-400">
                    P{suggestion.priority}
                  </span>
                </div>
              </div>

              <div className="flex items-center gap-2 text-xs">
                <span className="text-gray-500 dark:text-gray-400">
                  Confidence: {(suggestion.confidence * 100).toFixed(0)}%
                </span>
                {suggestion.applied && (
                  <span className="px-2 py-0.5 bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200 rounded">
                    Applied
                  </span>
                )}
              </div>

              {expandedId === suggestion.id && (
                <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
                  {suggestion.description && (
                    <p className="text-sm text-gray-600 dark:text-gray-300 mb-3">
                      {suggestion.description}
                    </p>
                  )}

                  {suggestion.original_code && suggestion.suggested_code && (
                    <div className="grid md:grid-cols-2 gap-3">
                      <div>
                        <p className="text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
                          Original:
                        </p>
                        <pre className="bg-red-50 dark:bg-red-900/20 p-2 rounded text-xs overflow-x-auto border border-red-200 dark:border-red-800">
                          <code>{suggestion.original_code}</code>
                        </pre>
                      </div>
                      <div>
                        <p className="text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
                          Suggested:
                        </p>
                        <pre className="bg-green-50 dark:bg-green-900/20 p-2 rounded text-xs overflow-x-auto border border-green-200 dark:border-green-800">
                          <code>{suggestion.suggested_code}</code>
                        </pre>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
