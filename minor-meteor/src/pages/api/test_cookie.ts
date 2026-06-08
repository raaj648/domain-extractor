import type { APIRoute } from 'astro';
import { createClient } from '@supabase/supabase-js';

export const prerender = false;

const supabaseUrl = import.meta.env.SUPABASE_URL;
const supabaseKey = import.meta.env.SUPABASE_SERVICE_ROLE_KEY;

const supabase = createClient(supabaseUrl as string, supabaseKey as string);

function stringifyCookies(cookiesObj: Record<string, any>) {
    const parts: string[] = [];
    for (const [k, v] of Object.entries(cookiesObj || {})) {
        if (typeof v === 'string' && v.trim()) parts.push(`${k}=${encodeURIComponent(v.trim())}`);
    }
    return parts.join('; ');
}

function extractTitle(html: string) {
    const m = html.match(/<title[^>]*>([\s\S]*?)<\/title>/i);
    if (!m) return null;
    return m[1].replace(/\s+/g, ' ').trim();
}

export const POST: APIRoute = async ({ request }) => {
    try {
        const body = await request.json().catch(() => ({}));
        const url = typeof body?.url === 'string' ? body.url.trim() : '';
        const testUrl = url || 'https://member.expireddomains.net/domains/combinedexpired/';

        const { data: settingsData, error } = await supabase.from('settings').select('*');
        if (error) throw error;

        const settings: Record<string, any> = {};
        settingsData?.forEach((s) => {
            settings[s.key] = s.value;
        });

        const cookiesConf = settings.cookies || {};
        if (!cookiesConf || typeof cookiesConf !== 'object') {
            return new Response(JSON.stringify({ ok: false, error: 'Missing cookies config in settings.' }), {
                status: 400,
                headers: { 'Content-Type': 'application/json' },
            });
        }

        const cookieHeader = stringifyCookies(cookiesConf);
        if (!cookieHeader) {
            return new Response(JSON.stringify({ ok: false, error: 'No cookie entries with non-empty values were found in settings.cookies.' }), {
                status: 400,
                headers: { 'Content-Type': 'application/json' },
            });
        }

        const resp = await fetch(testUrl, {
            method: 'GET',
            headers: {
                'User-Agent':
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                Accept: 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                Cookie: cookieHeader,
            },
            redirect: 'follow',
        });

        const text = await resp.text();

        const loginRequired =
            /Login\s*\/\s*Sign\s*Up/i.test(text) || /You must be logged in/i.test(text);

        return new Response(
            JSON.stringify({
                ok: true,
                status: resp.status,
                url: testUrl,
                loginRequired,
                title: extractTitle(text),
                html: text,
            }),
            { status: 200, headers: { 'Content-Type': 'application/json' } }
        );
    } catch (err: any) {
        return new Response(JSON.stringify({ ok: false, error: err?.message || 'Unknown error' }), {
            status: 500,
            headers: { 'Content-Type': 'application/json' },
        });
    }
};
