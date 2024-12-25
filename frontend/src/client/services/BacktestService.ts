/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { BacktestRequest } from '../models/BacktestRequest';
import type { BacktestResult } from '../models/BacktestResult';
import type { ListBacktestIdsResultItem } from '../models/ListBacktestIdsResultItem';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class BacktestService {
    /**
     * List Backtest Ids
     * @returns ListBacktestIdsResultItem Successful Response
     * @throws ApiError
     */
    public static listBacktestIdsBacktestsGet(): CancelablePromise<Array<ListBacktestIdsResultItem>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/backtests',
        });
    }
    /**
     * Run Backtest
     * @returns BacktestResult Successful Response
     * @throws ApiError
     */
    public static runBacktestBacktestsPost({
        requestBody,
    }: {
        requestBody: BacktestRequest,
    }): CancelablePromise<BacktestResult> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/backtests',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Backtest Result
     * @returns BacktestResult Successful Response
     * @throws ApiError
     */
    public static getBacktestResultBacktestsBacktestIdGet({
        backtestId,
    }: {
        backtestId: number,
    }): CancelablePromise<BacktestResult> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/backtests/{backtest_id}',
            path: {
                'backtest_id': backtestId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Delete Backtest Result
     * @returns any Successful Response
     * @throws ApiError
     */
    public static deleteBacktestResultBacktestsBacktestIdDelete({
        backtestId,
    }: {
        backtestId: number,
    }): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/backtests/{backtest_id}',
            path: {
                'backtest_id': backtestId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
