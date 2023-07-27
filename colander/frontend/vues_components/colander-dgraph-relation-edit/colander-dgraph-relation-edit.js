new Vue({
  delimiters: ['[[', ']]'],
  data: {
    ctx: {},
    $pending_edge: null,
    allStyles: {},
  },
  methods: {
    cancel: function () {
      let tmp = JSON.parse(JSON.stringify(this.ctx));
      tmp.pending_edge = this.$pending_edge;
      $(this.$el).trigger('close-component', [tmp]);
      this.$pending_edge = null;
    },
    save: function() {
      let tmp = JSON.parse(JSON.stringify(this.ctx));
      tmp.pending_edge = this.$pending_edge;
      this.$pending_edge = null;
      $(this.$el).trigger('save-relation', [tmp]);
    },
    edit_relation: function(ctx) {
      let tmp = Object.assign({}, ctx);
      this.$pending_edge = tmp.pending_edge;
      delete tmp.pending_edge;
      this.ctx = tmp;
      $(this.$el).find('input[name=name]').select();
    }
  },
  computed: {
    invalidForm: function() {
      let name = this.ctx.name?.trim();
      return !name;
    }
  }
});
//# sourceURL=webpack://colander/./colander/frontend/vues_components/colander-dgraph-relation-edit/colander-dgraph-relation-edit.js
