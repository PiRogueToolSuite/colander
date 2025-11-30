<script>
import Pills from "./Pills.vue";
import GenericEntityDetails from "./GenericEntityDetails.vue";
import Dialog from "primevue/dialog";

export default {
  components: {
    Dialog,
    GenericEntityDetails,
    Pills,
  },
  props: {
    entity: Object
  },
  data() {
    return {
      visible: false
    }
  },
  methods: {
    toggle() {
      this.visible = !this.visible;
    },
    show() {
      this.visible = true;
    },
    hide() {
      this.visible = false;
    }
  }
}
</script>

<template>
  <Dialog
    v-model:visible="this.visible" modal
    :style="{ minWidth: '25vw', maxWidth: '95vw', minHeight: '35vh', maxHeight: '95vh' }"
  >
    <template #header>
      <div class="text-start h5">
        <i class="fa me-1 text-muted" :class="this.entity.superTypeStyle['icon-font-classname']"></i>
        <Pills :entity="this.entity"/>
        <i class="nf me-1 text-muted" :class="this.entity.type['icon-font-classname']"></i>
        <span class="font-monospace me-1 fw-bold text-truncate">{{ this.entity.name }}</span>
      </div>
    </template>
    <GenericEntityDetails :entity="this.entity" :show-name="false"/>
  </Dialog>
</template>

<style scoped>

</style>
