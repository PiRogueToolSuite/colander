<template>
  <div class="generic-entity-details text-small">
    <div class="row">
      <div class="col-xl">
        <span v-if="this.showName" class="h5 font-monospace me-1 fw-bold text-wrap">{{ this.entity.name }}</span>
        <h6 v-if="this.showName">Details</h6>
        <ul class="list-unstyled">
          <li v-if="this.entity.description" class="text-muted fst-italic text-wrap mb-2">
            <span class="text-muted">{{ this.entity.description }}</span>
          </li>
          <li class="">
            <span class="field-name text-primary font-monospace">type: </span>
            <span class="font-monospace text-capitalize">{{ this.entity.super_type.name }}</span> -
            <span class="font-monospace">{{ this.entity.type.name }}</span>
          </li>
          <li class="">
            <span class="field-name text-primary font-monospace">id:</span>
            <span class="font-monospace">{{ this.entity.id }}</span>
          </li>
          <li class="">
            <span class="field-name text-primary font-monospace">created at:</span>
            <span class="font-monospace">{{ this.entity.created_at }}</span>
          </li>
          <li class="">
            <span class="field-name text-primary font-monospace">updated at:</span>
            <span class="font-monospace">{{ this.entity.updated_at }}</span>
          </li>

          <li v-if="entity.md5" class="">
            <span class="field-name text-primary font-monospace">MD5:</span>
            <span class="font-monospace">{{ this.entity.md5 }}</span>
          </li>
          <li v-if="entity.sha1" class="">
            <span class="field-name text-primary font-monospace">SHA1:</span>
            <span class="font-monospace">{{ this.entity.sha1 }}</span>
          </li>
          <li v-if="entity.sha256" class="">
            <span class="field-name text-primary font-monospace">SHA256:</span>
            <span class="font-monospace">{{ this.entity.sha256 }}</span>
          </li>
          <li v-if="entity.extension" class="">
            <span class="field-name text-primary font-monospace">extension:</span>
            <span class="font-monospace">{{ this.entity.extension }}</span>
          </li>
          <li v-if="entity.first_seen" class="">
            <span class="field-name text-primary font-monospace">first seen:</span>
            <span class="font-monospace">{{ this.entity.first_seen }}</span>
          </li>
          <li v-if="entity.last_seen" class="">
            <span class="field-name text-primary font-monospace">last seen:</span>
            <span class="font-monospace">{{ this.entity.last_seen }}</span>
          </li>
        </ul>
      </div>
      <div v-if="this.entity['attributes'] && Object.keys(this.entity.attributes).length !== 0" class="col-xl">
        <h6 v-if="this.showName">Attributes</h6>
        <ul class="list-unstyled font-monospace">
          <li v-for="[k, v] in Object.entries(this.entity.attributes)">
            <span class="field-name text-primary font-monospace">{{ k }}:</span>
            <span class="font-monospace text-wrap">{{ v }}</span>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    entity: Object,
    showName: Boolean,
  },
  components: {},
  data() {
    return {
      styles: null,
      loading: true,
    }
  },
  created() {
    this.$cache.retrieve('all_styles').then((styles) => {
      this.styles = styles;
      this.attachStyles();
      this.loading = false;
    });
  },
  mounted() {
    this.loading = true;
  },
  methods: {
    attachStyles() {
      if (this.styles && !this.loading) {
        this.entity.superTypeStyle = this.getSuperTypeStyle(entity);
        this.entity.type = this.getTypeStyle(entity);
      }
    },
    getSuperTypeStyle(entity) {
      if (this.styles) {
        return Object.values(this.styles).find(
          (value) => value.short_name === entity.super_type.short_name
        );
      }
    },
    getTypeStyle(entity) {
      if (this.styles) {
        const superTypeStyle = Object.values(this.styles).find(
          (value) => value.short_name === entity.super_type.short_name
        );
        if (superTypeStyle) {
          return superTypeStyle.types[entity.type.short_name];
        }
      }
    }
  }
}
</script>

<style scoped>
</style>
