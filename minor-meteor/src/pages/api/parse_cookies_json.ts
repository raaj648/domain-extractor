import type { APIRoute } from 'astro';

export const prerender = false;

export const POST: APIRoute = async ({ request }) => {
    try {
        const { json } = await request.json();
        if (typeof json !== 'string') {
            return new Response(JSON.stringify({ error: 'Missing json string.' }), { status: 400 });
        }

        const parsed = JSON.parse(json);

        if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
            return new Response(JSON.stringify({ error: 'Cookie JSON must be an object of cookieName -> cookieValue.' }), { status: 400 });
        }

        // Convert values to strings and filter blanks
        const out: Record<string, string> = {};
        for (const [k, v] of Object.entries(parsed as Record<string, unknown>)) {
            if (typeof v === 'string' && v.trim()) out[k] = v.trim();
        }

        if (Object.keys(out).length === 0) {
            return new Response(JSON.stringify({ error: 'No cookie entries with non-empty values were found.' }), { status: 400 });
        }

        return new Response(JSON.stringify({ success: true, cookies: out }), { status: 200, headers: { 'Content-Type': 'application/json' } });
    } catch (err: any) {
        return new Response(JSON.stringify({ error: err?.message || 'Invalid JSON' }), { status: 400, headers: { 'Content-Type': 'application/json' } });
    }
};
