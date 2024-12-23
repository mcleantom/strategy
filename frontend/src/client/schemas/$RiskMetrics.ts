/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $RiskMetrics = {
    properties: {
        total_losing_streak: {
            type: 'number',
            isRequired: true,
        },
        largest_losing_trade: {
            type: 'number',
            isRequired: true,
        },
        largest_winning_trade: {
            type: 'number',
            isRequired: true,
        },
        total_winning_streak: {
            type: 'number',
            isRequired: true,
        },
        current_streak: {
            type: 'number',
            isRequired: true,
        },
        expectancy: {
            type: 'number',
            isRequired: true,
        },
        expected_net_profit: {
            type: 'number',
            isRequired: true,
        },
        average_holding_period: {
            type: 'number',
            isRequired: true,
        },
        gross_profit: {
            type: 'number',
            isRequired: true,
        },
        gross_loss: {
            type: 'number',
            isRequired: true,
        },
        max_drawdown: {
            type: 'number',
            isRequired: true,
        },
    },
} as const;
