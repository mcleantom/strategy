/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $BacktestResult = {
    properties: {
        trades: {
            type: 'array',
            contains: {
                type: 'Trade',
            },
            isRequired: true,
        },
        equity_curve: {
            type: 'array',
            contains: {
                type: 'EquityCurveItem',
            },
            isRequired: true,
        },
        baseline: {
            type: 'array',
            contains: {
                type: 'BaselineItem',
            },
            isRequired: true,
        },
    },
} as const;
