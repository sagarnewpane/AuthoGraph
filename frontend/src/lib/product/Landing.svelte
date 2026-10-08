<script lang="ts">
	import {
		ArrowUpRight,
		ArrowRight,
		LockKeyhole,
		ShieldCheck,
		Fingerprint,
		Eye,
		Link2,
		Check,
		ImagePlus
	} from 'lucide-svelte';
	let preview = 'watermark';
</script>

<section class="hero">
	<div class="hero-copy">
		<span class="intro"><span></span>A PRIVATE SPACE FOR YOUR CREATIVE WORK</span>
		<h1>Made by you.<br />Shared on<br /><em>your terms.</em></h1>
		<p>
			Your images deserve more than an open link. Protect your work, choose who sees it, and keep
			every share in view.
		</p>
		<div class="hero-actions">
			<a href="/register" class="btn primary"
				>Create your workspace <ArrowUpRight aria-hidden="true" size={18} /></a
			><a href="#how-it-works" class="text-link"
				>Take a closer look <ArrowRight aria-hidden="true" size={16} /></a
			>
		</div>
		<div class="hero-facts">
			<span><Check aria-hidden="true" size={14} /> Private by default</span><span
				><Check aria-hidden="true" size={14} /> No credit card needed</span
			>
		</div>
		<a href="/verify-image" class="text-link" style="margin-top:20px"
			>Check an image’s hidden signature <ArrowRight size={15} aria-hidden="true" /></a
		>
	</div>
	<div class="hero-art">
		<div class="art-caption"><span>THE PRIVATE COLLECTION</span><span>PREVIEW / 001</span></div>
		<div class="hero-photo">
			<img
				src="/images/studio-arch.png"
				alt="Sunlit limestone arch framing a blue Mediterranean sea"
				width="1536"
				height="1024"
				fetchpriority="high"
			/>{#if preview === 'watermark'}<div class="proof-watermark" aria-hidden="true">
					authograph / preview<br />authograph / preview<br />authograph / preview
				</div>{/if}
			<div class="photo-label">
				<span>Coastal studies</span><small>Architectural collection · Sample image</small>
			</div>
		</div>
		<div class="permission-card">
			<div class="permission-icon"><ShieldCheck aria-hidden="true" size={22} /></div>
			<div>
				<strong>A little more peace of mind.</strong>
				<p>Watermarked. Shared with permission.</p>
			</div>
			<span class="permission-check"><Check aria-hidden="true" size={14} /></span>
		</div>
		<div class="art-controls">
			<span>Try the preview</span>
			<div>
				<button
					class:chosen={preview === 'original'}
					aria-pressed={preview === 'original'}
					on:click={() => (preview = 'original')}>Original</button
				><button
					class:chosen={preview === 'watermark'}
					aria-pressed={preview === 'watermark'}
					on:click={() => (preview = 'watermark')}
					><LockKeyhole aria-hidden="true" size={12} /> Watermarked</button
				>
			</div>
		</div>
	</div>
</section>
<div class="value-strip">
	<span>Less uncertainty.<br /><strong>More creative control.</strong></span>
	<div><LockKeyhole aria-hidden="true" size={19} /><span>Private image storage</span></div>
	<div><Fingerprint aria-hidden="true" size={19} /><span>Visible & hidden watermarks</span></div>
	<div><Eye aria-hidden="true" size={19} /><span>Verified recipient access</span></div>
</div>
<section class="workflow" id="how-it-works">
	<div class="workflow-intro">
		<span class="eyebrow">FROM YOUR STUDIO TO THEIR SCREEN</span>
		<h2>A considered way<br />to share your work.</h2>
		<p>One place for your images and the decisions around them.</p>
	</div>
	<div class="steps">
		<article>
			<span class="step-icon"><ImagePlus aria-hidden="true" size={22} /></span><small
				>01 / COLLECT</small
			>
			<h3>Bring your work together.</h3>
			<p>
				Upload your images into a private library. Find the right file without losing track of the
				original.
			</p>
		</article>
		<article>
			<span class="step-icon"><Fingerprint aria-hidden="true" size={22} /></span><small
				>02 / PROTECT</small
			>
			<h3>Make your mark.</h3>
			<p>
				Apply your watermark and ownership details. Preview the result before anyone else sees it.
			</p>
		</article>
		<article>
			<span class="step-icon"><Link2 aria-hidden="true" size={22} /></span><small>03 / SHARE</small>
			<h3>Open the right doors.</h3>
			<p>
				Invite recipients, set an expiry, and decide whether downloads are available. Review access
				as it happens.
			</p>
		</article>
	</div>
</section>
<section class="honest-section">
	<div>
		<span class="eyebrow">BUILT AROUND REAL CONTROL</span>
		<h2>Share with intention.<br /><span class="serif">Know the limits.</span></h2>
	</div>
	<div>
		<p>
			No website can prevent every screenshot or copy. AuthoGraph helps you manage access,
			discourage reuse with watermarks, and keep a record of activity through your share links.
		</p>
		<a href="/learn/access" class="text-link"
			>Explore how protection works <ArrowUpRight aria-hidden="true" size={16} /></a
		>
	</div>
</section>
<section class="landing-cta">
	<div>
		<span class="eyebrow">YOUR NEXT COLLECTION STARTS HERE</span>
		<h2>Give your work a private home.</h2>
	</div>
	<a href="/register" class="btn primary"
		>Get started <ArrowUpRight aria-hidden="true" size={17} /></a
	>
</section>

<style>
	.hero {
		max-width: 1480px;
		margin: auto;
		padding: 64px 6% 86px;
		display: grid;
		grid-template-columns: 1fr 1.08fr;
		gap: 7%;
		align-items: center;
	}
	.intro {
		display: flex;
		gap: 9px;
		align-items: center;
		font-size: 12px;
		font-weight: 700;
		letter-spacing: 1.5px;
		color: var(--muted-ink);
	}
	.intro > span {
		height: 6px;
		width: 6px;
		border-radius: 50%;
		background: var(--studio);
	}
	h1 {
		font-size: clamp(52px, 5.4vw, 80px);
		font-weight: 600;
		line-height: 1.08;
		letter-spacing: -4px;
		margin: 27px 0;
	}
	h1 em {
		font-family: Georgia, serif;
		color: var(--studio);
		font-weight: 400;
		letter-spacing: -3px;
	}
	.hero-copy > p {
		font-size: 15px;
		max-width: 370px;
		color: var(--muted-ink);
		line-height: 1.9;
	}
	.hero-actions {
		display: flex;
		align-items: center;
		gap: 24px;
		flex-wrap: wrap;
		margin-top: 30px;
	}
	.hero-actions .btn {
		min-height: 49px;
	}
	.hero-facts {
		display: flex;
		gap: 20px;
		margin-top: 24px;
		font-size: 12px;
		color: var(--muted-ink);
	}
	.hero-facts span {
		display: flex;
		gap: 5px;
		align-items: center;
	}
	.hero-facts :global(svg) {
		color: var(--positive);
	}
	.hero-art {
		position: relative;
		min-width: 0;
		padding: 0 0 40px;
	}
	.art-caption {
		display: flex;
		justify-content: space-between;
		gap: 8px;
		font-size: 12px;
		letter-spacing: 1.6px;
		font-weight: 600;
		color: var(--muted-ink);
		margin-bottom: 14px;
	}
	.hero-photo {
		aspect-ratio: 1.03;
		position: relative;
		overflow: hidden;
		border-radius: 100px 8px 8px 8px;
		background: #dde6ec;
	}
	.hero-photo > img {
		width: 100%;
		height: 100%;
		object-fit: cover;
		object-position: 54%;
	}
	.proof-watermark {
		position: absolute;
		inset: 20% -15%;
		transform: rotate(-28deg);
		text-align: center;
		line-height: 4.5;
		font-size: 22px;
		color: #ffffff75;
		font-weight: 500;
		pointer-events: none;
		white-space: nowrap;
	}
	.photo-label {
		position: absolute;
		bottom: 24px;
		left: 24px;
		display: grid;
		gap: 6px;
		color: white;
		text-shadow: 0 1px 6px #252736;
	}
	.photo-label > span {
		font-size: 16px;
		font-weight: 600;
	}
	.photo-label small {
		font-size: 12px;
	}
	.permission-card {
		position: absolute;
		right: -20px;
		bottom: 20px;
		display: flex;
		align-items: center;
		gap: 12px;
		max-width: calc(100% - 16px);
		background: white;
		border: 1px solid var(--line);
		border-radius: 10px;
		padding: 18px;
		box-shadow: 0 12px 40px #28233d12;
	}
	.permission-icon {
		width: 40px;
		height: 40px;
		display: grid;
		place-items: center;
		color: var(--studio);
		background: var(--studio-soft);
		border-radius: 9px;
	}
	.permission-card strong {
		font-size: 12px;
	}
	.permission-card p {
		font-size: 12px;
		color: var(--muted-ink);
		margin-top: 5px;
	}
	.permission-check {
		width: 22px;
		height: 22px;
		border-radius: 50%;
		background: var(--positive-soft);
		color: var(--positive);
		display: grid;
		place-items: center;
		margin-left: 8px;
	}
	.art-controls {
		margin-top: 16px;
		display: flex;
		align-items: center;
		gap: 12px;
		font-size: 12px;
		color: var(--muted-ink);
	}
	.art-controls > div {
		display: flex;
		gap: 4px;
	}
	.art-controls button {
		display: flex;
		align-items: center;
		gap: 4px;
		font-size: 12px;
		min-height: 36px;
		padding: 7px 10px;
		border: 1px solid transparent;
		border-radius: 5px;
		background: none;
	}
	.art-controls button.chosen {
		background: white;
		border-color: var(--line);
		color: var(--studio);
	}
	.value-strip {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 32px;
		padding: 32px 6%;
		border-block: 1px solid var(--line);
		background: white;
	}
	.value-strip > span {
		font-size: 12px;
		line-height: 1.8;
		color: var(--muted-ink);
	}
	.value-strip strong {
		color: var(--ink);
		font-weight: 600;
	}
	.value-strip > div {
		display: flex;
		align-items: center;
		gap: 12px;
		font-size: 12px;
		font-weight: 600;
	}
	.value-strip :global(svg) {
		color: var(--studio);
	}
	.workflow {
		padding: 90px 6%;
		max-width: 1600px;
		margin: auto;
	}
	.workflow-intro h2 {
		font-size: 38px;
		line-height: 1.25;
		letter-spacing: -1.6px;
		margin: 18px 0;
	}
	.workflow-intro p {
		font-size: 14px;
		color: var(--muted-ink);
	}
	.steps {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: 48px;
		margin-top: 48px;
	}
	.steps article {
		padding-top: 26px;
		border-top: 1px solid var(--line);
	}
	.step-icon {
		display: grid;
		place-items: center;
		background: var(--studio-soft);
		color: var(--studio);
		border-radius: 10px;
		width: 48px;
		height: 48px;
		margin-bottom: 24px;
	}
	.steps small {
		font-size: 12px;
		letter-spacing: 1.4px;
		color: var(--muted-ink);
		font-weight: 700;
	}
	.steps h3 {
		font-size: 18px;
		margin: 12px 0;
	}
	.steps p {
		font-size: 13px;
		color: var(--muted-ink);
		max-width: 330px;
	}
	.honest-section {
		padding: 60px 6%;
		background: #eeedf6;
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 10%;
		align-items: center;
	}
	.honest-section h2 {
		font-size: 36px;
		letter-spacing: -1px;
		line-height: 1.3;
		margin-top: 18px;
	}
	.honest-section p {
		font-size: 14px;
		color: var(--muted-ink);
		max-width: 460px;
	}
	.honest-section .text-link {
		margin-top: 16px;
	}
	.landing-cta {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 28px;
		padding: 70px 6%;
		background: white;
	}
	.landing-cta h2 {
		font-size: 29px;
		letter-spacing: -1px;
		margin-top: 16px;
	}
	@media (max-width: 1050px) {
		.hero {
			gap: 5%;
			padding-top: 40px;
		}
		h1 {
			font-size: 58px;
			letter-spacing: -3px;
		}
		.hero-actions {
			gap: 12px;
		}
		.permission-card {
			right: 0;
			bottom: 20px;
			padding: 12px;
		}
		.permission-check {
			display: none;
		}
		.hero-photo {
			aspect-ratio: 0.85;
		}
		.value-strip {
			gap: 20px;
		}
		.value-strip > div {
			font-size: 12px;
		}
	}
	@media (max-width: 760px) {
		.hero {
			grid-template-columns: 1fr;
			padding: 35px 20px 44px;
			gap: 40px;
		}
		.hero-copy {
			text-align: left;
		}
		h1 {
			font-size: 60px;
		}
		.hero-copy > p {
			max-width: 460px;
		}
		.hero-photo {
			aspect-ratio: 1.1;
			border-radius: 70px 8px 8px 8px;
		}
		.hero-art {
			max-width: 540px;
			width: 100%;
			margin: auto;
		}
		.value-strip {
			padding: 24px 20px;
			display: grid;
			grid-template-columns: 1fr 1fr;
			gap: 24px;
		}
		.value-strip > div {
			font-size: 12px;
			align-items: flex-start;
		}
		.workflow {
			padding: 54px 20px;
		}
		.workflow-intro h2 {
			font-size: 32px;
		}
		.steps {
			grid-template-columns: 1fr;
			gap: 28px;
			margin-top: 32px;
		}
		.steps article {
			display: grid;
			grid-template-columns: 48px 1fr;
			gap: 0 20px;
		}
		.step-icon {
			grid-row: 1/4;
		}
		.steps p {
			max-width: 100%;
			grid-column: 2;
		}
		.steps h3 {
			margin: 8px 0;
		}
		.honest-section {
			grid-template-columns: 1fr;
			padding: 40px 20px;
			gap: 24px;
		}
		.landing-cta {
			padding: 44px 20px;
			flex-wrap: wrap;
		}
		.landing-cta h2 {
			font-size: 25px;
		}
	}
</style>
