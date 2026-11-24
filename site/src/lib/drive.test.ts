import { describe, expect, it } from 'vitest';
import { parseDriveLink } from './drive';

const id = '1AbC-dEf_GhIjKlMnOp';
const file = { url: `https://drive.google.com/file/d/${id}/view`, embed: `https://drive.google.com/file/d/${id}/preview` };

describe('parseDriveLink', () => {
  it.each([
    `https://drive.google.com/file/d/${id}/view?usp=sharing`,
    `  https://drive.google.com/file/d/${id}/view?usp=drive_link  `,
    `https://drive.google.com/file/d/${id}`,
    `https://drive.google.com/file/u/0/d/${id}/edit`,
    `https://drive.google.com/open?id=${id}`,
    `https://drive.google.com/uc?export=download&id=${id}`,
  ])('reads file link %s', (link) => expect(parseDriveLink(link)).toEqual(file));

  it('keeps the resource key', () =>
    expect(parseDriveLink(`https://drive.google.com/file/d/${id}/view?resourcekey=0-abc`)?.embed).toBe(
      `${file.embed}?resourcekey=0-abc`,
    ));

  it('reads a folder as a link without a player', () =>
    expect(parseDriveLink(`https://drive.google.com/drive/u/1/folders/${id}?usp=sharing`)).toEqual({
      url: `https://drive.google.com/drive/folders/${id}`,
      embed: null,
    }));

  it('gives the same result for its own output', () => expect(parseDriveLink(file.url)).toEqual(file));

  it.each([
    '',
    null,
    'not a link',
    'javascript:alert(1)',
    `http://drive.google.com/file/d/${id}/view`,
    `https://drive.google.com.evil.com/file/d/${id}/view`,
    `https://evil.com/?x=https://drive.google.com/file/d/${id}/view`,
    'https://drive.google.com/drive/my-drive',
    'https://drive.google.com/file/d/"><script>/view',
  ])('rejects %s', (link) => expect(parseDriveLink(link)).toBeNull());
});
