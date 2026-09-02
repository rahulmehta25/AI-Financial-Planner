/**
 * Simulation path visualization using Recharts.
 * Replaced the previous Three.js implementation which added ~472 kB to the bundle
 * with no functional advantage over a 2D line chart for this use case.
 */
import React, { useMemo } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

interface ThreeVisualizationProps {
  results: {
    paths: number[][]
    finalValues: number[]
    timestamps: number[]
    confidenceIntervals?: {
      '10%': number[]
      '25%': number[]
      '50%': number[]
      '75%': number[]
      '90%': number[]
    }
  }
}

const COLORS = {
  p10: '#ef4444',
  p25: '#f97316',
  p50: '#22c55e',
  p75: '#3b82f6',
  p90: '#a855f7',
}

function formatCurrency(value: number): string {
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`
  if (value >= 1_000) return `$${(value / 1_000).toFixed(0)}K`
  return `$${value.toFixed(0)}`
}

const ThreeVisualization: React.FC<ThreeVisualizationProps> = ({ results }) => {
  const { timestamps, confidenceIntervals } = results

  const chartData = useMemo(() => {
    if (!confidenceIntervals || !timestamps) return []

    // Sample every N steps to keep the chart performant (max 120 points)
    const step = Math.max(1, Math.floor(timestamps.length / 120))
    return timestamps
      .filter((_, i) => i % step === 0)
      .map((t, idx) => {
        const origIdx = idx * step
        return {
          year: parseFloat(t.toFixed(1)),
          p10: confidenceIntervals['10%'][origIdx],
          p25: confidenceIntervals['25%'][origIdx],
          p50: confidenceIntervals['50%'][origIdx],
          p75: confidenceIntervals['75%'][origIdx],
          p90: confidenceIntervals['90%'][origIdx],
        }
      })
  }, [timestamps, confidenceIntervals])

  if (chartData.length === 0) return null

  return (
    <Card className="glass border-white/10">
      <CardHeader>
        <CardTitle className="text-base">Simulation Path Distribution</CardTitle>
        <CardDescription>Percentile bands across all simulated paths</CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={320}>
          <LineChart data={chartData} margin={{ top: 4, right: 16, left: 8, bottom: 4 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
            <XAxis
              dataKey="year"
              tickFormatter={(v) => `Y${v}`}
              stroke="rgba(255,255,255,0.3)"
              tick={{ fontSize: 11 }}
            />
            <YAxis
              tickFormatter={formatCurrency}
              stroke="rgba(255,255,255,0.3)"
              tick={{ fontSize: 11 }}
              width={64}
            />
            <Tooltip
              formatter={(value: number, name: string) => [formatCurrency(value), name]}
              labelFormatter={(label) => `Year ${label}`}
              contentStyle={{
                background: 'rgba(15,15,25,0.92)',
                border: '1px solid rgba(255,255,255,0.1)',
                borderRadius: 8,
                fontSize: 12,
              }}
            />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            <Line type="monotone" dataKey="p10" name="10th pct" stroke={COLORS.p10} dot={false} strokeWidth={1.5} />
            <Line type="monotone" dataKey="p25" name="25th pct" stroke={COLORS.p25} dot={false} strokeWidth={1.5} />
            <Line type="monotone" dataKey="p50" name="Median" stroke={COLORS.p50} dot={false} strokeWidth={2.5} />
            <Line type="monotone" dataKey="p75" name="75th pct" stroke={COLORS.p75} dot={false} strokeWidth={1.5} />
            <Line type="monotone" dataKey="p90" name="90th pct" stroke={COLORS.p90} dot={false} strokeWidth={1.5} />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}

export default ThreeVisualization
