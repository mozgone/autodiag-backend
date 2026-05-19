export interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
  tenant_id: string;
  is_active: boolean;
}

export interface ManagerStats {
  calls_count: number;
  calls_quality_avg: number;
  deals_created: number;
  deals_won: number;
  conversion_rate: number;
  revenue: number;
  plan_completion: number;
  crm_fill_rate: number;
  overdue_tasks: number;
  trend: 'up' | 'down' | 'stable';
}

export interface Manager {
  id: string;
  full_name: string;
  email: string | null;
  team_id: string | null;
  monthly_plan: number;
  is_active: boolean;
  avatar_url: string | null;
  created_at: string;
  stats?: ManagerStats;
}

export interface Recommendation {
  id: string;
  rec_type: 'strength' | 'growth' | 'alert' | 'forecast';
  title: string;
  content: string;
  priority: number;
  is_read: boolean;
  created_at: string;
}

export interface ManagerDetail extends Manager {
  recommendations: Recommendation[];
  weekly_history: Array<{
    week: number;
    revenue: number;
    calls: number;
    conversion: number;
    crm_fill: number;
    period: string;
  }>;
}

export interface OverviewStats {
  total_managers: number;
  active_deals: number;
  total_revenue_month: number;
  avg_conversion_rate: number;
  plan_completion_avg: number;
  top_performer: string | null;
  at_risk_deals: number;
}

export interface RevenueChartPoint {
  date: string;
  revenue: number;
  calls: number;
  conversion: number;
}

export interface RankingItem {
  rank: number;
  manager_id: string;
  full_name: string;
  revenue: number;
  plan_completion: number;
  calls_count: number;
  conversion_rate: number;
  trend: string;
}
