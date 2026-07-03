export interface Article {
  id: number;
  name: string;
  html_url: string;
  body: string;
  created_at: string;
  updated_at: string;
}

export interface ZendeskApiResponse {
  count: number;
  next_page: string | null;
  page: number;
  page_count: number;
  per_page: number;
  previous_page: string | null;
  articles: Article[];
}