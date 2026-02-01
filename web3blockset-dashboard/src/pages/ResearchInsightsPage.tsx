import { Compass, Layers, Users, Clock, Shield, BookOpen } from "lucide-react";
import type { LucideIcon } from "lucide-react";

interface ResearchQuestion {
  id: string;
  question: string;
  description: string;
  relevantColumns: string[];
}

interface ResearchTheme {
  icon: LucideIcon;
  title: string;
  color: string;
  bgColor: string;
  borderColor: string;
  description: string;
  questions: ResearchQuestion[];
}

const themes: ResearchTheme[] = [
  {
    icon: Compass,
    title: "Technology Adoption and Platform Migration",
    color: "text-blue-700",
    bgColor: "bg-blue-50",
    borderColor: "border-blue-200",
    description:
      "Understanding how blockchain platforms and tools are adopted by community developers, and how adoption patterns change over time.",
    questions: [
      {
        id: "1a",
        question:
          "Which blockchain platforms and tools are adopted by community developers, and how do adoption patterns change over time?",
        description:
          "Existing BOSE studies focus on theoretical platform comparisons but lack empirical adoption data. The community dataset records explicit tool mentions across 2,787 repositories with timestamps tracking adoption chronology.",
        relevantColumns: ["raw_text", "owner_used", "created_at", "data_source"],
      },
      {
        id: "1b",
        question:
          "What factors predict blockchain tool abandonment, and how long do projects remain maintained?",
        description:
          "The Provider Dataset includes 20.5% archived repositories with archived flags, combined with creation and update timestamps measuring lifespan.",
        relevantColumns: ["archived", "created_at", "updated_at", "repository_category"],
      },
    ],
  },
  {
    icon: Layers,
    title: "Cross-Platform Development Challenges",
    color: "text-purple-700",
    bgColor: "bg-purple-50",
    borderColor: "border-purple-200",
    description:
      "Investigating how platform architecture affects developer problems and whether different blockchain platforms exhibit distinct challenges.",
    questions: [
      {
        id: "2a",
        question:
          "Do different blockchain platforms exhibit distinct developer challenges and issue types?",
        description:
          "The repository classification distinguishes 34 Blockchain Core/Protocol repositories (Ethereum, Solana, Near, Algorand, etc.). The repository_classification column combined with labels and clean_text enables cross-platform issue comparison.",
        relevantColumns: ["repository_category", "labels", "clean_text", "owner"],
      },
      {
        id: "2b",
        question:
          "How does programming language choice correlate with issue resolution time and developer sentiment across blockchain platforms?",
        description:
          "The language metadata combined with creation and closing timestamps addresses this question. The language distribution (TypeScript 26.8%, JavaScript 17.2%, Rust 13.2%, Solidity 11.5%, Go 9%) reflects distinct platform ecosystems.",
        relevantColumns: ["language", "created_at", "closed_at", "repository_category"],
      },
    ],
  },
  {
    icon: Users,
    title: "Developer Collaboration and Contribution Patterns",
    color: "text-teal-700",
    bgColor: "bg-teal-50",
    borderColor: "border-teal-200",
    description:
      "Examining collaboration networks, contributor roles, interaction patterns, and retention in blockchain open-source projects.",
    questions: [
      {
        id: "3a",
        question:
          "How do collaboration networks differ between core maintainers and community contributors across blockchain platforms?",
        description:
          "Author and owner fields capture interaction patterns. Activity frequency across timestamps can distinguish core maintainers from occasional contributors. The comment_authors field captures multi-party discussions.",
        relevantColumns: ["author", "author_id", "owner", "comment_authors", "created_at"],
      },
      {
        id: "3b",
        question:
          "What factors predict long-term contributor retention in blockchain projects?",
        description:
          "Repeated author_id values across creation timestamps measure sustained contribution over the temporal span (2012-2024).",
        relevantColumns: ["author_id", "created_at", "repository", "owner"],
      },
    ],
  },
  {
    icon: Clock,
    title: "Issue Resolution and Maintainability Patterns",
    color: "text-amber-700",
    bgColor: "bg-amber-50",
    borderColor: "border-amber-200",
    description:
      "Analyzing how issue resolution time varies across repository categories, organizational size, and project popularity.",
    questions: [
      {
        id: "4a",
        question:
          "How does issue resolution time vary across repository categories and organizational size?",
        description:
          "The 383,387 provider documents include comments count, creation, update, and closing timestamps measuring maintainer responsiveness. The dataset spans 40 Educational Resource/Boilerplate, 37 SDK/Library, 34 Blockchain Core/Protocol repositories.",
        relevantColumns: [
          "comments_count",
          "created_at",
          "updated_at",
          "closed_at",
          "repository_category",
        ],
      },
      {
        id: "4b",
        question:
          "Does repository popularity correlate with maintainer responsiveness and code contribution acceptance rates?",
        description:
          "Stars and forks metrics indicate project popularity. The relationship between popularity and pull request acceptance ratios can measure contribution dynamics.",
        relevantColumns: ["stars", "forks", "type", "state", "created_at", "closed_at"],
      },
    ],
  },
  {
    icon: Shield,
    title: "Security Vulnerability Disclosure and Response",
    color: "text-red-700",
    bgColor: "bg-red-50",
    borderColor: "border-red-200",
    description:
      "Understanding vulnerability disclosure practices across blockchain platforms, where security is paramount due to immutability and financial stakes.",
    questions: [
      {
        id: "5a",
        question:
          "How do vulnerability disclosure and resolution practices differ across blockchain platforms and repository types?",
        description:
          "The labels column captures security-related tags across issues and pull requests. Combined with timestamps, it measures time-to-resolution for security issues across the 381 provider repositories.",
        relevantColumns: ["labels", "created_at", "closed_at", "repository_category"],
      },
      {
        id: "5b",
        question:
          "How do security vulnerabilities in provider repositories propagate to community projects?",
        description:
          "The community dataset's explicit references to provider tools (captured in raw_text) allow tracking whether security discussions in provider repositories appear in the 2,787 community repositories.",
        relevantColumns: ["raw_text", "data_source", "owner_used", "matching_keywords"],
      },
    ],
  },
  {
    icon: BookOpen,
    title: "Evolution of Development Terminology",
    color: "text-emerald-700",
    bgColor: "bg-emerald-50",
    borderColor: "border-emerald-200",
    description:
      "Tracking how blockchain development terminology evolves and which terms predict emerging technologies or practices.",
    questions: [
      {
        id: "6a",
        question:
          "How does blockchain development terminology evolve, and which terms predict emerging technologies or practices?",
        description:
          "The temporal dimension combined with clean_text enables longitudinal vocabulary analysis from 2012 to 2024, capturing discussions through periods of ecosystem evolution and providing evidence for studying how developer language adapts to technological change.",
        relevantColumns: ["clean_text", "stemmed_text", "created_at", "year"],
      },
    ],
  },
];

