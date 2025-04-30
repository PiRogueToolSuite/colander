<script>
import { Cropper } from 'vue-advanced-cropper';

// This function is used to detect the actual image type,
function getMimeType(file, fallback = null) {
	const byteArray = (new Uint8Array(file)).subarray(0, 4);
  let header = '';
  for (let i = 0; i < byteArray.length; i++) {
     header += byteArray[i].toString(16);
  }
	switch (header) {
    case "89504e47":
      return "image/png";
    case "47494638":
      return "image/gif";
    case "ffd8ffe0":
    case "ffd8ffe1":
    case "ffd8ffe2":
    case "ffd8ffe3":
    case "ffd8ffe8":
      return "image/jpeg";
    default:
      return fallback;
    }
}

export default {
  name: 'ColanderThumbnailInputField',
  components: {Cropper},
  props: {
    id: String,
    class: String,
  },
  data() {
    return {
      currentImage: {
        /* track the current 'server-side' image */
        /* if present */
        src: null,
      },
      thumbnailImage: {
        /* track the current 'client-side' thumbnail (cropped) */
        /* will be posted within the form */
        src: null,
        type: null,
        name: null,
      },
      croppedImage: {
        /* track the current 'client-side' in-progress crop image */
        /* will be discarded */
        src: null,
        type: null,
        name: null,
      },
      supportedMimeType: {
        'image/png': true,
        'image/jpeg': true,
      },
      cropperConfig: {
        stencil: {
          aspectRatio: 1,
        },
        outputFormat: {
          width: 256,
          height: 256,
        },
        boundaries: 'fill',
        restriction: 'none',
        backgroundClass: 'cropper-background',
        foregroundClass: 'cropper-foreground',
      }
    };
  },
  created() {
    this.$logger(this, 'ThumbnailInputField');
  },
  computed: {
    removable() {
      return this.currentImage.src !== null && this.currentImage.src === this.thumbnailImage.src;
    },
    resetable() {
      return this.currentImage.src !== this.thumbnailImage.src;
    },
  },
  mounted() {
    $(this.$refs.adjustThumbnailModal).on('hidden.bs.modal', () => {
      //alert('canceled ?');
    });
    $(this.$refs.adjustThumbnailModal).on('shown.bs.modal', () => {
      this.croppingFeaturesReset();
    });
    this.$fileUploader = this.$refs.slotContent.querySelector('#id_thumbnail');
    this.$checkboxClear = this.$refs.slotContent.querySelector('#thumbnail-clear_id');
    this.$debug('$fileUploader', this.$fileUploader);
    this.$debug('$checboxClear', this.$checkboxClear);
    if (!this.$fileUploader) {
      throw new Error("ThumbnailInputField need a slot containing an <input type='file' id='id_thumbnail'/>");
    }
    if (this.$checkboxClear) {
      this.$info('No previous thumbnail mode');
    }
    this.findInitialImage(this.$refs.slotContent);
    this.$debug('mounted');
  },
  methods: {
    findInitialImage(domTree) {
      const jImg = $(domTree).find('img');
      if (jImg.length) {
        this.setInitialImageSrc(jImg.attr('src'));
      }
    },
    setInitialImageSrc(imgSrc) {
      this.currentImage.src = imgSrc;
      this.thumbnailImage.src = imgSrc;
      if (this.$checkboxClear) {
        this.$checkboxClear.checked = false;
      }
    },
    loadImage(event) {
      // Reference to the DOM input element
      const {files} = event.target;
      this.handleFiles(files);
    },
    handleFiles(files) {
			if (files && files[0]) {

				if (this.croppedImage.src) {
					URL.revokeObjectURL(this.croppedImage.src)
				}

				const blob = URL.createObjectURL(files[0]);

				const reader = new FileReader();

				reader.onload = (e) => {
					this.croppedImage = {
						src: blob,
						type: getMimeType(e.target.result, files[0].type),
            name: files[0].name,
					};
          this.croppingStart();
				};

				reader.readAsArrayBuffer(files[0]);
			}
    },
    croppingCancel() {
      $(this.$refs.adjustThumbnailModal).modal('hide');
    },
    croppingStart(ctx) {
      $(this.$refs.adjustThumbnailModal).modal('show');
    },
    croppingFeaturesReset() {
    },
    croppingConfirm() {
      $(this.$refs.adjustThumbnailModal).modal('hide');

      let cropResult = this.$refs.cropper.getResult();

      if (cropResult.canvas) {
        cropResult.canvas.toBlob((blob) => {
          this.$debug('cropped blob', blob);
          let file = new File([blob], this.croppedImage.name, { type:this.croppedImage.type, lastModified:new Date().getTime()});
          let container = new DataTransfer();
          container.items.add(file);
          if (this.$checkboxClear) {
            this.$checkboxClear.checked = false;
          }
          this.$fileUploader.files = container.files;
          this.thumbnailImage.src = URL.createObjectURL(blob);
        }, 'image/png');
      }
    },
    cropperFitToImage() {
      this.$refs.cropper.setCoordinates(({ coordinates, imageSize }) => ({
        width: imageSize.width,
        height: imageSize.height
      }));
    },
    manualLoad(event) {
      event.preventDefault();
      event.stopPropagation();
      this.$refs.fileChooser.click();
    },
    removeThumbnail(event) {
      event.preventDefault();
      event.stopPropagation();
      this.thumbnailImage.src = null;
      if (this.$checkboxClear) {
        this.$checkboxClear.checked = true;
      }
    },
    resetThumbnail(event) {
      event?.preventDefault();
      event?.stopPropagation();
      this.thumbnailImage.src = this.currentImage.src;
      let emptyContainer = new DataTransfer();
      this.$fileUploader.files = emptyContainer.files;
      this.$refs.fileChooser.files = emptyContainer.files;
    },
    dragover(event) {
      event.preventDefault();
      event.stopPropagation();
      let dt = event.dataTransfer;
      for(let item of dt.items) {
        this.$debug('item', item);
        if (item.kind === 'file' && item.type in this.supportedMimeType) {
          this.$refs.dropzone.classList.add('drop-accepted');
          event.dataTransfer.dropEffect = 'copy';
          return true;
        }
      }
      this.$refs.dropzone.classList.add('drop-rejected');
      event.dataTransfer.dropEffect = 'none';
      return false;
    },
    dragleave(event) {
      event.preventDefault();
      event.stopPropagation();
      this.$refs.dropzone.classList.remove('drop-accepted');
      this.$refs.dropzone.classList.remove('drop-rejected');
    },
    drop(event) {
      event.preventDefault();
      event.stopPropagation();
      this.$refs.dropzone.classList.remove('drop-accepted');
      this.$refs.dropzone.classList.remove('drop-rejected');

      let dt = event.dataTransfer;
      for(let item of dt.items) {
        if (item.kind === 'file' && item.type in this.supportedMimeType) {
          this.handleFiles(event.dataTransfer.files);
          return;
        }
      }
    },
  }
};
</script>
<template>
  <div :id :class>
    <div class='slot-content' ref="slotContent">
      <slot/>
    </div>
    <input class="visually-hidden" type='file' ref='fileChooser' accept='image/png, image/jpeg, image/jpg' @change="loadImage($event)"/>
    <div class='drop-zone' ref='dropzone' @dragleave="dragleave" @dragover="dragover" @drop="drop">
      <div class='row'>
        <div class='col-8'>
          <div class='d-flex justify-content-center p-1'>
            <button class='btn btn-sm btn-secondary text-white' @click="manualLoad">Browse</button>
          </div>
          <div class='hint d-flex justify-content-center p-1'>Or drap'n drop one here</div>
        </div>
        <div class='col-4'>
          <div v-if="thumbnailImage.src">
            <img class='img-thumbnail me-2' v-if="thumbnailImage.src" v-bind:src="thumbnailImage.src" alt="Current thumbnail" />
            <button v-if="removable" class='btn btn-sm btn-secondary text-white' @click="removeThumbnail">Remove</button>
            <button v-if="resetable" class='btn btn-sm btn-secondary text-white' @click="resetThumbnail">Reset</button>
          </div>
          <div v-else>No thumbnail</div>
        </div>
      </div>
    </div>
  </div>
  <Teleport to="body">
    <div ref='adjustThumbnailModal' class="modal fade show">
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title text-primary">Thumbnail adjustment</h5>
          </div>
          <div class="modal-body">
            <div class="cropper-actions">
              <button type="button" class="btn btn-outline-primary" @click="$refs.cropper.reset()">Reset</button>
              <button type="button" class="btn btn-outline-primary ms-1" @click="cropperFitToImage()">Fit to image</button>
            </div>
            <div class="cropper-container">
              <cropper ref="cropper"
                       :src="croppedImage.src"
                       :foregroundClass="cropperConfig.foregroundClass"
                       :backgroundClass="cropperConfig.backgroundClass"
                       :defaultBoundaries="cropperConfig.boundaries"
                       :imageRestriction="cropperConfig.restriction"
                       :stencil-props="cropperConfig.stencil"
                       :canvas="cropperConfig.outputFormat"/>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="croppingCancel()">Cancel</button>
            <button type="button" class="btn btn-primary" @click="croppingConfirm()">Confirm</button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style lang="scss">
