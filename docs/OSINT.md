# Synthetic OSINT

Phase 11 teaches source evaluation and entity correlation using a bundled
catalog of fabricated organization, domain, directory, repository, document
and social-content records.

## Safety boundary

- The catalog is local, static and explicitly marked synthetic.
- All hostnames use the reserved `.invalid` domain.
- Example IP addresses use documentation-only address space.
- The service performs substring search over its bundled catalog; it does not
  resolve DNS, fetch web pages, contact social platforms or query external
  search engines.
- Search is read-only. Results include source type, observation time,
  simulated confidence, collection method, indicators and related synthetic
  entity IDs.
- No credentials or real personal data are included.

## Dashboard workflow

1. Open the OSINT section in the local dashboard.
2. Search for an indicator such as `analyst-amber`,
   `staging.northstar-lab.invalid` or `northstar-lab.invalid`.
3. Compare records that share a synthetic entity ID.
4. Record the source ID and collection method before drawing a conclusion.
5. Separate observed fixture content from analyst inference; every result is
   labeled `SIMULATED`.

## API

```bash
curl http://127.0.0.1:8096/health
curl 'http://127.0.0.1:8096/search?q=analyst-amber'
```

The browser uses the same-origin route `/api/osint/search?q=...`. Queries are
limited to 80 allow-listed ASCII characters. External URLs and control
characters are rejected.

The synthetic dataset is an educational fixture, not intelligence about a real
organization or person.
