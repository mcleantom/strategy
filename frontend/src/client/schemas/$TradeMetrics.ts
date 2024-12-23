/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $TradeMetrics = {
    properties: {
        total_trades: {
            type: 'number',
            isRequired: true,
        },
        total_winning_trades: {
            type: 'number',
            isRequired: true,
        },
        total_losing_trades: {
            type: 'number',
            isRequired: true,
        },
        starting_balance: {
            type: 'number',
            isRequired: true,
        },
        finishing_balance: {
            type: 'number',
            isRequired: true,
        },
        longs_count: {
            type: 'number',
            isRequired: true,
        },
        longs_percentage: {
            type: 'number',
            isRequired: true,
        },
        shorts_count: {
            type: 'number',
            isRequired: true,
        },
        shorts_percentage: {
            type: 'number',
            isRequired: true,
        },
        fee: {
            type: 'number',
            isRequired: true,
        },
        total_open_trades: {
            type: 'number',
            isRequired: true,
        },
        open_pl: {
            type: 'number',
            isRequired: true,
        },
    },
} as const;
