/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Exchange } from '../models/Exchange';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class ExchangesService {
    /**
     * Get Exchanges Symbols
     * @returns string Successful Response
     * @throws ApiError
     */
    public static getExchangesSymbolsExchangeExchangeSymbolsGet({
        exchange,
    }: {
        exchange: Exchange,
    }): CancelablePromise<Array<string>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/exchange/{exchange}/symbols',
            path: {
                'exchange': exchange,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
