<script>
import { defineComponent } from 'vue';
//import Cropper from 'cropperjs';
import CropperCanvas from '@cropper/element-canvas';
import CropperImage from '@cropper/element-image';
import CropperShade from '@cropper/element-shade';
import CropperHandle from '@cropper/element-handle';
import CropperSelection from '@cropper/element-selection';

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
  data() {
    return {
      image: {
        src: null,
        type: null,
      },
      current: {
        src: null,
      },
      supportedMimeType: {
        'image/png': true,
        'image/jpeg': true,
      },
    };
  },
  computed: {
    removable() {
      return this.current.src !== null && this.current.src === this.image.src;
    },
    resetable() {
      return this.current.src !== this.image.src;
    },
  },
  beforeCreate() {
    CropperCanvas.$define();
    CropperImage.$define();
    CropperShade.$define();
    CropperHandle.$define();
    CropperSelection.$define();
  },
  mounted() {
    $(this.$refs.adjustThumbnailModal).on('hidden.bs.modal', () => {
      alert('canceled ?');
    });
    $(this.$refs.adjustThumbnailModal).on('shown.bs.modal', () => {
      this.croppingFetauresReset();
    });
    this.$nextTick(() => {
      this.$refs.cropperImage.$ready((image) => {
        console.log('Image ready ?', image);
      });
    });
    console.log('mounted');
  },
  methods: {
    replacedDom(jDomTree) {
      const jImg = jDomTree.find('img');
      if (jImg.length) {
        this.current.src = jImg.attr('src');
        this.image.src = this.current.src;
      }
      console.log('replacedDom');
    },
    loadImage(event) {
      // Reference to the DOM input element
      const {files} = event.target;
      this.handleFiles(files);
    },
    handleFiles(files) {
			// Ensure that you have a file before attempting to read it
			if (files && files[0]) {
				// 1. Revoke the object URL, to allow the garbage collector to destroy the uploaded before file
				if (this.image.src) {
					URL.revokeObjectURL(this.image.src)
				}
				// 2. Create the blob link to the file to optimize performance:
				const blob = URL.createObjectURL(files[0]);

				// 3. The steps below are designated to determine a file mime type to use it during the
				// getting of a cropped image from the canvas. You can replace it them by the following string,
				// but the type will be derived from the extension and it can lead to an incorrect result:
				//
				// this.image = {
				//    src: blob;
				//    type: files[0].type
				// }

				// Create a new FileReader to read this image binary data
				const reader = new FileReader();
				// Define a callback function to run, when FileReader finishes its job
				reader.onload = (e) => {
					// Note: arrow function used here, so that "this.image" refers to the image of Vue component
					this.image = {
						// Set the image source (it will look like blob:http://example.com/2c5270a5-18b5-406e-a4fb-07427f5e7b94)
						src: blob,
						// Determine the image type to preserve it during the extracting the image from canvas:
						type: getMimeType(e.target.result, files[0].type),
					};

          let file = new File([reader.result], files[0].name, { type:this.image.type, lastModified:new Date().getTime()});
          let container = new DataTransfer();
          container.items.add(file);
          this.$refs.fileUploader.files = container.files;
          this.croppingStart();
				};
				// Start the reader job - read file as a data url (base64 format)
				reader.readAsArrayBuffer(files[0]);
			}
    },
    croppingCancel() {
      $(this.$refs.adjustThumbnailModal).modal('hide');
    },
    croppingStart(ctx) {
      $(this.$refs.adjustThumbnailModal).modal('show');
      /*
      this.$refs.cropperImage.$ready((image) => {
        setTimeout(() => {
          console.log('image ready', image.naturalWidth, image.naturalHeight);
          this.$refs.cropperImage.$center();
          this.$refs.cropperSelection.$center();
        }, 1000);
      });
       */
    },
    croppingFetauresReset() {
      console.log('Guy de gluk', this.$refs.cropperCanvas);
      this.$refs.cropperImage.$center("contain");
      this.$refs.cropperSelection.$center();
    },
    croppingConfirm() {
      $(this.$refs.adjustThumbnailModal).modal('hide');
    },
    manualLoad(event) {
      event.preventDefault();
      event.stopPropagation();
      this.$refs.fileChooser.click();
    },
    removeThumbnail(event) {
      event.preventDefault();
      event.stopPropagation();
      this.image.src = null;
      this.$refs.checkboxClear.checked = true;
    },
    resetThumbnail(event) {
      event.preventDefault();
      event.stopPropagation();
      this.image.src = this.current.src;
      this.$refs.fileUploader.files = [];
    },
    dragover(event) {
      console.log('dragover', event, event.dataTransfer);
      event.preventDefault();
      event.stopPropagation();
      let dt = event.dataTransfer;
      for(let item of dt.items) {
        console.log('item', item);
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
      console.log('dragleave', event, event.dataTransfer);
      event.preventDefault();
      event.stopPropagation();
      this.$refs.dropzone.classList.remove('drop-accepted');
      this.$refs.dropzone.classList.remove('drop-rejected');
    },
    drop(event) {
      console.log('drop', event);
      event.preventDefault();
      event.stopPropagation();
      this.$refs.dropzone.classList.remove('drop-accepted');
      this.$refs.dropzone.classList.remove('drop-rejected');

      let dt = event.dataTransfer;
      for(let item of dt.items) {
        console.log('item', item);
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
  <label class="form-label">Thumbnail</label>
  <input class="visually-hidden" type='file' ref='fileChooser' accept='image/png,image/jpeg' @change="loadImage($event)"/>
  <input class="visually-hidden" type="file" ref='fileUploader' name="thumbnail" accept="image/png, image/jpeg" id="id_thumbnail"/>
  <input class="visually-hidden" type="checkbox" ref='checkboxClear' name="thumbnail-clear" id="thumbnail-clear_id" />
  <div class='drop-zone' ref='dropzone' @dragleave="dragleave" @dragover="dragover" @drop="drop">
    <div class='row'>
      <div class='col-8'>
        <div class='d-flex justify-content-center p-1'>
          <button class='btn btn-sm btn-secondary text-white' @click="manualLoad">Browse</button>
        </div>
        <div class='hint d-flex justify-content-center p-1'>Or drap'n drop one here</div>
      </div>
      <div class='col-4'>
        <div v-if="image.src">
          <img class='img-thumbnail' v-if="image.src" v-bind:src="image.src" alt="Current thumbnail" />
          <button v-if="removable" class='btn btn-sm btn-secondary text-white' @click="removeThumbnail">Remove</button>
          <button v-if="resetable" class='btn btn-sm btn-secondary text-white' @click="resetThumbnail">Reset</button>
        </div>
        <div v-else>No thumbnail</div>
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
            <p>Please adjust your thumbnail.</p>
            <div class="cropper-container">
              <cropper-canvas ref="cropperCanvas" background>
                <cropper-image ref="cropperImage" v-bind:src="image.src" initial-center-size="contain"/>
                <cropper-shade hidden></cropper-shade>
                <cropper-selection ref="cropperSelection"
                                   initial-coverage="0.5"
                                   initial-aspect-ratio="1"
                                   aspect-ratio="1"
                                   movable resizable outlined>
                  <cropper-handle action="move" theme-color="rgba(255, 255, 255, 0.35)"></cropper-handle>
                  <cropper-handle action="n-resize"></cropper-handle>
                  <cropper-handle action="e-resize"></cropper-handle>
                  <cropper-handle action="s-resize"></cropper-handle>
                  <cropper-handle action="w-resize"></cropper-handle>
                  <cropper-handle action="ne-resize"></cropper-handle>
                  <cropper-handle action="nw-resize"></cropper-handle>
                  <cropper-handle action="se-resize"></cropper-handle>
                  <cropper-handle action="sw-resize"></cropper-handle>
                </cropper-selection>
              </cropper-canvas>
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

<style lang="scss" scoped>
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
  max-height: 144px;
}
.cropper-container {
  width: 100%;
  min-height: 288px;

  cropper-canvas {
    width: 100%;
    min-height: 288px;
  }
}
</style>
