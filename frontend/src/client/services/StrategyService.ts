/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { BacktestRequest } from '../models/BacktestRequest';
import type { BacktestResult } from '../models/BacktestResult';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class StrategyService {
    /**
     * Run Strategy
     * @returns BacktestResult Successful Response
     * @throws ApiError
     */
    public static runStrategyBacktestPost({
        strategyName,
        requestBody,
    }: {
        strategyName: string,
        requestBody: BacktestRequest,
    }): CancelablePromise<BacktestResult> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/backtest',
            query: {
                'strategy_name': strategyName,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
