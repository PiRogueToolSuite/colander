<script setup>
</script>
<script>
import {defineAsyncComponent} from "vue";

export default {
  components: {
    ThumbnailInputField: defineAsyncComponent(() =>
      import(/* webpackChunkName: "ThumbnailInputField" */ '../ThumbnailInputField.vue')),
  },
  data() {
    return {
      entity: {},
      allStyles: {},
    };
  },
  created() {
    this.$logger(this, 'EntityEditPane');
  },
  methods: {
    optionContent: (t) => {
      // Unfortunately, vuejs (at least in v2), strip out
      // 'invalid' html childing (e.g: for option tag content)
      // In our case, <i> tags are stripped out from vue template generation.
      // Using v-html binding allow-us to workaround this behaviour.
      return `<i class="fa nf ${t['icon-font-classname']}"></i> ${t.name}`;
    },
    cancel: function () {
      $(this.$el).trigger('close-component');
    },
    save: function() {
      let tmp = JSON.parse(JSON.stringify(this.entity));

      if (this.$refs.thumbnailDelete.checked) {
        this.$debug('Deleting existing thumbnail');
        tmp['thumbnail_delete'] = true;
        $(this.$el).trigger('save-entity', [tmp]);
      }
      else if (this.$refs.thumbnailFileUploader.files.length > 0) {
        let fileToUpload = this.$refs.thumbnailFileUploader.files[0];
        this.$debug('Adding file to upload', fileToUpload);
        const reader = new FileReader();
        reader.onload = () => {
          tmp['thumbnail'] = {
            content: reader.result,
            name: fileToUpload.name,
            size: fileToUpload.size,
            lastModified: fileToUpload.lastModified,
            type: fileToUpload.type,
          };
          $(this.$el).trigger('save-entity', [tmp]);
        };
        reader.onerror = (err) => {
          this.$error('fileToUpload reader error', err);
        };
        reader.readAsDataURL(fileToUpload);
      }
      else {
        $(this.$el).trigger('save-entity', [tmp]);
      }
    },
    edit_entity: function(ctx) {
      this.$debug('edit_entity ctx:', ctx);
      this.entity = ctx;
      this.$refs.thumbnailEditor.setInitialImageSrc(this.entity.thumbnail_url);
      this.$refs.thumbnailEditor.resetThumbnail();
      $(this.$el).find('input[name=name]').select();
    }
  },
  computed: {
    types: function() {
      if (!this.allStyles[this.entity.super_type]) return null;
      if (Object.keys(this.allStyles[this.entity.super_type].types).length === 0) return null;
      return this.allStyles[this.entity.super_type].types;
    },
    invalidForm: function() {
      let name = this.entity.name?.trim();
      if (!name) return true;
      if (this.entity.super_type === 'PiRogueExperiment') return false;
      let type = this.entity.type;
      if (!type) return true;
      if (['DataFragment', 'DetectionRule'].includes(this.entity.super_type)) {
        let content = this.entity.content?.trim();
        if (!content) return true;
      }
      return false;
    }
  }
};
</script>
<template>
  <div class="vue-component">
    <div class='vue-container container py-2'>
      <div class="body">
        <h5>
          <i v-bind:class="['fa', 'text-primary', allStyles[entity.super_type]?.['icon-font-classname']]" v-bind:title="entity.super_type"></i>
          {{entity.super_type}} entity
        </h5>
        <div class="form-group mb-2">
            <label>Entity name*</label>
            <input class="form-control" type="text" placeholder="Entity name" v-model="entity.name" name="name"/>
        </div>
        <div v-if="types">
          <div class="form-group mb-2">
            <label>{{entity.super_type}} type*</label>
            <select class='form-control' name="type" size="6" v-model="entity.type">
              <option v-for="(type, tid) in types" v-bind:value="tid" v-html="optionContent(type)"/>
            </select>
          </div>
        </div>
        <div v-if="entity.super_type == 'DataFragment'">
          <div class="form-group mb-2">
            <label>Content*</label>
            <textarea name='content' class="form-control" row="5" v-model="entity.content"></textarea>
          </div>
        </div>
        <div v-else-if="entity.super_type == 'DetectionRule'">
          <h4>Content</h4>
          <pre>{{entity.content}}</pre>
        </div>
        <div class="form-group mb-2">
          <label class="form-label" for="id_thumbnail">Thumbnail</label>
          <ThumbnailInputField ref="thumbnailEditor">
            <div>
              <input id="id_thumbnail" ref="thumbnailFileUploader" type="file" accept='image/png, image/jpeg, image/jpg'/>
              <input id="thumbnail-clear_id" ref="thumbnailDelete" type="checkbox" />
            </div>
          </ThumbnailInputField>
        </div>
      </div>
      <div class="footer">
          <button @click="cancel()" type="button" class="btn btn-outline-secondary me-1" role="cancel">Cancel</button>
          <button @click="save()" v-bind:disabled="invalidForm" type="button" class="btn btn-primary" role="save">Save</button>
      </div>
    </div>
  </div>
</template>
