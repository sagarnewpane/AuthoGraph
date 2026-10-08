<script lang="ts">
	import { enhance } from '$app/forms';
	import { page } from '$app/stores';
	import Brand from './Brand.svelte';
	import { ArrowRight, ArrowLeft, LockKeyhole, Eye, EyeOff } from 'lucide-svelte';
	export let mode: 'login' | 'register' | 'forgot' | 'reset' = 'login';
	export let form: { error?: string; message?: string; values?: Record<string, string> } | null =
		null;
	let busy = false;
	let reveal = false;
	$: title = {
		login: 'Welcome back.',
		register: 'A home for your best work.',
		forgot: 'Let’s get you back in.',
		reset: 'Choose a new password.'
	}[mode];
	$: description = {
		login: 'Sign in to your creative workspace.',
		register: 'Create your private image workspace.',
		forgot: 'Enter your email to request a password reset link.',
		reset: 'Use a strong password you haven’t used elsewhere.'
	}[mode];
</script>

<svelte:head><title>{title} · AuthoGraph</title></svelte:head>
<main id="main" class="auth-layout">
	<section class="auth-form-side">
		<Brand />
		<div class="auth-form">
			<span class="eyebrow">YOUR WORK. YOUR PERMISSIONS.</span>
			<h1>{title}</h1>
			<p class="muted">{description}</p>
			{#if $page.url.searchParams.has('registered')}<div class="success" role="status">
					Your workspace is ready. Sign in to get started.
				</div>{/if}{#if $page.url.searchParams.has('reset')}<div class="success" role="status">
					Password updated. Sign in with your new password.
				</div>{/if}
			<form
				method="POST"
				use:enhance={() => {
					busy = true;
					return async ({ update }) => {
						await update({ reset: false });
						busy = false;
					};
				}}
				class="form-stack"
			>
				{#if form?.error}<div class="error" role="alert" tabindex="-1">
						{form.error}
					</div>{/if}{#if form?.message}<div class="success" role="status">
						{form.message}
					</div>{/if}{#if mode === 'register' || mode === 'login'}<div class="field">
						<label for="username">Username</label><input
							id="username"
							name="username"
							autocomplete="username"
							value={form?.values?.username || ''}
							required
							maxlength="150"
							placeholder="Your username"
						/>
					</div>{/if}{#if mode === 'register' || mode === 'forgot'}<div class="field">
						<label for="email">Email address</label><input
							id="email"
							name="email"
							type="email"
							autocomplete="email"
							value={form?.values?.email || ''}
							required
							placeholder="you@studio.com"
						/>
					</div>{/if}{#if mode !== 'forgot'}<div class="field">
						<div class="row between">
							<label for="password">{mode === 'reset' ? 'New password' : 'Password'}</label
							>{#if mode === 'login'}<a href="/forget-password" class="forgot-link"
									>Forgot password?</a
								>{/if}
						</div>
						<div class="password-field">
							<input
								id="password"
								name="password"
								type={reveal ? 'text' : 'password'}
								required
								minlength={mode === 'login' ? 1 : 8}
								autocomplete={mode === 'login' ? 'current-password' : 'new-password'}
							/><button
								type="button"
								aria-label={reveal ? 'Hide password' : 'Show password'}
								aria-pressed={reveal}
								on:click={() => (reveal = !reveal)}
								>{#if reveal}<EyeOff aria-hidden="true" size={17} />{:else}<Eye
										aria-hidden="true"
										size={17}
									/>{/if}</button
							>
						</div>
						{#if mode !== 'login'}<small
								>At least 8 characters, with uppercase, lowercase, a number, and a symbol.</small
							>{/if}
					</div>{/if}{#if mode === 'register' || mode === 'reset'}<div class="field">
						<label for="confirm">Confirm password</label><input
							id="confirm"
							name="confirm_password"
							type="password"
							autocomplete="new-password"
							required
							minlength="8"
						/>
					</div>{/if}<button class="btn primary" disabled={busy}
					>{busy
						? 'Please wait…'
						: mode === 'login'
							? 'Sign in'
							: mode === 'register'
								? 'Create workspace'
								: mode === 'forgot'
									? 'Send reset link'
									: 'Update password'}<ArrowRight aria-hidden="true" size={16} /></button
				>{#if mode === 'register'}<p class="agreement">
						By creating an account, you agree to the <a href="/terms">Terms</a> and
						<a href="/privacy">Privacy policy</a>.
					</p>{/if}
			</form>
			<div class="auth-bottom">
				{#if mode === 'login'}New to AuthoGraph? <a href="/register">Create an account</a
					>{:else if mode === 'register'}Already have a workspace? <a href="/login">Sign in</a
					>{:else}<a href="/login"
						><ArrowLeft
							aria-hidden="true"
							size={14}
							style="display:inline;vertical-align:middle"
						/>Back to sign in</a
					>{/if}
			</div>
		</div>
		<div class="auth-foot">
			<a href="/">← Back to AuthoGraph</a><span>A little more creative control.</span>
		</div>
	</section>
	<aside class="auth-art">
		<img
			src="/images/studio-arch.png"
			alt="Limestone arch overlooking a blue sea"
			width="1536"
			height="1024"
		/>
		<div class="art-top">
			<LockKeyhole aria-hidden="true" size={16} /><span>THE PRIVATE COLLECTION</span>
		</div>
		<div class="art-copy">
			<span>MAKE SPACE FOR YOUR WORK.</span>
			<h2>Yours to create.<br /><em>Yours to share.</em></h2>
			<p>A quieter place for your images,<br />and more control over where they go.</p>
		</div>
		<div class="art-bottom"><span>Coastal studies / Sample collection</span><span>001</span></div>
	</aside>
</main>

<style>
	.auth-layout {
		min-height: 100vh;
		display: grid;
		grid-template-columns: 1fr 1fr;
		background: white;
	}
	.auth-form-side {
		padding: 40px 9%;
		display: flex;
		flex-direction: column;
		min-width: 0;
	}
	.auth-form {
		max-width: 390px;
		width: 100%;
		margin: auto;
		padding: 48px 0;
	}
	.auth-form .eyebrow {
		font-size: 12px;
	}
	.auth-form h1 {
		font-size: 33px;
		line-height: 1.3;
		margin: 18px 0 10px;
	}
	.auth-form > p {
		font-size: 13px;
		margin-bottom: 30px;
	}
	.auth-form > .success {
		margin-bottom: 20px;
	}
	.auth-form form > .btn {
		margin-top: 5px;
	}
	.forgot-link {
		font-size: 12px;
		color: var(--studio);
		min-height: 32px;
		display: flex;
		align-items: center;
	}
	.password-field {
		position: relative;
	}
	.password-field input {
		padding-right: 48px;
	}
	.password-field button {
		position: absolute;
		right: 0;
		top: 0;
		height: 44px;
		width: 44px;
		background: none;
		border: 0;
		color: var(--muted-ink);
		display: grid;
		place-items: center;
	}
	.auth-bottom {
		font-size: 12px;
		text-align: center;
		margin-top: 28px;
		color: var(--muted-ink);
	}
	.auth-bottom a,
	.agreement a {
		color: var(--studio);
		font-weight: 600;
	}
	.agreement {
		font-size: 12px;
		color: var(--muted-ink);
		text-align: center;
	}
	.auth-foot {
		font-size: 12px;
		display: flex;
		justify-content: space-between;
		gap: 20px;
		color: var(--muted-ink);
	}
	.auth-art {
		margin: 16px;
		position: relative;
		border-radius: 12px;
		overflow: hidden;
		background: #324857;
		min-height: 650px;
	}
	.auth-art > img {
		height: 100%;
		width: 100%;
		position: absolute;
		object-fit: cover;
		object-position: 50%;
	}
	.auth-art::after {
		content: '';
		position: absolute;
		inset: 0;
		background: linear-gradient(180deg, #071e2a15 0%, transparent 30%, #071e2aa0 100%);
	}
	.art-top {
		position: absolute;
		top: 32px;
		left: 32px;
		z-index: 1;
		display: flex;
		align-items: center;
		gap: 10px;
		color: white;
		font-size: 12px;
		letter-spacing: 2px;
	}
	.art-copy {
		position: absolute;
		left: 44px;
		right: 32px;
		bottom: 104px;
		z-index: 1;
		color: white;
	}
	.art-copy > span {
		font-size: 12px;
		letter-spacing: 2px;
	}
	.art-copy h2 {
		font-size: 48px;
		font-weight: 500;
		line-height: 1.15;
		letter-spacing: -2px;
		margin: 20px 0;
	}
	.art-copy em {
		font-family: Georgia, serif;
		font-weight: 400;
	}
	.art-copy p {
		font-size: 13px;
		line-height: 1.8;
		color: #f3f3f3;
	}
	.art-bottom {
		position: absolute;
		z-index: 1;
		bottom: 32px;
		left: 44px;
		right: 32px;
		display: flex;
		justify-content: space-between;
		color: white;
		font-size: 12px;
		letter-spacing: 0.7px;
	}
	@media (max-width: 1000px) {
		.auth-form-side {
			padding: 32px 8%;
		}
		.art-copy {
			left: 28px;
		}
		.art-copy h2 {
			font-size: 38px;
		}
		.auth-foot span {
			display: none;
		}
	}
	@media (max-width: 700px) {
		.auth-layout {
			grid-template-columns: 1fr;
		}
		.auth-form-side {
			padding: 24px;
		}
		.auth-art {
			display: none;
		}
		.auth-form {
			padding: 54px 0;
		}
		.auth-form h1 {
			font-size: 30px;
		}
		.auth-foot {
			padding-top: 20px;
		}
	}
</style>
