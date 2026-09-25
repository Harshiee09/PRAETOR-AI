// Generated with openapi-typescript. Do not edit.
// PROVISIONAL document-workflow supplement; supplied backend OpenAPI lacks these endpoints.

export interface paths {
    "/v1/documents": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post: {
            parameters: {
                query?: never;
                header?: never;
                path?: never;
                cookie?: never;
            };
            requestBody: {
                content: {
                    "multipart/form-data": {
                        /** Format: binary */
                        file: string;
                    };
                };
            };
            responses: {
                /** @description Uploaded document metadata */
                201: {
                    headers: {
                        [name: string]: unknown;
                    };
                    content: {
                        "application/json": components["schemas"]["DocumentInfo"];
                    };
                };
            };
        };
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/documents/{document_id}": {
        parameters: {
            query?: never;
            header?: never;
            path: {
                document_id: string;
            };
            cookie?: never;
        };
        get: {
            parameters: {
                query?: never;
                header?: never;
                path: {
                    document_id: string;
                };
                cookie?: never;
            };
            requestBody?: never;
            responses: {
                /** @description Document and passages */
                200: {
                    headers: {
                        [name: string]: unknown;
                    };
                    content: {
                        "application/json": components["schemas"]["DocumentDetail"];
                    };
                };
            };
        };
        put?: never;
        post?: never;
        delete: {
            parameters: {
                query?: never;
                header?: never;
                path: {
                    document_id: string;
                };
                cookie?: never;
            };
            requestBody?: never;
            responses: {
                /** @description Forgotten */
                204: {
                    headers: {
                        [name: string]: unknown;
                    };
                    content?: never;
                };
            };
        };
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/documents/analyze": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post: {
            parameters: {
                query?: never;
                header?: never;
                path?: never;
                cookie?: never;
            };
            requestBody: {
                content: {
                    "application/json": components["schemas"]["DocumentAnalysisRequest"];
                };
            };
            responses: {
                /** @description Document analysis */
                200: {
                    headers: {
                        [name: string]: unknown;
                    };
                    content: {
                        "application/json": components["schemas"]["DocumentAnalysis"];
                    };
                };
            };
        };
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
        DocumentInfo: {
            document_id: string;
            filename: string;
            pages: number;
            unreadable_pages: number[];
            passage_count: number;
            words: number;
            uploaded_at: string;
            expires_at: string;
            warnings: string[];
        };
        DocumentPassage: {
            n: number;
            locator: string;
            page_start: number;
            page_end: number;
            text: string;
        };
        DocumentDetail: {
            document_id: string;
            filename: string;
            pages: number;
            unreadable_pages: number[];
            passage_count: number;
            words: number;
            uploaded_at: string;
            expires_at: string;
            warnings: string[];
            passages: components["schemas"]["DocumentPassage"][];
        };
        /** @enum {string} */
        DocumentTask: "ask" | "summary" | "risks" | "checklist" | "lawyer_questions" | "compare";
        /** Citation */
        DocumentCitation: {
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
            /** @enum {string} */
            kind: "document" | "law";
            document_id?: string | null;
            page_start?: number | null;
            page_end?: number | null;
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
        /** AskResponse */
        DocumentAnalysis: {
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
            citations: components["schemas"]["DocumentCitation"][];
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
            task: components["schemas"]["DocumentTask"];
            documents: {
                filename: string;
                pages_read: number[] | string;
                complete: boolean;
            }[];
            law_checked: boolean;
        };
        DocumentAnalysisRequest: {
            document_ids: string[];
            task: components["schemas"]["DocumentTask"];
            question?: string | null;
        };
    };
    responses: never;
    parameters: never;
    requestBodies: never;
    headers: never;
    pathItems: never;
}
export type $defs = Record<string, never>;
export type operations = Record<string, never>;
