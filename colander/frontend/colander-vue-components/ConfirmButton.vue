<script>
export default {
  props: {
    class: String,
    href: String,
    title: String,
    type: String,
    role: String,
    disabled: Boolean,
  },
  data() {
    return {
      askingConfirmation: false,
    }
  },
  created() {
    this.$logger(this, 'ConfirmButton');
    this.$debug('created', this.$el);
  },
  mounted() {
    this.$debug('mounted', this.$el);
  },
  methods: {
    askOrDoAction(event) {
      this.$debug('askOrDoAction', event);
      if (this.askingConfirmation) {
        // Proceed to action
        // Aka: do nothing
      }
      else {
        event.preventDefault();
        event.stopPropagation();
        event.stopImmediatePropagation(); // Also stop on propagation on this node
        this.askingConfirmation = true;
      }
    },
    restore(event) {
      this.askingConfirmation = false;
    }
  },
};
</script>
<template>
  <a :class :href :title :type :role :disabled @click="askOrDoAction($event)" @blur="restore($event)">
    <span v-if="askingConfirmation">
      <strong>Sure ?</strong>
    </span>
    <span v-else>
      <slot/>
    </span>
  </a>
</template>
