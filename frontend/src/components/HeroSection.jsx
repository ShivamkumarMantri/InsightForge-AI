import React from 'react';
import { Sparkles } from 'lucide-react';

/**
 * HeroSection Component
 * Premium futuristic hero section:
 * - Striking typography with subtle electric gradient highlight on "into answers."
 * - Soft ambient blue/violet radial blur glow behind the heading
 * - Futuristic floating badge with micro-pulsing AI spark dot
 * - Clean, professional, executive supporting narrative
 */
export default function HeroSection() {
  return (
    <section className="hero-section" aria-label="Hero Introduction">
      {/* Soft blue/violet ambient atmosphere backlight */}
      <div className="hero-rgb-ambient" aria-hidden="true" />
      <div className="hero-ambient-orb blue" aria-hidden="true" />
      <div className="hero-ambient-orb violet" aria-hidden="true" />

      {/* Eyebrow badge */}
      <div className="hero-eyebrow">
        <span className="eyebrow-badge">
          <span className="eyebrow-ai-spark-dot"></span>
          <Sparkles size={11} className="eyebrow-sparkle" />
          <span>AI DATA INTELLIGENCE PLATFORM</span>
        </span>
      </div>

      {/* Main heading with soft glowing backdrop */}
      <div className="hero-heading-container">
        <div className="hero-heading-backlight" aria-hidden="true"></div>
        <h1 className="hero-heading">
          Turn your data <span className="hero-gradient-text">into answers.</span>
        </h1>
      </div>

      {/* Supporting text */}
      <p className="hero-subtext">
        Upload a dataset. Ask questions naturally. Let InsightForge analyze,
        visualize and explain what matters.
      </p>
    </section>
  );
}
