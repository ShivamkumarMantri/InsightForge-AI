import React from 'react';
import {
  TrendingUp,
  BarChart2,
  Award,
  Zap,
  ArrowRight,
  Sparkles
} from 'lucide-react';

/**
 * SuggestionCard Component
 * Futuristic 3D elevated suggestion cards with:
 * - Controlled colorful micro-gradient accents per card
 * - Layered glass surface with inner highlights
 * - Hover elevation and subtle light reflection
 * - Glowing arrow / action indicator
 */
export default function SuggestionCard({
  category = 'ANALYSIS',
  prompt = '',
  icon: Icon = Sparkles,
  accent = 'cyan', // 'cyan' | 'violet' | 'blue' | 'magenta' | 'emerald' | 'amber'
  index = 0,
  onSelect = () => {}
}) {
  // Determine accent by index if not passed directly
  const ACCENT_LIST = ['blue', 'violet', 'cyan', 'magenta'];
  const resolvedAccent = accent || ACCENT_LIST[index % ACCENT_LIST.length];

  return (
    <button
      type="button"
      className={`suggestion-card accent-${resolvedAccent}`}
      onClick={() => onSelect(prompt)}
      aria-label={`Suggested query: ${prompt}`}
    >
      {/* Subtle top edge glow reflection */}
      <span className="card-top-shine" aria-hidden="true"></span>

      <div className="suggestion-top-row">
        <div className="suggestion-badge">
          <span className="badge-glow-ring"></span>
          <Icon size={12} className="suggestion-icon" />
          <span>{category}</span>
        </div>

        <span className="suggestion-arrow-wrap">
          <ArrowRight size={13} className="suggestion-arrow" />
        </span>
      </div>

      <div className="suggestion-text">
        "{prompt}"
      </div>

      {/* Subtle micro ambient glow corner */}
      <span className="card-corner-glow" aria-hidden="true"></span>
    </button>
  );
}
