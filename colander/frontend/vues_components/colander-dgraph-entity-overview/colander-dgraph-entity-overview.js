Vue.createApp({
  delimiters: ['[[', ']]'],
  data: () => ({
    entity: {},
    allStyles: {},
  }),
  methods: {
    date_str: (dStr) => {
      if (!dStr) return '';
      return new Intl.DateTimeFormat('default', {dateStyle: 'long', timeStyle: 'short'}).format(new Date(dStr));
    },
    close: function () {
      $(this.$el).trigger('close-component');
    },
    quickEdit: function () {
      $(this.$el).trigger('quick-edit-entity', [this.entity.id]);
    },
  },
  computed: {
    descriptionMarkdown: function() {
      // entity.description || 'No description'
      if (this.entity.description) {
        return Markdown.render(this.entity.description);
      }
      return 'No description';
    }
  }
});
//# sourceURL=webpack://colander/./colander/frontend/vues_components/colander-dgraph-entity-overview/colander-dgraph-entity-overview.js
