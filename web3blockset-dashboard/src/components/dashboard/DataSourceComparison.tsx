import { Server, Globe } from "lucide-react";
import type { OverviewData } from "../../types";
import { formatNumber } from "../../utils/formatNumber";

export default function DataSourceComparison({ data }: { data: OverviewData }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl border border-blue-200 p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 bg-blue-500 rounded-lg text-white">
            <Server size={20} />
          </div>
          <div>
            <h3 className="font-semibold text-blue-900">Provider Dataset</h3>
            <p className="text-sm text-blue-600">Official organization repositories</p>
          </div>
        </div>
        <div className="space-y-3">
          <div className="flex justify-between">
            <span className="text-sm text-blue-700">Records</span>
            <span className="font-semibold text-blue-900">{formatNumber(data.totalProviderRecords)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm text-blue-700">Repositories</span>
            <span className="font-semibold text-blue-900">{formatNumber(data.totalProviderRepos)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm text-blue-700">Organizations</span>
            <span className="font-semibold text-blue-900">{formatNumber(data.totalOrganizations)}</span>
          </div>
        </div>
      </div>

      <div className="bg-gradient-to-br from-orange-50 to-orange-100 rounded-xl border border-orange-200 p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 bg-orange-500 rounded-lg text-white">
            <Globe size={20} />
          </div>
          <div>
            <h3 className="font-semibold text-orange-900">Community Dataset</h3>
            <p className="text-sm text-orange-600">Adopter/community repositories</p>
          </div>
        </div>
        <div className="space-y-3">
          <div className="flex justify-between">
            <span className="text-sm text-orange-700">Records</span>
            <span className="font-semibold text-orange-900">{formatNumber(data.totalCommunityRecords)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm text-orange-700">Repositories</span>
            <span className="font-semibold text-orange-900">{formatNumber(data.totalCommunityRepos)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm text-orange-700">Search Strategy</span>
            <span className="font-semibold text-orange-900">Keyword-based</span>
          </div>
        </div>
      </div>
    </div>
  );
}
