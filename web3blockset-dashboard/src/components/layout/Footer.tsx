import { GITHUB_REPO_URL, ZENODO_URL } from "../../utils/constants";

export default function Footer() {
  return (
    <footer className="bg-white border-t border-border mt-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-sm text-slate-500">
          <div>
            <h3 className="font-semibold text-slate-700 mb-2">Web3BlockSet</h3>
            <p>
              A curated dataset for empirical research in Blockchain-Oriented
              Software Engineering (BOSE).
            </p>
          </div>
          <div>
            <h3 className="font-semibold text-slate-700 mb-2">Links</h3>
            <ul className="space-y-1">
              <li>
                <a href={GITHUB_REPO_URL} target="_blank" rel="noopener noreferrer" className="hover:text-primary-600 transition-colors">
                  GitHub Repository
                </a>
              </li>
              <li>
                <a href={ZENODO_URL} target="_blank" rel="noopener noreferrer" className="hover:text-primary-600 transition-colors">
                  Zenodo Dataset
                </a>
              </li>
            </ul>
          </div>
          <div>
            <h3 className="font-semibold text-slate-700 mb-2">License</h3>
            <p>MIT License &copy; 2025</p>
            <p className="mt-1">Soares et al.</p>
          </div>
        </div>
      </div>
    </footer>
  );
}
