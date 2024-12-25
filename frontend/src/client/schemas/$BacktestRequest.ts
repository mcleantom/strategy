/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $BacktestRequest = {
    properties: {
        timeframe: {
            type: 'ETimeframe',
            isRequired: true,
        },
        strategy: {
            type: 'string',
            isRequired: true,
        },
    },
} as const;
