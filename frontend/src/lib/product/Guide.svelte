<script lang="ts">
	import {
		ArrowLeft,
		ArrowUpRight,
		ShieldCheck,
		Link2,
		Fingerprint,
		FileText,
		Bell,
		Activity,
		Image
	} from 'lucide-svelte';
	export let topic = 'access';
	const guides: Record<
		string,
		{ title: string; intro: string; sections: { title: string; text: string }[] }
	> = {
		access: {
			title: 'Share with the right people.',
			intro:
				'An image stays private until you create a share link. Each link has its own access settings.',
			sections: [
				{
					title: 'Create a link',
					text: 'Open an image from your library and choose Sharing. Name your link, optionally add specific recipient emails and a password, then set an expiry or a maximum number of verified views.'
				},
				{
					title: 'Verify the recipient',
					text: 'Recipients enter their email and receive a six-digit code. The code lasts five minutes. A verified viewing session lasts up to fifteen minutes; link expiry or revocation can end it sooner.'
				},
				{
					title: 'Change your mind',
					text: 'Revoke a link from Share links or the image’s Sharing tab. Revocation blocks future image requests, including existing sessions. Copies already saved or captured cannot be recalled.'
				},
				{
					title: 'Understand download controls',
					text: 'Turning off downloads removes the download action and blocks the download endpoint. A browser must still receive image pixels to display them, so it cannot prevent every screenshot or copy.'
				}
			]
		},
		watermark: {
			title: 'Leave your signature.',
			intro:
				'A visible watermark can discourage reuse. A hidden message can carry attribution inside image pixels.',
			sections: [
				{
					title: 'Design your watermark',
					text: 'Open an image and enable Visible watermark. Set the text, color, opacity, size, rotation, and spacing. Choose a tiled pattern or a centered mark, then save to inspect the protected preview.'
				},
				{
					title: 'Preserve the original',
					text: 'Watermarks are applied to separate copies. Your original image remains private and can be downloaded from its workspace.'
				},
				{
					title: 'Check a shared image',
					text: 'Anyone can use /verify-image without an account. Upload the protected PNG to check its signed creator and hidden message. Older copies with plain hidden text are shown as unsigned attribution.'
				},
				{
					title: 'Hidden messages have limits',
					text: 'Hidden text is embedded in the protected image. Compression, resizing, cropping, or other edits may destroy the message. It is not a guarantee of ownership or a reliable way to identify who leaked an image.'
				}
			]
		},
		metadata: {
			title: 'Keep the context with the image.',
			intro: 'Record creator information, copyright notes, and intended usage alongside your work.',
			sections: [
				{
					title: 'Add ownership details',
					text: 'Open the Metadata tab, name a custom field, and enter its value. You can remove custom fields at any time.'
				},
				{
					title: 'Sharing metadata',
					text: 'When metadata protection is included in a share link, your stored metadata is embedded as an AuthoGraph text field in the PNG copy. This is not a signed ownership certificate.'
				},
				{
					title: 'Metadata is editable',
					text: 'Other software can alter or remove metadata. Keep original files and other records of authorship separately.'
				}
			]
		},
		logs: {
			title: 'See what happens after sharing.',
			intro:
				'Activity records requests handled by AuthoGraph, including verified views, downloads, and denied attempts.',
			sections: [
				{
					title: 'Review activity',
					text: 'Open Activity to search by recipient email or image name. Filter events by view, download, or attempt.'
				},
				{
					title: 'What a view means',
					text: 'A verified view is recorded after successful email verification. It does not measure how long someone looked at an image or prove they saw every pixel.'
				},
				{
					title: 'Where visibility ends',
					text: 'Screenshots, copied files, and later use outside AuthoGraph are not tracked. IP addresses describe a network request, not a verified physical location.'
				}
			]
		},
		notifications: {
			title: 'Stay informed, without the noise.',
			intro: 'Choose the emails you want to receive from your workspace.',
			sections: [
				{
					title: 'Choose your notifications',
					text: 'Open Settings, then Notifications. Enable or disable access request, verified view, download, and failed access alerts.'
				},
				{
					title: 'Email verification',
					text: 'Verification codes and password reset messages are separate from activity preferences. They require a working email service configured by the workspace operator.'
				}
			]
		},
		'ai-protection': {
			title: 'AI resistance is experimental.',
			intro:
				'Image perturbation is an optional processing feature. Its effectiveness depends on the model and transformations applied to the image.',
			sections: [
				{
					title: 'Opt-in processing',
					text: 'AI processing is disabled until a workspace operator configures an HTTPS service. Before processing, you must confirm that your image may be sent to that service.'
				},
				{
					title: 'Evaluate the result',
					text: 'Inspect the returned image before sharing it. Perturbations may reduce visual quality. No guarantee is made that an image will resist training, recognition, or editing.'
				}
			]
		},
		privacy: {
			title: 'How this workspace handles data.',
			intro:
				'AuthoGraph stores the information needed to manage accounts, images, and private sharing.',
			sections: [
				{
					title: 'Accounts and files',
					text: 'Your account contains your username, email, optional profile details, and notification preferences. Uploaded originals are encrypted. The server can decrypt them to generate previews and authorized downloads.'
				},
				{
					title: 'Share activity',
					text: 'Access records may contain a recipient email, IP address, action, and time. These records are visible to the image owner. Browser screenshots and activity outside the service are not tracked.'
				},
				{
					title: 'External services',
					text: 'Email is sent through the configured email provider. Optional AI processing sends an image to the configured service only after confirmation. This page describes the application; hosting and provider arrangements depend on the workspace operator.'
				},
				{
					title: 'Deletion',
					text: 'Delete images from their Details tab. Delete your account from Settings → Account security to remove its application records and files. Backup retention depends on the workspace operator.'
				}
			]
		},
		terms: {
			title: 'Use your workspace responsibly.',
			intro: 'Use AuthoGraph for images you have permission to upload and share.',
			sections: [
				{
					title: 'Your content',
					text: 'You remain responsible for your images, recipient permissions, and any usage rights you grant. Uploading an image does not establish or verify copyright ownership.'
				},
				{
					title: 'Protection limits',
					text: 'Access restrictions govern requests made through AuthoGraph. Watermarks and metadata can be edited or removed, and displayed images can be captured. AI resistance is experimental.'
				},
				{
					title: 'Service availability',
					text: 'This application is under active development. Keep independent backups of important originals. Commercial service terms and support commitments must be provided by the operator before a paid launch.'
				}
			]
		}
	};
	$: content = guides[topic] || guides.access;
	const navigation = [
		{ id: 'access', name: 'Private sharing', icon: Link2 },
		{ id: 'watermark', name: 'Watermarks', icon: Fingerprint },
		{ id: 'metadata', name: 'Metadata', icon: FileText },
		{ id: 'logs', name: 'Activity', icon: Activity },
		{ id: 'notifications', name: 'Notifications', icon: Bell },
		{ id: 'ai-protection', name: 'AI resistance', icon: Image }
	];
