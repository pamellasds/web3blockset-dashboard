import { useState } from "react";
import { Download, Copy, Check, ExternalLink } from "lucide-react";
import { ZENODO_URL, CITATION_BIBTEX, PAPER_TITLE, AUTHORS } from "../../utils/constants";
import type { OverviewData } from "../../types";

export default function DownloadCitation({ data }: { data: OverviewData }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(CITATION_BIBTEX).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div className="bg-white rounded-xl border border-border p-6">
        <h3 className="text-base font-semibold text-slate-800 mb-2">Download Dataset</h3>
        <p className="text-sm text-slate-500 mb-4">
          The full dataset contains {data.totalRecords.toLocaleString()} records with 25+ fields including
          original text, cleaned text, and stemmed text.
        </p>
        <div className="space-y-3">
          <a
            href={ZENODO_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 w-full justify-center px-4 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors font-medium text-sm"
          >
            <Download size={16} />
            Download from Zenodo
            <ExternalLink size={14} />
          </a>
          <div className="flex items-center gap-4 text-xs text-slate-400">
            <span>CSV format (~1.8 GB)</span>
            <span>Last updated: {data.lastUpdated}</span>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-border p-6">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-base font-semibold text-slate-800">How to Cite</h3>
          <button
            onClick={handleCopy}
            className="flex items-center gap-1 text-xs text-primary-600 hover:text-primary-700 transition-colors"
          >
            {copied ? <Check size={14} /> : <Copy size={14} />}
            {copied ? "Copied!" : "Copy BibTeX"}
          </button>
        </div>
        <p className="text-sm text-slate-600 mb-3">
          <strong>{PAPER_TITLE}</strong>
        </p>
        <p className="text-xs text-slate-500 mb-3">
          {AUTHORS.map((a) => a.name).join(", ")}
        </p>
        <pre className="bg-slate-50 rounded-lg p-3 text-xs text-slate-600 overflow-x-auto font-mono whitespace-pre-wrap">
          {CITATION_BIBTEX}
        </pre>
      </div>
    </div>
  );
}
