import axios from "axios";
import dotenv from "dotenv";
import path from "path";
import  { type Article, type ZendeskApiResponse } from "./types.ts";

dotenv.config({ path: path.join(__dirname, "..", ".env") });

const baseUrl = process.env.BASE_URL;
const zendeskApi = process.env.ZENDESK_API;

if (!baseUrl || !zendeskApi) {
    throw new Error("Missing required env vars: BASE_URL and ZENDESK_API must both be set");
}

const normalizedBaseUrl = (baseUrl.startsWith("http") ? baseUrl : `https://${baseUrl}`).replace(/\/$/, "");
const normalizedApiPath = zendeskApi.startsWith("/") ? zendeskApi : `/${zendeskApi}`;

export const getArticles = async (): Promise<Article[]> => {
    const articles: Article[] = [];
    //this part I only ran 1 time to get the articles, but I can make it loop through all pages if needed
    let url: string | null = `${normalizedBaseUrl}${normalizedApiPath}`;

        const response = await axios.get<ZendeskApiResponse>(url);
        const data = response.data as ZendeskApiResponse;

        if (data && Array.isArray(data.articles)) {
            articles.push(...data.articles);
        }


    return articles;
};
