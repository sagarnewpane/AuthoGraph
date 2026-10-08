# AuthoGraph

Private image storage and sharing, built with Django REST Framework and SvelteKit 2/Svelte 5.

## Features

- Image library, search, sorting, bulk uploads, and original downloads.
- Visible watermarks, UTF-8 hidden attribution messages, and editable metadata.
- Public `/verify-image` checker: read hidden attribution without an account. New protected copies include a signed creator username and a pixel digest; legacy plain messages are labeled unsigned. Verification uploads are not saved in the library.
- Separate protected previews and downloads; originals stay private.
- Email-verified share links with optional password, expiry, view limit, and download permission.
- Editable recipient filenames and separate preview/download watermark choices. Shared previews follow the saved watermark by default; downloads without a visible watermark retain other selected protection.
- Metadata controls for shared previews and downloads: include saved metadata, strip embedded metadata, or have downloads follow the preview. Stripping removes source EXIF, ICC profiles, and text fields while keeping pixel watermarks.
- Link revocation, access requests, recorded views/downloads/attempts, and email preferences.
- Profile, avatars, password reset/change, and account deletion.
- Optional external AI processing with explicit consent. Disabled unless an HTTPS service is configured.

Screenshots cannot be prevented. Hidden messages are fragile and may disappear after image transformations. AI resistance is experimental.

## Local setup

Python 3.10+ and Node 22.12+ are required.

```sh
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
./setup_project.sh
./start_project.sh
```

Set independent random secrets in `backend/.env`, and use the same `INTERNAL_PROXY_SECRET` in both environment files. Configure `HOST_MAIL` and `MAIL_PASSWORD` for recipient verification and password reset. Real credentials belong only in ignored `.env` files.

Frontend: http://localhost:5173. Backend: http://127.0.0.1:8000.

```sh
.venv/bin/python backend/manage.py createsuperuser
```

## Validation

```sh
.venv/bin/python backend/manage.py test backend.tests
npm --prefix frontend run check
npm --prefix frontend run build
```

## Deployment

- Set `DJANGO_DEBUG=false`, real allowed hosts, `FRONTEND_URL`, and strong, independent signing/encryption/proxy secrets.
- Run Django migrations and collectstatic. Use `backend.deployment` settings for production.
- Build the frontend and run its Node adapter with `ORIGIN=https://your-domain`, `BACKEND_URL`, and `BODY_SIZE_LIMIT=22M`.
- Terminate HTTPS at a trusted proxy. Keep the Django service private; configure `TRUST_PROXY_HTTPS=true` only for that proxy.
- **Never expose `/media/` or the private media directory through a web server, CDN, or public bucket.** Image bytes must go through authorized endpoints.
- Use PostgreSQL (`DATABASE_URL`) for concurrent workloads and Redis (`REDIS_URL`) for shared rate limits across workers. SQLite and local cache are development defaults.
- Originals accept JPG, PNG, and WebP up to 20 MB / 25 million pixels. Storage quota defaults to 2 GB per account and is configurable via `STORAGE_QUOTA_BYTES`.
- Back up the database, private media, `IMAGE_MASTER_KEY`, and `DJANGO_SECRET_KEY`. Losing the image key makes encrypted originals unreadable; changing the signing key invalidates existing signed attribution unless retained as a Django signing fallback.

New originals use AES-GCM with wrapped per-image keys. Historical AES-CBC originals remain readable. To wrap historical raw keys, back up first and run:

```sh
.venv/bin/python backend/manage.py wrap_image_keys
.venv/bin/python backend/manage.py wrap_image_keys --apply
```

For key rotation, retain the old value as `IMAGE_PREVIOUS_MASTER_KEY`, set the new `IMAGE_MASTER_KEY`, wrap keys with `--apply`, verify readability, then remove the previous key.

The app does not include subscription billing or organization/team accounts yet.

## Design

The redesign uses the UI/UX Pro Max guidance documented in `design-system/authograph/MASTER.md`, the original logo recolored with CSS, and Poppins in workspace headings. The generated architectural image and its prompt are documented there.
