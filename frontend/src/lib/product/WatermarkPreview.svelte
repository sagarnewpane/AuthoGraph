<script lang="ts">
	import { onMount, onDestroy, createEventDispatcher } from 'svelte';
	export let imageId: number;
	export let refreshKey = 0;
	export let fallback: string;
	export let alt: string;
	export let watermark: {
		enabled: boolean;
		settings: {
			text: string;
			fontSize: number;
			opacity: number;
			rotation: number;
			color: string;
			pattern: string;
			spacing: number;
			horizontalOffset: number;
			verticalOffset: number;
		};
	};
	const dispatch = createEventDispatcher<{ previewerror: string }>();
	let canvas: HTMLCanvasElement;
	let base: HTMLImageElement | undefined;
	let baseUrl = '';
	let mounted = false;
	let ready = false;
	let loadedKey = '';
	let request: AbortController | undefined;
	let revision = 0;
	let frame = 0;
	$: key = `${imageId}:${refreshKey}`;
	$: if (mounted && key !== loadedKey) {
		loadedKey = key;
		loadBase();
	}
	$: if (base && canvas && watermark) scheduleDraw();
	async function loadBase() {
		request?.abort();
		request = new AbortController();
		const current = ++revision;
		let candidate = '';
		try {
			const response = await fetch(`/api/images/${imageId}/preview`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ enabled: false }),
				signal: request.signal
			});
			if (!response.ok) throw new Error('Could not load the live preview.');
			candidate = URL.createObjectURL(await response.blob());
			const image = new Image();
			image.src = candidate;
			await Promise.all([image.decode(), document.fonts.load('32px AuthoGraphWatermark')]);
			if (!mounted || current !== revision) return;
			const previous = baseUrl;
			baseUrl = candidate;
			candidate = '';
			base = image;
			if (previous) URL.revokeObjectURL(previous);
		} catch (error) {
			if (
				current === revision &&
				mounted &&
				!(error instanceof DOMException && error.name === 'AbortError')
			)
				dispatch('previewerror', error instanceof Error ? error.message : 'Preview failed.');
		} finally {
			if (candidate) URL.revokeObjectURL(candidate);
		}
	}
	function scheduleDraw() {
		if (typeof cancelAnimationFrame !== 'undefined') cancelAnimationFrame(frame);
		frame = requestAnimationFrame(draw);
	}
	function draw() {
		if (!base || !canvas) return;
		const width = base.naturalWidth;
		const height = base.naturalHeight;
		const scale = Math.min(1, 1600 / Math.max(width, height));
		const targetWidth = Math.max(1, Math.round(width * scale));
		const targetHeight = Math.max(1, Math.round(height * scale));
		if (canvas.width !== targetWidth) canvas.width = targetWidth;
		if (canvas.height !== targetHeight) canvas.height = targetHeight;
		const context = canvas.getContext('2d');
		if (!context) return;
		context.setTransform(scale, 0, 0, scale, 0, 0);
		context.clearRect(0, 0, width, height);
		context.drawImage(base, 0, 0, width, height);
		if (watermark.enabled && watermark.settings.text) {
			const options = watermark.settings;
			const stamp = document.createElement('canvas');
			const ink = stamp.getContext('2d');
			if (!ink) return;
			const size = Math.max(1, Math.round(Number(options.fontSize) || 24));
			ink.font = `${size}px AuthoGraphWatermark`;
			const bounds = ink.measureText(options.text);
			stamp.width = Math.max(
				1,
				Math.ceil(bounds.actualBoundingBoxLeft + bounds.actualBoundingBoxRight) + 24
			);
			stamp.height = Math.max(
				1,
				Math.ceil(bounds.actualBoundingBoxAscent + bounds.actualBoundingBoxDescent) + 24
			);
			ink.font = `${size}px AuthoGraphWatermark`;
			ink.fillStyle = options.color;
			ink.fillText(
				options.text,
				12 + bounds.actualBoundingBoxLeft,
				12 + bounds.actualBoundingBoxAscent
			);
			const angle = (-(Number(options.rotation) || 0) * Math.PI) / 180;
			const rotatedWidth = Math.ceil(
				Math.abs(stamp.width * Math.cos(angle)) + Math.abs(stamp.height * Math.sin(angle))
			);
			const rotatedHeight = Math.ceil(
				Math.abs(stamp.height * Math.cos(angle)) + Math.abs(stamp.width * Math.sin(angle))
			);
			const gap = Math.max(20, Number(options.spacing) || 80);
			context.globalAlpha = Math.max(0, Math.min(1, Number(options.opacity) / 100));
			const paint = (x: number, y: number) => {
				context.save();
				context.translate(
					x + (Number(options.horizontalOffset) || 0),
					y + (Number(options.verticalOffset) || 0)
				);
				context.rotate(angle);
				context.drawImage(stamp, -stamp.width / 2, -stamp.height / 2);
				context.restore();
			};
			const padding = Math.min(50, Math.floor(width / 4), Math.floor(height / 4));
			if (options.pattern === 'tiled') {
				for (let y = -rotatedHeight; y < height + rotatedHeight; y += rotatedHeight + gap)
					for (let x = -rotatedWidth; x < width + rotatedWidth; x += rotatedWidth + gap)
						paint(x + rotatedWidth / 2, y + rotatedHeight / 2);
			} else if (options.pattern === 'diagonal') {
				for (let i = 0; i < 5; i++)
					paint(
						padding + ((width - 2 * padding) * i) / 4,
						padding + ((height - 2 * padding) * i) / 4
					);
			} else if (options.pattern === 'grid') {
				for (let y = padding; y < height - padding; y += rotatedHeight + gap)
					for (let x = padding; x < width - padding; x += rotatedWidth + gap) paint(x, y);
			} else if (options.pattern === 'corners') {
				paint(padding, padding);
				paint(width - padding, padding);
				paint(padding, height - padding);
				paint(width - padding, height - padding);
			} else paint(width / 2, height / 2);
			context.globalAlpha = 1;
		}
		ready = true;
	}
	onMount(() => {
		mounted = true;
	});
	onDestroy(() => {
		mounted = false;
		revision++;
		request?.abort();
		if (typeof cancelAnimationFrame !== 'undefined') cancelAnimationFrame(frame);
		if (baseUrl) URL.revokeObjectURL(baseUrl);
	});
</script>

<div class="live-preview" role="img" aria-label={`${alt} — live watermark preview`}>
	<img src={fallback} alt="" aria-hidden="true" class:covered={ready} />
	<canvas bind:this={canvas} class:ready aria-hidden="true"></canvas>
</div>

<style>
	@font-face {
		font-family: AuthoGraphWatermark;
		src: url('/fonts/watermark.ttf') format('truetype');
		font-display: swap;
	}
	.live-preview {
		position: relative;
		width: 100%;
		height: 100%;
	}
	img,
	canvas {
		width: 100%;
		height: 100%;
		object-fit: contain;
	}
	canvas {
		position: absolute;
		inset: 0;
		opacity: 0;
	}
	canvas.ready {
		opacity: 1;
	}
	img.covered {
		opacity: 0;
	}
</style>
