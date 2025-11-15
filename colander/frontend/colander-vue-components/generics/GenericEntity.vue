<template>
  <div v-if="!this.loading && this.visible" class="generic-entity text-small">
    <div class="row">
      <div class="col-12">
        <div class="card entity-card p-0 m-1"
             :style="this.cardStyle"
             @click="toggleSelect($event)">
          <div class="card-body p-2">
            <div class="row">
              <div class="col-8">
                <div>
                  <i class="fa me-1" :class="this.entity.superTypeStyle['icon-font-classname']"></i>
                  <Pills :entity="entity"/>
                  <i class="nf me-1" :class="this.entity.type['icon-font-classname']"></i>
                  <span class="font-monospace me-1 fw-bold text-truncate">{{ this.entity.name }}</span>
                  <Button icon="pi pi-eye" variant="text" size="small" rounded @click="toggleQuickView($event)"/>
                  <EntityQuickViewDialog ref="quickViewDialog" :entity="this.entity" />
                </div>
                <div>
                  <span class="text-muted text-capitalize">{{ this.entity.super_type.name }} - </span>
                  <span class="text-muted ">{{ this.entity.type.name }}</span>
                  <span v-for="tag in this.tags" class="badge bg-secondary mx-1">
                    <i class="fa fa-tag"></i>
                    {{ tag }}
                  </span>
                </div>
              </div>
              <div class="col-4 d-flex align-self-stretch align-items-end justify-content-end">
                <slot name="right" :entity="this.entity">
                  <Button icon="pi pi-eye" size="small" label="Quick view"
                          @click="toggleQuickView($event)"/>
                </slot>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import Button from 'primevue/button';
import Card from 'primevue/card';
import Pills from "./Pills.vue";
import EntityQuickViewDialog from "./EntityQuickViewDialog.vue";

export default {
  props: {
    entity: Object,
    selectable: Boolean,
  },
  components: {
    Button,
    Card,
    EntityQuickViewDialog,
    Pills,
  },
  data() {
    return {
      showQuickView: false,
      visible: true,
      loading: true,
      selected: false,
    }
  },
  created() {
    this.$themeUtils.attachStyleToEntity(this.entity).then(() => {
      this.loading = false;
    });
  },
  mounted() {
    this.loading = true;
  },
  computed: {
    cardStyle() {
      if (!this.loading && this.entity.superTypeStyle) {
        let s = {
          borderLeftWidth: '6px',
          borderLeftColor: this.entity.superTypeStyle.color,
        }
        if (this.selected && this.selectable) {
          s.borderColor = 'var(--bs-primary)'
        }
        return s
      }
    },
    tags() {
      if (this.entity['attributes'] && this.entity['attributes']['tags']) {
        return this.entity.attributes.tags.split(',');
      }
      return [];
    }
  },
  methods: {
    select() {
      this.selected = true;
      this.$emit('select', {selected: this.selected, id: this.entity.id});
    },
    show() {
      this.visible = true;
    },
    hide() {
      this.visible = false;
    },
    deselect() {
      this.selected = false;
      this.$emit('select', {selected: this.selected, id: this.entity.id});
    },
    matchEntityName(term) {
      if (!term) {
        return true;
      }
      return this.entity.name.toLowerCase().includes(term.toLowerCase());
    },
    toggleSelect(event) {
      if (event && this.selectable) {
        this.selected = !this.selected;
        this.$emit('select', {selected: this.selected, id: this.entity.id});
        event.stopPropagation();
      }
    },
    toggleQuickView(event) {
      this.$refs.quickViewDialog.show();
      event.stopPropagation();
    },
  }
}
</script>

<style scoped>
.entity-card:hover {
  box-shadow: 0 2px 4px 0 rgba(0, 0, 0, 0.2), 0 3px 10px 0 rgba(0, 0, 0, 0.19);
}
</style>
