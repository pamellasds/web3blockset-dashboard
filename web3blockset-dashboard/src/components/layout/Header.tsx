import { NavLink } from "react-router-dom";
import { BarChart3, Lightbulb, Github } from "lucide-react";
import { GITHUB_REPO_URL } from "../../utils/constants";

const navItems = [
  { to: "/", label: "Dashboard", icon: BarChart3 },
  // { to: "/filter", label: "Explore Data", icon: Filter },
  { to: "/research", label: "Research Insights", icon: Lightbulb },
];

export default function Header() {
  return (
    <header className="bg-white border-b border-border sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <NavLink to="/" className="flex items-center gap-2 font-bold text-lg text-primary-700">
            <img src={`${import.meta.env.BASE_URL}logo.png`} alt="Web3BlockSet" className="h-8 object-contain" />
          </NavLink>

          <nav className="flex items-center gap-1">
            {navItems.map(({ to, label, icon: Icon }) => (
              <NavLink
                key={to}
                to={to}
                end={to === "/"}
                className={({ isActive }) =>
                  `flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? "bg-primary-50 text-primary-700"
                      : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                  }`
                }
              >
                <Icon size={16} />
                <span className="hidden md:inline">{label}</span>
              </NavLink>
            ))}
            <a
              href={GITHUB_REPO_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="ml-2 p-2 text-slate-500 hover:text-slate-900 transition-colors"
              title="GitHub Repository"
            >
              <Github size={18} />
            </a>
          </nav>
        </div>
      </div>
    </header>
  );
}
