'use client';

import { useMemo } from 'react';
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import type { DimReductionResponse } from '@/types/analytics';

interface ScatterPlot2DProps {
  data: DimReductionResponse;
}

// Generate distinct colors for different documents
const COLORS = [
  '#3B82F6', // blue
  '#EF4444', // red
  '#10B981', // green
  '#F59E0B', // amber
  '#8B5CF6', // purple
  '#EC4899', // pink
  '#14B8A6', // teal
  '#F97316', // orange
  '#6366F1', // indigo
  '#84CC16', // lime
];

export default function ScatterPlot2D({ data }: ScatterPlot2DProps) {
  // Group points by document
  const groupedData = useMemo(() => {
    const groups: Record<string, typeof data.points> = {};

    data.points.forEach((point) => {
      const key = point.document_name;
      if (!groups[key]) {
        groups[key] = [];
      }
      groups[key].push(point);
    });

    return Object.entries(groups).map(([name, points], index) => ({
      name,
      data: points,
      color: COLORS[index % COLORS.length],
    }));
  }, [data.points]);

  return (
    <div className="w-full">
      <ResponsiveContainer width="100%" height={600}>
        <ScatterChart
          margin={{
            top: 20,
            right: 20,
            bottom: 20,
            left: 20,
          }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            type="number"
            dataKey="x"
            name="Component 1"
            label={{ value: 'Component 1', position: 'insideBottom', offset: -10 }}
          />
          <YAxis
            type="number"
            dataKey="y"
            name="Component 2"
            label={{ value: 'Component 2', angle: -90, position: 'insideLeft' }}
          />
          <Tooltip
            content={({ active, payload }) => {
              if (active && payload && payload.length > 0) {
                const point = payload[0].payload;
                return (
                  <div className="bg-background border rounded-lg shadow-lg p-3 max-w-xs">
                    <p className="font-semibold text-sm mb-1">{point.document_name}</p>
                    <p className="text-xs text-muted-foreground mb-2">
                      Chunk {point.chunk_index}
                    </p>
                    <p className="text-xs line-clamp-3">{point.text_preview}</p>
                    <div className="flex gap-4 mt-2 text-xs text-muted-foreground">
                      <span>x: {point.x.toFixed(3)}</span>
                      <span>y: {point.y.toFixed(3)}</span>
                    </div>
                  </div>
                );
              }
              return null;
            }}
          />
          <Legend
            wrapperStyle={{
              paddingTop: '20px',
              maxHeight: '100px',
              overflowY: 'auto',
            }}
          />
          {groupedData.map((group) => (
            <Scatter
              key={group.name}
              name={group.name}
              data={group.data}
              fill={group.color}
              shape="circle"
            />
          ))}
        </ScatterChart>
      </ResponsiveContainer>

      {/* Stats */}
      <div className="mt-4 text-sm text-muted-foreground text-center">
        Showing {data.total_points} chunks across {groupedData.length} document(s) •
        Method: {data.method.toUpperCase()}
        {data.explained_variance && (
          <> • Explained variance: {(data.explained_variance * 100).toFixed(1)}%</>
        )}
      </div>
    </div>
  );
}
