import type { AnalysisDetail } from '@/types';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface MetricsOverviewProps {
  analysis: AnalysisDetail;
}

export default function MetricsOverview({ analysis }: MetricsOverviewProps) {
  const issueData = [
    { name: 'Critical', count: analysis.critical_issues, fill: '#ef4444' },
    { name: 'High', count: analysis.high_issues, fill: '#f59e0b' },
    { name: 'Medium', count: analysis.medium_issues, fill: '#eab308' },
    { name: 'Low', count: analysis.low_issues, fill: '#22c55e' },
  ];

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
      <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
        Analysis Overview
      </h2>

      <div className="grid md:grid-cols-4 gap-4 mb-8">
        <div className="bg-primary-50 dark:bg-primary-900/20 rounded-lg p-4">
          <p className="text-sm text-primary-600 dark:text-primary-400 font-semibold">Total Lines</p>
          <p className="text-3xl font-bold text-primary-900 dark:text-primary-100">
            {analysis.total_lines.toLocaleString()}
          </p>
        </div>

        <div className="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-4">
          <p className="text-sm text-purple-600 dark:text-purple-400 font-semibold">Total Files</p>
          <p className="text-3xl font-bold text-purple-900 dark:text-purple-100">
            {analysis.total_files}
          </p>
        </div>

        <div className="bg-orange-50 dark:bg-orange-900/20 rounded-lg p-4">
          <p className="text-sm text-orange-600 dark:text-orange-400 font-semibold">Avg Complexity</p>
          <p className="text-3xl font-bold text-orange-900 dark:text-orange-100">
            {analysis.average_complexity.toFixed(1)}
          </p>
        </div>

        <div className="bg-red-50 dark:bg-red-900/20 rounded-lg p-4">
          <p className="text-sm text-red-600 dark:text-red-400 font-semibold">Debt Ratio</p>
          <p className="text-3xl font-bold text-red-900 dark:text-red-100">
            {analysis.technical_debt_ratio.toFixed(1)}
          </p>
        </div>
      </div>

      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Issues by Severity
        </h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={issueData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="count" fill="#0ea5e9" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="grid md:grid-cols-3 gap-4">
        <div className="text-center p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
          <p className="text-sm text-gray-600 dark:text-gray-400">Total Debt Items</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">
            {analysis.total_debt_items}
          </p>
        </div>

        <div className="text-center p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
          <p className="text-sm text-gray-600 dark:text-gray-400">Suggestions</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">
            {analysis.suggestions.length}
          </p>
        </div>

        <div className="text-center p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
          <p className="text-sm text-gray-600 dark:text-gray-400">Status</p>
          <p className="text-2xl font-bold text-green-600">
            {analysis.status}
          </p>
        </div>
      </div>
    </div>
  );
}
