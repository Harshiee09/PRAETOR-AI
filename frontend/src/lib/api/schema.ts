// Generated with openapi-typescript. Do not edit.
// Source: docs/api/openapi.json (authoritative)

export interface paths {
    "/v1/ask": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Answer a question from the indexed sources, with citations */
        post: operations["ask_v1_ask_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/sources/{chunk_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** The full stored passage behind a citation card */
        get: operations["source_v1_sources__chunk_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/healthz": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Liveness and readiness (no key needed) */
        get: operations["healthz_v1_healthz_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/stats": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Corpus, index, model and server counters */
        get: operations["stats_v1_stats_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
}
export type webhooks = Record<string, never>;
export interface components {
    schemas: {
        /** AskRequest */
        AskRequest: {
            /**
             * Question
             * @description The user's question, in any supported language.
             */
            question: string;
            /**
             * Mode
             * @description Retrieval configuration; keep `full` in production.
             * @default full
             * @enum {string}
             */
            mode: "full" | "hybrid_rerank" | "hybrid" | "dense" | "keyword";
            /**
             * Explain
             * @description Include per-stage retrieval ranks, timings and validator details.
             * @default false
             */
            explain: boolean;
            /**
             * Use Cache
             * @description Reuse a cached answer for the same question and system version.
             * @default true
             */
            use_cache: boolean;
        };
        /** AskResponse */
        AskResponse: {
            /**
             * Answer Markdown
             * @description Markdown answer. A high-stakes answer starts with a safety block.
             */
            answer_markdown: string;
            /** Language */
            language: string;
            /**
             * Confidence
             * @enum {string}
             */
            confidence: "high" | "medium" | "low";
            /**
             * Abstained
             * @description True when the system declined to answer (thin evidence or a refused request).
             */
            abstained: boolean;
            /** Citations */
            citations: components["schemas"]["Citation"][];
            /**
             * Warnings
             * @description Deterministic notes to show with the answer: repeal, transition, state-law coverage, removed sentences.
             */
            warnings: string[];
            /** Jurisdiction Note */
            jurisdiction_note: string;
            /**
             * Disclaimer
             * @description Show once with every answer.
             */
            disclaimer: string;
            /**
             * Trace Id
             * @description Equals the X-Request-ID response header.
             */
            trace_id: string;
            /**
             * Provider
             * @description `ollama`, `extractive` (no model; verbatim passages) or null.
             */
            provider: string | null;
            /** Model */
            model?: string | null;
            classification: components["schemas"]["Classification"];
            /**
             * Cached
             * @default false
             */
            cached: boolean;
            /** Latency Ms */
            latency_ms: number;
            /** Explain */
            explain?: {
                [key: string]: unknown;
            } | null;
        };
        /** Citation */
        Citation: {
            /**
             * Id
             * @description The [S#] marker used in answer_markdown.
             */
            id: string;
            /**
             * Chunk Id
             * @description Pass to GET /v1/sources/{chunk_id} for the full passage.
             */
            chunk_id: string;
            /** Title */
            title: string;
            /**
             * Locator
             * @description Where in the source: `s. 106`, `paras 12-15`, `pp. 8-9`.
             */
            locator: string;
            /** Authority */
            authority: string;
            /**
             * Jurisdiction
             * @description `IN` for central law; ISO 3166-2 code for a state amendment.
             */
            jurisdiction: string;
            /**
             * Status
             * @description `in_force`, `repealed`, `partially_in_force` or `n/a` (judgments).
             */
            status: string;
            /** Source Url */
            source_url: string;
            /** Retrieved At */
            retrieved_at: string;
            /**
             * Quote
             * @description Verbatim excerpt (<= 300 characters) cut from the stored text in code.
             */
            quote: string;
            /** Section Heading */
            section_heading?: string | null;
            /** Court */
            court?: string | null;
            /** Decision Date */
            decision_date?: string | null;
            /**
             * Citation
             * @description Neutral or reporter citation as printed in the source record.
             */
            citation?: string | null;
        };
        /** Classification */
        Classification: {
            /** Domain */
            domain: string;
            /** Intent */
            intent: string;
            /** High Stakes */
            high_stakes: boolean;
        };
        /** Error */
        Error: {
            error: components["schemas"]["ErrorBody"];
        };
        /** ErrorBody */
        ErrorBody: {
            /** Code */
            code: string;
            /** Message */
            message: string;
            /** Request Id */
            request_id: string;
        };
        /** Health */
        Health: {
            /**
             * Status
             * @description `degraded`: no answer model, so answers fall back to verbatim passages; `down`: the index is unusable.
             * @enum {string}
             */
            status: "ok" | "degraded" | "down";
            /** Checks */
            checks: {
                [key: string]: string;
            };
        };
        /** Source */
        Source: {
            /** Chunk Id */
            chunk_id: string;
            /** Doc Type */
            doc_type: string;
            /** Title */
            title: string;
            /** Locator */
            locator: string;
            /**
             * Text
             * @description The full stored passage.
             */
            text: string;
            /** Authority */
            authority: string;
            /** Jurisdiction */
            jurisdiction: string;
            /** Status */
            status: string;
            /** Language */
            language: string;
            /** Source Url */
            source_url: string;
            /** Retrieved At */
            retrieved_at: string;
            /** Licence */
            licence: string;
            /** Page Start */
            page_start?: number | null;
            /** Page End */
            page_end?: number | null;
            /** Act Title */
            act_title?: string | null;
            /** Section */
            section?: string | null;
            /** Section Heading */
            section_heading?: string | null;
            /** Case Title */
            case_title?: string | null;
            /** Court */
            court?: string | null;
            /** Decision Date */
            decision_date?: string | null;
            /** Citation */
            citation?: string | null;
        };
        /** Stats */
        Stats: {
            /** Documents */
            documents: {
                [key: string]: number;
            };
            /** Chunks */
            chunks: {
                [key: string]: number;
            };
            /** Index */
            index: {
                [key: string]: unknown;
            };
            /** Model */
            model: {
                [key: string]: unknown;
            };
            /** Prompt Version */
            prompt_version: string;
            /** Cache Entries */
            cache_entries: number;
            /** Uptime S */
            uptime_s: number;
            /** Requests */
            requests: {
                [key: string]: number;
            };
            /** Answer Latency Ms */
            answer_latency_ms: {
                [key: string]: number | null;
            };
        };
    };
    responses: never;
    parameters: never;
    requestBodies: never;
    headers: never;
    pathItems: never;
}
export type $defs = Record<string, never>;
export interface operations {
    ask_v1_ask_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["AskRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AskResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Error"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Error"];
                };
            };
            /** @description Unprocessable Entity */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Error"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Error"];
                };
            };
        };
    };
    source_v1_sources__chunk_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                chunk_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Source"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Error"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Error"];
                };
            };
            /** @description Unprocessable Entity */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Error"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Error"];
                };
            };
        };
    };
    healthz_v1_healthz_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Health"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Health"];
                };
            };
        };
    };
    stats_v1_stats_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Stats"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Error"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Error"];
                };
            };
            /** @description Unprocessable Entity */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Error"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Error"];
                };
            };
        };
    };
}
