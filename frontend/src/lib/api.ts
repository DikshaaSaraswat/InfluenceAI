// Centralized client for the InfluenceAI FastAPI backend.
export const API_BASE_URL: string =
  (import.meta.env["VITE_API_BASE_URL"] as string | undefined)?.replace(/\/$/, "") || "http://127.0.0.1:8000";

export class ApiError extends Error {
  constructor(message: string, public status?: number) {
    super(message);
  }
}

async function request<T = any>(method: string, path: string, body?: unknown): Promise<T> {
  let res: Response;

  try {
    res = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers: body !== undefined ? { "Content-Type": "application/json" } : {},
      body: body !== undefined ? JSON.stringify(body) : null,
    });
  } catch {
    throw new ApiError(`Cannot reach the backend at ${API_BASE_URL}. Is the FastAPI server running?`);
  }

  const text = await res.text();
  let data: any = text;

  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    /* plain text */
  }

  if (!res.ok) {
    const detail = data?.detail ?? data?.message ?? data;
    throw new ApiError(
      `${res.status}: ${typeof detail === "string" ? detail : JSON.stringify(detail)}`,
      res.status
    );
  }

  return data as T;
}

export function asList(data: any): any[] {
  if (Array.isArray(data)) return data;

  if (data && typeof data === "object") {
    for (const k of ["data", "items", "results", "influencers", "followups", "follow_ups", "replies"]) {
      if (Array.isArray(data[k])) return data[k];
    }
  }

  return [];
}

export const api = {
  listInfluencers: () => request("GET", "/influencers"),
  createInfluencer: (body: Record<string, unknown>) => request("POST", "/influencers", body),
  analyzeInfluencer: (id: string | number, body: Record<string, unknown>) => request("POST", `/influencers/${id}/analyze`, body),
  updateStatus: (id: string | number, status: string) => request("PATCH", `/influencers/${id}/status`, { status }),
  updateEmail: (id: string | number, email: string) => request("PATCH", `/influencers/${id}/email`, { email }),
  updateProfileUrl: (id: string | number, profile_url: string) => request("PATCH", `/influencers/${id}/profile-url`, { profile_url }),

  generateDraftEmail: (id: string | number, body?: Record<string, unknown>) =>
    request("POST", `/influencers/${id}/draft-email`, body ?? {}),

  getDraftEmail: (id: string | number) =>
    request("GET", `/influencers/${id}/draft-email`),

  updateDraftEmail: (id: string | number, body: { subject: string; body: string }) =>
    request("PATCH", `/influencers/${id}/draft-email`, body),

  approveEmail: (id: string | number) =>
    request("PATCH", `/influencers/${id}/approve-email`),

  sendEmail: (id: string | number) =>
    request("POST", `/influencers/${id}/send-email`),

  listFollowups: () =>
    request("GET", "/followups"),

  updateDueFollowups: () =>
    request("POST", "/followups/update-due"),

  getFollowup: (id: string | number) =>
    request("GET", `/followups/${id}`),

  generateFollowup: (
    id: string | number,
    body: { name: string; niche: string; campaign: string }
  ) => request("POST", `/followups/${id}/generate`, body),

  updateFollowupDraft: (id: string | number, body: { subject: string; body: string }) =>
    request("PATCH", `/followups/${id}/draft`, body),

  approveFollowup: (id: string | number) =>
    request("PATCH", `/followups/${id}/approve`),

  sendFollowup: (id: string | number) =>
    request("POST", `/followups/${id}/send`),

  syncReplies: () =>
    request("POST", "/replies/sync"),

  analyzeReply: (id: string | number) =>
    request("POST", `/replies/${id}/analyze`),

  getReply: (id: string | number) =>
    request("GET", `/replies/${id}`),

  updateReplyDraft: (id: string | number, body: { suggested_reply: string }) =>
    request("PATCH", `/replies/${id}/draft`, body),

  approveReply: (id: string | number) =>
    request("PATCH", `/replies/${id}/approve`),

  sendReply: (id: string | number) =>
    request("POST", `/replies/${id}/send`),
};

export const pick = (o: any, ...keys: string[]) => {
  for (const k of keys) {
    if (o?.[k] !== undefined && o?.[k] !== null && o?.[k] !== "") {
      return o[k];
    }
  }

  return undefined;
};

export const inf = {
  id: (i: any) => pick(i, "id", "_id", "influencer_id"),
  name: (i: any) => pick(i, "name", "full_name") ?? "—",
  username: (i: any) => pick(i, "instagram_username", "username", "handle") ?? "",
  niche: (i: any) => pick(i, "niche", "category") ?? "",
  location: (i: any) => pick(i, "location", "city", "country") ?? "",
  followers: (i: any) => Number(pick(i, "followers", "followers_count", "follower_count") ?? 0),
  email: (i: any) => pick(i, "email") ?? "",
  status: (i: any) => String(pick(i, "status") ?? "new"),
};

export const draftOf = (d: any) => ({
  subject: String(
    pick(d, "subject", "draft_subject", "email_subject") ??
    pick(d?.draft, "subject") ??
    ""
  ),

  body: String(
    pick(d, "body", "draft_body", "email_body", "email_draft", "content") ??
    pick(d?.draft, "body") ??
    ""
  ),
});
