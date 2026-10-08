<script lang="ts">
	import Brand from '$lib/product/Brand.svelte';
	import { api } from '$lib/product/api';
	import {
		LockKeyhole,
		ArrowRight,
		ShieldCheck,
		Download,
		Mail,
		ArrowLeft,
		Check
	} from 'lucide-svelte';
	import type { PageData } from './$types';
	export let data: PageData;
	let email = '';
	let password = '';
	let otp = '';
	let step = 'email';
	let needsPassword = false;
	let busy = false;
	let error = '';
	let canRequest = false;
	let message = '';
	let requested = false;
	let image: {
		image_url: string;
		image_name: string;
		allow_download: boolean;
		download_without_watermark: boolean;
		protection_features: Record<string, boolean>;
	} | null = null;
	async function initiate() {
		busy = true;
		error = '';
		canRequest = false;
		try {
			const response = await fetch(`/api/access/${data.token}/initiate`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ email, password: password || undefined })
			});
			const result = await response.json();
			if (!response.ok) {
				canRequest = !!result.can_request_access;
				throw new Error(result.error || result.detail || 'Unable to send a verification code.');
			}
			if (result.requires_password) {
				needsPassword = true;
			} else {
				step = 'otp';
			}
		} catch (e) {
			error = e instanceof Error ? e.message : 'Request failed.';
		} finally {
			busy = false;
		}
	}
	async function verify() {
		busy = true;
		error = '';
		try {
			image = await api<typeof image>(`/api/access/${data.token}/verify`, {
				method: 'POST',
				body: JSON.stringify({ email, otp })
			});
			step = 'image';
		} catch (e) {
			error = e instanceof Error ? e.message : 'Verification failed.';
		} finally {
			busy = false;
		}
	}
	async function requestAccess() {
		busy = true;
		error = '';
		try {
			await api(`/api/access/${data.token}/request`, {
				method: 'POST',
				body: JSON.stringify({ email, message })
			});
			requested = true;
			canRequest = false;
		} catch (e) {
			error = e instanceof Error ? e.message : 'Request failed.';
		} finally {
			busy = false;
		}
	}
</script>

<svelte:head
	><title>Private image · AuthoGraph</title><meta
		name="robots"
		content="noindex,nofollow"
	/></svelte:head