</script>

<svelte:head><title>{content.title} · AuthoGraph</title></svelte:head>
<div class="guide">
	<div class="guide-intro">
		<span class="eyebrow">AUTHOGRAPH / FIELD NOTES</span>
		<h1>{content.title}</h1>
		<p>{content.intro}</p>
	</div>
	<div class="guide-layout">
		<nav aria-label="Protection guides">
			<span class="eyebrow">THE ESSENTIALS</span>{#each navigation as item}<a
					href={`/learn/${item.id}`}
					class:active={topic === item.id}
					><svelte:component this={item.icon} aria-hidden="true" size={16} />{item.name}</a
				>{/each}
		</nav>
		<article>
			{#each content.sections as section}<section>
					<h2>{section.title}</h2>
					<p>{section.text}</p>
				</section>{/each}<a href="/images" class="btn primary"
				>Open your library <ArrowUpRight aria-hidden="true" size={15} /></a
			>
		</article>
	</div>
</div>

<style>
	.guide {
		max-width: 1060px;
		margin: auto;
		padding: 54px 24px 80px;
	}
	.guide-intro {
		max-width: 720px;
		margin-bottom: 48px;
	}
	.guide-intro h1 {
		font-size: 43px;
		line-height: 1.2;
		margin: 18px 0;
	}
	.guide-intro > p {
		color: var(--muted-ink);
		font-size: 15px;
	}
	.guide-layout {
		display: grid;
		grid-template-columns: 200px 1fr;
		gap: 64px;
	}
	.guide nav {
		display: flex;
		flex-direction: column;
		gap: 6px;
	}
	.guide nav > span {
		font-size: 12px;
		margin: 8px 12px 16px;
	}
	.guide nav > a {
		display: flex;
		align-items: center;
		gap: 10px;
		min-height: 44px;
		padding: 10px 12px;
		font-size: 12px;
		color: var(--muted-ink);
		border-radius: 7px;
	}
	.guide nav > a.active {
		background: var(--studio-soft);
		color: var(--studio);
		font-weight: 600;
	}
	.guide article {
		min-width: 0;
	}
	.guide article section {
		padding-bottom: 28px;
		margin-bottom: 28px;
		border-bottom: 1px solid var(--line);
	}
	.guide h2 {
		font-size: 19px;
		margin-bottom: 14px;
	}
	.guide article p {
		font-size: 14px;
		line-height: 1.9;
		color: var(--muted-ink);
	}
	@media (max-width: 700px) {
		.guide {
			padding: 36px 20px;
		}
		.guide-intro h1 {
			font-size: 33px;
		}
		.guide-layout {
			grid-template-columns: 1fr;
			gap: 32px;
		}
		.guide nav {
			display: grid;
			grid-template-columns: 1fr 1fr;
		}
		.guide nav > span {
			grid-column: 1/-1;
		}
	}
</style>