@import '~vue-advanced-cropper/dist/style.css';

.slot-content
{
  & > div
  {
    display: none;
  }
}

.drop-zone
{
  border: 2px dashed lightgray;
  border-radius: 0.5em;

  &.drop-accepted {
    background-color: rgba(128,255,128, 0.5);
    cursor: copy;
  }

  &.drop-rejected {
    background-color: rgba(255,128,128, 0.5);
    cursor: not-allowed;
  }
}
.img-thumbnail
{
  max-height: 72px;
}
.cropper-actions
{
  .btn {
    border-radius: var(--bs-btn-border-radius) var(--bs-btn-border-radius) 0 0;
    border-width: var(--bs-btn-border-width) var(--bs-btn-border-width) 0 var(--bs-btn-border-width);
  }
}
.cropper-container {
  width: 100%;
  min-height: 288px;
  max-height: 288px;
  position: relative;
  .vue-advanced-cropper {
    height: 288px;
  }
  :deep(.cropper-background) {
    background: rgba(0, 0, 0, 0.2);
    background: repeating-conic-gradient(rgba(0, 0, 0, 0.2) 0% 25%, transparent 0% 50%) 50% / 20px 20px;
  }
  :deep(.cropper-foreground) {
    opacity: 1;
    background: rgba(0, 0, 0, 0.8);
  }
}
</style>
