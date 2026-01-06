import { supabase } from "../lib/supabase";

// src/api/authFetch.ts
export async function authFetch(
    input: RequestInfo,
    init: RequestInit = {}
  ) {
    const {
      data: { session },
    } = await supabase.auth.getSession();
  
    console.log("SESSION", session); // 👈 ADD THIS
  
    if (!session) {
      throw new Error("Not authenticated");
    }
  
    console.log("ACCESS TOKEN (first 20 chars):", session.access_token.slice(0, 20));
  
    return fetch(input, {
      ...init,
      headers: {
        ...(init.headers || {}),
        Authorization: `Bearer ${session.access_token}`,
      },
    });
  }
  