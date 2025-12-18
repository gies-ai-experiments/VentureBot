import React, { useMemo } from 'react';

// ============================================
// Types
// ============================================
export type MarketSizeData = {
  tam: string;
  sam: string;
  som: string;
  currency: string;
};

export type TrendDataPoint = {
  year: string;
  value: number;
};

export type HeatmapData = {
  competitors: string[];
  metrics: string[];
  scores: number[][]; // [competitor_index][metric_index]
};

export type GraphData = {
  market_size?: MarketSizeData;
  market_trend?: TrendDataPoint[];
  competitor_heatmap?: HeatmapData;
};

// ============================================
// Funnel Chart (TAM/SAM/SOM)
// ============================================
export function FunnelChart({ data }: { data: MarketSizeData }) {
  const currency = data.currency || '$';
  
  return (
    <div className="chart-container funnel-chart">
      <h3>Market Size Opportunity</h3>
      <div className="funnel-stack">
        <div className="funnel-layer funnel-tam">
          <span className="funnel-label">TAM</span>
          <span className="funnel-value">{currency}{data.tam}</span>
          <span className="funnel-desc">Total Addressable Market</span>
        </div>
        <div className="funnel-layer funnel-sam">
          <span className="funnel-label">SAM</span>
          <span className="funnel-value">{currency}{data.sam}</span>
          <span className="funnel-desc">Serviceable Addressable Market</span>
        </div>
        <div className="funnel-layer funnel-som">
          <span className="funnel-label">SOM</span>
          <span className="funnel-value">{currency}{data.som}</span>
          <span className="funnel-desc">Serviceable Obtainable Market</span>
        </div>
      </div>
    </div>
  );
}

// ============================================
// Line Chart (Simple SVG)
// ============================================
export function TrendLineChart({ data }: { data: TrendDataPoint[] }) {
  const points = useMemo(() => {
    if (!data || data.length === 0) return '';
    
    const maxVal = Math.max(...data.map(d => d.value)) || 100;
    const width = 100; // SVG coordinate space
    const height = 50; 
    
    return data.map((d, i) => {
      const x = (i / (data.length - 1)) * width;
      const y = height - (d.value / maxVal) * height; // Invert Y
      return `${x},${y}`;
    }).join(' ');
  }, [data]);

  const fillPoints = `0,50 ${points} 100,50`;

  return (
    <div className="chart-container line-chart">
      <h3>Market Growth Trend</h3>
      <div className="line-chart-viz">
        <svg viewBox="0 0 100 50" preserveAspectRatio="none">
          <defs>
            <linearGradient id="lineGradient" x1="0" x2="0" y1="0" y2="1">
              <stop offset="0%" stopColor="var(--accent-secondary)" stopOpacity="0.5" />
              <stop offset="100%" stopColor="var(--accent-secondary)" stopOpacity="0" />
            </linearGradient>
          </defs>
          <polygon points={fillPoints} fill="url(#lineGradient)" />
          <polyline points={points} fill="none" stroke="var(--accent-primary)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          
          {data.map((d, i) => {
             const maxVal = Math.max(...data.map(p => p.value)) || 100;
             const x = data.length === 1 ? 50 : (i / (data.length - 1)) * 100;
             const y = 50 - (d.value / maxVal) * 50;
             return (
               <g key={i}>
                <circle cx={x} cy={y} r="2" fill="var(--bg-card)" stroke="var(--accent-primary)" strokeWidth="1" />
               </g>
             );
          })}
        </svg>
        <div className="chart-labels">
          {data.map((d) => (
            <div key={d.year} className="chart-label">
              <span className="year">{d.year}</span>
              <span className="val">{d.value}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ============================================
// Heatmap (Grid)
// ============================================
export function CompetitorHeatmap({ data }: { data: HeatmapData }) {
  const getScoreColor = (score: number) => {
    // 1-5 scale colors
    if (score >= 4.5) return 'var(--success)';
    if (score >= 3.5) return 'var(--accent-primary)';
    if (score >= 2.5) return 'var(--warning)';
    return 'var(--error)';
  };

  return (
    <div className="chart-container heatmap-chart">
      <h3>Competitor Comparison</h3>
      <div className="heatmap-grid" style={{ gridTemplateColumns: `auto repeat(${data.metrics.length}, 1fr)` }}>
        {/* Header Row */}
        <div className="heatmap-cell header corner"></div>
        {data.metrics.map(metric => (
          <div key={metric} className="heatmap-cell header metric">{metric}</div>
        ))}

        {/* Competitor Rows */}
        {data.competitors.map((comp, rowIndex) => (
          <React.Fragment key={comp}>
            <div className="heatmap-cell header competitor">{comp}</div>
            {data.scores[rowIndex]?.map((score, colIndex) => (
              <div key={`${rowIndex}-${colIndex}`} className="heatmap-cell value">
                <div 
                  className="score-dot" 
                  style={{ 
                    backgroundColor: getScoreColor(score),
                    opacity: score >= 1 ? 0.2 + (score * 0.15) : 0.1 
                  }}
                >
                  {score}
                </div>
              </div>
            ))}
          </React.Fragment>
        ))}
      </div>
    </div>
  );
}

// ============================================
// Main Chart Renderer
// ============================================
export function DataVisualizer({ data }: { data: GraphData }) {
  if (!data) return null;

  return (
    <div className="data-visualizer">
      {data.market_size && <FunnelChart data={data.market_size} />}
      <div className="charts-row">
        {data.market_trend && <TrendLineChart data={data.market_trend} />}
        {data.competitor_heatmap && <CompetitorHeatmap data={data.competitor_heatmap} />}
      </div>
    </div>
  );
}
