export interface DriveLink {
  /** Clean link that is stored and opened in a new tab. */
  url: string;
  /** Player address for an iframe. Null for a folder, which can only be opened. */
  embed: string | null;
}

const ID = /^[\w-]{10,}$/;

/** Reads a Google Drive share link (file or folder). Returns null for anything else. The result is rebuilt from the id. */
export function parseDriveLink(input: string | null | undefined): DriveLink | null {
  let u: URL;
  try {
    u = new URL((input ?? '').trim());
  } catch {
    return null;
  }
  if (u.protocol !== 'https:' || u.hostname !== 'drive.google.com') return null;

  // older files are only reachable with the resource key from their share link
  const key = u.searchParams.get('resourcekey');
  const query = key && /^[\w-]+$/.test(key) ? `?resourcekey=${key}` : '';

  const folder = /\/folders\/([^/]+)/.exec(u.pathname)?.[1];
  if (folder) return ID.test(folder) ? { url: `https://drive.google.com/drive/folders/${folder}${query}`, embed: null } : null;

  const id =
    /\/file\/(?:u\/\d+\/)?d\/([^/]+)/.exec(u.pathname)?.[1] ??
    (/^\/(open|uc)$/.test(u.pathname) ? u.searchParams.get('id') : null);
  if (!id || !ID.test(id)) return null;
  const base = `https://drive.google.com/file/d/${id}`;
  return { url: `${base}/view${query}`, embed: `${base}/preview${query}` };
}
