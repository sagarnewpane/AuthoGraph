<script lang="ts">
	export let prefix = 'new-link';
	export let filename = '';
	export let showWatermark = true;
	export let allowDownload = false;
	export let downloadWithoutWatermark = false;
	export let watermarkAvailable = false;
	export let includeMetadata = true;
	export let downloadMetadataMode: 'inherit' | 'include' | 'strip' = 'inherit';
</script>

<div class="field">
	<label for={`${prefix}-filename`}>Filename shown to recipients</label>
	<input
		id={`${prefix}-filename`}
		bind:value={filename}
		maxlength="180"
		placeholder="Campaign preview"
	/>
	<small>This changes the shared title and download filename. Downloads use PNG format.</small>
</div>
<label class="check">
	<input type="checkbox" bind:checked={showWatermark} />
	<span
		><strong>Show watermark on shared image</strong><small
			>{watermarkAvailable
				? 'Use the image’s saved watermark in the recipient preview.'
				: 'Enable and save a visible watermark in Protection first.'}</small
		></span
	>
</label>
<div class="field">
	<label for={`${prefix}-metadata`}>Metadata in shared image</label>
	<select id={`${prefix}-metadata`} bind:value={includeMetadata}>
		<option value={true}>Include saved metadata</option>
		<option value={false}>Strip metadata</option>
	</select>
	<small
		>Include saved ownership and image details, or remove embedded metadata from the shared copy.</small
	>
</div>
<label class="check">
	<input type="checkbox" bind:checked={allowDownload} />
	<span
		><strong>Allow downloads</strong><small>Verified recipients can download this image.</small
		></span
	>
</label>
{#if allowDownload}
	<div class="field">
		<label for={`${prefix}-download`}>Downloaded copy</label>
		<select id={`${prefix}-download`} bind:value={downloadWithoutWatermark}>
			<option value={false}>Same protection as the shared preview</option>
			<option value={true}>Without visible watermark</option>
		</select>
		<small
			>Removing the visible watermark keeps the link’s hidden message and AI processing. Choose
			metadata separately below.</small
		>
	</div>
	<div class="field">
		<label for={`${prefix}-download-metadata`}>Metadata in downloaded image</label>
		<select id={`${prefix}-download-metadata`} bind:value={downloadMetadataMode}>
			<option value="inherit">Same as shared image</option>
			<option value="include">Include saved metadata</option>
			<option value="strip">Strip metadata</option>
		</select>
		<small>Stripping metadata does not remove visible watermarks or hidden messages.</small>
	</div>
{/if}
