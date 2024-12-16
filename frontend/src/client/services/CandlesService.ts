/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { GetTickersResponseItem } from '../models/GetTickersResponseItem';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class CandlesService {
    /**
     * Get Tickers
     * @returns GetTickersResponseItem Successful Response
     * @throws ApiError
     */
    public static getTickersTickersGet(): CancelablePromise<Array<GetTickersResponseItem>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/tickers',
        });
    }
    /**
     * Import Candles
     * @returns any Successful Response
     * @throws ApiError
     */
    public static importCandlesCandlesImportExchangeSymbolPost({
        exchange,
        symbol,
        startDate,
    }: {
        exchange: string,
        symbol: string,
        startDate: string,
    }): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/candles/import/{exchange}/{symbol}',
            path: {
                'exchange': exchange,
                'symbol': symbol,
            },
            query: {
                'start_date': startDate,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
