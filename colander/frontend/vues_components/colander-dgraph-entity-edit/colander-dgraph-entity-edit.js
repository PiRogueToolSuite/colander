new Vue({
  delimiters: ['[[', ']]'],
  data: {
    entity: {},
    allStyles: {},
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
      $(this.$el).trigger('save-entity', [tmp]);
    },
    edit_entity: function(ctx) {
      this.entity = ctx;
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
      return !type;
    }
  }
});
//# sourceURL=webpack://colander/./colander/frontend/vues_components/colander-dgraph-entity-edit/colander-dgraph-entity-edit.js
