<script>
import {Button} from "primevue";

export default {
  components: { Button },
  props: [ 'label', 'icon' ],
  emits: [ 'confirmed', 'canceled' ],
  data() {
    return {
      pendingConfirmation: false,
    }
  },
  methods: {
    onClick() {
      if (this.pendingConfirmation) {
        this.$emit('confirmed');
        this.pendingConfirmation = false;
      }
      else {
        this.pendingConfirmation = true;
      }
    },
    cancelAction() {
      this.pendingConfirmation = false;
      this.$emit('canceled');
    }
  },
  computed: {
    currentLabel() {
      return this.pendingConfirmation ? 'Sure ?' : this.label;
    },
    currentIcon() {
      return this.pendingConfirmation ? '' : this.icon;
    },
    currentWeight() {
      return this.pendingConfirmation ? 700 : 500;
    }
  }
}
</script>
<template>
  <Button :label="currentLabel" :icon="currentIcon" @click="onClick" @blur="cancelAction" class="dynamic-weight"/>
</template>
<style scoped>
.dynamic-weight {
  --p-button-label-font-weight: v-bind(currentWeight);
}
</style>
