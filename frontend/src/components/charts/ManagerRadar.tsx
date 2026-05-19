import React from 'react';
import { RadarChart, PolarGrid, PolarAngleAxis, Radar, ResponsiveContainer } from 'recharts';

interface Props {
  stats: {
    calls_count: number;
    calls_quality_avg: number;
    conversion_rate: number;
    crm_fill_rate: number;
    plan_completion: number;
  };
}

export default function ManagerRadar({ stats }: Props) {
  const data = [
    { subject: 'Звонки', value: Math.min((stats.calls_count / 60) * 100, 100) },
    { subject: 'Качество', value: (stats.calls_quality_avg / 10) * 100 },
    { subject: 'Конверсия', value: Math.min(stats.conversion_rate * 2, 100) },
    { subject: 'CRM', value: stats.crm_fill_rate },
    { subject: 'План', value: Math.min(stats.plan_completion, 100) },
  ];
  return (
    <ResponsiveContainer width="100%" height={200}>
      <RadarChart data={data}>
        <PolarGrid stroke="#e2e8f0" />
        <PolarAngleAxis dataKey="subject" tick={{ fontSize: 12, fill: '#64748b' }} />
        <Radar dataKey="value" stroke="#6366f1" fill="#6366f1" fillOpacity={0.15} strokeWidth={2} />
      </RadarChart>
    </ResponsiveContainer>
  );
}
