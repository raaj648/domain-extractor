import type { APIRoute } from 'astro';
import { createClient } from '@supabase/supabase-js';
import dns from 'dns/promises';

export const prerender = false;

const supabaseUrl = import.meta.env.SUPABASE_URL || process.env.SUPABASE_URL;
const supabaseKey = import.meta.env.SUPABASE_SERVICE_ROLE_KEY || process.env.SUPABASE_SERVICE_ROLE_KEY;

const supabase = createClient(supabaseUrl, supabaseKey);

async function notifyTelegram(token: string, chatId: string, text: string) {
  if (!token || !chatId) return;
  const url = `https://api.telegram.org/bot${token}/sendMessage`;
  try {
    await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ chat_id: chatId, text, parse_mode: 'Markdown' }),
    });
  } catch (e) {
    console.error('Telegram notification error:', e);
  }
}

export const GET: APIRoute = async () => {
  const startTime = Date.now();
  const checkedDomains: string[] = [];
  let availableCount = 0;
  let errorMessage: string | null = null;
  let status = 'success';

  try {
    // 1. Fetch settings
    const { data: settingsData } = await supabase.from('settings').select('*');
    const settings: Record<string, any> = {};
    settingsData?.forEach((s) => {
      settings[s.key] = s.value;
    });

    const telegramSettings = settings.telegram || {};
    const botToken = telegramSettings.bot_token;
    const chatId = telegramSettings.chat_id;
    const notifyDeleteDay = telegramSettings.notify_on_delete_day !== false;
    const notifyAvailable = telegramSettings.notify_on_available !== false;

    // 2. Query domains deleting today or in the past
    const today = new Date().toISOString().split('T')[0];
    const { data: domainsToCheck, error: queryError } = await supabase
      .from('tracked_domains')
      .select('*')
      .eq('status', 'pending_delete')
      .lte('delete_date', today);

    if (queryError) throw queryError;

    if (domainsToCheck && domainsToCheck.length > 0) {
      for (const domainRecord of domainsToCheck) {
        const domain = domainRecord.domain;
        checkedDomains.push(domain);

        // Deletion day reminder
        if (domainRecord.delete_date === today && !domainRecord.notified_delete_day) {
          if (notifyDeleteDay) {
            await notifyTelegram(
              botToken,
              chatId,
              `⏰ *Reminder:* \`${domain}\` is deleting TODAY. Starting active monitoring...`
            );
          }
          await supabase
            .from('tracked_domains')
            .update({ notified_delete_day: true })
            .eq('domain', domain);
        }

        // DNS availability check
        let isAvailable = false;
        try {
          // Check if nameservers resolve
          await dns.resolveNs(domain);
        } catch (dnsError: any) {
          // If DNS resolveNs fails, check error code.
          // ENOTFOUND/ENODATA usually indicates the domain does not resolve/exist anymore.
          if (dnsError.code === 'ENOTFOUND' || dnsError.code === 'ENODATA') {
            isAvailable = true;
          }
        }

        if (isAvailable) {
          availableCount++;
          // Update domain status in database
          await supabase
            .from('tracked_domains')
            .update({
              status: 'available',
              last_checked_at: new Date().toISOString(),
              notified_available: true,
            })
            .eq('domain', domain);

          if (notifyAvailable && !domainRecord.notified_available) {
            await notifyTelegram(
              botToken,
              chatId,
              `🎉 *Alert: Domain is Available!*\n` +
              `🌐 *Domain:* \`${domain}\`\n` +
              `🔗 [Register Domain](https://www.namecheap.com/domains/registration/results/?domain=${domain})`
            );
          }
        } else {
          // Check if delete date has passed. If yes, it got registered or renewed by someone else.
          const deleteDate = new Date(domainRecord.delete_date);
          const yesterday = new Date();
          yesterday.setDate(yesterday.getDate() - 1);

          if (deleteDate < yesterday) {
            await supabase
              .from('tracked_domains')
              .update({
                status: 'registered',
                last_checked_at: new Date().toISOString(),
              })
              .eq('domain', domain);
          } else {
            await supabase
              .from('tracked_domains')
              .update({
                last_checked_at: new Date().toISOString(),
              })
              .eq('domain', domain);
          }
        }
      }
    }

    // Log the successful run
    await supabase.from('cron_runs').insert({
      duration_ms: Date.now() - startTime,
      domains_checked: checkedDomains,
      domains_available: availableCount,
      status: 'success',
    });

    return new Response(
      JSON.stringify({ success: true, checked: checkedDomains.length, available: availableCount }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (err: any) {
    status = 'failed';
    errorMessage = err.message || 'Unknown error occurred';

    // Log the failure
    await supabase.from('cron_runs').insert({
      duration_ms: Date.now() - startTime,
      domains_checked: checkedDomains,
      domains_available: 0,
      status: 'failed',
      error_message: errorMessage,
    });

    return new Response(JSON.stringify({ success: false, error: errorMessage }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' },
    });
  }
};
