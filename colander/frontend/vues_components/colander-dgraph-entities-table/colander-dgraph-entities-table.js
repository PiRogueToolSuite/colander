Vue.createApp({
  delimiters: ['[[', ']]'],
  data: () => ({
    entities:{},
    allStyles: {},
    overrides: {},
    editableVisibility: false,
    currentSort: {
      attributes: [], // defaults initial values set in created()
      direction: 'asc',
    },
    currentSearch: '',
  }),
  created: function() {
    // Globally defines sort attributes importance
    this.sortAttributesDefaults = [
      'name', 'visibility', 'super_type', 'type',
    ];
    this.currentSort.attributes = [...this.sortAttributesDefaults];
  },
  methods: {
    sort: function(attr) {
      if (attr === this.currentSort.attributes[0]) { // Unsafe ?
        this.currentSort.direction = this.currentSort.direction === 'asc' ? 'desc' : 'asc';
      }
      let newSortAttrs = [attr];
      for(let dfltAttr of this.sortAttributesDefaults) {
        if (newSortAttrs.includes(dfltAttr)) continue;
        newSortAttrs.push(dfltAttr);
      }
      this.currentSort.attributes = newSortAttrs;
    },
    isCurrentSort: function(attr) {
      return false;
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
      // Not needed anymore

      // Despite Vue3's new Reactive architecture,
      // added entities do not refresh the table.
      // Even using $forceUpdate, settings initiale reactive(entities), etc)
      // The only hack found (for now) is to force a sort of the table
      this.sort(this.currentSort.attributes);
      this.$nextTick().then(() => {
        this.sort(this.currentSort.attributes);
      })
    },
    refresh: function() {
      // Used (at least) when an entity attributes is changed.
      this.$nextTick().then(() => {
        this.$forceUpdate();
      });
    },
    close: function () {
      $(this.$el).trigger('close-component');
    },
    toggleEntityVisibility: function(eid) {
      this.overrides[eid] = this.overrides[eid] || {};
      this.overrides[eid].hidden = !(this.overrides[eid]?.hidden);
      $(this.$el).trigger('entity-visibility-changed', [eid, this.overrides[eid].hidden]);
    }
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
        for(let currentAttr of this.currentSort.attributes) {
          if (currentAttr === 'visibility') {
            if (this.overrides[aid] === undefined || this.overrides[bid] === undefined) continue;
            if (this.overrides[aid]['hidden'] < this.overrides[bid]['hidden']) return -1 * modifier;
            if (this.overrides[aid]['hidden'] > this.overrides[bid]['hidden']) return 1 * modifier;
          } else {
            if (this.entities[aid][currentAttr] < this.entities[bid][currentAttr]) return -1 * modifier;
            if (this.entities[aid][currentAttr] > this.entities[bid][currentAttr]) return 1 * modifier;
          }
        }
        return 0;
      });
      return keys;
    }
  }
});
//# sourceURL=webpack://colander/./colander/frontend/vues_components/colander-dgraph-entities-table/colander-dgraph-entities-table.js
