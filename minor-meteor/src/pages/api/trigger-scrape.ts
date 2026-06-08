import type { APIRoute } from 'astro';
import { createClient } from '@supabase/supabase-js';
import { Octokit } from '@octokit/rest';

export const prerender = false;

const supabaseUrl = import.meta.env.SUPABASE_URL || process.env.SUPABASE_URL;
const supabaseKey = import.meta.env.SUPABASE_SERVICE_ROLE_KEY || process.env.SUPABASE_SERVICE_ROLE_KEY;

const supabase = createClient(supabaseUrl, supabaseKey);

export const POST: APIRoute = async () => {
  try {
    const { data: githubData, error: dbError } = await supabase
      .from('settings')
      .select('value')
      .eq('key', 'github')
      .single();

    if (dbError || !githubData) {
      return new Response(
        JSON.stringify({ error: 'GitHub configuration not found in Supabase settings.' }),
        { status: 400, headers: { 'Content-Type': 'application/json' } }
      );
    }

    const { repo_owner, repo_name, pat_token } = githubData.value;

    if (!repo_owner || !repo_name || !pat_token) {
      return new Response(
        JSON.stringify({ error: 'GitHub repository configuration details are incomplete.' }),
        { status: 400, headers: { 'Content-Type': 'application/json' } }
      );
    }

    const octokit = new Octokit({ auth: pat_token });

    // Trigger repository dispatch to run GHA workflow
    await octokit.actions.createWorkflowDispatch({
      owner: repo_owner,
      repo: repo_name,
      workflow_id: 'scrape.yml',
      ref: 'main',
    });

    return new Response(JSON.stringify({ success: true }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });
  } catch (err: any) {
    return new Response(JSON.stringify({ error: err.message }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' },
    });
  }
};
