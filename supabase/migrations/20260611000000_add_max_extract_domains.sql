-- Add max_extract_domains to settings table
INSERT INTO settings (key, value) VALUES
  ('max_extract_domains', '1000'::text::jsonb)
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;
