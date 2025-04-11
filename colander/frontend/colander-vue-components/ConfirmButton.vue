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
      itsAButtonTag: false, // Can't be a computed var, this.$el will be null at rendering
                            // using computed value for the first time
      askingConfirmation: false,
    }
  },
  created() {
    this.$logger(this, 'ConfirmButton');
    this.$debug('itsAButtonTag', this.type);
    this.itsAButtonTag = this.type?.toLowerCase() === 'button';
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
  <button v-if="itsAButtonTag" :disabled
          :class :href :title :type :role @click="askOrDoAction($event)" @blur="restore($event)">
    <span v-if="askingConfirmation">
      <strong>Sure ?</strong>
    </span>
    <span v-else>
      <slot/>
    </span>
  </button>
  <a v-else :class :href :title :type :role @click="askOrDoAction($event)" @blur="restore($event)">
    <span v-if="askingConfirmation">
      <strong>Sure ?</strong>
    </span>
    <span v-else>
      <slot/>
    </span>
  </a>
</template>
