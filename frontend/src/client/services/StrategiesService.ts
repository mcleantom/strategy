/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Body_update_strategy_strategy__name__put } from '../models/Body_update_strategy_strategy__name__put';
import type { CreateStrategyRequest } from '../models/CreateStrategyRequest';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class StrategiesService {
    /**
     * Get Strategies
     * @returns string Successful Response
     * @throws ApiError
     */
    public static getStrategiesStrategiesGet(): CancelablePromise<Array<string>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/strategies',
        });
    }
    /**
     * Create Strategy
     * @returns any Successful Response
     * @throws ApiError
     */
    public static createStrategyStrategyPost({
        requestBody,
    }: {
        requestBody: CreateStrategyRequest,
    }): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/strategy',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Strategy
     * @returns string Successful Response
     * @throws ApiError
     */
    public static getStrategyStrategyNameGet({
        name,
    }: {
        name: string,
    }): CancelablePromise<string> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/strategy/{name}',
            path: {
                'name': name,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Update Strategy
     * @returns any Successful Response
     * @throws ApiError
     */
    public static updateStrategyStrategyNamePut({
        name,
        formData,
    }: {
        name: string,
        formData: Body_update_strategy_strategy__name__put,
    }): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/strategy/{name}',
            path: {
                'name': name,
            },
            formData: formData,
            mediaType: 'multipart/form-data',
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
