/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { BaselineItem } from './BaselineItem';
import type { EquityItem } from './EquityItem';
import type { Trade } from './Trade';
export type BacktestResult = {
    trades: Array<Trade>;
    equity_curve: Array<EquityItem>;
    baseline: Array<BaselineItem>;
};

