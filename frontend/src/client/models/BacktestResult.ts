/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { BaselineItem } from './BaselineItem';
import type { EquityItem } from './EquityItem';
import type { PerformanceMetrics } from './PerformanceMetrics';
import type { RiskMetrics } from './RiskMetrics';
import type { Trade } from './Trade';
import type { TradeMetrics } from './TradeMetrics';
export type BacktestResult = {
    trades: Array<Trade>;
    equity_curve: Array<EquityItem>;
    baseline: Array<BaselineItem>;
    performance_metrics: PerformanceMetrics;
    risk_metrics: RiskMetrics;
    trade_metrics: TradeMetrics;
};

