/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $ListBacktestIdsResultItem = {
    properties: {
        id: {
            type: 'number',
            isRequired: true,
        },
        strategy_name: {
            type: 'string',
            isRequired: true,
        },
        date_created: {
            type: 'string',
            isRequired: true,
            format: 'date-time',
        },
    },
} as const;
