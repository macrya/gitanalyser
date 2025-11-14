import type { TechnicalDebtItem } from '@/types';
import { useState } from 'react';

interface DebtListProps {
  debtItems: TechnicalDebtItem[];
}

export default function DebtList({ debtItems }: DebtListProps) {
  const [filter, setFilter] = useState<string>('all');
  const [expandedId, setExpandedId] = useState<number | null>(null);

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
      case 'high': return 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200';
      case 'medium': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
      case 'low': return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
      default: return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200';
    }
  };

  const filteredItems = filter === 'all'
    ? debtItems
    : debtItems.filter(item => item.severity === filter);

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-xl font-bold text-gray-900 dark:text-white">
          Technical Debt Items ({filteredItems.length})
        </h3>
        <select
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
        >
          <option value="all">All</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
      </div>

      <div className="space-y-3 max-h-[600px] overflow-y-auto">
        {filteredItems.length === 0 ? (
          <p className="text-gray-500 dark:text-gray-400 text-center py-8">
            No debt items found
          </p>
        ) : (
          filteredItems.map((item) => (
            <div
              key={item.id}
              className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
              onClick={() => setExpandedId(expandedId === item.id ? null : item.id)}
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex-1">
                  <h4 className="font-semibold text-gray-900 dark:text-white">
                    {item.title}
                  </h4>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    {item.file_path}:{item.line_number || 'N/A'}
                  </p>
                </div>
                <span className={`px-2 py-1 rounded text-xs font-semibold ${getSeverityColor(item.severity)}`}>
                  {item.severity}
                </span>
              </div>

              {expandedId === item.id && (
                <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
                  {item.description && (
                    <p className="text-sm text-gray-600 dark:text-gray-300 mb-2">
                      {item.description}
                    </p>
                  )}
                  {item.code_snippet && (
                    <pre className="bg-gray-50 dark:bg-gray-900 p-2 rounded text-xs overflow-x-auto">
                      <code>{item.code_snippet}</code>
                    </pre>
                  )}
                  {item.estimated_effort_hours && (
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                      Estimated effort: {item.estimated_effort_hours}h
                    </p>
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
