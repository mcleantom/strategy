/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Trade = {
    properties: {
        type: {
            type: 'string',
            isRequired: true,
        },
        entry_price: {
            type: 'number',
            isRequired: true,
        },
        exit_price: {
            type: 'number',
            isRequired: true,
        },
        quantity: {
            type: 'number',
            isRequired: true,
        },
        pnl: {
            type: 'number',
            isRequired: true,
        },
        entry_timestamp: {
            type: 'string',
            isRequired: true,
            format: 'date-time',
        },
        exit_timestamp: {
            type: 'string',
            isRequired: true,
            format: 'date-time',
        },
    },
} as const;