>
<main id="main" class="share-page">
	<header>
		<Brand /><span class="badge"><LockKeyhole aria-hidden="true" size={12} />Private share</span>
	</header>
	{#if step === 'image' && image}<section class="viewer">
			<div class="viewer-heading">
				<div>
					<span class="eyebrow">SHARED WITH YOU</span>
					<h1>{image.image_name}</h1>
					<p class="muted small">Verified as {email}</p>
				</div>
				{#if image.allow_download}<a
						href={`/api/access/${data.token}/download`}
						class="btn primary"
						download
						><Download aria-hidden="true" size={16} />{image.download_without_watermark
							? 'Download without watermark'
							: 'Download image'}</a
					>{/if}
			</div>
			{#if error}<div class="error" role="alert">{error}</div>{/if}
			<div class="viewer-image">
				<img
					src={image.image_url}
					alt={image.image_name}
					on:error={() =>
						(error =
							'Your viewing session expired or access was revoked. Reload this page to verify again.')}
				/>
			</div>
			<div class="row between wrap" style="margin-top:20px">
				<span class="small muted"
					><ShieldCheck aria-hidden="true" size={15} style="display:inline;vertical-align:middle" /> Shared
					through a verified session</span
				><span class="small muted">Respect the creator’s usage permissions.</span>
			</div>
		</section>{:else}<section class="share-gate">
			<div class="gate-icon">
				{#if step === 'otp'}<Mail aria-hidden="true" size={28} />{:else}<LockKeyhole
						aria-hidden="true"
						size={28}
					/>{/if}
			</div>
			<span class="eyebrow">A LITTLE PRIVACY GOES A LONG WAY</span>
			<h1>
				{requested
					? 'Request sent.'
					: step === 'otp'
						? 'Check your inbox.'
						: 'You’ve been invited in.'}
			</h1>
			<p>
				{requested
					? 'The image owner will review your request. Once approved, return here and verify your email.'
					: step === 'otp'
						? `Enter the six-digit code sent to ${email}. It expires in five minutes.`
						: 'Verify your email to view this private image. The creator stays in control of access.'}
			</p>
			{#if error}<div class="error" role="alert">{error}</div>{/if}{#if requested}<button
					class="btn"
					on:click={() => {
						requested = false;
						step = 'email';
					}}>Back to verification</button
				>{:else if canRequest}<form class="form-stack" on:submit|preventDefault={requestAccess}>
					<div class="field">
						<label for="request-message"
							>Message to the creator <span class="muted">(optional)</span></label
						><textarea
							id="request-message"
							bind:value={message}
							maxlength="2000"
							placeholder="Let them know why you need access."></textarea>
					</div>
					<button class="btn primary" disabled={busy}
						>{busy ? 'Sending…' : 'Request access'}<ArrowRight
							aria-hidden="true"
							size={16}
						/></button
					><button
						type="button"
						class="btn quiet"
						on:click={() => {
							canRequest = false;
							error = '';
						}}>Use another email</button
					>
				</form>{:else if step === 'otp'}<form class="form-stack" on:submit|preventDefault={verify}>
					<div class="field">
						<label for="code">Verification code</label><input
							id="code"
							class="otp-input"
							type="text"
							inputmode="numeric"
							autocomplete="one-time-code"
							pattern={'[0-9]{6}'}
							maxlength="6"
							bind:value={otp}
							required
							placeholder="000000"
						/>
					</div>
					<button class="btn primary" disabled={busy}
						>{busy ? 'Verifying…' : 'View image'}<ArrowRight aria-hidden="true" size={16} /></button
					><button class="btn quiet" type="button" disabled={busy} on:click={initiate}
						>Send a new code</button
					><button
						class="btn quiet"
						type="button"
						on:click={() => {
							step = 'email';
							error = '';
						}}><ArrowLeft aria-hidden="true" size={14} />Change email</button
					>
				</form>{:else}<form class="form-stack" on:submit|preventDefault={initiate}>
					<div class="field">
						<label for="viewer-email">Your email address</label><input
							id="viewer-email"
							type="email"
							bind:value={email}
							required
							autocomplete="email"
							placeholder="you@studio.com"
						/>
					</div>
					{#if needsPassword}<div class="field">
							<label for="link-password">Link password</label><input
								id="link-password"
								type="password"
								bind:value={password}
								required
								autocomplete="current-password"
							/><small>Ask the creator for this link’s password.</small>
						</div>{/if}<button class="btn primary" disabled={busy}
						>{busy ? 'Sending…' : 'Continue with email'}<ArrowRight
							aria-hidden="true"
							size={16}
						/></button
					>
				</form>{/if}
			<div class="gate-note">
				<ShieldCheck aria-hidden="true" size={15} /><span
					>Your access may be recorded by the image owner.</span
				>
			</div>
		</section>{/if}
	<footer>
		Made by them. Shared on their terms.<a href="/"
			>Learn about AuthoGraph <ArrowRight aria-hidden="true" size={12} /></a
		>
	</footer>
</main>

<style>
	.share-page {
		min-height: 100vh;
		display: flex;
		flex-direction: column;
	}
	.share-page header {
		height: 88px;
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 0 6%;
		border-bottom: 1px solid var(--line);
		background: white;
	}
	.share-gate {
		width: calc(100% - 40px);
		max-width: 460px;
		margin: 64px auto;
		padding: 38px;
		background: white;
		border: 1px solid var(--line);
		border-radius: 16px;
	}
	.gate-icon {
		width: 64px;
		height: 64px;
		background: var(--studio-soft);
		color: var(--studio);
		border-radius: 16px;
		display: grid;
		place-items: center;
		margin-bottom: 28px;
	}
	.share-gate > .eyebrow {
		font-size: 12px;
	}
	.share-gate h1 {
		font-size: 29px;
		margin: 14px 0;
	}
	.share-gate > p {
		font-size: 13px;
		color: var(--muted-ink);
		margin-bottom: 28px;
	}
	.share-gate > .error {
		margin-bottom: 20px;
	}
	.gate-note {
		display: flex;
		gap: 8px;
		font-size: 12px;
		color: var(--muted-ink);
		padding-top: 24px;
		margin-top: 24px;
		border-top: 1px solid var(--line);
		line-height: 1.6;
	}
	.otp-input {
		letter-spacing: 8px;
		font-size: 25px;
		text-align: center;
		min-height: 60px !important;
	}
	.share-page footer {
		margin-top: auto;
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 16px;
		flex-wrap: wrap;
		padding: 28px 6%;
		font-size: 12px;
		color: var(--muted-ink);
		border-top: 1px solid var(--line);
	}
	footer a {
		display: flex;
		gap: 6px;
		align-items: center;
	}
	.viewer {
		width: 100%;
		max-width: 1200px;
		padding: 40px;
		margin: 0 auto;
	}
	.viewer-heading {
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 24px;
		flex-wrap: wrap;
		margin-bottom: 28px;
	}
	.viewer-heading h1 {
		font-size: 27px;
		margin: 12px 0;
		overflow-wrap: anywhere;
	}
	.viewer-image {
		background: #e9eaf0;
		border-radius: 12px;
		padding: 24px;
		display: grid;
		place-items: center;
		min-height: 260px;
		margin-top: 20px;
	}
	.viewer-image img {
		max-height: 75vh;
		object-fit: contain;
	}
	@media (max-width: 600px) {
		.share-gate {
			padding: 26px;
			margin: 36px auto;
		}
		.share-page header {
			padding: 0 20px;
			height: 76px;
		}
		.viewer {
			padding: 24px 20px;
		}
		.viewer-image {
			padding: 12px;
		}
	}
</style>
