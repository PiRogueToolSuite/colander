new Vue({
  delimiters: ['[[', ']]'],
  data: {
    allStyles: {},
    entities: {},
    subgraph: {},
  },
  methods: {
    cancel: function () {
      $(this.$el).trigger('close-component');
    },
    save: function(edit_after_creation) {
      let tmp = JSON.parse(JSON.stringify(this.subgraph));
      $(this.$el).trigger('save-subgraph', [tmp, edit_after_creation]);
    },
  },
  computed: {
    invalidForm: function() {
      let name = this.subgraph.name?.trim();
      if (!name) return true;
      return false;
    },
    sortedEntities_keys: function() {
      if (!this.subgraph.overrides) return [];
      let keys = Object.keys(this.subgraph.overrides);
      return keys;
    },
  },
});
//# sourceURL=webpack://colander/./colander/frontend/vues_components/colander-dgraph-subgraph-form/colander-dgraph-subgraph-form.js
