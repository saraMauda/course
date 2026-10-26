import type { MetadataRoute } from 'next';
import { siteUrl } from '@/lib/shared';

// The course content sits behind login; only the landing page is public.
export default function robots(): MetadataRoute.Robots {
  return {
    rules: { userAgent: '*', allow: '/$', disallow: ['/admin', '/dashboard', '/docs', '/api', '/auth'] },
    sitemap: `${siteUrl}/sitemap.xml`,
  };
}
