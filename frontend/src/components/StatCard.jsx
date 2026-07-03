import React from 'react';
import { TrendingUp, TrendingDown } from 'lucide-react';
 
const StatCard = ({ label, value, delta, deltaLabel, icon: Icon, color = 'accent' }) => (
  <div className={`stat-card stat-card--${color}`}>
    <div className="stat-card-top">
      <span className="stat-card-label">{label}</span>
      {Icon && (
        <div className="stat-card-icon">
          <Icon size={18} />
        </div>
      )}
    </div>
    <div className="stat-card-value">{value}</div>
    {delta !== undefined && (
      <div className={`stat-card-delta ${delta >= 0 ? 'positive' : 'negative'}`}>
        {delta >= 0 ? <TrendingUp size={13} /> : <TrendingDown size={13} />}
        <span>{Math.abs(delta)}% {deltaLabel}</span>
      </div>
    )}
  </div>
);
 
export default StatCard;