<script lang="ts">
	export let compact = false;
</script>

<a href="/" class="brand" class:compact aria-label="AuthoGraph home"
	><span class="logo-frame"
		><img src="/LOGOV2%20(1).png" alt="AuthoGraph" width="1024" height="1024" /></span
	></a
>

<style>
	.brand {
		display: inline-flex;
		align-items: center;
		min-height: 44px;
	}
	.logo-frame {
		position: relative;
		display: block;
		overflow: hidden;
		width: 188px;
		aspect-ratio: 4.25;
	}
	.logo-frame img {
		position: absolute;
		width: 120%;
		max-width: none;
		height: auto;
		filter: hue-rotate(40deg);
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
	}
	.compact .logo-frame {
		width: 44px;
		aspect-ratio: 1;
	}
	.compact .logo-frame img {
		width: 520%;
		left: 258%;
	}
	@media (max-width: 480px) {
		.logo-frame {
			width: 165px;
		}
	}
</style>
