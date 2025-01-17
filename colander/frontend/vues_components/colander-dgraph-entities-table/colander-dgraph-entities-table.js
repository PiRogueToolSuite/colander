new Vue({
  delimiters: ['[[', ']]'],
  data: {
    entities:{},
    allStyles: {},
    editableVisibility: false,
    currentSort: {
      attribute: 'name',
      direction: 'asc',
    },
    currentSearch: '',
  },
  methods: {
    sort: function(attr) {
      if (attr === this.currentSort.attribute) {
        this.currentSort.direction = this.currentSort.direction === 'asc' ? 'desc' : 'asc';
      }
      this.currentSort.attribute = attr;
    },
    focusEntity: function(eid) {
      $(this.$el).trigger('focus-entity', [eid]);
    },
    filterBy: function(filter) {
      let lcFilter = filter.toLowerCase();
      if (this.currentSearch.toLowerCase().includes(lcFilter)) return;
      this.currentSearch = lcFilter + " " + this.currentSearch;
    },
    track_new_entity: function(ctx) {
      delete this.entities[ctx.id];
      Vue.set(this.entities, ctx.id, ctx);
    },
    refresh: function() {

    },
    close: function () {
      $(this.$el).trigger('close-component');
    },
  },
  computed: {
    sortedEntities_keys: function() {
      let keys = Object.keys(this.entities);
      let query = this.currentSearch;
      query = query.replaceAll(/\s+/g, ' ');
      let searchREs = query.split(' ').map((s) => new RegExp(s, 'i') );
      keys = keys.filter((eid) => {
        for(let sre of searchREs) {
          let match =
                 sre.test(this.entities[eid].name)
              || sre.test(this.entities[eid].type)
              || sre.test(this.entities[eid].super_type);
          if (!match) return false;
        }
        return true;
      });
      keys.sort((aid,bid) => {
        let modifier = this.currentSort.direction === 'desc' ? -1 : 1;
        if (this.entities[aid][this.currentSort.attribute] < this.entities[bid][this.currentSort.attribute]) return -1 * modifier;
        if (this.entities[aid][this.currentSort.attribute] > this.entities[bid][this.currentSort.attribute]) return  1 * modifier;
        return 0;
      });
      return keys;
    }
  }
});
//# sourceURL=webpack://colander/./colander/frontend/vues_components/colander-dgraph-entities-table/colander-dgraph-entities-table.js
