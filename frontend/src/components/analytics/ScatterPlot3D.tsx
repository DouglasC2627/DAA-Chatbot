'use client';

import { useMemo } from 'react';
import dynamic from 'next/dynamic';
import type { DimReductionResponse } from '@/types/analytics';
import type { PlotParams } from 'react-plotly.js';

// Dynamically import Plot to avoid SSR issues
const Plot = dynamic(() => import('react-plotly.js'), { ssr: false }) as React.ComponentType<PlotParams>;

interface ScatterPlot3DProps {
  data: DimReductionResponse;
}

// Generate distinct colors for different documents
const COLORS = [
  '#3B82F6', '#EF4444', '#10B981', '#F59E0B', '#8B5CF6',
  '#EC4899', '#14B8A6', '#F97316', '#6366F1', '#84CC16',
];

export default function ScatterPlot3D({ data }: ScatterPlot3DProps) {
  // Group points by document and create traces
  const traces = useMemo(() => {
    const groups: Record<string, typeof data.points> = {};

    data.points.forEach((point) => {
      const key = point.document_name;
      if (!groups[key]) {
        groups[key] = [];
      }
      groups[key].push(point);
    });

    return Object.entries(groups).map(([name, points], index) => ({
      type: 'scatter3d' as const,
      mode: 'markers' as const,
      name: name,
      x: points.map((p) => p.x),
      y: points.map((p) => p.y),
      z: points.map((p) => p.z || 0),
      text: points.map(
        (p) => `${p.document_name}<br>Chunk ${p.chunk_index}<br>${p.text_preview.slice(0, 100)}...`
      ),
      hovertemplate: '<b>%{text}</b><br>' +
        'x: %{x:.3f}<br>' +
        'y: %{y:.3f}<br>' +
        'z: %{z:.3f}<br>' +
        '<extra></extra>',
      marker: {
        size: 5,
        color: COLORS[index % COLORS.length],
        opacity: 0.8,
        line: {
          color: 'rgba(255, 255, 255, 0.5)',
          width: 0.5,
        },
      },
    }));
  }, [data.points]);

  return (
    <div className="w-full">
      <Plot
        data={traces}
        layout={{
          autosize: true,
          height: 700,
          scene: {
            xaxis: { title: 'Component 1' },
            yaxis: { title: 'Component 2' },
            zaxis: { title: 'Component 3' },
            camera: {
              eye: { x: 1.5, y: 1.5, z: 1.5 },
            },
          },
          hovermode: 'closest',
          showlegend: true,
          legend: {
            x: 1,
            xanchor: 'right',
            y: 1,
          },
          margin: {
            l: 0,
            r: 0,
            b: 0,
            t: 40,
          },
        }}
        config={{
          responsive: true,
          displayModeBar: true,
          displaylogo: false,
          modeBarButtonsToRemove: ['toImage'],
          modeBarButtonsToAdd: [
            {
              name: 'Reset',
              icon: {
                width: 1000,
                height: 1000,
                path: 'M500,200L500,800M200,500L800,500',
              },
              click: function (gd: any) {
                // @ts-expect-error - Plotly is available globally from react-plotly.js
                Plotly.relayout(gd, {
                  'scene.camera': {
                    eye: { x: 1.5, y: 1.5, z: 1.5 },
                  },
                });
              },
            },
          ],
        }}
        style={{ width: '100%', height: '100%' }}
      />

      {/* Stats */}
      <div className="mt-4 text-sm text-muted-foreground text-center">
        Showing {data.total_points} chunks across {traces.length} document(s) •
        Method: {data.method.toUpperCase()}
        {data.explained_variance && (
          <> • Explained variance: {(data.explained_variance * 100).toFixed(1)}%</>
        )}
      </div>

      {/* Interaction Hint */}
      <div className="mt-2 text-xs text-muted-foreground text-center">
        💡 Click and drag to rotate • Scroll to zoom • Double-click to reset view
      </div>
    </div>
  );
}