export default function ResearchInsightsPage() {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900">Research Insights</h1>
        <p className="text-slate-500 mt-2 max-w-3xl">
          Web3BlockSet combines provider and community repositories, temporal coverage (2012-2024),
          and repository categorization to enable diverse empirical studies. Below are open research
          questions proposed in the paper, with relevant dataset columns highlighted.
        </p>
      </div>

      <div className="space-y-8">
        {themes.map((theme) => (
          <section key={theme.title} className={`rounded-xl border ${theme.borderColor} ${theme.bgColor} p-6`}>
            <div className="flex items-start gap-3 mb-4">
              <div className={`p-2 rounded-lg bg-white/80 ${theme.color}`}>
                <theme.icon size={22} />
              </div>
              <div>
                <h2 className={`text-lg font-bold ${theme.color}`}>{theme.title}</h2>
                <p className="text-sm text-slate-600 mt-1">{theme.description}</p>
              </div>
            </div>

            <div className="space-y-4">
              {theme.questions.map((q) => (
                <div key={q.id} className="bg-white/80 rounded-lg border border-white/50 p-5">
                  <div className="flex items-baseline gap-2 mb-2">
                    <span className="text-xs font-bold text-slate-400 uppercase">RQ {q.id}</span>
                  </div>
                  <h3 className="font-semibold text-slate-800 text-sm leading-relaxed mb-2">
                    {q.question}
                  </h3>
                  <p className="text-sm text-slate-600 leading-relaxed mb-3">
                    {q.description}
                  </p>
                  <div className="flex flex-wrap gap-1.5">
                    {q.relevantColumns.map((col) => (
                      <span
                        key={col}
                        className="inline-block px-2 py-0.5 bg-slate-100 text-slate-600 rounded text-xs font-mono"
                      >
                        {col}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </section>
        ))}
      </div>

      {/* Methodology note */}
      <div className="mt-10 bg-white rounded-xl border border-border p-6">
        <h2 className="text-base font-semibold text-slate-800 mb-2">About the Dataset</h2>
        <p className="text-sm text-slate-600 leading-relaxed">
          Web3BlockSet was collected using a Mining Software Repositories (MSR) approach. The Provider
          Dataset includes 383,387 documents from 381 official repositories across 80 organizations identified
          from the Awesome Web3 list. The Community Dataset contains 8,209 documents from 4,500 adopter
          repositories found via keyword-based search. Repository categorization was performed using a hybrid
          LLM-assisted and human-validated approach with 92.4% inter-rater agreement.
        </p>
        <p className="text-sm text-slate-600 leading-relaxed mt-3">
          For full methodology details and citation information, see the{" "}
          <a href="#/" className="text-primary-600 hover:underline">Dashboard page</a>.
        </p>
      </div>
    </div>
  );
}
